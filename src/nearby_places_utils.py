# ============================================================================
# NEARBY PLACES UTILITIES - Find & Categorize POI Around Location
# ============================================================================
#
# Purpose:
#   Finds and categorizes Points of Interest (POI) around a given location.
#   Uses Overpass API to query OpenStreetMap data.
#
# Categories:
#   - Education: Schools, Universities, Libraries
#   - Food: Restaurants, Cafes, Food Stalls
#   - Attractions: Museums, Parks, Landmarks
#   - Accommodation: Hotels, Hostels, Homestays, Guesthouses
#   - Transport: Petrol pumps, Parking
#   - Amenities: Hospitals, Post Offices, Banks
#
# Features:
#   - Multi-source POI detection
#   - Halal food identification (when available)
#   - Distance calculation
#   - Category classification
#
# ============================================================================

import requests
from math import radians, cos, sin, asin, sqrt
import streamlit as st

# Overpass API endpoint
OVERPASS_API = "https://overpass-api.de/api/interpreter"

# Category definitions with OSM tags
PLACE_CATEGORIES = {
    "🎓 Education": {
        "tags": ["amenity=school", "amenity=university", "amenity=library", "amenity=kindergarten", "amenity=college"],
        "emoji": "🎓"
    },
    "🍽️ Food & Dining": {
        "tags": ["amenity=restaurant", "amenity=cafe", "amenity=fast_food", "amenity=food_court", "amenity=snack_bar"],
        "emoji": "🍽️"
    },
    "🎯 Attractions": {
        "tags": ["tourism=attraction", "tourism=museum", "tourism=artwork", "tourism=theme_park", "leisure=park"],
        "emoji": "🎯"
    },
    "🏨 Accommodation": {
        "tags": ["tourism=hotel", "tourism=hostel", "tourism=guest_house", "tourism=apartment", "tourism=alpine_hut", "tourism=chalet"],
        "emoji": "🏨"
    },
    "⛽ Transport": {
        "tags": ["amenity=fuel", "amenity=charging_station", "amenity=parking"],
        "emoji": "⛽"
    },
    "🏥 Amenities": {
        "tags": ["amenity=hospital", "amenity=pharmacy", "amenity=post_office", "amenity=bank", "amenity=atm"],
        "emoji": "🏥"
    }
}


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    Returns distance in kilometers
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers
    return c * r


def is_halal(tags):
    """Check if a food place is marked as halal"""
    halal_indicators = [
        tags.get("halal") == "yes",
        tags.get("diet:halal") == "yes",
        "halal" in tags.get("cuisine", "").lower(),
        tags.get("religion") == "muslim"
    ]
    return any(halal_indicators)


