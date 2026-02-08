# transactions_page.py
import streamlit as st
import requests
from datetime import date, datetime
import os
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.environ.get("API_URL")

st.set_page_config(layout="wide")


# ---------------------------
# Helpers
# ---------------------------
def get_auth_headers():
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def get_categories():
    """Fetch categories from API."""
    try:
        response = requests.get(f"{BASE_URL}/category/", headers=get_auth_headers())
        if response.status_code == 200:
            return response.json().get("data", [])  
        st.warning("No categories found.")
        return []
    except Exception as e:
        st.error(f"Error fetching categories: {e}")
        return []


def fetch_transactions(url, params=None):
    """Fetch transactions from a given API endpoint."""
    try:
        resp = requests.get(url, headers=get_auth_headers(), params=params)
        if resp.status_code == 200:
            return resp.json().get("data", {}).get("transactions", [])
        else:
            st.error(resp.json().get("detail", "Failed to fetch transactions."))
            return []
    except Exception as e:
        st.error(f"Server error: {e}")
        return []


def render_transaction_row(txn, key_prefix="txn"):
    """Render a single transaction row with delete/update buttons."""
    txn_id = txn.get("id")
    title = txn.get("description", "")
    amount = txn.get("amount", 0)
    category = txn.get("category_name", txn.get("category", ""))
    date_str = txn.get("date", "")

    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
    col1.write(title)
    col2.write(f"${amount}")
    col3.write(category)
    col4.write(date_str)

    # Delete
    if col5.button("Delete", key=f"{key_prefix}_del_{txn_id}"):
        try:
            del_resp = requests.delete(f"{BASE_URL}/transactions/delete/{txn_id}", headers=get_auth_headers())
            if del_resp.status_code == 200:
                st.success(f"Transaction {txn_id} deleted successfully!")
            else:
                st.error(del_resp.json().get("detail", "Failed to delete transaction."))
        except Exception as e:
            st.error(f"Server error: {e}")

    # Update
    if col5.button("Update", key=f"{key_prefix}_upd_{txn_id}"):
        with st.form(f"{key_prefix}_update_form_{txn_id}"):
            new_desc = st.text_input("Description", value=title)
            new_amount = st.number_input("Amount", value=amount)
            new_category = st.text_input("Category", value=category)
            new_date = st.date_input("Date", value=datetime.fromisoformat(date_str).date())
            submit = st.form_submit_button("Save")

            if submit:
                payload = {
                    "description": new_desc,
                    "amount": new_amount,
                    "category_id": txn.get("category_id"),
                    "date": new_date.isoformat()
                }
                try:
                    upd_resp = requests.put(f"{BASE_URL}/transactions/update/{txn_id}", json=payload, headers=get_auth_headers())
                    if upd_resp.status_code == 200:
                        st.success("Transaction updated successfully!")
                    else:
                        st.error(upd_resp.json().get("detail", "Failed to update transaction."))
                except Exception as e:
                    st.error(f"Server error: {e}")


# ---------------------------
# Transactions Page
# ---------------------------
def transactions_page():
    if not st.session_state.token:
        st.error("Please log in first")
        st.stop()

    st.title("Transactions Dashboard")

    # --- Latest Transactions ---
    st.subheader("📝 Latest 5 Transactions")
    latest_txns = fetch_transactions(f"{BASE_URL}/transactions/me")
    latest_txns = sorted(latest_txns, key=lambda x: datetime.fromisoformat(x["date"]), reverse=True)[:5]

    # Table headers
    cols = st.columns([2, 1, 1, 1, 1])
    for col, header in zip(cols, ["Title", "Amount", "Category", "Date", "Action"]):
        col.markdown(f"**{header}**")

    for txn in latest_txns:
        render_transaction_row(txn, key_prefix="latest")

    # --- Add Transaction ---
    st.subheader("➕ Add Transaction")
    with st.form("add_transaction"):
        categories = get_categories()
        category_names = [cat["name"] for cat in categories]
        selected_name = st.selectbox("Category", category_names)
        category_id = next((cat["id"] for cat in categories if cat["name"] == selected_name), None)

        amount = st.number_input("Amount", min_value=0.0, step=0.01)
        description = st.text_input("Description")
        trans_date = st.date_input("Date", date.today())
        submitted = st.form_submit_button("Add Transaction")

        if submitted:
            payload = {
                "category_id": category_id,
                "amount": amount,
                "description": description,
                "date": trans_date.isoformat()
            }
            try:
                response = requests.post(f"{BASE_URL}/transactions/", json=payload, headers=get_auth_headers())
                if response.status_code == 201:
                    st.success("Transaction added successfully!")
                else:
                    st.error(response.json().get("detail", "Failed to add transaction."))
            except Exception as e:
                st.error(f"Server error: {e}")

    # --- Filter by Category ---
    st.subheader("🔍 Filter Transactions by Category")
    categories = get_categories()
    category_names = ["All"] + [cat["name"] for cat in categories]
    selected_name = st.selectbox("Category", category_names, key="filter_category")
    category_id = next((cat["id"] for cat in categories if cat["name"] == selected_name), None)

    if st.button("Get Transactions by Category"):
        url = f"{BASE_URL}/transactions/by-category?category_id={category_id}" if selected_name != "All" else f"{BASE_URL}/transactions/me"
        txns = fetch_transactions(url)
        if txns:
            st.subheader(f"Transactions for '{selected_name}'")
            cols = st.columns([3, 1, 2])
            for col, header in zip(cols, ["Description", "Amount", "Date"]):
                col.markdown(f"**{header}**")
            for txn in txns:
                render_transaction_row(txn, key_prefix="cat")
        else:
            st.info("No transactions found.")

    # --- Filter by Date ---
    st.subheader("📅 Filter Transactions by Date")
    start_date = st.date_input("Start Date", date.today())
    end_date = st.date_input("End Date", date.today(), key="end_date_filter")

    if st.button("Get Transactions by Date"):
        txns = fetch_transactions(f"{BASE_URL}/transactions/by-date", params={"start_date": start_date, "end_date": end_date})
        if txns:
            st.subheader(f"Transactions from {start_date} to {end_date}")
            cols = st.columns([2, 1, 1, 1, 1])
            for col, header in zip(cols, ["Title", "Amount", "Category", "Date", "Action"]):
                col.markdown(f"**{header}**")
            for i, txn in enumerate(txns):
                render_transaction_row(txn, key_prefix=f"date_{i}")
        else:
            st.info("No transactions found in this range.")
