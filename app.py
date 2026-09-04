import streamlit as st
from auth import login_form, logout
from modules.reports import show_report_module
from database import supabase

# Page Config
st.set_page_config(page_title="School ERP", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for Mobile Responsiveness & Design
st.markdown("""
    <style>
    .main { background-color: #F6F8FA; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #2E5077; color: white; }
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E0E0E0; }
    @media (max-width: 640px) {
        .stColumns { flex-direction: column !important; }
    }
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
    
    menu = st.sidebar.radio("મેનુ", ["🏠 ડેશબોર્ડ", "📝 અહેવાલ મોડ્યુલ", "⚙️ સેટિંગ્સ"])
    
    if st.sidebar.button("લોગ આઉટ"):
        logout()

    if menu == "🏠 ડેશબોર્ડ":
        st.header("🏫 શાળા ડેશબોર્ડ")
        col1, col2, col3 = st.columns(3)
        col1.metric("કુલ વિદ્યાર્થીઓ", "250")
        col2.metric("હાજર શિક્ષકો", "12/15")
        col3.metric("બાકી અહેવાલો", "04")
        
    elif menu == "📝 અહેવાલ મોડ્યુલ":
        show_report_module()
        
    elif menu == "⚙️ સેટિંગ્સ":
        st.header("⚙️ સેટિંગ્સ અને યુઝર મેનેજમેન્ટ")
        
        tab1, tab2 = st.tabs(["🔑 પાસવર્ડ બદલો", "👤 નવો યુઝર ઉમેરો (માત્ર આચાર્ય માટે)"])
        
        with tab1:
            st.subheader("તમારો પાસવર્ડ બદલો")
            new_password = st.text_input("નવો પાસવર્ડ લખો", type="password")
            if st.button("પાસવર્ડ સેવ કરો"):
                if new_password:
                    # Supabase માં નવો પાસવર્ડ અપડેટ કરવાનો કોડ
                    supabase.table("school_users").update({"password": new_password}).eq("username", st.session_state.username).execute()
                    st.success("✅ તમારો પાસવર્ડ સફળતાપૂર્વક બદલાઈ ગયો છે!")
                else:
                    st.warning("⚠️ કૃપા કરીને નવો પાસવર્ડ લખો.")
                    
        with tab2:
            if st.session_state.role == "Principal":
                st.subheader("શાળાના નવા શિક્ષકનું એકાઉન્ટ બનાવો")
                new_name = st.text_input("શિક્ષકનું પૂરું નામ")
                new_user = st.text_input("નવું યુઝરનેમ (દા.ત. ramesh_sir)")
                new_pass = st.text_input("નવો પાસવર્ડ", type="password")
                new_role = st.selectbox("હોદ્દો", ["Teacher", "Clerk"])
                
                if st.button("નવું એકાઉન્ટ બનાવો"):
                    if new_name and new_user and new_pass:
                        try:
                            # Supabase માં નવો યુઝર ઉમેરવાનો કોડ
                            supabase.table("school_users").insert({
                                "name": new_name,
                                "username": new_user,
                                "password": new_pass,
                                "role": new_role
                            }).execute()
                            st.success(f"✅ {new_name} નું એકાઉન્ટ બની ગયું છે!")
                        except Exception as e:
                            st.error("❌ આ યુઝરનેમ પહેલેથી કોઈ વાપરે છે. બીજું યુઝરનેમ ટ્રાય કરો.")
                    else:
                        st.warning("⚠️ કૃપા કરીને બધી વિગતો ભરો.")
            else:
                st.error("⛔ નવો યુઝર ઉમેરવાનો અધિકાર માત્ર આચાર્યશ્રી ને જ છે.")
