import streamlit as st
from streamlit_folium import st_folium
import folium
from src.search_utils import search_address
from src.location_utils import get_current_location
from src.history_utils import save_to_history, load_history, delete_history_item, clear_all_history
from src.route_history_utils import save_route, load_routes, delete_route, clear_all_routes
from src.routing_utils import get_route, add_route_to_map
from src.nearby_places_utils import get_nearby_places

# ============================================================================
# T14 MAP EXPLORER - Interactive Map Application
# ============================================================================
# 
# Purpose:
#   A comprehensive web-based mapping application that allows users to:
#   - Search for locations using multiple geocoding services
#   - Visualize locations on interactive maps (Google Maps, OSM)
#   - Find routes between two points with distance/duration
#   - Drop pins on the map and capture coordinates
#   - Maintain search history for quick access
#
# Features:
#   • Location Search: Photon → Google Geocoding → Nominatim (fallback chain)
#   • Interactive Map: Multiple tile layers (Google, Satellite, OpenStreetMap)
#   • Route Finding: OSRM-based routing with distance and duration
#   • Pin Dropping: Click map to capture coordinates and set routes
#   • Search History: Persistent storage with individual and bulk delete
#   • Current Location: IP-based location detection
#
# Author: Development Team
# Date: January 2026
# Version: 1.0.0
# ============================================================================

