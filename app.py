import streamlit as st
from auth import login_form, logout
from database import supabase
import datetime
import json
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import google.generativeai as genai

# Page Config
st.set_page_config(page_title="School ERP", layout="wide", initial_sidebar_state="expanded")

# Custom CSS
st.markdown("""
    <style>
    .main { background-color: #F6F8FA; }
    .stButton>button { border-radius: 8px; background-color: #2E5077; color: white; }
    </style>
    """, unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_form()
else:
    # Gemini AI Setup
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    except:
        pass

    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2991/2991148.png", width=100)
    st.sidebar.title(f"નમસ્તે, {st.session_state.name}")
    st.sidebar.markdown(f"**હોદ્દો:** {st.session_state.role}")
    
    # નવું ડાયનેમિક મેનુ
    menu = st.sidebar.radio("મેનુ પસંદ કરો", ["🏠 ડેશબોર્ડ", "📊 સ્માર્ટ પત્રક", "🤖 AI અહેવાલ", "👨‍🏫 શિક્ષક પ્રોફાઇલ", "⚙️ સેટિંગ્સ"])
    
    if st.sidebar.button("લોગ આઉટ", use_container_width=True):
        logout()

    if menu == "🏠 ડેશબોર્ડ":
        st.header("🏫 મુખ્ય ડેશબોર્ડ")
        col1, col2, col3 = st.columns(3)
        col1.metric("શાળાના કુલ વિદ્યાર્થીઓ", "250")
        col2.metric("આજની શિક્ષકોની હાજરી", "12/15")
        col3.metric("શાળાના કુલ અહેવાલો", "24")

    elif menu == "📊 સ્માર્ટ પત્રક":
        st.header("📊 સ્માર્ટ પત્રક (1-Click Excel)")
        st.info("કચેરીમાંથી માંગ્યા મુજબની માહિતી પર ટીક કરો અને સીધી Excel ફાઈલ ડાઉનલોડ કરો. (કોઈ કોડિંગની જરૂર નહીં!)")
        
        all_t = supabase.table("school_users").select("*").eq("role", "Teacher").execute().data
        if all_t:
            df = pd.DataFrame(all_t)
            df = df.rename(columns={
                'name': 'શિક્ષકનું નામ', 'phone_number': 'મોબાઈલ નંબર',
                'aadhaar_number': 'આધારકાર્ડ નંબર', 'qualification': 'લાયકાત',
                'birthdate': 'જન્મ તારીખ', 'joining_date': 'જોડાવાની તારીખ'
            })
            
            st.write("**તમારે પત્રકમાં કઈ કઈ માહિતી જોઈએ છે? (ટીક કરો)**")
            col1, col2, col3, col4 = st.columns(4)
            show_name = col1.checkbox("શિક્ષકનું નામ", value=True)
            show_phone = col2.checkbox("મોબાઈલ નંબર", value=True)
            show_aadhaar = col3.checkbox("આધારકાર્ડ નંબર")
            show_qual = col4.checkbox("લાયકાત")
            show_bdate = col1.checkbox("જન્મ તારીખ")
            show_jdate = col2.checkbox("જોડાવાની તારીખ")
            
            selected_cols = []
            if show_name: selected_cols.append('શિક્ષકનું નામ')
            if show_phone: selected_cols.append('મોબાઈલ નંબર')
            if show_aadhaar: selected_cols.append('આધારકાર્ડ નંબર')
            if show_qual: selected_cols.append('લાયકાત')
            if show_bdate: selected_cols.append('જન્મ તારીખ')
            if show_jdate: selected_cols.append('જોડાવાની તારીખ')
            
            if selected_cols:
                final_df = df[selected_cols]
                st.dataframe(final_df, use_container_width=True)
                
                csv = final_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Excel ફાઈલ ડાઉનલોડ કરો", data=csv, file_name="smart_patrak.csv", mime="text/csv")
        else:
            st.warning("કોઈ ડેટા નથી.")

    elif menu == "🤖 AI અહેવાલ":
        st.header("🤖 સ્માર્ટ AI અહેવાલ લેખક")
        st.write("માત્ર બે-ત્રણ શબ્દોમાં માહિતી આપો, અને AI આખો પ્રોફેશનલ અહેવાલ લખી આપશે!")
        
        topic = st.text_area("અહેવાલની ટૂંકી વિગત લખો:", placeholder="દા.ત. શાળામાં વિજ્ઞાન મેળાનું આયોજન, સરપંચશ્રી હાજર રહ્યા, 50 પ્રોજેક્ટ રજૂ થયા.")
        
        if st.button("✨ અહેવાલ બનાવો"):
            if topic:
                with st.spinner("AI અહેવાલ લખી રહ્યું છે..."):
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        prompt = f"તમે ગુજરાતની પ્રાથમિક શાળાના એક અનુભવી શિક્ષક છો. નીચેની માહિતી પરથી શુદ્ધ ગુજરાતીમાં એક પ્રોફેશનલ શાળાકીય અહેવાલ તૈયાર કરો:\n\n{topic}"
                        response = model.generate_content(prompt)
                        st.success("✅ અહેવાલ તૈયાર છે!")
                        st.text_area("ફાઇનલ અહેવાલ:", value=response.text, height=350)
                    except Exception as e:
                        st.error(f"AI એરર: {e}")

    elif menu == "👨‍🏫 શિક્ષક પ્રોફાઇલ":
        st.header("👨‍🏫 શિક્ષક પ્રોફાઇલ અને માહિતી")
        # અગાઉનો પ્રોફાઇલ સેવ કરવાનો અને સુપાબેઝ વાળો બધો જ કોડ અહીં અગાઉની જેમ જ રહેશે...
        # (સરળતા માટે મેં અહીં ટૂંકાવ્યું છે, તમે જૂનો પ્રોફાઇલ વાળો બ્લોક એમને એમ રાખી શકો છો).
        st.info("અહીં તમારી શિક્ષક પ્રોફાઇલ મેનેજમેન્ટ સિસ્ટમ ચાલુ રહેશે.")

    elif menu == "⚙️ સેટિંગ્સ":
        st.header("⚙️ સેટિંગ્સ")
        st.info("પાસવર્ડ અને યુઝર મેનેજમેન્ટ.")
