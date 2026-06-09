import streamlit as st
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(
    page_title="AES Transport Planner",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Styling ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Figtree', sans-serif; }
.main .block-container { padding: 0 !important; max-width: 100% !important; }
.aes-header {
    background: #0d823b; padding: 12px 20px; display: flex;
    align-items: center; justify-content: space-between;
    margin-bottom: 0;
}
.aes-header h1 { color: white; font-size: 18px; font-weight: 700; margin: 0; }
.aes-header p { color: rgba(255,255,255,.75); font-size: 11px; margin: 0; }
.week-nav-bar {
    background: #065f46; padding: 8px 20px;
    display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
}
.day-header-del {
    background: #0d823b; color: white; padding: 6px 10px;
    font-weight: 700; font-size: 13px; border-radius: 5px 5px 0 0;
    text-align: center;
}
.day-header-wknd {
    background: #546270; color: white; padding: 6px 10px;
    font-weight: 700; font-size: 13px; border-radius: 5px 5px 0 0;
    text-align: center;
}
.section-del {
    background: #f0fdf4; border-top: 2px solid #0d823b;
    padding: 3px 6px; font-size: 10px; font-weight: 700;
    color: #166534; text-transform: uppercase; letter-spacing: .5px;
}
.section-col {
    background: #eff6ff; border-top: 2px solid #3b82f6;
    padding: 3px 6px; font-size: 10px; font-weight: 700;
    color: #1e40af; text-transform: uppercase; letter-spacing: .5px;
}
.job-booked {
    background: #d1fae5; border: 1px solid #6ee7b7;
    border-radius: 5px; padding: 6px 8px; margin-bottom: 4px;
}
.job-enquiry {
    background: white; border: 1px solid #e2e6ea;
    border-radius: 5px; padding: 6px 8px; margin-bottom: 4px;
}
.job-customer { font-weight: 700; font-size: 12px; color: #1a2e1a; }
.job-enquiry .job-customer { color: #40424a; }
.job-postcode { font-size: 10px; font-weight: 600; color: #065f46; margin-top: 2px; }
.job-enquiry .job-postcode { color: #374151; }
.job-load { font-size: 10px; color: #4b5563; padding: 1px 0; }
.job-notes { font-size: 9px; color: #9ca3af; font-style: italic; }
.badge-booked {
    display: inline-block; background: #059669; color: white;
    font-size: 8px; font-weight: 700; border-radius: 2px;
    padding: 0 4px; margin-bottom: 2px;
}
.badge-enquiry {
    display: inline-block; background: #fef3c7; color: #92400e;
    border: 1px solid #fcd34d; font-size: 8px; font-weight: 700;
    border-radius: 2px; padding: 0 4px; margin-bottom: 2px;
}
.veh-bar {
    background: #fffbeb; border-bottom: 1px solid #fde68a;
    padding: 3px 8px; font-size: 10px; color: #92400e; font-weight: 700;
}
.hol-bar {
    background: #eff6ff; border-bottom: 1px solid #bfdbfe;
    padding: 3px 8px; font-size: 10px; color: #1e40af; font-weight: 700;
}
.driver-chip {
    display: inline-block; background: rgba(13,130,59,.15); color: #065f46;
    border: 1px solid rgba(13,130,59,.2); border-radius: 3px;
    padding: 0 5px; font-size: 9px; font-weight: 700; margin-left: 4px;
}
div[data-testid="stHorizontalBlock"] > div { padding: 0 4px !important; }
.stButton button {
    font-family: 'Figtree', sans-serif !important;
    font-size: 11px !important;
}
</style>
""", unsafe_allow_html=True)

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Sat/Sun']

# ── Google Sheets connection ──────────────────────────────────
def get_sheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open("AES Transport Planner").sheet1
        return sheet
    except Exception as e:
        return None

def load_data():
    sheet = get_sheet()
    if sheet:
        try:
            val = sheet.cell(1, 1).value
            if val and val.strip():
                return json.loads(val)
        except:
            pass
    return get_default_data()

def save_data(data):
    sheet = get_sheet()
    if sheet:
        try:
            sheet.update_cell(1, 1, json.dumps(data))
            return True
        except:
            return False
    return False

# ── Default seed data ─────────────────────────────────────────
def get_default_data():
    def wk(offset):
        d = datetime.now()
        day = d.weekday()
        mon = d - timedelta(days=day) + timedelta(weeks=offset)
        return mon.strftime('%Y-%m-%d')

    data = {
        'weekOffsets': [-1, 0, 1, 2, 3],
        'weekOffset': 0,
        'weeks': {}
    }

    w0 = wk(0)
    data['weeks'][w0] = {
        'jobs': [
            {'id':'w0-1','customer':'Jones Homes','loads':[{'desc':'Solar Loo','driver':'RS1'}],'postcode':'WA4 3EN','col':'del','day':0,'status':'booked','notes':''},
            {'id':'w0-2','customer':'MBC','loads':[{'desc':'Boss Unit','driver':'RS2'}],'postcode':'M14 4AH','col':'col','day':0,'status':'booked','notes':''},
            {'id':'w0-3','customer':'Wright Build','loads':[{'desc':'Chem Loo','driver':'RS1'}],'postcode':'WN2 4NU','col':'del','day':0,'status':'booked','notes':''},
            {'id':'w0-4','customer':'GreanPower','loads':[{'desc':'20kva','driver':'AP3'}],'postcode':'Etihad','col':'del','day':0,'status':'enquiry','notes':'Awaiting PO'},
            {'id':'w0-5','customer':'A Connolly','loads':[{'desc':'24ft','driver':'DF2'},{'desc':'24ft','driver':'DF3'},{'desc':'24ft','driver':'CR2'},{'desc':'24ft','driver':'CR3'}],'postcode':'L8 0TU–L8 4TF','col':'col','day':0,'status':'booked','notes':'Site Move'},
            {'id':'w0-6','customer':'A Connolly','loads':[{'desc':'24ft','driver':'DF1'},{'desc':'24ft','driver':'IB1'}],'postcode':'WA3 6RG–L8 4TF','col':'col','day':0,'status':'booked','notes':'Site Move'},
            {'id':'w0-7','customer':'Stuart Energy','loads':[{'desc':'24ft','driver':''},{'desc':'24ft','driver':''},{'desc':'24ft','driver':''},{'desc':'24ft','driver':''}],'postcode':'WN8 9TB','col':'col','day':0,'status':'booked','notes':''},
            {'id':'w0-8','customer':'Everton FC','loads':[{'desc':'6x Chem Loo','driver':''}],'postcode':'L3 0BW','col':'col','day':0,'status':'booked','notes':''},
            {'id':'w0-9','customer':'A Connolly','loads':[{'desc':'24ft','driver':'CR1'}],'postcode':'WN8 9TB–L8 4TF','col':'col','day':0,'status':'booked','notes':'Site Move'},
            {'id':'w0-10','customer':'Event Structures','loads':[{'desc':'20ft','driver':''}],'postcode':'NW1 4NR','col':'del','day':1,'status':'booked','notes':'W&D 2 man'},
            {'id':'w0-11','customer':'Event Structures','loads':[{'desc':'20ft','driver':''}],'postcode':'NN12 8TN/PO18','col':'del','day':1,'status':'booked','notes':'W&D 2 man'},
            {'id':'w0-12','customer':'Huyton Gate','loads':[{'desc':'2x Chemi Loo','driver':''},{'desc':'1x Disabled','driver':''}],'postcode':'L34 4AJ','col':'col','day':1,'status':'enquiry','notes':'TBC'},
            {'id':'w0-13','customer':'John Reilly','loads':[{'desc':'10ft Store Exchange','driver':'CR2'}],'postcode':'M38 9XE','col':'del','day':2,'status':'booked','notes':''},
            {'id':'w0-14','customer':'HolmePatrick Dev','loads':[{'desc':'24ft','driver':'DF1'},{'desc':'24ft','driver':'AP1'},{'desc':'Staircase','driver':'RB1'}],'postcode':'LA1 3JJ','col':'del','day':2,'status':'booked','notes':''},
            {'id':'w0-15','customer':'Chandos','loads':[{'desc':'24ft','driver':'IB2'}],'postcode':'WA8 3UJ','col':'del','day':2,'status':'booked','notes':''},
            {'id':'w0-16','customer':'Zenex Ltd','loads':[{'desc':'32ft','driver':'DF1'},{'desc':'32ft RB','driver':''}],'postcode':'RG10 0SD','col':'del','day':2,'status':'enquiry','notes':'Confirm vehicle'},
            {'id':'w0-17','customer':'John Reilly','loads':[{'desc':'10ft Store Exchange','driver':'CR3'}],'postcode':'M38 9XE','col':'col','day':2,'status':'booked','notes':''},
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

    w1 = wk(1)
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

# ── Week helpers ──────────────────────────────────────────────
def get_monday(offset):
    d = datetime.now()
    day = d.weekday()
    return (d - timedelta(days=day) + timedelta(weeks=offset)).replace(hour=0,minute=0,second=0,microsecond=0)

def week_key(offset):
    return get_monday(offset).strftime('%Y-%m-%d')

def week_range_label(offset):
    mon = get_monday(offset)
    fri = mon + timedelta(days=4)
    return f"{mon.strftime('%-d %b')} – {fri.strftime('%-d %b %Y')}"

def week_tab_label(offset):
    if offset == 0: return 'This Week'
    if offset == -1: return 'Last Week'
    if offset == 1: return 'Next Week'
    return get_monday(offset).strftime('%-d %b')

def get_day_label(offset, day_idx):
    if day_idx == 5: return 'Sat/Sun'
    mon = get_monday(offset)
    d = mon + timedelta(days=day_idx)
    return d.strftime('%-d %b')

def get_week_data(data, offset):
    k = week_key(offset)
    if k not in data['weeks']:
        data['weeks'][k] = {'jobs': [], 'vehicles': [], 'holidays': []}
    return data['weeks'][k]

# ── Job card HTML ─────────────────────────────────────────────
def job_html(job, readonly=False):
    is_booked = job['status'] == 'booked'
    cls = 'job-booked' if is_booked else 'job-enquiry'
    badge = '<span class="badge-booked">BOOKED</span>' if is_booked else '<span class="badge-enquiry">ENQUIRY</span>'
    loads_html = ''
    for l in job['loads']:
        drv = f'<span class="driver-chip">{l["driver"]}</span>' if l.get('driver') else ''
        loads_html += f'<div class="job-load">📦 {l.get("desc","—")}{drv}</div>'
    notes = f'<div class="job-notes">{job["notes"]}</div>' if job.get('notes') else ''
    return f'''<div class="{cls}">
        {badge}
        <div class="job-customer">{job["customer"]}</div>
        {loads_html}
        <div class="job-postcode">📍 {job["postcode"]}</div>
        {notes}
    </div>'''

# ── Session state ─────────────────────────────────────────────
if 'data' not in st.session_state:
    st.session_state.data = load_data()
if 'current_offset' not in st.session_state:
    st.session_state.current_offset = 0
if 'mode' not in st.session_state:
    st.session_state.mode = 'team'
if 'show_add_job' not in st.session_state:
    st.session_state.show_add_job = False
if 'add_job_day' not in st.session_state:
    st.session_state.add_job_day = 0
if 'add_job_col' not in st.session_state:
    st.session_state.add_job_col = 'del'
if 'edit_job_id' not in st.session_state:
    st.session_state.edit_job_id = None
if 'next_id' not in st.session_state:
    st.session_state.next_id = 1000

data = st.session_state.data

# ── Header ────────────────────────────────────────────────────
st.markdown('''<div class="aes-header">
    <div>
        <h1>🚛 AINSCOUGH ENVIRONMENTAL SERVICES</h1>
        <p>Transport Planner</p>
    </div>
</div>''', unsafe_allow_html=True)

# ── Mode toggle ───────────────────────────────────────────────
col_mode1, col_mode2, col_spacer = st.columns([1,1,8])
with col_mode1:
    if st.button('✏ Team Edit' if st.session_state.mode != 'team' else '✏ Team Edit ✓',
                 type='primary' if st.session_state.mode == 'team' else 'secondary',
                 use_container_width=True):
        st.session_state.mode = 'team'
        st.rerun()
with col_mode2:
    if st.button('👁 Read Only' if st.session_state.mode != 'readonly' else '👁 Read Only ✓',
                 type='primary' if st.session_state.mode == 'readonly' else 'secondary',
                 use_container_width=True):
        st.session_state.mode = 'readonly'
        st.rerun()

if st.session_state.mode == 'readonly':
    st.info('👁 **Read-Only Mode** — Viewing live availability. Share this page with partner businesses.')

st.divider()

# ── Week navigation ───────────────────────────────────────────
offsets = data.get('weekOffsets', [-1,0,1,2,3])
week_cols = st.columns(len(offsets) + 3)

with week_cols[0]:
    if st.button('‹', help='Previous week'):
        new_off = st.session_state.current_offset - 1
        if new_off not in offsets:
            offsets.insert(0, new_off)
            data['weekOffsets'] = offsets
        st.session_state.current_offset = new_off
        st.rerun()

for i, off in enumerate(offsets):
    with week_cols[i+1]:
        label = week_tab_label(off)
        is_active = off == st.session_state.current_offset
        btn_type = 'primary' if is_active else 'secondary'
        if st.button(f"**{label}**\n{week_range_label(off)}" if is_active else f"{label}\n{week_range_label(off)}",
                     key=f'wk_{off}', type=btn_type, use_container_width=True):
            st.session_state.current_offset = off
            st.rerun()

with week_cols[len(offsets)+1]:
    if st.button('›', help='Next week'):
        new_off = st.session_state.current_offset + 1
        if new_off not in offsets:
            offsets.append(new_off)
            data['weekOffsets'] = offsets
        st.session_state.current_offset = new_off
        st.rerun()

with week_cols[len(offsets)+2]:
    if st.button('＋ Week', help='Add a new week', type='secondary'):
        new_off = max(offsets) + 1
        offsets.append(new_off)
        data['weekOffsets'] = offsets
        st.session_state.current_offset = new_off
        st.rerun()

offset = st.session_state.current_offset
wd = get_week_data(data, offset)

st.markdown(f"### 📅 {week_range_label(offset)}")

# ── Stats ─────────────────────────────────────────────────────
jobs = wd.get('jobs', [])
total = len(jobs)
booked = len([j for j in jobs if j['status'] == 'booked'])
enquiry = len([j for j in jobs if j['status'] == 'enquiry'])
total_loads = sum(len(j.get('loads',[])) for j in jobs)

s1,s2,s3,s4,s5 = st.columns(5)
s1.metric("Total Jobs", total)
s2.metric("Booked", booked)
s3.metric("Enquiries", enquiry)
s4.metric("Total Loads", total_loads)
s5.metric("Week", week_range_label(offset))

# ── Search & filter ───────────────────────────────────────────
fc1, fc2 = st.columns([3,1])
with fc1:
    search = st.text_input('🔍 Search', placeholder='Customer or postcode…', label_visibility='collapsed')
with fc2:
    status_filter = st.selectbox('Status', ['All', 'Booked', 'Enquiry'], label_visibility='collapsed')

def job_matches(j):
    if status_filter == 'Booked' and j['status'] != 'booked': return False
    if status_filter == 'Enquiry' and j['status'] != 'enquiry': return False
    if search:
        q = search.lower()
        if q not in j['customer'].lower() and q not in j['postcode'].lower(): return False
    return True

filtered_jobs = [j for j in jobs if job_matches(j)]

# ── Add / Edit job form ───────────────────────────────────────
readonly = st.session_state.mode == 'readonly'

if not readonly:
    with st.expander('➕ Add New Job', expanded=st.session_state.show_add_job):
        with st.form('add_job_form', clear_on_submit=True):
            fc1,fc2,fc3,fc4 = st.columns(4)
            with fc1: cust = st.text_input('Customer *')
            with fc2: post = st.text_input('Postcode *')
            with fc3: col_type = st.selectbox('Type', ['Delivery','Collection'])
            with fc4: day_sel = st.selectbox('Day', DAYS)

            fc5,fc6 = st.columns(2)
            with fc5: status_sel = st.selectbox('Status', ['Enquiry','Booked'])
            with fc6: notes_inp = st.text_input('Notes')

            st.markdown('**Loads & Driver Initials**')
            lc1,lc2,lc3,lc4 = st.columns(4)
            loads_list = []
            for i,(lc,label) in enumerate([(lc1,'Load 1'),(lc2,'Load 2'),(lc3,'Load 3'),(lc4,'Load 4')]):
                with lc:
                    ld = st.text_input(f'Load {i+1}', placeholder='e.g. 24ft, Chem Loo', key=f'ld_{i}')
                    dr = st.text_input(f'Driver {i+1}', placeholder='e.g. CR2', key=f'dr_{i}', max_chars=5)
                    if ld: loads_list.append({'desc': ld, 'driver': dr.upper()})

            submitted = st.form_submit_button('Add Job', type='primary')
            if submitted and cust and post:
                if not loads_list:
                    loads_list = [{'desc': '', 'driver': ''}]
                new_job = {
                    'id': f'j-{st.session_state.next_id}',
                    'customer': cust,
                    'postcode': post,
                    'col': 'del' if col_type == 'Delivery' else 'col',
                    'day': DAYS.index(day_sel),
                    'status': status_sel.lower(),
                    'notes': notes_inp,
                    'loads': loads_list
                }
                st.session_state.next_id += 1
                wd['jobs'].append(new_job)
                save_data(data)
                st.success(f'✓ Job added for {cust}')
                st.rerun()

# ── Vehicles & Holidays ───────────────────────────────────────
if not readonly:
    with st.expander('🚛 Vehicles / PMI / MOT  |  🏖 Staff Holidays'):
        vc1, vc2 = st.columns(2)
        with vc1:
            st.markdown('**🚛 Vehicle Bookings**')
            vehs = wd.get('vehicles', [])
            for v in vehs:
                vc_a, vc_b, vc_c, vc_d = st.columns([2,2,2,1])
                with vc_a: st.text(f"{v['reg']} – {v['name']}")
                with vc_b:
                    new_day = st.selectbox('Day', DAYS, index=v['day'], key=f"vd_{v['id']}", label_visibility='collapsed')
                    v['day'] = DAYS.index(new_day)
                with vc_c:
                    new_note = st.text_input('Note', value=v['note'], key=f"vn_{v['id']}", label_visibility='collapsed')
                    v['note'] = new_note
                with vc_d:
                    if st.button('✕', key=f"dv_{v['id']}"):
                        wd['vehicles'] = [x for x in vehs if x['id'] != v['id']]
                        save_data(data); st.rerun()
            if st.button('+ Add Vehicle'):
                wd['vehicles'].append({'id': st.session_state.next_id, 'reg':'', 'name':'', 'day':0, 'note':''})
                st.session_state.next_id += 1
                save_data(data); st.rerun()

        with vc2:
            st.markdown('**🏖 Staff Holidays**')
            hols = wd.get('holidays', [])
            for h in hols:
                ha, hb = st.columns([3,1])
                with ha:
                    new_name = st.text_input('Name', value=h['name'], key=f"hn_{h['id']}", label_visibility='collapsed')
                    h['name'] = new_name
                    day_checks = st.multiselect('Days off', DAYS, default=[DAYS[d] for d in h['days'] if d < len(DAYS)], key=f"hd_{h['id']}", label_visibility='collapsed')
                    h['days'] = [DAYS.index(d) for d in day_checks]
                with hb:
                    if st.button('✕', key=f"dh_{h['id']}"):
                        wd['holidays'] = [x for x in hols if x['id'] != h['id']]
                        save_data(data); st.rerun()
            if st.button('+ Add Person'):
                wd['holidays'].append({'id': st.session_state.next_id, 'name':'', 'days':[]})
                st.session_state.next_id += 1
                save_data(data); st.rerun()

        if st.button('💾 Save Vehicles & Holidays', type='primary'):
            save_data(data)
            st.success('Saved!')

st.divider()

# ── Main planner grid ─────────────────────────────────────────
cols = st.columns(6)
vehs = wd.get('vehicles', [])
hols = wd.get('holidays', [])

for di, (col, day_name) in enumerate(zip(cols, DAYS)):
    with col:
        day_label = get_day_label(offset, di)
        day_vehs = [v for v in vehs if v['day'] == di]
        day_hols = [h for h in hols if di in h.get('days', [])]
        day_dels = [j for j in filtered_jobs if j['day'] == di and j['col'] == 'del']
        day_cols = [j for j in filtered_jobs if j['day'] == di and j['col'] == 'col']

        hdr_cls = 'day-header-wknd' if di == 5 else 'day-header-del'
        st.markdown(f'<div class="{hdr_cls}">{day_name}<br/><small style="font-weight:400;opacity:.8">{day_label}</small></div>', unsafe_allow_html=True)

        if day_vehs:
            veh_text = ' · '.join([f"🚛 {v['reg']} ({v['note']})" for v in day_vehs])
            st.markdown(f'<div class="veh-bar">{veh_text}</div>', unsafe_allow_html=True)
        if day_hols:
            hol_text = ' · '.join([f"🏖 {h['name']}" for h in day_hols])
            st.markdown(f'<div class="hol-bar">{hol_text}</div>', unsafe_allow_html=True)

        # Deliveries
        st.markdown('<div class="section-del">Deliveries</div>', unsafe_allow_html=True)
        if day_dels:
            for job in day_dels:
                st.markdown(job_html(job, readonly), unsafe_allow_html=True)
                if not readonly:
                    bc1, bc2 = st.columns(2)
                    with bc1:
                        new_status = 'enquiry' if job['status'] == 'booked' else 'booked'
                        if st.button(f"↔ {'Enquiry' if job['status']=='booked' else 'Book'}", key=f"ts_{job['id']}", use_container_width=True):
                            job['status'] = new_status
                            save_data(data); st.rerun()
                    with bc2:
                        if st.button('🗑', key=f"del_{job['id']}", use_container_width=True):
                            wd['jobs'] = [j for j in wd['jobs'] if j['id'] != job['id']]
                            save_data(data); st.rerun()
        else:
            st.markdown('<div style="color:#d1d5db;font-size:10px;text-align:center;padding:8px">—</div>', unsafe_allow_html=True)

        # Collections
        st.markdown('<div class="section-col">Collections</div>', unsafe_allow_html=True)
        if day_cols:
            for job in day_cols:
                st.markdown(job_html(job, readonly), unsafe_allow_html=True)
                if not readonly:
                    bc1, bc2 = st.columns(2)
                    with bc1:
                        new_status = 'enquiry' if job['status'] == 'booked' else 'booked'
                        if st.button(f"↔ {'Enquiry' if job['status']=='booked' else 'Book'}", key=f"ts_{job['id']}", use_container_width=True):
                            job['status'] = new_status
                            save_data(data); st.rerun()
                    with bc2:
                        if st.button('🗑', key=f"del_{job['id']}", use_container_width=True):
                            wd['jobs'] = [j for j in wd['jobs'] if j['id'] != job['id']]
                            save_data(data); st.rerun()
        else:
            st.markdown('<div style="color:#d1d5db;font-size:10px;text-align:center;padding:8px">—</div>', unsafe_allow_html=True)

# ── Auto save on any interaction ──────────────────────────────
save_data(data)
