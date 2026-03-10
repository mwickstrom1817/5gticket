import streamlit as st
from utils.auth import require_role, logout as _logout, create_user
from utils.db import fetchall, fetchone, execute, execute_returning
from utils.theme import inject_global_css, render_sidebar, page_header
from utils.email_notify import send_welcome_email

inject_global_css()
require_role("admin")

if "user" in st.session_state:
    render_sidebar(st.session_state["user"], _logout)

page_header("Customers", "5G Security // Customer Management")

tab1, tab2 = st.tabs(["Customer List", "Add New Customer"])

# ── Tab 1: Customer List ───────────────────────────────────────────────────────
with tab1:
    customers = fetchall("SELECT * FROM customers ORDER BY company")

    if not customers:
        st.info("No customers yet. Use the 'Add New Customer' tab to get started.")
    else:
        for c in customers:
            with st.expander(f"🏢  {c['company']}  —  {c['city'] or ''}, {c['state'] or ''}"):
                col1, col2 = st.columns(2)
                with col1:
                    new_company = st.text_input("Company",  c["company"],         key=f"co_{c['id']}")
                    new_address = st.text_input("Address",  c["address"] or "",   key=f"addr_{c['id']}")
                    new_city    = st.text_input("City",     c["city"] or "",      key=f"city_{c['id']}")
                    new_state   = st.text_input("State",    c["state"] or "",     key=f"st_{c['id']}")
                    new_zip     = st.text_input("ZIP",      c["zip"] or "",       key=f"zip_{c['id']}")
                with col2:
                    new_phone   = st.text_input("Phone",    c["phone"] or "",     key=f"ph_{c['id']}")
                    new_email   = st.text_input("Email",    c["email"] or "",     key=f"em_{c['id']}")
                    new_notes   = st.text_area("Notes",     c["notes"] or "",     key=f"nt_{c['id']}", height=100)

                st.markdown("""
                    <div style="font-family:'Share Tech Mono',monospace; font-size:0.68rem;
                                letter-spacing:2px; color:#555; text-transform:uppercase;
                                margin:0.75rem 0 0.4rem 0;">
                        5G Site Agent
                    </div>
                """, unsafe_allow_html=True)
                new_spectrum_id = st.text_input(
                    "DW Spectrum System ID",
                    value=c.get("spectrum_system_id") or "",
                    key=f"spec_{c['id']}",
                    placeholder="e.g. 72890a4e-c7fa-4ed4-8977-c49a41713d3c",
                    help="From DW Spectrum desktop app: System Administration > General > System ID"
                )

                if st.button("💾 Save Changes", key=f"save_{c['id']}", type="primary"):
                    execute("""
                        UPDATE customers
                        SET company=%s, address=%s, city=%s, state=%s, zip=%s,
                            phone=%s, email=%s, notes=%s, spectrum_system_id=%s
                        WHERE id=%s
                    """, (new_company, new_address, new_city, new_state, new_zip,
                          new_phone, new_email, new_notes, new_spectrum_id or None, c["id"]))
                    st.success("Customer updated.")
                    st.rerun()

                st.markdown("---")
                st.markdown("**Portal Login Account**")
                user = fetchone(
                    "SELECT * FROM users WHERE customer_id = %s AND role='customer'",
                    (c["id"],)
                )
                if user:
                    st.markdown(f"Login email: `{user['email']}`")
                    col_pw, col_btn = st.columns([3, 1])
                    with col_pw:
                        new_pw = st.text_input("Reset Password (leave blank to keep)",
                                               type="password", key=f"pw_{c['id']}")
                    with col_btn:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("🔑 Reset", key=f"rpw_{c['id']}"):
                            if new_pw:
                                from utils.auth import update_password
                                update_password(user["id"], new_pw)
                                st.success("Password updated.")
                            else:
                                st.warning("Enter a new password first.")
                else:
                    st.info("No portal account yet.")
                    with st.form(key=f"create_login_{c['id']}"):
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            lu_name  = st.text_input("Contact Name")
                        with col_b:
                            lu_email = st.text_input("Login Email")
                        with col_c:
                            lu_pw = st.text_input("Temp Password", type="password")
                        send_welcome = st.checkbox("Send welcome email to customer", value=True)
                        if st.form_submit_button("Create Login", type="primary"):
                            if lu_name and lu_email and lu_pw:
                                create_user(lu_name, lu_email, lu_pw, "customer", c["id"])
                                if send_welcome:
                                    send_welcome_email(
                                        to_email=lu_email,
                                        contact_name=lu_name,
                                        company=c["company"],
                                        temp_password=lu_pw
                                    )
                                    st.success(f"Login created and welcome email sent to {lu_email}!")
                                else:
                                    st.success(f"Login created for {lu_email}")
                                st.rerun()
                            else:
                                st.error("Fill in all fields.")

                st.markdown("---")
                st.markdown("**System Health**")
                system_types = ["cameras", "access_control", "alarms", "network"]
                existing = {s["system_type"]: s for s in fetchall(
                    "SELECT * FROM systems WHERE customer_id = %s", (c["id"],)
                )}
                sys_cols = st.columns(len(system_types))
                for i, stype in enumerate(system_types):
                    with sys_cols[i]:
                        sys = existing.get(stype, {})
                        current    = sys.get("status", "green")
                        auto       = sys.get("auto_updated", False)
                        last_polled = sys.get("last_polled")

                        label = stype.replace("_", " ").title()
                        if auto and last_polled:
                            polled_str = last_polled.strftime("%b %d %H:%M")
                            st.markdown(f"""
                                <div style="font-family:'DM Mono',monospace; font-size:0.65rem;
                                            color:#00e676; margin-bottom:2px;">
                                    ⚡ AUTO — {polled_str}
                                </div>
                            """, unsafe_allow_html=True)

                        new_status = st.selectbox(
                            label,
                            ["green", "yellow", "red"],
                            index=["green", "yellow", "red"].index(current),
                            key=f"sys_{c['id']}_{stype}"
                        )
                        if st.button("Update", key=f"upd_{c['id']}_{stype}"):
                            if stype in existing:
                                execute("""
                                    UPDATE systems SET status=%s, updated_at=NOW(),
                                    auto_updated=FALSE
                                    WHERE customer_id=%s AND system_type=%s
                                """, (new_status, c["id"], stype))
                            else:
                                execute("""
                                    INSERT INTO systems (customer_id, system_type, status)
                                    VALUES (%s, %s, %s)
                                """, (c["id"], stype, new_status))
                            st.success("Updated.")
                            st.rerun()

