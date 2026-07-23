from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Optional, Tuple

import httpx

from launcher.config import APP_VERSION, UPDATE_RELEASES_API, UPDATE_REPO_URL

CheckStatus = Literal["update", "current", "no_releases", "error"]


@dataclass
class UpdateInfo:
    tag: str
    version: str
    html_url: str
    download_url: Optional[str]
    body: str


@dataclass
class UpdateCheckResult:
    status: CheckStatus
    info: Optional[UpdateInfo] = None
    message: str = ""


_VERSION_RE = re.compile(r"(\d+(?:\.\d+)*)")


def parse_version(value: str) -> Tuple[int, ...]:
    text = (value or "").strip()
    if text.lower().startswith("v"):
        text = text[1:]
    match = _VERSION_RE.search(text)
    if not match:
        return (0,)
    return tuple(int(part) for part in match.group(1).split("."))


def is_remote_newer(remote: str, local: str = APP_VERSION) -> bool:
    return parse_version(remote) > parse_version(local)


def _pick_windows_asset(assets: list) -> Optional[str]:
    preferred = []
    fallback = []
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        name = str(asset.get("name", "")).lower()
        url = asset.get("browser_download_url")
        if not url:
            continue
        if name.endswith(".exe") or "windows" in name or name.endswith(".zip"):
            preferred.append(str(url))
        else:
            fallback.append(str(url))
    if preferred:
        for url in preferred:
            if url.lower().endswith(".exe"):
                return url
        return preferred[0]
    return fallback[0] if fallback else None


def check_for_update(timeout: float = 15.0) -> UpdateCheckResult:
    """
    Checks GitHub Releases for Damir00109/VLauncher_Windows.
    Publish a release with tag v0.2.0 and attach VLauncher.exe.
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"VLauncher/{APP_VERSION}",
    }
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
            response = client.get(UPDATE_RELEASES_API)
    except httpx.HTTPError as exc:
        return UpdateCheckResult(status="error", message=str(exc))

    if response.status_code == 404:
        return UpdateCheckResult(
            status="no_releases",
            message="В репозитории пока нет релизов",
        )
    if response.status_code >= 400:
        return UpdateCheckResult(
            status="error",
            message=f"GitHub API HTTP {response.status_code}",
        )

    try:
        data = response.json()
    except ValueError:
        return UpdateCheckResult(status="error", message="Некорректный ответ GitHub")
    if not isinstance(data, dict):
        return UpdateCheckResult(status="error", message="Некорректный ответ GitHub")

    tag = str(data.get("tag_name") or "").strip()
    if not tag:
        return UpdateCheckResult(status="no_releases", message="Пустой tag_name")

    if not is_remote_newer(tag, APP_VERSION):
        return UpdateCheckResult(status="current")

    assets = data.get("assets") if isinstance(data.get("assets"), list) else []
    html_url = str(data.get("html_url") or UPDATE_REPO_URL)
    info = UpdateInfo(
        tag=tag,
        version=tag.lstrip("vV"),
        html_url=html_url,
        download_url=_pick_windows_asset(assets),
        body=str(data.get("body") or "").strip(),
    )
    return UpdateCheckResult(status="update", info=info)
