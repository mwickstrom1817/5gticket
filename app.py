import streamlit as st
from utils.auth import check_login, logout
from utils.db import init_db
from utils.theme import inject_global_css, render_logo

st.set_page_config(
    page_title="5G Security | Customer Portal",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_global_css()
init_db()

# ── Handle Google OAuth callback ───────────────────────────────────────────────
from utils.oauth import handle_oauth_callback
if "code" in st.query_params:
    if handle_oauth_callback():
        st.switch_page("pages/admin_dashboard.py")

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

    # Force password change if flagged
    if st.session_state.get("force_change_password"):
        st.switch_page("pages/change_password.py")

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
