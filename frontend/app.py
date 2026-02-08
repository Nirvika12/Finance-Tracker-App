# main.py
import streamlit as st
import requests
from datetime import datetime
from components.transactions import transactions_page 
from components.budgets import budget_tab
from components.user import profile_page
from dotenv import load_dotenv
import os 
from streamlit_cookies_manager import EncryptedCookieManager

# -------------------------------------------------
# LOAD ENV
# -------------------------------------------------
load_dotenv()
BASE_URL = os.getenv("API_URL")
COOKIE_PASSWORD = os.getenv("COOKIE_PASSWORD")

# -------------------------------------------------
# COOKIE MANAGER
# -------------------------------------------------
cookies = EncryptedCookieManager(prefix="ftok_", password=COOKIE_PASSWORD)
if not cookies.ready():
    st.stop()

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Finance Tracker App",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "token" not in st.session_state:
    st.session_state.token = None

if not st.session_state.token:
    token_from_cookie = cookies.get("token")
    if token_from_cookie:
        st.session_state.token = token_from_cookie

if "current_tab" not in st.session_state:
    st.session_state.current_tab = "Dashboard"

# -------------------------------------------------
# AUTH HELPERS
# -------------------------------------------------
def is_authenticated() -> bool:
    return st.session_state.token is not None

def force_logout():
    """Clears token and reruns app"""
    st.session_state.token = None
    cookies["token"] = ""
    cookies.save()
    st.rerun()

def get_current_user():
    """Fetch current user info from API"""
    if not st.session_state.token:
        return None
    try:
        res = requests.get(
            f"{BASE_URL}/users/me",
            headers={"Authorization": f"Bearer {st.session_state.token}"},
            timeout=5,
        )
        if res.status_code == 200:
            return res.json().get("data")  # <- important, API wraps data
        elif res.status_code == 401:
            force_logout()
    except Exception as e:
        st.error(f"⚠️ Error fetching user: {e}")
    return None

# -------------------------------------------------
# AUTH PAGE (LOGIN / SIGNUP)
# -------------------------------------------------
def auth_page():
    st.markdown("""
    <h1 style="text-align:center; color:#E0BCBC; font-size:40px;">
    Finance Tracker App
    </h1>
    """, unsafe_allow_html=True)

    st.markdown(
        "<h3 style='text-align:center; color:#E0BCBC;'>Track your transactions easily</h3>",
        unsafe_allow_html=True,
    )

    tabs = st.tabs(["Login", "Sign Up"])

    # ---------------- LOGIN ----------------
    with tabs[0]:
        st.subheader("🔑 Login")
        with st.form("login_form"):
            email = st.text_input("Email").strip()
            password = st.text_input("Password", type="password").strip()
            submit = st.form_submit_button("Login")

            if submit:
                if not email or not password:
                    st.warning("Please enter both email and password")
                    return

                try:
                    login_response = requests.post(
                        f"{BASE_URL}/users/login",
                        json={"email": email, "password": password},
                        timeout=5,
                    )

                    if login_response.status_code == 200:
                        st.session_state.token = login_response.json()["data"]["access_token"]
                        cookies["token"] = st.session_state.token
                        cookies.save()
                        st.success("Login successful 🎉")
                        st.rerun()
                    else:
                        st.error(login_response.json().get("detail", "Invalid email or password"))

                except Exception as e:
                    st.error(f"⚠️ Server error: {e}")

    # ---------------- SIGNUP ----------------
    with tabs[1]:
        st.subheader("📝 Sign Up")
        with st.form("signup_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Sign Up")

            if submit:
                if not all([name, email, password, confirm_password]):
                    st.warning("Please fill all fields")
                elif password != confirm_password:
                    st.warning("Passwords do not match")
                else:
                    try:
                        res = requests.post(
                            f"{BASE_URL}/users/signup",
                            json={
                                "name": name,
                                "email": email,
                                "password": password,
                            },
                            timeout=5,
                        )

                        if res.status_code == 201:
                            st.success("✅ Account created! Please login.")
                        else:
                            st.error(res.json().get("detail", "Signup failed"))

                    except Exception as e:
                        st.error(f"⚠️ Server error: {e}")

# -------------------------------------------------
# DASHBOARD APP
# -------------------------------------------------
def dashboard_app():
    user = get_current_user()

    if st.session_state.token and not user:
        force_logout()

    if not st.session_state.token:
        auth_page()
        return

    st.markdown(
        "<h1 style='text-align:center; color:#4CAF50;'>💰 Finance Tracker Dashboard</h1>",
        unsafe_allow_html=True,
    )
    st.write(f"Welcome, **{user['name']}**")

    # ---------------- SIDEBAR TABS ----------------
    tab_options = ["Transactions", "Budget", "Profile"]
    current_index = tab_options.index(st.session_state.current_tab) if st.session_state.current_tab in tab_options else 0

    tab = st.sidebar.radio("Go to:", tab_options, index=current_index)
    st.session_state.current_tab = tab


    if tab == "Transactions":
        transactions_page()
    elif tab == "Budget":
        budget_tab()
    elif tab == "Profile":
        profile_page()

    # ---------------- LOGOUT ----------------
    if st.sidebar.button("🚪 Logout"):
        force_logout()

# -------------------------------------------------
# ROUTING
# -------------------------------------------------
if is_authenticated():
    dashboard_app()
else:
    auth_page()
