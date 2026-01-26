# transactions_page.py
import streamlit as st
import requests
from datetime import date, datetime
import os

BASE_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")

st.set_page_config(layout="wide")


# ---------------------------
# Get categories
# ---------------------------
def get_categories():
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    try:
        response = requests.get(f"{BASE_URL}/category/", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.warning("No categories found.")
            return []
    except Exception as e:
        st.error(f"Error fetching categories: {e}")
        return []


# ---------------------------
# Transactions Page
# ---------------------------
def transactions_page():
    if not st.session_state.token:
        st.error("You must be logged in to view transactions.")
        return

    headers = {"Authorization": f"Bearer {st.session_state.token}"}

    st.title("Transactions Dashboard")

    # ---------------------------
    # Fetch all transactions
    # ---------------------------
    try:
        response = requests.get(f"{BASE_URL}/transactions/me", headers=headers)
        if response.status_code == 200:
            transactions = response.json() or []

            # Sort by date descending
            transactions_sorted = sorted(
                transactions, key=lambda x: datetime.fromisoformat(x['date']), reverse=True
            )
            latest_transactions = transactions_sorted[:5]

            st.subheader("📝 Latest 5 Transactions")

            # Table headers
            cols = st.columns([2, 1, 1, 1, 1])
            headers_list = ["Title", "Amount", "Category", "Date", "Action"]
            for col, header in zip(cols, headers_list):
                col.markdown(f"**{header}**")

            for i, txn in enumerate(latest_transactions):
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

                # Delete button
                if col5.button("Delete", key=f"del_{txn_id}"):
                    try:
                        del_resp = requests.delete(f"{BASE_URL}/transactions/delete/{txn_id}", headers=headers)
                        if del_resp.status_code == 200:
                            st.success(f"Transaction {txn_id} deleted successfully!")
                            st.experimental_rerun()
                        else:
                            st.error(del_resp.json().get("detail", "Failed to delete transaction."))
                    except Exception as e:
                        st.error(f"Server error: {e}")

                # Update button
                if col5.button("Update", key=f"upd_{txn_id}"):
                    with st.form(f"update_form_{txn_id}"):
                        new_desc = st.text_input("Description", value=title)
                        new_amount = st.number_input("Amount", value=amount)
                        new_category = st.text_input("Category", value=category)
                        new_date = st.date_input("Date", value=datetime.fromisoformat(date_str).date())
                        submit = st.form_submit_button("Save")

                        if submit:
                            payload = {
                                "description": new_desc,
                                "amount": new_amount,
                                "category_id": txn.get("category_id"),  # keep same category
                                "date": new_date.isoformat()
                            }
                            try:
                                upd_resp = requests.put(f"{BASE_URL}/transactions/update/{txn_id}", json=payload, headers=headers)
                                if upd_resp.status_code == 200:
                                    st.success("Transaction updated successfully!")
                                    st.experimental_rerun()
                                else:
                                    st.error(upd_resp.json().get("detail", "Failed to update transaction."))
                            except Exception as e:
                                st.error(f"Server error: {e}")

        else:
            st.error("Failed to fetch transactions from server.")
            transactions = []

    except Exception as e:
        st.error(f"Server error: {e}")
        transactions = []

    # ---------------------------
    # Add new transaction
    # ---------------------------
    st.subheader("➕ Add Transaction")
    with st.form("add_transaction"):
        categories = get_categories()
        category_names = [cat['name'] for cat in categories]
        selected_name = st.selectbox("Category", category_names)
        category_id = next((cat['id'] for cat in categories if cat['name'] == selected_name), None)

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
                response = requests.post(f"{BASE_URL}/transactions/", json=payload, headers=headers)
                if response.status_code == 200:
                    st.success("Transaction added successfully!")
                    st.experimental_rerun()
                else:
                    st.error(response.json().get("detail", "Failed to add transaction."))
            except Exception as e:
                st.error(f"Server error: {e}")

    # ---------------------------
    # Filter by category
    # ---------------------------
    st.subheader("🔍 Filter Transactions by Category")
    categories = get_categories()
    category_names = ["All"] + [cat['name'] for cat in categories]
    selected_name = st.selectbox("Category", category_names, key="filter_category")
    category_id = next((cat['id'] for cat in categories if cat['name'] == selected_name), None)

    if st.button("Get Transactions by Category"):
        try:
            url = f"{BASE_URL}/transactions/by-category?category_id={category_id}" if selected_name != "All" else f"{BASE_URL}/transactions/me"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                transactions = response.json()
                if not transactions:
                    st.info("No transactions found.")
                else:
                    st.subheader(f"Transactions for '{selected_name}'")
                    cols = st.columns([3, 1, 2])
                    headers_list = ["Description", "Amount", "Date"]
                    for col, header in zip(cols, headers_list):
                        col.markdown(f"**{header}**")

                    for txn in transactions:
                        col1, col2, col3 = st.columns([3, 1, 2])
                        col1.write(txn.get("description", ""))
                        col2.write(f"${txn.get('amount', 0)}")
                        col3.write(txn.get("date", ""))

            else:
                st.error("Failed to fetch transactions by category.")
        except Exception as e:
            st.error(f"Server error: {e}")

    # ---------------------------
    # Filter by date
    # ---------------------------
    st.subheader("📅 Filter Transactions by Date")
    start_date = st.date_input("Start Date", date.today())
    end_date = st.date_input("End Date", date.today(), key="end_date_filter")

    if st.button("Get Transactions by Date"):
        try:
            response = requests.get(f"{BASE_URL}/transactions/by-date?start_date={start_date}&end_date={end_date}", headers=headers)
            if response.status_code == 200:
                transactions = response.json()
                if not transactions:
                    st.info("No transactions found in this range.")
                else:
                    st.subheader(f"Transactions from {start_date} to {end_date}")
                    cols = st.columns([2, 1, 1, 1, 1])
                    headers_list = ["Title", "Amount", "Category", "Date", "Action"]
                    for col, header in zip(cols, headers_list):
                        col.markdown(f"**{header}**")
                    
                    for i, txn in enumerate(transactions):
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

                        if col5.button("Delete", key=f"del_date_{i}_{txn_id}"):
                            try:
                                del_resp = requests.delete(f"{BASE_URL}/transactions/delete/{txn_id}", headers=headers)
                                if del_resp.status_code == 200:
                                    st.success(f"Transaction {txn_id} deleted successfully!")
                                    st.experimental_rerun()
                                else:
                                    st.error(del_resp.json().get("detail", "Failed to delete transaction."))
                            except Exception as e:
                                st.error(f"Server error: {e}")

                        if col5.button("Update", key=f"upd_date_{i}_{txn_id}"):
                            with st.form(f"update_form_date_{i}_{txn_id}"):
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
                                        upd_resp = requests.put(f"{BASE_URL}/transactions/update/{txn_id}", json=payload, headers=headers)
                                        if upd_resp.status_code == 200:
                                            st.success("Transaction updated successfully!")
                                            st.experimental_rerun()
                                        else:
                                            st.error(upd_resp.json().get("detail", "Failed to update transaction."))
                                    except Exception as e:
                                        st.error(f"Server error: {e}")

        except Exception as e:
            st.error(f"Server error: {e}")
