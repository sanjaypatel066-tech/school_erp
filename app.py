import streamlit as st
from auth import login_form, logout
from modules.reports import show_report_module
from database import supabase
import datetime
import json
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

st.set_page_config(page_title="School ERP", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .main { background-color: #F4F7FE; }
    div[data-baseweb="input"], div[data-baseweb="select"] {
        border-radius: 12px; border: 1.5px solid #E2E8F0; background-color: #F8FAFC; transition: all 0.3s ease;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within {
        border-color: #4318FF; box-shadow: 0 0 0 3px rgba(67, 24, 255, 0.15); background-color: #FFFFFF;
    }
    .stForm {
        background-color: #FFFFFF; padding: 30px; border-radius: 20px; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08); border-top: 6px solid #4318FF;
    }
    .stButton > button {
        width: 100%; background: linear-gradient(135deg, #4318FF 0%, #868CFF 100%); color: white; border-radius: 14px; padding: 12px; font-size: 18px; font-weight: bold; border: none; transition: transform 0.2s ease;
    }
    .stButton > button:hover { transform: translateY(-3px); box-shadow: 0 10px 20px rgba(67, 24, 255, 0.4); }
    </style>
    """, unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_form()
else:
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2991/2991148.png", width=100)
    st.sidebar.title(f"નમસ્તે, {st.session_state.name}")
    st.sidebar.markdown(f"**હોદ્દો:** {st.session_state.role}")
    
    menu = st.sidebar.radio("મેનુ પસંદ કરો", ["🏠 ડેશબોર્ડ", "✨ સ્માર્ટ એન્ટ્રી", "👨‍🏫 શિક્ષક પ્રોફાઇલ", "📝 અહેવાલ મોડ્યુલ", "📊 સ્માર્ટ પત્રક", "🤖 AI અહેવાલ", "⚙️ સેટિંગ્સ"])
    
    if st.sidebar.button("લોગ આઉટ", use_container_width=True):
        logout()

    if menu == "🏠 ડેશબોર્ડ":
        if st.session_state.role == "Principal":
            st.header("🏫 આચાર્યશ્રીનું મુખ્ય ડેશબોર્ડ")
            col1, col2, col3 = st.columns(3)
            col1.metric("શાળાના કુલ વિદ્યાર્થીઓ", "250")
            col2.metric("આજની શિક્ષકોની હાજરી", "12/15")
            col3.metric("શાળાના કુલ અહેવાલો", "24")
        else:
            st.header(f"સ્વાગત છે, {st.session_state.name} શિક્ષકમિત્ર! 👨‍🏫")
            col1, col2 = st.columns(2)
            col1.metric("તમારા બનાવેલા અહેવાલો", "05")
            col2.metric("તમારો આજનો તાસ", "ધોરણ ૬, ૭")
            
    elif menu == "✨ સ્માર્ટ એન્ટ્રી":
        st.header("✨ સ્માર્ટ ડાયનેમિક એન્ટ્રી ફોર્મ")
        
        with st.spinner("તમારું ફોર્મ અને ડેટાબેઝ તૈયાર થઈ રહ્યા છે..."):
            try:
                raw_creds = st.secrets["GOOGLE_CREDENTIALS"]
                creds_dict = json.loads(raw_creds, strict=False) 
                scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
                creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
                client = gspread.authorize(creds)
                
                all_sheets = client.list_spreadsheet_files()
                
                if all_sheets:
                    sheet_options = {s['name']: s['id'] for s in all_sheets}
                    selected_sheet_name = st.selectbox("📂 ડેટા એન્ટ્રી માટે Google Sheet પસંદ કરો:", list(sheet_options.keys()))
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
                                q_name = get_val(0, col_idx)
                                if q_name != "":
                                    # Row 12 (Index 11) માંથી પ્રશ્નનો ક્રમ લેવો (ખાલી હોય તો 999)
                                    order_val = get_val(11, col_idx, "999")
                                    try: order_num = int(order_val)
                                    except: order_num = 999
                                    
                                    questions_list.append({
                                        "name": q_name,
                                        "type": get_val(1, col_idx).split()[0] if get_val(1, col_idx) else "1",
                                        "options": get_val(2, col_idx),
                                        "tab": get_val(3, col_idx, "સામાન્ય માહિતી") or "સામાન્ય માહિતી",
                                        "help": get_val(4, col_idx),
                                        "mandatory": get_val(5, col_idx).lower() in ['હા', 'yes'],
                                        "order": order_num
                                    })
                            
                            # પ્રશ્નોને આપેલા ક્રમ મુજબ ગોઠવવા
                            questions_list = sorted(questions_list, key=lambda x: x['order'])
                            
                            tab_new, tab_edit = st.tabs(["📝 નવી એન્ટ્રી", "✏️ જૂનો ડેટા જુઓ/સુધારો"])
                            data_sheet_name = "Data 2025-26"
                            
                            # TAB 1: નવી એન્ટ્રી
                            with tab_new:
                                unique_tabs = list(dict.fromkeys([q['tab'] for q in questions_list if q['name'] not in ['Timestamp', 'શિક્ષકનું નામ']]))
                                
                                with st.form("dynamic_magic_form", clear_on_submit=True):
                                    st.subheader(f"📝 {selected_sheet_name} એન્ટ્રી")
                                    form_answers = {}
                                    
                                    for q in questions_list:
                                        if q['name'] == 'Timestamp':
                                            form_answers[q['name']] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        elif q['name'] == 'શિક્ષકનું નામ':
                                            form_answers[q['name']] = st.session_state.name
                                            
                                    if unique_tabs:
                                        st_tabs = st.tabs(unique_tabs)
                                        for idx, tab_name in enumerate(unique_tabs):
                                            with st_tabs[idx]:
                                                for q in questions_list:
                                                    if q['tab'] == tab_name and q['name'] not in ['Timestamp', 'શિક્ષકનું નામ']:
                                                        q_mark = " *" if q['mandatory'] else ""
                                                        display_name = f"{q['name']}{q_mark}"
                                                        
                                                        if q['type'] == "1":
                                                            form_answers[q['name']] = st.text_input(display_name, help=q['help'])
                                                        elif q['type'] == "3":
                                                            # value=None વાપરવાથી ખાલી બોક્સ ઝીરો નહિ બતાવે
                                                            form_answers[q['name']] = st.number_input(display_name, help=q['help'], step=1, min_value=0, value=None)
                                                        elif q['type'] == "4":
                                                            form_answers[q['name']] = st.date_input(display_name, help=q['help'])
                                                        elif q['type'] == "6":
                                                            opts = [o.strip() for o in q['options'].split(",")] if q['options'] else []
                                                            if "અન્ય" not in opts: opts.append("અન્ય")
                                                            choice = st.selectbox(display_name, opts, help=q['help'])
                                                            if choice == "અન્ય":
                                                                form_answers[q['name']] = st.text_input(f"કૃપા કરીને '{q['name']}' ટાઈપ કરો:")
                                                            else:
                                                                form_answers[q['name']] = choice
                                    
                                    st.markdown("<br>", unsafe_allow_html=True)
                                    submitted = st.form_submit_button("🚀 ડેટા સેવ કરો")
                                    
                                    if submitted:
                                        missing_fields = [q['name'] for q in questions_list if q['mandatory'] and (form_answers.get(q['name']) is None or str(form_answers.get(q['name'])).strip() == "")]
                                        if missing_fields:
                                            st.error(f"⚠️ કૃપા કરીને ફરજિયાત ખાનાં ભરો: {', '.join(missing_fields)}")
                                        else:
                                            try:
                                                data_worksheet = sheet.worksheet(data_sheet_name)
                                            except gspread.exceptions.WorksheetNotFound:
                                                data_worksheet = sheet.add_worksheet(title=data_sheet_name, rows="1000", cols="20")
                                                data_worksheet.append_row([q['name'] for q in questions_list], value_input_option='USER_ENTERED')
                                            
                                            # ડેટા સેવ કરતી વખતે USER_ENTERED જેથી તારીખ અને આંકડાનું ફોર્મેટ ન બગડે
                                            row_data = ["" if form_answers.get(q['name']) is None else str(form_answers.get(q['name'])) for q in questions_list]
                                            data_worksheet.append_row(row_data, value_input_option='USER_ENTERED')
                                            st.success("✅ તમારો ડેટા સીધો Google Sheet માં સફળતાપૂર્વક સેવ થઈ ગયો છે!")

                            # TAB 2: ડેટા એડિટ
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
                                                if col_name in ['Timestamp', 'શિક્ષકનું નામ']:
                                                    edit_answers[col_name] = old_val
                                                    st.info(f"{col_name}: {old_val}")
                                                else:
                                                    edit_answers[col_name] = st.text_input(col_name, value=old_val)
                                                    
                                            if st.form_submit_button("💾 સુધારા સેવ કરો"):
                                                update_data = [edit_answers.get(c, "") for c in all_records[0]]
                                                sheet.values_update(
                                                    f"{data_sheet_name}!A{selected_idx + 2}:Z{selected_idx + 2}",
                                                    params={'valueInputOption': 'USER_ENTERED'},
                                                    body={'values': [update_data]}
                                                )
                                                st.success("✅ ડેટા સફળતાપૂર્વક સુધારી દેવાયો છે! નવો ડેટા જોવા માટે પેજ રિફ્રેશ કરો.")
                                    else:
                                        st.info("કોઈ જૂનો ડેટા નથી.")
                                except:
                                    st.warning("હજુ સુધી કોઈ ડેટા સેવ થયો નથી.")
                                    
                        else:
                            st.warning("⚠️ આ શીટના 'Setup' પાનામાં પૂરી માહિતી નથી.")
                    except gspread.exceptions.WorksheetNotFound:
                        st.error("⚠️ આ ગુગલ શીટમાં 'Setup' નામનું પાનું (Tab) મળતું નથી.")
                else:
                    st.info("⚠️ હજુ સુધી કોઈ ગૂગલ શીટ જોડાયેલી નથી.")
            except Exception as e:
                st.error(f"એરર આવી છે: {e}")

    elif menu == "📝 અહેવાલ મોડ્યુલ":
        show_report_module()
        
    elif menu == "👨‍🏫 શિક્ષક પ્રોફાઇલ":
        st.header("👨‍🏫 શિક્ષક પ્રોફાઇલ અને માહિતી")
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
        st.header("📊 સ્માર્ટ પત્રક")
        st.info("સ્માર્ટ પત્રક મોડ્યુલ અહીં આવશે.")

    elif menu == "🤖 AI અહેવાલ":
        st.header("🤖 સ્માર્ટ AI અહેવાલ લેખક")
        st.info("AI મોડ્યુલ અહીં આવશે.")

    elif menu == "⚙️ સેટિંગ્સ":
        st.header("⚙️ સેટિંગ્સ અને યુઝર મેનેજમેન્ટ")
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
