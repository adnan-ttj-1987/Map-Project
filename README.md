# T14 Map Explorer 🗺️

An interactive web-based mapping application built with Streamlit that allows users to search locations, find routes, and manage location history.

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

### 📌 Pin Dropping
- Click on map to drop pins and capture coordinates
- View all captured pins with exact coordinates
- Set pins as route start or destination
- Copy coordinates to clipboard
- Delete individual or all pins

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

## Installation 🔧

### Prerequisites
- Python 3.8+
- Git

### Setup

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/t14-map-explorer.git
cd t14-map-explorer
```

2. **Create virtual environment:**
```bash
python -m venv venv
.\Scripts\activate  # Windows
# or
source venv/bin/activate  # macOS/Linux
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
streamlit run app.py
```

Or use the provided batch file (Windows):
```bash
run_app.bat
```

The app will open in your default browser at `http://localhost:8501`

## Project Structure 📁

```
t14-map-explorer/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── run_app.bat                     # Windows launcher
├── .gitignore                      # Git ignore rules
├── README.md                       # This file
├── data/                           # Data storage
│   ├── search_history.json         # Saved searches
│   └── route_history.json          # Saved routes
└── src/                            # Source modules
    ├── search_utils.py             # Geocoding functions
    ├── location_utils.py           # Location detection
    ├── history_utils.py            # Search history management
    ├── route_history_utils.py      # Route history management
    └── routing_utils.py            # Route finding & display
```

## Module Documentation 📚

### `search_utils.py`
Handles location searching with multi-provider fallback:
- `search_address(query)` - Search for location coordinates

Providers (in order):
1. Photon API - Fast, open-source
2. Google Geocoding - High accuracy (needs API key)
3. Nominatim - Free fallback

### `location_utils.py`
IP-based current location detection:
- `get_current_location()` - Get user's approximate location

### `history_utils.py`
Search history persistence:
- `save_to_history(query, coords)` - Save search
- `load_history()` - Load all searches
- `delete_history_item(index)` - Delete specific search
- `clear_all_history()` - Clear all searches

### `route_history_utils.py`
Route calculation history:
- `save_route(...)` - Save calculated route
- `load_routes()` - Load all routes
- `delete_route(index)` - Delete specific route
- `clear_all_routes()` - Clear all routes

### `routing_utils.py`
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
- Max items kept: 10 most recent

## Troubleshooting 🔍

### "Photon API 403 Forbidden"
- Falls back to Nominatim automatically
- No action needed - app continues working

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
