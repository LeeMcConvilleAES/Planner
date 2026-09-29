"""AES Transport Planner
Version 3.0

3.0: sixteen weeks ahead. The week strip shows five tabs that slide around
the week on show (last week through week 16), the arrows walk through all
of them and Jump To Week is a real list. Ken's feed window is 16 weeks too
(aes_planner_feed.days_ahead 115 in his config, 29/09/2026).

2.9: Ken now checks Big Change every two minutes (config, 29/09/2026), so the
header goes red when a check is more than six minutes old, and the wording
says two minutes.

2.8: mileage only in the day view (no badge on the week cards or the job
card). A postcode counts once per run however many loads go there, in the
order it is first reached.

2.7: run and driver mileage in the day view. Each run is depot to the first
site, site to site in run order, and back to the depot; the driver total is
every run added up. The figures come from the postcode distance matrix Ken
V19.5 writes into the feed ("distance"). A leg that could not be measured
shows as a plus after the total.

2.6: road miles from the depot. Ken V19.4 puts "miles" (one way, by road,
from M46 9BE) on every feed card; the week card, the load pills in the day
view and the job card all show it. A card without a figure shows nothing.

2.5: in Team Edit a job card's RUN column has a driver and run number picker
per load (and a Whole Job row), so CR1 or DF3 can be set without opening the
day view. It writes the same run entry the day view does, so the day view
shows it and can still reorder it.

2.4: the header says "Big Change Checked X Mins Ago" from the heartbeat Ken
writes after every check (data/feed_heartbeat.json, Ken V19.3), not from the
age of the last change to the jobs file, which read as stale on a quiet
afternoon. The hint next to Vehicles & Holidays has gone, CONVERTED is purple,
and the holidays and vehicle bookings panel lists the week on show only.

2.3: in Team Edit the office can drag cards up and down a day's lane on the
week view. The order is kept in planner.json (card_order) per day and lane and
changes nothing else: not runs, not Big Change.

2.2: enquiries convert on their own. Every load of the page applies the
matches Ken lists in the feed, sure and likely alike, and writes planner.json,
so nobody has to be in Team Edit for it to happen and there is no Confirm or
Dismiss. An enquiry is deleted only from inside its edit form. Labels are in
Title Case.

2.1: the password box sits in the planner header, the migration report is
no longer shown on the page (it stays in planner.json), and clicking a card
views a Big Change job or edits an enquiry.

2.0: jobs come from Big Change, data lives in the Planner repo, the office plans
runs on the v1.6 design.

Ken checks Big Change every two minutes and writes data/bigchange_jobs.json when it changed: every AES transport job
as a planner card, keyed by date. This app reads it and never edits it. The app
owns data/planner.json: runs (keyed by Big Change job id), run start times,
capacity days, holidays, vehicle bookings, enquiries and enquiry conversions.
Both files sit in this repo and are read and written through the GitHub
contents API with a token in Streamlit secrets.

The front end is planner_ui/index.html, a Streamlit component with no build
step: the page posts its state back through the component protocol whenever
the office changes something, and this shell writes planner.json.

First run: when data/planner.json does not exist yet, the old Google Sheet blob
is read once and migrated. Enquiries carry over as enquiries, booked jobs that
Big Change now holds hand their driver codes to run entries, holidays, vehicle
bookings and capacity days become date ranged, and anything that could not be
placed is listed on screen. The Sheet is never written.

Secrets (Streamlit Cloud, Settings, Secrets):
  edit_password = "..."
  [github]
  token = "ghp_..."            # classic token with the repo scope
  repo = "LeeMcConvilleAES/Planner"
  branch = "main"
  [gcp_service_account]        # only until the migration has run
  ...
"""
import json
import os
import re
import time
import base64
import hashlib
from datetime import date, datetime, timedelta
from pathlib import Path

import requests
import streamlit as st
import streamlit.components.v1 as components

