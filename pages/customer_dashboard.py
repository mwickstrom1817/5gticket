import streamlit as st
from utils.db import fetchall, fetchone
from utils.theme import inject_global_css, render_sidebar, page_header, status_pill

inject_global_css()

# ── Sidebar ───────────────────────────────────────────────────────────────────
from utils.auth import logout as _logout
if "user" in st.session_state:
    render_sidebar(st.session_state["user"], _logout)


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

page_header("System Dashboard", f"{customer['company']}  //  {customer['city'] or ''}{', ' + customer['state'] if customer.get('state') else ''}")

# ── System Health Cards ────────────────────────────────────────────────────────
systems = fetchall("SELECT * FROM systems WHERE customer_id = %s ORDER BY system_type", (customer_id,))

system_meta = {
    "cameras":        ("📷", "Cameras"),
    "access_control": ("🚪", "Access Control"),
    "alarms":         ("🚨", "Alarm Systems"),
    "network":        ("🌐", "Network"),
}

status_cfg = {
    "green":  ("#003d1f", "#00e676", "ONLINE",    "▲"),
    "yellow": ("#3d2800", "#ffab00", "ATTENTION", "◆"),
    "red":    ("#3d0005", "#E8000E", "OFFLINE",   "▼"),
}

if systems:
    cols = st.columns(len(systems))
    for i, sys in enumerate(systems):
        icon, label  = system_meta.get(sys["system_type"], ("🔧", sys["system_type"].title()))
        bg, color, status_label, arrow = status_cfg.get(sys["status"], status_cfg["green"])
        updated = sys["updated_at"].strftime("%b %d, %Y") if sys.get("updated_at") else "—"

        with cols[i]:
            st.markdown(f"""
            <div style="background:#111; border:1px solid #2a2a2a; border-top:3px solid {color};
                        border-radius:3px; padding:1.2rem 1rem; text-align:center;
                        transition:all 0.2s;">
                <div style="font-size:1.8rem; margin-bottom:8px;">{icon}</div>
                <div style="font-family:'Rajdhani',sans-serif; font-weight:700; font-size:1rem;
                            letter-spacing:2px; text-transform:uppercase; color:#f0f0f0;
                            margin-bottom:10px;">{label}</div>
                <div style="background:{bg}; color:{color}; border:1px solid {color}44;
                            font-family:'Share Tech Mono',monospace; font-size:0.72rem;
                            letter-spacing:2px; padding:4px 12px; border-radius:2px;
                            display:inline-block; margin-bottom:8px;">
                    {arrow} {status_label}
                </div>
                <div style="font-family:'Share Tech Mono',monospace; font-size:0.62rem;
                            color:#444; margin-top:6px; letter-spacing:1px;">
                    UPDATED {updated.upper()}
                </div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Recent Tickets ─────────────────────────────────────────────────────────────
col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown("""
        <div style="font-family:'Rajdhani',sans-serif; font-weight:700; font-size:1.1rem;
                    letter-spacing:2px; text-transform:uppercase; color:#f0f0f0;
                    border-bottom:1px solid #2a2a2a; padding-bottom:8px; margin-bottom:1rem;">
            Recent Tickets
        </div>
    """, unsafe_allow_html=True)

    recent = fetchall("""
        SELECT * FROM tickets WHERE customer_id = %s
        ORDER BY created_at DESC LIMIT 5
    """, (customer_id,))

    if not recent:
        st.markdown('<div style="color:#444; font-family:\'Share Tech Mono\',monospace; font-size:0.8rem;">NO TICKETS ON RECORD</div>', unsafe_allow_html=True)
    else:
        for t in recent:
            created = t["created_at"].strftime("%b %d, %Y") if t["created_at"] else "—"
            with st.expander(f"#{t['id']}  //  {t['title']}"):
                st.markdown(f"**System:** {t['system_type'].replace('_',' ').title()}")
                st.markdown(f"**Submitted:** {created}")
                st.markdown(f"**Description:** {t['description'] or '—'}")
                st.markdown(status_pill(t["status"]), unsafe_allow_html=True)
                if t.get("admin_notes"):
                    st.info(f"💬 **Update from 5G Security:** {t['admin_notes']}")

with col_right:
    st.markdown("""
        <div style="font-family:'Rajdhani',sans-serif; font-weight:700; font-size:1.1rem;
                    letter-spacing:2px; text-transform:uppercase; color:#f0f0f0;
                    border-bottom:1px solid #2a2a2a; padding-bottom:8px; margin-bottom:1rem;">
            Quick Actions
        </div>
    """, unsafe_allow_html=True)

    if st.button("➕  SUBMIT NEW TICKET", use_container_width=True, type="primary"):
        st.switch_page("pages/submit_ticket.py")
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📋  VIEW ALL TICKETS", use_container_width=True):
        st.switch_page("pages/customer_tickets.py")
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🎥  MY EQUIPMENT", use_container_width=True):
        st.switch_page("pages/customer_equipment.py")

    st.markdown("""
        <div style="margin-top:2rem; background:#111; border:1px solid #2a2a2a;
                    border-left:3px solid #E8000E; border-radius:2px; padding:1rem;">
            <div style="font-family:'Share Tech Mono',monospace; font-size:0.65rem;
                        letter-spacing:2px; color:#E8000E; text-transform:uppercase;
                        margin-bottom:6px;">Emergency Contact</div>
            <div style="font-family:'Rajdhani',sans-serif; font-weight:600;
                        color:#f0f0f0; font-size:1rem;">5G Security</div>
            <div style="font-family:'Share Tech Mono',monospace; font-size:0.75rem;
                        color:#888; margin-top:4px;">support@fivegsecurity.net</div>
        </div>
    """, unsafe_allow_html=True)