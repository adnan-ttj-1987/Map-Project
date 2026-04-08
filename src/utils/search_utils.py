# ============================================================================
# SEARCH UTILITIES - Geocoding Module
# ============================================================================
#
# Purpose:
#   Provides location search functionality using multiple geocoding providers
#   with automatic fallback for reliability and accuracy.
#
# Geocoding Priority:
#   1. Photon API (open-source, fast, good for OSM data)
#   2. Google Geocoding API (if API key provided, very accurate)
#   3. Nominatim (free fallback, OSM-based)
#
# Features:
#   - Multi-provider fallback chain
#   - Rate limit handling
#   - Error logging and recovery
#   - Country bias (Malaysia) for local accuracy
#   - Timeout protection
#
# ============================================================================

import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import os
import re
from math import radians, cos, sin, asin, sqrt

def search_address(query, near_coords=None, use_malaysia_bias=True):
    """
    Search for an address and return coordinates.
    Uses a fallback chain to ensure high success rate:
    Photon → Google API (if available) → Nominatim
    
    Args:
        query (str): Address or place name to search
        
    Returns:
        list: [latitude, longitude] if found, None otherwise
        
    Example:
        >>> coords = search_address("Kuala Lumpur")
        >>> print(coords)
        [3.1390, 101.6869]
    """
    
    candidates = search_address_candidates(
        query,
        near_coords=near_coords,
        use_malaysia_bias=use_malaysia_bias,
        max_results=5,
    )
    if not candidates:
        return None
    return [candidates[0]["lat"], candidates[0]["lon"]]


def search_address_candidates(query, near_coords=None, use_malaysia_bias=True, max_results=5):
    """Return ranked candidate matches for a search query.

    Each candidate contains:
    - lat
    - lon
    - label
    - provider
    """
    candidates = []

    # 1) Photon first
    candidates.extend(_photon_geocode_candidates(query, max_results=max_results, use_malaysia_bias=use_malaysia_bias))

    # 2) Google if configured
    google_api_key = os.getenv("GOOGLE_GEOCODING_API_KEY")
    if google_api_key:
        candidates.extend(_google_geocode_candidates(query, google_api_key, max_results=max_results))

    # 3) Nominatim fallback
    candidates.extend(_nominatim_geocode_candidates(query, max_results=max_results, use_malaysia_bias=use_malaysia_bias))

    deduped = _dedupe_candidates(candidates)

    # 4) If nothing found, fallback to nearby Overpass name matching around reference point
    if not deduped and near_coords:
        deduped = _overpass_name_search_nearby(query, near_coords[0], near_coords[1], max_results=max_results)

    return deduped[:max_results]

def _photon_geocode_candidates(query, max_results=5, use_malaysia_bias=True):
    """
    Search using Photon API (open-source geocoder based on OpenStreetMap).
    
    Advantages:
    - Very fast responses
    - Good local place names
    - No rate limiting for reasonable use
    - Open source and privacy-friendly
    
    Args:
        query (str): Location search term
        
    Returns:
        list[dict]: candidate matches
    """
    try:
        url = "https://photon.komoot.io/api/"
        params = {
            'q': query,
            'limit': max_results,
        }
        if use_malaysia_bias:
            params['countrycodes'] = 'my'
        
        # Add proper headers to avoid 403 Forbidden errors
        headers = {
            'User-Agent': 'T14MapExplorer/1.0 (Streamlit App)'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        
        results = []
        for feature in data.get('features', []):
            try:
                location = feature['geometry']['coordinates']
                props = feature.get('properties', {})
                name = props.get('name') or query
                city = props.get('city') or props.get('state') or ""
                country = props.get('country') or ""
                parts = [name]
                if city:
                    parts.append(city)
                if country:
                    parts.append(country)
                results.append({
                    "lat": location[1],
                    "lon": location[0],
                    "label": ", ".join(parts),
                    "provider": "Photon",
                })
            except Exception:
                continue
        return results
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print(f"Photon API rate limited or forbidden (403). Falling back to alternative...")
        else:
            print(f"Photon geocode error: {e}")
        return []
    except Exception as e:
        print(f"Photon geocode error: {e}")
        return []

def _google_geocode_candidates(query, api_key, max_results=5):
    """
    Search using Google Geocoding API.
    
    Advantages:
    - Highest accuracy
    - Best for address validation
    - Comprehensive global coverage
    
    Requires:
    - Google Cloud API key with Geocoding API enabled
    - Set via GOOGLE_GEOCODING_API_KEY environment variable
    
    Args:
        query (str): Location search term
        api_key (str): Google API key
        
    Returns:
        list[dict]: candidate matches
    """
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': query,
            'key': api_key
        }
        
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        
        results = []
        for item in data.get('results', [])[:max_results]:
            try:
                location = item['geometry']['location']
                results.append({
                    "lat": location['lat'],
                    "lon": location['lng'],
                    "label": item.get('formatted_address', query),
                    "provider": "Google",
                })
            except Exception:
                continue
        return results
        
    except Exception as e:
        print(f"Google geocode error: {e}")
        return []

