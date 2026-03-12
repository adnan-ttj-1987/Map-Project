# ============================================================================
# LOCATION UTILITIES - User Location Detection
# ============================================================================
#
# Purpose:
#   Determines user's approximate geographic location using IP-based geolocation.
#   Works without requiring explicit permission or GPS hardware.
#
# Features:
#   - Multiple IP-based geolocation APIs with fallback chain
#   - Primary: ipapi.co - reliable service
#   - Secondary: geoip.json - independent service
#   - Tertiary: ip-api.com - additional fallback
#   - Graceful fallback to default location (Kuala Lumpur)
#   - Timeout protection
#   - Comprehensive error handling and debug logging
#
# Limitations:
#   - Accuracy typically within 10-30 km
#   - Depends on IP geolocation database accuracy
#   - May be blocked by corporate proxies/VPNs
#
# ============================================================================

import requests
import streamlit as st

# Default fallback location: Kuala Lumpur, Malaysia
DEFAULT_LOCATION = [3.1390, 101.6869]


def get_current_location(show_debug=False):
    """
    Fetches user's approximate geographic location based on IP address.
    
    Uses multiple free IP geolocation services in fallback chain:
    1. ipapi.co - Primary service (reliable, no key required)
    2. geoip.json - Secondary service (independent implementation)
    3. ip-api.com - Tertiary service (additional redundancy)
    4. Default location - Final fallback (Kuala Lumpur, Malaysia)
    
    Accuracy: Typically within city level (±10-30 km)
    
    Args:
        show_debug (bool): If True, returns debug info with location and source
        
    Returns:
        list: [latitude, longitude] coordinates
              - If successful: actual user location
              - If failed: default location [3.1390, 101.6869]
              
        dict: If show_debug=True, returns:
              {
                  'coords': [lat, lon],
                  'source': 'service_name',
                  'city': 'city_name',
                  'country': 'country_name',
                  'accuracy': 'approximate'
              }
              
    Example:
        >>> location = get_current_location()
        >>> print(location)
        [3.1390, 101.6869]  # KL coordinates or user's actual location
        
        >>> location_debug = get_current_location(show_debug=True)
        >>> print(location_debug)
        {
            'coords': [3.1234, 101.5678],
            'source': 'ipapi.co',
            'city': 'Kuala Lumpur',
            'country': 'Malaysia',
            'accuracy': 'city level (±10-30 km)'
        }
        
    Note:
        Always returns valid coordinates - never raises exception.
        On any error, returns fallback location [3.1390, 101.6869].
    """
    
    def _try_ipapi_co():
        """Primary service: ipapi.co (Most reliable)"""
        try:
            response = requests.get('https://ipapi.co/json/', timeout=4).json()
            latitude = response.get('latitude')
            longitude = response.get('longitude')
            
            if latitude is not None and longitude is not None:
                return {
                    'coords': [latitude, longitude],
                    'source': 'ipapi.co',
                    'city': response.get('city', 'Unknown'),
                    'country': response.get('country_name', 'Unknown'),
                    'accuracy': 'city level (±10-30 km)'
                }
        except Exception as e:
            print(f"[DEBUG] ipapi.co failed: {str(e)}")
        return None

    def _try_geoip_json():
        """Secondary service: geoip.json (Independent implementation)"""
        try:
            response = requests.get('https://geoip.json.com/me/', timeout=4).json()
            latitude = response.get('latitude')
            longitude = response.get('longitude')
            
            if latitude is not None and longitude is not None:
                return {
                    'coords': [latitude, longitude],
                    'source': 'geoip.json',
                    'city': response.get('city', 'Unknown'),
                    'country': response.get('country', 'Unknown'),
                    'accuracy': 'city level (±10-30 km)'
                }
        except Exception as e:
            print(f"[DEBUG] geoip.json failed: {str(e)}")
        return None

    def _try_ip_api():
        """Tertiary service: ip-api.com (Additional fallback)"""
        try:
            response = requests.get('http://ip-api.com/json/', timeout=4).json()
            
            if response.get('status') == 'success':
                latitude = response.get('lat')
                longitude = response.get('lon')
                
                if latitude is not None and longitude is not None:
                    return {
                        'coords': [latitude, longitude],
                        'source': 'ip-api.com',
                        'city': response.get('city', 'Unknown'),
                        'country': response.get('country', 'Unknown'),
                        'accuracy': 'city level (±10-30 km)'
                    }
        except Exception as e:
            print(f"[DEBUG] ip-api.com failed: {str(e)}")
        return None

    # Try services in order of preference
    result = None
    for service_func in [_try_ipapi_co, _try_geoip_json, _try_ip_api]:
        result = service_func()
        if result:
            print(f"[SUCCESS] Location detected via {result['source']}: {result['coords']} ({result['city']}, {result['country']})")
            break
    
    # If all services failed, use default
    if not result:
        print("[FALLBACK] All location services failed. Using default location (Kuala Lumpur).")
        result = {
            'coords': DEFAULT_LOCATION,
            'source': 'default_fallback',
            'city': 'Kuala Lumpur',
            'country': 'Malaysia',
            'accuracy': 'default'
        }
    
    # Return appropriate format based on show_debug flag
    if show_debug:
        return result
    else:
        return result['coords']