# Configure Streamlit page settings
st.set_page_config(
    page_title="T14 Map Explorer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 20px 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.5em;
    }
    .section-divider {
        margin: 30px 0 20px 0;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
# Initialize session state variables to persist data across reruns
def init_session_state():
    """Initialize all required session state variables."""
    if 'map_center' not in st.session_state:
        st.session_state.map_center = [2.7258, 101.9424]  # Default: Seremban, Malaysia
    if 'zoom' not in st.session_state:
        st.session_state.zoom = 12  # Default zoom level
    if 'route_start' not in st.session_state:
        st.session_state.route_start = None
    if 'route_end' not in st.session_state:
        st.session_state.route_end = None
    if 'captured_pins' not in st.session_state:
        st.session_state.captured_pins = []
    if 'start_location' not in st.session_state:
        st.session_state.start_location = ""
    if 'end_location' not in st.session_state:
        st.session_state.end_location = ""
    if 'route_distance' not in st.session_state:
        st.session_state.route_distance = None
    if 'route_duration' not in st.session_state:
        st.session_state.route_duration = None
    if 'location_info' not in st.session_state:
        st.session_state.location_info = None
    if 'show_location_debug' not in st.session_state:
        st.session_state.show_location_debug = False
    if 'show_location_info' not in st.session_state:
        st.session_state.show_location_info = True
    if 'sidebar_collapsed' not in st.session_state:
        st.session_state.sidebar_collapsed = False
    if 'nearby_places' not in st.session_state:
        st.session_state.nearby_places = {}
    if 'show_nearby_places' not in st.session_state:
        st.session_state.show_nearby_places = False
    if 'search_radius_km' not in st.session_state:
        st.session_state.search_radius_km = 1.0

init_session_state()

# ============================================================================
# SIDEBAR - SEARCH & NAVIGATION CONTROLS
# ============================================================================
with st.sidebar:
    # Sidebar collapse button
    col_sidebar_1, col_sidebar_2 = st.columns([0.7, 0.3])
    with col_sidebar_1:
        st.markdown("### 🗺️ Navigation Panel")
    with col_sidebar_2:
        if st.button("−" if not st.session_state.sidebar_collapsed else "+", key="sidebar_toggle", help="Collapse/Expand"):
            st.session_state.sidebar_collapsed = not st.session_state.sidebar_collapsed
            st.rerun()
    
    if not st.session_state.sidebar_collapsed:
        # --- SEARCH SECTION ---
        with st.container():
            st.markdown("#### 🔍 Search Location")
            search_query = st.text_input(
                "Find a place:",
                key="search_input",
                placeholder="e.g., 'Kuala Lumpur', 'Petronas Tower'",
                label_visibility="collapsed"
            )
            
            col_search_1, col_search_2 = st.columns(2)
            with col_search_1:
                if st.button("🔍 Search", use_container_width=True):
                    if search_query:
                        try:
                            coords = search_address(search_query)
                            if coords:
                                st.session_state.map_center = coords
                                st.session_state.zoom = 15
                                save_to_history(search_query, coords)
                                
                                # Fetch nearby places with selected radius
                                with st.spinner("🔍 Finding nearby places..."):
                                    nearby = get_nearby_places(coords[0], coords[1], st.session_state.search_radius_km)
                                    st.session_state.nearby_places = nearby
                                    st.session_state.show_nearby_places = True
                                
                                st.success(f"✅ Found: {search_query}")
                            else:
                                st.error(f"❌ Not found: {search_query}")
                        except Exception as e:
                            st.error(f"⚠️ Error: {str(e)}")
                    else:
                        st.warning("Please enter a location")
            
            with col_search_2:
                if st.button("🔄 Clear", use_container_width=True):
                    st.session_state.map_center = [2.7258, 101.9424]
                    st.session_state.zoom = 12
                    st.rerun()
            
            # Search radius control
            st.markdown("**Search Radius**")
            st.session_state.search_radius_km = st.slider(
                "Nearby places search radius (km):",
                min_value=0.5,
                max_value=5.0,
                value=st.session_state.search_radius_km,
                step=0.5,
                key="radius_slider",
                label_visibility="collapsed"
            )
    
        st.divider()
        
        # --- LOCATION SECTION ---
        with st.container():
            st.markdown("#### 📍 My Location")
            if st.button("🏠 Reset to My Location", use_container_width=True, key="sidebar_location_btn"):
                try:
                    location_info = get_current_location(show_debug=True)
                    if location_info and location_info['coords']:
                        st.session_state.map_center = location_info['coords']
                        st.session_state.zoom = 14
                        st.session_state.location_info = location_info
                        st.session_state.show_location_debug = True
                        st.success("📍 Location detected!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Could not detect location")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        st.divider()
        
        # --- ROUTE SECTION (COLLAPSIBLE) ---
        with st.expander("🛣️ Route Planner", expanded=True):
            start = st.text_input("Start:", placeholder="Origin", key="start_input", label_visibility="collapsed")
            end = st.text_input("End:", placeholder="Destination", key="end_input", label_visibility="collapsed")
            
            col_route_1, col_route_2 = st.columns(2)
            with col_route_1:
                if st.button("📍 Calculate", use_container_width=True):
                    if start and end:
                        try:
                            start_coords = search_address(start)
                            end_coords = search_address(end)
                            if start_coords and end_coords:
                                st.session_state.route_start = start_coords
                                st.session_state.route_end = end_coords
                                route_data = get_route(start_coords, end_coords)
                                if route_data:
                                    st.session_state.route_distance = route_data['distance']
                                    st.session_state.route_duration = route_data['duration']
                                    save_route(start, end, start_coords, end_coords, route_data['distance'], route_data['duration'])
                                    st.success("✅ Route calculated!")
                                st.rerun()
                            else:
                                st.error("❌ One or both locations not found")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                    else:
                        st.warning("Enter both start and end")
            
            with col_route_2:
                if st.button("🗑️ Clear", use_container_width=True):
                    st.session_state.route_start = None
                    st.session_state.route_end = None
                    st.session_state.route_distance = None
                    st.session_state.route_duration = None
                    st.rerun()
        
        st.divider()
        
        # --- HISTORY SECTION ---
        with st.expander("📚 Search History", expanded=False):
            try:
                history = load_history()
                if history:
                    for idx, item in enumerate(history):
                        col1, col2 = st.columns([0.8, 0.2])
                        with col1:
                            if st.button(f"📍 {item['query']}", key=f"hist_{idx}", use_container_width=True):
                                st.session_state.map_center = item['coords']
                                st.session_state.zoom = 15
                                st.rerun()
                        with col2:
                            if st.button("✕", key=f"del_hist_{idx}", use_container_width=True):
                                delete_history_item(idx)
                                st.rerun()
                    
                    if st.button("🗑️ Clear All", use_container_width=True):
                        clear_all_history()
                        st.success("✅ History cleared!")
                        st.rerun()
                else:
                    st.info("No search history")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        # --- ROUTE HISTORY SECTION ---
        with st.expander("📜 Route History", expanded=False):
            try:
                routes = load_routes()
                if routes:
                    for idx, route in enumerate(routes):
                        col1, col2 = st.columns([0.8, 0.2])
                        with col1:
                            route_text = f"🛣️ {route['start']} → {route['end']}"
                            if st.button(route_text, key=f"route_{idx}", use_container_width=True):
                                st.session_state.route_start = route['start_coords']
                                st.session_state.route_end = route['end_coords']
                                st.session_state.start_location = route['start']
                                st.session_state.end_location = route['end']
                                st.session_state.route_distance = route['distance']
                                st.session_state.route_duration = route['duration']
                                st.rerun()
                        with col2:
                            if st.button("✕", key=f"del_route_{idx}", use_container_width=True):
                                delete_route(idx)
                                st.rerun()
                    
                    if st.button("🗑️ Clear All", use_container_width=True):
                        clear_all_routes()
                        st.success("✅ Routes cleared!")
                        st.rerun()
                else:
                    st.info("No route history")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# ============================================================================
# MAIN CONTENT AREA
# ============================================================================

# --- HEADER ---
col_header_1, col_header_2, col_header_3 = st.columns([1, 2, 1])
with col_header_2:
    st.markdown("""
        <div class="main-header">
            <h1>🗺️ Map Explorer</h1>
            <p style="margin: 5px 0; font-size: 0.9em;">Navigate, Search & Plan Routes</p>
        </div>
    """, unsafe_allow_html=True)

# --- LOCATION INFO SECTION ---
if st.session_state.show_location_debug and st.session_state.location_info:
    info = st.session_state.location_info
    
    col_loc_title, col_loc_toggle = st.columns([0.85, 0.15])
    with col_loc_title:
        st.markdown("### 📍 Your Location")
    with col_loc_toggle:
        if st.button("−" if st.session_state.show_location_info else "+", key="location_info_toggle", help="Toggle details"):
            st.session_state.show_location_info = not st.session_state.show_location_info
            st.rerun()
    
    # Main location display
    col_info_1, col_info_2 = st.columns(2)
    with col_info_1:
        st.metric("🏙️ City", info.get('city', 'N/A'))
    with col_info_2:
        st.metric("🌍 Country", info.get('country', 'N/A'))
    
    # Collapsible details
    if st.session_state.show_location_info:
        col_info_3, col_info_4 = st.columns(2)
        with col_info_3:
            st.metric("📡 Source", info.get('source', 'N/A'))
        with col_info_4:
            st.metric("📐 Accuracy", info.get('accuracy', 'N/A'))
        
        col_lat, col_lon = st.columns(2)
        with col_lat:
            st.code(f"Latitude: {info['coords'][0]:.6f}", language="text")
        with col_lon:
            st.code(f"Longitude: {info['coords'][1]:.6f}", language="text")
    
    st.divider()

# --- LOCATION ACTION BUTTONS ---
col_action_1, col_action_2, col_action_3 = st.columns(3)
with col_action_1:
    if st.button("🏠 My Location", use_container_width=True, key="main_location_btn"):
        try:
            location_info = get_current_location(show_debug=True)
            if location_info and location_info['coords']:
                st.session_state.map_center = location_info['coords']
                st.session_state.zoom = 14
                st.session_state.location_info = location_info
                st.session_state.show_location_debug = True
                st.rerun()
            else:
                st.warning("⚠️ Could not detect location")
        except Exception as e:
            st.error(f"Error: {str(e)}")

with col_action_2:
    if st.button("🔄 Refresh Map", use_container_width=True):
        st.rerun()

with col_action_3:
    if st.button("⚙️ Reset View", use_container_width=True):
        st.session_state.map_center = [2.7258, 101.9424]
        st.session_state.zoom = 12
        st.rerun()

# --- CREATE & DISPLAY MAP ---
st.markdown("### 🗺️ Interactive Map")
st.markdown("*Click on the map to capture coordinates*")

m = folium.Map(
    location=st.session_state.map_center,
    zoom_start=st.session_state.zoom,
    tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    attr="Google Maps"
)

# Add satellite view
folium.TileLayer(
    tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    attr="Google Satellite",
    name="Satellite",
    overlay=False,
    control=True
).add_to(m)

# Add OSM
folium.TileLayer(
    tiles="OpenStreetMap",
    name="Street Map",
    overlay=False,
    control=True
).add_to(m)

folium.LayerControl(position='topright').add_to(m)

# Add route if available
if st.session_state.route_start and st.session_state.route_end:
    try:
        route_data = get_route(st.session_state.route_start, st.session_state.route_end)
        if route_data:
            add_route_to_map(m, st.session_state.route_start, st.session_state.route_end, route_data)
            all_lats = [st.session_state.route_start[0], st.session_state.route_end[0]]
            all_lons = [st.session_state.route_start[1], st.session_state.route_end[1]]
            bounds = [[min(all_lats), min(all_lons)], [max(all_lats), max(all_lons)]]
            m.fit_bounds(bounds, padding=(0.1, 0.1))
    except Exception as e:
        st.warning(f"⚠️ Route error: {str(e)}")
else:
        # Current location marker
        folium.Marker(
            location=st.session_state.map_center,
            popup="📍 Current View",
            icon=folium.Icon(color='blue', icon='dot', prefix='fa')
        ).add_to(m)

        # Add captured pins; highlight the most recently dropped pin
        for idx, pin in enumerate(st.session_state.captured_pins):
            is_last = (idx == len(st.session_state.captured_pins) - 1)
            if is_last:
                # Highlight last pin with a larger circle and darker marker
                folium.CircleMarker(
                    location=[pin['lat'], pin['lon']],
                    radius=10,
                    color='#b30000',
                    fill=True,
                    fill_color='#ff6666',
                    fill_opacity=0.9,
                    popup=f"📌 Selected Pin {idx + 1}: ({pin['lat']:.4f}, {pin['lon']:.4f})"
                ).add_to(m)
                folium.Marker(
                    location=[pin['lat'], pin['lon']],
                    popup=f"📌 Selected Pin {idx + 1}: ({pin['lat']:.4f}, {pin['lon']:.4f})",
                    icon=folium.Icon(color='darkred', icon='map-pin', prefix='fa')
                ).add_to(m)
            else:
                folium.Marker(
                    location=[pin['lat'], pin['lon']],
                    popup=f"📌 Pin {idx + 1}: ({pin['lat']:.4f}, {pin['lon']:.4f})",
                    icon=folium.Icon(color='red', icon='map-pin', prefix='fa')
                ).add_to(m)

        # Add nearby place markers if available. Show places relative to the highlighted pin if there is one,
        # otherwise show places for the current search/map center.
        if st.session_state.get('nearby_places'):
            # Determine reference point (use last pin if present)
            ref_point = None
            if st.session_state.captured_pins:
                last_pin = st.session_state.captured_pins[-1]
                ref_point = (last_pin['lat'], last_pin['lon'])
            else:
                ref_point = tuple(st.session_state.map_center)

            # Simple category -> color mapping for markers
            category_colors = {
                'Education': 'green',
                'Food & Dining': 'orange',
                'Attractions': 'cadetblue',
                'Accommodation': 'purple',
                'Transport': 'darkblue',
                'Amenities': 'gray'
            }

            # Category -> FontAwesome icon mapping
            category_icons = {
                'Education': 'graduation-cap',
                'Food & Dining': 'utensils',
                'Attractions': 'landmark',
                'Accommodation': 'hotel',
                'Transport': 'bus',
                'Amenities': 'info-circle'
            }

            for category, places in st.session_state.nearby_places.items():
                for place in places:
                    try:
                        plat = place.get('lat') or place.get('latitude')
                        plon = place.get('lon') or place.get('longitude')
                        if plat is None or plon is None:
                            continue
                        name = place.get('name', 'Unnamed')
                        rating = place.get('rating')
                        distance = place.get('distance')
                        popup_lines = [f"<b>{name}</b>"]
                        popup_lines.append(f"Category: {category}")
                        if rating is not None:
                            popup_lines.append(f"⭐ {rating}")
                        if distance is not None:
                            popup_lines.append(f"{distance:.2f} km away")
                        popup_html = '<br/>'.join(popup_lines)

                        color = category_colors.get(category, 'red')
                        icon_name = category_icons.get(category, 'info-circle')

                        # Draw connector line from reference point to this POI
                        try:
                            folium.PolyLine(
                                locations=[ref_point, (plat, plon)],
                                color=color,
                                weight=2,
                                opacity=0.6,
                                dash_array='5,5'
                            ).add_to(m)
                        except Exception:
                            pass

                        # Add POI marker with category-specific icon
                        folium.Marker(
                            location=[plat, plon],
                            popup=folium.Popup(popup_html, max_width=300),
                            icon=folium.Icon(color=color, icon=icon_name, prefix='fa')
                        ).add_to(m)
                    except Exception:
                        continue

# Display map
map_data = st_folium(m, width="100%", height=600, key="main_map")

# Capture pin clicks
if map_data and map_data.get('last_clicked'):
    clicked = map_data['last_clicked']
    new_pin = {'lat': clicked['lat'], 'lon': clicked['lng']}
    if not st.session_state.captured_pins or new_pin not in st.session_state.captured_pins:
        st.session_state.captured_pins.append(new_pin)
        
        # Fetch nearby places for this pin with selected radius
        with st.spinner("🔍 Finding nearby places..."):
            nearby = get_nearby_places(new_pin['lat'], new_pin['lon'], st.session_state.search_radius_km)
            st.session_state.nearby_places = nearby
            st.session_state.show_nearby_places = True
        
        st.success(f"📍 Pinned: {new_pin['lat']:.4f}, {new_pin['lon']:.4f}")
        st.rerun()

st.divider()

# ============================================================================
# CAPTURED PINS SECTION
# ============================================================================
if st.session_state.captured_pins:
    st.markdown("### 📌 Captured Pins")
    
    col_pins_clear = st.columns([1])[0]
    if st.button("🗑️ Clear All Pins", use_container_width=True):
        st.session_state.captured_pins = []
        st.success("✅ All pins cleared!")
        st.rerun()
    
    # Display pins in a organized grid
    for idx, pin in enumerate(st.session_state.captured_pins):
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1.5, 1, 0.5])
            
            with col1:
                st.text(f"📍 **Pin {idx + 1}**: {pin['lat']:.6f}, {pin['lon']:.6f}")
            
            with col2:
                if st.button("🚩 Start", key=f"start_{idx}", use_container_width=True):
                    st.session_state.route_start = [pin['lat'], pin['lon']]
                    st.success(f"✅ Pin {idx + 1} as start")
                    st.rerun()
            
            with col3:
                if st.button("🎯 End", key=f"dest_{idx}", use_container_width=True):
                    st.session_state.route_end = [pin['lat'], pin['lon']]
                    st.success(f"✅ Pin {idx + 1} as end")
                    st.rerun()
            
            with col4:
                if st.button("📋 Copy", key=f"copy_{idx}", use_container_width=True):
                    st.toast(f"📋 {pin['lat']:.6f}, {pin['lon']:.6f}")
            
            with col5:
                if st.button("✕", key=f"del_pin_{idx}", use_container_width=True):
                    st.session_state.captured_pins.pop(idx)
                    st.rerun()

