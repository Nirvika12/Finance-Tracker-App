# transactions_page.py
import streamlit as st
import requests
from datetime import date, datetime

BASE_URL = "http://127.0.0.1:8000/"

st.set_page_config(layout="wide")


def get_categories():
    try:
        response = requests.get(f"{BASE_URL}/category/")
        if response.status_code == 200:
            data = response.json()
            # Return just the names or full objects if needed
            return data
        else:
            st.warning("No categories found.")
            return []
    except Exception as e:
        st.error(f"Error fetching categories: {e}")
        return []

def transactions_page(user_id):
    st.title("Transactions Dashboard")

    # --- Get all transactions ---
    try:
        response = requests.get(f"{BASE_URL}/transactions/{user_id}")  # Adjust your API endpoint
        
        if response.status_code == 200:
            transactions = response.json()

            if not transactions:
                st.info("No transactions found.")
                return
        
            transactions_sorted = sorted(
            transactions, key=lambda x: datetime.fromisoformat(x['date']), reverse=True
            )
            latest_transactions = transactions_sorted[:5]


            st.subheader("📝 Latest 5 Transactions")

            # Display headers
            cols = st.columns([2, 1, 1, 1, 1])
            headers = ["Title", "Amount", "Category", "Date", "Action"]
            for col, header in zip(cols, headers):
                col.markdown(f"**{header}**")

            # Display each transaction
            for txn in latest_transactions:
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

                # Actions: Update / Delete
                if col5.button("Delete", key=f"del_{txn_id}"):
                    try:
                        del_resp = requests.delete(f"{BASE_URL}/transactions/delete/{txn_id}")
                        if del_resp.status_code == 200:
                            st.success(f"Transaction {txn_id} deleted successfully!")
                            st.rerun()  
                        else:
                            st.error(del_resp.json().get("detail", "Failed to delete transaction."))
                    except Exception as e:
                        st.error(f"Server error: {e}")

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
                                "category_id": txn.get("category_id"),  # keep same category or map if changed
                                "date": new_date.isoformat()
                            }
                            try:
                                upd_resp = requests.put(f"{BASE_URL}/transactions/update/{txn_id}", json=payload)
                                if upd_resp.status_code == 200:
                                    st.success("Transaction updated successfully!")
                                    st.rerun()
                                else:
                                    st.error(upd_resp.json().get("detail", "Failed to update transaction."))
                            except Exception as e:
                                st.error(f"Server error: {e}")

        else:
            st.error("Failed to fetch transactions.")
    except Exception as e:
        st.error(f"Server error: {e}")


    # --- Create a new transaction ---
    st.subheader("Add Transaction")
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
                "user_id": user_id,
                "category_id": category_id,
                "amount": amount,
                "description": description,
                "date": str(trans_date)
            }
            response = requests.post(BASE_URL + "transactions"+ "/", json=payload)
            if response.status_code == 200:
                st.success("Transaction added successfully!")
            else:
                st.error("Failed to add transaction.")

    st.subheader("🔍 Filter Transactions by Category")

    # Fetch categories
    categories = get_categories()
    category_names = [cat['name'] for cat in categories]
    selected_name = st.selectbox("Category", category_names)
    category_id = next((cat['id'] for cat in categories if cat['name'] == selected_name), None)

    if st.button("Get Transactions by Category"):
        try:
            response = requests.get(BASE_URL + f"/transactions/by-category?user_id={user_id}&category_id={category_id}")
            if response.status_code == 200:
                transactions = response.json()
                
                if not transactions:
                    st.info("No transactions found for this category.")
                else:
                    st.subheader(f"Transactions for '{selected_name}'")
                    
                    # Table headers
                    cols = st.columns([3, 1, 2])  # Adjust width as needed
                    headers = ["Description", "Amount", "Date"]
                    for col, header in zip(cols, headers):
                        col.markdown(f"**{header}**")
                    
                    # Display each transaction
                    for txn in transactions:
                        description = txn.get("description", "")
                        amount = txn.get("amount", 0)
                        date_str = txn.get("date", "")

                        col1, col2, col3 = st.columns([3, 1, 2])
                        col1.write(description)
                        col2.write(f"${amount}")
                        col3.write(date_str)
            else:
                st.error("No transactions found for this category.")
        except Exception as e:
            st.error(f"Server error: {e}")



    # --- Filter transactions by date ---
    st.subheader("Filter Transactions by Date")
    start_date = st.date_input("Start Date", date.today())
    end_date = st.date_input("End Date", date.today(), key="end_date_filter")

    if st.button("Get Transactions by Date"):
        try:
            response = requests.get(
                BASE_URL + f"/transactions/by-date?start_date={start_date}&end_date={end_date}"
            )

            if response.status_code == 200:
                transactions = response.json()

                if not transactions:
                    st.info("No transactions found in this range.")
                else:
                    st.subheader(f"Transactions from {start_date} to {end_date}")

                    # Display headers
                    cols = st.columns([2, 1, 1, 1, 1])
                    headers = ["Title", "Amount", "Category", "Date", "Action"]
                    for col, header in zip(cols, headers):
                        col.markdown(f"**{header}**")

                    # Display each transaction
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

                        # Unique keys for Delete/Update buttons
                        if col5.button("Delete", key=f"del_date_{i}_{txn_id}"):
                            try:
                                del_resp = requests.delete(f"{BASE_URL}/transactions/delete/{txn_id}")
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
                                        "category_id": txn.get("category_id"),  # keep same category
                                        "date": new_date.isoformat()
                                    }
                                    try:
                                        upd_resp = requests.put(f"{BASE_URL}/transactions/update/{txn_id}", json=payload)
                                        if upd_resp.status_code == 200:
                                            st.success("Transaction updated successfully!")
                                            st.experimental_rerun()
                                        else:
                                            st.error(upd_resp.json().get("detail", "Failed to update transaction."))
                                    except Exception as e:
                                        st.error(f"Server error: {e}")

            else:
                st.error("No transactions found in this range.")
        except Exception as e:
            st.error(f"Server error: {e}")
