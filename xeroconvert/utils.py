from datetime import datetime
import time
from colorama import Fore, Back, Style, init
init(autoreset=True)
from PyPDF2 import PdfReader
import io
import re
import contiguity
import os
import datetime
import requests

client_id = os.environ.get("CONTIGUITY_API")
client = contiguity.login(client_id)




# = Backend Functions + Operations =================================================================


# Function to check if an email is valid
def is_valid_email(email):
    # Regular expression for validating an email
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.fullmatch(regex, email):
        return True
    return False

        
# Function to send verification code via email
def send_verification_code(email, code):
    email_message = f"""Hi,<BR>
        Thank you for using <b>XeroConvert</b>!<BR>Your verification code is:
        <h1>{code}</h1>
        Please enter this code into the XeroConvert App to continue with PCSE Invoice convertions.<BR><BR>
        Best wishes,<BR>
        <B>XeroConvert</B>"""
        
    email_object = {
        "to": email,
        "from": "XeroConvert",
        "replyTo": "jan.duplessis@nhs.net",
        "subject": "XeroConvert - Verification Email",
        "html": email_message,
    }

    client.send.email(email_object)
    print("👍 Verification email sent!")
    
def send_final_email(email, diff):
    email_message = f"""Hi,<BR>
        Thank you for using <b>XeroConvert</b>!<BR>Please ensure you download your processed invoice via the download button on the app.<BR>
        Your invoice has shown a differece of:
        <h2>{diff}</h2>
        This can happend and the quickest way to deal with this is Xero is to add an additional row on your inoice with the difference amount (neg or positive), and assign it account reference Xtra NHS Income.<BR>
        If you have any questiosn please feel free to reply to this email.<BR><B>Share this tool with your colleagues.</b><BR><BR>
        Best wishes,<BR>
        <B>XeroConvert</B><BR><BR>
        <img src='https://github.com/janduplessis883/project-xeroconvert/blob/master/images/bmc_qr.png?raw=true' width=150>
        """
        
    email_object = {
        "to": email,
        "from": "XeroConvert",
        "replyTo": "jan.duplessis@nhs.net",
        "subject": "XeroConvert - Outcome",
        "html": email_message,
    }

    client.send.email(email_object)
    print("👍 Verification email sent!")

# Get Text off PDF Pages, one at a time
def read_pdf_pages(loaded_pdf):
    reader = PdfReader(io.BytesIO(loaded_pdf.read())) 
    full_text = ''
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text
    full_lines_list = full_text.splitlines()
    return full_lines_list
    
    
def remove_qof(lines_list):
    phrase_to_remove = 'Quality Outcomes Framework'
    modified_list = [my_string.replace(phrase_to_remove, '') for my_string in lines_list]
    return modified_list

def return_invoice_total_amount(lines_list):
    total_paid = lines_list[-1]
    total_amount = float(total_paid.split('£')[-1].replace(",",""))
    return total_amount

def list_minusexclusion_only_pound(input_list):
    final_list = []
    exclude_list = ["Paycode Description", "GMC Code Name Tier Rate", "Paycode Description", "Type Source", "Total Amount Paid", "Invoice", "Net", "Credit", "Percentage Received",  'GMC Code Name Month']
    for list in input_list:
        if [ex for ex in exclude_list if(ex in list)]:
            pass
        elif "£" in list:
            final_list.append(str(list))
            
    return final_list

def find_index_with_text(my_list, search_text):
    for index, string in enumerate(my_list):
        if search_text in string:
            return index
    return -1  # Return -1 or some other value to indicate the text was not found

def clean_amount_to_float(input_string):
    output = input_string.replace(",","")
    return float(output)

def append_global_sum(input_list, amount):
    input_list.append(f"Global Sum £{str(amount)}")
    return input_list

def format_invoice_number(input_number):
    return f"AutoINV-{str(input_number)}"


# Function to assign account_code
def get_account_no(invoice_description, account_code_dic):
    for x, y in account_code_dic.items():
        if x in invoice_description:
            return y  # Return immediately when a match is found
    return ""  # Return an empty string if no match is found