def query_overpass(lat, lon, radius_km=1.0):
    """
    Query Overpass API for POIs around a location
    
    Args:
        lat: Latitude
        lon: Longitude
        radius_km: Search radius in kilometers (default 1.0)
    Uses a simplified query format
    """
    try:
        # Convert radius_km to bbox_delta (rough approximation: 1km ≈ 0.009 degrees)
        bbox_delta = (radius_km / 111.0)  # More accurate conversion
        
        print(f"[DEBUG] Search radius: {radius_km} km (bbox_delta: {bbox_delta})")
        
        # Simplified Overpass query - just search for amenities, tourism, and leisure
        simple_query = f"""
[out:json];
(
  node["amenity"]({lat-bbox_delta},{lon-bbox_delta},{lat+bbox_delta},{lon+bbox_delta});
  way["amenity"]({lat-bbox_delta},{lon-bbox_delta},{lat+bbox_delta},{lon+bbox_delta});
  node["tourism"]({lat-bbox_delta},{lon-bbox_delta},{lat+bbox_delta},{lon+bbox_delta});
  way["tourism"]({lat-bbox_delta},{lon-bbox_delta},{lat+bbox_delta},{lon+bbox_delta});
  node["leisure"]({lat-bbox_delta},{lon-bbox_delta},{lat+bbox_delta},{lon+bbox_delta});
  way["leisure"]({lat-bbox_delta},{lon-bbox_delta},{lat+bbox_delta},{lon+bbox_delta});
);
out center;
"""
        
        print(f"[DEBUG] Querying Overpass API for location: {lat}, {lon}")
        print(f"[DEBUG] Query bbox: {lat-bbox_delta},{lon-bbox_delta},{lat+bbox_delta},{lon+bbox_delta}")
        
        response = requests.post(OVERPASS_API, data=simple_query, timeout=20)
        
        print(f"[DEBUG] Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"[DEBUG] Response received, parsing elements...")
                
                places = []
                elements = data.get("elements", [])
                print(f"[DEBUG] Found {len(elements)} elements in response")
                
                for element in elements:
                    tags = element.get("tags", {})
                    name = tags.get("name", "")
                    
                    # Skip unnamed places
                    if not name or name == "Unnamed":
                        continue
                    
                    # Get coordinates
                    place_lat = None
                    place_lon = None
                    
                    if "lat" in element and "lon" in element:
                        place_lat = element["lat"]
                        place_lon = element["lon"]
                    elif "center" in element:
                        place_lat = element["center"].get("lat")
                        place_lon = element["center"].get("lon")
                    
                    if not place_lat or not place_lon:
                        continue
                    
                    # Calculate distance
                    distance = haversine(lon, lat, place_lon, place_lat)
                    
                    # Skip if too far (>1.5km)
                    if distance > 1.5:
                        continue
                    
                    # Categorize
                    category = categorize_place(tags)
                    if category:
                        halal_status = None
                        if "Food" in category:
                            halal_status = is_halal(tags)
                        
                        # Extract rating information
                        rating = None
                        try:
                            rating_str = tags.get("rating", None)
                            if rating_str:
                                rating = float(rating_str)
                        except (ValueError, TypeError):
                            rating = None
                        
                        places.append({
                            "name": name,
                            "category": category,
                            "distance": round(distance, 2),
                            "lat": place_lat,
                            "lon": place_lon,
                            "tags": tags,
                            "halal": halal_status,
                            "url": tags.get("website", ""),
                            "phone": tags.get("phone", ""),
                            "rating": rating
                        })
                
                print(f"[DEBUG] Successfully processed {len(places)} places")
                return places
            except Exception as json_err:
                print(f"[ERROR] Failed to parse JSON response: {str(json_err)}")
                print(f"[DEBUG] Response text: {response.text[:500]}")
                return []
        else:
            print(f"[ERROR] Overpass API returned status {response.status_code}")
            print(f"[DEBUG] Response: {response.text[:200]}")
            return []
            
    except requests.exceptions.Timeout:
        print(f"[ERROR] Overpass API request timed out")
        return []
    except Exception as e:
        print(f"[ERROR] Exception querying Overpass API: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def categorize_place(tags):
    """Categorize a place based on OSM tags"""
    amenity = tags.get("amenity", "")
    tourism = tags.get("tourism", "")
    leisure = tags.get("leisure", "")
    
    # Check Education
    if amenity in ["school", "university", "library", "kindergarten", "college"]:
        return "🎓 Education"
    
    # Check Food
    if amenity in ["restaurant", "cafe", "fast_food", "food_court", "snack_bar", "food_stall"]:
        return "🍽️ Food & Dining"
    
    # Check Attractions
    if tourism in ["attraction", "museum", "artwork", "theme_park"] or leisure == "park":
        return "🎯 Attractions"
    
    # Check Accommodation (Hotels, Hostels, Homestays, etc.)
    if tourism in ["hotel", "hostel", "guest_house", "apartment", "alpine_hut", "chalet", "holiday_park"]:
        return "🏨 Accommodation"
    
    # Check Transport
    if amenity in ["fuel", "charging_station", "parking"]:
        return "⛽ Transport"
    
    # Check Amenities
    if amenity in ["hospital", "pharmacy", "post_office", "bank", "atm", "police", "fire_station"]:
        return "🏥 Amenities"
    
    return None


def get_nearby_places(lat, lon, radius_km=1.0):
    """
    Main function to get and categorize nearby places
    Sorts by rating (if available) then by distance
    Limits to top 5 per category
    
    Args:
        lat: Latitude
        lon: Longitude
        radius_km: Search radius in kilometers (default 1.0)
    
    Returns:
        Dictionary organized by category with top 5 places per category
    """
    places = query_overpass(lat, lon, radius_km)
    
    # Organize by category
    organized = {}
    for place in places:
        category = place["category"]
        if category not in organized:
            organized[category] = []
        organized[category].append(place)
    
    # Sort each category by rating (descending) then by distance (ascending)
    # Also limit to top 5 per category
    for category in organized:
        places_list = organized[category]
        
        # Separate places with and without ratings
        with_rating = [p for p in places_list if p.get("rating") is not None]
        without_rating = [p for p in places_list if p.get("rating") is None]
        
        # Sort: with_rating by rating descending, without_rating by distance ascending
        with_rating.sort(key=lambda x: (-x["rating"], x["distance"]))
        without_rating.sort(key=lambda x: x["distance"])
        
        # Combine and limit to top 5
        organized[category] = (with_rating + without_rating)[:5]
    
    return organized


def format_place_info(place):
    """Format place information for display"""
    info = f"📍 **{place['name']}**\n"
    info += f"Distance: {place['distance']} km\n"
    
    if place.get("halal") is not None:
        halal_status = "✅ Halal" if place["halal"] else "❌ Non-Halal"
        info += f"Status: {halal_status}\n"
    
    if place.get("phone"):
        info += f"📞 {place['phone']}\n"
    
    if place.get("url"):
        info += f"🌐 {place['url']}\n"
    
    return info
