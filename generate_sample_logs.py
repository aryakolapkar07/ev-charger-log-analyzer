"""Generate a synthetic EV-charger log file for testing the analyzer."""
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)
chargers = [f"charger-{i:02d}" for i in range(1, 7)]
events = [  # (level, code, message, weight)
    ("INFO", "S100", "Charging session started", 40),
    ("INFO", "S101", "Charging session completed", 38),
    ("WARNING", "W201", "Slow charging rate detected", 8),
    ("ERROR", "E102", "Connector lock failure", 6),
    ("ERROR", "E305", "Lost connection to backend (heartbeat timeout)", 5),
    ("ERROR", "E410", "Payment authorization failed", 4),
    ("CRITICAL", "C900", "Over-temperature protection triggered", 1),
]

lines, t = [], datetime(2026, 11, 10, 0, 0, 0)
for _ in range(1500):
    t += timedelta(seconds=random.randint(30, 400))
    level, code, msg, _w = random.choices(events, weights=[e[3] for e in events])[0]
    charger = random.choice(chargers)
    # Plant patterns to discover: charger-03 has lock problems, charger-05 drops at night
    if code == "E102" and random.random() < 0.7:
        charger = "charger-03"
    if code == "E305" and random.random() < 0.7:
        charger = "charger-05"
        t = t.replace(hour=random.choice([1, 2, 3])) if random.random() < 0.5 else t
    lines.append(f"{t:%Y-%m-%d %H:%M:%S} {level} {charger} [{code}] {msg}")

lines.sort()
lines.insert(100, "### corrupted line from firmware dump ###")
lines.insert(900, "garbled output 0x7F3A")

out = Path(__file__).parent / "sample_logs" / "charger_sample.log"
out.parent.mkdir(exist_ok=True)
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Wrote {len(lines)} lines to {out}")
