import streamlit as st
import base64
import os


def get_logo_base64():
    logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


def inject_global_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=DM+Mono:wght@400;500&family=Barlow:wght@600;700;800&display=swap');

    /* ── Root Variables ───────────────────────────────── */
    :root {
        --red:        #E8000E;
        --red-dim:    #a0000a;
        --red-glow:   rgba(232, 0, 14, 0.15);
        --black:      #0a0a0a;
        --surface:    #111111;
        --surface2:   #1a1a1a;
        --surface3:   #222222;
        --border:     #2a2a2a;
        --border-red: rgba(232, 0, 14, 0.3);
        --text:       #f0f0f0;
        --text-dim:   #999999;
        --text-muted: #555555;
        --green:      #00e676;
        --yellow:     #ffab00;
        --font-display: 'Barlow', sans-serif;
        --font-mono:    'DM Mono', monospace;
        --font-body:    'DM Sans', sans-serif;
    }

    /* ── Base ─────────────────────────────────────────── */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: var(--black) !important;
        font-family: var(--font-body) !important;
        color: var(--text) !important;
    }

    [data-testid="stApp"] {
        background-color: var(--black) !important;
    }

    /* ── Sidebar ──────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background-color: var(--surface) !important;
        border-right: 1px solid var(--border-red) !important;
        box-shadow: 4px 0 20px rgba(232, 0, 14, 0.05);
    }

    [data-testid="stSidebar"] * {
        font-family: var(--font-body) !important;
    }

    /* ── Sidebar nav links ────────────────────────────── */
    [data-testid="stSidebar"] a {
        color: var(--text-dim) !important;
        text-decoration: none !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.5px;
        transition: color 0.2s;
    }

    [data-testid="stSidebar"] a:hover {
        color: var(--red) !important;
    }

    /* ── Main content area ────────────────────────────── */
    .main .block-container {
        padding: 2rem 2.5rem !important;
        max-width: 1200px !important;
    }

    /* ── Typography ───────────────────────────────────── */
    h1 {
        font-family: var(--font-display) !important;
        font-weight: 700 !important;
        font-size: 2rem !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        color: var(--text) !important;
        border-bottom: 2px solid var(--red) !important;
        padding-bottom: 0.5rem !important;
        margin-bottom: 1.5rem !important;
    }

    h2 {
        font-family: var(--font-display) !important;
        font-weight: 600 !important;
        font-size: 1.3rem !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
        color: var(--text) !important;
    }

    h3 {
        font-family: var(--font-display) !important;
        font-weight: 600 !important;
        letter-spacing: 1px !important;
        color: var(--text-dim) !important;
    }

    /* ── Metrics ──────────────────────────────────────── */
    [data-testid="stMetric"] {
        background: var(--surface2) !important;
        border: 1px solid var(--border) !important;
        border-top: 2px solid var(--red) !important;
        border-radius: 4px !important;
        padding: 1rem 1.2rem !important;
    }

    [data-testid="stMetricLabel"] {
        font-family: var(--font-mono) !important;
        font-size: 0.78rem !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
        color: var(--text-dim) !important;
    }

    [data-testid="stMetricValue"] {
        font-family: var(--font-display) !important;
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: var(--text) !important;
    }

    /* ── Buttons ──────────────────────────────────────── */
    .stButton > button {
        background: transparent !important;
        border: 1px solid var(--border-red) !important;
        color: var(--red) !important;
        font-family: var(--font-display) !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
        border-radius: 2px !important;
        transition: all 0.2s ease !important;
        padding: 0.4rem 1.2rem !important;
    }

    .stButton > button:hover {
        background: var(--red-glow) !important;
        border-color: var(--red) !important;
        color: #fff !important;
        box-shadow: 0 0 12px var(--red-glow) !important;
    }

    .stButton > button[kind="primary"] {
        background: var(--red) !important;
        border-color: var(--red) !important;
        color: #fff !important;
    }

    .stButton > button[kind="primary"]:hover {
        background: #ff1a1a !important;
        box-shadow: 0 0 20px rgba(232, 0, 14, 0.4) !important;
    }

    /* ── Inputs ───────────────────────────────────────── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div,
    .stDateInput > div > div > input {
        background: var(--surface2) !important;
        border: 1px solid var(--border) !important;
        border-radius: 2px !important;
        color: var(--text) !important;
        font-family: var(--font-body) !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--red) !important;
        box-shadow: 0 0 0 1px var(--red) !important;
    }

    /* ── Expanders ────────────────────────────────────── */
    [data-testid="stExpander"] {
        background: var(--surface2) !important;
        border: 1px solid var(--border) !important;
        border-left: 3px solid var(--red) !important;
        border-radius: 2px !important;
        margin-bottom: 0.5rem !important;
    }

    [data-testid="stExpander"]:hover {
        border-color: var(--border-red) !important;
        border-left-color: var(--red) !important;
    }

    /* ── Tabs ─────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        border-bottom: 1px solid var(--border) !important;
        gap: 0 !important;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--text-dim) !important;
        font-family: var(--font-display) !important;
        font-weight: 600 !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        font-size: 0.85rem !important;
        border-bottom: 2px solid transparent !important;
        padding: 0.6rem 1.5rem !important;
    }

    .stTabs [aria-selected="true"] {
        color: var(--red) !important;
        border-bottom: 2px solid var(--red) !important;
        background: transparent !important;
    }

    /* ── Alerts / Info boxes ──────────────────────────── */
    .stAlert {
        border-radius: 2px !important;
        border-left: 3px solid !important;
        font-family: var(--font-body) !important;
    }

    [data-testid="stNotification"] {
        background: var(--surface2) !important;
    }

    /* ── Divider ──────────────────────────────────────── */
    hr {
        border-color: var(--border) !important;
        margin: 1.5rem 0 !important;
    }

    /* ── Selectbox ────────────────────────────────────── */
    [data-testid="stSelectbox"] label,
    [data-testid="stTextInput"] label,
    [data-testid="stTextArea"] label,
    [data-testid="stDateInput"] label,
    [data-testid="stFileUploader"] label {
        font-family: var(--font-mono) !important;
        font-size: 0.8rem !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
        color: var(--text-dim) !important;
    }

    /* ── File uploader ────────────────────────────────── */
    [data-testid="stFileUploader"] {
        background: var(--surface2) !important;
        border: 1px dashed var(--border-red) !important;
        border-radius: 2px !important;
    }

    /* ── Checkbox ─────────────────────────────────────── */
    .stCheckbox label {
        font-family: var(--font-body) !important;
        color: var(--text-dim) !important;
    }

    /* ── Caption / small text ─────────────────────────── */
    .stCaption, caption {
        font-family: var(--font-mono) !important;
        color: var(--text-muted) !important;
        font-size: 0.75rem !important;
    }

    /* ── Sidebar nav buttons ──────────────────────────── */
    [data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        border: none !important;
        border-left: 3px solid transparent !important;
        border-radius: 0 !important;
        color: #888 !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.3px !important;
        text-transform: none !important;
        text-align: left !important;
        padding: 0.45rem 0.75rem !important;
        margin: 1px 0 !important;
        box-shadow: none !important;
        transition: all 0.15s ease !important;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(232, 0, 14, 0.08) !important;
        border-left: 3px solid #E8000E !important;
        color: #f0f0f0 !important;
        box-shadow: none !important;
    }

    /* ── Scrollbar ────────────────────────────────────── */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: var(--black); }
    ::-webkit-scrollbar-thumb { background: var(--red-dim); border-radius: 2px; }

    /* ── Scanline overlay effect ──────────────────────── */
    [data-testid="stAppViewContainer"]::before {
        content: "";
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background: repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(0,0,0,0.03) 2px,
            rgba(0,0,0,0.03) 4px
        );
        pointer-events: none;
        z-index: 9999;
    }

    </style>
    """, unsafe_allow_html=True)


def render_logo(size="normal"):
    logo_b64 = get_logo_base64()
    img_tag = f'<img src="data:image/png;base64,{logo_b64}" style="height:{"48px" if size=="normal" else "36px"}; margin-right:12px;">' if logo_b64 else '<span style="font-size:2rem; margin-right:10px;">🔒</span>'

    if size == "normal":
        st.markdown(f"""
            <div style="display:flex; align-items:center; padding:12px 0 20px 0;">
                {img_tag}
                <div>
                    <div style="font-family:'Barlow',sans-serif; font-size:1.5rem; font-weight:700;
                                letter-spacing:3px; text-transform:uppercase; color:#f0f0f0;
                                line-height:1;">5G Security</div>
                    <div style="font-family:'DM Mono',monospace; font-size:0.65rem;
                                letter-spacing:3px; color:#E8000E; text-transform:uppercase;
                                margin-top:2px;">CUSTOMER PORTAL</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div style="display:flex; align-items:center; padding:8px 0 12px 0;">
                {img_tag}
                <div style="font-family:'Barlow',sans-serif; font-size:1.1rem; font-weight:700;
                            letter-spacing:2px; text-transform:uppercase; color:#f0f0f0;">
                    5G Security
                </div>
            </div>
        """, unsafe_allow_html=True)


def status_pill(status: str) -> str:
    """Return an HTML badge for a ticket/system status."""
    config = {
        "open":        ("#555", "#aaa",     "OPEN"),
        "in_progress": ("#7a4500", "#ffab00", "IN PROGRESS"),
        "resolved":    ("#004d2e", "#00e676", "RESOLVED"),
        "closed":      ("#1a1a1a", "#555",   "CLOSED"),
        "green":       ("#003d1f", "#00e676", "ONLINE"),
        "yellow":      ("#7a4500", "#ffab00", "ATTENTION"),
        "red":         ("#4d0005", "#E8000E", "OFFLINE"),
    }
    bg, color, label = config.get(status, ("#333", "#aaa", status.upper()))
    return (f'<span style="background:{bg}; color:{color}; border:1px solid {color}33; '
            f'font-family:\'Share Tech Mono\',monospace; font-size:0.7rem; letter-spacing:1.5px; '
            f'padding:2px 10px; border-radius:2px;">{label}</span>')


def urgency_pill(urgency: str) -> str:
    config = {
        "emergency": ("#4d0005", "#E8000E", "🔴 EMERGENCY"),
        "high":      ("#4d2200", "#ffab00", "🟠 HIGH"),
        "normal":    ("#001a4d", "#4d9fff", "🔵 NORMAL"),
        "low":       ("#1a1a1a", "#555555", "⚪ LOW"),
    }
    bg, color, label = config.get(urgency, ("#333", "#aaa", urgency.upper()))
    return (f'<span style="background:{bg}; color:{color}; border:1px solid {color}33; '
            f'font-family:\'Share Tech Mono\',monospace; font-size:0.7rem; letter-spacing:1.5px; '
            f'padding:2px 10px; border-radius:2px;">{label}</span>')


def render_sidebar(user: dict, logout_fn):
    """Render the full custom sidebar. Call this on every page."""
    with st.sidebar:
        render_logo()
        st.markdown(f"""
            <div style="background:#1a1a1a; border:1px solid #2a2a2a; border-left:3px solid #E8000E;
                        border-radius:2px; padding:10px 12px; margin-bottom:1rem;">
                <div style="font-family:'DM Mono',monospace; font-size:0.65rem;
                            letter-spacing:2px; color:#555; text-transform:uppercase;">Logged in as</div>
                <div style="font-family:'Barlow',sans-serif; font-weight:600; font-size:1rem;
                            color:#f0f0f0; margin-top:2px;">{user['name']}</div>
                <div style="font-family:'DM Mono',monospace; font-size:0.65rem;
                            color:#E8000E; letter-spacing:1px;">
                    {'ADMINISTRATOR' if user['role'] == 'admin' else 'CLIENT'}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="font-family:\'Share Tech Mono\',monospace; font-size:0.65rem; letter-spacing:2px; color:#444; text-transform:uppercase; padding:4px 0; margin-bottom:8px;">Navigation</div>', unsafe_allow_html=True)

        if user["role"] == "admin":
            nav_items = [
                ("pages/admin_dashboard.py",  "📊", "Dashboard"),
                ("pages/admin_customers.py",  "👥", "Customers"),
                ("pages/admin_equipment.py",  "🎥", "Equipment"),
                ("pages/admin_tickets.py",    "🎫", "Tickets"),
                ("pages/admin_settings.py",  "⚙️", "Settings"),
            ]
        else:
            nav_items = [
                ("pages/customer_dashboard.py", "🏠", "Dashboard"),
                ("pages/customer_equipment.py", "🎥", "My Equipment"),
                ("pages/customer_tickets.py",   "🎫", "My Tickets"),
                ("pages/submit_ticket.py",      "➕", "Submit Ticket"),
            ]

        for page, emoji, label in nav_items:
            if st.button(f"{emoji}  {label}", key=f"nav_{label}", use_container_width=True):
                st.switch_page(page)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div style="font-family:\'Share Tech Mono\',monospace; font-size:0.65rem; letter-spacing:2px; color:#444; text-transform:uppercase; border-top:1px solid #1a1a1a; padding-top:12px; margin-bottom:8px;">Account</div>', unsafe_allow_html=True)
        if st.button("🚪  Log Out", key="nav_logout", use_container_width=True):
            logout_fn()

        st.markdown("""
            <div style="position:fixed; bottom:1rem; font-family:'DM Mono',monospace;
                        font-size:0.6rem; color:#333; letter-spacing:1px;">
                5G SECURITY © 2026 | PORTAL v1.0
            </div>
        """, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = ""):
    st.markdown(f"""
        <div style="margin-bottom:1.5rem;">
            <h1 style="font-family:'Barlow',sans-serif; font-size:2rem; font-weight:700;
                       letter-spacing:3px; text-transform:uppercase; color:#f0f0f0;
                       border-bottom:2px solid #E8000E; padding-bottom:0.5rem; margin-bottom:0.3rem;">
                {title}
            </h1>
            {f'<p style="font-family:\'Share Tech Mono\',monospace; font-size:0.75rem; color:#555; letter-spacing:1px; margin:0;">{subtitle}</p>' if subtitle else ''}
        </div>
    """, unsafe_allow_html=True)