VERSION = "3.0"
HERE = Path(__file__).resolve().parent
FEED_PATH = "data/bigchange_jobs.json"
PLANNER_PATH = "data/planner.json"
HEARTBEAT_PATH = "data/feed_heartbeat.json"   # Ken writes it after every Big Change check
LOCAL_DATA_DIR = os.environ.get("PLANNER_LOCAL_DATA")   # tests: read and write files here, no GitHub
DAY_LABELS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Sat/Sun"]

# Drivers on AES transport jobs in Big Change, 28/09/2026, with the wagon each
# drove most. The office edits this list in the app; this is only the seed.
SEED_RESOURCES = [
    {"ini": "CR", "name": "Colin Rogers", "reg": "BV73 EWG"},
    {"ini": "DF", "name": "Darren Fishwick", "reg": "YK25 CXE"},
    {"ini": "RB", "name": "Rob Brown", "reg": "FJ74 YYD"},
    {"ini": "RS", "name": "Rob Sawyer", "reg": "FJ74 YYD"},
    {"ini": "SL", "name": "Ste Longworth", "reg": "MV75 BXZ"},
    {"ini": "DB", "name": "Danny Ball", "reg": "J25 AES"},
    {"ini": "AU", "name": "Alan Unsworth", "reg": "PN25 FKS"},
    {"ini": "SUB", "name": "Sub-Contractor", "reg": "", "sub": True},
]
SEED_VEHICLES = [
    {"reg": "BV73 EWG", "driver": "CR", "bed_ft": 32, "note": ""},
    {"reg": "YK25 CXE", "driver": "DF", "bed_ft": 32, "note": ""},
    {"reg": "FJ74 YYD", "driver": "RB", "bed_ft": 32, "note": "also Rob Sawyer"},
    {"reg": "MV75 BXZ", "driver": "SL", "bed_ft": 32, "note": ""},
    {"reg": "J25 AES", "driver": "DB", "bed_ft": 32, "note": ""},
    {"reg": "PN25 FKS", "driver": "AU", "bed_ft": 32, "note": ""},
]

st.set_page_config(page_title="AES Transport Planner", page_icon="🚛", layout="wide",
                   initial_sidebar_state="collapsed")


def now_uk():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Europe/London"))
    except Exception:                                            # noqa: BLE001
        return datetime.now()


def empty_planner():
    return {"version": 1, "updated_at": "", "updated_by": "", "resources": SEED_RESOURCES,
            "vehicles": SEED_VEHICLES, "runs": {}, "run_starts": {}, "capacity": [],
            "holidays": [], "vehicle_bookings": [], "enquiries": [], "conversions": {},
            "dismissed_matches": [], "card_notes": {}, "card_order": {}, "migration": None}


# ===== GitHub
def gh_conf():
    g = st.secrets.get("github", {}) if hasattr(st, "secrets") else {}
    return {"token": g.get("token", ""), "repo": g.get("repo", "LeeMcConvilleAES/Planner"),
            "branch": g.get("branch", "main")}


def gh_headers():
    return {"Authorization": f"Bearer {gh_conf()['token']}", "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"}


def read_file(path):
    """(parsed JSON, sha) for a file in the repo, (None, None) when it is not there."""
    if LOCAL_DATA_DIR:
        p = Path(LOCAL_DATA_DIR) / Path(path).name
        if not p.exists():
            return None, None
        raw = p.read_text("utf-8")
        return json.loads(raw), hashlib.sha1(raw.encode()).hexdigest()
    c = gh_conf()
    if not c["token"]:
        raise RuntimeError("No GitHub token in secrets ([github] token).")
    r = requests.get(f"https://api.github.com/repos/{c['repo']}/contents/{path}",
                     params={"ref": c["branch"]}, headers=gh_headers(), timeout=30)
    if r.status_code == 404:
        return None, None
    r.raise_for_status()
    body = r.json()
    raw = base64.b64decode(body.get("content") or "").decode("utf-8")
    return json.loads(raw) if raw.strip() else None, body.get("sha")