# ============================================================================
# NEARBY PLACES SECTION
# ============================================================================
if st.session_state.show_nearby_places:
    st.divider()
    
    if st.session_state.nearby_places and len(st.session_state.nearby_places) > 0:
        st.markdown("### 🏘️ Nearby Places Around This Area")
        
        nearby = st.session_state.nearby_places
        total_places = sum(len(places) for places in nearby.values())
        st.info(f"📍 Found {total_places} interesting places nearby")
        
        # Display by category with collapsible sections
        for category in sorted(nearby.keys()):
            places = nearby[category]
            if places:  # Only show category if it has places
                with st.expander(f"{category} ({len(places)} found)", expanded=True):
                    for place_idx, place in enumerate(places):
                        col1, col2 = st.columns([0.85, 0.15])
                        
                        with col1:
                            # Display place info
                            display_text = f"**{place['name']}** • {place['distance']} km"
                            
                            # Add halal status for food places
                            if place.get('halal') is not None:
                                halal_badge = "✅ Halal" if place['halal'] else "❌ Non-Halal"
                                display_text += f" • {halal_badge}"
                            
                            st.write(display_text)
                            
                            # Display additional info if available
                            info_text = ""
                            if place.get("phone"):
                                info_text += f"📞 {place['phone']}"
                            if place.get("url"):
                                if info_text:
                                    info_text += " | "
                                info_text += f"🌐 {place['url']}"
                            
                            if info_text:
                                st.caption(info_text)
                        
                        with col2:
                            # Use index to ensure unique key
                            if st.button("📍", key=f"place_{category}_{place_idx}_{place['lat']}_{place['lon']}", help="View on map"):
                                # Center map on this place
                                st.session_state.map_center = [place['lat'], place['lon']]
                                st.session_state.zoom = 16
                                st.rerun()
    else:
        st.warning("⚠️ No nearby places found for this location. Try a different area or check the map.")

# ============================================================================
# ROUTE & LOCATION INFO FOOTER
# ============================================================================
st.divider()
st.markdown("### 📊 Status Information")

# Route info
if st.session_state.route_start and st.session_state.route_end:
    try:
        route_data = get_route(st.session_state.route_start, st.session_state.route_end)
        if route_data:
            col_route_1, col_route_2 = st.columns(2)
            with col_route_1:
                st.metric("📏 Distance", f"{route_data['distance']} km")
            with col_route_2:
                total_minutes = int(route_data['duration'])
                hours = total_minutes // 60
                minutes = total_minutes % 60
                duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
                st.metric("⏱️ Duration", duration_str)
    except:
        pass

# Map info
col_loc_1, col_loc_2, col_loc_3 = st.columns(3)
with col_loc_1:
    st.metric("📍 Latitude", f"{st.session_state.map_center[0]:.4f}")
with col_loc_2:
    st.metric("📍 Longitude", f"{st.session_state.map_center[1]:.4f}")
with col_loc_3:
    st.metric("🔍 Zoom", f"{st.session_state.zoom}x")

st.divider()
st.caption("🗺️ T14 Map Explorer © 2026 | Telekom Malaysia Berhad")