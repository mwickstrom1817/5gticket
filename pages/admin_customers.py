import streamlit as st
from utils.auth import require_role, create_user, logout as _logout
from utils.db import fetchall, fetchone, execute, execute_returning
from utils.theme import inject_global_css, render_sidebar

inject_global_css()
require_role("admin")

if "user" in st.session_state:
    render_sidebar(st.session_state["user"], _logout)


st.title("👥 Manage Customers")
st.markdown("---")

tab1, tab2 = st.tabs(["Customer List", "Add New Customer"])

# ── Tab 1: List ────────────────────────────────────────────────────────────────
with tab1:
    customers = fetchall("SELECT * FROM customers ORDER BY company")

    if not customers:
        st.info("No customers yet. Use the 'Add New Customer' tab to get started.")
    else:
        for c in customers:
            with st.expander(f"🏢 {c['company']}  —  {c['city'] or ''}, {c['state'] or ''}"):
                col1, col2 = st.columns(2)
                with col1:
                    new_company = st.text_input("Company",  c["company"],  key=f"co_{c['id']}")
                    new_address = st.text_input("Address",  c["address"] or "", key=f"addr_{c['id']}")
                    new_city    = st.text_input("City",     c["city"] or "",    key=f"city_{c['id']}")
                    new_state   = st.text_input("State",    c["state"] or "",   key=f"st_{c['id']}")
                    new_zip     = st.text_input("ZIP",      c["zip"] or "",     key=f"zip_{c['id']}")
                with col2:
                    new_phone   = st.text_input("Phone",    c["phone"] or "",   key=f"ph_{c['id']}")
                    new_email   = st.text_input("Email",    c["email"] or "",   key=f"em_{c['id']}")
                    new_notes   = st.text_area("Notes",     c["notes"] or "",   key=f"nt_{c['id']}", height=100)

                col_save, col_del = st.columns([3, 1])
                with col_save:
                    if st.button("💾 Save Changes", key=f"save_{c['id']}"):
                        execute("""
                            UPDATE customers
                            SET company=%s, address=%s, city=%s, state=%s, zip=%s,
                                phone=%s, email=%s, notes=%s
                            WHERE id=%s
                        """, (new_company, new_address, new_city, new_state, new_zip,
                              new_phone, new_email, new_notes, c["id"]))
                        st.success("Customer updated.")
                        st.rerun()

                st.markdown("**Portal Login Account**")
                user = fetchone(
                    "SELECT * FROM users WHERE customer_id = %s AND role='customer'",
                    (c["id"],)
                )
                if user:
                    st.markdown(f"Login email: `{user['email']}`")
                    new_pw = st.text_input("Reset Password (leave blank to keep)",
                                           type="password", key=f"pw_{c['id']}")
                    if st.button("🔑 Reset Password", key=f"rpw_{c['id']}"):
                        if new_pw:
                            from utils.auth import update_password
                            update_password(user["id"], new_pw)
                            st.success("Password updated.")
                        else:
                            st.warning("Enter a new password first.")
                else:
                    st.info("No portal account yet.")
                    with st.form(key=f"create_login_{c['id']}"):
                        lu_name  = st.text_input("Contact Name")
                        lu_email = st.text_input("Login Email")
                        lu_pw    = st.text_input("Temp Password", type="password")
                        if st.form_submit_button("Create Login"):
                            if lu_name and lu_email and lu_pw:
                                create_user(lu_name, lu_email, lu_pw, "customer", c["id"])
                                st.success(f"Login created for {lu_email}")
                                st.rerun()
                            else:
                                st.error("Fill in all fields.")

                st.markdown("**System Health**")
                system_types = ["cameras", "access_control", "alarms", "network"]
                existing = {s["system_type"]: s for s in fetchall(
                    "SELECT * FROM systems WHERE customer_id = %s", (c["id"],)
                )}
                sys_cols = st.columns(len(system_types))
                for i, stype in enumerate(system_types):
                    with sys_cols[i]:
                        current = existing.get(stype, {}).get("status", "green")
                        new_status = st.selectbox(
                            stype.replace("_", " ").title(),
                            ["green", "yellow", "red"],
                            index=["green", "yellow", "red"].index(current),
                            key=f"sys_{c['id']}_{stype}"
                        )
                        if st.button("Update", key=f"upd_{c['id']}_{stype}"):
                            if stype in existing:
                                execute("""
                                    UPDATE systems SET status=%s, updated_at=NOW()
                                    WHERE customer_id=%s AND system_type=%s
                                """, (new_status, c["id"], stype))
                            else:
                                execute("""
                                    INSERT INTO systems (customer_id, system_type, status)
                                    VALUES (%s, %s, %s)
                                """, (c["id"], stype, new_status))
                            st.success("Updated.")
                            st.rerun()

# ── Tab 2: Add new ─────────────────────────────────────────────────────────────
with tab2:
    with st.form("add_customer"):
        st.subheader("New Customer")
        col1, col2 = st.columns(2)
        with col1:
            company = st.text_input("Company Name *")
            address = st.text_input("Address")
            city    = st.text_input("City")
            state   = st.text_input("State")
            zipcode = st.text_input("ZIP")
        with col2:
            phone  = st.text_input("Phone")
            email  = st.text_input("Company Email")
            notes  = st.text_area("Notes", height=80)

        st.markdown("**Portal Login (optional — can add later)**")
        col3, col4 = st.columns(2)
        with col3:
            contact_name  = st.text_input("Contact Name")
            contact_email = st.text_input("Login Email")
        with col4:
            contact_pw = st.text_input("Temp Password", type="password")

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

                # Insert default system rows
                for stype in ["cameras", "access_control", "alarms", "network"]:
                    execute(
                        "INSERT INTO systems (customer_id, system_type, status) VALUES (%s, %s, 'green')",
                        (new_id, stype)
                    )

                if contact_name and contact_email and contact_pw:
                    create_user(contact_name, contact_email, contact_pw, "customer", new_id)

                st.success(f"✅ Customer '{company}' added successfully!")
                st.rerun()