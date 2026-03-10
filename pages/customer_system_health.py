"""
pages/customer_system_health.py
Live system health dashboard powered by DW Spectrum cloud API.
"""

import streamlit as st
from utils.db import fetchone
from utils.theme import inject_global_css, render_sidebar, page_header
from utils.auth import logout as _logout
from utils.dw_spectrum import system_summary

inject_global_css()

if "user" not in st.session_state:
    st.warning("Please log in.")
    st.stop()

user = st.session_state["user"]
if user["role"] == "admin":
    st.switch_page("pages/admin_dashboard.py")

render_sidebar(user, _logout)

customer_id = user["customer_id"]
customer    = fetchone("SELECT * FROM customers WHERE id = %s", (customer_id,))

if not customer:
    st.error("Customer account not found.")
    st.stop()

page_header("System Health", f"{customer['company']}  //  Live Camera & NVR Status")

spectrum_system_id = customer.get("spectrum_system_id")

if not spectrum_system_id:
    st.markdown("""
        <div style="background:#111; border:1px solid #2a2a2a; border-left:3px solid #ffab00;
                    border-radius:3px; padding:2rem; margin-top:1rem; text-align:center;">
            <div style="font-size:2.5rem; margin-bottom:1rem;">📡</div>
            <div style="font-family:'Rajdhani',sans-serif; font-weight:700; font-size:1.1rem;
                        letter-spacing:2px; color:#ffab00; text-transform:uppercase; margin-bottom:0.5rem;">
                Live Monitoring Not Yet Configured
            </div>
            <div style="font-family:'DM Sans',sans-serif; font-size:0.9rem; color:#666; max-width:400px; margin:0 auto;">
                Contact 5G Security to get your system linked to live monitoring.
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# Refresh button
_, col_refresh = st.columns([5, 1])
with col_refresh:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with st.spinner("Fetching live system data..."):
    data = system_summary(spectrum_system_id)

cameras = data["cameras"]
storage = data["storage"]
server  = data["server"]

# ── Debug expander — shows raw API data to help diagnose issues ────────────────
with st.expander("🔧 Debug — Raw API Response (remove once working)", expanded=True):
    st.json({
        "spectrum_system_id": spectrum_system_id,
        "total_cams":     data["total_cams"],
        "online_cams":    data["online_cams"],
        "offline_cams":   data["offline_cams"],
        "recording":      data["recording"],
        "storage":        storage,
        "server":         server,
        "cameras_sample": cameras[:2] if cameras else [],
        "cam_error":      data.get("cam_err"),
        "storage_error":  data.get("stor_err"),
        "server_error":   data.get("srv_err"),
    })

# ── Overall status banner ──────────────────────────────────────────────────────
storage_warn = storage.get("pct_used", 0) >= 85
has_issues   = data["offline_cams"] > 0 or storage.get("has_error") or storage_warn

if not has_issues:
    banner_bg, banner_border, banner_color, banner_icon, banner_label = (
        "#0a1a0a", "#00e676", "#00e676", "✅", "ALL SYSTEMS OPERATIONAL"
    )
elif data["offline_cams"] > 0 or storage.get("has_error"):
    banner_bg, banner_border, banner_color, banner_icon, banner_label = (
        "#1a0a0a", "#E8000E", "#E8000E", "⚠️", "ATTENTION REQUIRED"
    )
else:
    banner_bg, banner_border, banner_color, banner_icon, banner_label = (
        "#1a1500", "#ffab00", "#ffab00", "◆", "WARNING — REVIEW RECOMMENDED"
    )

offline_suffix = f"&nbsp;·&nbsp; {data['offline_cams']} offline" if data["offline_cams"] > 0 else ""
st.markdown(f"""
    <div style="background:{banner_bg}; border:1px solid {banner_border};
                border-radius:3px; padding:1rem 1.5rem; margin-bottom:1.5rem;
                display:flex; align-items:center; gap:12px;">
        <div style="font-size:1.4rem;">{banner_icon}</div>
        <div>
            <div style="font-family:'Share Tech Mono',monospace; font-size:0.75rem;
                        letter-spacing:3px; color:{banner_color}; text-transform:uppercase;">
                {banner_label}
            </div>
            <div style="font-family:'DM Sans',sans-serif; font-size:0.85rem; color:#666; margin-top:2px;">
                {data['online_cams']} of {data['total_cams']} cameras online
                &nbsp;·&nbsp; {data['recording']} recording {offline_suffix}
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# ── Stat cards ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

def stat_card(col, icon, label, value, color="#f0f0f0", sub=None):
    sub_html = f'<div style="font-family:\'DM Mono\',monospace; font-size:0.7rem; color:#444; margin-top:4px;">{sub}</div>' if sub else ""
    with col:
        st.markdown(f"""
            <div style="background:#111; border:1px solid #2a2a2a; border-top:3px solid {color};
                        border-radius:3px; padding:1.2rem 1rem; text-align:center;">
                <div style="font-size:1.5rem; margin-bottom:6px;">{icon}</div>
                <div style="font-family:'Rajdhani',sans-serif; font-weight:700; font-size:1.8rem;
                            color:{color}; line-height:1;">{value}</div>
                <div style="font-family:'Share Tech Mono',monospace; font-size:0.65rem;
                            letter-spacing:2px; color:#555; text-transform:uppercase; margin-top:4px;">
                    {label}
                </div>
                {sub_html}
            </div>
        """, unsafe_allow_html=True)

stat_card(c1, "📷", "Cameras Online",
          f"{data['online_cams']} / {data['total_cams']}",
          "#00e676" if data["offline_cams"] == 0 else "#E8000E")

stat_card(c2, "🔴", "Recording", str(data["recording"]),
          "#E8000E" if data["recording"] > 0 else "#555")

if storage and storage.get("total_gb", 0) > 0:
    pct   = storage.get("pct_used", 0)
    scol  = "#00e676" if pct < 70 else ("#ffab00" if pct < 85 else "#E8000E")
    stat_card(c3, "💾", "Storage Used", f"{pct}%", scol,
              f"{storage.get('free_gb', 0)} GB free")
else:
    stat_card(c3, "💾", "Storage", "—", "#555")

if server:
    srv_ok = server.get("status") in ("online", "running", "")
    stat_card(c4, "🖥️", "NVR Status",
              "ONLINE" if srv_ok else "OFFLINE",
              "#00e676" if srv_ok else "#E8000E",
              server.get("version", ""))
else:
    stat_card(c4, "🖥️", "NVR Status", "—", "#555")

st.markdown("<br>", unsafe_allow_html=True)

# ── Camera list ────────────────────────────────────────────────────────────────
st.markdown("""
    <div style="font-family:'Rajdhani',sans-serif; font-weight:700; font-size:1.1rem;
                letter-spacing:2px; text-transform:uppercase; color:#f0f0f0;
                border-bottom:1px solid #2a2a2a; padding-bottom:8px; margin-bottom:1rem;">
        Camera Status
    </div>
""", unsafe_allow_html=True)

if not cameras:
    st.markdown("""
        <div style="font-family:'Share Tech Mono',monospace; font-size:0.8rem; color:#444; padding:1rem 0;">
            NO CAMERAS FOUND — Check NVR connection or system ID mapping.
        </div>
    """, unsafe_allow_html=True)
else:
    pairs = [cameras[i:i+2] for i in range(0, len(cameras), 2)]
    for pair in pairs:
        cols = st.columns(2)
        for idx, cam in enumerate(pair):
            online    = cam["status"] == "online"
            cam_color = "#00e676" if online else "#E8000E"
            cam_bg    = "#0a1a0a" if online else "#1a0a0a"
            status_icon = "🟢" if online else "🔴"
            rec_badge = '<span style="background:#4d0005; color:#E8000E; border:1px solid #E8000E44; font-family:\'Share Tech Mono\',monospace; font-size:0.6rem; letter-spacing:1px; padding:1px 6px; border-radius:2px; margin-left:8px;">● REC</span>' if cam["is_recording"] else ""
            model_ip  = " &nbsp;·&nbsp; ".join(filter(None, [cam.get("model", ""), cam.get("ip", "")]))
            motion    = f'<div style="font-family:\'DM Mono\',monospace; font-size:0.68rem; color:#444; margin-top:4px;">Last motion: {cam["last_motion"]}</div>' if cam.get("last_motion") else ""

            with cols[idx]:
                st.markdown(f"""
                    <div style="background:{cam_bg}; border:1px solid #2a2a2a;
                                border-left:3px solid {cam_color}; border-radius:3px;
                                padding:1rem 1.2rem; margin-bottom:10px;">
                        <div style="font-family:'Rajdhani',sans-serif; font-weight:700;
                                    font-size:0.95rem; letter-spacing:1px; color:#f0f0f0;
                                    text-transform:uppercase; margin-bottom:4px;">
                            {status_icon} {cam['name']} {rec_badge}
                        </div>
                        <div style="font-family:'Share Tech Mono',monospace; font-size:0.65rem;
                                    letter-spacing:2px; color:{cam_color}; margin-bottom:4px;">
                            {'ONLINE' if online else 'OFFLINE'}
                        </div>
                        <div style="font-family:'DM Mono',monospace; font-size:0.72rem; color:#444;">
                            {model_ip}
                        </div>
                        {motion}
                    </div>
                """, unsafe_allow_html=True)

# ── Storage detail ─────────────────────────────────────────────────────────────
if storage and storage.get("total_gb", 0) > 0:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
        <div style="font-family:'Rajdhani',sans-serif; font-weight:700; font-size:1.1rem;
                    letter-spacing:2px; text-transform:uppercase; color:#f0f0f0;
                    border-bottom:1px solid #2a2a2a; padding-bottom:8px; margin-bottom:1rem;">
            Storage
        </div>
    """, unsafe_allow_html=True)

    pct       = storage.get("pct_used", 0)
    bar_color = "#00e676" if pct < 70 else ("#ffab00" if pct < 85 else "#E8000E")
    warn_msg  = ""
    if pct >= 85:
        warn_msg = '<div style="font-family:\'DM Mono\',monospace; font-size:0.78rem; color:#E8000E; margin-top:8px;">⚠️ Storage running low — older footage may be overwritten. Contact 5G Security.</div>'
    elif pct >= 70:
        warn_msg = '<div style="font-family:\'DM Mono\',monospace; font-size:0.78rem; color:#ffab00; margin-top:8px;">◆ Storage above 70% — monitoring recommended.</div>'

    st.markdown(f"""
        <div style="background:#111; border:1px solid #2a2a2a; border-radius:3px; padding:1.2rem 1.5rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <div style="font-family:'Share Tech Mono',monospace; font-size:0.75rem; letter-spacing:1px; color:#888;">
                    {storage.get('used_gb', 0)} GB used of {storage.get('total_gb', 0)} GB
                </div>
                <div style="font-family:'Rajdhani',sans-serif; font-weight:700; font-size:1.2rem; color:{bar_color};">
                    {pct}%
                </div>
            </div>
            <div style="background:#1a1a1a; border-radius:2px; height:10px; overflow:hidden;">
                <div style="background:{bar_color}; width:{pct}%; height:100%; border-radius:2px;"></div>
            </div>
            <div style="display:flex; justify-content:space-between; margin-top:8px;">
                <div style="font-family:'DM Mono',monospace; font-size:0.68rem; color:#444;">
                    {storage.get('free_gb', 0)} GB free
                </div>
                <div style="font-family:'DM Mono',monospace; font-size:0.68rem; color:#444;">
                    {'⚠️ DISK ERROR DETECTED' if storage.get('has_error') else '✓ Disk health OK'}
                </div>
            </div>
            {warn_msg}
        </div>
    """, unsafe_allow_html=True)

st.markdown("""
    <div style="margin-top:2rem; font-family:'Share Tech Mono',monospace; font-size:0.65rem;
                color:#333; letter-spacing:1px; text-align:right;">
        LIVE DATA VIA DW SPECTRUM CLOUD  ·  AUTO-REFRESHES ON PAGE LOAD
    </div>
""", unsafe_allow_html=True)
