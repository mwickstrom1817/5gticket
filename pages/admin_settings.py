import streamlit as st
from utils.auth import require_role, logout as _logout
from utils.db import fetchall, execute
from utils.theme import inject_global_css, render_sidebar, page_header

inject_global_css()
require_role("admin")

if "user" in st.session_state:
    render_sidebar(st.session_state["user"], _logout)

page_header("Settings", "5G Security // Admin Management")

st.markdown("""
    <div style="font-family:'DM Sans',sans-serif; font-size:0.9rem; color:#999; margin-bottom:1.5rem;">
        Manage who can access the admin portal via Google OAuth.
        Only emails listed here will be granted admin access.
    </div>
""", unsafe_allow_html=True)

# ── Current admin list ─────────────────────────────────────────────────────────
st.markdown("""
    <div style="font-family:'Barlow',sans-serif; font-weight:700; font-size:1.1rem;
                letter-spacing:1px; text-transform:uppercase; color:#f0f0f0;
                border-bottom:1px solid #2a2a2a; padding-bottom:8px; margin-bottom:1rem;">
        Authorized Admins
    </div>
""", unsafe_allow_html=True)

admins = fetchall("SELECT * FROM admin_whitelist ORDER BY created_at")
current_user_email = st.session_state["user"]["email"]

if not admins:
    st.info("No admins configured.")
else:
    for admin in admins:
        is_you = admin["email"] == current_user_email
        col1, col2, col3 = st.columns([3, 2, 1])

        with col1:
            you_badge = ' <span style="font-family:\'DM Mono\',monospace; font-size:0.7rem; color:#E8000E; margin-left:8px;">YOU</span>' if is_you else ""
            st.markdown(f"""
                <div style="font-family:'DM Sans',sans-serif; font-size:1rem;
                            color:#f0f0f0; padding:8px 0;">
                    {"🔒" if is_you else "👤"} {admin["email"]}{you_badge}
                </div>
            """, unsafe_allow_html=True)

        with col2:
            added = admin["created_at"].strftime("%b %d, %Y") if admin.get("created_at") else "—"
            st.markdown(f"""
                <div style="font-family:'DM Mono',monospace; font-size:0.75rem;
                            color:#555; padding:8px 0;">Added {added}</div>
            """, unsafe_allow_html=True)

        with col3:
            if not is_you:
                if st.button("Remove", key=f"rm_{admin['id']}"):
                    execute("DELETE FROM admin_whitelist WHERE id = %s", (admin["id"],))
                    execute("DELETE FROM users WHERE email = %s AND role = 'admin'", (admin["email"],))
                    st.success(f"Removed {admin['email']}")
                    st.rerun()

st.markdown("---")

# ── Add new admin ──────────────────────────────────────────────────────────────
st.markdown("""
    <div style="font-family:'Barlow',sans-serif; font-weight:700; font-size:1.1rem;
                letter-spacing:1px; text-transform:uppercase; color:#f0f0f0;
                border-bottom:1px solid #2a2a2a; padding-bottom:8px; margin-bottom:1rem;">
        Add New Admin
    </div>
""", unsafe_allow_html=True)

st.markdown("""
    <div style="font-family:'DM Sans',sans-serif; font-size:0.85rem; color:#666; margin-bottom:1rem;">
        The person must have a Google account with this email.
        They will be able to sign in via Google OAuth on the login page.
    </div>
""", unsafe_allow_html=True)

with st.form("add_admin"):
    col1, col2 = st.columns([3, 1])
    with col1:
        new_email = st.text_input("Email Address", placeholder="colleague@fivegsecurity.net")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("➕ Add Admin", type="primary", use_container_width=True)

    if submitted:
        if not new_email or "@" not in new_email:
            st.error("Please enter a valid email address.")
        else:
            email_clean = new_email.lower().strip()
            existing = fetchall("SELECT id FROM admin_whitelist WHERE email = %s", (email_clean,))
            if existing:
                st.warning(f"{email_clean} is already an authorized admin.")
            else:
                execute(
                    "INSERT INTO admin_whitelist (email, added_by) VALUES (%s, %s)",
                    (email_clean, current_user_email)
                )
                st.success(f"✅ {email_clean} added. They can now sign in with Google.")
                st.rerun()

st.markdown("---")
st.markdown("""
    <div style="font-family:'DM Mono',monospace; font-size:0.72rem; color:#333;">
        // Admins authenticate via Google OAuth — no password required.<br>
        // Removing an admin revokes their portal access immediately.
    </div>
""", unsafe_allow_html=True)