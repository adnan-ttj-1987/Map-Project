import urllib.parse
import json
import os
import time

import requests

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
WIKIPEDIA_SUMMARY_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
GOOGLE_PLACES_TEXT_SEARCH_API = "https://maps.googleapis.com/maps/api/place/textsearch/json"
GOOGLE_PLACES_PHOTO_API = "https://maps.googleapis.com/maps/api/place/photo"
PHOTO_CACHE_TTL_SECONDS = 7 * 24 * 60 * 60
_PHOTO_CACHE: dict = {}
_PHOTO_CACHE_LOADED = False
_PHOTO_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "pin_photo_cache.json"
)


def _get_google_places_api_key() -> str | None:
    return os.getenv("GOOGLE_PLACES_API_KEY") or os.getenv("GOOGLE_GEOCODING_API_KEY")


def _load_photo_cache() -> None:
    global _PHOTO_CACHE_LOADED, _PHOTO_CACHE
    if _PHOTO_CACHE_LOADED:
        return

    try:
        if os.path.exists(_PHOTO_CACHE_FILE):
            with open(_PHOTO_CACHE_FILE, "r", encoding="utf-8") as cache_file:
                loaded = json.load(cache_file)
                if isinstance(loaded, dict):
                    _PHOTO_CACHE = loaded
    except Exception:
        _PHOTO_CACHE = {}

    _PHOTO_CACHE_LOADED = True


def _save_photo_cache() -> None:
    try:
        os.makedirs(os.path.dirname(_PHOTO_CACHE_FILE), exist_ok=True)
        with open(_PHOTO_CACHE_FILE, "w", encoding="utf-8") as cache_file:
            json.dump(_PHOTO_CACHE, cache_file)
    except Exception:
        pass


def _cache_key(label: str, lat: float, lon: float) -> str:
    return f"{label.strip().lower()}|{round(lat, 5)}|{round(lon, 5)}"


def clear_photo_cache() -> None:
    global _PHOTO_CACHE
    _PHOTO_CACHE = {}
    try:
        if os.path.exists(_PHOTO_CACHE_FILE):
            os.remove(_PHOTO_CACHE_FILE)
    except Exception:
        pass


def get_photo_cache_stats() -> dict:
    _load_photo_cache()
    file_exists = os.path.exists(_PHOTO_CACHE_FILE)
    file_size = os.path.getsize(_PHOTO_CACHE_FILE) if file_exists else 0
    return {
        "persistent_entries": len(_PHOTO_CACHE),
        "file_exists": file_exists,
        "file_size_bytes": file_size,
    }


def _search_titles(query: str, limit: int = 5) -> list[str]:
    try:
        response = requests.get(
            WIKIPEDIA_API,
            params={
                "action": "opensearch",
                "search": query,
                "limit": limit,
                "namespace": 0,
                "format": "json",
            },
            timeout=6,
        )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
            return [str(title) for title in data[1] if title]
    except Exception:
        return []
    return []


def _search_titles_by_geo(lat: float, lon: float, limit: int = 5) -> list[str]:
    try:
        response = requests.get(
            WIKIPEDIA_API,
            params={
                "action": "query",
                "list": "geosearch",
                "gscoord": f"{lat}|{lon}",
                "gsradius": 10000,
                "gslimit": limit,
                "format": "json",
            },
            timeout=6,
        )
        response.raise_for_status()
        data = response.json()
        places = data.get("query", {}).get("geosearch", [])
        return [str(item.get("title")) for item in places if item.get("title")]
    except Exception:
        return []


def _fetch_summary_image(title: str) -> dict | None:
    try:
        encoded_title = urllib.parse.quote(title, safe="")
        response = requests.get(f"{WIKIPEDIA_SUMMARY_API}{encoded_title}", timeout=6)
        response.raise_for_status()
        data = response.json()

        image_url = None
        if data.get("originalimage", {}).get("source"):
            image_url = data["originalimage"]["source"]
        elif data.get("thumbnail", {}).get("source"):
            image_url = data["thumbnail"]["source"]

        if not image_url:
            return None

        return {
            "title": data.get("title", title),
            "image_url": image_url,
            "source": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
            "description": data.get("description", ""),
        }
    except Exception:
        return None


