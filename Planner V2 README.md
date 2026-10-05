# AES Transport Planner V4.3

Version 4.3, 5 October 2026. V4.3: runs split on bed space, keeping the order; Auto Split Runs and Auto Split All; each run says why it ends. V4.2: fleet revenue, margin and profit per job count every booked job in the period, planned or not; driver rows count planned loads only. V4.1: the MD dashboard is behind a four digit PIN (md_pin in costs.json, checked on the server); cost and revenue follow the PIN rather than Team Edit. V4.0: profit per job (period margin over planned jobs) per driver and for the fleet. V3.9: the bar column on the MD table removed. V3.8: revenue is the price on the job itself (its sale lines in Big Change, Ken V20.8), invoice total once raised; no estimates. V3.7: costs.json in the app folder is copied to data/costs.json on every push. V3.6: the cost basis is `data/costs.json` in the repo. V3.5: revenue per wagon from the prices on the feed (Ken V20.6: invoiced total, or the rate card estimate until invoiced). V3.4: cost per wagon per day on the MD dashboard (Team Edit only), rates in the secrets under [aes_costs]; revenue per day fills in when the feed carries prices. V3.3: the MD (Mother Delta Dashboard) button and in-app dashboard; runs fixed to be per week as well as per weekday. V3.2: fuel cards get the oil slick finish (black with a purple, teal and amber swirl, wet highlight, dark base). V3.1: fuel deliveries (Big Change job type "Fuel Delivery", Ken V20.2) as black glossy cards in the deliveries lane, planned like a delivery with no bed length counted. V3.0: sixteen weeks ahead (five sliding tabs, arrows through all of them, Jump To Week is a list); Ken's feed window is 16 weeks. V2.9: Ken checks Big Change every two minutes; the header goes red after six. V2.8: mileage shows only in the day view; a postcode counts once per run however many loads go there. V2.7: run and driver mileage in the day view (each run is depot, sites in run order, back to depot; the driver total adds the runs up), from the postcode distance matrix Ken V19.5 writes into the feed. V2.6: road miles from the depot (M46 9BE, one way) on the week card, the day view load pills and the job card, from the "miles" field Ken V19.4 puts on every feed card. V2.5: in Team Edit a job card's RUN column has a driver and run number picker per load, plus a Whole Job row, so CR1 or DF3 can be set from the card; it writes the same run entry the day view uses, so the day view shows it and can still reorder it. V2.4: the header shows "Big Change Checked X Mins Ago" from `data/feed_heartbeat.json`, which Ken (V19.3 and later) writes after every check whether or not the jobs changed; the hint next to Vehicles & Holidays has gone; CONVERTED is purple; the holidays and vehicle bookings panel lists only the week on show, with a count of any others. V2.3: in Team Edit, cards on the week view can be dragged up and down within a day's lane; the order is saved per day and lane and changes nothing but the display. V2.2: enquiries convert on their own on every page load (no Confirm or Dismiss), an enquiry is deleted only from its edit form, labels in Title Case.

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

