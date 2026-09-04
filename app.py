import streamlit as st
from auth import login_form, logout
from modules.reports import show_report_module
from database import supabase
import datetime

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

# Session State Initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Application Logic
if not st.session_state.logged_in:
    login_form()
else:
    # Sidebar Navigation
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2991/2991148.png", width=100)
    st.sidebar.title(f"નમસ્તે, {st.session_state.name}")
    st.sidebar.markdown(f"**હોદ્દો:** {st.session_state.role}")
    
    # રોલ પ્રમાણે મેનુ અલગ દેખાશે
    menu_options = ["🏠 ડેશબોર્ડ", "📝 અહેવાલ મોડ્યુલ", "👨‍🏫 શિક્ષક પ્રોફાઇલ", "⚙️ સેટિંગ્સ"]
    menu = st.sidebar.radio("મેનુ પસંદ કરો", menu_options)
    
    if st.sidebar.button("લોગ આઉટ", use_container_width=True):
        logout()

    # ---------------- 1. ડેશબોર્ડ (અલગ-અલગ) ----------------
    if menu == "🏠 ડેશબોર્ડ":
        if st.session_state.role == "Principal":
            st.header("🏫 આચાર્યશ્રીનું મુખ્ય ડેશબોર્ડ")
            col1, col2, col3 = st.columns(3)
            col1.metric("શાળાના કુલ વિદ્યાર્થીઓ", "250")
            col2.metric("આજની શિક્ષકોની હાજરી", "12/15")
            col3.metric("શાળાના કુલ અહેવાલો", "24")
            st.info("અહીંથી તમે સમગ્ર શાળાની કામગીરી પર નજર રાખી શકશો.")
        else:
            st.header(f"સ્વાગત છે, {st.session_state.name} શિક્ષકમિત્ર! 👨‍🏫")
            col1, col2 = st.columns(2)
            col1.metric("તમારા બનાવેલા અહેવાલો", "05")
            col2.metric("તમારો આજનો તાસ/પિરિયડ", "ધોરણ ૬, ૭")
            st.success("શિક્ષક તરીકે તમે અહેવાલો બનાવી શકશો અને તમારી પ્રોફાઇલ જોઈ શકશો.")
            
    # ---------------- 2. અહેવાલ મોડ્યુલ ----------------
    elif menu == "📝 અહેવાલ મોડ્યુલ":
        show_report_module()
        
    # ---------------- 3. શિક્ષક પ્રોફાઇલ ----------------
    elif menu == "👨‍🏫 શિક્ષક પ્રોફાઇલ":
        st.header("👨‍🏫 શિક્ષક પ્રોફાઇલ અને માહિતી")
        
        if st.session_state.role == "Principal":
            st.write("આચાર્યશ્રી, તમે અહીંથી કોઈપણ શિક્ષકની માહિતી ઉમેરી કે બદલી શકો છો.")
            
            # ડેટાબેઝમાંથી શિક્ષકોનું લિસ્ટ લાવવું
            response = supabase.table("school_users").select("*").eq("role", "Teacher").execute()
            teachers = response.data
            
            if len(teachers) > 0:
                teacher_names = {t['name']: t for t in teachers}
                selected_teacher_name = st.selectbox("શિક્ષક પસંદ કરો:", list(teacher_names.keys()))
                selected_teacher = teacher_names[selected_teacher_name]
                
                with st.form("teacher_profile_form"):
                    st.subheader(f"{selected_teacher['name']} ની માહિતી")
                    
                    # ફોર્મમાં ડેટા ભરવો (જો જૂનો હોય તો તે દેખાશે)
                    col1, col2 = st.columns(2)
                    new_phone = col1.text_input("મોબાઈલ નંબર", value=selected_teacher.get('phone_number') or "")
                    new_aadhaar = col2.text_input("આધારકાર્ડ નંબર", value=selected_teacher.get('aadhaar_number') or "")
                    
                    new_qual = st.text_input("શૈક્ષણિક લાયકાત (દા.ત. B.Sc, B.Ed)", value=selected_teacher.get('qualification') or "")
                    
                    # તારીખ માટે ખાસ કોડ (જો તારીખ ન હોય તો આજની તારીખ બતાવશે)
                    b_date = datetime.datetime.strptime(selected_teacher['birthdate'], "%Y-%m-%d").date() if selected_teacher.get('birthdate') else datetime.date(1990, 1, 1)
                    j_date = datetime.datetime.strptime(selected_teacher['joining_date'], "%Y-%m-%d").date() if selected_teacher.get('joining_date') else datetime.date.today()
                    
                    col3, col4 = st.columns(2)
                    new_bdate = col3.date_input("જન્મ તારીખ", value=b_date)
                    new_jdate = col4.date_input("જોડાવાની તારીખ", value=j_date)
                    
                    submit_profile = st.form_submit_button("માહિતી સેવ કરો")
                    
                    if submit_profile:
                        # સુપાબેઝમાં ડેટા અપડેટ કરવો
                        supabase.table("school_users").update({
                            "phone_number": new_phone,
                            "aadhaar_number": new_aadhaar,
                            "qualification": new_qual,
                            "birthdate": str(new_bdate),
                            "joining_date": str(new_jdate)
                        }).eq("id", selected_teacher['id']).execute()
                        st.success("✅ શિક્ષકની પ્રોફાઇલ સફળતાપૂર્વક અપડેટ થઈ ગઈ છે!")
            else:
                st.warning("હજુ સુધી કોઈ શિક્ષકનું એકાઉન્ટ બનાવેલ નથી. પહેલા 'સેટિંગ્સ' માંથી શિક્ષક ઉમેરો.")
                
        else: # જો શિક્ષક પોતે લોગિન હોય તો
            st.write("અહીં તમારી પ્રોફાઇલની વિગતો આપેલી છે. જો કોઈ ભૂલ હોય તો આચાર્યશ્રીનો સંપર્ક કરો.")
            response = supabase.table("school_users").select("*").eq("username", st.session_state.username).execute()
            my_data = response.data[0]
            
            st.info(f"**નામ:** {my_data.get('name')}")
            st.write(f"📞 **મોબાઈલ:** {my_data.get('phone_number') or 'માહિતી નથી'}")
            st.write(f"💳 **આધાર નંબર:** {my_data.get('aadhaar_number') or 'માહિતી નથી'}")
            st.write(f"🎓 **લાયકાત:** {my_data.get('qualification') or 'માહિતી નથી'}")
            st.write(f"🎂 **જન્મ તારીખ:** {my_data.get('birthdate') or 'માહિતી નથી'}")
            st.write(f"🏢 **જોડાવાની તારીખ:** {my_data.get('joining_date') or 'માહિતી નથી'}")

    # ---------------- 4. સેટિંગ્સ ----------------
    elif menu == "⚙️ સેટિંગ્સ":
        st.header("⚙️ સેટિંગ્સ")
        tab1, tab2 = st.tabs(["🔑 પાસવર્ડ બદલો", "👤 નવો યુઝર ઉમેરો"])
        
        with tab1:
            st.subheader("તમારો પાસવર્ડ બદલો")
            new_password = st.text_input("નવો પાસવર્ડ લખો", type="password")
            if st.button("પાસવર્ડ સેવ કરો", key="btn_pass"):
                if new_password:
                    supabase.table("school_users").update({"password": new_password}).eq("username", st.session_state.username).execute()
                    st.success("✅ તમારો પાસવર્ડ બદલાઈ ગયો છે!")
                    
        with tab2:
            if st.session_state.role == "Principal":
                st.subheader("શાળાના નવા શિક્ષકનું એકાઉન્ટ બનાવો")
                new_name = st.text_input("શિક્ષકનું પૂરું નામ")
                new_user = st.text_input("નવું યુઝરનેમ (દા.ત. ramesh_sir)")
                new_pass = st.text_input("નવો પાસવર્ડ", type="password")
                new_role = st.selectbox("હોદ્દો", ["Teacher", "Clerk"])
                
                if st.button("નવું એકાઉન્ટ બનાવો", key="btn_user"):
                    if new_name and new_user and new_pass:
                        try:
                            supabase.table("school_users").insert({"name": new_name, "username": new_user, "password": new_pass, "role": new_role}).execute()
                            st.success(f"✅ {new_name} નું એકાઉન્ટ બની ગયું છે!")
                        except:
                            st.error("❌ આ યુઝરનેમ પહેલેથી છે. બીજું ટ્રાય કરો.")
            else:
                st.error("⛔ આ સુવિધા માત્ર આચાર્યશ્રી માટે છે.")
