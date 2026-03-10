import streamlit as st
from datetime import datetime, timezone, timedelta
from utils.auth import require_role
from utils.db import fetchall, fetchone
from utils.theme import inject_global_css, render_sidebar, page_header, status_pill, urgency_pill

inject_global_css()
require_role("admin")

# ── Sidebar ───────────────────────────────────────────────────────────────────
from utils.auth import logout as _logout
if "user" in st.session_state:
    render_sidebar(st.session_state["user"], _logout)


page_header("Admin Dashboard", "5G Security // Command Center")

# ── Stats ──────────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

total_customers = fetchone("SELECT COUNT(*) as c FROM customers")["c"]
total_equipment = fetchone("SELECT COUNT(*) as c FROM equipment")["c"]
open_tickets    = fetchone("SELECT COUNT(*) as c FROM tickets WHERE status IN ('open','in_progress')")["c"]
emergency_tix   = fetchone("SELECT COUNT(*) as c FROM tickets WHERE urgency='emergency' AND status NOT IN ('resolved','closed')")["c"]

col1.metric("Total Customers",  total_customers)
col2.metric("Equipment Items",  total_equipment)
col3.metric("Open Tickets",     open_tickets)
col4.metric("🚨 Emergency",     emergency_tix)

st.markdown("<br>", unsafe_allow_html=True)

# ── Open tickets ───────────────────────────────────────────────────────────────
col_l, col_r = st.columns([3, 2])

with col_l:
    st.markdown("""
        <div style="font-family:'Rajdhani',sans-serif; font-weight:700; font-size:1.1rem;
                    letter-spacing:2px; text-transform:uppercase; color:#f0f0f0;
                    border-bottom:1px solid #2a2a2a; padding-bottom:8px; margin-bottom:1rem;">
            Open &amp; In-Progress Tickets
        </div>
    """, unsafe_allow_html=True)

    tickets = fetchall("""
        SELECT t.*, c.company FROM tickets t
        JOIN customers c ON c.id = t.customer_id
        WHERE t.status IN ('open','in_progress')
        ORDER BY CASE t.urgency
            WHEN 'emergency' THEN 1 WHEN 'high' THEN 2
            WHEN 'normal' THEN 3    WHEN 'low'  THEN 4
        END, t.created_at DESC
    """)

    if not tickets:
        st.markdown('<div style="color:#444; font-family:\'Share Tech Mono\',monospace; font-size:0.8rem; padding:1rem 0;">NO OPEN TICKETS — ALL CLEAR</div>', unsafe_allow_html=True)
    else:
        for t in tickets:
            created = t["created_at"].strftime("%b %d, %Y") if t["created_at"] else "—"
            with st.expander(f"#{t['id']}  //  {t['company']}  —  {t['title']}"):
                st.markdown(
                    f"{urgency_pill(t['urgency'])}  &nbsp;  {status_pill(t['status'])}",
                    unsafe_allow_html=True
                )
                st.markdown(f"**System:** {t['system_type'].replace('_',' ').title()}")
                st.markdown(f"**Description:** {t['description'] or '—'}")
                if t.get("photo_url"):
                    st.markdown(f"[📎 View Photo]({t['photo_url']})")
                st.caption(f"Submitted: {created}")
                st.page_link("pages/admin_tickets.py", label="→ Manage in Tickets")

