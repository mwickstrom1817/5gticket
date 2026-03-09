import streamlit as st
from datetime import datetime, timezone
from utils.auth import require_role, logout as _logout
from utils.db import fetchall, fetchone, execute
from utils.email_notify import send_ticket_status_update
from utils.comments import get_comments, add_comment
from utils.theme import inject_global_css, render_sidebar, page_header, status_pill, urgency_pill

inject_global_css()
require_role("admin")

if "user" in st.session_state:
    render_sidebar(st.session_state["user"], _logout)

page_header("Tickets", "5G Security // Support Queue")


def time_ago(dt):
    """Return a human-readable time since dt."""
    if not dt:
        return "—"
    now    = datetime.now(timezone.utc)
    diff   = now - dt
    hours  = diff.total_seconds() / 3600
    days   = diff.days

    if hours < 1:
        mins = int(diff.total_seconds() / 60)
        return f"{mins}m ago"
    elif hours < 24:
        return f"{int(hours)}h ago"
    elif days == 1:
        return "1 day ago"
    else:
        return f"{days} days ago"


def age_color(dt):
    """Return a color based on ticket age."""
    if not dt:
        return "#555"
    diff  = datetime.now(timezone.utc) - dt
    hours = diff.total_seconds() / 3600
    if hours < 24:
        return "#00e676"   # green — under 24hrs
    elif hours < 48:
        return "#ffab00"   # yellow — 24-48hrs
    else:
        return "#E8000E"   # red — over 48hrs


# ── Filters ────────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    status_filter = st.selectbox("Status", ["All Open", "open", "in_progress", "resolved", "closed", "All"])
with col2:
    urgency_filter = st.selectbox("Urgency", ["All", "emergency", "high", "normal", "low"])
with col3:
    customers   = fetchall("SELECT id, company FROM customers ORDER BY company")
    cust_map    = {"All": None} | {c["company"]: c["id"] for c in customers}
    cust_choice = st.selectbox("Customer", list(cust_map.keys()))

# Build query
conditions = []
params     = []

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
            WHEN 'normal'    THEN 3 WHEN 'low'  THEN 4
        END,
        t.created_at DESC
""", params if params else None)

st.markdown(f"**{len(tickets)} ticket(s) found**")
st.markdown("---")

status_options = ["open", "in_progress", "resolved", "closed"]

for t in tickets:
    created   = t["created_at"].strftime("%b %d, %Y %I:%M %p") if t["created_at"] else "—"
    age_col   = age_color(t["created_at"])
    age_label = time_ago(t["created_at"])

    # Response time info
    if t.get("first_responded_at"):
        response_time = t["first_responded_at"] - t["created_at"]
        response_hrs  = response_time.total_seconds() / 3600
        if response_hrs < 1:
            resp_label = f"{int(response_time.total_seconds()/60)}m"
        elif response_hrs < 24:
            resp_label = f"{int(response_hrs)}h"
        else:
            resp_label = f"{response_time.days}d"
        resp_str = f"First response: {resp_label}"
    else:
        resp_str = "No response yet"

    auto_badge = " 🤖 AUTO" if t.get("auto_generated") else ""
    with st.expander(
        f"#{t['id']}  //  {t['company']}  —  {t['title']}  [{t['status'].replace('_',' ').upper()}]{auto_badge}"
    ):
        # Age indicator
        st.markdown(f"""
            <div style="display:flex; gap:12px; align-items:center; margin-bottom:1rem;">
                {urgency_pill(t['urgency'])}
                {status_pill(t['status'])}
                <span style="font-family:'DM Mono',monospace; font-size:0.75rem; color:{age_col};">
                    ⏱ Open {age_label}
                </span>
                <span style="font-family:'DM Mono',monospace; font-size:0.75rem; color:#555;">
                    {resp_str}
                </span>
            </div>
        """, unsafe_allow_html=True)

        col_left, col_right = st.columns([3, 2])

        with col_left:
            st.markdown(f"**System:** {t['system_type'].replace('_',' ').title()}")
            st.markdown(f"**Description:** {t['description'] or '—'}")
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
                height=100
            )
            notify = st.checkbox("Notify customer by email", value=True, key=f"notify_{t['id']}")

            if st.button("💾 Update Ticket", key=f"upd_{t['id']}", type="primary"):
                now = datetime.now(timezone.utc)

                # Set first_responded_at if this is the first status change
                first_responded_at = t.get("first_responded_at")
                if not first_responded_at and new_status != "open":
                    first_responded_at = now

                # Set resolved_at if resolving or closing
                resolved_at = t.get("resolved_at")
                if not resolved_at and new_status in ("resolved", "closed"):
                    resolved_at = now

                execute("""
                    UPDATE tickets
                    SET status=%s, admin_notes=%s, updated_at=%s,
                        first_responded_at=%s, resolved_at=%s
                    WHERE id=%s
                """, (new_status, new_notes, now,
                      first_responded_at, resolved_at, t["id"]))

                if notify and t.get("cust_email"):
                    updated_ticket = dict(t)
                    updated_ticket["status"]      = new_status
                    updated_ticket["admin_notes"] = new_notes
                    user = fetchone(
                        "SELECT name FROM users WHERE customer_id=%s AND role='customer'",
                        (t["customer_id"],)
                    )
                    cust_name = user["name"] if user else t["company"]
                    send_ticket_status_update(updated_ticket, t["cust_email"], cust_name)

                st.success(f"Ticket #{t['id']} updated.")
                st.rerun()

        # ── Comments ───────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("""
            <div style="font-family:'Barlow',sans-serif; font-weight:700; font-size:0.95rem;
                        letter-spacing:1px; text-transform:uppercase; color:#f0f0f0;
                        margin-bottom:0.75rem;">
                💬 Comments
            </div>
        """, unsafe_allow_html=True)

        comments = get_comments(t["id"])

        if not comments:
            st.markdown('<div style="font-family:\'DM Mono\',monospace; font-size:0.78rem; color:#444; margin-bottom:0.5rem;">No comments yet.</div>', unsafe_allow_html=True)
        else:
            for c in comments:
                is_admin   = c["author_role"] == "admin"
                bg         = "#1a1a1a" if is_admin else "#0f1a0f"
                border_col = "#E8000E" if is_admin else "#00e676"
                created_c  = c["created_at"].strftime("%b %d, %Y %I:%M %p") if c["created_at"] else ""
                st.markdown(f"""
                    <div style="background:{bg}; border:1px solid #2a2a2a;
                                border-left:3px solid {border_col}; border-radius:2px;
                                padding:10px 14px; margin-bottom:8px;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                            <span style="font-family:'Barlow',sans-serif; font-weight:600;
                                         font-size:0.85rem; color:{border_col};">
                                {'🔒 ' if is_admin else '👤 '}{c['author_name']}
                            </span>
                            <span style="font-family:'DM Mono',monospace; font-size:0.68rem; color:#444;">
                                {created_c}
                            </span>
                        </div>
                        <div style="font-family:'DM Sans',sans-serif; font-size:0.9rem; color:#ccc;">
                            {c['message']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        with st.form(key=f"comment_form_{t['id']}"):
            new_comment = st.text_area("Add a comment", placeholder="Type your response here...", height=80, label_visibility="collapsed")
            if st.form_submit_button("💬 Post Comment", type="primary"):
                if new_comment.strip():
                    admin_name = st.session_state["user"]["name"]
                    add_comment(t["id"], admin_name, "admin", new_comment.strip())
                    st.success("Comment posted.")
                    st.rerun()
                else:
                    st.warning("Please enter a comment.")
