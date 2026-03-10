"""
utils/dw_spectrum.py
Reads camera health, storage, and NVR data from the database.
Data is written by the 5G Agent running on each customer's NVR machine.
"""

from utils.db import fetchall, fetchone


def get_camera_health(customer_id: int) -> list[dict]:
    return fetchall("""
        SELECT * FROM camera_health
        WHERE customer_id = %s
        ORDER BY status ASC, name ASC
    """, (customer_id,))


def get_storage_health(customer_id: int) -> dict:
    row = fetchone("SELECT * FROM storage_health WHERE customer_id = %s", (customer_id,))
    return dict(row) if row else {}


def get_nvr_info(customer_id: int) -> dict:
    row = fetchone("SELECT * FROM nvr_info WHERE customer_id = %s", (customer_id,))
    return dict(row) if row else {}


def get_last_polled(customer_id: int):
    row = fetchone("""
        SELECT MAX(last_polled) as last_polled FROM systems
        WHERE customer_id = %s AND auto_updated = TRUE
    """, (customer_id,))
    return row["last_polled"] if row else None


def system_summary(customer_id: int) -> dict:
    cameras   = get_camera_health(customer_id)
    storage   = get_storage_health(customer_id)
    server    = get_nvr_info(customer_id)
    last_poll = get_last_polled(customer_id)

    cameras = [dict(c) for c in cameras]

    total_cams   = len(cameras)
    online_cams  = sum(1 for c in cameras if c["status"] == "online")
    offline_cams = sum(1 for c in cameras if c["status"] == "offline")
    recording    = sum(1 for c in cameras if c.get("is_recording"))

    return {
        "cameras":      cameras,
        "storage":      storage,
        "server":       server,
        "last_polled":  last_poll,
        "total_cams":   total_cams,
        "online_cams":  online_cams,
        "offline_cams": offline_cams,
        "recording":    recording,
        "has_data":     total_cams > 0 or bool(storage),
    }
