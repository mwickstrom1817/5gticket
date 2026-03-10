"""
pages/admin_system_health.py
Admin bird's-eye view of all customer system health.
Shows summarized camera, storage, and NVR status per customer.
"""

import streamlit as st
from datetime import datetime, timezone, timedelta
from utils.auth import require_role, logout as _logout
from utils.db import fetchall
from utils.theme import inject_global_css, render_sidebar, page_header

inject_global_css()
require_role("admin")

if "user" in st.session_state:
    render_sidebar(st.session_state["user"], _logout)

page_header("System Health", "5G Security // All Customer Sites")

# ── Fetch all customers + their health data ────────────────────────────────────
customers = fetchall("SELECT * FROM customers ORDER BY company")

if not customers:
    st.info("No customers yet.")
    st.stop()

# Build a lookup of system statuses per customer
customer_ids = [c["id"] for c in customers]

systems = fetchall("""
    SELECT customer_id, system_type, status, auto_updated, last_polled
    FROM systems
    WHERE customer_id = ANY(%s)
""", (customer_ids,))

cameras = fetchall("""
    SELECT customer_id,
           COUNT(*)                                            AS total,
           SUM(CASE WHEN status='online'  THEN 1 ELSE 0 END) AS online,
           SUM(CASE WHEN is_recording     THEN 1 ELSE 0 END) AS recording,
           SUM(CASE WHEN status='offline' THEN 1 ELSE 0 END) AS offline,
           MAX(updated_at)                                    AS last_updated
    FROM camera_health
    WHERE customer_id = ANY(%s)
    GROUP BY customer_id
""", (customer_ids,))

storage = fetchall("""
    SELECT customer_id, total_gb, used_gb, free_gb, pct_used, has_error, updated_at
    FROM storage_health
    WHERE customer_id = ANY(%s)
""", (customer_ids,))

nvr = fetchall("""
    SELECT customer_id, name, version, status, updated_at
    FROM nvr_info
    WHERE customer_id = ANY(%s)
""", (customer_ids,))

# Index by customer_id
sys_map  = {}
for s in systems:
    sys_map.setdefault(s["customer_id"], {})[s["system_type"]] = s

cam_map  = {r["customer_id"]: r for r in cameras}
stor_map = {r["customer_id"]: r for r in storage}
nvr_map  = {r["customer_id"]: r for r in nvr}

# ── Summary bar ───────────────────────────────────────────────────────────────
now = datetime.now(timezone.utc)

total_sites    = len(customers)
sites_ok       = 0
sites_warn     = 0
sites_offline  = 0
sites_no_agent = 0

for c in customers:
    cid  = c["id"]
    cams = cam_map.get(cid)
    stor = stor_map.get(cid)
    sys  = sys_map.get(cid, {})
    cam_sys = sys.get("cameras", {})

    if not cams:
        sites_no_agent += 1
        continue

    cam_status = cam_sys.get("status", "green")
    stor_pct   = stor.get("pct_used", 0) if stor else 0
    has_error  = stor.get("has_error", False) if stor else False

    if cam_status == "red" or has_error or stor_pct >= 85:
        sites_offline += 1
    elif cam_status == "yellow" or stor_pct >= 70:
        sites_warn += 1
    else:
        sites_ok += 1

col_a, col_b, col_c, col_d = st.columns(4)

def summary_pill(col, label, value, color, bg):
    with col:
        st.markdown(f"""
            <div style="background:{bg}; border:1px solid {color}33;
                        border-top:3px solid {color}; border-radius:3px;
                        padding:1rem; text-align:center;">
                <div style="font-family:'Barlow',sans-serif; font-weight:700;
                            font-size:2rem; color:{color}; line-height:1;">{value}</div>
                <div style="font-family:'DM Mono',monospace; font-size:0.65rem;
                            letter-spacing:2px; color:#555; text-transform:uppercase;
                            margin-top:4px;">{label}</div>
            </div>
        """, unsafe_allow_html=True)

summary_pill(col_a, "Total Sites",    total_sites,    "#888",    "#111")
summary_pill(col_b, "All Clear",      sites_ok,       "#00e676", "#0a1a0a")
summary_pill(col_c, "Needs Attention",sites_warn,     "#ffab00", "#1a1500")
summary_pill(col_d, "Issues / Offline", sites_offline + sites_no_agent, "#E8000E", "#1a0a0a")

st.markdown("<br>", unsafe_allow_html=True)

# ── Filter bar ────────────────────────────────────────────────────────────────
col_search, col_filter = st.columns([3, 1])
with col_search:
    search = st.text_input("Search", placeholder="Search customers...", label_visibility="collapsed")
with col_filter:
    filter_status = st.selectbox("Filter", ["All", "Issues", "Warning", "OK", "No Agent"],
                                  label_visibility="collapsed")