def write_file(path, obj, sha, message):
    """Write a JSON file with its sha; on a 409 re-read the sha once and retry."""
    raw = json.dumps(obj, indent=1, ensure_ascii=False)
    if LOCAL_DATA_DIR:
        p = Path(LOCAL_DATA_DIR) / Path(path).name
        p.write_text(raw, "utf-8")
        return hashlib.sha1(raw.encode()).hexdigest()
    c = gh_conf()
    url = f"https://api.github.com/repos/{c['repo']}/contents/{path}"
    payload = {"message": message, "content": base64.b64encode(raw.encode("utf-8")).decode(),
               "branch": c["branch"]}
    if sha:
        payload["sha"] = sha
    for attempt in range(2):
        r = requests.put(url, json=payload, headers=gh_headers(), timeout=60)
        if r.status_code in (200, 201):
            return r.json()["content"]["sha"]
        if r.status_code in (409, 422) and attempt == 0:
            _cur, fresh = read_file(path)
            if fresh:
                payload["sha"] = fresh
            continue
        raise RuntimeError(f"GitHub refused the write to {path}: HTTP {r.status_code} {r.text[:200]}")
    raise RuntimeError(f"GitHub refused the write to {path} twice")


# ===== Google Sheet (migration only)
def read_sheet_blob():
    """The old planner blob, or None when the Sheet is not configured or empty."""
    if os.environ.get("PLANNER_LOCAL_SHEET"):                    # tests: a blob in a file
        p = Path(os.environ["PLANNER_LOCAL_SHEET"])
        return json.loads(p.read_text("utf-8")) if p.exists() else None
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        creds_dict = dict(st.secrets["gcp_service_account"])
    except Exception:                                            # noqa: BLE001
        return None
    try:
        creds = Credentials.from_service_account_info(
            creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets",
                                "https://www.googleapis.com/auth/drive"])
        sheet = gspread.authorize(creds).open("AES Transport Planner").sheet1
        val = sheet.cell(1, 1).value
        return json.loads(val) if val and val.strip() else None
    except Exception as e:                                       # noqa: BLE001
        st.session_state["sheet_error"] = str(e)
        return None


def _norm_pc(s):
    return re.sub(r"\s+", "", str(s or "").upper())


def _cust_key(name):
    words = re.sub(r"[^a-z0-9 ]", " ", str(name or "").lower()).split()
    stop = {"ltd", "limited", "plc", "llp", "the", "and", "co", "company", "group", "uk"}
    return " ".join(w for w in words if w not in stop)


def _day_iso(monday_iso, di):
    try:
        m = date.fromisoformat(monday_iso)
    except (TypeError, ValueError):
        return None
    return (m + timedelta(days=min(max(int(di), 0), 5))).isoformat()


