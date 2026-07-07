from typing import Dict, Optional, Tuple

import httpx

from launcher.config import API_BASE, HWID


def api_call(
    method: str,
    path: str,
    body: Optional[Dict] = None,
    auth: Optional[str] = None,
) -> Tuple[int, Optional[Dict]]:
    headers = {"Content-Type": "application/json"}
    if auth:
        headers["Authorization"] = f"Bearer {auth}"
    try:
        if method == "POST":
            r = httpx.post(f"{API_BASE}{path}", json=body, headers=headers, timeout=60)
        elif method == "DELETE":
            r = httpx.delete(f"{API_BASE}{path}", headers=headers, timeout=30)
        else:
            r = httpx.get(f"{API_BASE}{path}", headers=headers, timeout=60)
        data = r.json() if r.text else None
        return r.status_code, data
    except Exception:
        return 0, None


def api_request(
    method: str,
    path: str,
    body: Optional[Dict] = None,
    auth: Optional[str] = None,
) -> Optional[Dict]:
    status, data = api_call(method, path, body, auth)
    if status >= 400 or status == 0:
        return None
    return data


def refresh_session(refresh_token: str) -> Tuple[bool, Optional[Dict]]:
    status, data = api_call("POST", "/launcher/auth/refresh", {"refreshToken": refresh_token, "hwid": HWID})
    if status == 200 and data:
        return True, data
    return False, None
