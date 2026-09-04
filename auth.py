import streamlit as st
from database import supabase

def login_form():
    st.markdown("""<h2 style='text-align: center; color: #2E5077;'>શાળા લોગિન</h2>""", unsafe_allow_html=True)
    
    with st.container():
        user = st.text_input("યુઝરનેમ (Username)")
        pw = st.text_input("પાસવર્ડ (Password)", type="password")
        
        if st.button("લોગિન કરો", use_container_width=True):
            if user and pw:
                # ડેટાબેઝમાં પાસવર્ડ ચેક કરવાની સિસ્ટમ
                response = supabase.table("school_users").select("*").eq("username", user).execute()
                
                if len(response.data) > 0:
                    db_user = response.data[0]
                    if db_user['password'] == pw:
                        st.session_state.logged_in = True
                        st.session_state.role = db_user['role']
                        st.session_state.username = db_user['username']
                        st.session_state.name = db_user['name']
                        st.rerun()
                    else:
                        st.error("❌ ખોટો પાસવર્ડ! ફરી પ્રયાસ કરો.")
                else:
                    st.error("❌ આ યુઝરનેમ મળ્યું નથી!")
            else:
                st.warning("⚠️ કૃપા કરીને યુઝરનેમ અને પાસવર્ડ બંને લખો.")

def logout():
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.name = None
    st.rerun()
