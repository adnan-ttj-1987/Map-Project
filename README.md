# T14 Map Explorer 🗺️

An interactive web-based mapping application built with Streamlit that allows users to search locations, find routes, and manage location history.

Full software documentation (use cases, architecture, assumptions, and extension design) is available at `docs/SOFTWARE_DOCUMENTATION.md`.
Architecture Decision Records (ADR) are tracked in `docs/adr/` and indexed in `docs/adr/README.md`.

### ADR Workflow
Use ADRs to capture architecture-level decisions and the rationale behind them.

1. Copy `docs/adr/0000-template.md` to a new file named `docs/adr/000N-short-title.md`.
2. Fill in Context, Decision, Alternatives, Consequences, and Follow-up Actions.
3. Mark status as `Proposed` while under review, then switch to `Accepted` once agreed.
4. If a new decision replaces an old one, set `Supersedes` and update the old ADR status to `Superseded`.
5. Reference the ADR ID in relevant PR descriptions and code comments when helpful.

## Features ✨

### 📍 Location Search
- **Multi-provider geocoding** with automatic fallback chain:
  - Photon API (fast, open-source)
  - Google Geocoding (if API key provided)
  - Nominatim (free fallback)
- Search by location name with instant map centering
- Save and manage search history

### 🛣️ Route Finding
- Calculate driving routes between two points
- Display distance (km) and estimated duration (hours/minutes)
- Route visualization with start/end markers
- Save routes to history for quick access
- Click saved routes to reload on map
- Multi-waypoint journeys using labeled START/STOP/END pins
- Route summary with per-leg focus and split controls

### 📌 Pin Dropping
- Click on map to drop pins and capture coordinates
- View all captured pins with exact coordinates and custom labels
- Assign role per pin (START/STOP/END)
- Build journeys from assigned pin roles
- Delete individual or all pins

### 🧭 Journey Controls
- Focus any route leg to center map and refresh nearby places
- Split a leg by target distance or target hours
- Generate breakpoint stops with nearby places for each breakpoint
- Center overall journey manually or automatically when zooming out

### 🏘️ Nearby Places
- Two display modes:
  - By Category (grouped)
  - By Distance (Flat, with category shown in item name)
- Persistent local cache for nearby place lookups (`data/nearby_cache.json`)

### 📚 Search History
- Automatically save location searches
- Quick access to recent searches
- Delete individual or all search history
- Click history items to jump to locations

### 🗺️ Interactive Map
- Multiple map layers:
  - Google Maps (default)
  - Google Satellite
  - OpenStreetMap
- Layer switcher in top-right
- Fully interactive with zoom/pan

### ℹ️ About Page
- Dedicated About page reachable via the new **About** button
- Shows platform capabilities and architecture highlights
- Displays update/change history from `data/update_history.json`

## Installation 🔧

### Prerequisites
- Python 3.14
- Git

### Setup

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/t14-map-explorer.git
cd t14-map-explorer
```

2. **Create virtual environment:**
```bash
py -3.14 -m venv .venv
.\.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # macOS/Linux
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **(Optional) Set up Google Geocoding API:**
```bash
# Create .env file
echo GOOGLE_GEOCODING_API_KEY=your_api_key > .env
```

Get a free Google API key:
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create a new project
- Enable "Geocoding API"
- Create an API key (free tier: $200 credit/month)

## Usage 🚀

### Run the app:
```bash
.venv\Scripts\streamlit run app.py
```

Or use the provided batch file (Windows):
```bash
run_app.bat
```

`run_app.bat` now bootstraps `.venv` automatically and installs dependencies before launching the app.

The app will open in your default browser at `http://localhost:8501`

## Project Structure 📁

```
t14-map-explorer/
├── app.py                          # Main app orchestrator (composes domain modules)
├── pages/
│   └── 1_About.py                  # About page (capabilities + update timeline)
├── requirements.txt                # Python dependencies
├── run_app.bat                     # Windows launcher
├── .gitignore                      # Git ignore rules
├── README.md                       # This file
├── data/                           # Data storage
│   ├── search_history.json         # Saved searches
│   ├── route_history.json          # Saved routes
│   ├── update_history.json         # App update/change history
│   └── nearby_cache.json           # Persistent nearby places cache
└── src/                            # Source modules
│   ├── utils/                      # Utility/service modules
│   │   ├── changelog_utils.py      # Update history load/save helpers
│   │   ├── search_utils.py         # Geocoding functions
│   │   ├── location_utils.py       # Location detection
│   │   ├── history_utils.py        # Search history management
│   │   ├── route_history_utils.py  # Route history management
│   │   ├── nearby_places_utils.py  # Nearby places query + caching
│   │   └── routing_utils.py        # Route finding & display
└── src/ui/                         # UI domain modules
    ├── session_state.py            # Session state initialization and defaults
    ├── styles.py                   # Shared styles
    ├── sidebar_sections.py         # Sidebar/search/route/history/settings UI
    ├── map_sections.py             # Map rendering + map interactions
    ├── main_sections.py            # Header, location panel, top action buttons
    ├── detail_sections.py          # Backward-compatible detail exports
    └── details/                    # Detailed feature submodules
        ├── shared.py               # Shared helpers for pins/journey/nearby
        ├── nearby_section.py       # Nearby list rendering and actions
        └── pins_journey_section.py # Captured pins + journey builder
```

