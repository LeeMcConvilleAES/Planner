# AES Transport Planner V2.0

Version 2.0, 28 September 2026.

Jobs come from Big Change. Ken writes `data/bigchange_jobs.json` in this repo every ten minutes; the app reads it and never edits it. The app owns `data/planner.json`: runs (keyed by Big Change job id), run start times, capacity days, holidays, vehicle bookings, enquiries and conversions. Both files are read and written through the GitHub contents API.

## Files

- `app.py`: the Streamlit shell. Reads both files, migrates the old Sheet once, gates editing behind the password, writes `planner.json` on every change.
- `planner_ui/index.html`: the front end, a Streamlit component with no build step. All the planning rules live here.
- `requirements.txt`: streamlit, streamlit-autorefresh, requests, gspread, google-auth.
- `app_v1_sheet.py`: the previous app, kept so it can be deployed as a second Streamlit app for the parallel week.

## Streamlit Cloud secrets

Add these in the app's Settings, Secrets, before the first run of V2:

```toml
edit_password = "the team password"

[github]
token = "ghp_..."
repo = "LeeMcConvilleAES/Planner"
branch = "main"

[gcp_service_account]
# keep the existing block until the migration has run, then it can go
```

The token is a classic personal access token with the `repo` scope, on an account that is a collaborator on this repo.

## First run

If `data/planner.json` does not exist, the app reads the Google Sheet once and writes it: enquiries carry over, booked jobs that Big Change now holds hand their driver codes to run entries, holidays, vehicle bookings and capacity days become date ranged. A report shows at the top of the page until someone hides it. The Sheet is never written.

## Rules the front end enforces

- Every load is allocated on its own; a drop lands in front of the first card whose midpoint is below the pointer, or at the end of the run.
- Deliveries always before collections on a run; a site move orders like a collection.
- Enquiries can never be put on a run. A sure match from Ken converts on its own when editing is unlocked; a likely match is offered with Confirm and Dismiss.
- A job Big Change moved keeps its run for the old day and shows MOVED until it is re-planned. A job Big Change dropped is listed under the day for 7 days.
- SUB is the sub-contractor column: SUB1, SUB2, one run per subbie wagon, no bed check.

## Local test

```
set PLANNER_LOCAL_DATA=C:\some\folder      (holds bigchange_jobs.json and planner.json)
set PLANNER_EDIT_PASSWORD=test
streamlit run app.py
```
