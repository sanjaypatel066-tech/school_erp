import streamlit as st
from database import supabase

def login_form():
    st.markdown("<h1 style='text-align: center; color: #2E5077;'>શાળા લોગિન</h1>", unsafe_allow_html=True)
    
    username = st.text_input("યુઝરનેમ (Username)")
    password = st.text_input("પાસવર્ડ (Password)", type="password")
    
    if st.button("લોગિન કરો"):
        if username and password:
            with st.spinner("લોગિન ચેક થઈ રહ્યું છે..."):
                try:
                    # સુપાબેઝમાંથી યુઝરનો ડેટા મંગાવો
                    response = supabase.table("school_users").select("*").eq("username", username).execute()
                    users = response.data
                    
                    if len(users) > 0:
                        user = users[0]
                        # પાસવર્ડ મેચ કરો
                        if user['password'] == password:
                            st.session_state.logged_in = True
                            st.session_state.username = user['username']
                            st.session_state.name = user['name']
                            st.session_state.role = user['role']
                            st.rerun()  # આ જાદુઈ કમાન્ડ પેજને આગળ લઈ જશે!
                        else:
                            st.error("❌ પાસવર્ડ ખોટો છે.")
                    else:
                        st.error("❌ આ યુઝરનેમ ડેટાબેઝમાં મળતું નથી.")
                except Exception as e:
                    st.error(f"⚠️ ડેટાબેઝ એરર (તમારું Supabase હજુ બંધ હોઈ શકે છે): {e}")
        else:
            st.warning("⚠️ યુઝરનેમ અને પાસવર્ડ બંને લખવા જરૂરી છે.")

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.name = ""
    st.session_state.role = ""
    st.rerun()