st.markdown("<br>", unsafe_allow_html=True)

# ── Customer cards ────────────────────────────────────────────────────────────
def agent_freshness(last_polled):
    """Return color + label based on how recently the agent checked in."""
    if not last_polled:
        return "#555", "NO AGENT"
    # Make timezone-aware if needed
    if last_polled.tzinfo is None:
        last_polled = last_polled.replace(tzinfo=timezone.utc)
    age = now - last_polled
    if age < timedelta(minutes=10):
        return "#00e676", f"LIVE · {int(age.total_seconds() // 60)}m ago"
    elif age < timedelta(minutes=30):
        return "#ffab00", f"STALE · {int(age.total_seconds() // 60)}m ago"
    else:
        hours = age.total_seconds() / 3600
        label = f"{int(hours)}h ago" if hours < 24 else f"{int(hours//24)}d ago"
        return "#E8000E", f"OFFLINE · {label}"

for c in customers:
    cid    = c["id"]
    cams   = cam_map.get(cid)
    stor   = stor_map.get(cid)
    nvr_r  = nvr_map.get(cid)
    sys    = sys_map.get(cid, {})
    cam_sys = sys.get("cameras", {})
    acc_sys = sys.get("access_control", {})

    # Determine overall site status
    stor_pct  = stor.get("pct_used", 0)  if stor else 0
    has_error = stor.get("has_error", False) if stor else False
    cam_status = cam_sys.get("status", "green") if cams else "unknown"

    if not cams:
        site_color, site_bg, site_label = "#555", "#111", "NO AGENT DATA"
    elif cam_status == "red" or has_error or stor_pct >= 85:
        site_color, site_bg, site_label = "#E8000E", "#1a0505", "ATTENTION REQUIRED"
    elif cam_status == "yellow" or stor_pct >= 70:
        site_color, site_bg, site_label = "#ffab00", "#1a1505", "WARNING"
    else:
        site_color, site_bg, site_label = "#00e676", "#051a0a", "ALL CLEAR"

    # Apply search/filter
    if search and search.lower() not in c["company"].lower():
        continue
    if filter_status == "Issues"   and site_label not in ("ATTENTION REQUIRED",):
        continue
    if filter_status == "Warning"  and site_label != "WARNING":
        continue
    if filter_status == "OK"       and site_label != "ALL CLEAR":
        continue
    if filter_status == "No Agent" and site_label != "NO AGENT DATA":
        continue

    # Agent freshness
    last_polled   = cam_sys.get("last_polled") if cam_sys else None
    agent_color, agent_label = agent_freshness(last_polled)

    # Camera stats
    if cams:
        cam_total     = cams["total"]     or 0
        cam_online    = cams["online"]    or 0
        cam_recording = cams["recording"] or 0
        cam_offline   = cams["offline"]   or 0
    else:
        cam_total = cam_online = cam_recording = cam_offline = 0

    # Storage
    if stor and stor.get("total_gb", 0) > 0:
        pct       = stor["pct_used"] or 0
        bar_color = "#00e676" if pct < 70 else ("#ffab00" if pct < 85 else "#E8000E")
        err_txt   = "  ·  DISK ERROR" if has_error else ""
        p         = str(pct)
        stor_html = (
            '<div style="margin-top:8px;">'
            + '<div style="display:flex;justify-content:space-between;margin-bottom:3px;">'
            + '<div style="font-family:DM Mono,monospace;font-size:0.65rem;color:#555;">STORAGE</div>'
            + '<div style="font-family:DM Mono,monospace;font-size:0.65rem;color:' + bar_color + ';">' + p + '%</div>'
            + '</div>'
            + '<div style="background:#1a1a1a;border-radius:2px;height:5px;overflow:hidden;">'
            + '<div style="background:' + bar_color + ';width:' + p + '%;height:100%;border-radius:2px;"></div>'
            + '</div>'
            + '<div style="font-family:DM Mono,monospace;font-size:0.62rem;color:#444;margin-top:2px;">'
            + str(stor["free_gb"]) + " GB free of " + str(stor["total_gb"]) + " GB" + err_txt
            + '</div>'
            + '</div>'
        )
    else:
        stor_html = '<div style="font-family:DM Mono,monospace;font-size:0.62rem;color:#333;margin-top:8px;">NO STORAGE DATA</div>'

    # NVR
    if nvr_r:
        nvr_ok    = nvr_r.get("status") in ("online", "running", "")
        nvr_color = "#00e676" if nvr_ok else "#E8000E"
        nvr_name  = nvr_r.get("name", "—")
        nvr_ver   = nvr_r.get("version", "?")
        nvr_html  = (
            '<div style="font-family:DM Mono,monospace;font-size:0.65rem;color:' + nvr_color + ';margin-top:6px;">'
            'NVR: ' + nvr_name + ' · v' + nvr_ver +
            '</div>'
        )
    else:
        nvr_html = ""

    # Access control status dot
    acc_status = acc_sys.get("status", "green") if acc_sys else "green"
    acc_colors = {"green": "#00e676", "yellow": "#ffab00", "red": "#E8000E"}
    acc_color  = acc_colors.get(acc_status, "#555")

    # Build card HTML as a plain string to avoid nested f-string issues
    offline_block = ""
    if cam_offline > 0:
        offline_block = (
            '<div style="text-align:center;">'
            '<div style="font-family:Barlow,sans-serif;font-weight:700;font-size:1.4rem;color:#E8000E;line-height:1;">' + str(cam_offline) + '</div>'
            '<div style="font-family:DM Mono,monospace;font-size:0.58rem;color:#E8000E;letter-spacing:1px;text-transform:uppercase;">Offline</div>'
            '</div>'
        )

    cam_color = "#00e676" if cam_offline == 0 else "#E8000E"
    rec_color = "#E8000E" if cam_recording > 0 else "#333"
    location  = (c.get("city") or "") + (", " + c["state"] if c.get("state") else "")

    offline_block = ""
    if cam_offline > 0:
        offline_block = (
            '<div style="text-align:center;">'
            '<div style="font-family:Barlow,sans-serif;font-weight:700;font-size:1.4rem;'
            'color:#E8000E;line-height:1;">' + str(cam_offline) + '</div>'
            '<div style="font-family:DM Mono,monospace;font-size:0.58rem;'
            'color:#E8000E;letter-spacing:1px;text-transform:uppercase;">Offline</div>'
            '</div>'
        )

    card = (
        '<div style="background:' + site_bg + ';border:1px solid #2a2a2a;'
        'border-left:4px solid ' + site_color + ';border-radius:3px;'
        'padding:1rem 1.5rem;margin-bottom:10px;">'

        # Header
        '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;">'
        '<div>'
        '<div style="font-family:Barlow,sans-serif;font-weight:700;font-size:1rem;'
        'letter-spacing:1.5px;text-transform:uppercase;color:#f0f0f0;">' + c["company"] + '</div>'
        '<div style="font-family:DM Mono,monospace;font-size:0.62rem;color:#444;margin-top:2px;">'
        + location + ' &nbsp;·&nbsp; ID #' + str(cid) + '</div>'
        '</div>'
        '<div style="text-align:right;">'
        '<div style="font-family:DM Mono,monospace;font-size:0.65rem;'
        'letter-spacing:2px;color:' + site_color + ';text-transform:uppercase;">' + site_label + '</div>'
        '<div style="font-family:DM Mono,monospace;font-size:0.6rem;'
        'color:' + agent_color + ';margin-top:2px;">⚡ ' + agent_label + '</div>'
        '</div>'
        '</div>'

        # Stats row
        '<div style="display:flex;gap:24px;flex-wrap:wrap;align-items:center;">'

        '<div style="display:flex;gap:16px;align-items:center;">'
        '<div style="text-align:center;">'
        '<div style="font-family:Barlow,sans-serif;font-weight:700;font-size:1.4rem;'
        'color:' + cam_color + ';line-height:1;">' + str(cam_online) + '/' + str(cam_total) + '</div>'
        '<div style="font-family:DM Mono,monospace;font-size:0.58rem;'
        'color:#555;letter-spacing:1px;text-transform:uppercase;">Cameras</div>'
        '</div>'
        '<div style="text-align:center;">'
        '<div style="font-family:Barlow,sans-serif;font-weight:700;font-size:1.4rem;'
        'color:' + rec_color + ';line-height:1;">' + str(cam_recording) + '</div>'
        '<div style="font-family:DM Mono,monospace;font-size:0.58rem;'
        'color:#555;letter-spacing:1px;text-transform:uppercase;">Recording</div>'
        '</div>'
        + offline_block +
        '</div>'

        '<div style="width:1px;height:40px;background:#2a2a2a;"></div>'

        '<div style="text-align:center;">'
        '<div style="width:12px;height:12px;border-radius:50%;background:' + acc_color + ';'
        'margin:0 auto 4px auto;box-shadow:0 0 6px ' + acc_color + '44;"></div>'
        '<div style="font-family:DM Mono,monospace;font-size:0.58rem;'
        'color:#555;letter-spacing:1px;text-transform:uppercase;">Access</div>'
        '</div>'

        '<div style="flex:1;min-width:200px;">'
        + stor_html + nvr_html +
        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(card, unsafe_allow_html=True)

# ── Refresh button ─────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
if st.button("🔄 Refresh", use_container_width=False):
    st.rerun()
