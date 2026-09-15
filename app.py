import streamlit as st
from auth import login_form, logout
from modules.reports import show_report_module
from database import supabase
import datetime
from datetime import datetime as dt, timedelta
import json
import base64
import requests
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import google.generativeai as genai

# 1. Page Config & Clean Modern UI/UX
st.set_page_config(page_title="School ERP Pro", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    .premium-header {
        background: linear-gradient(135deg, #0A3663 0%, #1E3A8A 100%);
        padding: 30px; border-radius: 0 0 24px 24px; color: white; text-align: center; 
        margin-top: -60px; margin-bottom: 25px; box-shadow: 0 8px 20px rgba(10,54,99,0.15);
    }
    .premium-header h2 { font-weight: 700; font-size: 24px; color: #FFFFFF; margin-bottom: 4px; }
    .premium-header p { color: #E2E8F0; font-size: 14px; font-weight: 400; }
    .stForm, div[data-testid="stExpander"] {
        background-color: #FFFFFF; padding: 25px; border-radius: 16px; 
        box-shadow: 0 4px 20px rgba(0,0,0,0.03); border: 1px solid #E2E8F0; margin-bottom: 20px;
    }
    div[data-baseweb="input"], div[data-baseweb="select"], textarea {
        border-radius: 10px !important; border: 1.5px solid #CBD5E1 !important; 
        background-color: #F8FAFC !important; font-size: 14px !important; transition: all 0.2s ease;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within, textarea:focus {
        border-color: #0A3663 !important; box-shadow: 0 0 0 3px rgba(10, 54, 99, 0.1) !important; 
        background-color: #FFFFFF !important;
    }
    .stButton > button {
        width: 100%; background: linear-gradient(135deg, #16A34A 0%, #15803D 100%); 
        color: white; border-radius: 25px; padding: 10px 20px; font-size: 15px; 
        font-weight: 600; border: none; box-shadow: 0 4px 12px rgba(22, 163, 74, 0.3); 
        transition: all 0.2s ease;
    }
    .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(22, 163, 74, 0.4); }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #F1F5F9; padding: 8px; border-radius: 14px; }
    .stTabs [data-baseweb="tab"] { border-radius: 10px; padding: 8px 16px; font-weight: 500; font-size: 14px; color: #334155; }
    .stTabs [aria-selected="true"] { background-color: #0A3663 !important; color: white !important; box-shadow: 0 2px 8px rgba(10,54,99,0.25); }
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }
    </style>
    """, unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'form_unlocked' not in st.session_state:
    st.session_state.form_unlocked = False
if 'edit_unlocked' not in st.session_state:
    st.session_state.edit_unlocked = False
if 'setup_edit_verified' not in st.session_state:
    st.session_state.setup_edit_verified = False

if not st.session_state.logged_in:
    login_form()
else:
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2991/2991148.png", width=80)
    st.sidebar.title(f"નમસ્તે, {st.session_state.name}")
    st.sidebar.markdown(f"**હોદ્દો:** {st.session_state.role}")
    
    menu = st.sidebar.radio("મેનુ પસંદ કરો", [
        "🏠 ડેશબોર્ડ", "✨ સ્માર્ટ એન્ટ્રી", "🔍 ફોટો અને રેકોર્ડ વ્યૂઅર", "👨‍🏫 શિક્ષક પ્રોફાઇલ", 
        "📝 અહેવાલ મોડ્યુલ", "📊 સ્માર્ટ પત્રક", "🤖 AI અહેવાલ", "⚙️ સેટિંગ્સ"
    ])
    
    if st.sidebar.button("લોગ આઉટ", use_container_width=True):
        st.session_state.form_unlocked = False
        st.session_state.edit_unlocked = False
        st.session_state.setup_edit_verified = False
        logout()

    if menu == "🏠 ડેશબોર્ડ":
        st.markdown("<div class='premium-header'><h2>શાળા ડેશબોર્ડ</h2><p>સ્માર્ટ એજ્યુકેશન મેનેજમેન્ટ સિસ્ટમ</p></div>", unsafe_allow_html=True)
        if st.session_state.role == "Principal":
            col1, col2, col3 = st.columns(3)
            col1.metric("શાળાના કુલ વિદ્યાર્થીઓ", "250", "+12")
            col2.metric("આજની શિક્ષકોની હાજરી", "12/15", "80%")
            col3.metric("શાળાના કુલ અહેવાલો", "24", "અપડેટેડ")
        else:
            col1, col2 = st.columns(2)
            col1.metric("તમારા બનાવેલા અહેવાલો", "05")
            col2.metric("તમારો આજનો તાસ", "ધોરણ ૬, ૭")
            
    elif menu == "✨ સ્માર્ટ એન્ટ્રી":
        st.markdown("<div class='premium-header'><h2>✨ સ્માર્ટ ડાયનેમિક એન્ટ્રી</h2><p>Google Sheet આધારિત સ્માર્ટ ફોર્મ</p></div>", unsafe_allow_html=True)
        
        with st.spinner("ડેટાબેઝ સિંક થઈ રહ્યો છે..."):
            try:
                raw_creds = st.secrets["GOOGLE_CREDENTIALS"]
                creds_dict = json.loads(raw_creds, strict=False) 
                scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
                creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
                client = gspread.authorize(creds)
                
                all_sheets = client.list_spreadsheet_files()
                
                if all_sheets:
                    sheet_options = {s['name']: s['id'] for s in all_sheets}
                    selected_sheet_name = st.selectbox("📂 ફોર્મ પસંદ કરો:", list(sheet_options.keys()))
                    selected_sheet_id = sheet_options[selected_sheet_name]
                    
                    st.markdown("---")
                    sheet = client.open_by_key(selected_sheet_id)
                    
                    try:
                        setup_sheet = sheet.worksheet("Setup")
                        setup_data = setup_sheet.get_all_values()
                        
                        row_map = {}
                        setup_password = ""
                        global_folder_id = "1WdU4f1b3R166DoBDaPfVN2qtgkUKum93"
                        apps_script_url = ""
                        
                        for i, row in enumerate(setup_data):
                            if not row: continue
                            header = str(row[0]).strip().lower()
                            if "પ્રશ્ન" in header or "હેડિંગ" in header: row_map['q_name'] = i
                            elif "પ્રકાર" in header and ("ડેટા" in header or "code" in header): row_map['type'] = i
                            elif "ડ્રોપડાઉન" in header: row_map['options'] = i
                            elif "વિભાગ" in header: row_map['tab'] = i
                            elif "માર્ગદર્શિકા" in header or "help" in header: row_map['help'] = i
                            elif "ફરજિયાત" in header: row_map['mandatory'] = i
                            elif "ડિફોલ્ટ" in header or "default" in header: row_map['default'] = i
                            elif "કોલમ" in header or "column" in header: row_map['order'] = i
                            elif "entry" in header: row_map['entry_mode'] = i
                            elif "edit" in header: row_map['edit_mode'] = i
                            elif "ફોર્મનો પ્રકાર" in header or "mode" in header: row_map['form_mode'] = i
                            elif "પાસવર્ડ" in header or "password" in header:
                                if len(row) > 1 and str(row[1]).strip() not in ["", "-"]:
                                    setup_password = str(row[1]).strip()
                            
                            for cell in row:
                                cell_lower = str(cell).strip().lower()
                                if "folder id" in cell_lower:
                                    cell_idx = row.index(cell)
                                    if cell_idx + 1 < len(row) and str(row[cell_idx + 1]).strip() not in ["", "-"]:
                                        global_folder_id = str(row[cell_idx + 1]).strip()
                                if "deploy" in cell_lower or "script url" in cell_lower or "apps script" in cell_lower:
                                    cell_idx = row.index(cell)
                                    if cell_idx + 1 < len(row) and str(row[cell_idx + 1]).strip() not in ["", "-"]:
                                        apps_script_url = str(row[cell_idx + 1]).strip()

                        def get_mapped_val(key, col_idx, default=""):
                            if key not in row_map: return default
                            row_idx = row_map[key]
                            try:
                                if row_idx < len(setup_data) and col_idx < len(setup_data[row_idx]):
                                    val = str(setup_data[row_idx][col_idx]).strip()
                                    return val if val not in ["", "-"] else default
                                return default
                            except:
                                return default

                        if 'q_name' in row_map:
                            questions_list = []
                            max_cols = max([len(row) for row in setup_data]) if setup_data else 0
                            form_mode_val = "1"
                            
                            for col_idx in range(1, max_cols):
                                if 'form_mode' in row_map:
                                    fm_val = get_mapped_val('form_mode', col_idx)
                                    if "1" in fm_val or "2" in fm_val: form_mode_val = fm_val

                                q_name = get_mapped_val('q_name', col_idx)
                                if q_name != "":
                                    order_val = get_mapped_val('order', col_idx, "999")
                                    try: order_num = int(order_val)
                                    except: order_num = 999
                                    
                                    entry_mode = get_mapped_val('entry_mode', col_idx, "1").split()[0]
                                    edit_mode = get_mapped_val('edit_mode', col_idx, "1").split()[0]
                                    q_type = get_mapped_val('type', col_idx, "1").split()[0]
                                    
                                    questions_list.append({
                                        "name": q_name, "type": q_type, "options": get_mapped_val('options', col_idx, ""),
                                        "tab": get_mapped_val('tab', col_idx, "સામાન્ય માહિતી"), "help": get_mapped_val('help', col_idx, ""),
                                        "mandatory": get_mapped_val('mandatory', col_idx, "no").lower() in ['હા', 'yes', 'true'],
                                        "default": get_mapped_val('default', col_idx, ""), "order": order_num,
                                        "entry_mode": entry_mode, "edit_mode": edit_mode
                                    })
                            
                            questions_list = sorted(questions_list, key=lambda x: x['order'])
                            
                            if "1" in form_mode_val:
                                data_sheet_name = "Entry"
                            else:
                                today = datetime.date.today()
                                if today.month < 6:
                                    data_sheet_name = f"Data {today.year-1}-{str(today.year)[-2:]}"
                                else:
                                    data_sheet_name = f"Data {today.year}-{str(today.year+1)[-2:]}"
                            
                            tab_new, tab_edit = st.tabs(["📝 નવી એન્ટ્રી કરો", "✏️ જૂનો ડેટા સુધારો"])
                            
                            with tab_new:
                                if setup_password and not st.session_state.form_unlocked:
                                    st.warning("🔒 આ ફોર્મ સુરક્ષિત છે. નવી એન્ટ્રી કરવા માટે પાસવર્ડ દાખલ કરો:")
                                    entered_pwd = st.text_input("નવી એન્ટ્રી પાસવર્ડ નાખો:", type="password", key="new_entry_pwd")
                                    if st.button("🔓 અનલોક કરો", key="btn_unlock_new"):
                                        if entered_pwd == setup_password:
                                            st.session_state.form_unlocked = True
                                            st.success("✅ પાસવર્ડ સાચો છે! હવે ફોર્મ ખુલી ગયું છે.")
                                            st.rerun()
                                        else:
                                            st.error("❌ ખોટો પાસવર્ડ!")
                                    st.stop()

                                unique_tabs = list(dict.fromkeys([q['tab'] for q in questions_list]))
                                
                                if 'form_state_cache' not in st.session_state:
                                    st.session_state.form_state_cache = {}

                                with st.form("dynamic_magic_form"):
                                    st.markdown(f"<h2>📝 {selected_sheet_name}</h2>", unsafe_allow_html=True)
                                    form_answers = {}
                                    
                                    if unique_tabs:
                                        st_tabs = st.tabs(unique_tabs)
                                        for idx, tab_name in enumerate(unique_tabs):
                                            with st_tabs[idx]:
                                                for q in questions_list:
                                                    if q['tab'] == tab_name:
                                                        mode = q['entry_mode']
                                                        auto_val = ""
                                                        if q['name'].lower() in ['timestamp', 'સમય', 'તારીખ અને સમય']:
                                                            auto_val = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                                                        elif q['name'] in ['શિક્ષકનું નામ', 'શિક્ષક']:
                                                            auto_val = st.session_state.name
                                                        elif q['default']:
                                                            if q['default'].lower() == 'today': auto_val = datetime.date.today().strftime("%d-%m-%Y")
                                                            else: auto_val = q['default']
                                                        
                                                        cached_val = st.session_state.form_state_cache.get(q['name'], auto_val)
                                                        
                                                        if mode == "6":
                                                            form_answers[q['name']] = auto_val
                                                            continue
                                                            
                                                        is_locked = mode in ["2", "3", "4", "5"]
                                                        q_mark = " *" if q['mandatory'] and not is_locked else ""
                                                        display_name = f"{q['name']}{q_mark}"
                                                        
                                                        if is_locked:
                                                            st.text_input(display_name, value=auto_val, disabled=True, key=f"inp_{q['name']}")
                                                            form_answers[q['name']] = auto_val
                                                        else:
                                                            if q['type'] == "1": form_answers[q['name']] = st.text_input(display_name, value=str(cached_val) if not isinstance(cached_val, type(None)) else "", help=q['help'], key=f"inp_{q['name']}")
                                                            elif q['type'] == "2": form_answers[q['name']] = st.text_area(display_name, value=str(cached_val) if not isinstance(cached_val, type(None)) else "", help=q['help'], key=f"inp_{q['name']}")
                                                            elif q['type'] == "3": form_answers[q['name']] = st.number_input(display_name, help=q['help'], step=1, min_value=0, value=cached_val if isinstance(cached_val, (int, float)) else None, key=f"inp_{q['name']}")
                                                            elif q['type'] == "4": form_answers[q['name']] = st.date_input(display_name, help=q['help'], key=f"inp_{q['name']}")
                                                            elif q['type'] == "5":
                                                                opts = [o.strip() for o in q['options'].split(",")] if q['options'] else ["વિકલ્પો નથી"]
                                                                form_answers[q['name']] = st.selectbox(display_name, opts, help=q['help'], key=f"inp_{q['name']}")
                                                            elif q['type'] == "6":
                                                                opts = [o.strip() for o in q['options'].split(",")] if q['options'] else []
                                                                if "અન્ય" not in opts: opts.append("અન્ય")
                                                                choice = st.selectbox(display_name, opts, help=q['help'], key=f"inp_{q['name']}")
                                                                if choice == "અન્ય": form_answers[q['name']] = st.text_input(f"કૃપા કરીને '{q['name']}' ટાઈપ કરો:", key=f"inp_other_{q['name']}")
                                                                else: form_answers[q['name']] = choice
                                                            elif q['type'] == "7":
                                                                switch_val = st.toggle(display_name, help=q['help'], key=f"inp_{q['name']}")
                                                                form_answers[q['name']] = "હા" if switch_val else "ના"
                                                            elif q['type'] == "8": form_answers[q['name']] = st.time_input(display_name, help=q['help'], key=f"inp_{q['name']}")
                                                            elif q['type'] == "9":
                                                                f_up = st.file_uploader(display_name, type=["png", "jpg", "jpeg", "pdf"], help=q['help'], key=f"inp_{q['name']}")
                                                                form_answers[q['name']] = f_up
                                                            elif q['type'] == "10": form_answers[q['name']] = st.text_input(display_name, value=str(cached_val), help="અહીં લિંક પેસ્ટ કરો", key=f"inp_{q['name']}")
                                                            elif q['type'] == "11":
                                                                st.text_input(display_name, value="Auto Generated", disabled=True, key=f"inp_{q['name']}")
                                                                form_answers[q['name']] = "Auto"
                                                            elif q['type'] == "12":
                                                                val = st.text_input(display_name, value=str(cached_val) if not isinstance(cached_val, type(None)) else "", help=q['help'] + " (ફક્ત આંકડા જ લખો)", key=f"inp_{q['name']}")
                                                                if val and not val.isdigit() and val != "": st.warning(f"⚠️ કૃપા કરીને '{q['name']}' માં ફક્ત આંકડા જ લખો.")
                                                                form_answers[q['name']] = val
                                                            else: form_answers[q['name']] = st.text_input(display_name, value=str(cached_val), help=q['help'], key=f"inp_{q['name']}")
                                                                    
                                    st.markdown("<br>", unsafe_allow_html=True)
                                    submitted = st.form_submit_button("✅ ડેટા સેવ કરો")
                                    
                                    for q_k, q_v in form_answers.items():
                                        if not hasattr(q_v, "read"):
                                            st.session_state.form_state_cache[q_k] = q_v

                                    if submitted:
                                        missing = [q['name'] for q in questions_list if q['mandatory'] and q['entry_mode'] == "1" and (form_answers.get(q['name']) is None or (isinstance(form_answers.get(q['name']), str) and str(form_answers.get(q['name'])).strip() == ""))]
                                        if missing:
                                            st.error(f"⚠️ ફરજિયાત ખાનાં ભરો: {', '.join(missing)}")
                                        else:
                                            if not apps_script_url:
                                                st.error("⚠️ Setup પાનામાં 'Deploy' લિંક મળેલી નથી!")
                                            else:
                                                with st.spinner(f"ડેટા '{data_sheet_name}' માં સેવ થઈ રહ્યો છે..."):
                                                    for q in questions_list:
                                                        if q['type'] == "9":
                                                            file_obj = form_answers.get(q['name'])
                                                            if file_obj:
                                                                try:
                                                                    file_bytes = file_obj.getvalue()
                                                                    encoded_bytes = base64.b64encode(file_bytes).decode('utf-8')
                                                                    payload = {"filename": file_obj.name, "mimeType": file_obj.type, "bytes": encoded_bytes}
                                                                    response = requests.post(apps_script_url, json=payload)
                                                                    res_data = response.json()
                                                                    if "url" in res_data:
                                                                        img_url = res_data["url"]
                                                                        form_answers[q['name']] = f'=IMAGE("{img_url}")'
                                                                    else:
                                                                        form_answers[q['name']] = file_obj.name
                                                                except:
                                                                    form_answers[q['name']] = file_obj.name
                                                            else:
                                                                form_answers[q['name']] = ""
                                                                
                                                    try: data_ws = sheet.worksheet(data_sheet_name)
                                                    except:
                                                        data_ws = sheet.add_worksheet(title=data_sheet_name, rows="1000", cols="20")
                                                        data_ws.append_row([q['name'] for q in questions_list], value_input_option='USER_ENTERED')
                                                    
                                                    row_data = ["" if form_answers.get(q['name']) is None else str(form_answers.get(q['name'])) for q in questions_list]
                                                    data_ws.append_row(row_data, value_input_option='USER_ENTERED')
                                                    
                                                    st.session_state.form_state_cache = {}
                                                    st.success(f"✅ ડેટા સફળતાપૂર્વક '{data_sheet_name}' માં સેવ થઈ ગયો છે!")

                            with tab_edit:
                                all_ws = sheet.worksheets()
                                all_ws_names = [w.title for w in all_ws]
                                
                                sel_edit_ws_name = st.selectbox("📋 સુધારવા માટે ડેટા ટેબ પસંદ કરો:", all_ws_names, key="edit_ws_select")
                                
                                if setup_password:
                                    if sel_edit_ws_name.lower() == "setup":
                                        st.warning("🔒 Setup શીટ એડિટ કરવા માટે પાસવર્ડ આવશ્યક છે:")
                                        setup_edit_pwd = st.text_input("Setup એડિટ પાસવર્ડ નાખો:", type="password", key="setup_pwd_input")
                                        if st.button("🔓 Setup અનલોક કરો", key="btn_unlock_setup"):
                                            if setup_edit_pwd == setup_password:
                                                st.session_state.setup_edit_verified = True
                                                st.success("✅ પાસવર્ડ સાચો છે!")
                                                st.rerun()
                                            else:
                                                st.error("❌ ખોટો પાસવર્ડ!")
                                                st.stop()
                                        
                                        if not st.session_state.get('setup_edit_verified', False):
                                            st.stop()
                                    else:
                                        if not st.session_state.edit_unlocked:
                                            st.warning("🔒 ડેટા એડિટ કરવા માટે પાસવર્ડ દાખલ કરો:")
                                            entered_edit_pwd = st.text_input("એડિટ પાસવર્ડ નાખો:", type="password", key="normal_edit_pwd")
                                            if st.button("🔓 એડિટ અનલોક કરો", key="btn_unlock_normal"):
                                                if entered_edit_pwd == setup_password:
                                                    st.session_state.edit_unlocked = True
                                                    st.success("✅ પાસવર્ડ સાચો છે!")
                                                    st.rerun()
                                                else:
                                                    st.error("❌ ખોટો પાસવર્ડ!")
                                            st.stop()

                                try:
                                    edit_ws = sheet.worksheet(sel_edit_ws_name)
                                    records_display = edit_ws.get_all_values(value_render_option='FORMATTED_VALUE')
                                    records_formula = edit_ws.get_all_values(value_render_option='FORMULA')
                                    
                                    if len(records_display) > 1:
                                        df = pd.DataFrame(records_display[1:], columns=records_display[0])
                                        st.dataframe(df, use_container_width=True)
                                        
                                        st.markdown("### ✏️ એન્ટ્રી સુધારો")
                                        options = [f"Row {i+2}: " + " | ".join([str(v) for v in row[:3]]) for i, row in enumerate(records_display[1:])]
                                        selected_idx = st.selectbox("સુધારવા માટે એન્ટ્રી પસંદ કરો:", range(len(options)), format_func=lambda x: options[x], key="edit_row_select")
                                        
                                        target_row_idx = selected_idx + 1
                                        selected_row_display = records_display[target_row_idx]
                                        selected_row_formula = records_formula[target_row_idx]
                                        
                                        with st.form("edit_form"):
                                            edit_answers = {}
                                            for col_idx, col_name in enumerate(records_display[0]):
                                                old_val_display = selected_row_display[col_idx] if col_idx < len(selected_row_display) else ""
                                                old_val_formula = selected_row_formula[col_idx] if col_idx < len(selected_row_formula) else ""
                                                
                                                if old_val_display and str(old_val_display).isdigit() and len(str(old_val_display)) == 5:
                                                    try:
                                                        base_date = dt(1899, 12, 30)
                                                        converted_date = base_date + timedelta(days=int(old_val_display))
                                                        old_val_display = converted_date.strftime("%d-%m-%Y")
                                                    except:
                                                        pass

                                                q = next((item for item in questions_list if item["name"] == col_name), None)
                                                
                                                if q:
                                                    mode = q['edit_mode']
                                                    if mode == "6": 
                                                        edit_answers[col_name] = old_val_formula if old_val_formula else old_val_display
                                                    elif mode in ["2", "3", "4", "5"]:
                                                        st.text_input(f"{col_name} (લોક)", value=old_val_display, disabled=True, key=f"edit_lock_{col_name}_{target_row_idx}")
                                                        edit_answers[col_name] = old_val_formula if old_val_formula else old_val_display
                                                    elif q['type'] == "9": 
                                                        if old_val_formula:
                                                            st.markdown(f"**{col_name}**: (પહેલેથી ફોટો સેવ છે)")
                                                        else:
                                                            st.markdown(f"**{col_name}**: (કોઈ ફોટો નથી)")
                                                            
                                                        f_up = st.file_uploader(f"નવો ફોટો અપલોડ કરો (જો બદલવો હોય તો જ)", type=["png", "jpg", "jpeg", "pdf"], key=f"edit_file_{col_name}_{target_row_idx}")
                                                        
                                                        if f_up:
                                                            try:
                                                                file_bytes = f_up.getvalue()
                                                                encoded_bytes = base64.b64encode(file_bytes).decode('utf-8')
                                                                payload = {"filename": file_bytes.name if hasattr(file_bytes, 'name') else "photo.jpg", "mimeType": f_up.type, "bytes": encoded_bytes}
                                                                res = requests.post(apps_script_url, json=payload).json()
                                                                edit_answers[col_name] = f'=IMAGE("{res["url"]}")' if "url" in res else old_val_formula
                                                            except:
                                                                edit_answers[col_name] = old_val_formula
                                                        else:
                                                            edit_answers[col_name] = old_val_formula if old_val_formula else old_val_display
                                                    else: 
                                                        edit_answers[col_name] = st.text_input(col_name, value=old_val_display, key=f"edit_txt_{col_name}_{target_row_idx}")
                                                else:
                                                    st.text_input(f"{col_name} (જૂનો ડેટા)", value=old_val_display, disabled=True, key=f"edit_old_{col_name}_{target_row_idx}")
                                                    edit_answers[col_name] = old_val_formula if old_val_formula else old_val_display
                                                    
                                            if st.form_submit_button("💾 સુધારા સેવ કરો"):
                                                with st.spinner("સુધારા સેવ થઈ રહ્યા છે..."):
                                                    update_data = [edit_answers.get(c, "") for c in records_display[0]]
                                                    edit_ws.update(f"A{target_row_idx + 1}:Z{target_row_idx + 1}", [update_data], value_input_option='USER_ENTERED')
                                                    
                                                    if sel_edit_ws_name.lower() == "setup":
                                                        st.session_state.setup_edit_verified = False
                                                        
                                                    st.success("✅ ડેટા સફળતાપૂર્વક સુધરી ગયો છે!")
                                    else: 
                                        st.info(f"'{sel_ws_name}' ટેબમાં હજુ કોઈ ડેટા નથી.")
                                except Exception as e: 
                                    st.warning(f"ડેટા લોડ કરવામાં એરર: {e}")
                        else: st.warning("⚠️ Setup પાનામાં પ્રશ્નો મળતા નથી.")
                    except gspread.exceptions.WorksheetNotFound: st.error("⚠️ Setup પાનું મળતું નથી.")
                else: st.info("⚠️ કોઈ ગૂગલ શીટ જોડાયેલી નથી.")
            except Exception as e: st.error(f"એરર: {e}")

    elif menu == "🔍 ફોટો અને રેકોર્ડ વ્યૂઅર":
        st.markdown("<div class='premium-header'><h2>🔍 સ્માર્ટ ફોટો અને રેકોર્ડ વ્યૂઅર</h2><p>ગૂગલ શીટમાંથી ડેટા અને ફોટો શોધો</p></div>", unsafe_allow_html=True)
        try:
            raw_creds = st.secrets["GOOGLE_CREDENTIALS"]
            creds_dict = json.loads(raw_creds, strict=False) 
            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            client = gspread.authorize(creds)
            all_sheets = client.list_spreadsheet_files()
            
            if all_sheets:
                sheet_options = {s['name']: s['id'] for s in all_sheets}
                sel_sheet_name = st.selectbox("📂 ગૂગલ ફાઇલ પસંદ કરો:", list(sheet_options.keys()), key="viewer_sheet")
                sel_sheet_id = sheet_options[sel_sheet_name]
                sheet = client.open_by_key(sel_sheet_id)
                
                worksheets = sheet.worksheets()
                ws_names = [w.title for w in worksheets]
                
                sel_ws_name = st.selectbox("📋 ડેટા ટેબ (Worksheet) પસંદ કરો:", ws_names, key="viewer_worksheet")
                target_ws = sheet.worksheet(sel_ws_name)
                
                records = target_ws.get_all_values(value_render_option='FORMULA')
                if len(records) > 1:
                    headers = records[0]
                    df = pd.DataFrame(records[1:], columns=headers)
                    
                    st.markdown("---")
                    col_search_1, col_search_2 = st.columns(2)
                    search_col = col_search_1.selectbox("સર્ચ કરવા માટે કોલમ પસંદ કરો:", headers)
                    search_val = col_search_2.text_input("શોધવા માટે નામ અથવા શબ્દ લખો:")
                    
                    if search_val:
                        filtered_df = df[df[search_col].astype(str).str.contains(search_val, case=False, na=False)]
                    else:
                        filtered_df = df
                        
                    st.write(f"કુલ મળેલા પરિણામો: {len(filtered_df)}")
                    
                    for idx, row in filtered_df.iterrows():
                        with st.expander(f"📁 રેકોર્ડ #{idx+1} - {row.get(headers[0], 'વિગત')}"):
                            col_info, col_img = st.columns([2, 1])
                            with col_info:
                                for h in headers:
                                    if "photo" not in h.lower() and "ફોટો" not in h.lower():
                                        st.markdown(f"**{h}:** {row[h]}")
                            with col_img:
                                photo_val = ""
                                for h, val in row.items():
                                    val_str = str(val)
                                    if "http" in val_str or "IMAGE" in val_str or "drive.google.com" in val_str:
                                        photo_val = val_str
                                        break
                                
                                if photo_val:
                                    img_url = ""
                                    if "http" in photo_val:
                                        if '"' in photo_val:
                                            parts = photo_val.split('"')
                                            for p in parts:
                                                if "http" in p:
                                                    img_url = p
                                                    break
                                        else:
                                            img_url = photo_val
                                    
                                    if img_url:
                                        if "id=" in img_url:
                                            file_id = img_url.split("id=")[1].split("&")[0]
                                            direct_img_url = f"https://lh3.googleusercontent.com/d/{file_id}"
                                        else:
                                            direct_img_url = img_url
                                            
                                        try:
                                            st.image(direct_img_url, caption="અપલોડેડ ફોટો", width=250)
                                        except:
                                            st.warning("ફોટો લોડ કરવામાં તકલીફ છે.")
                                    else:
                                        st.info(f"સેવ થયેલ માહિતી: {photo_val}")
                                else:
                                    st.info("આ એન્ટ્રીમાં કોઈ ફોટો ઉપલબ્ધ નથી.")
                else:
                    st.info("આ ટેબમાં હજુ કોઈ ડેટા નથી.")
        except Exception as e:
            st.error(f"એરર: {e}")

    elif menu == "📝 અહેવાલ મોડ્યુલ":
        st.markdown("<div class='premium-header'><h2>📝 અહેવાલ મોડ્યુલ</h2></div>", unsafe_allow_html=True)
        show_report_module()
        
    elif menu == "👨‍🏫 શિક્ષક પ્રોફાઇલ":
        st.markdown("<div class='premium-header'><h2>👨‍🏫 શિક્ષક પ્રોફાઇલ અને માહિતી</h2></div>", unsafe_allow_html=True)
        if st.session_state.role == "Principal":
            response = supabase.table("school_users").select("*").eq("role", "Teacher").execute()
            teachers = response.data
            if teachers:
                teacher_names = {t['name']: t for t in teachers}
                selected_name = st.selectbox("શિક્ષક પસંદ કરો:", list(teacher_names.keys()))
                selected_teacher = teacher_names[selected_name]
                
                with st.form("teacher_profile_form"):
                    st.subheader(f"{selected_teacher['name']} ની માહિતી")
                    col1, col2 = st.columns(2)
                    new_phone = col1.text_input("મોબાઈલ નંબર", value=selected_teacher.get('phone_number') or "")
                    new_aadhaar = col2.text_input("આધારકાર્ડ નંબર", value=selected_teacher.get('aadhaar_number') or "")
                    new_qual = st.text_input("શૈક્ષણિક લાયકાત", value=selected_teacher.get('qualification') or "")
                    
                    b_date_str = selected_teacher.get('birthdate')
                    j_date_str = selected_teacher.get('joining_date')
                    b_date = datetime.datetime.strptime(b_date_str, "%Y-%m-%d").date() if b_date_str else datetime.date(1990, 1, 1)
                    j_date = datetime.datetime.strptime(j_date_str, "%Y-%m-%d").date() if j_date_str else datetime.date.today()
                    
                    col3, col4 = st.columns(2)
                    new_bdate = col3.date_input("જન્મ તારીખ", value=b_date)
                    new_jdate = col4.date_input("જોડાવાની તારીખ", value=j_date)
                    
                    if st.form_submit_button("માહિતી સેવ કરો"):
                        supabase.table("school_users").update({
                            "phone_number": new_phone, "aadhaar_number": new_aadhaar, 
                            "qualification": new_qual, "birthdate": str(new_bdate), "joining_date": str(new_jdate)
                        }).eq("id", selected_teacher['id']).execute()
                        st.success("✅ પ્રોફાઇલ સેવ થઈ ગઈ છે!")
            else:
                st.warning("કોઈ શિક્ષક ઉમેરેલ નથી.")
        else:
            st.write("અહીં તમારી પ્રોફાઇલની વિગતો આપેલી છે.")
            my_data = supabase.table("school_users").select("*").eq("username", st.session_state.username).execute().data[0]
            st.info(f"**નામ:** {my_data.get('name')}")
            st.write(f"📞 **મોબાઈલ:** {my_data.get('phone_number') or '-'}")

    elif menu == "📊 સ્માર્ટ પત્રક":
        st.markdown("<div class='premium-header'><h2>📊 સ્માર્ટ પત્રક</h2></div>", unsafe_allow_html=True)
        st.info("સ્માર્ટ પત્રક મોડ્યુલ અહીં આવશે.")

    elif menu == "🤖 AI અહેવાલ":
        st.markdown("<div class='premium-header'><h2>🤖 સ્માર્ટ AI અહેવાલ લેખક</h2></div>", unsafe_allow_html=True)
        
        # --- સ્માર્ટ AI અહેવાલ લેખક મોડ્યુલ ---
        try:
            api_key = st.secrets.get("GEMINI_API_KEY", "")
            if api_key:
                genai.configure(api_key=api_key)
                ai_model = genai.GenerativeModel("gemini-1.5-flash")
                
                prompt_topic = st.text_input("અહેવાલનો વિષય અથવા મુખ્ય મુદ્દાઓ લખੋ:", placeholder="દા.ત. શાળામાં યોજાયેલ વિજ્ઞાન મેળો અને પ્રદર્શન...")
                report_type = st.selectbox("અહેવાલનો પ્રકાર પસંદ કરો:", ["ઔપચારિક અહેવાલ", "ટૂંકો અહેવાલ (સોશિયલ મીડિયા માટે)", "વિગતવાર અહેવાલ", "પ્રેસ નોટ"])
                
                if st.button("✨ AI પાસે અહેવાલ લખાવો"):
                    if prompt_topic:
                        with st.spinner("AI અહેવાલ તૈયાર કરી રહ્યું છે..."):
                            full_prompt = f"તમે એક નિષ્ણાત શાળા શિક્ષક અને લેખક છો. નીચેના વિષય પર ગુજરાતી ભાષામાં એક ઉત્તમ, સચોટ અને આકર્ષક {report_type} લખો:\n\nવિષય: {prompt_topic}"
                            response = ai_model.generate_content(full_prompt)
                            st.markdown("### 📄 તૈયાર થયેલ અહેવાલ:")
                            st.write(response.text)
                    else:
                        st.warning("કૃપા કરીને અહેવાલનો વિષય લખો.")
            else:
                st.info("🤖 AI મોડ્યુલ સક્રિય કરવા માટે Streamlit Secrets માં `GEMINI_API_KEY` ઉમેરો.")
        except Exception as e:
            st.warning(f"AI મોડ્યુલ લોડ કરવામાં એરર: {e}")

    elif menu == "⚙️ સેટિંગ્સ":
        st.markdown("<div class='premium-header'><h2>⚙️ સેટિંગ્સ અને યુઝર મેનેજમેન્ટ</h2></div>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["🔑 પાસવર્ડ બદલો", "👤 નવો શિક્ષક ઉમેરો"])
        
        with tab1:
            st.subheader("તમારો પાસવર્ડ અપડેટ કરો")
            new_password = st.text_input("નવો પાસવર્ડ દાખલ કરો", type="password")
            if st.button("પાસવર્ડ સેવ કરો", key="btn_pass"):
                if new_password:
                    try:
                        supabase.table("school_users").update({"password": new_password}).eq("username", st.session_state.username).execute()
                        st.success("✅ તમારો નવો પાસવર્ડ સફળતાપૂર્વક સેવ થઈ ગયો છે!")
                    except Exception as e:
                        st.error(f"⚠️ એરર: {e}")
                else:
                    st.warning("કૃપા કરીને નવો પાસવર્ડ લખો.")

        with tab2:
            if st.session_state.role == "Principal":
                st.subheader("નવા શિક્ષકનું લોગિન બનાવો")
                with st.form("add_new_user_form", clear_on_submit=True):
                    n_name = st.text_input("શિક્ષકનું પૂરું નામ")
                    n_user = st.text_input("નવું યુઝરનેમ (લોગિન માટે)")
                    n_pass = st.text_input("નવો પાસવર્ડ", type="password")
                    
                    submitted = st.form_submit_button("નવું એકાઉન્ટ બનાવો")
                    
                    if submitted:
                        if n_name and n_user and n_pass:
                            try:
                                supabase.table("school_users").insert({
                                    "name": n_name, "username": n_user, "password": n_pass, "role": "Teacher"
                                }).execute()
                                st.success(f"✅ {n_name} નું એકાઉન્ટ સફળતાપૂર્વક બની ગયું છે!")
                            except Exception as e:
                                st.error("❌ આ યુઝરનેમ પહેલેથી ડેટાબેઝમાં છે.")
                        else:
                            st.warning("⚠️ કૃપા કરીને બધી વિગતો ભરો.")
            else:
                st.info("🔒 નવા શિક્ષકને ઉમેરવાનો અધિકાર માત્ર આચાર્યશ્રી પાસે જ છે.")
