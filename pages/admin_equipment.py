import streamlit as st
from utils.auth import require_role, logout as _logout
from utils.db import fetchall, execute
from utils.theme import inject_global_css, render_sidebar, page_header
from utils.qr import generate_qr_base64, generate_qr_bytes

inject_global_css()
require_role("admin")

if "user" in st.session_state:
    render_sidebar(st.session_state["user"], _logout)

page_header("Equipment", "5G Security // Equipment Management")

customers = fetchall("SELECT id, company FROM customers ORDER BY company")
if not customers:
    st.info("Add customers first before managing equipment.")
    st.stop()

customer_map = {c["company"]: c["id"] for c in customers}

tab1, tab2 = st.tabs(["Equipment List", "Add Equipment"])

# ── Tab 1: Equipment List ──────────────────────────────────────────────────────
with tab1:
    selected_company = st.selectbox("Filter by Customer", ["All"] + list(customer_map.keys()))

    query  = "SELECT e.*, c.company FROM equipment e JOIN customers c ON c.id=e.customer_id"
    params = ()
    if selected_company != "All":
        query  += " WHERE e.customer_id = %s"
        params  = (customer_map[selected_company],)
    query += " ORDER BY c.company, e.system_type, e.name"

    items = fetchall(query, params)

    if not items:
        st.info("No equipment found.")
    else:
        for item in items:
            with st.expander(f"📦  {item['company']} — {item['name']} ({item['system_type'].replace('_',' ').title()})"):
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    new_name     = st.text_input("Name",     item["name"],           key=f"nm_{item['id']}")
                    new_location = st.text_input("Location", item["location"] or "", key=f"loc_{item['id']}")
                    new_stype    = st.selectbox("System Type",
                                                ["cameras","access_control","alarms","network"],
                                                index=["cameras","access_control","alarms","network"].index(item["system_type"]),
                                                key=f"st_{item['id']}")
                with col2:
                    new_model   = st.text_input("Model",    item["model"] or "",      key=f"mod_{item['id']}")
                    new_serial  = st.text_input("Serial #", item["serial_num"] or "", key=f"ser_{item['id']}")
                    new_install = st.date_input("Install Date",
                                                value=item["install_date"] if item["install_date"] else None,
                                                key=f"ins_{item['id']}")
                with col3:
                    # QR Code
                    st.markdown("""
                        <div style="font-family:'DM Mono',monospace; font-size:0.7rem;
                                    color:#555; letter-spacing:1px; margin-bottom:6px;">
                            QR CODE
                        </div>
                    """, unsafe_allow_html=True)
                    qr_b64 = generate_qr_base64(item["id"])
                    st.markdown(f"""
                        <img src="data:image/png;base64,{qr_b64}"
                             style="width:100%; max-width:140px; border:1px solid #2a2a2a;
                                    border-radius:2px; background:white; padding:4px;">
                    """, unsafe_allow_html=True)
                    qr_bytes = generate_qr_bytes(item["id"])
                    st.download_button(
                        "⬇️ Download",
                        data=qr_bytes,
                        file_name=f"qr_{item['company'].replace(' ','_')}_{item['name'].replace(' ','_')}.png",
                        mime="image/png",
                        key=f"qrdl_{item['id']}",
                        use_container_width=True
                    )

                new_notes = st.text_area("Notes", item["notes"] or "", key=f"nt_{item['id']}")

                col_s, col_d = st.columns([4, 1])
                with col_s:
                    if st.button("💾 Save", key=f"sv_{item['id']}", type="primary"):
                        execute("""
                            UPDATE equipment
                            SET name=%s, location=%s, system_type=%s, model=%s,
                                serial_num=%s, install_date=%s, notes=%s
                            WHERE id=%s
                        """, (new_name, new_location, new_stype, new_model,
                              new_serial, new_install, new_notes, item["id"]))
                        st.success("Saved.")
                        st.rerun()
                with col_d:
                    if st.button("🗑️ Delete", key=f"del_{item['id']}"):
                        execute("DELETE FROM equipment WHERE id=%s", (item["id"],))
                        st.rerun()

# ── Tab 2: Add Equipment ───────────────────────────────────────────────────────
with tab2:
    with st.form("add_equipment"):
        col1, col2 = st.columns(2)
        with col1:
            cust_choice = st.selectbox("Customer *", list(customer_map.keys()))
            eq_name     = st.text_input("Equipment Name *")
            eq_type     = st.selectbox("System Type *", ["cameras","access_control","alarms","network"])
            eq_location = st.text_input("Location / Zone")
        with col2:
            eq_model   = st.text_input("Model")
            eq_serial  = st.text_input("Serial Number")
            eq_install = st.date_input("Install Date", value=None)
            eq_notes   = st.text_area("Notes", height=80)

        if st.form_submit_button("➕ Add Equipment", type="primary"):
            if not eq_name or not cust_choice:
                st.error("Customer and equipment name are required.")
            else:
                execute("""
                    INSERT INTO equipment
                        (customer_id, system_type, name, location, model, serial_num, install_date, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (customer_map[cust_choice], eq_type, eq_name, eq_location,
                      eq_model, eq_serial, eq_install, eq_notes))
                st.success(f"✅ '{eq_name}' added. A QR code is now available in the Equipment List.")
                st.rerun()
