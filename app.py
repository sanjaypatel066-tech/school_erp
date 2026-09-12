import streamlit as st
from auth import login_form, logout
from modules.reports import show_report_module
from database import supabase
import datetime
import json
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import requests

# Page Config
st.set_page_config(page_title="School ERP", layout="wide", initial_sidebar_state="expanded")

# Custom CSS (Premium Modern Look)
st.markdown("""
    <style>
    .main { background-color: #F4F7FE; }
    
    div[data-baseweb="input"], div[data-baseweb="select"] {
        border-radius: 12px;
        border: 1.5px solid #E2E8F0;
        background-color: #F8FAFC;
        transition: all 0.3s ease;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within {
        border-color: #4318FF;
        box-shadow: 0 0 0 3px rgba(67, 24, 255, 0.15);
        background-color: #FFFFFF;
    }
    
    .stForm {
        background-color: #FFFFFF;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
        border-top: 6px solid #4318FF;
    }
    
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #4318FF 0%, #868CFF 100%);
        color: white;
        border-radius: 14px;
        padding: 12px;
        font-size: 18px;
        font-weight: bold;
        border: none;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 20px rgba(67, 24, 255, 0.4);
    }
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
        st.markdown("આ ફોર્મ તમારી Google Sheet ના 'Setup' માંથી ઓટોમેટિક બની રહ્યું છે!")
        
        with st.spinner("તમારું ફોર્મ તૈયાર થઈ રહ્યું છે..."):
            try:
                creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
                scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
                creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
                client = gspread.authorize(creds)
                
                sheet = client.open_by_key("1BCu-RmpfFDixmt8IQ2B82fz3XcdOEhICG2E9_30_sQw")
                setup_sheet = sheet.worksheet("Setup")
                setup_data = setup_sheet.get_all_values()
                
                if len(setup_data) >= 11:
                    with st.form("dynamic_magic_form", clear_on_submit=True):
                        st.subheader(f"📝 {setup_data[0][1]} એન્ટ્રી")
                        
                        form_answers = {}
                        
                        for col_idx in range(1, len(setup_data[0])):
                            question = setup_data[0][col_idx]
                            q_type = setup_data[1][col_idx]
                            help_text = setup_data[4][col_idx]
                            
                            if question.strip() != "":
                                if q_type == "1":
                                    form_answers[question] = st.text_input(question, help=help_text)
                                elif q_type == "3":
                                    form_answers[question] = st.number_input(question, help=help_text, step=1, min_value=0)
                                elif q_type == "4":
                                    form_answers[question] = st.date_input(question, help=help_text)
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        submitted = st.form_submit_button("🚀 ડેટા સેવ કરો")
                        
                        if submitted:
                            st.success("✅ તમારો ડેટા સફળતાપૂર્વક લેવાયો!")
                            st.json(form_answers) 
                else:
                    st.warning("⚠️ Setup શીટમાં પૂરી માહિતી નથી. કૃપા કરીને Row 1 થી 11 ભરો.")
            except Exception as e:
                st.error(f"એરર આવી છે: {e}")

    elif menu == "📝 અહેવાલ મોડ્યુલ":
        show_report_module()
        
    elif menu == "👨‍🏫 શિક્ષક પ્રોફાઇલ":
        st.header("👨‍🏫 શિક્ષક પ્રોફાઇલ અને માહિતી")
        if st.session_state.role == "Principal":
            response = supabase.table("school_users").select("*").eq("role", "Teacher").execute()
            teachers = response.data
            if len(teachers) > 0:
                teacher_names = {t['name']: t for t in teachers}
                selected_name = st.selectbox("શિક્ષક પસંદ કરો:", list(teacher_names.keys()))
                selected_teacher = teacher_names[selected_name]
                
                with st.form("teacher_profile_form"):
                    st.subheader(f"{selected_teacher['name']} ની માહિતી")
                    col1, col2 = st.columns(2)
                    new_phone = col1.text_input("મોબાઈલ નંબર", value=selected_teacher.get('phone_number') or "")
                    new_aadhaar = col2.text_input("આધારકાર્ડ નંબર", value=selected_teacher.get('aadhaar_number') or "")
                    new_qual = st.text_input("શૈક્ષણિક લાયકાત", value=selected_teacher.get('qualification') or "")
                    
                    b_date = datetime.datetime.strptime(selected_teacher['birthdate'], "%Y-%m-%d").date() if selected_teacher.get('birthdate') else datetime.date(1990, 1, 1)
                    j_date = datetime.datetime.strptime(selected_teacher['joining_date'], "%Y-%m-%d").date() if selected_teacher.get('joining_date') else datetime.date.today()
                    
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
        st.info("જૂનો કોડ અહીં યથાવત છે.")

    elif menu == "🤖 AI અહેવાલ":
        st.header("🤖 સ્માર્ટ AI અહેવાલ લેખક")
        st.info("જૂનો કોડ અહીં યથાવત છે.")

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
                                    "name": n_name, 
                                    "username": n_user, 
                                    "password": n_pass, 
                                    "role": "Teacher"
                                }).execute()
                                st.success(f"✅ {n_name} નું એકાઉન્ટ સફળતાપૂર્વક બની ગયું છે!")
                            except Exception as e:
                                st.error("❌ આ યુઝરનેમ પહેલેથી ડેટાબેઝમાં છે.")
                        else:
                            st.warning("⚠️ કૃપા કરીને બધી વિગતો ભરો.")
            else:
                st.info("🔒 નવા શિક્ષકને ઉમેરવાનો અધિકાર માત્ર આચાર્યશ્રી પાસે જ છે.")
