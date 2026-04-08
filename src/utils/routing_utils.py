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


def get_multi_waypoint_route(waypoints_coords):
    """
    Fetches driving route through multiple waypoints (multi-stop routing).
    
    Uses OSRM (Open Source Routing Machine) to calculate:
    - Complete route geometry visiting all waypoints in order
    - Total distance (kilometers)
    - Estimated duration (minutes)
    - Individual leg information
    
    Args:
        waypoints_coords (list): List of [latitude, longitude] coordinate pairs.
                                Must have at least 2 waypoints (start and end).
        
    Returns:
        dict: Route information containing:
            {
              'distance': float (kilometers),
              'duration': float (minutes),
              'coordinates': list of [lon, lat] coordinate pairs,
              'waypoint_names': list of waypoint indices,
              'legs': list of leg dicts with distance/duration for each segment
            }
            Returns None if route cannot be calculated
            
    Example:
        >>> waypoints = [
        ...     [3.1390, 101.6869],  # KL
        ...     [3.0573, 101.5243],  # Petaling Jaya
        ...     [2.7258, 101.9424]   # Seremban
        ... ]
        >>> route = get_multi_waypoint_route(waypoints)
        >>> print(f"Total Distance: {route['distance']} km")
        >>> print(f"Total Duration: {route['duration']} minutes")
        >>> for i, leg in enumerate(route['legs'], 1):
        ...     print(f"Leg {i}: {leg['distance']} km, {leg['duration']} min")
    """
    
    if not waypoints_coords or len(waypoints_coords) < 2:
        print("At least 2 waypoints required for multi-route")
        return None
    
    try:
        # Build OSRM URL with semicolon-separated waypoints
        # Format: lon1,lat1;lon2,lat2;lon3,lat3
        waypoint_str = ";".join(
            f"{coord[1]},{coord[0]}" for coord in waypoints_coords
        )
        
        url = f"http://router.project-osrm.org/route/v1/driving/{waypoint_str}"
        
        # Request parameters
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
            
            # Process legs (segments between waypoints)
            legs = []
            if 'legs' in route:
                for leg in route['legs']:
                    legs.append({
                        'distance': round(leg['distance'] / 1000, 2),
                        'duration': round(leg['duration'] / 60, 1)
                    })
            
            return {
                'distance': distance_km,
                'duration': duration_min,
                'coordinates': route['geometry']['coordinates'],
                'waypoint_names': list(range(len(waypoints_coords))),
                'legs': legs,
                'num_waypoints': len(waypoints_coords)
            }
        else:
            # OSRM returned successful response but no valid routes
            print("No multi-waypoint route found")
            return None
            
    except Exception as e:
        print(f"Multi-waypoint routing error: {str(e)}")
        return None


def add_multi_waypoint_route_to_map(m, waypoints_coords, route_data, waypoint_labels=None):
    """
    Adds multi-waypoint route visualization to a folium map.
    
    Creates:
    - Green marker at starting point (with play icon)
    - Orange numbered markers at intermediate waypoints
    - Red marker at final destination (with flag icon)
    - Purple polyline showing the complete route path
    - Popup with total distance and duration information
    
    Args:
        m (folium.Map): Folium map object to add markers/lines to
        waypoints_coords (list): List of [latitude, longitude] coordinate pairs
        route_data (dict): Route information from get_multi_waypoint_route()
                          Must contain 'coordinates' and route stats
        
    Returns:
        None (modifies map in place)
        
    Example:
        >>> m = folium.Map(location=[3.1390, 101.6869], zoom_start=10)
        >>> waypoints = [[3.1390, 101.6869], [3.0573, 101.5243], [2.7258, 101.9424]]
        >>> route = get_multi_waypoint_route(waypoints)
        >>> add_multi_waypoint_route_to_map(m, waypoints, route)
        # Map now displays multi-waypoint route with numbered stops
        
    Note:
        Requires route_data to have 'coordinates' and route stats.
        Silently returns if route_data is None (no route available).
    """
    
    if not route_data or not waypoints_coords:
        return

    if waypoint_labels is None:
        waypoint_labels = [f"Pin {idx + 1}" for idx in range(len(waypoints_coords))]
    
    # Add starting point marker (green with play icon)
    folium.Marker(
        location=waypoints_coords[0],
        popup=f"🟢 Start: {waypoint_labels[0]}",
        tooltip="Route start",
        icon=folium.Icon(color='green', icon='play', prefix='fa')
    ).add_to(m)
    
    # Add intermediate waypoints (orange with numbers)
    for idx in range(1, len(waypoints_coords) - 1):
        leg_info = ""
        if idx - 1 < len(route_data.get('legs', [])):
            leg = route_data['legs'][idx - 1]
            leg_info = f"\nLeg {idx}: {leg['distance']} km, {leg['duration']} min"
        
        stop_label = waypoint_labels[idx] if idx < len(waypoint_labels) else f"Pin {idx + 1}"
        folium.Marker(
            location=waypoints_coords[idx],
            popup=f"🟠 Stop {idx}: {stop_label}{leg_info}",
            tooltip=f"Stop {idx}: {stop_label}",
            icon=folium.Icon(color='orange', icon=str(idx), prefix='fa', prefix_alt='glyphicon')
        ).add_to(m)
    
    # Add final destination marker (red with flag icon)
    if len(waypoints_coords) > 1:
        final_leg_idx = len(route_data.get('legs', [])) - 1
        leg_info = ""
        if final_leg_idx >= 0 and final_leg_idx < len(route_data.get('legs', [])):
            leg = route_data['legs'][final_leg_idx]
            leg_info = f"\nLeg {len(waypoints_coords) - 1}: {leg['distance']} km, {leg['duration']} min"
        
        folium.Marker(
            location=waypoints_coords[-1],
            popup=f"🔴 Destination: {waypoint_labels[-1]}{leg_info}",
            tooltip="Route end",
            icon=folium.Icon(color='red', icon='flag', prefix='fa')
        ).add_to(m)
    
    # Add route line if coordinates available
    if 'coordinates' in route_data:
        # Convert GeoJSON coordinates [lon, lat] to Folium format [lat, lon]
        coords = [[coord[1], coord[0]] for coord in route_data['coordinates']]
        
        # Draw polyline for the multi-waypoint route
        folium.PolyLine(
            coords,
            color='purple',                # Purple line for multi-route
            weight=4,                      # Thicker line
            opacity=0.8,                   # Semi-transparent for visibility
            popup=f"Distance: {route_data['distance']} km | Duration: {route_data['duration']} min | {route_data['num_waypoints']} stops"
        ).add_to(m)
