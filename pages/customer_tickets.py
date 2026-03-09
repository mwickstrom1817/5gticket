import streamlit as st
from utils.db import fetchall
from utils.theme import inject_global_css, render_sidebar
from utils.auth import logout as _logout

inject_global_css()

if "user" not in st.session_state:
    st.warning("Please log in.")
    st.stop()

if "user" in st.session_state:
    render_sidebar(st.session_state["user"], _logout)

user        = st.session_state["user"]
customer_id = user["customer_id"]

st.title("🎫 My Tickets")
st.markdown("---")

status_filter = st.selectbox("Filter by Status", ["All", "open", "in_progress", "resolved", "closed"])

query  = "SELECT * FROM tickets WHERE customer_id = %s"
params = [customer_id]
if status_filter != "All":
    query  += " AND status = %s"
    params.append(status_filter)
query += " ORDER BY created_at DESC"

tickets = fetchall(query, params)

if not tickets:
    st.info("No tickets found.")
    if st.button("➕ Submit Your First Ticket", type="primary"):
        st.switch_page("pages/submit_ticket.py")
else:
    status_badge = {
        "open":        ("📋 Open",        "#6c757d"),
        "in_progress": ("🔧 In Progress",  "#fd7e14"),
        "resolved":    ("✅ Resolved",     "#198754"),
        "closed":      ("🔒 Closed",       "#1a1a2e"),
    }
    urgency_badge = {
        "emergency": "🔴 EMERGENCY",
        "high":      "🟠 HIGH",
        "normal":    "🔵 NORMAL",
        "low":       "⚪ LOW",
    }

    for t in tickets:
        badge_label, badge_color = status_badge.get(t["status"], ("—", "#333"))
        urg     = urgency_badge.get(t["urgency"], t["urgency"])
        created = t["created_at"].strftime("%b %d, %Y %I:%M %p") if t["created_at"] else "—"
        updated = t["updated_at"].strftime("%b %d, %Y") if t.get("updated_at") else "—"

        with st.expander(f"{badge_label}  |  #{t['id']} — {t['title']}"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**System:** {t['system_type'].replace('_',' ').title()}")
                st.markdown(f"**Urgency:** {urg}")
                st.markdown(f"**Description:** {t['description'] or '—'}")
                if t.get("photo_url"):
                    st.markdown(f"[📎 View Attached Photo]({t['photo_url']})")
            with col2:
                st.markdown(f"**Submitted:**  \n{created}")
                st.markdown(f"**Last Updated:**  \n{updated}")

            if t.get("admin_notes"):
                st.info(f"💬 **Update from 5G Security:** {t['admin_notes']}")

    st.markdown("---")
    if st.button("➕ Submit New Ticket", type="primary"):
        st.switch_page("pages/submit_ticket.py")