```

The cost basis for the MD dashboard is `costs.json` beside this file; the push script copies it to `data/costs.json` in the repo on every push, so edit it here and run the script. `[aes_costs]` in the secrets is only a fallback if that file is missing.

The Hiabs do 12 mpg (Nathan, 29/09/2026); 30 for the 4x4 and 15 for the 7.5t are placeholders until known; change them in `data/costs.json` and the dashboard follows on the next load. The 7.5t wagon YG17 FCJ (£50 a week depreciation) sits under `_unassigned_vehicles`; move it under `vehicles` with the driver's initials to cost it.

The token is a classic personal access token with the `repo` scope, on an account that is a collaborator on this repo.

## First run

If `data/planner.json` does not exist, the app reads the Google Sheet once and writes it: enquiries carry over, booked jobs that Big Change now holds hand their driver codes to run entries, holidays, vehicle bookings and capacity days become date ranged. A report shows at the top of the page until someone hides it. The Sheet is never written.

## Rules the front end enforces

- Every load is allocated on its own; a drop lands in front of the first card whose midpoint is below the pointer, or at the end of the run.
- Deliveries always before collections on a run; a site move orders like a collection; a fuel delivery orders like a delivery and takes no bed length.
- Bed space (Nathan, 05/10/2026): a run leaves the depot carrying its deliveries; each drop frees that unit's length; each collection takes its length; a delivery after a collection means back to the depot. More than one collection is fine while they fit. Unit length is read from the load description ("20ft"); a load with no length counts as 0 and the bed line says how many are unsized.
- Run breaks: when a load lands on a run that cannot carry it, the planner starts the next run at that point, in the same order, and says so. Breaks the office makes are kept ("ENDS: Office break"). Auto Split Runs re-packs one driver's day from scratch in order, removing breaks that are not needed; Auto Split All does every driver for the day. Each run shows why it ends: back to the depot to load, next delivery would not fit, collection filled the bed, bed full for the next collection, or office break. The bed line shows the most the bed carries on that run. SUB has no bed check and is never split.
- Enquiries can never be put on a run. Matches from Ken, sure and likely, convert on their own on every page load.
- Mileage (day view only): each run shows its round trip, depot to each site in the order first reached and back to the depot, a postcode counted once per run; the driver header totals the runs, each out from the depot. Load pills show one way miles from the depot. A plus after a figure means a leg could not be measured. Figures come from Ken's feed (postcodes.io and OSRM, cached).
- Run from the card: in Team Edit, open a booked job and pick a driver and run number per load (or for the whole job). None takes the load off its run. Deliveries slot ahead of collections on that run; the day view shows the result and can reorder it.
- Week view card order: in Team Edit a card can be dragged above or below another card in the same day and lane (top half of the target lands before it, bottom half after). It is saved in `card_order` and affects nothing but the display.
- A job Big Change moved keeps its run for the old day and shows MOVED until it is re-planned. A job Big Change dropped is listed under the day for 7 days.
- SUB is the sub-contractor column: SUB1, SUB2, one run per subbie wagon, no bed check.

## MD: Mother Delta Dashboard

Placement and trigger: the black MD button at the right of the header, left of TEAM EDIT and READ ONLY, visible in both modes. Click asks for the four digit PIN (`md_pin` in `costs.json`; `PLANNER_MD_PIN` or `md_pin` in the secrets override it). The PIN is checked by `app.py`, never sent to the browser, and the cost basis only goes to the page once it has been accepted. Unlocked lasts for that browser session; LOCK on the dashboard locks it again. CLOSE, the backdrop or Escape closes the panel. Auto refresh does not close it.

Data: nothing is fetched. Every figure is computed in the front end from what the page already holds: feed cards (`data/bigchange_jobs.json`, with each card's `pc_key` and the `distance` matrix Ken writes), the runs in `data/planner.json` and the drivers list. A run's miles are depot to each site in run order and back, a postcode counted once per run (the same `runMiles` the day view shows).

Period: a selector, Week On Show (default), Next 4 Weeks, All 18 Weeks Loaded. The feed holds from yesterday forward, so past weeks are not there yet.

Metrics, initial set:

- Fleet Miles: sum of every planned run's miles in the period. A plus means a leg could not be measured.
- Days With Runs: day slots (Mon to Fri plus the Sat/Sun slot) with at least one planned run.
- Average Miles Per Day: fleet miles divided by days with runs.
- Drivers Active: drivers with at least one planned run.
- Per driver table: days with a run, runs, loads, miles, average miles per day (miles over that driver's days). Sorted by miles.

Money (behind the MD PIN, from `data/costs.json`):

- Cost per wagon day = driver hourly rate × hours per day + weekly lease ÷ working days per week + fuel (miles ÷ mpg × 4.546 × price per litre). Wages and leases count on every working day in the period whether or not a run is planned; fuel follows the miles planned.
- Wagon Cost, Period: the sum across drivers with a cost basis. Cost Per Wagon Day: that over working days and wagons.
- Revenue per day: the `price` Ken puts on each load, summed over the driver's planned loads and spread over the working days. The price is the job's own sale lines in Big Change (quantity × unit selling price, from `GET /jobs/{id}/lineItems`, there from booking), replaced by the invoiced total ex VAT once an invoice exists (`price_source` is `job` or `invoice`). A load with neither adds nothing and is counted as having no price.
- Margin = revenue less cost, per day and for the period.
- Fleet revenue (and so the fleet margin and profit per job) counts every booked job in the period whether or not it is on a run yet; the tile says how much of it is on runs so far. The driver rows count only the loads planned onto that driver's runs.
- Profit per job = the period margin divided by the jobs: all booked jobs for the fleet, planned loads for a driver. Because wages and leases count every working day, a lightly planned period shows a loss per job that shrinks as the week fills.
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
