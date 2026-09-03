import streamlit as st
from auth import login_form, logout
from modules.reports import show_report_module

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
    st.sidebar.title(f"નમસ્તે, {st.session_state.role}")
    
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
