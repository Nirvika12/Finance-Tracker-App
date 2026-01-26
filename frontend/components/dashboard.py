import streamlit as st
import pandas as pd
import requests
import altair as alt
from datetime import datetime
import os

BASE_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Finance Dashboard", layout="wide")

# -------------------------------
# Helper for auth headers
# -------------------------------
def get_auth_headers():
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

# -------------------------------
# Dashboard Page
# -------------------------------
def dashboard_page():

    # -------------------------------
    # Fetch Data from APIs
    # -------------------------------
    @st.cache_data
    def fetch_transactions():
        try:
            resp = requests.get(f"{BASE_URL}/transactions/me", headers=get_auth_headers())
            if resp.status_code == 200:
                df = pd.DataFrame(resp.json())
                if not df.empty:
                    df['Date'] = pd.to_datetime(df['date'], errors='coerce')
                    df['Type'] = df['is_expense'].apply(lambda x: 'Expense' if x else 'Income')
                    df['signed_amount'] = df.apply(lambda r: -r['amount'] if r['is_expense'] else r['amount'], axis=1)
                    return df
        except Exception as e:
            st.error(f"Error fetching transactions: {e}")
        return pd.DataFrame()

    @st.cache_data
    def fetch_budgets(month):
        try:
            resp = requests.get(
                f"{BASE_URL}/dashboard/budget-category/",
                params={"month": month},
                headers=get_auth_headers()
            )
            if resp.status_code == 200:
                return pd.DataFrame(resp.json().get("budgets", []))
        except Exception as e:
            st.error(f"Error fetching budgets: {e}")
        return pd.DataFrame()

    @st.cache_data
    def fetch_categories():
        try:
            resp = requests.get(f"{BASE_URL}/category/", headers=get_auth_headers())
            if resp.status_code == 200:
                return pd.DataFrame(resp.json())
        except Exception as e:
            st.error(f"Error fetching categories: {e}")
        return pd.DataFrame()

    # -------------------------------
    # Load transactions
    # -------------------------------
    transactions = fetch_transactions()
    if transactions.empty:
        st.warning("No transactions found.")
        st.stop()

    # Prepare months & current month
    months = transactions['Date'].dt.to_period('M').astype(str).unique()
    current_month = datetime.today().strftime("%Y-%m")
    default_index = list(months).index(current_month) if current_month in months else 0

    # Sidebar filters
    selected_month = st.sidebar.selectbox("Select Month", months, index=default_index)
    selected_type = st.sidebar.multiselect("Transaction Type", ['Income', 'Expense'], default=['Income', 'Expense'])
    selected_categories = st.sidebar.multiselect(
        "Categories",
        options=transactions['category_name'].unique(),
        default=transactions['category_name'].unique()
    )

    # Filter transactions
    filtered_txn = transactions[
        (transactions['Date'].dt.to_period('M').astype(str) == selected_month) &
        (transactions['Type'].isin(selected_type)) &
        (transactions['category_name'].isin(selected_categories))
    ]

    # Fetch budgets
    budgets = fetch_budgets(selected_month)
    categories = fetch_categories()

    # -------------------------------
    # Top KPIs
    # -------------------------------
    st.title(f"💰 Finance Dashboard - {selected_month}")

    total_income = filtered_txn[filtered_txn['Type']=='Income']['signed_amount'].sum()
    total_expense = filtered_txn[filtered_txn['Type']=='Expense']['signed_amount'].abs().sum()
    balance = filtered_txn['signed_amount'].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("💵 Balance", f"${balance:.2f}")
    col2.metric("📈 Total Income", f"${total_income:.2f}")
    col3.metric("📉 Total Expenses", f"${total_expense:.2f}")

    # -------------------------------
    # Budget progress bars
    # -------------------------------
    if not budgets.empty:
        st.subheader("📊 Budget Progress by Category")
        for _, b in budgets.iterrows():
            spent = b.get('spent', 0)
            budget_amt = b.get('budget', 0)
            category_name = b.get('category_name', 'Category')
            progress = min(spent / budget_amt, 1.0) if budget_amt > 0 else 0

            st.markdown(f"**{category_name}**: Spent ${spent:.2f} / Budget ${budget_amt:.2f}")
            st.progress(progress)

    # -------------------------------
    # Charts
    # -------------------------------
    st.subheader("Expenses by Category")
    expense_data = filtered_txn[filtered_txn['Type']=='Expense'].groupby('category_name')['amount'].sum().abs().reset_index()
    chart1 = alt.Chart(expense_data).mark_bar().encode(
        x='category_name',
        y='amount',
        tooltip=['category_name', 'amount']
    )
    st.altair_chart(chart1, use_container_width=True)

    st.subheader("Income vs Expenses Over Time")
    time_data = filtered_txn.groupby(['Date','Type'])['signed_amount'].sum().reset_index()
    chart2 = alt.Chart(time_data).mark_line(point=True).encode(
        x='Date',
        y='signed_amount',
        color='Type',
        tooltip=['Date','Type','signed_amount']
    )
    st.altair_chart(chart2, use_container_width=True)

    st.subheader("Expense Distribution")
    pie_chart = alt.Chart(expense_data).mark_arc().encode(
        theta='amount',
        color='category_name',
        tooltip=['category_name','amount']
    )
    st.altair_chart(pie_chart, use_container_width=True)

    # -------------------------------
    # Recent Transactions Table
    # -------------------------------
    st.subheader("Recent Transactions")
    st.dataframe(filtered_txn.sort_values('Date', ascending=False).head(10))
