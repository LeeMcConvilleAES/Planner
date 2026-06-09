import streamlit as st
import json
from datetime import datetime, timedelta

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False

st.set_page_config(page_title="AES Transport Planner", page_icon="🚛", layout="wide", initial_sidebar_state="collapsed")

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Sat/Sun']

# ─────────────────────────────────────────────────────────────
# STYLING — match the HTML version exactly
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Figtree',sans-serif!important}
#MainMenu,footer,header[data-testid="stHeader"]{display:none}
.main .block-container{padding:0!important;max-width:100%!important}
.block-container{padding-top:0!important}

.aes-hdr{background:#0d823b;padding:10px 16px;display:flex;align-items:center;justify-content:space-between;border-radius:0}
.aes-hdr-title{color:white;font-weight:700;font-size:15px;letter-spacing:.2px;margin:0}
.aes-hdr-sub{color:rgba(255,255,255,.75);font-size:10px;margin:0}
.mode-tag{background:rgba(255,255,255,.2);border:1px solid rgba(255,255,255,.4);border-radius:5px;padding:4px 12px;color:white;font-size:11px;font-weight:700}

.planner-table{border-collapse:collapse;width:100%;table-layout:fixed;margin-top:6px}
.planner-table th,.planner-table td{border:1px solid #e2e6ea;vertical-align:top}
.day-th{background:#0d823b;color:white;text-align:center;padding:7px 5px;font-weight:700;font-size:12px}
.day-th.wknd{background:#546270}
.day-th small{font-weight:400;opacity:.8;font-size:10px}
.col-sub-th{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;padding:4px 6px;text-align:center}
.del-th{background:#f0fdf4;color:#166534;border-bottom:2px solid #0d823b}
.col-th{background:#eff6ff;color:#1e40af;border-bottom:2px solid #3b82f6}
.veh-row td{background:#fffbeb;font-size:9px;color:#92400e;font-weight:700;padding:3px 8px;text-align:center;border-bottom:1px solid #fde68a}
.jobs-cell{padding:5px;vertical-align:top;min-height:90px}
.jobs-cell.del{background:#fafffe}
.jobs-cell.col{background:#f8faff}

.job{border-radius:5px;padding:5px 7px;margin-bottom:4px;border:1px solid #e2e6ea;background:white}
.job.booked{background:#d1fae5;border-color:#6ee7b7}
.jcust{font-weight:700;font-size:11px;color:#1a2e1a}
.job.enquiry .jcust{color:#40424a}
.jpost{font-size:9px;font-weight:600;color:#065f46;margin-top:2px}
.job.enquiry .jpost{color:#374151}
.jload{font-size:9px;color:#4b5563;font-weight:600;padding:1px 0;display:flex;align-items:center;justify-content:space-between}
.job.booked .jload{color:#065f46}
.dchip{display:inline-block;background:rgba(13,130,59,.15);color:#065f46;border-radius:3px;padding:0 5px;font-size:8px;font-weight:700;min-width:22px;text-align:center;border:1px solid rgba(13,130,59,.2)}
.job.enquiry .dchip{background:rgba(245,158,11,.15);color:#92400e;border-color:rgba(245,158,11,.3)}
.enqb{font-size:7px;font-weight:700;background:#fef3c7;color:#92400e;border:1px solid #fcd34d;border-radius:2px;padding:0 4px;margin-bottom:2px;display:inline-block}
.bkdb{font-size:7px;font-weight:700;background:#059669;color:white;border-radius:2px;padding:0 4px;margin-bottom:2px;display:inline-block}
.jnotes{font-size:8px;color:#9ca3af;font-style:italic;margin-top:2px}
.empty-cell{color:#d1d5db;font-size:9px;text-align:center;padding:10px 4px}

.legend-row{display:flex;align-items:center;gap:14px;padding:6px 4px}
.legend-item{display:flex;align-items:center;gap:5px;font-size:11px}
.legend-sw{width:13px;height:13px;border-radius:3px;border:1px solid rgba(0,0,0,.1)}

div[data-testid="stHorizontalBlock"]{gap:6px}
.stButton button{font-family:'Figtree',sans-serif!important;font-size:11px!important;border-radius:5px!important}
div[data-testid="stMetric"]{background:white;border:1px solid #e2e6ea;border-radius:6px;padding:6px 10px}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# GOOGLE SHEETS
# ─────────────────────────────────────────────────────────────
def get_sheet():
    if not GSPREAD_AVAILABLE:
        return None
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        scopes = ["https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client.open("AES Transport Planner").sheet1
    except Exception:
        return None

def load_data():
    sheet = get_sheet()
    if sheet:
        try:
            val = sheet.cell(1, 1).value
            if val and val.strip():
                return json.loads(val)
        except Exception:
            pass
    return get_default_data()

def save_data(d):
    sheet = get_sheet()
    if sheet:
        try:
            sheet.update_cell(1, 1, json.dumps(d))
            return True
        except Exception:
            return False
    return False

# ─────────────────────────────────────────────────────────────
# WEEK HELPERS
# ─────────────────────────────────────────────────────────────
def get_monday(offset):
    d = datetime.now()
    return (d - timedelta(days=d.weekday()) + timedelta(weeks=offset)).replace(hour=0, minute=0, second=0, microsecond=0)

def week_key(offset):
    return get_monday(offset).strftime('%Y-%m-%d')

def week_range_label(offset):
    mon = get_monday(offset); fri = mon + timedelta(days=4)
    return f"{mon.strftime('%-d %b')} – {fri.strftime('%-d %b %Y')}"

def week_tab_label(offset):
    if offset == 0: return 'This Week'
    if offset == -1: return 'Last Week'
    if offset == 1: return 'Next Week'
    return get_monday(offset).strftime('%-d %b')

def get_day_label(offset, di):
    if di == 5: return 'Sat/Sun'
    return (get_monday(offset) + timedelta(days=di)).strftime('%-d %b')

def get_week_data(data, offset):
    k = week_key(offset)
    if k not in data['weeks']:
        data['weeks'][k] = {'jobs': [], 'vehicles': [], 'holidays': []}
    return data['weeks'][k]

# ─────────────────────────────────────────────────────────────
# DEFAULT SEED DATA
# ─────────────────────────────────────────────────────────────
def get_default_data():
    data = {'weekOffsets': [-1, 0, 1, 2, 3], 'weeks': {}}
    w0 = week_key(0)
    data['weeks'][w0] = {
        'jobs': [
            {'id':'w0-1','customer':'Jones Homes','loads':[{'desc':'Solar Loo','driver':'RS1'}],'postcode':'WA4 3EN','col':'del','day':0,'status':'booked','notes':''},
            {'id':'w0-2','customer':'MBC','loads':[{'desc':'Boss Unit','driver':'RS2'}],'postcode':'M14 4AH','col':'col','day':0,'status':'booked','notes':''},
            {'id':'w0-3','customer':'Wright Build','loads':[{'desc':'Chem Loo','driver':'RS1'}],'postcode':'WN2 4NU','col':'del','day':0,'status':'booked','notes':''},
            {'id':'w0-4','customer':'GreanPower','loads':[{'desc':'20kva','driver':'AP3'}],'postcode':'Etihad','col':'del','day':0,'status':'enquiry','notes':'Awaiting PO'},
            {'id':'w0-5','customer':'A Connolly','loads':[{'desc':'24ft','driver':'DF2'},{'desc':'24ft','driver':'DF3'},{'desc':'24ft','driver':'CR2'},{'desc':'24ft','driver':'CR3'}],'postcode':'L8 0TU–L8 4TF','col':'col','day':0,'status':'booked','notes':'Site Move'},
            {'id':'w0-6','customer':'A Connolly','loads':[{'desc':'24ft','driver':'DF1'},{'desc':'24ft','driver':'IB1'}],'postcode':'WA3 6RG–L8','col':'col','day':0,'status':'booked','notes':'Site Move'},
            {'id':'w0-7','customer':'Stuart Energy','loads':[{'desc':'24ft','driver':''},{'desc':'24ft','driver':''},{'desc':'24ft','driver':''},{'desc':'24ft','driver':''}],'postcode':'WN8 9TB','col':'col','day':0,'status':'booked','notes':''},
            {'id':'w0-8','customer':'Everton FC','loads':[{'desc':'6x Chem Loo','driver':''}],'postcode':'L3 0BW','col':'col','day':0,'status':'booked','notes':''},
            {'id':'w0-9','customer':'A Connolly','loads':[{'desc':'24ft','driver':'CR1'}],'postcode':'WN8 9TB','col':'col','day':0,'status':'booked','notes':'Site Move'},
            {'id':'w0-10','customer':'Event Structures','loads':[{'desc':'20ft','driver':''}],'postcode':'NW1 4NR','col':'del','day':1,'status':'booked','notes':'W&D 2 man'},
            {'id':'w0-11','customer':'Event Structures','loads':[{'desc':'20ft','driver':''}],'postcode':'NN12 8TN','col':'del','day':1,'status':'booked','notes':'W&D 2 man'},
            {'id':'w0-12','customer':'Huyton Gate','loads':[{'desc':'2x Chemi Loo','driver':''},{'desc':'1x Disabled','driver':''}],'postcode':'L34 4AJ','col':'col','day':1,'status':'enquiry','notes':'TBC'},
            {'id':'w0-13','customer':'John Reilly','loads':[{'desc':'10ft Store Exch','driver':'CR2'}],'postcode':'M38 9XE','col':'del','day':2,'status':'booked','notes':''},
            {'id':'w0-14','customer':'HolmePatrick Dev','loads':[{'desc':'24ft','driver':'DF1'},{'desc':'24ft','driver':'AP1'},{'desc':'Staircase','driver':'RB1'}],'postcode':'LA1 3JJ','col':'del','day':2,'status':'booked','notes':''},
            {'id':'w0-15','customer':'Chandos','loads':[{'desc':'24ft','driver':'IB2'}],'postcode':'WA8 3UJ','col':'del','day':2,'status':'booked','notes':''},
            {'id':'w0-16','customer':'Zenex Ltd','loads':[{'desc':'32ft','driver':'DF1'},{'desc':'32ft RB','driver':''}],'postcode':'RG10 0SD','col':'del','day':2,'status':'enquiry','notes':'Confirm vehicle'},
            {'id':'w0-17','customer':'John Reilly','loads':[{'desc':'10ft Store Exch','driver':'CR3'}],'postcode':'M38 9XE','col':'col','day':2,'status':'booked','notes':''},
            {'id':'w0-18','customer':'A Connolly','loads':[{'desc':'24ft','driver':'CR1'}],'postcode':'OL10 3EG','col':'col','day':2,'status':'booked','notes':''},
            {'id':'w0-19','customer':'Perfect Associates','loads':[{'desc':'20ft Store','driver':'IB1'}],'postcode':'SL4 1NJ','col':'col','day':2,'status':'booked','notes':''},
            {'id':'w0-20','customer':'2x Empty IBC','loads':[{'desc':'IBC','driver':'RS1'}],'postcode':'L31 0BP','col':'col','day':2,'status':'booked','notes':''},
            {'id':'w0-21','customer':'M Group','loads':[{'desc':'24ft','driver':'CR1'},{'desc':'32ft','driver':'IB1'},{'desc':'Staircase','driver':'AP1'},{'desc':'Water Barrel x2','driver':'AP1'},{'desc':'HT','driver':'AP1'}],'postcode':'ST10 4LJ','col':'col','day':2,'status':'booked','notes':''},
            {'id':'w0-22','customer':'GreanPower','loads':[{'desc':'40kva','driver':'RB1'}],'postcode':'Trafford Park','col':'col','day':2,'status':'enquiry','notes':''},
            {'id':'w0-23','customer':'Artium','loads':[{'desc':'32ft','driver':'DF1'},{'desc':'32ft','driver':'DF2'},{'desc':'32ft','driver':'RB1'},{'desc':'32ft','driver':'RB2'},{'desc':'32ft','driver':'IB2'},{'desc':'32ft','driver':'IB1'},{'desc':'Staircase','driver':'RS1'},{'desc':'Staircase','driver':'RS1'}],'postcode':'LS9 8EX','col':'del','day':3,'status':'booked','notes':''},
            {'id':'w0-24','customer':'HolmePatrick Dev','loads':[{'desc':'2+1','driver':'CR1'},{'desc':'Smoking Shelter','driver':'CR1'}],'postcode':'LA1 3JJ','col':'del','day':3,'status':'booked','notes':''},
            {'id':'w0-25','customer':'M Group','loads':[{'desc':'24ft off','driver':'AP2'},{'desc':'24ft Can','driver':'IB3'},{'desc':'32ft','driver':'CR2'}],'postcode':'PR8 4QQ','col':'col','day':3,'status':'booked','notes':''},
            {'id':'w0-26','customer':'Redfern Energy','loads':[{'desc':'20ft Store','driver':'CR4'}],'postcode':'M31 4BR','col':'col','day':3,'status':'booked','notes':''},
            {'id':'w0-27','customer':'GreanPower','loads':[{'desc':'60kva','driver':'AP1'}],'postcode':'Cardiff','col':'col','day':3,'status':'booked','notes':''},
            {'id':'w0-28','customer':'Lowbery','loads':[{'desc':'20ft Store','driver':'DF2'}],'postcode':'M31 4AY','col':'del','day':4,'status':'booked','notes':'9-11am'},
            {'id':'w0-29','customer':'MCI Developments','loads':[{'desc':'32ft','driver':'DF1'},{'desc':'32ft','driver':'RB1'},{'desc':'32ft','driver':'IB1'},{'desc':'Staircase','driver':'ROB'}],'postcode':'ST5 6AT','col':'del','day':4,'status':'booked','notes':''},
            {'id':'w0-30','customer':'Rowland Homes','loads':[{'desc':'Boss Unit','driver':''}],'postcode':'PR25 5KP','col':'del','day':4,'status':'enquiry','notes':''},
            {'id':'w0-31','customer':'CLC','loads':[{'desc':'10ft','driver':'CR2'}],'postcode':'L36 2QX','col':'col','day':4,'status':'booked','notes':''},
            {'id':'w0-32','customer':'Pinnington','loads':[{'desc':'24ft','driver':'CR1'}],'postcode':'LA14 5UG','col':'col','day':4,'status':'booked','notes':''},
            {'id':'w0-33','customer':'M Group','loads':[{'desc':'20ft','driver':'RB2'}],'postcode':'FY5 4LH','col':'col','day':4,'status':'booked','notes':''},
            {'id':'w0-34','customer':'Event Structures','loads':[{'desc':'20ft','driver':''}],'postcode':'NN12 8TN','col':'del','day':5,'status':'booked','notes':'Weekend crew'},
            {'id':'w0-35','customer':'MCI Developments','loads':[{'desc':'32ft','driver':''},{'desc':'32ft RB1','driver':''},{'desc':'Staircase','driver':''}],'postcode':'ST5 6AT','col':'col','day':5,'status':'booked','notes':''},
        ],
        'vehicles': [
            {'id':1,'reg':'CXE & DRAG','name':'Scania','day':3,'note':'PMI'},
            {'id':2,'reg':'BXZ','name':'Scania','day':4,'note':'PMI'},
            {'id':3,'reg':'JRO','name':'Bardsley','day':0,'note':'MOT'},
        ],
        'holidays': [{'id':1,'name':'AL Unsworth','days':[1,2,3,4]}]
    }
    w1 = week_key(1)
    data['weeks'][w1] = {
        'jobs': [
            {'id':'w1-1','customer':'H H Smith','loads':[{'desc':'2+1','driver':'CR2'}],'postcode':'SK2 7AF','col':'del','day':0,'status':'booked','notes':''},
            {'id':'w1-2','customer':'H H Smith','loads':[{'desc':'2+1','driver':'IB2'}],'postcode':'M45 7GJ','col':'col','day':0,'status':'booked','notes':''},
            {'id':'w1-3','customer':'M Group','loads':[{'desc':'20ft','driver':''},{'desc':'20ft Store','driver':''},{'desc':'Waste Barrel','driver':''}],'postcode':'LA2 8FG','col':'col','day':1,'status':'booked','notes':''},
            {'id':'w1-4','customer':'A Connolly','loads':[{'desc':'20ft','driver':''},{'desc':'20ft','driver':''}],'postcode':'SK9-OL10','col':'col','day':1,'status':'booked','notes':''},
            {'id':'w1-5','customer':'Event Structure','loads':[{'desc':'20ft','driver':''}],'postcode':'M31 4QZ','col':'col','day':1,'status':'booked','notes':''},
            {'id':'w1-6','customer':'MCC Construction','loads':[{'desc':'32ft','driver':''}],'postcode':'SK12 1NW','col':'del','day':2,'status':'booked','notes':'Pre 7am'},
            {'id':'w1-7','customer':'LCC Highways','loads':[{'desc':'20ft','driver':''},{'desc':'20ft','driver':''},{'desc':'20ft','driver':''}],'postcode':'PR5 4AR','col':'col','day':2,'status':'booked','notes':''},
        ],
        'vehicles': [{'id':1,'reg':'JRO','name':'Bardsley','day':0,'note':'MOT'},{'id':2,'reg':'ZFY','name':'Bardsley','day':3,'note':'PMI'}],
        'holidays': [{'id':1,'name':'AL Unsworth','days':[0,1,2,3,4]}]
    }
    return data

# ─────────────────────────────────────────────────────────────
# JOB CARD HTML
# ─────────────────────────────────────────────────────────────
def job_html(job):
    is_b = job['status'] == 'booked'
    cls = 'job booked' if is_b else 'job enquiry'
    badge = '<span class="bkdb">BOOKED</span>' if is_b else '<span class="enqb">ENQUIRY</span>'
    loads = ''
    for l in job['loads']:
        drv = f'<span class="dchip">{l["driver"]}</span>' if l.get('driver') else ''
        loads += f'<div class="jload"><span>📦 {l.get("desc","—")}</span>{drv}</div>'
    notes = f'<div class="jnotes">{job["notes"]}</div>' if job.get('notes') else ''
    return f'<div class="{cls}">{badge}<div class="jcust">{job["customer"]}</div>{loads}<div class="jpost">📍 {job["postcode"]}</div>{notes}</div>'

# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────
if 'data' not in st.session_state:
    st.session_state.data = load_data()
if 'offset' not in st.session_state:
    st.session_state.offset = 0
if 'mode' not in st.session_state:
    st.session_state.mode = 'readonly'   # everyone starts in view-only
if 'edit_unlocked' not in st.session_state:
    st.session_state.edit_unlocked = False
if 'next_id' not in st.session_state:
    st.session_state.next_id = 5000

data = st.session_state.data
data.setdefault('weekOffsets', [-1, 0, 1, 2, 3])

# Edit is only allowed if the correct password has been entered this session
def get_edit_password():
    try:
        return st.secrets["edit_password"]
    except Exception:
        return "aes2025"   # fallback if no secret set (change via Streamlit secrets)

readonly = (st.session_state.mode == 'readonly') or (not st.session_state.edit_unlocked)

# ── Auto-refresh ONLY in read-only view ──────────────────────
# Refreshes every 30s so viewers always see the latest from the Sheet.
# Session state (incl. edit unlock) survives this, so editors are unaffected.
# We skip it entirely when editing so no one loses what they're typing.
if readonly and AUTOREFRESH_AVAILABLE:
    st_autorefresh(interval=30000, key='ro_refresh')
    # Pull fresh data from the Sheet on each auto-refresh tick
    st.session_state.data = load_data()
    data = st.session_state.data
    data.setdefault('weekOffsets', [-1, 0, 1, 2, 3])

# ─────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────
mode_label = '👁 READ ONLY' if readonly else '✏ TEAM EDIT'
st.markdown(f'''<div class="aes-hdr">
  <div style="display:flex;align-items:center;gap:10px">
    <span style="font-size:22px">🚛</span>
    <div><p class="aes-hdr-title">AINSCOUGH ENVIRONMENTAL SERVICES</p>
    <p class="aes-hdr-sub">Transport Planner</p></div>
  </div>
  <span class="mode-tag">{mode_label}</span>
</div>''', unsafe_allow_html=True)

# Mode toggle
mc1, mc2, mc_sp = st.columns([1.3, 1.3, 9])
with mc1:
    if st.button('✏ Team Edit', type='primary' if not readonly else 'secondary', use_container_width=True):
        st.session_state.mode = 'team'; st.rerun()
with mc2:
    if st.button('👁 Read Only', type='primary' if readonly else 'secondary', use_container_width=True):
        st.session_state.mode = 'readonly'; st.rerun()

# Password gate: if they want Team Edit but haven't unlocked yet, ask for the password
if st.session_state.mode == 'team' and not st.session_state.edit_unlocked:
    with st.container():
        st.warning('🔒 Editing is password protected. Enter the team password to make changes.')
        pc1, pc2, pc_sp = st.columns([2, 1, 7])
        with pc1:
            pw = st.text_input('Edit password', type='password', label_visibility='collapsed', placeholder='Enter password…')
        with pc2:
            if st.button('Unlock', type='primary', use_container_width=True):
                if pw == get_edit_password():
                    st.session_state.edit_unlocked = True
                    st.rerun()
                else:
                    st.error('Incorrect password')
        st.caption('Viewing is open to everyone — only editing requires the password.')

# Show a lock/unlock indicator + logout when unlocked
if st.session_state.edit_unlocked:
    lc1, lc_sp = st.columns([2, 10])
    with lc1:
        if st.button('🔓 Editing unlocked — Lock again', use_container_width=True):
            st.session_state.edit_unlocked = False
            st.session_state.mode = 'readonly'
            st.rerun()

# ─────────────────────────────────────────────────────────────
# WEEK NAVIGATION
# ─────────────────────────────────────────────────────────────
offsets = data['weekOffsets']
nav = st.columns([0.5] + [1.3]*len(offsets) + [0.5, 1.2])
with nav[0]:
    if st.button('‹', use_container_width=True):
        no = st.session_state.offset - 1
        if no not in offsets: offsets.insert(0, no)
        st.session_state.offset = no; st.rerun()
for i, off in enumerate(offsets):
    with nav[i+1]:
        active = off == st.session_state.offset
        if st.button(f"{week_tab_label(off)}\n{week_range_label(off)}", key=f'w{off}',
                     type='primary' if active else 'secondary', use_container_width=True):
            st.session_state.offset = off; st.rerun()
with nav[len(offsets)+1]:
    if st.button('›', use_container_width=True):
        no = st.session_state.offset + 1
        if no not in offsets: offsets.append(no)
        st.session_state.offset = no; st.rerun()
with nav[len(offsets)+2]:
    if st.button('＋ Add Week', use_container_width=True):
        no = max(offsets) + 1
        offsets.append(no); st.session_state.offset = no; st.rerun()

offset = st.session_state.offset
wd = get_week_data(data, offset)
jobs = wd.get('jobs', [])

# ─────────────────────────────────────────────────────────────
# TOOLBAR: search, filter, legend, stats
# ─────────────────────────────────────────────────────────────
tb1, tb2, tb3 = st.columns([3, 1.2, 2])
with tb1:
    search = st.text_input('Search', placeholder='🔍 Search customer or postcode…', label_visibility='collapsed')
with tb2:
    status_filter = st.selectbox('Status', ['All statuses', 'Booked', 'Enquiry'], label_visibility='collapsed')
with tb3:
    st.markdown(f'''<div class="legend-row" style="justify-content:flex-end">
      <b style="color:#0d823b;font-size:11px">{week_range_label(offset)}</b>
      <div class="legend-item"><span class="legend-sw" style="background:#d1fae5;border-color:#6ee7b7"></span><b style="color:#065f46">Booked</b></div>
      <div class="legend-item"><span class="legend-sw" style="background:white;border-color:#d1d5db"></span><span style="color:#6b7280">Enquiry</span></div>
    </div>''', unsafe_allow_html=True)

total = len(jobs)
booked = len([j for j in jobs if j['status'] == 'booked'])
enquiry = len([j for j in jobs if j['status'] == 'enquiry'])
total_loads = sum(len(j.get('loads', [])) for j in jobs)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Jobs", total); m2.metric("Booked", booked)
m3.metric("Enquiries", enquiry); m4.metric("Total Loads", total_loads)

# Filter
def matches(j):
    if status_filter == 'Booked' and j['status'] != 'booked': return False
    if status_filter == 'Enquiry' and j['status'] != 'enquiry': return False
    if search:
        q = search.lower()
        if q not in j['customer'].lower() and q not in j['postcode'].lower(): return False
    return True
fj = [j for j in jobs if matches(j)]

# ─────────────────────────────────────────────────────────────
# ADD JOB / VEHICLES / HOLIDAYS (team mode only)
# ─────────────────────────────────────────────────────────────
if not readonly:
    with st.expander('➕ Add New Job'):
        with st.form('addjob', clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            cust = c1.text_input('Customer *')
            post = c2.text_input('Postcode *')
            ctype = c3.selectbox('Type', ['Delivery', 'Collection'])
            dsel = c4.selectbox('Day', DAYS)
            c5, c6 = st.columns(2)
            ssel = c5.selectbox('Status', ['Enquiry', 'Booked'])
            notes = c6.text_input('Notes')
            st.markdown('**Loads & Driver Initials** (fill as many as needed)')
            lc = st.columns(4)
            loads_in = []
            for i in range(4):
                with lc[i]:
                    ld = st.text_input(f'Load {i+1}', placeholder='24ft, Chem Loo…', key=f'ld{i}')
                    dr = st.text_input(f'Driver {i+1}', placeholder='CR2', key=f'dr{i}', max_chars=5)
                    if ld: loads_in.append({'desc': ld, 'driver': dr.upper()})
            if st.form_submit_button('Add Job', type='primary') and cust and post:
                wd['jobs'].append({
                    'id': f'j-{st.session_state.next_id}', 'customer': cust, 'postcode': post,
                    'col': 'del' if ctype == 'Delivery' else 'col', 'day': DAYS.index(dsel),
                    'status': ssel.lower(), 'notes': notes,
                    'loads': loads_in if loads_in else [{'desc': '', 'driver': ''}]
                })
                st.session_state.next_id += 1
                save_data(data); st.success(f'Added {cust}'); st.rerun()

    with st.expander('🚛 Vehicles  &  🏖 Holidays'):
        vcol, hcol = st.columns(2)
        with vcol:
            st.markdown('**🚛 Vehicles / PMI / MOT**')
            for v in wd.get('vehicles', []):
                a, b, c, d = st.columns([2, 2, 2, 0.6])
                v['reg'] = a.text_input('Reg', value=v['reg'], key=f"vr{v['id']}", label_visibility='collapsed')
                nd = b.selectbox('Day', DAYS, index=v['day'], key=f"vd{v['id']}", label_visibility='collapsed')
                v['day'] = DAYS.index(nd)
                v['note'] = c.text_input('Note', value=v['note'], key=f"vn{v['id']}", label_visibility='collapsed')
                if d.button('✕', key=f"vx{v['id']}"):
                    wd['vehicles'] = [x for x in wd['vehicles'] if x['id'] != v['id']]
                    save_data(data); st.rerun()
            if st.button('+ Add Vehicle'):
                wd['vehicles'].append({'id': st.session_state.next_id, 'reg': '', 'name': '', 'day': 0, 'note': ''})
                st.session_state.next_id += 1; save_data(data); st.rerun()
        with hcol:
            st.markdown('**🏖 Staff Holidays**')
            for h in wd.get('holidays', []):
                a, b = st.columns([3, 0.6])
                h['name'] = a.text_input('Name', value=h['name'], key=f"hn{h['id']}", label_visibility='collapsed')
                if b.button('✕', key=f"hx{h['id']}"):
                    wd['holidays'] = [x for x in wd['holidays'] if x['id'] != h['id']]
                    save_data(data); st.rerun()
                dsel2 = st.multiselect('Days', DAYS, default=[DAYS[d] for d in h['days'] if d < 6], key=f"hd{h['id']}", label_visibility='collapsed')
                h['days'] = [DAYS.index(x) for x in dsel2]
            if st.button('+ Add Person'):
                wd['holidays'].append({'id': st.session_state.next_id, 'name': '', 'days': []})
                st.session_state.next_id += 1; save_data(data); st.rerun()
        if st.button('💾 Save', type='primary'):
            save_data(data); st.success('Saved')

# ─────────────────────────────────────────────────────────────
# BUILD THE PLANNER TABLE (HTML — matches screenshot)
# ─────────────────────────────────────────────────────────────
vehs = wd.get('vehicles', [])
hols = wd.get('holidays', [])

html = '<table class="planner-table"><thead><tr>'
for di, dn in enumerate(DAYS):
    wknd = ' wknd' if di == 5 else ''
    html += f'<th class="day-th{wknd}" colspan="2">{dn}<br/><small>{get_day_label(offset, di)}</small></th>'
html += '</tr><tr class="veh-row">'
for di in range(6):
    dv = [v for v in vehs if v['day'] == di]
    dh = [h for h in hols if di in h.get('days', [])]
    info = ''
    if dv: info += ' · '.join([f"🚛 {v['reg']} ({v['note']})" for v in dv])
    if dh: info += (' · ' if info else '') + ' · '.join([f"🏖 {h['name']}" for h in dh])
    if info:
        html += f'<td colspan="2">{info}</td>'
    else:
        html += '<td colspan="2" style="background:#f9fafb;height:3px;border:none"></td>'
html += '</tr><tr>'
for di in range(6):
    html += '<th class="col-sub-th del-th">Deliveries</th><th class="col-sub-th col-th">Collections</th>'
html += '</tr></thead><tbody><tr>'
for di in range(6):
    dels = [j for j in fj if j['day'] == di and j['col'] == 'del']
    cols = [j for j in fj if j['day'] == di and j['col'] == 'col']
    html += '<td class="jobs-cell del">'
    html += ''.join([job_html(j) for j in dels]) if dels else '<div class="empty-cell">—</div>'
    html += '</td><td class="jobs-cell col">'
    html += ''.join([job_html(j) for j in cols]) if cols else '<div class="empty-cell">—</div>'
    html += '</td>'
html += '</tr></tbody></table>'

st.markdown(html, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# EDIT / DELETE (team mode) — compact controls below grid
# ─────────────────────────────────────────────────────────────
if not readonly and fj:
    st.divider()
    st.markdown('**Quick actions** — change status or remove a job')
    for j in fj:
        cc1, cc2, cc3 = st.columns([4, 1.2, 1])
        day_name = DAYS[j['day']]
        col_name = 'Delivery' if j['col'] == 'del' else 'Collection'
        cc1.markdown(f"<span style='font-size:12px'>**{j['customer']}** · {j['postcode']} · {day_name} {col_name} · {len(j['loads'])} load(s)</span>", unsafe_allow_html=True)
        with cc2:
            if st.button(f"↔ {'Enquiry' if j['status']=='booked' else 'Book'}", key=f"t{j['id']}", use_container_width=True):
                j['status'] = 'enquiry' if j['status'] == 'booked' else 'booked'
                save_data(data); st.rerun()
        with cc3:
            if st.button('🗑', key=f"d{j['id']}", use_container_width=True):
                wd['jobs'] = [x for x in wd['jobs'] if x['id'] != j['id']]
                save_data(data); st.rerun()

# persist any inline edits
save_data(data)
