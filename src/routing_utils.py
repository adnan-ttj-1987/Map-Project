# ============================================================================
# ROUTING UTILITIES - Route Finding and Visualization
# ============================================================================
#
# Purpose:
#   Provides route finding between two geographic points using
#   OSRM (Open Source Routing Machine) and displays routes on maps.
#
# Features:
#   - Calculates driving routes between coordinates
#   - Provides distance (km) and duration (minutes)
#   - Creates visual route lines on folium maps
#   - Marks start and end points with distinct icons
#   - No API key required (uses public OSRM instance)
#
# Service:
#   OSRM (Open Source Routing Machine)
#   - Free public routing service
#   - Covers worldwide road networks
#   - No authentication needed
#   - Rate limited to reasonable use
#
# Data:
#   Input: [latitude, longitude] coordinate pairs
#   Output: GeoJSON route geometry with distance and duration
#
# ============================================================================

import requests
import folium
from geopy.geocoders import Nominatim

def get_route(start_coords, end_coords):
    """
    Fetches driving route between two geographic coordinates.
    
    Uses OSRM (Open Source Routing Machine) to calculate:
    - Route geometry (path along roads)
    - Total distance (kilometers)
    - Estimated duration (minutes)
    
    Args:
        start_coords (list): [latitude, longitude] of starting point
        end_coords (list): [latitude, longitude] of destination
        
    Returns:
        dict: Route information containing:
            {
              'route': GeoJSON geometry object,
              'distance': float (kilometers),
              'duration': float (minutes),
              'coordinates': list of [lon, lat] coordinate pairs
            }
            Returns None if route cannot be calculated
            
    Example:
        >>> start = [3.1390, 101.6869]  # KL
        >>> end = [2.7258, 101.9424]    # Seremban
        >>> route = get_route(start, end)
        >>> print(f"Distance: {route['distance']} km")
        >>> print(f"Duration: {route['duration']} minutes")
        
    Raises:
        Returns None on error instead of raising exception.
        Check return value for success/failure.
    """
    try:
        # OSRM API endpoint for routing
        # Uses OpenStreetMap data for route calculation
        url = "http://router.project-osrm.org/route/v1/driving/{},{};{},{}".format(
            start_coords[1], start_coords[0],  # start: longitude, latitude
            end_coords[1], end_coords[0]       # end: longitude, latitude
        )
        
        # Request parameters for detailed route information
        params = {
            "overview": "full",              # Return complete route geometry
            "geometries": "geojson"          # Return as GeoJSON format
        }
        
        # Call OSRM API with timeout protection
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Check if route was successfully calculated
        if data.get('routes'):
            route = data['routes'][0]  # Get first (best) route
            
            # Extract and convert distance (meters to kilometers)
            distance_km = round(route['distance'] / 1000, 2)
            
            # Extract and convert duration (seconds to minutes)
            duration_min = round(route['duration'] / 60, 1)
            
            return {
                'route': route['geometry'],           # GeoJSON coordinates
                'distance': distance_km,               # Kilometers
                'duration': duration_min,              # Minutes
                'coordinates': route['geometry']['coordinates']  # For polyline
            }
        else:
            # OSRM returned successful response but no valid routes
            print("No route found between coordinates")
            return None
            
    except Exception as e:
        print(f"Routing error: {str(e)}")
        return None

def add_route_to_map(m, start_coords, end_coords, route_data):
    """
    Adds route visualization to a folium map.
    
    Creates:
    - Green marker at starting point (with play icon)
    - Red marker at destination (with flag icon)
    - Blue polyline showing the actual route path
    - Popup with distance and duration information
    
    Args:
        m (folium.Map): Folium map object to add markers/lines to
        start_coords (list): [latitude, longitude] of route start
        end_coords (list): [latitude, longitude] of route end
        route_data (dict): Route information from get_route()
                          Must contain 'coordinates' and route stats
        
    Returns:
        None (modifies map in place)
        
    Example:
        >>> m = folium.Map(location=[3.1390, 101.6869], zoom_start=10)
        >>> start = [3.1390, 101.6869]
        >>> end = [2.7258, 101.9424]
        >>> route = get_route(start, end)
        >>> add_route_to_map(m, start, end, route)
        # Map now displays complete route with markers
        
    Note:
        Requires route_data to have 'coordinates' and distance/duration fields.
        Silently returns if route_data is None (no route available).
    """
    
    if not route_data:
        return
    
    # Add starting point marker (green with play icon)
    folium.Marker(
        location=start_coords,
        popup="📍 Start Point",           # Popup shown on click
        tooltip="Route start",            # Tooltip on hover
        icon=folium.Icon(color='green', icon='play', prefix='fa')  # Green play icon
    ).add_to(m)
    
    # Add destination marker (red with flag icon)
    folium.Marker(
        location=end_coords,
        popup="🎯 Destination",           # Popup shown on click
        tooltip="Route end",              # Tooltip on hover
        icon=folium.Icon(color='red', icon='flag', prefix='fa')  # Red flag icon
    ).add_to(m)
    
    # Add route line if coordinates available
    if 'coordinates' in route_data:
        # Convert GeoJSON coordinates [lon, lat] to Folium format [lat, lon]
        coords = [[coord[1], coord[0]] for coord in route_data['coordinates']]
        
        # Draw polyline for the route
        folium.PolyLine(
            coords,
            color='blue',                  # Blue line
            weight=3,                      # Line thickness
            opacity=0.8,                   # Semi-transparent for visibility
            popup=f"Distance: {route_data['distance']} km | Duration: {route_data['duration']} min"
        ).add_to(m)
