"""
utils/dw_spectrum.py
Handles authentication and data fetching from the Digital Watchdog Spectrum
cloud API (powered by Network Optix / NX Cloud).

Secrets required in Streamlit secrets:
    DW_CLOUD_EMAIL    = "your@email.com"
    DW_CLOUD_PASSWORD = "yourpassword"
"""

import requests
import streamlit as st
from datetime import datetime, timezone


# ── NX Cloud base URLs ─────────────────────────────────────────────────────────
NX_CLOUD_HOST  = "https://nxvms.com"
AUTH_URL       = f"{NX_CLOUD_HOST}/cdb/oauth2/token"
SYSTEMS_URL    = f"{NX_CLOUD_HOST}/cdb/system/get"


# ── Auth ───────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3300)  # Cache token for ~55 minutes (tokens expire in 1hr)
def get_cloud_token() -> str | None:
    """
    Authenticate to NX Cloud with 5G Security admin credentials.
    Returns a bearer token valid for all systems the account has access to.

    NX Cloud requires a JSON body (not form-encoded) with these exact fields.
    scope must be "{cloud_url} cloudSystemId=*" to get access to all systems.
    """
    try:
        resp = requests.post(AUTH_URL, json={
            "grant_type":    "password",
            "response_type": "token",
            "client_id":     "3rdParty",
            "scope":         f"{NX_CLOUD_HOST} cloudSystemId=*",
            "username":      st.secrets["DW_CLOUD_EMAIL"],
            "password":      st.secrets["DW_CLOUD_PASSWORD"],
        }, timeout=10)
        resp.raise_for_status()
        return resp.json().get("access_token")
    except Exception as e:
        st.error(f"DW Cloud auth failed: {e}")
        return None