def _nominatim_geocode_candidates(query, max_results=5, use_malaysia_bias=True):
    """
    Search using Nominatim (OpenStreetMap geocoder).
    
    Advantages:
    - Completely free (no API key needed)
    - Open source
    - Works for most locations
    
    Considerations:
    - Slower than other providers
    - Rate limited to 1 request per second
    - Fallback chain adds Malaysia context for better accuracy
    
    Args:
        query (str): Location search term
        
    Returns:
        list[dict]: candidate matches
    """
    try:
        geolocator = Nominatim(user_agent="t14_map_app_v1")

        locations = geolocator.geocode(
            query,
            timeout=10,
            addressdetails=True,
            exactly_one=False,
            limit=max_results,
        )

        results = _normalize_nominatim_results(locations)

        if not results and use_malaysia_bias:
            locations = geolocator.geocode(
                f"{query}, Malaysia",
                timeout=10,
                exactly_one=False,
                limit=max_results,
            )
            results = _normalize_nominatim_results(locations)

        return results
        
    except GeocoderTimedOut:
        print("Nominatim timeout - server busy")
        return []
    except Exception as e:
        print(f"Nominatim error: {e}")
        return []


def _normalize_nominatim_results(locations):
    if not locations:
        return []
    if not isinstance(locations, list):
        locations = [locations]

    normalized = []
    for location in locations:
        try:
            normalized.append({
                "lat": float(location.latitude),
                "lon": float(location.longitude),
                "label": location.address,
                "provider": "Nominatim",
            })
        except Exception:
            continue
    return normalized


def _dedupe_candidates(candidates):
    deduped = []
    seen = set()
    for item in candidates:
        key = (round(item["lat"], 5), round(item["lon"], 5), item.get("label", "").lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _haversine_km(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371
    return c * r


def _overpass_name_search_nearby(query, lat, lon, max_results=5):
    """Fallback lookup by name around map center using Overpass."""
    try:
        escaped = re.escape(query)
        overpass_query = f"""
[out:json][timeout:20];
(
  node(around:3000,{lat},{lon})["name"~"{escaped}",i];
  way(around:3000,{lat},{lon})["name"~"{escaped}",i];
  relation(around:3000,{lat},{lon})["name"~"{escaped}",i];
);
out center;
"""
        response = requests.post("https://overpass-api.de/api/interpreter", data=overpass_query, timeout=20)
        response.raise_for_status()

        items = []
        for element in response.json().get("elements", []):
            tags = element.get("tags", {})
            name = tags.get("name")
            if not name:
                continue

            el_lat = element.get("lat")
            el_lon = element.get("lon")
            if el_lat is None or el_lon is None:
                center = element.get("center", {})
                el_lat = center.get("lat")
                el_lon = center.get("lon")
            if el_lat is None or el_lon is None:
                continue

            distance = _haversine_km(lat, lon, el_lat, el_lon)
            items.append({
                "lat": el_lat,
                "lon": el_lon,
                "label": f"{name} (nearby name match)",
                "provider": "Overpass-nearby",
                "distance": distance,
            })

        items.sort(key=lambda x: x.get("distance", 9999))
        return items[:max_results]
    except Exception as e:
        print(f"Overpass nearby name fallback error: {e}")
        return []


