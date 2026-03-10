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


# ── DW Spectrum Cloud base URLs ────────────────────────────────────────────────
NX_CLOUD_HOST  = "https://dwspectrum.digital-watchdog.com"
AUTH_URL       = f"{NX_CLOUD_HOST}/cdb/oauth2/token"
SYSTEMS_URL    = f"{NX_CLOUD_HOST}/cdb/system/get"


# ── Auth ───────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3300)
def get_cloud_token() -> str | None:
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

@st.cache_data(ttl=300)
def get_cloud_systems() -> list[dict]:
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


# ── Per-system API — tries multiple relay URL formats ─────────────────────────

def _system_get(system_id: str, path: str) -> dict | list | None:
    """
    Try multiple relay URL formats and auth styles used by NX/DW cloud.
    Returns parsed JSON on success, or error dict with full debug info.
    """
    token = get_cloud_token()
    if not token:
        return {"error": "no_token", "message": "Could not get auth token."}

    attempts = [
        # (base_url, use_query_param_auth)
        (f"{NX_CLOUD_HOST}/proxy/{system_id}", False),
        (f"{NX_CLOUD_HOST}/proxy/{system_id}", True),
        (f"https://{system_id}.relay.vmsproxy.com", False),
        (f"https://{system_id}.relay.nxvms.com", False),
    ]

    last_error = "No attempts made"
    for base, use_query in attempts:
        url     = f"{base}{path}"
        headers = {"X-Runtime-Guid": system_id}
        params  = {}
        if use_query:
            params["auth"] = token
        else:
            headers["Authorization"] = f"Bearer {token}"
        try:
            resp     = requests.get(url, headers=headers, params=params,
                                    timeout=15, allow_redirects=True)
            raw_text = resp.text.strip()
            auth_tag = "query" if use_query else "header"
            if resp.status_code == 200 and raw_text:
                try:
                    return resp.json()
                except Exception:
                    last_error = f"{url} [{auth_tag}] → 200 but non-JSON: {raw_text[:400]}"
                    continue
            last_error = f"{url} [{auth_tag}] → HTTP {resp.status_code} | {raw_text[:400]}"
        except requests.exceptions.Timeout:
            last_error = f"{url} → Timeout"
        except requests.exceptions.ConnectionError as e:
            last_error = f"{url} → ConnectionError: {str(e)[:150]}"
        except Exception as e:
            last_error = f"{url} → {str(e)[:150]}"

    return {"error": "all_failed", "message": last_error}


# ── Camera data ────────────────────────────────────────────────────────────────

def get_cameras(system_id: str) -> tuple[list[dict], str | None]:
    """Returns (cameras_list, error_message_or_None)"""
    raw = _system_get(system_id, "/api/cameras")

    if isinstance(raw, dict) and raw.get("error"):
        return [], raw.get("message", "Unknown error")

    cameras = raw if isinstance(raw, list) else raw.get("data", [])
    if not cameras:
        return [], f"API returned empty cameras list. Raw response: {str(raw)[:300]}"

    result = []
    for cam in cameras:
        status_raw = (cam.get("status") or "").lower()
        if status_raw in ("online", "recording"):
            status = "online"
        elif status_raw in ("offline", "unauthorized", "notdefined"):
            status = "offline"
        else:
            status = "unknown"

        result.append({
            "id":           cam.get("id", ""),
            "name":         cam.get("name") or cam.get("physicalId", "Unknown Camera"),
            "status":       status,
            "status_raw":   status_raw,
            "is_recording": status_raw == "recording",
            "model":        cam.get("model", ""),
            "firmware":     cam.get("firmware", ""),
            "ip":           cam.get("url", "").replace("rtsp://", "").split(":")[0],
            "last_motion":  _parse_ts(cam.get("lastMotionTime")),
            "physical_id":  cam.get("physicalId", ""),
        })

    result.sort(key=lambda c: (0 if c["status"] == "offline" else 1, c["name"]))
    return result, None


# ── Storage data ───────────────────────────────────────────────────────────────

def get_storage_info(system_id: str) -> tuple[dict, str | None]:
    raw = _system_get(system_id, "/api/storages")

    if isinstance(raw, dict) and raw.get("error"):
        return {}, raw.get("message")

    storages    = raw if isinstance(raw, list) else raw.get("data", [])
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

    return {
        "total_gb":     total_gb,
        "used_gb":      used_gb,
        "free_gb":      free_gb,
        "pct_used":     pct_used,
        "has_error":    has_error,
    }, None


# ── Server health ──────────────────────────────────────────────────────────────

def get_server_info(system_id: str) -> tuple[dict, str | None]:
    raw = _system_get(system_id, "/api/servers")

    if isinstance(raw, dict) and raw.get("error"):
        return {}, raw.get("message")

    servers = raw if isinstance(raw, list) else raw.get("data", [])
    if not servers:
        return {}, None

    srv = servers[0]
    return {
        "name":    srv.get("name", "NVR"),
        "version": srv.get("version", ""),
        "status":  (srv.get("status") or "").lower(),
        "os_time": _parse_ts(srv.get("osTime")),
    }, None


# ── Helpers ────────────────────────────────────────────────────────────────────

def _parse_ts(ts) -> str | None:
    if not ts:
        return None
    try:
        dt = datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc)
        return dt.strftime("%b %d, %Y %I:%M %p UTC")
    except Exception:
        return None


def system_summary(system_id: str) -> dict:
    cameras, cam_err  = get_cameras(system_id)
    storage, stor_err = get_storage_info(system_id)
    server,  srv_err  = get_server_info(system_id)

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
        # Error messages for debug
        "cam_err":      cam_err,
        "stor_err":     stor_err,
        "srv_err":      srv_err,
    }