def migrate_from_sheet(blob, feed, planner):
    """Fold the old Sheet blob into a fresh planner.json. Pure, for testing.
    Returns (planner, report lines)."""
    report = []
    cards_by_day = feed.get("jobs", {}) if feed else {}
    ini_by_name = {}
    for r in planner["resources"]:
        if r.get("sub"):
            continue
        parts = r["name"].lower().split()
        ini_by_name[r["name"].lower()] = r["ini"]
        ini_by_name[parts[-1]] = r["ini"]                        # surname
        ini_by_name[r["ini"].lower()] = r["ini"]
    known_codes = {r["ini"] for r in planner["resources"]}
    today = now_uk().date()
    n_match = n_runs = n_enq = n_unplaced = n_hol = n_veh = 0
    unplaced_codes = set()
    for wk, wd in (blob.get("weeks") or {}).items():
        for j in (wd or {}).get("jobs", []) or []:
            day_iso = _day_iso(wk, j.get("day", 0))
            if not day_iso or date.fromisoformat(day_iso) < today - timedelta(days=1):
                continue
            kind = "col" if str(j.get("col", "")).lower().startswith("col") else "del"
            status = str(j.get("status", "")).lower()
            items = [str(l.get("desc", "")).strip() for l in (j.get("loads") or []) if str(l.get("desc", "")).strip()]
            if status == "enquiry":
                planner["enquiries"].append({
                    "id": f"e-{j.get('id') or len(planner['enquiries'])}", "day": day_iso, "col": kind,
                    "customer": j.get("customer", ""), "postcode": str(j.get("postcode", "")).upper(),
                    "po": "", "items": items or ["(no items)"], "notes": j.get("notes", ""),
                    "created_at": now_uk().isoformat(timespec="seconds"), "created_by": "migration"})
                n_enq += 1
                continue
            # a booked job: find the feed card for the same day, kind, and postcode or customer
            cands = [c for c in cards_by_day.get(day_iso, []) if c.get("col") == kind]
            pc, ck = _norm_pc(j.get("postcode")), _cust_key(j.get("customer"))
            hit = [c for c in cands if pc and _norm_pc(c.get("postcode")) == pc] or \
                  [c for c in cands if ck and _cust_key(c.get("customer")) == ck]
            if not hit:
                planner["enquiries"].append({
                    "id": f"e-{j.get('id') or len(planner['enquiries'])}", "day": day_iso, "col": kind,
                    "customer": j.get("customer", ""), "postcode": str(j.get("postcode", "")).upper(),
                    "po": "", "items": items or ["(no items)"],
                    "notes": ("Not in Big Change. " + str(j.get("notes", ""))).strip(),
                    "created_at": now_uk().isoformat(timespec="seconds"), "created_by": "migration"})
                n_enq += 1
                report.append(f"{day_iso} {j.get('customer')} {j.get('postcode')}: booked in the Sheet but not in Big Change, kept as an enquiry")
                continue
            n_match += 1
            card = hit[0]
            loads = card.get("loads", [])
            for li, l in enumerate(j.get("loads") or []):
                m = re.match(r"^([A-Z]+?)(\d+)$", str(l.get("driver") or "").strip().upper())
                if not m:
                    continue
                if m.group(1) not in known_codes:
                    unplaced_codes.add(m.group(1)); n_unplaced += 1
                    continue
                if li >= len(loads):
                    report.append(f"{day_iso} {card.get('customer')}: the Sheet had more loads than Big Change ({len(j.get('loads') or [])} vs {len(loads)}), code {l.get('driver')} not placed")
                    continue
                bid = str(loads[li].get("bigchange_id"))
                planner["runs"][bid] = {"day": day_iso, "driver": m.group(1), "run": int(m.group(2)), "seq": li + 1}
                n_runs += 1
        for h in (wd or {}).get("holidays", []) or []:
            name = str(h.get("name", "")).strip()
            ini = ini_by_name.get(name.lower()) or ini_by_name.get(name.lower().split()[-1] if name else "", None)
            days = sorted(int(d) for d in (h.get("days") or []) if str(d).isdigit())
            if not ini or not days:
                report.append(f"week {wk}: holiday '{name}' not migrated ({'no driver match' if not ini else 'no days'}), re-enter by hand")
                continue
            planner["holidays"].append({"id": f"h-{wk}-{ini}", "driver": ini,
                                        "from": _day_iso(wk, days[0]), "to": _day_iso(wk, days[-1])})
            n_hol += 1
        for v in (wd or {}).get("vehicles", []) or []:
            reg, di, note = str(v.get("reg", "")).strip().upper(), v.get("day", 0), str(v.get("note", "")).upper()
            if not reg:
                continue
            typ = "MOT" if "MOT" in note else "REPAIR" if "REPAIR" in note else "TEST" if "TEST" in note else "SERVICE"
            full = [x for x in planner["vehicles"] if x["reg"].replace(" ", "").endswith(reg.replace(" ", ""))]
            planner["vehicle_bookings"].append({"id": f"v-{wk}-{reg}", "reg": full[0]["reg"] if full else reg, "type": typ,
                                                "driver": full[0]["driver"] if full else "",
                                                "from": _day_iso(wk, di), "to": _day_iso(wk, di)})
            n_veh += 1
        for di in (wd or {}).get("capacity", []) or []:
            iso = _day_iso(wk, di)
            if iso and iso not in planner["capacity"]:
                planner["capacity"].append(iso)
    # deliveries first, then the Sheet's order, inside every run
    by_run = {}
    for bid, e in planner["runs"].items():
        by_run.setdefault((e["day"], e["driver"], e["run"]), []).append(bid)
    kind_of = {str(l.get("bigchange_id")): c.get("col") for cs in cards_by_day.values() for c in cs for l in c.get("loads", [])}
    for key, bids in by_run.items():
        bids.sort(key=lambda b: (kind_of.get(b) != "del", planner["runs"][b]["seq"]))
        for i, b in enumerate(bids):
            planner["runs"][b]["seq"] = i + 1
    summary = (f"Migrated from the Sheet on {now_uk():%d/%m/%Y %H:%M}: {n_match} booked jobs matched to Big Change, "
               f"{n_runs} run entries, {n_enq} enquiries kept, {n_hol} holidays, {n_veh} vehicle bookings, "
               f"{len(planner['capacity'])} capacity days; {n_unplaced} driver codes not placed"
               + (f" ({', '.join(sorted(unplaced_codes))})" if unplaced_codes else "") + ".")
    planner["migration"] = {"at": now_uk().isoformat(timespec="seconds"), "summary": summary, "report": report}
    return planner, [summary] + report


