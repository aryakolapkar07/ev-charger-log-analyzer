# 🔌 EV Charger Log Analyzer

A Python tool (command line + Streamlit web app) that parses charger-style log files, finds **recurring issues**, highlights **problem chargers** and **peak failure times**, and suggests next actions. Built to practise log analysis and root cause analysis for technical support work.

**Live demo:** _add your Streamlit link here_

## Features
- Parses log lines with regex; counts and reports unparsable lines
- Groups WARNING/ERROR/CRITICAL events by error code
- Shows chargers with the most problems and the hours when issues peak
- Suggests recommended actions per error code (editable knowledge base)
- Downloadable text report and CSV

## Log format
```
2026-11-10 08:15:32 ERROR charger-03 [E102] Connector lock failure
```
The `[CODE]` part is optional.

## Run locally
```bash
pip install -r requirements.txt
python generate_sample_logs.py          # creates sample_logs/charger_sample.log
python log_analyzer.py sample_logs/charger_sample.log --top 5   # CLI report
streamlit run app.py                    # web app
```

## Example findings (from the synthetic sample data)
- `charger-03` accounts for most connector lock failures (E102) -> likely a hardware issue on that unit
- `charger-05` shows repeated backend heartbeat timeouts (E305), mostly at night -> check site network/SIM signal

## Tech
Python, pandas, regex, Streamlit

## Note
The sample data is synthetic and the error codes are illustrative.
