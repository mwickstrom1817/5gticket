import streamlit as st
from utils.db import fetchall, fetchone

if "user" not in st.session_state:
    st.warning("Please log in.")
    st.stop()

user = st.session_state["user"]
customer_id = user["customer_id"]

st.title("🎥 My Equipment")
st.markdown("---")

system_icons = {
    "cameras":        "📷 Cameras",
    "access_control": "🚪 Access Control",
    "alarms":         "🚨 Alarm Systems",
    "network":        "🌐 Network & Cabling",
}

for stype, label in system_icons.items():
    items = fetchall("""
        SELECT * FROM equipment
        WHERE customer_id = %s AND system_type = %s
        ORDER BY location, name
    """, (customer_id, stype))

    if items:
        st.subheader(label)
        for item in items:
            with st.expander(f"📦 {item['name']}  —  {item['location'] or 'Location not specified'}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Location:** {item['location'] or '—'}")
                    st.markdown(f"**Model:** {item['model'] or '—'}")
                    st.markdown(f"**Serial #:** {item['serial_num'] or '—'}")
                with col2:
                    install = item["install_date"].strftime("%B %d, %Y") if item.get("install_date") else "—"
                    st.markdown(f"**Installed:** {install}")
                    if item.get("notes"):
                        st.markdown(f"**Notes:** {item['notes']}")
        st.markdown("---")

if not any(
    fetchall("SELECT 1 FROM equipment WHERE customer_id=%s AND system_type=%s", (customer_id, s))
    for s in system_icons
):
    st.info("Your equipment list is being set up. Check back soon or contact 5G Security.")