# ── Tab 2: Add New Customer ────────────────────────────────────────────────────
with tab2:
    with st.form("add_customer"):
        col1, col2 = st.columns(2)
        with col1:
            company = st.text_input("Company Name *")
            address = st.text_input("Address")
            city    = st.text_input("City")
            state   = st.text_input("State")
            zipcode = st.text_input("ZIP")
        with col2:
            phone = st.text_input("Phone")
            email = st.text_input("Company Email")
            notes = st.text_area("Notes", height=80)

        st.markdown("**Portal Login (optional — can add later)**")
        col3, col4 = st.columns(2)
        with col3:
            contact_name  = st.text_input("Contact Name")
            contact_email = st.text_input("Login Email")
        with col4:
            contact_pw    = st.text_input("Temp Password", type="password")

        send_welcome = st.checkbox("Send welcome email to customer", value=True)

        submitted = st.form_submit_button("➕ Add Customer", type="primary")
        if submitted:
            if not company:
                st.error("Company name is required.")
            else:
                row = execute_returning("""
                    INSERT INTO customers (company, address, city, state, zip, phone, email, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                """, (company, address, city, state, zipcode, phone, email, notes))

                new_id = row["id"]

                for stype in ["cameras", "access_control", "alarms", "network"]:
                    execute(
                        "INSERT INTO systems (customer_id, system_type, status) VALUES (%s, %s, 'green')",
                        (new_id, stype)
                    )

                if contact_name and contact_email and contact_pw:
                    create_user(contact_name, contact_email, contact_pw, "customer", new_id)
                    if send_welcome:
                        send_welcome_email(
                            to_email=contact_email,
                            contact_name=contact_name,
                            company=company,
                            temp_password=contact_pw
                        )
                        st.success(f"✅ '{company}' added and welcome email sent to {contact_email}!")
                    else:
                        st.success(f"✅ Customer '{company}' added successfully!")
                else:
                    st.success(f"✅ Customer '{company}' added! Add a portal login from the Customer List tab.")
                st.rerun()
