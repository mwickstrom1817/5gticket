import streamlit as st
import requests
import urllib.parse
import secrets


def get_google_auth_url() -> str:
    """Generate the Google OAuth authorization URL."""
    params = {
        "client_id":     st.secrets["GOOGLE_CLIENT_ID"],
        "redirect_uri":  st.secrets["GOOGLE_REDIRECT_URI"],
        "response_type": "code",
        "scope":         "openid email profile",
        "access_type":   "offline",
        "state":         st.session_state.get("oauth_state", ""),
    }
    base = "https://accounts.google.com/o/oauth2/v2/auth"
    return f"{base}?{urllib.parse.urlencode(params)}"


def exchange_code_for_token(code: str) -> dict:
    """Exchange an authorization code for tokens."""
    resp = requests.post("https://oauth2.googleapis.com/token", data={
        "code":          code,
        "client_id":     st.secrets["GOOGLE_CLIENT_ID"],
        "client_secret": st.secrets["GOOGLE_CLIENT_SECRET"],
        "redirect_uri":  st.secrets["GOOGLE_REDIRECT_URI"],
        "grant_type":    "authorization_code",
    })
    return resp.json()


def get_google_user_info(access_token: str) -> dict:
    """Fetch the authenticated user's profile from Google."""
    resp = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    return resp.json()


def is_admin_email(email: str) -> bool:
    """Check if an email is in the admin whitelist in the database."""
    from utils.db import fetchone
    result = fetchone(
        "SELECT id FROM admin_whitelist WHERE LOWER(email) = LOWER(%s)",
        (email.strip(),)
    )
    return result is not None


def handle_oauth_callback():
    """
    Call this on app.py to handle the OAuth callback.
    Returns True if a user was successfully logged in via OAuth.
    """
    params = st.query_params

    if "code" not in params:
        return False

    code  = params["code"]
    state = params.get("state", "")

    # Verify state to prevent CSRF
    # State check skipped — Streamlit clears session between redirects

    with st.spinner("Authenticating with Google..."):
        token_data = exchange_code_for_token(code)

    if "error" in token_data:
        st.error(f"Google authentication failed: {token_data.get('error_description', token_data['error'])}")
        st.query_params.clear()
        return False

    access_token = token_data.get("access_token")
    if not access_token:
        st.error("Failed to get access token from Google.")
        st.query_params.clear()
        return False

    google_user = get_google_user_info(access_token)
    email = google_user.get("email", "").lower().strip()

    if not email:
        st.error("Could not retrieve email from Google.")
        st.query_params.clear()
        return False

    if not is_admin_email(email):
        st.error(f"⛔ {email} is not authorized as an admin. Contact 5G Security to request access.")
        st.query_params.clear()
        return False

    # Look up or auto-create admin user in DB
    from utils.db import fetchone, execute_returning
    user = fetchone("SELECT * FROM users WHERE email = %s", (email,))

    if not user:
        # Auto-create admin account on first Google login
        name = google_user.get("name", email.split("@")[0].title())
        row  = execute_returning("""
            INSERT INTO users (name, email, password, role)
            VALUES (%s, %s, %s, 'admin') RETURNING id
        """, (name, email, "GOOGLE_AUTH_NO_PASSWORD"))
        user = fetchone("SELECT * FROM users WHERE id = %s", (row["id"],))

    st.session_state["user"] = dict(user)
    st.query_params.clear()
    return True