import streamlit as st
from utils.auth import check_login, logout
from utils.db import init_db

st.set_page_config(
    page_title="5G Security | Customer Portal",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize DB on startup
init_db()

# ── Branding ──────────────────────────────────────────────────────────────────
def render_logo():
    st.markdown("""
        <div style='display:flex; align-items:center; gap:12px; padding:8px 0 16px 0;'>
            <span style='font-size:2rem;'>🔒</span>
            <div>
                <div style='font-size:1.4rem; font-weight:700; color:#1a1a2e; line-height:1;'>5G Security</div>
                <div style='font-size:0.75rem; color:#666; letter-spacing:1px;'>CUSTOMER PORTAL</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ── Auth gate ─────────────────────────────────────────────────────────────────
if "user" not in st.session_state:
    render_logo()
    st.markdown("---")
    check_login()
else:
    user = st.session_state["user"]

    with st.sidebar:
        render_logo()
        st.markdown("---")
        st.markdown(f"👤 **{user['name']}**")
        st.markdown(f"`{'Admin' if user['role'] == 'admin' else 'Customer'}`")
        st.markdown("---")

        if user["role"] == "admin":
            st.page_link("pages/admin_dashboard.py",  label="📊 Admin Dashboard",   icon=None)
            st.page_link("pages/admin_customers.py",  label="👥 Manage Customers",  icon=None)
            st.page_link("pages/admin_equipment.py",  label="🎥 Manage Equipment",  icon=None)
            st.page_link("pages/admin_tickets.py",    label="🎫 Manage Tickets",    icon=None)
        else:
            st.page_link("pages/customer_dashboard.py", label="🏠 My Dashboard",   icon=None)
            st.page_link("pages/customer_equipment.py", label="🎥 My Equipment",   icon=None)
            st.page_link("pages/customer_tickets.py",   label="🎫 My Tickets",     icon=None)
            st.page_link("pages/submit_ticket.py",      label="➕ Submit Ticket",  icon=None)

        st.markdown("---")
        if st.button("🚪 Log Out", use_container_width=True):
            logout()

    # Default landing page
    if user["role"] == "admin":
        st.switch_page("pages/admin_dashboard.py")
    else:
        st.switch_page("pages/customer_dashboard.py")
