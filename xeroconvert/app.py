import streamlit as st
import pandas as pd
import re
import pandas as pd
import random
from io import StringIO
import datetime
from trubrics.integrations.streamlit import FeedbackCollector

from utils import *

st.set_page_config(
    page_title="XeroConvert",
)
# Title of the app
html = """
<style>
.gradient-text {
    background: linear-gradient(45deg, #6e48aa, #bf4278, #579cc4, #e16d33);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    font-size: 3em;
    font-weight: bold;
}
</style>
<div class="gradient-text">XeroConvert <a href="https://janduplessis.notion.site/XeroConvert-Help-4a8586902d1a4adfaed23fcfa610fbdb?pvs=4">
    <img src="https://github.com/janduplessis883/project-xeroconvert/blob/master/images/icons8-help-24.png?raw=true" alt="FAQ & Help" style="width:16px;height:16px;"></a></div>
"""
# Render the HTML in the Streamlit app
st.markdown(html, unsafe_allow_html=True)
st.markdown("""**XeroConvert** is an innovative solution designed to simplify the account management and processing challenges faced by GP surgeries. This tool seamlessly converts **PCSE Payment Statements** into a formatted CSV file, optimized for direct import into **Xero**, the leading Online Accounting software.""")
st.markdown("""With XeroConvert, you can process a full year's worth of statements in less than an hour, revolutionizing your accounting practices.""")
st.markdown("Simply download your PCSE Statements as **Expanded PDFs**, upload them to XeroConvert, and let the Python magic extract the necessary information for you.")
# Initialize session state variables
if 'code' not in st.session_state:
    st.session_state['code'] = None
if 'email_verified' not in st.session_state:
    st.session_state['email_verified'] = False

# Email Verification Section
def email_verification_section():
    user_email = st.text_input('Enter your email address', value='')
    if st.button('Verify Email') and user_email:
        if is_valid_email(user_email):
            code = random.randint(1000, 9999)
            st.session_state['code'] = code
            st.session_state['user_email'] = user_email
            st.success("Verification code sent to your email.")
            send_verification_code(user_email, code)
            send_webhook(user_email, code)
        else:
            st.error("Invalid email address.")
    if st.session_state['code']:
        entered_code = st.text_input("Enter the 4-digit code sent to your email")
        if st.button("Submit Code"):
            if str(entered_code) == str(st.session_state['code']):
                st.session_state['email_verified'] = True
                st.success("Email verified successfully!")
                st.button("Continue to Statement Processing...")
            
            else:
                st.error("Incorrect code.")

# Invoice Form Section
def invoice_form_section():
    with st.form("invoice_form"):
        invoice_number = st.text_input("Invoice Number")
        st.markdown("Invoice numbers start with `AutoINV-xxxxx`, it is important to use the next unique invoice number according to Xero. Make a note of your last used invoice number for furutre reference.")
        invoice_date = st.date_input("Invoice Date", datetime.date.today())
        file_upload = st.file_uploader("Upload File", type=['pdf'])
        submit_button = st.form_submit_button("Process Invoice")

        if submit_button and file_upload is not None:
            format_invoice_no = format_invoice_number(invoice_number)
            st.write(f"✔️ Invoice number formatted: {format_invoice_no}")
            st.session_state['invoice_no'] = format_invoice_no
            format_invoice_date = invoice_date.strftime('%d %b %Y')
            st.write(f"✔️ Invoice date formatted: {format_invoice_date}")
            
            full_lines = read_pdf_pages(file_upload)
            full_lines = remove_qof(full_lines)
            st.write('✔️ PDF text extracted')
            total_amount_master = return_invoice_total_amount(full_lines)
            st.write(f"✔️ Nett Invoice amount extracted: £ {total_amount_master}")
            final_list = list_minusexclusion_only_pound(full_lines)

            # Find index of Global Sum Payment 
            index = find_index_with_text(full_lines, "Capitation Monthly Payment GMS/PMS/APMS")
            
            
            global_sum = full_lines[index+1]
            global_sum = clean_amount_to_float(global_sum)
            st.write(f"✔️ Global sum amount: £{global_sum}")
            
            index_aspiration = find_index_with_text(full_lines, 'Aspiration')

            aspiration_amount = return_invoice_aspiration(index_aspiration, full_lines)
            new_list = append_aspiration(final_list, aspiration_amount)
            st.write(f"✔️ QOF Aspiration: £{aspiration_amount}")
            new_list = append_global_sum(final_list, global_sum)
            # Create a progress bar
            st.write("Progress - Invoice Extraction")
            progress_bar = st.progress(0)
            def update_progress(progress):
                progress_bar.progress(progress)
            my_dict = build_df_lists(new_list, invoice_nu=format_invoice_no, invoice_da_te=format_invoice_date, progress_callback=update_progress)
            df = pd.DataFrame(my_dict)
            st.session_state['processed_df'] = df.to_csv(index=False).encode('utf-8')
            invoice_t = df['Total'][0]
            invoice_diff = calculate_diff(total_amount_master, invoice_t)
            diff = f"Difference: £ {round(invoice_diff, 2)}"
            st.info(f"Nett Income: £ {total_amount_master}")
            st.info(f"Processed invoice Total: £ {round(invoice_t,2)}")
            if invoice_diff != 0.0:
                st.warning(diff)
                st.markdown("Dealing with differences in Nett Income and Invoice Total. Created an extra row in Xero for the diffrence and assign it to **Xtra NHS Income**.")
                send_final_email(st.session_state['user_email'], st.session_state['invoice_no'], diff)
                
            send_webhook_outcome(st.session_state['code'], diff)
            
            collector = FeedbackCollector(
                project="default",
                email=st.secrets.TRUBRICS_EMAIL,
                password=st.secrets.TRUBRICS_PASSWORD,
            )

            collector.st_feedback(
                component="default",
                feedback_type="thumbs",
                open_feedback_label="[Optional] Provide additional feedback",
                model="gpt-3.5-turbo",
                prompt_id=None,  # see `Prompts` to log prompts and model generations
            )
            st.session_state['email_verified'] = False

            
        elif submit_button:
            st.warning("Please upload a PDF file.")
            
    # Outside the form, check if 'processed_df' is in session state
    if 'processed_df' in st.session_state and st.session_state['processed_df']:
        
        st.download_button(
            label="Download CSV for Xero Import",
            data=st.session_state['processed_df'],
            file_name=f'{return_timestamp()}_XeroImport.csv',
            mime='text/csv',
        )
        st.markdown("App by [janduplessis883](https://github.com/janduplessis883/project-xeroconvert)")

# Display sections based on email verification status
if not st.session_state['email_verified']:
    email_verification_section()
else:
    invoice_form_section()
    
    
