import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.environ.get("API_URL")


def get_auth_headers():
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def force_logout():
    st.session_state.token = None
    st.experimental_rerun()


def profile_page():

    # --- Fetch current user info ---
    try:
        resp = requests.get(
            f"{BASE_URL}/users/me",
            headers=get_auth_headers(),
            timeout=5,
        )

        if resp.status_code == 401:
            force_logout()

        if resp.status_code != 200:
            st.error("Failed to fetch user data")
            return

        user_data = resp.json().get("data", {})

    except Exception as e:
        st.error(f"Server error: {e}")
        return

    # ---------------- DISPLAY ----------------
    st.subheader("👤 User Profile")
    st.write(f"**Name:** {user_data.get('name', 'N/A')}")
    st.write(f"**Email:** {user_data.get('email', 'N/A')}")
    st.write(f"**User ID:** {user_data.get('id', 'N/A')}")
    st.write(f"**Registered on:** {user_data.get('created_at', 'N/A')}")

    st.markdown("---")
    st.subheader("✏️ Update Profile")

    # ---------------- UPDATE PROFILE ----------------
    with st.form("update_profile_form"):
        new_name = st.text_input("Name", value=user_data.get('name', ''))
        new_email = st.text_input("Email", value=user_data.get('email', ''))
        submitted = st.form_submit_button("Update Profile")

        if submitted:
            payload = {}
            if new_name != user_data.get("name"):
                payload["name"] = new_name
            if new_email != user_data.get("email"):
                payload["email"] = new_email

            if not payload:
                st.info("Nothing changed to update.")
            else:
                try:
                    resp = requests.put(
                        f"{BASE_URL}/users/me",
                        json=payload,
                        headers=get_auth_headers(),
                        timeout=5,
                    )

                    if resp.status_code == 401:
                        force_logout()

                    if resp.status_code == 200:
                        st.success("✅ Profile updated successfully!")
                        st.experimental_rerun()
                    else:
                        st.error(resp.json().get("detail", "Failed to update profile"))

                except Exception as e:
                    st.error(f"Server error: {e}")

    st.markdown("---")
    st.subheader("🔒 Change Password")

    # ---------------- CHANGE PASSWORD ----------------
    with st.form("change_password_form"):
        old_password = st.text_input("Old Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        submitted_pass = st.form_submit_button("Update Password")

        if submitted_pass:
            if not old_password or not new_password or not confirm_password:
                st.warning("All fields are required!")
            elif new_password != confirm_password:
                st.warning("Passwords do not match!")
            else:
                try:
                    payload = {
                        "old_password": old_password,
                        "new_password": new_password,
                    }

                    resp = requests.put(
                        f"{BASE_URL}/users/me/password",
                        json=payload,
                        headers=get_auth_headers(),
                        timeout=5,
                    )

                    if resp.status_code == 401:
                        force_logout()

                    if resp.status_code == 200:
                        st.success("✅ Password updated successfully!")
                    else:
                        st.error(resp.json().get("detail", "Failed to update password"))

                except Exception as e:
                    st.error(f"Server error: {e}")
