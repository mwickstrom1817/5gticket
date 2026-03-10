import psycopg2
import psycopg2.extras
import streamlit as st


def get_conn():
    """Return a connection to Neon PostgreSQL."""
    return psycopg2.connect(
        st.secrets["NEON_DATABASE_URL"],
        cursor_factory=psycopg2.extras.RealDictCursor
    )


def init_db():
    """Create tables if they don't exist."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          SERIAL PRIMARY KEY,
            name        TEXT NOT NULL,
            email       TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,          -- bcrypt hash
            role        TEXT NOT NULL DEFAULT 'customer',  -- 'admin' | 'customer'
            customer_id INTEGER,                -- FK → customers.id (null for admin)
            created_at  TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id          SERIAL PRIMARY KEY,
            company     TEXT NOT NULL,
            address     TEXT,
            city        TEXT,
            state       TEXT,
            zip         TEXT,
            phone       TEXT,
            email       TEXT,
            notes       TEXT,
            spectrum_system_id TEXT,
            created_at  TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS systems (
            id          SERIAL PRIMARY KEY,
            customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
            system_type TEXT NOT NULL,   -- 'cameras' | 'access_control' | 'alarms' | 'network'
            status      TEXT NOT NULL DEFAULT 'green',  -- 'green' | 'yellow' | 'red'
            notes       TEXT,
            updated_at  TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS equipment (
            id          SERIAL PRIMARY KEY,
            customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
            system_type TEXT NOT NULL,
            name        TEXT NOT NULL,
            location    TEXT,
            model       TEXT,
            serial_num  TEXT,
            install_date DATE,
            notes       TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id           SERIAL PRIMARY KEY,
            customer_id  INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
            system_type  TEXT NOT NULL,
            urgency      TEXT NOT NULL DEFAULT 'normal',  -- 'low' | 'normal' | 'high' | 'emergency'
            title        TEXT NOT NULL,
            description  TEXT,
            photo_url    TEXT,         -- R2 object URL
            status       TEXT NOT NULL DEFAULT 'open',   -- 'open' | 'in_progress' | 'resolved' | 'closed'
            admin_notes  TEXT,
            created_at   TIMESTAMPTZ DEFAULT NOW(),
            updated_at   TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    conn.commit()
    cur.close()
    conn.close()


# ── Generic helpers ────────────────────────────────────────────────────────────

def fetchall(query, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params or ())
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def fetchone(query, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params or ())
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def execute(query, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params or ())
    conn.commit()
    cur.close()
    conn.close()


def execute_returning(query, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params or ())
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return row
