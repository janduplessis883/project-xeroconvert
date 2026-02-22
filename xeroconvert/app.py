import streamlit as st
import pandas as pd
import datetime
import streamlit_shadcn_ui as ui

from utils import *

st.set_page_config(
    page_title="XeroConvert",
)
# Title of the app
html = """
<style>
.gradient-text {
    background: linear-gradient(45deg, #6e48aa, #e73323, #9b5670, #4f7abd);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    font-size: 3em;
    font-weight: bold;
}
</style>
<div class="gradient-text">XeroConvert <a href="https://janduplessis.notion.site/XeroConvert-Help-4a8586902d1a4adfaed23fcfa610fbdb?pvs=4">
    <img src="https://github.com/janduplessis883/project-xeroconvert/blob/master/images/icons8-question-mark.gif?raw=true" alt="FAQ & Help" style="width:16px;height:16px;"></a></div>
"""
# Render the HTML in the Streamlit app
st.markdown(html, unsafe_allow_html=True)

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
            diff = f"Discrepancy Amount: £ {round(invoice_diff, 2)}"
            st.info(f"Nett Income: £ {total_amount_master}")
            st.info(f"Processed Statement Total: £ {round(invoice_t,2)}")
            if invoice_diff != 0.0:
                st.warning(diff)
                st.markdown("Dealing with differences in Nett Income and Invoice Total. Created an extra row in Xero for the diffrence and assign it to **Xtra NHS Income**.")
            
            


            
        elif submit_button:
            st.warning("Please upload a PDF file.")
            
    # Outside the form, check if 'processed_df' is in session state
    if 'processed_df' in st.session_state and st.session_state['processed_df']:
        
        st.download_button(
            label="Download CSV for Xero Import",
            data=st.session_state['processed_df'],
            file_name=f'{return_timestamp()}-Xero.csv',
            mime='text/csv',
        )
        st.markdown("App by [janduplessis883](https://github.com/janduplessis883/project-xeroconvert)")

switch_value = ui.switch(default_checked=False, label="Demo Video", key="switch1")
if switch_value == True:
    video_url = "https://youtu.be/2v31iyN6fHo?si=6I-PXLOyw8BDntKU"
    st.video(video_url)

st.markdown("""**XeroConvert** is an innovative solution designed to simplify the account management and processing challenges faced by GP surgeries. This tool seamlessly converts **PCSE Payment Statements** into a formatted CSV file, optimized for direct import into **Xero**, the leading Online Accounting software.""")
st.markdown("""With XeroConvert, you can process a full year's worth of statements in less than an hour, revolutionizing your accounting practices.""")
st.markdown("Simply download your PCSE Statements as **Expanded PDFs**, upload them to XeroConvert, and let the Python magic extract the necessary information for you.")

st.markdown("The **integrity of your data** is our top priority. Thus, uploaded PDFs and the generated CSV files are neither stored nor archived on our systems. As soon as the conversion process is complete, all files are permanently deleted, ensuring your sensitive financial information remains confidential and in your control at all times. With XeroConvert, you can rest assured that your accounting data is processed with the utmost security and discretion.")
ui.badges(badge_list=[("Secure", "default"), ("PCSE Income Statements", "outline"), ("Xero Cloud Accounting", "outline")], class_name="flex gap-2", key="badges1")
ui.badges(badge_list=[("Developed by Jan du Plessis, NHS GP Practice Manager, London - jan.duplessis@nhs.net", "secondary")], class_name="flex gap-2", key="badges2")
st.markdown('Please leave **feedback** when invited, to help improve this app.')
invoice_form_section()
    
    
