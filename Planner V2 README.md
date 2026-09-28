# AES Transport Planner V2.4

Version 2.4, 28 September 2026. V2.4: the header shows "Big Change Checked X Mins Ago" from `data/feed_heartbeat.json`, which Ken (V19.3 and later) writes after every check whether or not the jobs changed; the hint next to Vehicles & Holidays has gone; CONVERTED is purple; the holidays and vehicle bookings panel lists only the week on show, with a count of any others. V2.3: in Team Edit, cards on the week view can be dragged up and down within a day's lane; the order is saved per day and lane and changes nothing but the display. V2.2: enquiries convert on their own on every page load (no Confirm or Dismiss), an enquiry is deleted only from its edit form, labels in Title Case.

Jobs come from Big Change. Ken checks every ten minutes, writes `data/bigchange_jobs.json` in this repo when the jobs changed and `data/feed_heartbeat.json` every time; the app reads both and never edits them. The app owns `data/planner.json`: runs (keyed by Big Change job id), run start times, capacity days, holidays, vehicle bookings, enquiries, conversions and the week view card order. Both files are read and written through the GitHub contents API.

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
- Enquiries can never be put on a run. Matches from Ken, sure and likely, convert on their own on every page load.
- Week view card order: in Team Edit a card can be dragged above or below another card in the same day and lane (top half of the target lands before it, bottom half after). It is saved in `card_order` and affects nothing but the display.
- A job Big Change moved keeps its run for the old day and shows MOVED until it is re-planned. A job Big Change dropped is listed under the day for 7 days.
- SUB is the sub-contractor column: SUB1, SUB2, one run per subbie wagon, no bed check.

## Local test

```
set PLANNER_LOCAL_DATA=C:\some\folder      (holds bigchange_jobs.json and planner.json)
set PLANNER_EDIT_PASSWORD=test
streamlit run app.py
```
