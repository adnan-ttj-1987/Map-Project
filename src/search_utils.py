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

def search_address(query):
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
    
    # Try Photon API first (most accurate, open-source, no auth needed)
    result = _photon_geocode(query)
    if result:
        return result
    
    # Try Google Geocoding API if key available
    google_api_key = os.getenv('GOOGLE_GEOCODING_API_KEY')
    if google_api_key:
        try:
            result = _google_geocode(query, google_api_key)
            if result:
                return result
        except Exception as e:
            print(f"Google API error: {e}")
    
    # Fall back to Nominatim (free, no API key needed)
    return _nominatim_geocode(query)

def _photon_geocode(query):
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
        list: [latitude, longitude] or None
    """
    try:
        url = "https://photon.komoot.io/api/"
        params = {
            'q': query,
            'limit': 5,
            'countrycodes': 'my'  # Bias towards Malaysia for better local results
        }
        
        # Add proper headers to avoid 403 Forbidden errors
        headers = {
            'User-Agent': 'T14MapExplorer/1.0 (Streamlit App)'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('features'):
            # Get the best match (first result with highest relevance)
            location = data['features'][0]['geometry']['coordinates']
            # Photon returns [longitude, latitude], we need [latitude, longitude]
            return [location[1], location[0]]
        return None
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print(f"Photon API rate limited or forbidden (403). Falling back to alternative...")
        else:
            print(f"Photon geocode error: {e}")
        return None
    except Exception as e:
        print(f"Photon geocode error: {e}")
        return None

def _google_geocode(query, api_key):
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
        list: [latitude, longitude] or None
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
        
        if data['results']:
            location = data['results'][0]['geometry']['location']
            return [location['lat'], location['lng']]
        return None
        
    except Exception as e:
        print(f"Google geocode error: {e}")
        return None

def _nominatim_geocode(query):
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
        list: [latitude, longitude] or None
    """
    try:
        geolocator = Nominatim(user_agent="t14_map_app_v1")
        
        # First attempt: search as-is
        location = geolocator.geocode(
            query,
            timeout=10,
            addressdetails=True
        )
        
        if location:
            return [location.latitude, location.longitude]
        
        # Second attempt: add Malaysia context for better local results
        if not location:
            location = geolocator.geocode(
                f"{query}, Malaysia",
                timeout=10
            )
            if location:
                return [location.latitude, location.longitude]
        
        return None
        
    except GeocoderTimedOut:
        print("Nominatim timeout - server busy")
        return None
    except Exception as e:
        print(f"Nominatim error: {e}")
        return None


