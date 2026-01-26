import streamlit as st
import requests
from datetime import datetime, date
from components.transactions import transactions_page 
from components.budgets import budget_tab
from components.dashboard import dashboard_page
from components.user import profile_page
from dotenv import load_dotenv
import os 
from jose import jwt, JWTError


load_dotenv()

SECRET_KEY_TOKEN = os.getenv("SECRET_KEY_TOKEN")

SECRET_KEY = SECRET_KEY_TOKEN
ALGORITHM = "HS256"
month = datetime.today().strftime("%Y-%m")
BASE_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")


def get_user_from_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except JWTError:
        return None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.token = None

# Check token validity on reload
if st.session_state.token and not st.session_state.logged_in:
    user_id = get_user_from_token(st.session_state.token)
    if user_id:
        st.session_state.logged_in = True
        st.session_state.user_id = user_id
        # Optional: fetch user name from API
        try:
            response = requests.get(f"{BASE_URL}/users/me", headers={"Authorization": f"Bearer {st.session_state.token}"})
            if response.status_code == 200:
                st.session_state.user_name = response.json()["name"]
        except:
            pass
    else:
        st.session_state.clear()


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
                            st.session_state.user_name = user_data["name"]
                            st.session_state.token = user_data["access_token"]
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
    st.write(f"Welcome, {st.session_state.user_name}")

    tab = st.sidebar.radio("Go to:", ["Profile", "Dashboard", "Transactions", "Budget"])

    if tab == "Dashboard":
        dashboard_page()
      
    elif tab == "Transactions":
        transactions_page()
    
    elif tab == "Profile":
        profile_page()

    elif tab == "Budget":
        st.subheader("💰 Monthly Budget Overview") 
        budget_tab()

    # Logout in sidebar
    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.switch_page("pages/login.py")
        st.rerun()


# --- Routing ---
if st.session_state.logged_in:
    dashboard_app()
else:
    auth_page()