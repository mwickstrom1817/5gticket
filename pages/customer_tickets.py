import streamlit as st
from utils.db import fetchall
from utils.theme import inject_global_css, render_sidebar, page_header, status_pill
from utils.auth import logout as _logout
from utils.comments import get_comments, add_comment

inject_global_css()

if "user" not in st.session_state:
    st.warning("Please log in.")
    st.stop()

if "user" in st.session_state:
    render_sidebar(st.session_state["user"], _logout)

user        = st.session_state["user"]
customer_id = user["customer_id"]

page_header("My Tickets", "Support History")

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

            # ── Comments ───────────────────────────────────────────────────────
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
                st.markdown('<div style="font-family:\'DM Mono\',monospace; font-size:0.78rem; color:#444;">No comments yet.</div>', unsafe_allow_html=True)
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
                                    {'🔒 5G Security' if is_admin else '👤 ' + c['author_name']}
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

            # Customer reply form — only on open/in_progress tickets
            if t["status"] in ("open", "in_progress"):
                with st.form(key=f"cust_comment_{t['id']}"):
                    new_comment = st.text_area("Reply", placeholder="Add a comment or additional info...", height=80, label_visibility="collapsed")
                    if st.form_submit_button("💬 Send Reply", type="primary"):
                        if new_comment.strip():
                            add_comment(t["id"], user["name"], "customer", new_comment.strip())
                            st.success("Reply sent.")
                            st.rerun()
                        else:
                            st.warning("Please enter a message.")
            else:
                st.markdown('<div style="font-family:\'DM Mono\',monospace; font-size:0.75rem; color:#444; margin-top:8px;">This ticket is closed — no further replies.</div>', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("➕ Submit New Ticket", type="primary"):
        st.switch_page("pages/submit_ticket.py")