def build_df_lists(input_list, invoice_nu, invoice_da_te, progress_callback=None):
    #Declairing required variables.
    contact_name = []
    email_address = []
    PO1 = []
    PO2 = []
    PO3 = []
    PO4 = []
    city = []
    PO_region = []
    postal_code = []
    country = []
    address1 = []
    address2 = []
    address3 = []
    address4 = []
    sa_city = []
    sa_region = []
    sa_postalcode = []
    sa_country = []
    invoice_number = []
    ref = []
    invoice_date = []
    due_date = []
    planned_date = []
    total = []
    tax_total = []
    invoice_amount_paid = []
    invoice_amount_due = []
    inv_item_code = []
    description = []
    quantitiy = []
    unit_amount = []
    line_amount = []
    account_code = []
    tax_type = []
    discount =[]
    tax_amount = []
    trackn1 = []
    tracko1 = []
    trackn2 = []
    tracko2 = []
    currency = []
    type_ = []
    sent = []
    status = []
    
    account_code_dict = {
    "rates": "102",
    "childhood flu": "124A",
    "influenza": "124",
    "mmr": "137",
    "pneumoc": "125",
    "rotavirus": "128",
    "hpv": "158",
    "men b": "135",
    "hib/men c": "135A",
    "6 in 1": "120",
    "pms cis": "209",
    "last phase of life": "165",
    "hard to reach": "193",
    "carers": "193",
    "my way": "183B",
    "access": "193",
    "long covid": "193",
    "pcn participation": "250B",
    "rent": "111",
    "prescribing": "203",
    "ecg": "185",
    "spoke": "132A",
    "warfarin": "181",
    "homeless": "186",
    "wound": "192",
    "mental": "187",
    "diabetes": "184",
    "phlebotomy": "189",
    "coordinate": "183",
    "levy": "523",
    "global": "100",
    "aspiration": "103"
    }
    
    for i, l in enumerate(input_list):
        if progress_callback is not None:
            progress = (i + 1) / len(input_list)
            time.sleep(0.08)
            progress_callback(progress)
            
        if "-£" in l:

            # Split once at the first occurrence of "-£"
            value_pair_list = l.split("-£", 1)
            invoiceable_desc = value_pair_list[0]
            invoice_desc_lower = invoiceable_desc.lower()

            # There should not be a second split on "£" here as it's already split above
            invoiceable_value_str = value_pair_list[-1].replace(",", "")
            
            invoiceable_value = float(invoiceable_value_str)
            invoiceable_value = invoiceable_value * -1
            contact_name.append('NHS England GMS')
            email_address.append("")
            PO1.append("")
            PO2.append('')
            PO3.append('')
            PO4.append('')
            city.append('')
            PO_region.append('')
            postal_code.append('')
            country.append('')
            address1.append('')
            address2.append('')
            address3.append('')
            address4.append('')
            sa_city.append('')
            sa_region.append('')
            sa_postalcode.append('')
            sa_country.append('')
            invoice_number.append(invoice_nu)
            ref.append('')
            invoice_date.append(invoice_da_te)
            due_date.append(invoice_da_te)
            planned_date.append('')
            tax_total.append(0)
            invoice_amount_paid.append(0)
            inv_item_code.append('')
            description.append(invoiceable_desc)
            quantitiy.append(1)
            unit_amount.append(invoiceable_value)
            invoice_amount_due.append(invoiceable_value)
            discount.append('')
            line_amount.append(invoiceable_value)
            tax_type.append('No VAT')
            tax_amount.append(0)
            trackn1.append('')
            tracko1.append('')
            trackn2.append('')
            tracko2.append('')
            currency.append('GBP')
            type_.append('Sales Invoice')
            sent.append('')
            status.append('')
            account_code.append(get_account_no(invoice_desc_lower, account_code_dict))

        else:
            # Split once at the first occurrence of "£"
            value_pair_list = l.split("£", 1)
            invoiceable_desc = value_pair_list[0]
            invoice_desc_lower = invoiceable_desc.lower()

            invoiceable_value_str = value_pair_list[-1].replace(",", "")
            invoiceable_value = float(invoiceable_value_str)
        
            contact_name.append('NHS England GMS')
            email_address.append("")
            PO1.append("")
            PO2.append('')
            PO3.append('')
            PO4.append('')
            city.append('')
            PO_region.append('')
            postal_code.append('')
            country.append('')
            address1.append('')
            address2.append('')
            address3.append('')
            address4.append('')
            sa_city.append('')
            sa_region.append('')
            sa_postalcode.append('')
            sa_country.append('')
            invoice_number.append(invoice_nu)
            ref.append('')
            invoice_date.append(invoice_da_te)
            due_date.append(invoice_da_te)
            planned_date.append('')
            tax_total.append(0)
            invoice_amount_paid.append(0)
            inv_item_code.append('')
            description.append(invoiceable_desc)
            quantitiy.append(1)
            unit_amount.append(invoiceable_value)
            discount.append('')
            line_amount.append(invoiceable_value)
            invoice_amount_due.append(invoiceable_value)
            account_code.append(get_account_no(invoice_desc_lower, account_code_dict))
            tax_type.append('No VAT')
            tax_amount.append(0)
            trackn1.append('')
            tracko1.append('')
            trackn2.append('')
            tracko2.append('')
            currency.append('GBP')
            type_.append('Sales Invoice')
            sent.append('')
            status.append('')
            
        if progress_callback is not None:
            progress = (i + 1) / len(input_list)
            progress_callback(progress)
            
    total_amount = sum(unit_amount)
    for i in range(len(unit_amount)):
        total.append(total_amount)
            
    output_dict = {
        'ContactName': contact_name,
        'EmailAddress': email_address,
        'POAddressLine1':PO1,
        'POAddressLine2': PO2,
        'POAddressLine3': PO3,
        'POAddressLine4': PO4,
        'POCity': city,
        'PORegion': PO_region,
        'POPostalCode': postal_code,
        'POCountry': country,
        'SAAddressLine1': address1,
        'SAAddressLine2': address2,
        'SAAddressLine3': address3,
        'SAAddressLine4': address4,
        'SACity': sa_city,
        'SARegion': sa_region,
        'SAPostalCode': sa_postalcode,
        'SACountry': sa_country,
        'InvoiceNumber': invoice_number,
        'Reference': ref,
        'InvoiceDate': invoice_date,
        'DueDate': invoice_date,
        'PlannedDate': invoice_date,
        'Total': total,
        'TaxTotal': tax_total,
        'InvoiceAmountPaid': invoice_amount_paid,
        'InvoiceAmountDue': invoice_amount_due,
        'InventoryItemCode': inv_item_code,
        'Description': description,
        'Quantity': quantitiy,
        'UnitAmount': unit_amount,
        'Discount': discount,
        'LineAmount': line_amount,
        'AccountCode': account_code,
        'TaxType': tax_type,
        'TaxAmount': tax_amount,
        'TrackingName1': trackn1,
        'TrackingOption1': tracko1,
        'TrackingName2': trackn2,
        'TrackingOption2': tracko2,
        'Currency':	currency,
        'Type':	type_,
        'Sent':	sent,
        'Status': status
    }
    

    return output_dict

