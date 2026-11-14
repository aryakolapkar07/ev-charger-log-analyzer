"""
Log Analyzer
------------
Parses EV-charger-style log files, finds recurring issues, and produces a
summary report to speed up root cause analysis.

Expected log line format:
    2026-11-10 08:15:32 ERROR charger-03 [E102] Connector lock failure
The [CODE] part is optional.

Usage:
    python log_analyzer.py sample_logs/charger_sample.log --top 5
"""
import argparse
import re
from pathlib import Path

import pandas as pd

LOG_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+"
    r"(?P<level>DEBUG|INFO|WARNING|ERROR|CRITICAL)\s+"
    r"(?P<charger>\S+)\s+"
    r"(?:\[(?P<code>[A-Za-z0-9_]+)\]\s+)?"
    r"(?P<message>.*)$"
)

LEVEL_ORDER = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}
PROBLEM_LEVELS = ["WARNING", "ERROR", "CRITICAL"]

# Example knowledge base (synthetic). Extend this with your own findings.
RECOMMENDED_ACTIONS = {
    "E102": "Check connector lock actuator and wiring; inspect for debris. Replace actuator if repeated on the same unit.",
    "E305": "Check site network/router and SIM signal; verify backend endpoint and certificate; consider a firmware update.",
    "E410": "Verify payment gateway status and terminal connectivity; check recent config changes.",
    "W201": "Check grid supply and load balancing at the site; review charger power limits.",
    "C900": "Dispatch field technician: inspect cooling, ventilation and temperature sensor before re-enabling.",
}


def parse_lines(lines):
    """Parse an iterable of log lines. Returns (DataFrame, number_of_unparsed_lines)."""
    records, bad = [], 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        match = LOG_PATTERN.match(line)
        if match:
            records.append(match.groupdict())
        else:
            bad += 1
    df = pd.DataFrame(
        records, columns=["timestamp", "level", "charger", "code", "message"]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df, bad


def load_log(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return parse_lines(f)


def level_counts(df):
    return df["level"].value_counts().reindex(list(LEVEL_ORDER), fill_value=0)


def top_issues(df, n=10):
    """Most frequent WARNING/ERROR/CRITICAL issues, grouped by code (or message)."""
    cols = ["issue", "occurrences", "chargers_affected", "worst_level",
            "first_seen", "last_seen", "example_message", "recommended_action"]
    problems = df[df["level"].isin(PROBLEM_LEVELS)].copy()
    if problems.empty:
        return pd.DataFrame(columns=cols)
    problems["issue"] = problems["code"].fillna(problems["message"])
    grouped = (
        problems.groupby("issue")
        .agg(
            occurrences=("issue", "size"),
            chargers_affected=("charger", "nunique"),
            worst_level=("level", lambda s: max(s, key=LEVEL_ORDER.get)),
            first_seen=("timestamp", "min"),
            last_seen=("timestamp", "max"),
            example_message=("message", "first"),
        )
        .sort_values("occurrences", ascending=False)
        .head(n)
        .reset_index()
    )
    grouped["recommended_action"] = grouped["issue"].map(RECOMMENDED_ACTIONS).fillna(
        "Capture full diagnostics and escalate to engineering for root cause analysis."
    )
    return grouped[cols]


def problems_by_charger(df):
    problems = df[df["level"].isin(PROBLEM_LEVELS)]
    return problems["charger"].value_counts().sort_values(ascending=False)


def problems_by_hour(df):
    problems = df[df["level"].isin(PROBLEM_LEVELS)]
    return problems.groupby(problems["timestamp"].dt.hour).size().reindex(range(24), fill_value=0)


def build_report(df, bad_lines=0, top_n=5):
    if df.empty:
        return "No valid log lines found."
    out = []
    out.append("LOG ANALYSIS REPORT")
    out.append("=" * 60)
    out.append(f"Period: {df['timestamp'].min()}  ->  {df['timestamp'].max()}")
    out.append(f"Total lines parsed: {len(df)}   Unparsed lines: {bad_lines}")
    out.append(f"Chargers seen: {df['charger'].nunique()}")
    out.append("")
    out.append("Lines by level:")
    for level, count in level_counts(df).items():
        out.append(f"  {level:<9}{count}")
    out.append("")
    out.append(f"Top {top_n} recurring issues:")
    issues = top_issues(df, top_n)
    for i, row in enumerate(issues.itertuples(), start=1):
        out.append(f"  {i}. [{row.issue}] {row.example_message}")
        out.append(f"     {row.occurrences} occurrences on {row.chargers_affected} charger(s), worst level {row.worst_level}")
        out.append(f"     Suggested action: {row.recommended_action}")
    out.append("")
    out.append("Chargers with most problems:")
    for charger, count in problems_by_charger(df).head(5).items():
        out.append(f"  {charger}: {count}")
    busiest = problems_by_hour(df)
    out.append("")
    out.append(f"Peak problem hour: {int(busiest.idxmax()):02d}:00 ({int(busiest.max())} events)")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description="Analyze charger log files.")
    parser.add_argument("logfile", type=Path, help="Path to the log file")
    parser.add_argument("--top", type=int, default=5, help="How many top issues to show")
    parser.add_argument("--csv", type=Path, help="Optional: save top issues to a CSV file")
    args = parser.parse_args()

    df, bad = load_log(args.logfile)
    print(build_report(df, bad, args.top))
    if args.csv:
        top_issues(df, args.top).to_csv(args.csv, index=False)
        print(f"\nSaved top issues to {args.csv}")


if __name__ == "__main__":
    main()
