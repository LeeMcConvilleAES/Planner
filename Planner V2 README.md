# AES Transport Planner V3.4

Version 3.4, 29 September 2026. V3.4: cost per wagon per day on the MD dashboard (Team Edit only), rates in the secrets under [aes_costs]; revenue per day fills in when the feed carries prices. V3.3: the MD (Mother Delta Dashboard) button and in-app dashboard; runs fixed to be per week as well as per weekday. V3.2: fuel cards get the oil slick finish (black with a purple, teal and amber swirl, wet highlight, dark base). V3.1: fuel deliveries (Big Change job type "Fuel Delivery", Ken V20.2) as black glossy cards in the deliveries lane, planned like a delivery with no bed length counted. V3.0: sixteen weeks ahead (five sliding tabs, arrows through all of them, Jump To Week is a list); Ken's feed window is 16 weeks. V2.9: Ken checks Big Change every two minutes; the header goes red after six. V2.8: mileage shows only in the day view; a postcode counts once per run however many loads go there. V2.7: run and driver mileage in the day view (each run is depot, sites in run order, back to depot; the driver total adds the runs up), from the postcode distance matrix Ken V19.5 writes into the feed. V2.6: road miles from the depot (M46 9BE, one way) on the week card, the day view load pills and the job card, from the "miles" field Ken V19.4 puts on every feed card. V2.5: in Team Edit a job card's RUN column has a driver and run number picker per load, plus a Whole Job row, so CR1 or DF3 can be set from the card; it writes the same run entry the day view uses, so the day view shows it and can still reorder it. V2.4: the header shows "Big Change Checked X Mins Ago" from `data/feed_heartbeat.json`, which Ken (V19.3 and later) writes after every check whether or not the jobs changed; the hint next to Vehicles & Holidays has gone; CONVERTED is purple; the holidays and vehicle bookings panel lists only the week on show, with a count of any others. V2.3: in Team Edit, cards on the week view can be dragged up and down within a day's lane; the order is saved per day and lane and changes nothing but the display. V2.2: enquiries convert on their own on every page load (no Confirm or Dismiss), an enquiry is deleted only from its edit form, labels in Title Case.

Jobs come from Big Change. Ken checks every two minutes, writes `data/bigchange_jobs.json` in this repo when the jobs changed and `data/feed_heartbeat.json` every time; the app reads both and never edits them. The app owns `data/planner.json`: runs (keyed by Big Change job id), run start times, capacity days, holidays, vehicle bookings, enquiries, conversions and the week view card order. Both files are read and written through the GitHub contents API.

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

# Cost basis for the MD dashboard. Never in the repo; only sent to the page in Team Edit.
[aes_costs]
fuel_price_per_litre = 1.55
hours_per_day = 9
working_days_per_week = 5

[aes_costs.drivers]
DF = 17.50
RB = 16.75
CR = 16.75
DB = 16.00
RS = 14.50
SL = 16.75

[aes_costs.vehicles.DF]
reg = "YK25 CXE"
lease_per_week = 1350
mpg = 9
note = "HGV Hiab"

[aes_costs.vehicles.SL]
reg = "MV75 BXZ"
lease_per_week = 1450
mpg = 9
note = "HGV Hiab"

[aes_costs.vehicles.CR]
reg = "BV73 EWG"
lease_per_week = 950
mpg = 9
note = "HGV Hiab"

[aes_costs.vehicles.RB]
reg = "FJ74 YYD"
lease_per_week = 1350
mpg = 9
note = "HGV Hiab"

