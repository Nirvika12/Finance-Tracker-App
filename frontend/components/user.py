import streamlit as st
import requests
import os

BASE_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")

def get_auth_headers():
    """Returns headers with JWT token for authenticated requests."""
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def profile_page():
    """Displays user profile info and allows updating name/email/password"""

    # --- Fetch current user info ---
    try:
        resp = requests.get(f"{BASE_URL}/users/me", headers=get_auth_headers())
        if resp.status_code == 200:
            user_data = resp.json()
        else:
            st.error("Failed to fetch user data")
            return
    except Exception as e:
        st.error(f"Server error: {e}")
        return

    st.subheader("👤 User Profile")
    st.write(f"**Name:** {user_data.get('name', 'N/A')}")
    st.write(f"**Email:** {user_data.get('email', 'N/A')}")
    st.write(f"**User ID:** {user_data.get('id', 'N/A')}")
    st.write(f"**Registered on:** {user_data.get('created_at', 'N/A')}")

    st.markdown("---")
    st.subheader("✏️ Update Profile")

    # --- Update name/email form ---
    with st.form("update_profile_form"):
        new_name = st.text_input("Name", value=user_data.get('name', ''))
        new_email = st.text_input("Email", value=user_data.get('email', ''))
        submitted = st.form_submit_button("Update Profile")

        if submitted:
            payload = {}
            if new_name != user_data.get('name'):
                payload['name'] = new_name
            if new_email != user_data.get('email'):
                payload['email'] = new_email

            if payload:
                try:
                    resp = requests.put(f"{BASE_URL}/users/me", json=payload, headers=get_auth_headers())
                    if resp.status_code == 200:
                        st.success("✅ Profile updated successfully!")
                        # Optionally update session state
                        st.session_state.user_name = new_name
                    else:
                        st.error(resp.json().get("detail", "Failed to update profile"))
                except Exception as e:
                    st.error(f"Server error: {e}")
            else:
                st.info("Nothing changed to update.")

    st.markdown("---")
    st.subheader("🔒 Change Password")

    # --- Change password form ---
    with st.form("change_password_form"):
        old_password = st.text_input("Old Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        submitted_pass = st.form_submit_button("Update Password")

        if submitted_pass:
            if new_password != confirm_password:
                st.warning("Passwords do not match!")
            else:
                try:
                    payload = {"password_hash": new_password}
                    resp = requests.put(f"{BASE_URL}/users/me/password", json=payload, headers=get_auth_headers())
                    if resp.status_code == 200:
                        st.success("✅ Password updated successfully!")
                    else:
                        st.error(resp.json().get("detail", "Failed to update password"))
                except Exception as e:
                    st.error(f"Server error: {e}")
