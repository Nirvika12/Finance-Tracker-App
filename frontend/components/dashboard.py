import streamlit as st
import pandas as pd
import numpy as np
import datetime
import altair as alt

# --------------------------
# Placeholder Data
# --------------------------
np.random.seed(42)
categories = ['Food', 'Rent', 'Transport', 'Entertainment', 'Salary', 'Other']
dates = pd.date_range(end=datetime.date.today(), periods=50).to_pydatetime().tolist()
transactions = pd.DataFrame({
    'Date': np.random.choice(dates, 50),
    'Description': np.random.choice(['Grocery', 'Movie', 'Taxi', 'Salary', 'Rent', 'Shopping'], 50),
    'Category': np.random.choice(categories, 50),
    'Amount': np.random.randint(-500, 2000, 50)
})
transactions['Type'] = transactions['Amount'].apply(lambda x: 'Income' if x > 0 else 'Expense')

# --------------------------
# Sidebar Filters
# --------------------------
st.sidebar.header("Filters")
start_date = st.sidebar.date_input("Start Date", value=transactions['Date'].min())
end_date = st.sidebar.date_input("End Date", value=transactions['Date'].max())
selected_categories = st.sidebar.multiselect("Select Categories", options=categories, default=categories)

# Filter data based on user selection
filtered = transactions[
    (transactions['Date'] >= pd.to_datetime(start_date)) &
    (transactions['Date'] <= pd.to_datetime(end_date)) &
    (transactions['Category'].isin(selected_categories))
]

# --------------------------
# Top KPIs
# --------------------------
st.title("💰 Finance Tracker Dashboard")

total_income = filtered[filtered['Type']=='Income']['Amount'].sum()
total_expense = filtered[filtered['Type']=='Expense']['Amount'].sum()
balance = total_income + total_expense  # Expenses are negative

col1, col2, col3 = st.columns(3)
col1.metric("💵 Total Balance", f"${balance}")
col2.metric("📈 Total Income", f"${total_income}")
col3.metric("📉 Total Expenses", f"${abs(total_expense)}")

# --------------------------
# Charts
# --------------------------
st.subheader("Expenses by Category")
expense_data = filtered[filtered['Type']=='Expense'].groupby('Category')['Amount'].sum().abs().reset_index()

chart1 = alt.Chart(expense_data).mark_bar().encode(
    x='Category',
    y='Amount',
    tooltip=['Category', 'Amount']
).properties(width=600)
st.altair_chart(chart1, use_container_width=True)

st.subheader("Income vs Expenses Over Time")
time_data = filtered.groupby(['Date', 'Type'])['Amount'].sum().reset_index()
chart2 = alt.Chart(time_data).mark_line(point=True).encode(
    x='Date',
    y='Amount',
    color='Type',
    tooltip=['Date', 'Type', 'Amount']
).properties(width=700)
st.altair_chart(chart2, use_container_width=True)

# --------------------------
# Recent Transactions
# --------------------------
st.subheader("Recent Transactions")
st.dataframe(filtered.sort_values(by='Date', ascending=False).head(10))
