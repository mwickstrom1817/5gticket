import streamlit as st
from utils.auth import require_role
from utils.db import fetchall, fetchone, execute
from utils.email_notify import send_ticket_status_update

require_role("admin")

st.title("🎫 Manage Tickets")
st.markdown("---")

# ── Filters ────────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    status_filter = st.selectbox("Status", ["All Open", "open", "in_progress", "resolved", "closed", "All"])
with col2:
    urgency_filter = st.selectbox("Urgency", ["All", "emergency", "high", "normal", "low"])
with col3:
    customers = fetchall("SELECT id, company FROM customers ORDER BY company")
    cust_map  = {"All": None} | {c["company"]: c["id"] for c in customers}
    cust_choice = st.selectbox("Customer", list(cust_map.keys()))

# Build query
conditions = []
params = []

if status_filter == "All Open":
    conditions.append("t.status IN ('open','in_progress')")
elif status_filter != "All":
    conditions.append("t.status = %s")
    params.append(status_filter)

if urgency_filter != "All":
    conditions.append("t.urgency = %s")
    params.append(urgency_filter)

if cust_map[cust_choice]:
    conditions.append("t.customer_id = %s")
    params.append(cust_map[cust_choice])

where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

tickets = fetchall(f"""
    SELECT t.*, c.company, c.email as cust_email
    FROM tickets t
    JOIN customers c ON c.id = t.customer_id
    {where}
    ORDER BY
        CASE t.urgency
            WHEN 'emergency' THEN 1 WHEN 'high' THEN 2
            WHEN 'normal' THEN 3    WHEN 'low'  THEN 4
        END,
        t.created_at DESC
""", params if params else None)

st.markdown(f"**{len(tickets)} ticket(s) found**")
st.markdown("---")

urgency_badge = {
    "emergency": "🔴", "high": "🟠", "normal": "🔵", "low": "⚪"
}
status_options = ["open", "in_progress", "resolved", "closed"]

for t in tickets:
    badge = urgency_badge.get(t["urgency"], "⚪")
    created = t["created_at"].strftime("%b %d, %Y %I:%M %p") if t["created_at"] else "—"

    with st.expander(
        f"{badge} #{t['id']} — {t['company']} | {t['title']} "
        f"[{t['status'].replace('_',' ').upper()}]"
    ):
        col_left, col_right = st.columns([3, 2])

        with col_left:
            st.markdown(f"**System:** {t['system_type'].replace('_',' ').title()}")
            st.markdown(f"**Urgency:** {t['urgency'].upper()}")
            st.markdown(f"**Description:**")
            st.markdown(t["description"] or "_No description_")
            if t.get("photo_url"):
                st.markdown(f"[📎 View Attached Photo]({t['photo_url']})")
            st.caption(f"Submitted: {created}")

        with col_right:
            new_status = st.selectbox(
                "Status",
                status_options,
                index=status_options.index(t["status"]),
                key=f"st_{t['id']}"
            )
            new_notes = st.text_area(
                "Admin Notes (visible to customer)",
                value=t.get("admin_notes") or "",
                key=f"an_{t['id']}",
                height=120
            )
            notify = st.checkbox("Notify customer by email", value=True, key=f"notify_{t['id']}")

            if st.button("💾 Update Ticket", key=f"upd_{t['id']}", type="primary"):
                execute("""
                    UPDATE tickets
                    SET status=%s, admin_notes=%s, updated_at=NOW()
                    WHERE id=%s
                """, (new_status, new_notes, t["id"]))

                if notify and t.get("cust_email"):
                    updated_ticket = dict(t)
                    updated_ticket["status"]      = new_status
                    updated_ticket["admin_notes"] = new_notes

                    # Get customer contact name
                    user = fetchone(
                        "SELECT name FROM users WHERE customer_id=%s AND role='customer'",
                        (t["customer_id"],)
                    )
                    cust_name = user["name"] if user else t["company"]
                    send_ticket_status_update(updated_ticket, t["cust_email"], cust_name)

                st.success(f"Ticket #{t['id']} updated.")
                st.rerun()
