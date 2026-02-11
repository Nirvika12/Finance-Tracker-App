import streamlit as st
import requests
from datetime import date
import os
from dotenv import load_dotenv

load_dotenv()

#BASE_URL = os.environ.get("API_URL")

BASE_URL = st.secrets["API_URL"]

def get_auth_headers():
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def get_categories():
    try:
        response = requests.get(f"{BASE_URL}/category/", headers=get_auth_headers())
        if response.status_code == 200:
            return response.json().get("data", [])
        else:
            st.warning("No categories found.")
            return []
    except Exception as e:
        st.error(f"Error fetching categories: {e}")
        return []

def budget_tab():
    st.subheader("💰 Budget Tracker")

    today = date.today()
    current_month = today.strftime("%Y-%m")
    categories = get_categories()

    # -----------------------------
    # Current Month Overall Progress
    # -----------------------------
    if categories:
        try:
            resp = requests.get(
                f"{BASE_URL}/budget/monthly-status/",
                params={"month": current_month},
                headers=get_auth_headers()
            )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                budgets = data.get("budgets", [])

                total_budget = sum(b["amount"] for b in budgets)
                total_spent = sum(b["spent"] for b in budgets)
                remaining = total_budget - total_spent
                progress = round((total_spent / total_budget) * 100, 2) if total_budget > 0 else 0

                st.markdown(f"### Current Month Overview ({current_month})")
                st.write(f"**Total Budget:** ${total_budget}")
                st.write(f"**Total Spent:** ${total_spent}")
                st.write(f"**Remaining:** ${remaining}")
                st.progress(min(progress / 100, 1.0))

                if total_budget == 0:
                    st.info("No budgets set for this month yet.")
                elif remaining < 0:
                    st.error("🚨 You have exceeded your total monthly budget!")
                elif progress >= 80:
                    st.warning("⚠️ You're nearing your total monthly budget limit!")

            else:
                st.info("No budget data available for this month.")
        except Exception as e:
            st.error(f"Error fetching current month budget: {e}")

    st.markdown("---")

    # -----------------------------
    # Filter by Category / Month
    # -----------------------------
    st.subheader("🔍 Filter Budget by Category / Month")

    if not categories:
        st.info("No categories available for filtering.")
        return

    category_names = ["All"] + [cat["name"] for cat in categories]
    filter_category = st.selectbox("Category", category_names)
    filter_month = st.text_input("Month (YYYY-MM)", value=current_month)

    if st.button("Show Budget Status", key="filter_btn"):
        try:
            resp = requests.get(
                f"{BASE_URL}/budget/monthly-status/",
                params={"month": filter_month},
                headers=get_auth_headers()
            )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                budgets = data.get("budgets", [])

                # Filter by category if not "All"
                if filter_category != "All":
                    cat_obj = next((c for c in categories if c["name"] == filter_category), None)
                    if cat_obj:
                        budgets = [b for b in budgets if b["category_id"] == cat_obj["id"]]
                if not budgets:
                    st.info("No budget found for this selection.")
                else:
                    st.write(f"### Budget Details - {filter_category} / {filter_month}")
                    for b in budgets:
                        cat_name = next((c["name"] for c in categories if c["id"] == b["category_id"]), "Unknown")

                        st.subheader(cat_name)
                        st.write(f"**Budget:** ${b['amount']:.2f}")
                        st.write(f"**Spent:** ${b['spent']:.2f}")
                        st.write(f"**Remaining:** ${b['remaining']:.2f}")
                        st.progress(min(b["progress"] / 100, 1.0))

                        if b["remaining"] < 0:
                            st.error(f"🚨 Budget exceeded for {cat_name}!")
                        elif b["progress"] >= 80:
                            st.warning(f"⚠️ Approaching budget limit for {cat_name}!")
                        st.markdown("---")

            else:
                st.error("Failed to fetch budget data.")
        except Exception as e:
            st.error(f"Error fetching filtered budget: {e}")

    # -----------------------------
    # Add / Update Budget
    # -----------------------------
    st.subheader("➕ Add / Update Budget")
    with st.form("budget_form"):
        new_category = st.selectbox("Category", category_names)
        new_month = st.text_input("Month (YYYY-MM)", value=current_month)
        new_amount = st.number_input("Budget Amount", min_value=0.0)
        submit_budget = st.form_submit_button("Save / Update Budget")
        new_category_id = next((cat['id'] for cat in categories if cat['name'] == new_category), None)

        if submit_budget:
            payload = {
                "category_id": new_category_id,
                "month": new_month,
                "monthly_limit": new_amount
            }
            try:
                resp = requests.post(
                    f"{BASE_URL}/budget/create-or-update/",
                    json=payload,
                    headers=get_auth_headers()
                )
                if resp.status_code in [200, 201]:
                    st.success(f"✅ Budget for {new_category} in {new_month} saved successfully!")
                else:
                    st.error(resp.json().get("detail", "Failed to save budget."))
            except Exception as e:
                st.error(f"Server error: {e}")
