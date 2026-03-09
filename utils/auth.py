import streamlit as st
import bcrypt
import secrets
from utils.db import fetchone, execute, execute_returning


# ── Password helpers ───────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── Session ────────────────────────────────────────────────────────────────────

def logout():
    st.session_state.clear()
    st.switch_page("app.py")


def check_login():
    from utils.oauth import get_google_auth_url, is_admin_email

    st.markdown("""
        <div style="background:#111; border:1px solid #2a2a2a; border-top:3px solid #E8000E;
                    border-radius:3px; padding:2rem; margin-bottom:1rem;">
            <div style="font-family:'Share Tech Mono',monospace; font-size:0.7rem;
                        letter-spacing:2px; color:#555; text-transform:uppercase;
                        margin-bottom:1.5rem;">// Authentication Required</div>
    """, unsafe_allow_html=True)

    email = st.text_input("EMAIL ADDRESS")

    # Detect if this is an admin email and show appropriate login
    admin_mode = email and is_admin_email(email)

    if admin_mode:
        # ── Admin: Google OAuth ────────────────────────────────────────────────
        st.markdown("""
            <div style="font-family:'Share Tech Mono',monospace; font-size:0.72rem;
                        color:#E8000E; letter-spacing:1px; margin:0.5rem 0 1rem 0;">
                ✓ Admin account detected — sign in with Google
            </div>
        """, unsafe_allow_html=True)

        if st.button("🔵  Sign in with Google", use_container_width=True, type="primary"):
            # Generate state token for CSRF protection
            state = secrets.token_urlsafe(16)
            st.session_state["oauth_state"] = state
            auth_url = get_google_auth_url()
            st.markdown(f'<meta http-equiv="refresh" content="0; url={auth_url}">', unsafe_allow_html=True)
            st.markdown(f'<a href="{auth_url}" style="color:#E8000E;">Click here if not redirected...</a>', unsafe_allow_html=True)

    else:
        # ── Customer: email/password ───────────────────────────────────────────
        password = st.text_input("PASSWORD", type="password")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("ACCESS PORTAL", use_container_width=True, type="primary"):
            if not email or not password:
                st.error("Please enter your email and password.")
                st.markdown("</div>", unsafe_allow_html=True)
                return

            user = fetchone(
                "SELECT * FROM users WHERE email = %s", (email.lower().strip(),)
            )

            if user and user["password"] != "GOOGLE_AUTH_NO_PASSWORD" and verify_password(password, user["password"]):
                st.session_state["user"] = dict(user)
                st.rerun()
            else:
                st.error("Invalid credentials. Access denied.")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("""
        <div style="font-family:'Share Tech Mono',monospace; font-size:0.65rem;
                    color:#333; text-align:center; letter-spacing:1px; margin-top:1rem;">
            NEED ACCESS? CONTACT 5G SECURITY AT SUPPORT@FIVEGSECURITY.NET
        </div>
    """, unsafe_allow_html=True)


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
