import streamlit as st
from fpdf import FPDF
import base64
from datetime import datetime

def show_report_module():
    st.title("📝 શાળા પ્રવૃત્તિ અહેવાલ")
    
    tab1, tab2 = st.tabs(["નવો અહેવાલ બનાવો", "જૂના અહેવાલ જુઓ"])

    with tab1:
        with st.form("report_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                date = st.date_input("તારીખ", datetime.now())
                title = st.text_input("અહેવાલનું શીર્ષક (Title)")
            
            description = st.text_area("વિગતવાર વર્ણન (Description)")
            
            uploaded_files = st.file_uploader("ફોટા અપલોડ કરો (મહત્તમ 5)", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
            
            st.divider()
            st.subheader("PDF સેટિંગ્સ")
            use_letterhead = st.checkbox("સ્કૂલ લેટરહેડ ઉમેરો", value=True)
            add_sign = st.checkbox("આચાર્યશ્રીનો સિક્કો/સહી ઉમેરો")
            
            if add_sign:
                sign_pass = st.text_input("સહી માટે પાસવર્ડ", type="password")

            submit = st.form_submit_with_button("અહેવાલ સાચવો અને PDF બનાવો")

            if submit:
                # Logic to process and save data
                st.success("અહેવાલ સફળતાપૂર્વક સાચવવામાં આવ્યો છે!")
                generate_pdf(title, date, description, use_letterhead)

    with tab2:
        st.info("અહીં તમે જૂના અહેવાલો શોધી શકશો અને તેને ફરીથી ડાઉનલોડ કરી શકશો.")
        # Search & Table Logic will go here in Phase 2

def generate_pdf(title, date, desc, letterhead):
    pdf = FPDF()
    pdf.add_page()
    
    # Register Gujarati Font
    try:
        pdf.add_font('Gujarati', '', 'assets/fonts/gujarati.ttf')
        pdf.set_font('Gujarati', size=14)
    except:
        pdf.set_font('Arial', size=14)

    if letterhead:
        pdf.set_text_color(46, 80, 119)
        pdf.cell(200, 10, txt="નવાપુરા(મહુવડ) પ્રાથમિક શાળા", ln=True, align='C')
        pdf.set_font('Gujarati', size=10)
        pdf.cell(200, 10, txt="તા. પાદરા, જી. વડોદરા (DISE: ૨૪૧૯૦૭૦૭૦૦૧)", ln=True, align='C')
        pdf.line(10, 30, 200, 30)
        pdf.ln(10)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Gujarati', size=16)
    pdf.cell(200, 10, txt=f"અહેવાલ: {title}", ln=True, align='L')
    pdf.set_font('Gujarati', size=12)
    pdf.cell(200, 10, txt=f"તારીખ: {date}", ln=True, align='L')
    pdf.ln(5)
    pdf.multi_cell(0, 10, txt=desc)
    
    pdf_output = pdf.output(dest='S').encode('latin-1', errors='ignore')
    b64 = base64.b64encode(pdf_output).decode('latin-1')
    href = f'<a href="data:application/pdf;base64,{b64}" download="report.pdf">📥 PDF ડાઉનલોડ કરો</a>'
    st.markdown(href, unsafe_allow_html=True)