# ===== loading
def load_all():
    """Both files, migrating once if planner.json does not exist yet."""
    feed, _ = read_file(FEED_PATH)
    planner, sha = read_file(PLANNER_PATH)
    if planner is None:
        planner = empty_planner()
        blob = read_sheet_blob()
        if blob:
            planner, _lines = migrate_from_sheet(blob, feed or {}, planner)
        planner["updated_at"] = now_uk().isoformat(timespec="seconds")
        planner["updated_by"] = "first run"
        sha = write_file(PLANNER_PATH, planner, None, "Planner: first planner.json" + (" (migrated from the Sheet)" if blob else ""))
    for k, v in empty_planner().items():
        planner.setdefault(k, v)
    if apply_enquiry_matches(feed, planner):
        planner["updated_at"] = now_uk().isoformat(timespec="seconds")
        planner["updated_by"] = "ken"
        sha = write_file(PLANNER_PATH, planner, sha, "Planner: enquiries converted from Big Change")
    return feed, planner, sha


def apply_enquiry_matches(feed, planner):
    """Convert every enquiry Ken says Big Change now covers. Pure; returns the
    number converted. The enquiry's notes and items are appended to the card
    as card_notes, and the conversion is recorded so it never repeats."""
    matches = (feed or {}).get("enquiry_matches") or []
    if not matches:
        return 0
    enqs = {q.get("id"): q for q in planner.get("enquiries", []) if isinstance(q, dict)}
    conv = planner.setdefault("conversions", {})
    notes = planner.setdefault("card_notes", {})
    done_cards = {c.get("card") for c in conv.values() if isinstance(c, dict)}
    n = 0
    for m in matches:
        eid, card = m.get("enquiry_id"), m.get("bigchange_card")
        if not eid or not card or eid in conv or eid not in enqs or card in done_cards:
            continue
        q = enqs[eid]
        conv[eid] = {"card": card, "at": now_uk().isoformat(timespec="seconds"), "by": "ken",
                     "level": m.get("level", ""), "why": m.get("why", ""), "enquiry_customer": q.get("customer", "")}
        note = " / ".join(x for x in [q.get("notes", ""), "enquiry: " + ", ".join(q.get("items") or []) if q.get("items") else ""] if x)
        if note:
            notes[card] = " / ".join(x for x in [notes.get(card, ""), note] if x)
        done_cards.add(card)
        n += 1
    if n:
        planner["enquiries"] = [q for q in planner.get("enquiries", []) if not (isinstance(q, dict) and q.get("id") in conv)]
    return n


