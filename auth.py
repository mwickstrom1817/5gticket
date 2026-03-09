import streamlit as st
import bcrypt
from utils.db import fetchone, execute, execute_returning


# ── Password helpers ───────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── Session ────────────────────────────────────────────────────────────────────

def logout():
    st.session_state.clear()
    st.rerun()


def check_login():
    st.markdown("### Sign in to your account")
    email    = st.text_input("Email address")
    password = st.text_input("Password", type="password")

    if st.button("Sign In", use_container_width=True, type="primary"):
        if not email or not password:
            st.error("Please enter your email and password.")
            return

        user = fetchone(
            "SELECT * FROM users WHERE email = %s", (email.lower().strip(),)
        )

        if user and verify_password(password, user["password"]):
            st.session_state["user"] = dict(user)
            st.rerun()
        else:
            st.error("Invalid email or password.")

    st.markdown("---")
    st.caption("Having trouble? Contact 5G Security at support@5gsecurity.com")


# ── Admin helpers ──────────────────────────────────────────────────────────────

def create_user(name: str, email: str, password: str, role: str, customer_id=None):
    hashed = hash_password(password)
    return execute_returning(
        """
        INSERT INTO users (name, email, password, role, customer_id)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (name, email.lower().strip(), hashed, role, customer_id)
    )


def update_password(user_id: int, new_password: str):
    hashed = hash_password(new_password)
    execute("UPDATE users SET password = %s WHERE id = %s", (hashed, user_id))


def require_role(role: str):
    """Call at top of any page to enforce role-based access."""
    user = st.session_state.get("user")
    if not user:
        st.warning("Please log in.")
        st.stop()
    if user["role"] != role:
        st.error("⛔ You don't have permission to view this page.")
        st.stop()
