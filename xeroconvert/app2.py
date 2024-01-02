import streamlit as st

import streamlit as st
from datetime import datetime

# Date input
input_date = st.date_input("Select a date")

# Format the date for display or use in your code
formatted_date = input_date.strftime('%d-%b-%Y')

st.write("Formatted date:", formatted_date)