[aes_costs.vehicles.RS]
reg = "PN74 NCZ"
lease_per_week = 187.50
mpg = 30
note = "4x4"
```

The mpg figures are placeholders (9 for an HGV Hiab, 30 for the 4x4, 15 for the 7.5t) until real consumption is known; change them in the secrets and the dashboard follows on the next load. The 7.5t wagon YG17 FCJ (£50 a week depreciation) is not assigned to a driver here; add `[aes_costs.vehicles.XX]` for whoever drives it.

The token is a classic personal access token with the `repo` scope, on an account that is a collaborator on this repo.

## First run

If `data/planner.json` does not exist, the app reads the Google Sheet once and writes it: enquiries carry over, booked jobs that Big Change now holds hand their driver codes to run entries, holidays, vehicle bookings and capacity days become date ranged. A report shows at the top of the page until someone hides it. The Sheet is never written.

## Rules the front end enforces

- Every load is allocated on its own; a drop lands in front of the first card whose midpoint is below the pointer, or at the end of the run.
- Deliveries always before collections on a run; a site move orders like a collection; a fuel delivery orders like a delivery and takes no bed length.
- Enquiries can never be put on a run. Matches from Ken, sure and likely, convert on their own on every page load.
- Mileage (day view only): each run shows its round trip, depot to each site in the order first reached and back to the depot, a postcode counted once per run; the driver header totals the runs, each out from the depot. Load pills show one way miles from the depot. A plus after a figure means a leg could not be measured. Figures come from Ken's feed (postcodes.io and OSRM, cached).
- Run from the card: in Team Edit, open a booked job and pick a driver and run number per load (or for the whole job). None takes the load off its run. Deliveries slot ahead of collections on that run; the day view shows the result and can reorder it.
- Week view card order: in Team Edit a card can be dragged above or below another card in the same day and lane (top half of the target lands before it, bottom half after). It is saved in `card_order` and affects nothing but the display.
- A job Big Change moved keeps its run for the old day and shows MOVED until it is re-planned. A job Big Change dropped is listed under the day for 7 days.
- SUB is the sub-contractor column: SUB1, SUB2, one run per subbie wagon, no bed check.

## MD: Mother Delta Dashboard

Placement and trigger: the black MD button at the right of the header, left of TEAM EDIT and READ ONLY, visible in both modes. Click opens the dashboard as an in-app panel (same overlay as the job card); CLOSE, the backdrop or Escape closes it. Auto refresh does not close it.

Data: nothing is fetched. Every figure is computed in the front end from what the page already holds: feed cards (`data/bigchange_jobs.json`, with each card's `pc_key` and the `distance` matrix Ken writes), the runs in `data/planner.json` and the drivers list. A run's miles are depot to each site in run order and back, a postcode counted once per run (the same `runMiles` the day view shows).

Period: a selector, Week On Show (default), Next 4 Weeks, All 18 Weeks Loaded. The feed holds from yesterday forward, so past weeks are not there yet.

Metrics, initial set:

- Fleet Miles: sum of every planned run's miles in the period. A plus means a leg could not be measured.
- Days With Runs: day slots (Mon to Fri plus the Sat/Sun slot) with at least one planned run.
- Average Miles Per Day: fleet miles divided by days with runs.
- Drivers Active: drivers with at least one planned run.
- Per driver table: days with a run, runs, loads, miles, average miles per day (miles over that driver's days), and a bar scaled to the top driver. Sorted by miles.

Money (Team Edit only, from `[aes_costs]` in the secrets):

- Cost per wagon day = driver hourly rate × hours per day + weekly lease ÷ working days per week + fuel (miles ÷ mpg × 4.546 × price per litre). Wages and leases count on every working day in the period whether or not a run is planned; fuel follows the miles planned.
- Wagon Cost, Period: the sum across drivers with a cost basis. Cost Per Wagon Day: that over working days and wagons.
- Revenue per day: the `price` (invoiced) or `est_price` (rate card) Ken puts on each load, summed over the driver's planned loads and spread over the working days. Shows "awaiting feed" until the feed carries prices.
- Margin = revenue less cost, per day and for the period.
- Not included: overtime beyond the base day, employer NI, pension, insurance, tyres, servicing.

Only loads on a run count; loads not yet planned add nothing. Subcontractor runs (SUB) are included as a driver row.

Adding a metric: extend `mdStats()` in `planner_ui/index.html` with the number, then add a tile (`tile(label, value, sub)`) or a table column in `renderMd()`. Per driver figures go on the row objects; fleet figures on `fleet`. When a metric needs data the page does not hold (past weeks, Big Change job fields not on the cards), Ken writes it into the feed or a new file in `data/` and `app.py` passes it into the component as another argument; the dashboard stays baked into the app.

Accessibility: the panel is a dialog with an aria label, the period selector is a labelled select, and the table is a real table with header cells. Errors: a missing distance matrix gives "+" marks rather than a failure; no runs gives a plain message.

## Local test

```
set PLANNER_LOCAL_DATA=C:\some\folder      (holds bigchange_jobs.json and planner.json)
set PLANNER_EDIT_PASSWORD=test
streamlit run app.py
```