with col_r:
    st.markdown("""
        <div style="font-family:'Rajdhani',sans-serif; font-weight:700; font-size:1.1rem;
                    letter-spacing:2px; text-transform:uppercase; color:#f0f0f0;
                    border-bottom:1px solid #2a2a2a; padding-bottom:8px; margin-bottom:1rem;">
            System Health Overview
        </div>
    """, unsafe_allow_html=True)

    systems = fetchall("""
        SELECT c.company, s.system_type, s.status, s.updated_at
        FROM systems s JOIN customers c ON c.id = s.customer_id
        ORDER BY c.company, s.system_type
    """)

    if not systems:
        st.info("No systems configured yet.")
    else:
        status_dot = {"green": ("🟢", "#00e676"), "yellow": ("🟡", "#ffab00"), "red": ("🔴", "#E8000E")}
        current_company = None
        for s in systems:
            if s["company"] != current_company:
                if current_company:
                    st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(f'<div style="font-family:\'Rajdhani\',sans-serif; font-weight:700; font-size:0.95rem; letter-spacing:1px; color:#f0f0f0; text-transform:uppercase;">{s["company"]}</div>', unsafe_allow_html=True)
                current_company = s["company"]

            dot, color = status_dot.get(s["status"], ("⚪", "#555"))
            updated = s["updated_at"].strftime("%b %d") if s["updated_at"] else "—"
            st.markdown(
                f'<div style="display:flex; align-items:center; gap:8px; padding:3px 0 3px 8px;">'
                f'{dot} <span style="font-family:\'Share Tech Mono\',monospace; font-size:0.75rem; color:#888;">'
                f'{s["system_type"].replace("_"," ").upper()}</span>'
                f'<span style="font-family:\'Share Tech Mono\',monospace; font-size:0.65rem; color:#444; margin-left:auto;">{updated}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

# ── Agent Health ───────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
    <div style="font-family:'Rajdhani',sans-serif; font-weight:700; font-size:1.1rem;
                letter-spacing:2px; text-transform:uppercase; color:#f0f0f0;
                border-bottom:1px solid #2a2a2a; padding-bottom:8px; margin-bottom:1rem;">
        Site Agent Health
    </div>
""", unsafe_allow_html=True)

agent_sites = fetchall("""
    SELECT c.company, c.id as customer_id,
           MAX(s.last_polled) as last_polled
    FROM customers c
    LEFT JOIN systems s ON s.customer_id = c.id AND s.auto_updated = TRUE
    GROUP BY c.id, c.company
    ORDER BY c.company
""")

now = datetime.now(timezone.utc)

if not agent_sites:
    st.info("No customers configured yet.")
else:
    cols = st.columns(min(len(agent_sites), 4))
    for i, site in enumerate(agent_sites):
        with cols[i % 4]:
            last_polled = site["last_polled"]

            if last_polled is None:
                dot        = "⚪"
                label      = "NO AGENT"
                age_str    = "Never polled"
                card_color = "#1a1a1a"
                border     = "#333"
            else:
                # Make sure last_polled is timezone-aware
                if last_polled.tzinfo is None:
                    last_polled = last_polled.replace(tzinfo=timezone.utc)
                age = now - last_polled
                mins = int(age.total_seconds() / 60)

                if age < timedelta(minutes=10):
                    dot        = "🟢"
                    label      = "ONLINE"
                    card_color = "#0a1a0a"
                    border     = "#00e676"
                elif age < timedelta(minutes=30):
                    dot        = "🟡"
                    label      = "DELAYED"
                    card_color = "#1a1500"
                    border     = "#ffab00"
                else:
                    dot        = "🔴"
                    label      = "OFFLINE"
                    card_color = "#1a0a0a"
                    border     = "#E8000E"

                if mins < 60:
                    age_str = f"{mins}m ago"
                elif mins < 1440:
                    age_str = f"{mins // 60}h {mins % 60}m ago"
                else:
                    age_str = last_polled.strftime("%b %d, %H:%M")

            st.markdown(f"""
                <div style="background:{card_color}; border:1px solid {border};
                            border-radius:4px; padding:14px 16px; margin-bottom:8px;">
                    <div style="font-family:'Rajdhani',sans-serif; font-weight:700;
                                font-size:0.95rem; letter-spacing:1px; color:#f0f0f0;
                                text-transform:uppercase; margin-bottom:4px;">
                        {dot} &nbsp; {site['company']}
                    </div>
                    <div style="font-family:'DM Mono',monospace; font-size:0.65rem;
                                letter-spacing:2px; color:{border}; margin-bottom:6px;">
                        {label}
                    </div>
                    <div style="font-family:'Share Tech Mono',monospace; font-size:0.7rem;
                                color:#555;">
                        Last poll: {age_str}
                    </div>
                </div>
            """, unsafe_allow_html=True)