def _google_text_search(query: str, lat: float, lon: float, radius_m: int = 2000) -> list[dict]:
    api_key = _get_google_places_api_key()
    if not api_key:
        return []

    try:
        response = requests.get(
            GOOGLE_PLACES_TEXT_SEARCH_API,
            params={
                "query": query,
                "location": f"{lat},{lon}",
                "radius": radius_m,
                "language": "en",
                "key": api_key,
            },
            timeout=6,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("results", []) if isinstance(payload, dict) else []
    except Exception:
        return []


def _extract_google_photo_entries(results: list[dict], limit: int = 3) -> list[dict]:
    api_key = _get_google_places_api_key()
    if not api_key:
        return []

    photos: list[dict] = []
    seen_urls: set[str] = set()
    for result in results:
        photo_items = result.get("photos") or []
        if not photo_items:
            continue

        photo_ref = photo_items[0].get("photo_reference")
        if not photo_ref:
            continue

        image_url = (
            f"{GOOGLE_PLACES_PHOTO_API}?maxwidth=800"
            f"&photo_reference={urllib.parse.quote(photo_ref, safe='')}"
            f"&key={urllib.parse.quote(api_key, safe='')}"
        )

        if image_url in seen_urls:
            continue
        seen_urls.add(image_url)

        photos.append(
            {
                "title": result.get("name", "Google Place"),
                "image_url": image_url,
                "source": result.get("url", "https://maps.google.com"),
                "description": result.get("formatted_address", ""),
            }
        )

        if len(photos) >= limit:
            break

    return photos


def _fetch_google_place_photos(label: str, lat: float, lon: float, limit: int = 3) -> list[dict]:
    results = _google_text_search(label, lat, lon, radius_m=2000)
    photos = _extract_google_photo_entries(results, limit=limit)
    if photos:
        return photos

    # Retry with local-context query to improve landmark hit rate.
    local_query = f"{label} near {lat:.4f},{lon:.4f}"
    results = _google_text_search(local_query, lat, lon, radius_m=4000)
    return _extract_google_photo_entries(results, limit=limit)


def fetch_place_photos(label: str, lat: float, lon: float, limit: int = 3) -> list[dict]:
    _load_photo_cache()
    key = _cache_key(label, lat, lon)
    now = time.time()

    cached = _PHOTO_CACHE.get(key)
    if (
        isinstance(cached, dict)
        and (now - cached.get("ts", 0) <= PHOTO_CACHE_TTL_SECONDS)
        and isinstance(cached.get("photos"), list)
    ):
        return cached.get("photos", [])[:limit]

    photos: list[dict] = []
    seen_urls: set[str] = set()

    # Preferred provider when API key is configured.
    google_photos = _fetch_google_place_photos(label, lat, lon, limit=limit)
    for photo in google_photos:
        image_url = photo.get("image_url")
        if not image_url or image_url in seen_urls:
            continue
        seen_urls.add(image_url)
        photos.append(photo)
        if len(photos) >= limit:
            _PHOTO_CACHE[key] = {"ts": now, "photos": photos}
            _save_photo_cache()
            return photos

    title_candidates = _search_titles(label, limit=6)
    if not title_candidates:
        title_candidates = _search_titles_by_geo(lat, lon, limit=6)

    for title in title_candidates:
        photo = _fetch_summary_image(title)
        if not photo:
            continue
        image_url = photo.get("image_url")
        if not image_url or image_url in seen_urls:
            continue
        seen_urls.add(image_url)
        photos.append(photo)
        if len(photos) >= limit:
            break

    _PHOTO_CACHE[key] = {"ts": now, "photos": photos}
    _save_photo_cache()

    return photos
