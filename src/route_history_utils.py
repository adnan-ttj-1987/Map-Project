# ============================================================================
# ROUTE HISTORY UTILITIES - Route History Management
# ============================================================================
#
# Purpose:
#   Manages persistent storage of calculated routes between locations.
#   Provides CRUD operations for route records including:
#   - Save newly calculated routes
#   - Load route history from storage
#   - Delete individual route entries
#   - Clear all route history
#
# Storage:
#   File-based JSON storage in data/route_history.json
#   Automatically creates data directory if missing
#   Keeps only the 10 most recent routes
#
# Data Structure:
#   [
#     {
#       "start": "Kuala Lumpur",
#       "end": "Seremban",
#       "start_coords": [3.1390, 101.6869],
#       "end_coords": [2.7258, 101.9424],
#       "distance": 68.45,
#       "duration": 65.3
#     },
#     ...
#   ]
#
# ============================================================================

import json
import os
from datetime import datetime

# Configuration: Where to store route history
HISTORY_FILE = "data/route_history.json"

# Maximum number of routes to keep in history
MAX_HISTORY_ITEMS = 10

def save_route(start_name, end_name, start_coords, end_coords, distance, duration):
    """
    Saves a calculated route to persistent storage.
    
    Features:
    - Prevents duplicate routes (same start/end locations)
    - Stores most recent routes first (LIFO)
    - Automatically limits history to MAX_HISTORY_ITEMS (default: 10)
    - Creates data directory if it doesn't exist
    - Includes timestamp for tracking
    
    Args:
        start_name (str): Human-readable name of starting location
        end_name (str): Human-readable name of destination
        start_coords (list): [latitude, longitude] of start
        end_coords (list): [latitude, longitude] of end
        distance (float): Route distance in kilometers
        duration (float): Estimated duration in minutes
        
    Returns:
        None
        
    Example:
        >>> save_route("KL", "Seremban", [3.1390, 101.6869], [2.7258, 101.9424], 68.45, 65.3)
        
    Note:
        Automatically deduplicates routes with identical start/end locations.
        Older routes are removed to maintain history size limit.
    """
    # Load existing route history
    history = load_routes()
    
    # Create new route entry
    new_route = {
        "start": start_name,
        "end": end_name,
        "start_coords": start_coords,
        "end_coords": end_coords,
        "distance": distance,
        "duration": duration,
        "timestamp": datetime.now().isoformat()  # Track when route was calculated
    }
    
    # Check if this route already exists (same start and end)
    # to avoid storing duplicate routes
    route_exists = False
    for route in history:
        if (route["start"] == start_name and 
            route["end"] == end_name and
            route["start_coords"] == start_coords and
            route["end_coords"] == end_coords):
            route_exists = True
            break
    
    # Only add if it's a new unique route
    if not route_exists:
        history.insert(0, new_route)
    
    # Keep only the most recent routes (trim older ones)
    history = history[:MAX_HISTORY_ITEMS]
    
    # Ensure data directory exists, create if missing
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    
    # Write updated history to file
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def load_routes():
    """
    Loads route history from persistent JSON file.
    
    Returns:
        list: Array of route entries, each with location names and coordinates
              Empty list if file doesn't exist or is empty
              
    Example:
        >>> routes = load_routes()
        >>> for route in routes:
        ...     print(f"{route['start']} → {route['end']}: {route['distance']} km")
        
    Note:
        Gracefully returns empty list if file doesn't exist yet.
        This is expected on first run of application.
    """
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # If file is corrupted or can't be read, return empty history
            return []
    return []

def delete_route(index):
    """
    Deletes a specific route entry from history by its index position.
    
    Args:
        index (int): Position of route to delete (0-based indexing)
                     Index 0 is most recent route
        
    Returns:
        bool: True if deletion succeeded, False if index out of range
        
    Example:
        >>> delete_route(0)  # Delete most recent route
        True
        >>> delete_route(100)  # Invalid index
        False
        
    Note:
        Route indices are 0-based and ordered by recency (newest first).
    """
    history = load_routes()
    
    # Validate index is within valid range
    if 0 <= index < len(history):
        # Remove route at specified index
        history.pop(index)
        
        # Save updated history back to file
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
        return True
    
    return False

def clear_all_routes():
    """
    Completely removes all route history.
    
    This operation:
    - Deletes the route history JSON file
    - Is permanent and cannot be undone
    - Will leave an empty history on next route calculation
    
    Returns:
        bool: True if successful, False if error occurs
        
    Example:
        >>> clear_all_routes()
        True
        >>> load_routes()
        []  # Returns empty list after clearing
        
    Warning:
        This operation is permanent! All stored route history is deleted.
    """
    try:
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        return True
    except Exception as e:
        print(f"Error clearing route history: {e}")
        return False
