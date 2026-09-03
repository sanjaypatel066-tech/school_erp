import streamlit as st
from supabase import create_client, Client

# Initialize Supabase Connection
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

def save_report(data):
    return supabase.table("school_reports").insert(data).execute()

def get_reports():
    return supabase.table("school_reports").select("*").order("date", desc=True).execute()
