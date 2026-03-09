import streamlit as st
from utils.auth import require_role
from utils.db import fetchall, fetchone

require_role("admin")

st.title("📊 Admin Dashboard")
st.markdown("---")

# ── Summary stats ──────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

total_customers = fetchone("SELECT COUNT(*) as c FROM customers")["c"]
total_equipment = fetchone("SELECT COUNT(*) as c FROM equipment")["c"]
open_tickets    = fetchone("SELECT COUNT(*) as c FROM tickets WHERE status IN ('open','in_progress')")["c"]
emergency_tix   = fetchone("SELECT COUNT(*) as c FROM tickets WHERE urgency='emergency' AND status NOT IN ('resolved','closed')")["c"]

col1.metric("Customers",        total_customers)
col2.metric("Equipment Items",  total_equipment)
col3.metric("Open Tickets",     open_tickets)
col4.metric("🚨 Emergency",     emergency_tix)

st.markdown("---")

# ── Open tickets ───────────────────────────────────────────────────────────────
st.subheader("🎫 Open & In-Progress Tickets")

tickets = fetchall("""
    SELECT t.*, c.company
    FROM tickets t
    JOIN customers c ON c.id = t.customer_id
    WHERE t.status IN ('open', 'in_progress')
    ORDER BY
        CASE t.urgency
            WHEN 'emergency' THEN 1
            WHEN 'high'      THEN 2
            WHEN 'normal'    THEN 3
            WHEN 'low'       THEN 4
        END,
        t.created_at DESC
""")

if not tickets:
    st.success("✅ No open tickets right now.")
else:
    urgency_badge = {
        "emergency": "🔴 EMERGENCY",
        "high":      "🟠 HIGH",
        "normal":    "🔵 NORMAL",
        "low":       "⚪ LOW",
    }
    status_badge = {
        "open":        "📋 Open",
        "in_progress": "🔧 In Progress",
    }

    for t in tickets:
        with st.expander(
            f"{urgency_badge.get(t['urgency'], t['urgency'])}  |  "
            f"#{t['id']} — {t['company']} — {t['title']}  "
            f"({status_badge.get(t['status'], t['status'])})"
        ):
            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.markdown(f"**System:** {t['system_type'].replace('_',' ').title()}")
                st.markdown(f"**Description:** {t['description'] or '—'}")
                if t.get("photo_url"):
                    st.markdown(f"[📎 View Photo]({t['photo_url']})")
                st.caption(f"Submitted: {t['created_at'].strftime('%b %d, %Y %I:%M %p') if t['created_at'] else '—'}")
            with col_b:
                st.markdown(f"**Admin Notes:**")
                st.markdown(t.get("admin_notes") or "_None yet_")
            st.page_link("pages/admin_tickets.py", label="→ Manage this ticket")

st.markdown("---")

# ── System health overview ─────────────────────────────────────────────────────
st.subheader("🟢 System Health Overview")

systems = fetchall("""
    SELECT c.company, s.system_type, s.status, s.updated_at
    FROM systems s
    JOIN customers c ON c.id = s.customer_id
    ORDER BY c.company, s.system_type
""")

if not systems:
    st.info("No systems configured yet. Add customers and assign systems.")
else:
    status_icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
    current_company = None
    for s in systems:
        if s["company"] != current_company:
            if current_company is not None:
                st.markdown("---")
            st.markdown(f"**{s['company']}**")
            current_company = s["company"]
        icon = status_icon.get(s["status"], "⚪")
        updated = s["updated_at"].strftime("%b %d") if s["updated_at"] else "—"
        st.markdown(
            f"&nbsp;&nbsp;&nbsp;{icon} {s['system_type'].replace('_',' ').title()} "
            f"<span style='color:#999; font-size:0.8rem;'>— updated {updated}</span>",
            unsafe_allow_html=True
        )
