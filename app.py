import streamlit as st
from auth import login_form, logout
from modules.reports import show_report_module
from database import supabase
import datetime
import json
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. Page Config
st.set_page_config(page_title="School ERP Pro", layout="wide", initial_sidebar_state="expanded")

# 2. Premium App-Like UI (CSS)
st.markdown("""
    <style>
    /* બેકગ્રાઉન્ડ કલર */
    .stApp { background-color: #F0F4F8; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* ગ્રેડિયન્ટ હેડર (ફોટા મુજબ બ્લુ થી મરૂન) */
    .premium-header {
        background: linear-gradient(135deg, #0A3663 0%, #8B1B22 100%);
        padding: 30px; border-radius: 0 0 25px 25px; color: white; text-align: center; margin-top: -60px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    /* કાર્ડ જેવી ડિઝાઇન */
    .stForm, div[data-testid="stExpander"] {
        background-color: #FFFFFF; padding: 25px; border-radius: 20px; box-shadow: 0 8px 20px rgba(0,0,0,0.05); border: 1px solid #E2E8F0; margin-bottom: 20px;
    }
    
    /* ઇનપુટ બોક્સ ડિઝાઇન */
    div[data-baseweb="input"], div[data-baseweb="select"], textarea {
        border-radius: 10px !important; border: 1.5px solid #CBD5E1 !important; background-color: #F8FAFC !important; transition: all 0.3s ease;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within, textarea:focus {
        border-color: #0A3663 !important; box-shadow: 0 0 0 3px rgba(10, 54, 99, 0.1) !important; background-color: #FFFFFF !important;
    }
    
    /* સુંદર બટન */
    .stButton > button {
        width: 100%; background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%); color: white; border-radius: 30px; padding: 10px 20px; font-size: 16px; font-weight: bold; border: none; box-shadow: 0 4px 10px rgba(34, 197, 94, 0.3); transition: all 0.2s;
    }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 15px rgba(34, 197, 94, 0.4); }
    
    /* ટેબ્સ ડિઝાઇન */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: white; padding: 10px; border-radius: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .stTabs [data-baseweb="tab"] { border-radius: 10px; padding: 8px 16px; }
    .stTabs [aria-selected="true"] { background-color: #0A3663; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. લોગિન સિસ્ટમ
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_form()
else:
    # સાઈડબાર
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2991/2991148.png", width=100)
    st.sidebar.title(f"નમસ્તે, {st.session_state.name}")
    st.sidebar.markdown(f"**હોદ્દો:** {st.session_state.role}")
    
    menu = st.sidebar.radio("મેનુ પસંદ કરો", ["🏠 ડેશબોર્ડ", "✨ સ્માર્ટ એન્ટ્રી", "👨‍🏫 શિક્ષક પ્રોફાઇલ", "⚙️ સેટિંગ્સ"])
    
    if st.sidebar.button("લોગ આઉટ", use_container_width=True):
        logout()

    if menu == "🏠 ડેશબોર્ડ":
        st.markdown("<div class='premium-header'><h2>શાળા ડેશબોર્ડ</h2><p>સ્માર્ટ એજ્યુકેશન સિસ્ટમ</p></div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        col1.metric("કુલ વિદ્યાર્થીઓ", "250", "+12")
        col2.metric("આજની હાજરી", "95%", "+2%")
        col3.metric("રિપોર્ટ્સ", "24", "અપડેટેડ")
            
    elif menu == "✨ સ્માર્ટ એન્ટ્રી":
        st.markdown("<div class='premium-header'><h2>✨ સ્માર્ટ ડાયનેમિક એન્ટ્રી</h2><p>Google Sheet આધારિત ફોર્મ</p></div>", unsafe_allow_html=True)
        
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
                        
                        def get_val(row_idx, col_idx, default=""):
                            try: return str(setup_data[row_idx][col_idx]).strip()
                            except IndexError: return default

                        if len(setup_data) >= 2:
                            questions_list = []
                            for col_idx in range(1, len(setup_data[0])):
                                q_name = get_val(1, col_idx)
                                if q_name != "":
                                    order_val = get_val(12, col_idx, "999")
                                    try: order_num = int(order_val)
                                    except: order_num = 999
                                    
                                    entry_mode = get_val(13, col_idx, "1").split()[0]
                                    edit_mode = get_val(14, col_idx, "1").split()[0]
                                    
                                    questions_list.append({
                                        "name": q_name,
                                        "type": get_val(2, col_idx).split()[0] if get_val(2, col_idx) else "1",
                                        "options": get_val(3, col_idx),
                                        "tab": get_val(4, col_idx, "સામાન્ય માહિતી") or "સામાન્ય માહિતી",
                                        "help": get_val(5, col_idx),
                                        "mandatory": get_val(6, col_idx).lower() in ['હા', 'yes'],
                                        "default": get_val(7, col_idx),
                                        "order": order_num,
                                        "entry_mode": entry_mode,
                                        "edit_mode": edit_mode
                                    })
                            
                            questions_list = sorted(questions_list, key=lambda x: x['order'])
                            
                            tab_new, tab_edit = st.tabs(["📝 નવી એન્ટ્રી કરો", "✏️ જૂનો ડેટા સુધારો"])
                            data_sheet_name = "Data 2025-26"
                            
                            # === TAB 1: નવી એન્ટ્રી ===
                            with tab_new:
                                unique_tabs = list(dict.fromkeys([q['tab'] for q in questions_list]))
                                
                                with st.form("dynamic_magic_form", clear_on_submit=True):
                                    st.subheader(f"📝 {selected_sheet_name}")
                                    form_answers = {}
                                    
                                    if unique_tabs:
                                        st_tabs = st.tabs(unique_tabs)
                                        for idx, tab_name in enumerate(unique_tabs):
                                            with st_tabs[idx]:
                                                for q in questions_list:
                                                    if q['tab'] == tab_name:
                                                        mode = q['entry_mode']
                                                        
                                                        auto_val = ""
                                                        if q['name'].lower() in ['timestamp', 'સમય']:
                                                            auto_val = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                                                        elif q['name'] in ['શિક્ષકનું નામ', 'શિક્ષક']:
                                                            auto_val = st.session_state.name
                                                        elif q['default']:
                                                            if q['default'].lower() == 'today':
                                                                auto_val = datetime.date.today().strftime("%d-%m-%Y")
                                                            else: auto_val = q['default']
                                                        
                                                        if mode == "6":
                                                            form_answers[q['name']] = auto_val
                                                            continue
                                                            
                                                        is_locked = mode in ["2", "3", "4", "5"]
                                                        q_mark = " *" if q['mandatory'] and not is_locked else ""
                                                        display_name = f"{q['name']}{q_mark}"
                                                        
                                                        if is_locked:
                                                            st.text_input(display_name, value=auto_val, disabled=True, help="આ ખાનું લોક છે.")
                                                            form_answers[q['name']] = auto_val
                                                        else:
                                                            # ALL 12 INPUT TYPES
                                                            if q['type'] == "1":
                                                                form_answers[q['name']] = st.text_input(display_name, value=auto_val, help=q['help'])
                                                            elif q['type'] == "2":
                                                                form_answers[q['name']] = st.text_area(display_name, value=auto_val, help=q['help'])
                                                            elif q['type'] == "3":
                                                                form_answers[q['name']] = st.number_input(display_name, help=q['help'], step=1, min_value=0, value=None)
                                                            elif q['type'] == "4":
                                                                form_answers[q['name']] = st.date_input(display_name, help=q['help'])
                                                            elif q['type'] == "5":
                                                                opts = [o.strip() for o in q['options'].split(",")] if q['options'] else ["વિકલ્પો નથી"]
                                                                form_answers[q['name']] = st.selectbox(display_name, opts, help=q['help'])
                                                            elif q['type'] == "6":
                                                                opts = [o.strip() for o in q['options'].split(",")] if q['options'] else []
                                                                if "અન્ય" not in opts: opts.append("અન્ય")
                                                                choice = st.selectbox(display_name, opts, help=q['help'])
                                                                if choice == "અન્ય":
                                                                    form_answers[q['name']] = st.text_input(f"કૃપા કરીને '{q['name']}' ટાઈપ કરો:")
                                                                else: form_answers[q['name']] = choice
                                                            elif q['type'] == "7":
                                                                switch_val = st.toggle(display_name, help=q['help'])
                                                                form_answers[q['name']] = "હા" if switch_val else "ના"
                                                            elif q['type'] == "8":
                                                                form_answers[q['name']] = st.time_input(display_name, help=q['help'])
                                                            elif q['type'] == "9":
                                                                f_up = st.file_uploader(display_name, type=["png", "jpg", "pdf"], help=q['help'])
                                                                form_answers[q['name']] = f_up.name if f_up else ""
                                                            elif q['type'] == "10":
                                                                form_answers[q['name']] = st.text_input(display_name, value=auto_val, help="અહીં લિંક પેસ્ટ કરો")
                                                            elif q['type'] == "11":
                                                                st.text_input(display_name, value="Auto Generated", disabled=True)
                                                                form_answers[q['name']] = "Auto"
                                                            elif q['type'] == "12":
                                                                # 15 આંકડાના પ્રોબ્લેમ માટે શુદ્ધ ટેક્સ્ટ ઇનપુટ
                                                                val = st.text_input(display_name, value=auto_val, help=q['help'] + " (ફક્ત આંકડા જ લખો)")
                                                                if val and not val.isdigit():
                                                                    st.warning(f"⚠️ કૃપા કરીને '{q['name']}' માં ફક્ત આંકડા જ લખો.")
                                                                form_answers[q['name']] = val
                                                                    
                                    st.markdown("<br>", unsafe_allow_html=True)
                                    submitted = st.form_submit_button("✅ ડેટા સેવ કરો")
                                    
                                    if submitted:
                                        missing = [q['name'] for q in questions_list if q['mandatory'] and q['entry_mode'] == "1" and (form_answers.get(q['name']) is None or str(form_answers.get(q['name'])).strip() == "")]
                                        if missing:
                                            st.error(f"⚠️ ફરજિયાત ખાનાં ભરો: {', '.join(missing)}")
                                        else:
                                            try: data_ws = sheet.worksheet(data_sheet_name)
                                            except:
                                                data_ws = sheet.add_worksheet(title=data_sheet_name, rows="1000", cols="20")
                                                data_ws.append_row([q['name'] for q in questions_list], value_input_option='USER_ENTERED')
                                            
                                            row_data = ["" if form_answers.get(q['name']) is None else str(form_answers.get(q['name'])) for q in questions_list]
                                            data_ws.append_row(row_data, value_input_option='USER_ENTERED')
                                            st.success("✅ ડેટા સફળતાપૂર્વક સેવ થઈ ગયો છે!")

                            # === TAB 2: ડેટા એડિટ ===
                            with tab_edit:
                                try:
                                    data_ws = sheet.worksheet(data_sheet_name)
                                    all_records = data_ws.get_all_values()
                                    if len(all_records) > 1:
                                        df = pd.DataFrame(all_records[1:], columns=all_records[0])
                                        st.dataframe(df, use_container_width=True)
                                        
                                        st.markdown("### ✏️ એન્ટ્રી સુધારો")
                                        options = [f"Row {i+2}: " + " | ".join(row[:3]) for i, row in enumerate(all_records[1:])]
                                        selected_idx = st.selectbox("સુધારવા માટે એન્ટ્રી પસંદ કરો:", range(len(options)), format_func=lambda x: options[x])
                                        selected_row = all_records[selected_idx + 1]
                                        
                                        with st.form("edit_form"):
                                            edit_answers = {}
                                            for col_idx, col_name in enumerate(all_records[0]):
                                                old_val = selected_row[col_idx] if col_idx < len(selected_row) else ""
                                                q = next((item for item in questions_list if item["name"] == col_name), None)
                                                
                                                if q:
                                                    mode = q['edit_mode']
                                                    if mode == "6": edit_answers[col_name] = old_val
                                                    elif mode in ["2", "3", "4", "5"]:
                                                        st.text_input(f"{col_name} (લોક)", value=old_val, disabled=True)
                                                        edit_answers[col_name] = old_val
                                                    else: edit_answers[col_name] = st.text_input(col_name, value=old_val)
                                                else:
                                                    st.text_input(f"{col_name} (જૂનો ડેટા)", value=old_val, disabled=True)
                                                    edit_answers[col_name] = old_val
                                                    
                                            if st.form_submit_button("💾 સુધારા સેવ કરો"):
                                                update_data = [edit_answers.get(c, "") for c in all_records[0]]
                                                sheet.values_update(f"{data_sheet_name}!A{selected_idx + 2}:Z{selected_idx + 2}", params={'valueInputOption': 'USER_ENTERED'}, body={'values': [update_data]})
                                                st.success("✅ ડેટા સુધરી ગયો છે! રિફ્રેશ કરો.")
                                    else: st.info("કોઈ જૂનો ડેટા નથી.")
                                except: st.warning("હજુ કોઈ ડેટા સેવ થયો નથી.")
                        else: st.warning("⚠️ Setup પાનામાં પૂરી માહિતી નથી.")
                    except gspread.exceptions.WorksheetNotFound: st.error("⚠️ Setup પાનું મળતું નથી.")
                else: st.info("⚠️ કોઈ ગૂગલ શીટ જોડાયેલી નથી.")
            except Exception as e: st.error(f"એરર: {e}")

    elif menu == "⚙️ સેટિંગ્સ":
        st.markdown("<div class='premium-header'><h2>⚙️ સેટિંગ્સ</h2></div>", unsafe_allow_html=True)
        st.info("સેટિંગ્સ મોડ્યુલ...")
