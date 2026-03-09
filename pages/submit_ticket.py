import streamlit as st
from utils.db import fetchone, execute_returning
from utils.storage import upload_ticket_photo
from utils.email_notify import send_ticket_notification, send_ticket_confirmation

if "user" not in st.session_state:
    st.warning("Please log in.")
    st.stop()

user        = st.session_state["user"]
customer_id = user["customer_id"]
customer    = fetchone("SELECT * FROM customers WHERE id = %s", (customer_id,))

st.title("➕ Submit a Support Ticket")
st.markdown("Describe the issue and we'll get back to you as soon as possible.")
st.markdown("---")

with st.form("ticket_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
        system_type = st.selectbox("Which system is affected? *", [
            "cameras", "access_control", "alarms", "network"
        ], format_func=lambda x: {
            "cameras":        "📷 Cameras",
            "access_control": "🚪 Access Control",
            "alarms":         "🚨 Alarm System",
            "network":        "🌐 Network / Cabling",
        }.get(x, x))

    with col2:
        urgency = st.selectbox("Urgency *", [
            "low", "normal", "high", "emergency"
        ], index=1, format_func=lambda x: {
            "low":       "⚪ Low — Not urgent",
            "normal":    "🔵 Normal — Standard request",
            "high":      "🟠 High — Affecting operations",
            "emergency": "🔴 Emergency — System down / security breach",
        }.get(x, x))

    title = st.text_input("Brief Summary *", placeholder="e.g. Camera 3 offline, front door reader not responding")

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
        st.warning("🔴 **Emergency tickets** will trigger an immediate email alert to our team. "
                   "For life-safety emergencies, please also call us directly.")

    submitted = st.form_submit_button("📨 Submit Ticket", type="primary", use_container_width=True)

    if submitted:
        if not title or not description:
            st.error("Please fill in the summary and description.")
        else:
            photo_url = None

            # Upload photo to R2 if provided
            if photo:
                with st.spinner("Uploading photo..."):
                    try:
                        photo_bytes  = photo.read()
                        content_type = photo.type or "image/jpeg"
                        photo_url    = upload_ticket_photo(photo_bytes, content_type, customer_id)
                    except Exception as e:
                        st.warning(f"Photo upload failed: {e}. Ticket will be submitted without photo.")

            # Save ticket to DB
            row = execute_returning("""
                INSERT INTO tickets
                    (customer_id, system_type, urgency, title, description, photo_url, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'open')
                RETURNING id, created_at
            """, (customer_id, system_type, urgency, title, description, photo_url))

            # Send email notification
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

            st.success(f"✅ Ticket #{row['id']} submitted successfully! We'll be in touch soon.")
            st.balloons()
