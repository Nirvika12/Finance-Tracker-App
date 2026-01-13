import streamlit as st
import requests
from datetime import date, datetime

BASE_URL = "http://127.0.0.1:8000"


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

def budget_tab(user_id):
    st.subheader("💰 Budget Tracker")

    # --- 1️⃣ Current Month Overview ---
    today = date.today()
    current_month = today.strftime("%Y-%m")

    try:
        response = requests.post(
            f"{BASE_URL}/budget-status/",
            params={"user_id": user_id, "month": current_month, "category": "all", "amount": 0}
        )
        if response.status_code == 200:
            overview = response.json()
            st.markdown(f"### Budget Summary: {current_month}")
            st.write(f"**Total Budget:** ${overview['amount']}")
            st.write(f"**Total Spent:** ${overview['spent']}")
            st.write(f"**Remaining:** ${overview['remaining']}")
            st.progress(min(overview['progress'] / 100, 1.0))

            # Warning if over 80%
            if overview['progress'] >= 80:
                st.warning("⚠️ You're nearing your total budget limit!")
        else:
            st.info("No budget set for this month yet.")
    except Exception as e:
        st.error(f"Error fetching budget overview: {e}")

    st.markdown("---")

    # --- 2️⃣ Filter by Category and Month ---
    st.subheader("🔍 Filter Budget by Category / Month")

    categories = get_categories() 
    category_names = [cat['name'] for cat in categories]
    filter_category = st.selectbox("Category", category_names)
    category_id = next((cat['id'] for cat in categories if cat['name'] == filter_category), None)
    
    filter_month = st.text_input("Month (YYYY-MM)", value=current_month)

    if st.button("Show Budget Status", key="filter_btn"):
        try:
            payload = {
                "user_id": user_id,
                "category_id": category_id,
                "month": filter_month,
            }
            resp = requests.get(f"{BASE_URL}/budget/budget-status/", params=payload)
            if resp.status_code == 200:
                data = resp.json()
                st.write(f"### Budget Details for {filter_category} - {filter_month}")
                st.write(f"**Budget:** ${data['amount']}")
                st.write(f"**Spent:** ${data['spent']}")
                st.write(f"**Remaining:** ${data['remaining']}")
                st.progress(min(data['progress'] / 100, 1.0))

                if data['progress'] >= 80:
                    st.warning("⚠️ Approaching budget limit for this category!")
            else:
                st.info("No budget found for this selection.")
        except Exception as e:
            st.error(f"Error fetching filtered budget: {e}")

    st.markdown("---")

    # --- 3️⃣ Add / Update Budget ---
    st.subheader("➕ Add / Update Budget")
    with st.form("budget_form"):
        new_category = st.selectbox("Category", category_names)
        new_month = st.text_input("Month (YYYY-MM)", value=current_month)
        new_amount = st.number_input("Budget Amount", min_value=0.0)
        submit_budget = st.form_submit_button("Save / Update Budget")

        if submit_budget:
            payload = {
                "user_id": user_id,
                "category_id": category_id,
                "month": new_month,
                "monthly_limit": new_amount
            }
            try:
                resp = requests.post(f"{BASE_URL}/budget/create-or-update/", json=payload)
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    st.success(f"✅ Budget for {new_category} in {new_month} saved successfully!")
                   # st.write("Budget Status:", data.get("budget", data))
                else:
                    st.error(resp.json().get("detail", "Failed to save budget."))
            except Exception as e:
                st.error(f"Server error: {e}")
