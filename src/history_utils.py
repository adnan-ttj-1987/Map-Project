# ============================================================================
# HISTORY UTILITIES - Search History Management
# ============================================================================
#
# Purpose:
#   Manages persistent storage of user search history.
#   Provides CRUD operations for search records including:
#   - Save new searches
#   - Load history from storage
#   - Delete individual items
#   - Clear all history
#
# Storage:
#   File-based JSON storage in data/search_history.json
#   Automatically creates data directory if missing
#   Keeps only the 10 most recent searches
#
# Data Structure:
#   [
#     {
#       "query": "Kuala Lumpur",
#       "coords": [3.1390, 101.6869]
#     },
#     ...
#   ]
#
# ============================================================================

import json
import os

# Configuration: Where to store search history
HISTORY_FILE = "data/search_history.json"

# Maximum number of searches to keep in history
MAX_HISTORY_ITEMS = 10

def save_to_history(query, coords):
    """
    Saves a location search query and its coordinates to persistent storage.
    
    Features:
    - Prevents duplicate entries (same query + coords)
    - Stores most recent searches first (LIFO)
    - Automatically limits history to MAX_HISTORY_ITEMS (default: 10)
    - Creates data directory if it doesn't exist
    
    Args:
        query (str): The search query term (e.g., "Kuala Lumpur")
        coords (list): [latitude, longitude] of found location
        
    Returns:
        None
        
    Example:
        >>> save_to_history("Petronas Twin Towers", [3.1560, 101.7127])
        
    Note:
        If the exact same search was already saved, it won't be duplicated.
        Older searches are automatically removed to maintain history size.
    """
    # Load existing history from file
    history = load_history()
    
    # Create new search entry
    new_entry = {"query": query, "coords": coords}
    
    # Check if this exact search already exists to avoid duplicates
    if new_entry not in history:
        # Add to beginning of list (most recent first)
        history.insert(0, new_entry)
    
    # Keep only the most recent searches (trim older ones)
    history = history[:MAX_HISTORY_ITEMS]
    
    # Ensure data directory exists, create if missing
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    
    # Write updated history to file
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def load_history():
    """
    Loads search history from persistent JSON file.
    
    Returns:
        list: Array of search entries, each with 'query' and 'coords'
              Empty list if file doesn't exist or is empty
              
    Example:
        >>> history = load_history()
        >>> for item in history:
        ...     print(f"{item['query']}: {item['coords']}")
        
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

def delete_history_item(index):
    """
    Deletes a specific search entry from history by its index position.
    
    Args:
        index (int): Position of item to delete (0-based indexing)
                     Index 0 is most recent search
        
    Returns:
        bool: True if deletion succeeded, False if index out of range
        
    Example:
        >>> delete_history_item(0)  # Delete most recent search
        True
        >>> delete_history_item(100)  # Invalid index
        False
        
    Note:
        History indices are 0-based and ordered by recency (newest first).
    """
    history = load_history()
    
    # Validate index is within valid range
    if 0 <= index < len(history):
        # Remove item at specified index
        history.pop(index)
        
        # Save updated history back to file
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
        return True
    
    return False

def clear_all_history():
    """
    Completely removes all search history.
    
    This operation:
    - Deletes the history JSON file
    - Is permanent and cannot be undone
    - Will leave an empty history on next search
    
    Returns:
        bool: True if successful, False if error occurs
        
    Example:
        >>> clear_all_history()
        True
        >>> load_history()
        []  # Returns empty list after clearing
        
    Warning:
        This operation is permanent! All stored search history is deleted.
    """
    try:
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        return True
    except Exception as e:
        print(f"Error clearing history: {e}")
        return False

