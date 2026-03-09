import streamlit as st
from utils.db import fetchall, fetchone
from utils.auth import require_role

# Any logged-in user can see this, but must be authenticated
if "user" not in st.session_state:
    st.warning("Please log in.")
    st.stop()

user = st.session_state["user"]
if user["role"] == "admin":
    st.switch_page("pages/admin_dashboard.py")

customer_id = user["customer_id"]
customer    = fetchone("SELECT * FROM customers WHERE id = %s", (customer_id,))

if not customer:
    st.error("Customer account not found. Please contact 5G Security.")
    st.stop()

st.title(f"Welcome, {user['name']} 👋")
st.markdown(f"**{customer['company']}** — {customer['city'] or ''}{', ' + customer['state'] if customer.get('state') else ''}")
st.markdown("---")

# ── System Health Cards ────────────────────────────────────────────────────────
st.subheader("🔒 System Health")

systems = fetchall(
    "SELECT * FROM systems WHERE customer_id = %s ORDER BY system_type",
    (customer_id,)
)

system_icons = {
    "cameras":        "📷",
    "access_control": "🚪",
    "alarms":         "🚨",
    "network":        "🌐",
}

status_config = {
    "green":  {"label": "Online",      "color": "#198754", "bg": "#d1e7dd", "icon": "✅"},
    "yellow": {"label": "Attention",   "color": "#856404", "bg": "#fff3cd", "icon": "⚠️"},
    "red":    {"label": "Offline",     "color": "#842029", "bg": "#f8d7da", "icon": "🔴"},
}

if systems:
    cols = st.columns(len(systems))
    for i, sys in enumerate(systems):
        cfg   = status_config.get(sys["status"], status_config["green"])
        icon  = system_icons.get(sys["system_type"], "🔧")
        label = sys["system_type"].replace("_", " ").title()
        updated = sys["updated_at"].strftime("%b %d") if sys.get("updated_at") else "—"

        with cols[i]:
            st.markdown(f"""
            <div style="
                background:{cfg['bg']}; border-radius:12px; padding:20px;
                text-align:center; border:1px solid {cfg['color']}33;
            ">
                <div style="font-size:2rem;">{icon}</div>
                <div style="font-weight:700; font-size:1rem; margin:6px 0;">{label}</div>
                <div style="color:{cfg['color']}; font-weight:600;">{cfg['icon']} {cfg['label']}</div>
                <div style="color:#888; font-size:0.75rem; margin-top:4px;">Updated {updated}</div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("System health data is being set up. Check back soon.")

st.markdown("---")

# ── Recent Tickets ─────────────────────────────────────────────────────────────
st.subheader("🎫 Recent Tickets")

recent_tickets = fetchall("""
    SELECT * FROM tickets
    WHERE customer_id = %s
    ORDER BY created_at DESC
    LIMIT 5
""", (customer_id,))

if not recent_tickets:
    st.info("No tickets submitted yet.")
else:
    status_badge = {
        "open":        ("📋 Open",        "#6c757d"),
        "in_progress": ("🔧 In Progress",  "#fd7e14"),
        "resolved":    ("✅ Resolved",     "#198754"),
        "closed":      ("🔒 Closed",       "#1a1a2e"),
    }
    urgency_badge = {
        "emergency": "🔴", "high": "🟠", "normal": "🔵", "low": "⚪"
    }

    for t in recent_tickets:
        badge_label, badge_color = status_badge.get(t["status"], ("—", "#333"))
        urg = urgency_badge.get(t["urgency"], "⚪")
        created = t["created_at"].strftime("%b %d, %Y") if t["created_at"] else "—"

        with st.expander(f"{urg} #{t['id']} — {t['title']}  |  {badge_label}"):
            st.markdown(f"**System:** {t['system_type'].replace('_',' ').title()}")
            st.markdown(f"**Submitted:** {created}")
            st.markdown(f"**Description:** {t['description'] or '—'}")
            if t.get("admin_notes"):
                st.info(f"💬 **Update from 5G Security:** {t['admin_notes']}")

st.markdown("---")

# ── Quick actions ──────────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)
with col_a:
    if st.button("➕ Submit a New Ticket", use_container_width=True, type="primary"):
        st.switch_page("pages/submit_ticket.py")
with col_b:
    if st.button("📋 View All Tickets", use_container_width=True):
        st.switch_page("pages/customer_tickets.py")

st.markdown("---")
st.markdown("""
    <div style="text-align:center; color:#888; font-size:0.85rem;">
        Need immediate help? Call <strong>5G Security</strong> at your service number.
    </div>
""", unsafe_allow_html=True)
