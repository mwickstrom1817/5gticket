import streamlit as st
from utils.db import execute
from utils.theme import inject_global_css, render_sidebar, page_header
from utils.auth import logout as _logout, update_password
import bcrypt

inject_global_css()

if "user" not in st.session_state:
    st.warning("Please log in.")
    st.stop()

user = st.session_state["user"]

# Only show this page if they must change password
if not user.get("must_change_password"):
    st.switch_page("pages/customer_dashboard.py")

render_sidebar(user, _logout)

page_header("Set Your Password", "Welcome to 5G Security Portal")

st.markdown("""
    <div style="font-family:'DM Sans',sans-serif; font-size:0.95rem; color:#999;
                margin-bottom:2rem; max-width:500px;">
        For your security, please set a new password before continuing.
        Your temporary password will no longer work after this step.
    </div>
""", unsafe_allow_html=True)

with st.form("change_password"):
    new_pw      = st.text_input("New Password", type="password")
    confirm_pw  = st.text_input("Confirm Password", type="password")
    submitted   = st.form_submit_button("🔒 Set Password & Continue", type="primary")

    if submitted:
        if not new_pw or not confirm_pw:
            st.error("Please fill in both fields.")
        elif len(new_pw) < 8:
            st.error("Password must be at least 8 characters.")
        elif new_pw != confirm_pw:
            st.error("Passwords don't match.")
        else:
            # Update password and clear the flag
            update_password(user["id"], new_pw)
            execute(
                "UPDATE users SET must_change_password = FALSE WHERE id = %s",
                (user["id"],)
            )
            # Update session state so they don't get redirected again
            st.session_state["user"]["must_change_password"] = False
            st.success("Password set! Redirecting to your dashboard...")
            st.switch_page("pages/customer_dashboard.py")
