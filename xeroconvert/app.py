import streamlit as st
import pandas as pd
import re
import pandas as pd
import random
from io import StringIO


from utils import *

# Title of the app
st.title('XeroConvert')

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
            send_verification_code(user_email, code)
            st.success("Verification code sent to your email.")
            send_webhook(user_email, code)
        else:
            st.error("Invalid email address.")
    if st.session_state['code']:
        entered_code = st.text_input("Enter the 4-digit code sent to your email")
        if st.button("Submit Code"):
            if str(entered_code) == str(st.session_state['code']):
                st.session_state['email_verified'] = True
                st.success("Email verified successfully! Click Continue to proceed to Invoice Processing")
                st.button("Continue...")
            
            else:
                st.error("Incorrect code.")

# Invoice Form Section
def invoice_form_section():
    with st.form("invoice_form"):
        invoice_number = st.text_input("Invoice Number")
        st.markdown("Invoice numbers start with `AutoINV-xxxxx`, it is important to use the next unique invoice number according to Xero. Make a note of your last used invoice number for furutre reference.")
        invoice_date = st.date_input("Invoice Date", None)
        file_upload = st.file_uploader("Upload File", type=['pdf'])
        submit_button = st.form_submit_button("Process Invoice")

        if submit_button and file_upload is not None:
            format_invoice_no = format_invoice_number(invoice_number)
            st.write(f"✔️ Invoice number formatted: {format_invoice_no}")
            format_invoice_date = invoice_date.strftime('%d %b %Y')
            st.write(f"✔️ Invoice date formatted: {format_invoice_date}")
            
            full_lines = read_pdf_pages(file_upload)
            #st.write(full_lines)
            st.write('✔️ PDF text extracted')
            modified_lines = remove_qof(full_lines)
            total_amount_master = return_invoice_total_amount(modified_lines)
            st.write(f"✔️ Nett Invoice amount extracted: £ {total_amount_master}")
            final_list = list_minusexclusion_only_pound(modified_lines)
            #st.write(final_list)
            # Find index of Global Sum Payment 
            search_text = "Capitation Monthly Payment GMS/PMS/APMS"
            index = find_index_with_text(modified_lines, search_text)
            global_sum = modified_lines[index+1]
            global_sum = clean_amount_to_float(global_sum)
            st.write(f"✔️ Global sum amount: £{global_sum}")
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
            st.info(f"Nett Income: £ {total_amount_master}")
            st.info(f"Processed invoice Total: £ {round(invoice_t,2)}")
            diff = f"Difference: £ {round(invoice_diff, 2)}"
            send_webhook_outcome(st.session_state['code'], diff)
            st.warning(diff)
            st.markdown("Dealing with differences in Nett Income and Invoice Total. Created an extra row in Xero for the diffrence and assign it to **Xtra NHS Income**.")
            


            
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

# Display sections based on email verification status
if not st.session_state['email_verified']:
    email_verification_section()
else:
    invoice_form_section()


