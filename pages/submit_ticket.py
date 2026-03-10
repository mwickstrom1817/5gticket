import streamlit as st
from utils.db import fetchone, execute_returning
from utils.storage import upload_ticket_photo
from utils.email_notify import send_ticket_notification, send_ticket_confirmation
from utils.theme import inject_global_css, render_sidebar, page_header
from utils.auth import logout as _logout

inject_global_css()

if "user" not in st.session_state:
    st.warning("Please log in.")
    st.stop()

user        = st.session_state["user"]
customer_id = user["customer_id"]
customer    = fetchone("SELECT * FROM customers WHERE id = %s", (customer_id,))

if "user" in st.session_state:
    render_sidebar(st.session_state["user"], _logout)

page_header("Submit Ticket", "Report an Issue")

# ── Check for QR code pre-fill ─────────────────────────────────────────────────
prefill_equipment_id = st.session_state.pop("prefill_equipment_id", None)
prefill_system_type  = None
prefill_title        = ""

if prefill_equipment_id:
    equipment = fetchone(
        "SELECT * FROM equipment WHERE id = %s AND customer_id = %s",
        (prefill_equipment_id, customer_id)
    )
    if equipment:
        prefill_system_type = equipment["system_type"]
        prefill_title       = f"{equipment['name']}"
        st.markdown(f"""
            <div style="background:#0f1a0f; border:1px solid #00e67633;
                        border-left:3px solid #00e676; border-radius:2px;
                        padding:12px 16px; margin-bottom:1.5rem;">
                <div style="font-family:'DM Sans',sans-serif; font-size:0.9rem; color:#00e676;">
                    📷 Pre-filled from QR scan: <strong>{equipment['name']}</strong>
                    — {equipment['system_type'].replace('_',' ').title()}
                    {f"• {equipment['location']}" if equipment.get('location') else ''}
                </div>
            </div>
        """, unsafe_allow_html=True)

system_types = ["cameras", "access_control", "alarms", "network"]
system_index = system_types.index(prefill_system_type) if prefill_system_type else 0

with st.form("ticket_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
        system_type = st.selectbox("Which system is affected? *", system_types,
            index=system_index,
            format_func=lambda x: {
                "cameras":        "📷 Cameras",
                "access_control": "🚪 Access Control",
                "alarms":         "🚨 Alarm System",
                "network":        "🌐 Network / Cabling",
            }.get(x, x))

    with col2:
        urgency = st.selectbox("Urgency *", ["low", "normal", "high", "emergency"],
            index=1,
            format_func=lambda x: {
                "low":       "⚪ Low — Not urgent",
                "normal":    "🔵 Normal — Standard request",
                "high":      "🟠 High — Affecting operations",
                "emergency": "🔴 Emergency — System down / security breach",
            }.get(x, x))

    title = st.text_input(
        "Brief Summary *",
        value=prefill_title,
        placeholder="e.g. Camera 3 offline, front door reader not responding"
    )

    description = st.text_area(
        "Detailed Description *",
        placeholder="Describe what's happening, when it started, what you've already tried...",
        height=150
    )

    photo = st.file_uploader(
        "Attach a Photo (optional)",
        type=["jpg", "jpeg", "png", "webp"],
        help="Upload a photo of the issue if helpful."
    )

    st.markdown("---")

    if urgency == "emergency":
        st.warning("🔴 **Emergency tickets** will trigger an immediate alert to our team. "
                   "For life-safety emergencies, please also call us directly.")

    submitted = st.form_submit_button("📨 Submit Ticket", type="primary", use_container_width=True)

    if submitted:
        if not title or not description:
            st.error("Please fill in the summary and description.")
        else:
            photo_url = None
            if photo:
                with st.spinner("Uploading photo..."):
                    try:
                        photo_url = upload_ticket_photo(photo.read(), photo.type or "image/jpeg", customer_id)
                    except Exception as e:
                        st.warning(f"Photo upload failed: {e}. Ticket will be submitted without photo.")

            row = execute_returning("""
                INSERT INTO tickets
                    (customer_id, system_type, urgency, title, description, photo_url, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'open')
                RETURNING id, created_at
            """, (customer_id, system_type, urgency, title, description, photo_url))

            ticket_data = {
                "id":          row["id"],
                "system_type": system_type,
                "urgency":     urgency,
                "title":       title,
                "description": description,
                "photo_url":   photo_url,
            }
            send_ticket_notification(ticket_data, dict(customer))
            send_ticket_confirmation(ticket_data, dict(customer), user['name'])

            st.success(f"✅ Ticket #{row['id']} submitted! We'll be in touch soon.")
            st.balloons()
