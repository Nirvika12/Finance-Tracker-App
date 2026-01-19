import streamlit as st
import pandas as pd
import requests
import altair as alt
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Finance Dashboard", layout="wide")


def dashboard_page(user_id):

    # -------------------------------
    # 1️⃣ Fetch Data from APIs
    # -------------------------------
    @st.cache_data
    def fetch_transactions(user_id):
        resp = requests.get(f"{BASE_URL}/transactions/{user_id}")
        if resp.status_code == 200:
            df = pd.DataFrame(resp.json())
            if not df.empty:
                df['Date'] = pd.to_datetime(df['date'])
                df['Type'] = df['amount'].apply(lambda x: 'Income' if x > 0 else 'Expense')
                return df
        return pd.DataFrame()

    @st.cache_data
    def fetch_budgets(user_id, month):
        resp = requests.get(f"{BASE_URL}/budget/monthly-status?user_id={user_id}&month={month}")
        if resp.status_code == 200:
            data = resp.json()
            budgets = pd.DataFrame(data.get("budgets", []))
            return budgets
        return pd.DataFrame()

    @st.cache_data
    def fetch_categories():
        resp = requests.get(f"{BASE_URL}/category/")
        if resp.status_code == 200:
            return pd.DataFrame(resp.json())
        return pd.DataFrame()

    # -------------------------------
    # 2️⃣ Load transactions & filter
    # -------------------------------
    transactions = fetch_transactions(user_id)
    if transactions.empty:
        st.warning("No transactions found.")
        st.stop()

    # Prepare months & current month
    months = transactions['Date'].dt.to_period('M').astype(str).unique()
    current_month = datetime.today().strftime("%Y-%m")
    default_index = list(months).index(current_month) if current_month in months else 0

    selected_month = st.sidebar.selectbox("Select Month", months, index=default_index)
    selected_type = st.sidebar.multiselect("Transaction Type", ['Income', 'Expense'], default=['Income', 'Expense'])
    selected_categories = st.sidebar.multiselect(
        "Categories",
        options=transactions['category_name'].unique(),
        default=transactions['category_name'].unique()
    )

    # Filter transactions based on sidebar selection
    filtered_txn = transactions[
        (transactions['Date'].dt.to_period('M').astype(str) == selected_month) &
        (transactions['Type'].isin(selected_type)) &
        (transactions['category_name'].isin(selected_categories))
    ]

    # Fetch budgets & categories
    budgets = fetch_budgets(user_id, selected_month)
    categories = fetch_categories()

    # -------------------------------
    # 3️⃣ Top KPIs
    # -------------------------------
    st.title(f"💰 Finance Dashboard - {selected_month}")

    total_income = filtered_txn[filtered_txn['Type']=='Income']['amount'].sum()
    total_expense = filtered_txn[filtered_txn['Type']=='Expense']['amount'].abs().sum()
    balance = total_income - total_expense

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
            budget_amt = b.get('amount', 0)
            category_name = b.get('category_name', 'Category')
            progress = min(spent / budget_amt, 1.0) if budget_amt > 0 else 0

            # Display nicely
            st.markdown(f"**{category_name}**: Spent ${spent:.2f} / Budget ${budget_amt:.2f}")
            st.progress(progress)


    # -------------------------------
    # 4️⃣ Charts
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
    time_data = filtered_txn.groupby(['Date','Type'])['amount'].sum().reset_index()
    chart2 = alt.Chart(time_data).mark_line(point=True).encode(
        x='Date',
        y='amount',
        color='Type',
        tooltip=['Date','Type','amount']
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
    # 5️⃣ Recent Transactions Table
    # -------------------------------
    st.subheader("Recent Transactions")
    st.dataframe(filtered_txn.sort_values('Date', ascending=False).head(10))
