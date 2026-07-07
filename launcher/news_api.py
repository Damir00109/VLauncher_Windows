from typing import Dict, List, Optional

import httpx

from launcher.api import api_request


def normalize_news_api_url(url: str) -> str:
    return url.strip().rstrip("/")


def news_list_url(api_url: str, limit: int = 10) -> str:
    base = normalize_news_api_url(api_url)
    return f"{base}?limit={limit}"


def news_detail_url(api_url: str, slug: str) -> str:
    slug = slug.strip().strip("/")
    return f"{normalize_news_api_url(api_url)}/{slug}"


def get_launcher_news_api_url() -> Optional[str]:
    data = api_request("GET", "/launcher/config")
    if not data:
        return None
    url = str(data.get("newsApiUrl") or "").strip()
    return url or None


def fetch_news_list(api_url: str, limit: int = 10) -> List[Dict]:
    response = httpx.get(news_list_url(api_url, limit), timeout=20.0, follow_redirects=True)
    response.raise_for_status()
    payload = response.json()
    items = payload.get("news", [])
    return items if isinstance(items, list) else []


def fetch_news_article(api_url: str, slug: str) -> Dict:
    response = httpx.get(news_detail_url(api_url, slug), timeout=20.0, follow_redirects=True)
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, dict) else {}