## Module Documentation 📚

### `src/utils/search_utils.py`
Handles location searching with multi-provider fallback:
- `search_address(query)` - Search for location coordinates

Providers (in order):
1. Photon API - Fast, open-source
2. Google Geocoding - High accuracy (needs API key)
3. Nominatim - Free fallback

### `src/utils/location_utils.py`
IP-based current location detection:
- `get_current_location()` - Get user's approximate location

### `src/utils/history_utils.py`
Search history persistence:
- `save_to_history(query, coords)` - Save search
- `load_history()` - Load all searches
- `delete_history_item(index)` - Delete specific search
- `clear_all_history()` - Clear all searches

### `src/utils/route_history_utils.py`
Route calculation history:
- `save_route(...)` - Save calculated route
- `load_routes()` - Load all routes
- `delete_route(index)` - Delete specific route
- `clear_all_routes()` - Clear all routes

### `src/utils/routing_utils.py`
Route finding and visualization:
- `get_route(start, end)` - Calculate route using OSRM
- `add_route_to_map(map, start, end, route)` - Add route to map

## Technologies Used 🛠️

- **Streamlit** - Web framework
- **Folium** - Interactive mapping
- **Geopy** - Geocoding
- **Requests** - HTTP library
- **OSRM** - Open Source Routing Machine
- **Photon API** - Location search
- **Google Geocoding API** - Alternative geocoding

## Configuration ⚙️

### Environment Variables
```bash
# Optional: Google Geocoding API key
GOOGLE_GEOCODING_API_KEY=your_api_key_here
```

### Data Storage
- Search history: `data/search_history.json`
- Route history: `data/route_history.json`
- Nearby cache: `data/nearby_cache.json`
- Max items kept: 10 most recent

## Troubleshooting 🔍

### "Photon API 403 Forbidden"
- Falls back to Nominatim automatically
- No action needed - app continues working

### "Could not run due to Python version"
- The old root-level virtual environment in this repository points to a removed Python 3.13 install
- Use `.venv` instead of `Scripts\activate.bat` at the project root
- Run `run_app.bat` to recreate the environment automatically on Windows

### "Could not find location"
- Try more specific location name
- Use "City, Country" format
- Check if location exists on Google Maps

### "Location services unavailable"
- Disable VPN/proxy
- Check internet connection
- Falls back to default location (Kuala Lumpur)

## Performance 📊

- **Search**: <2 seconds (Photon), <5 seconds (Nominatim)
- **Route**: <3 seconds for typical routes
- **Map**: Instant rendering up to 100+ markers
- **History**: Instant load/save (<100ms)

## Browser Compatibility 🌐

Tested and working on:
- Chrome 120+
- Firefox 121+
- Safari 17+
- Edge 120+

## License 📄

MIT License - See LICENSE file for details

## Contributing 🤝

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## Roadmap 🗓️

- [ ] Offline map support
- [ ] Multiple route alternatives
- [ ] Traffic layer
- [ ] POI (Points of Interest) display
- [ ] Route export (GPX/KML)
- [ ] Dark mode
- [ ] Mobile app version
- [ ] User accounts/sync

## Support 💬

For issues, questions, or suggestions:
- Open an [Issue](https://github.com/yourusername/t14-map-explorer/issues)
- Check existing issues for solutions
- Include error messages and steps to reproduce

## Credits 👏

- **OSRM** - Open Source Routing Machine
- **Folium** - Leaflet.js Python wrapper
- **Streamlit** - Web app framework
- **Photon** - Komoot's geocoding service
- **OpenStreetMap** - Map data

## Changelog 📝

### v1.0.0 (2026-01-28)
- Initial release
- Location search with multi-provider fallback
- Interactive map with multiple layers
- Route finding and history
- Pin dropping with coordinate capture
- Search history management
- Route history with quick reload

---

**T14 Map Explorer** - Making location discovery easy 🎯
