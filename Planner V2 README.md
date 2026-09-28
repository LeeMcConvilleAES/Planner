# AES Transport Planner V2.8

Version 2.8, 28 September 2026. V2.8: mileage shows only in the day view; a postcode counts once per run however many loads go there. V2.7: run and driver mileage in the day view (each run is depot, sites in run order, back to depot; the driver total adds the runs up), from the postcode distance matrix Ken V19.5 writes into the feed. V2.6: road miles from the depot (M46 9BE, one way) on the week card, the day view load pills and the job card, from the "miles" field Ken V19.4 puts on every feed card. V2.5: in Team Edit a job card's RUN column has a driver and run number picker per load, plus a Whole Job row, so CR1 or DF3 can be set from the card; it writes the same run entry the day view uses, so the day view shows it and can still reorder it. V2.4: the header shows "Big Change Checked X Mins Ago" from `data/feed_heartbeat.json`, which Ken (V19.3 and later) writes after every check whether or not the jobs changed; the hint next to Vehicles & Holidays has gone; CONVERTED is purple; the holidays and vehicle bookings panel lists only the week on show, with a count of any others. V2.3: in Team Edit, cards on the week view can be dragged up and down within a day's lane; the order is saved per day and lane and changes nothing but the display. V2.2: enquiries convert on their own on every page load (no Confirm or Dismiss), an enquiry is deleted only from its edit form, labels in Title Case.

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
- Mileage (day view only): each run shows its round trip, depot to each site in the order first reached and back to the depot, a postcode counted once per run; the driver header totals the runs, each out from the depot. Load pills show one way miles from the depot. A plus after a figure means a leg could not be measured. Figures come from Ken's feed (postcodes.io and OSRM, cached).
- Run from the card: in Team Edit, open a booked job and pick a driver and run number per load (or for the whole job). None takes the load off its run. Deliveries slot ahead of collections on that run; the day view shows the result and can reorder it.
- Week view card order: in Team Edit a card can be dragged above or below another card in the same day and lane (top half of the target lands before it, bottom half after). It is saved in `card_order` and affects nothing but the display.
- A job Big Change moved keeps its run for the old day and shows MOVED until it is re-planned. A job Big Change dropped is listed under the day for 7 days.
- SUB is the sub-contractor column: SUB1, SUB2, one run per subbie wagon, no bed check.

## Local test

```
set PLANNER_LOCAL_DATA=C:\some\folder      (holds bigchange_jobs.json and planner.json)
set PLANNER_EDIT_PASSWORD=test
streamlit run app.py
```
