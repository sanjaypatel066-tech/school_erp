import streamlit as st
from auth import login_form, logout
from modules.reports import show_report_module
from database import supabase
import datetime
import json
import gspread
from google.oauth2.service_account import Credentials

# Page Config
st.set_page_config(page_title="School ERP", layout="wide", initial_sidebar_state="expanded")

# Custom CSS
st.markdown("""
    <style>
    .main { background-color: #F6F8FA; }
    .stButton>button { border-radius: 8px; background-color: #2E5077; color: white; }
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E0E0E0; }
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
    
    menu = st.sidebar.radio("મેનુ પસંદ કરો", ["🏠 ડેશબોર્ડ", "📝 અહેવાલ મોડ્યુલ", "👨‍🏫 શિક્ષક પ્રોફાઇલ", "⚙️ સેટિંગ્સ"])
    
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
                        # ૧. ડેટાબેઝમાં સેવ
                        supabase.table("school_users").update({
                            "phone_number": new_phone, "aadhaar_number": new_aadhaar, 
                            "qualification": new_qual, "birthdate": str(new_bdate), "joining_date": str(new_jdate)
                        }).eq("id", selected_teacher['id']).execute()
                        
# ૨. ગૂગલ શીટ લાઈવ સિંક
                        try:
                            creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
                            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
                            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
                            client = gspread.authorize(creds)
                            
                            sheet = client.open("શિક્ષક માહિતી").sheet1
                            
                            # ડેટાબેઝમાંથી બધા શિક્ષકોનો ડેટા લાવવો
                            response = supabase.table("school_users").select("*").eq("role", "Teacher").execute()
                            all_t = response.data
                            
                            # એકસાથે પત્રક (Table) તૈયાર કરવું
                            all_data = [["શિક્ષકનું નામ", "મોબાઈલ નંબર", "આધારકાર્ડ નંબર", "લાયકાત", "જન્મ તારીખ", "જોડાવાની તારીખ"]]
                            for t in all_t:
                                all_data.append([t.get('name',''), t.get('phone_number',''), t.get('aadhaar_number',''), t.get('qualification',''), t.get('birthdate',''), t.get('joining_date','')])
                                
                            sheet.clear()
                            
                            # લાઈબ્રેરીના જૂના/નવા વર્ઝન મુજબ ડેટા લખવો
                            try:
                                sheet.update(values=all_data, range_name="A1")
                            except TypeError:
                                sheet.update("A1", all_data)
                                
                            st.success("✅ પ્રોફાઇલ સેવ થઈ ગઈ છે અને Google Sheet માં ડેટા Live Sync થઈ ગયો છે!")
                        except Exception as e:
                            if "200" in str(e):
                                st.success("✅ ડેટા ગુગલ શીટમાં પહોંચી ગયો છે! (તમારી ગૂગલ શીટ ચેક કરો)")
                            else:
                                st.error(f"⚠️ ગૂગલ શીટ એરર: {e}")
            else:
                st.warning("કોઈ શિક્ષક ઉમેરેલ નથી.")
        else:
            st.write("અહીં તમારી પ્રોફાઇલની વિગતો આપેલી છે.")
            my_data = supabase.table("school_users").select("*").eq("username", st.session_state.username).execute().data[0]
            st.info(f"**નામ:** {my_data.get('name')}")
            st.write(f"📞 **મોબાઈલ:** {my_data.get('phone_number') or '-'}")
            st.write(f"💳 **આધાર નંબર:** {my_data.get('aadhaar_number') or '-'}")

    elif menu == "⚙️ સેટિંગ્સ":
        st.header("⚙️ સેટિંગ્સ")
        tab1, tab2 = st.tabs(["🔑 પાસવર્ડ બદલો", "👤 નવો યુઝર ઉમેરો"])
        with tab1:
            new_password = st.text_input("નવો પાસવર્ડ", type="password")
            if st.button("પાસવર્ડ સેવ કરો", key="btn_pass") and new_password:
                supabase.table("school_users").update({"password": new_password}).eq("username", st.session_state.username).execute()
                st.success("✅ પાસવર્ડ બદલાઈ ગયો છે!")
        with tab2:
            if st.session_state.role == "Principal":
                n_name = st.text_input("શિક્ષકનું પૂરું નામ")
                n_user = st.text_input("નવું યુઝરનેમ")
                n_pass = st.text_input("નવો પાસવર્ડ", type="password")
                if st.button("નવું એકાઉન્ટ બનાવો", key="btn_user") and n_name and n_user and n_pass:
                    try:
                        supabase.table("school_users").insert({"name": n_name, "username": n_user, "password": n_pass, "role": "Teacher"}).execute()
                        st.success(f"✅ {n_name} નું એકાઉન્ટ બની ગયું છે!")
                    except:
                        st.error("❌ આ યુઝરનેમ પહેલેથી છે.")
