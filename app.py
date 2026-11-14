"""Streamlit web app for the Log Analyzer."""
from pathlib import Path

import streamlit as st

import log_analyzer as la

st.set_page_config(page_title="EV Charger Log Analyzer", page_icon="🔌", layout="wide")
st.title("🔌 EV Charger Log Analyzer")
st.caption("Upload a log file to find recurring issues, problem chargers and peak failure times.")

SAMPLE = Path(__file__).parent / "sample_logs" / "charger_sample.log"

uploaded = st.sidebar.file_uploader("Upload a .log or .txt file", type=["log", "txt"])
use_sample = st.sidebar.checkbox("Use sample log", value=uploaded is None)
top_n = st.sidebar.slider("Top issues to show", 3, 15, 5)

if uploaded is not None and not use_sample:
    lines = uploaded.getvalue().decode("utf-8", errors="replace").splitlines()
    df, bad = la.parse_lines(lines)
elif SAMPLE.exists():
    df, bad = la.load_log(SAMPLE)
else:
    st.info("Upload a log file to begin.")
    st.stop()

if df.empty:
    st.error("No valid log lines found. Expected: `YYYY-MM-DD HH:MM:SS LEVEL charger-id [CODE] message`")
    st.stop()

problems = df[df["level"].isin(la.PROBLEM_LEVELS)]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Lines parsed", len(df))
c2.metric("Problem events", len(problems))
c3.metric("Chargers", df["charger"].nunique())
c4.metric("Unparsed lines", bad)

st.subheader("Top recurring issues")
issues = la.top_issues(df, top_n)
st.dataframe(issues, width="stretch", hide_index=True)

left, right = st.columns(2)
with left:
    st.subheader("Problems by charger")
    st.bar_chart(la.problems_by_charger(df))
with right:
    st.subheader("Problems by hour of day")
    st.bar_chart(la.problems_by_hour(df))

st.subheader("Lines by level")
st.bar_chart(la.level_counts(df))

report = la.build_report(df, bad, top_n)
with st.expander("Text report"):
    st.code(report)
st.download_button("Download report (.txt)", report, file_name="log_report.txt")
st.download_button("Download top issues (.csv)", issues.to_csv(index=False), file_name="top_issues.csv")
