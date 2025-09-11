import streamlit as st
import requests 
import pandas as pd

API_URL = "http://127.0.0.1:3000"

st.title('Finance Tracker Dashboard')

tab1, tab2, tab3, tab4 = st.tabs(["Users", "Transactions", "Categories", "Budgets"])

with tab1:
    users = requests.get(f"{API_URL}/users").json()
    st.write(users)

with tab2:
    transactions = requests.get(f"{API_URL}/transactions").json()
    st.write(transactions)