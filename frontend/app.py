import streamlit as st
import requests
import base64
from components.transactions import transactions_page 
from components.budgets import budget_tab



# --- Initialize session state ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "login_error" not in st.session_state:
    st.session_state.login_error = ""

BASE_URL = "http://127.0.0.1:8000"

# --- Page config ---
st.set_page_config(
    page_title="Finance Tracker App",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# --- Auth Page ---
def auth_page():
    st.markdown("""
    <h1 style="text-align:center; color:#E0BCBC; font-size:40px;">
    Finance Tracker App
    </h1>
    """, unsafe_allow_html=True)

    st.markdown("<h3 style='text-align:center; color:#E0BCBC;'>Track your transactions easily</h3>", unsafe_allow_html=True)

    # --- Tabs for Login / Signup ---
    tab = st.tabs(["Login", "Sign Up"])
    
    # --- LOGIN TAB ---
    with tab[0]:
        st.subheader("🔑 Login")
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email").strip()
            password = st.text_input("Password", type="password", key="login_password").strip()
            submitted = st.form_submit_button("Login")
            if submitted:
                if email and password:
                    try:
                        response = requests.post(f"{BASE_URL}/users/login", json={"email": email, "password": password})
                        if response.status_code == 200:
                            user_data = response.json()
                            st.session_state.logged_in = True
                            st.session_state.user_id = user_data.get("user_id")
                            st.success("Login successful! 🎉")
                            st.rerun()

                        else:
                            st.error("Invalid email or password")
                    except Exception as e:
                        st.error(f"⚠️ Server error: {e}")
                else:
                    st.warning("Please enter both email and password")

    # --- SIGNUP TAB ---
    with tab[1]:
        st.subheader("📝 Sign Up")
        with st.form("signup_form"):
            name = st.text_input("Full Name", key="signup_name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
            submitted = st.form_submit_button("Sign Up")
            if submitted:
                if not all([name, email, password, confirm_password]):
                    st.warning("Please fill all fields")
                elif password != confirm_password:
                    st.warning("Passwords do not match")
                else:
                    try:
                        response = requests.post(
                            f"{BASE_URL}/users/signup",
                            json={"name": name, "email": email, "password": password},
                        )
                        if response.status_code == 201:
                            st.success("✅ Account created! Please login.")
                        else:
                            st.error(response.json().get("detail", "Signup failed."))
                    except Exception as e:
                        st.error(f"⚠️ Server error: {e}")

# --- Main Dashboard App ---
def dashboard_app():
    st.markdown("<h1 style='text-align:center; color:#4CAF50;'>💰 Finance Tracker Dashboard</h1>", unsafe_allow_html=True)
    st.write(f"Welcome, User ID: {st.session_state.user_id}")

    tab = st.sidebar.radio("Go to:", ["Profile", "Dashboard", "Transactions", "Budget"])

    if tab == "Dashboard":
        st.subheader("📊 Dashboard")
        st.write("Overview of your finances will appear here.")
    
    elif tab == "Transactions":
        transactions_page(st.session_state.user_id)
    
    elif tab == "Profile":
        st.subheader("👤 User Profile")
        st.write("Profile details go here...")

    elif tab == "Budget":
        st.subheader("💰 Monthly Budget Overview")
        #budget_limit = 
       # current_spending = 

        #st.progress(min(current_spending / budget_limit, 1.0))
        #st.write(f"Spent: ${current_spending} / ${budget_limit}")   
        budget_tab(st.session_state.user_id)

    # Logout in sidebar
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.rerun()


# --- Routing ---
if st.session_state.logged_in:
    dashboard_app()
else:
    auth_page()