import streamlit as st

def login_form():
    st.markdown("""<h2 style='text-align: center; color: #2E5077;'>શાળા લોગિન</h2>""", unsafe_allow_html=True)
    
    with st.container():
        user = st.text_input("યુઝરનેમ (Username)")
        pw = st.text_input("પાસવર્ડ (Password)", type="password")
        role = st.selectbox("તમારો હોદ્દો (Role)", ["Principal", "Teacher", "Student", "Parent"])
        
        if st.button("લોગિન કરો", use_container_width=True):
            # Simplified for Phase 1 - In Phase 2 we connect to Supabase Auth
            if user == "admin" and pw == "admin123":
                st.session_state.logged_in = True
                st.session_state.role = role
                st.session_state.username = user
                st.rerun()
            else:
                st.error("ખોટો યુઝરનેમ અથવા પાસવર્ડ!")

def logout():
    st.session_state.logged_in = False
    st.rerun()