def get_edit_password():
    try:
        return st.secrets["edit_password"]
    except Exception:                                            # noqa: BLE001
        return os.environ.get("PLANNER_EDIT_PASSWORD", "")


# ===== the page
st.markdown("""<style>
.block-container{padding:0.4rem 0.6rem 0 0.6rem;max-width:100%}
header[data-testid="stHeader"]{height:0;visibility:hidden}
#MainMenu,footer{visibility:hidden}
iframe{border:0}
</style>""", unsafe_allow_html=True)

ss = st.session_state
ss.setdefault("unlocked", False)
ss.setdefault("last_written", None)
ss.setdefault("write_error", None)
ss.setdefault("last_seen_rev", 0)

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=45000 if ss["unlocked"] else 30000, key="refresh")
except Exception:                                                # noqa: BLE001
    pass

try:
    feed, planner, planner_sha = load_all()
    load_error = None
except Exception as e:                                           # noqa: BLE001
    feed, planner, planner_sha, load_error = None, ss.get("planner_cache") or empty_planner(), None, str(e)


def checked_minutes():
    """Whole minutes since Ken last checked Big Change, or None without a heartbeat."""
    try:
        hb, _ = read_file(HEARTBEAT_PATH)
        from datetime import timezone
        at = datetime.fromisoformat(str((hb or {}).get("checked_at", "")).replace("Z", "+00:00"))
        if at.tzinfo is None:
            at = at.replace(tzinfo=timezone.utc)
        return max(0, int((datetime.now(timezone.utc) - at).total_seconds() // 60))
    except Exception:                                            # noqa: BLE001
        return None


checked_min = checked_minutes()
if load_error:
    st.error(f"Could not read the planner data: {load_error}. Showing the last copy this browser had; nothing will be saved until it clears.")
ss["planner_cache"] = planner

notice, notice_kind = "", "info"
if ss["write_error"]:
    notice, notice_kind = ss["write_error"], "error"
elif ss.get("pw_error"):
    notice, notice_kind = ss["pw_error"], "error"
elif ss["last_written"]:
    notice = f"Saved {ss['last_written']:%H:%M:%S}"

_planner_ui = components.declare_component("aes_planner", path=str(HERE / "planner_ui"))
args = {"feed": feed or {}, "planner": planner, "can_edit": ss["unlocked"],
        "today": now_uk().date().isoformat(), "version": VERSION,
        "server_rev": ss["last_seen_rev"], "notice": notice, "notice_kind": notice_kind,
        "checked_min": checked_min}
value = _planner_ui(**args, key="planner_ui", default=None)

if value and isinstance(value, dict) and value.get("rev", 0) > ss["last_seen_rev"] and value.get("action"):
    if value["action"] == "unlock":
        if get_edit_password() and value.get("password") == get_edit_password():
            ss["unlocked"], ss["pw_error"] = True, None
        else:
            ss["pw_error"] = "Wrong password. Viewing is open to everyone."
    elif value["action"] == "lock":
        ss["unlocked"], ss["pw_error"] = False, None
    ss["last_seen_rev"] = value["rev"]
    st.rerun()
if value and isinstance(value, dict) and value.get("rev", 0) > ss["last_seen_rev"] and value.get("planner"):
    if not ss["unlocked"]:
        ss["write_error"] = "That change was not saved: editing is locked."
    else:
        new = value["planner"]
        for k, v in empty_planner().items():
            new.setdefault(k, v)
        new["updated_at"] = now_uk().isoformat(timespec="seconds")
        new["updated_by"] = "office"
        try:
            write_file(PLANNER_PATH, new, planner_sha, f"Planner: {value.get('what', 'office change')}")
            ss["last_written"] = now_uk()
            ss["write_error"] = None
            ss["planner_cache"] = new
        except Exception as e:                                   # noqa: BLE001
            ss["write_error"] = f"Not saved: {e}"
    ss["last_seen_rev"] = value["rev"]
    st.rerun()