def calculate_diff(invoice_nett, invoice_total):
    diff = invoice_nett - invoice_total
    return diff


def return_timestamp():
    # Get the current timestamp
    current_timestamp = datetime.datetime.now()

    # Convert the timestamp to a string
    # You can format the string as you like, here's an example format: YYYY-MM-DD HH:MM:SS
    timestamp_string = current_timestamp.strftime("%Y-%m-%d-%H-%M")

    return timestamp_string

def send_webhook(email, code):
    """
    Send a webhook with the specified email address.

    :param email: The email address to send.
    :param webhook_url: The URL of the webhook endpoint.
    """
    data = {'email': email,
            'code': code}
    response = requests.post('https://eo51s228rg0gorn.m.pipedream.net', json=data)
    return response

def send_webhook_outcome(code, amount):
    """
    Send a webhook with the specified email address.

    :param email: The email address to send.
    :param webhook_url: The URL of the webhook endpoint.
    """
    data = {'outcome': amount,
            'code': code}
    response = requests.post('https://eopqq9ouuddk92z.m.pipedream.net', json=data)
    return response

# # = Decorators =================================================================
def time_it(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        print(f"{Fore.YELLOW}[🏁] FUCTION: {func.__name__}()")
        result = func(*args, **kwargs)
        print(
            f"{Fore.GREEN}{Style.DIM}[✔️] Completed: {func.__name__}() - Time taken: {time.time() - start_time:.2f} seconds"
        )
        return result

    return wrapper