# ── System list ────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)  # Cache system list for 5 minutes
def get_cloud_systems() -> list[dict]:
    """
    Return all DW cloud systems the account has access to.
    Each item includes: systemId, name, ownerAccountEmail, stateOfHealth, etc.
    """
    token = get_cloud_token()
    if not token:
        return []
    try:
        resp = requests.get(SYSTEMS_URL, headers={
            "Authorization": f"Bearer {token}"
        }, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else data.get("systems", [])
    except Exception as e:
        st.error(f"Failed to fetch system list: {e}")
        return []


# ── Per-system API calls via relay proxy ───────────────────────────────────────

def _system_get(system_id: str, path: str) -> dict | list | None:
    """
    Make an authenticated GET request to a specific NVR via the NX relay proxy.
    path should start with /api/... e.g. /api/cameras
    """
    token = get_cloud_token()
    if not token:
        return None
    relay_base = f"https://{system_id}.relay.vmsproxy.com"
    try:
        resp = requests.get(f"{relay_base}{path}", headers={
            "Authorization": f"Bearer {token}"
        }, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        return {"error": "timeout", "message": "NVR did not respond in time."}
    except requests.exceptions.ConnectionError:
        return {"error": "offline", "message": "Cannot reach NVR via cloud relay."}
    except Exception as e:
        return {"error": "unknown", "message": str(e)}


# ── Camera data ────────────────────────────────────────────────────────────────

def get_cameras(system_id: str) -> list[dict]:
    """
    Fetch all cameras for a system and return cleaned-up camera dicts.
    """
    raw = _system_get(system_id, "/api/cameras")
    if not raw or isinstance(raw, dict) and raw.get("error"):
        return []

    cameras = raw if isinstance(raw, list) else raw.get("data", [])
    result  = []

    for cam in cameras:
        status_raw = (cam.get("status") or "").lower()

        if status_raw in ("online", "recording"):
            status = "online"
        elif status_raw in ("offline", "unauthorized", "notdefined"):
            status = "offline"
        else:
            status = "unknown"

        result.append({
            "id":              cam.get("id", ""),
            "name":            cam.get("name") or cam.get("physicalId", "Unknown Camera"),
            "status":          status,
            "status_raw":      status_raw,
            "is_recording":    status_raw == "recording",
            "model":           cam.get("model", ""),
            "firmware":        cam.get("firmware", ""),
            "ip":              cam.get("url", "").replace("rtsp://", "").split(":")[0],
            "last_motion":     _parse_ts(cam.get("lastMotionTime")),
            "physical_id":     cam.get("physicalId", ""),
        })

    # Sort: offline first so issues are visible at top
    result.sort(key=lambda c: (0 if c["status"] == "offline" else 1, c["name"]))
    return result


# ── Storage data ───────────────────────────────────────────────────────────────

def get_storage_info(system_id: str) -> dict:
    """
    Fetch storage/server info for an NVR system.
    Returns a dict with total_gb, used_gb, free_gb, retention_days, and disk health.
    """
    raw = _system_get(system_id, "/api/storages")
    if not raw or isinstance(raw, dict) and raw.get("error"):
        return {}

    storages = raw if isinstance(raw, list) else raw.get("data", [])
    total_bytes = 0
    free_bytes  = 0
    has_error   = False

    for s in storages:
        if s.get("isUsedForWriting", True):
            total_bytes += s.get("totalSpace", 0)
            free_bytes  += s.get("freeSpace", 0)
            if s.get("status", "").lower() not in ("online", ""):
                has_error = True

    used_bytes = total_bytes - free_bytes
    total_gb   = round(total_bytes / (1024 ** 3), 1) if total_bytes else 0
    used_gb    = round(used_bytes  / (1024 ** 3), 1) if used_bytes  else 0
    free_gb    = round(free_bytes  / (1024 ** 3), 1) if free_bytes  else 0
    pct_used   = round((used_bytes / total_bytes) * 100) if total_bytes else 0

    # Estimate retention based on usage rate is tricky without time data —
    # use a rough heuristic: assume ~1GB/camera/day at standard quality
    return {
        "total_gb":       total_gb,
        "used_gb":        used_gb,
        "free_gb":        free_gb,
        "pct_used":       pct_used,
        "has_error":      has_error,
        "raw_storages":   storages,
    }


# ── Server health ──────────────────────────────────────────────────────────────

def get_server_info(system_id: str) -> dict:
    """
    Fetch server / media server health info.
    Returns uptime, version, CPU/RAM if available.
    """
    raw = _system_get(system_id, "/api/servers")
    if not raw or isinstance(raw, dict) and raw.get("error"):
        return {}

    servers = raw if isinstance(raw, list) else raw.get("data", [])
    if not servers:
        return {}

    srv = servers[0]  # Primary server
    return {
        "name":           srv.get("name", "NVR"),
        "version":        srv.get("version", ""),
        "status":         (srv.get("status") or "").lower(),
        "os_time":        _parse_ts(srv.get("osTime")),
    }


# ── Helpers ────────────────────────────────────────────────────────────────────

def _parse_ts(ts) -> str | None:
    """Convert a millisecond unix timestamp to a readable string."""
    if not ts:
        return None
    try:
        dt = datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc)
        return dt.strftime("%b %d, %Y %I:%M %p UTC")
    except Exception:
        return None


def system_summary(system_id: str) -> dict:
    """
    Convenience function — fetch cameras + storage + server in one call.
    Returns a combined dict for use in the dashboard.
    """
    cameras = get_cameras(system_id)
    storage = get_storage_info(system_id)
    server  = get_server_info(system_id)

    total_cams   = len(cameras)
    online_cams  = sum(1 for c in cameras if c["status"] == "online")
    offline_cams = sum(1 for c in cameras if c["status"] == "offline")
    recording    = sum(1 for c in cameras if c["is_recording"])

    return {
        "cameras":      cameras,
        "storage":      storage,
        "server":       server,
        "total_cams":   total_cams,
        "online_cams":  online_cams,
        "offline_cams": offline_cams,
        "recording":    recording,
        "overall_ok":   offline_cams == 0 and not storage.get("has_error"),
    }
