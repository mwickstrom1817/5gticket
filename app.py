import streamlit as st
from utils.auth import check_login, logout, update_password
from utils.db import init_db, fetchone as db_fetchone
from utils.theme import inject_global_css, render_logo
from utils.password_reset import validate_reset_token, consume_reset_token, create_reset_token, send_reset_email

st.set_page_config(
    page_title="5G Security | Customer Portal",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_global_css()
init_db()
st.write("DEBUG: past init")

# ── Handle Google OAuth callback ───────────────────────────────────────────────
from utils.oauth import handle_oauth_callback
if "code" in st.query_params:
    if handle_oauth_callback():
        st.switch_page("pages/admin_dashboard.py")

# ── Handle password reset token ────────────────────────────────────────────────
if "reset_token" in st.query_params:
    token = st.query_params["reset_token"]
    user_row = validate_reset_token(token)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        render_logo()
        st.markdown("<br>", unsafe_allow_html=True)
        if not user_row:
            st.error("This reset link is invalid or has expired. Please request a new one.")
        else:
            st.markdown("### 🔒 Set New Password")
            st.markdown(f"Setting password for **{user_row['email']}**")
            with st.form("reset_pw_form"):
                new_pw     = st.text_input("New Password", type="password")
                confirm_pw = st.text_input("Confirm Password", type="password")
                if st.form_submit_button("Set Password", type="primary"):
                    if not new_pw or not confirm_pw:
                        st.error("Please fill in both fields.")
                    elif len(new_pw) < 8:
                        st.error("Password must be at least 8 characters.")
                    elif new_pw != confirm_pw:
                        st.error("Passwords don't match.")
                    else:
                        update_password(user_row["user_id"], new_pw)
                        consume_reset_token(token)
                        st.success("Password updated! You can now log in.")
                        st.query_params.clear()
                        st.rerun()
    st.stop()

# ── Handle forgot password form ────────────────────────────────────────────────
if "forgot_password" in st.query_params:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        render_logo()
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Reset Your Password")
        st.markdown("Enter your email and we'll send you a reset link.")
        with st.form("forgot_form"):
            reset_email = st.text_input("Email Address")
            if st.form_submit_button("Send Reset Link", type="primary"):
                if reset_email:
                    user = db_fetchone(
                        "SELECT * FROM users WHERE email = %s AND role = 'customer'",
                        (reset_email.lower().strip(),)
                    )
                    if user:
                        token = create_reset_token(user["id"])
                        send_reset_email(user["email"], user["name"], token)
                    # Always show success to avoid email enumeration
                    st.success("If that email is registered, a reset link is on its way!")
        st.markdown("""
            <div style="text-align:center; margin-top:1rem;">
                <a href="/" style="font-family:'DM Mono',monospace; font-size:0.72rem;
                   color:#555; letter-spacing:1px; text-decoration:none;">
                   ← Back to login
                </a>
            </div>
        """, unsafe_allow_html=True)
    st.stop()

if "user" not in st.session_state:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        render_logo()
        st.markdown("""
            <div style="font-family:'Share Tech Mono',monospace; font-size:0.72rem;
                        letter-spacing:2px; color:#555; text-transform:uppercase;
                        margin-bottom:2rem;">
                Secure Client Access Portal
            </div>
        """, unsafe_allow_html=True)
        check_login()
else:
    user = st.session_state["user"]

    # Force password change — render inline before anything else
    if user.get("must_change_password") and user.get("role") == "customer":
        from utils.db import execute
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            render_logo()
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 🔒 Set Your Password")
            st.markdown("For your security, please set a new password before continuing.")
            with st.form("force_pw_change"):
                new_pw     = st.text_input("New Password", type="password")
                confirm_pw = st.text_input("Confirm Password", type="password")
                if st.form_submit_button("Set Password & Continue", type="primary"):
                    if not new_pw or not confirm_pw:
                        st.error("Please fill in both fields.")
                    elif len(new_pw) < 8:
                        st.error("Password must be at least 8 characters.")
                    elif new_pw != confirm_pw:
                        st.error("Passwords don't match.")
                    else:
                        update_password(user["id"], new_pw)
                        execute("UPDATE users SET must_change_password = FALSE WHERE id = %s", (user["id"],))
                        st.session_state["user"]["must_change_password"] = False
                        st.success("Password updated! Loading your dashboard...")
                        st.rerun()
        st.stop()

    with st.sidebar:
        render_logo()
        st.markdown(f"""
            <div style="background:#1a1a1a; border:1px solid #2a2a2a; border-left:3px solid #E8000E;
                        border-radius:2px; padding:10px 12px; margin-bottom:1rem;">
                <div style="font-family:'Share Tech Mono',monospace; font-size:0.65rem;
                            letter-spacing:2px; color:#555; text-transform:uppercase;">Logged in as</div>
                <div style="font-family:'Rajdhani',sans-serif; font-weight:600; font-size:1rem;
                            color:#f0f0f0; margin-top:2px;">{user['name']}</div>
                <div style="font-family:'Share Tech Mono',monospace; font-size:0.65rem;
                            color:#E8000E; letter-spacing:1px;">
                    {'ADMINISTRATOR' if user['role'] == 'admin' else 'CLIENT'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="font-family:\'Share Tech Mono\',monospace; font-size:0.65rem; letter-spacing:2px; color:#444; text-transform:uppercase; padding:4px 0; margin-bottom:8px;">Navigation</div>', unsafe_allow_html=True)

        if user["role"] == "admin":
            nav_items = [
                ("pages/admin_dashboard.py",  "📊", "Dashboard"),
                ("pages/admin_customers.py",  "👥", "Customers"),
                ("pages/admin_equipment.py",  "🎥", "Equipment"),
                ("pages/admin_tickets.py",    "🎫", "Tickets"),
            ]
        else:
            nav_items = [
                ("pages/customer_dashboard.py", "🏠", "Dashboard"),
                ("pages/customer_equipment.py", "🎥", "My Equipment"),
                ("pages/customer_tickets.py",   "🎫", "My Tickets"),
                ("pages/submit_ticket.py",      "➕", "Submit Ticket"),
            ]

        for page, emoji, label in nav_items:
            if st.button(f"{emoji}  {label}", key=f"nav_{label}", use_container_width=True):
                st.switch_page(page)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div style="font-family:\'Share Tech Mono\',monospace; font-size:0.65rem; letter-spacing:2px; color:#444; text-transform:uppercase; padding:4px 0; margin-bottom:8px; border-top:1px solid #1a1a1a; padding-top:12px;">Account</div>', unsafe_allow_html=True)
        if st.button("🚪  Log Out", key="nav_logout", use_container_width=True):
            logout()

        st.markdown("""
            <div style="position:fixed; bottom:1rem; font-family:'Share Tech Mono',monospace;
                        font-size:0.6rem; color:#333; letter-spacing:1px;">
                5G SECURITY © 2026 | PORTAL v1.0
            </div>
        """, unsafe_allow_html=True)

    if user["role"] == "admin":
        st.switch_page("pages/admin_dashboard.py")
    else:
        st.switch_page("pages/customer_dashboard.py")
