# =============================================================================
# api.py - API Handler
# =============================================================================
# This module is responsible for:
#   - Communicating with the OpenWeatherMap API
#   - Resolving city names accurately via the Geocoding API (lat/lon lookup)
#   - Parsing the JSON response into a clean Python dictionary
#   - Handling all network/API-related errors gracefully
#
# Search supports:
#   "Hyderabad"            → plain city name
#   "Hyderabad, IN"        → city + country code (most accurate)
#   "Springfield, US"      → disambiguate common names
# =============================================================================

import requests                        # For making HTTP requests
from config import API_KEY, BASE_URL, UNITS  # Import settings from config

# OpenWeatherMap Geocoding API endpoint (resolves city name → lat/lon)
GEO_URL = "https://api.openweathermap.org/geo/1.0/direct"

# Weather by coordinates endpoint (most accurate — no ambiguity)
WEATHER_BY_COORD_URL = "https://api.openweathermap.org/data/2.5/weather"


# -----------------------------------------------------------------------------
# Function: _resolve_city_coordinates
# Purpose : Uses the Geocoding API to convert a city name → (lat, lon, country)
#           This ensures we always get the correct city, especially for:
#           - Cities with the same name in different countries
#           - Indian/Asian cities that may be misidentified
# Params  : city_query (str) - e.g. "Hyderabad" or "Hyderabad, IN"
# Returns : (lat, lon, resolved_name, country) tuple OR None on failure
# -----------------------------------------------------------------------------
def _resolve_city_coordinates(city_query: str):
    """
    Resolve a city name to precise GPS coordinates using the Geocoding API.

    Supports queries like:
        "Hyderabad"       → searches globally, returns top match
        "Hyderabad, IN"   → narrows search to India specifically
        "London, GB"      → pinpoints London, United Kingdom

    Returns:
        tuple: (lat, lon, city_name, country_code) or None on failure.
    """
    # Parse optional country code suffix (e.g. "Hyderabad, IN" → city="Hyderabad", cc="IN")
    parts = [p.strip() for p in city_query.split(",")]
    city_part    = parts[0]
    country_code = parts[1].upper() if len(parts) >= 2 else None

    # Build geocoding query: "city,countrycode" or just "city"
    geo_query = f"{city_part},{country_code}" if country_code else city_part

    params = {
        "q":     geo_query,
        "limit": 5,          # Get top 5 matches so we can pick the best one
        "appid": API_KEY,
    }

    try:
        response = requests.get(GEO_URL, params=params, timeout=10)

        if response.status_code == 200:
            results = response.json()

            if not results:
                return None   # No city found with that name

            # If country code was specified, prefer that country's result
            if country_code:
                for r in results:
                    if r.get("country", "").upper() == country_code:
                        return (r["lat"], r["lon"],
                                r.get("name", city_part),
                                r.get("country", ""),
                                r.get("state", ""))
            # Fall back to first result (most relevant match)
            best = results[0]
            return (best["lat"], best["lon"],
                    best.get("name", city_part),
                    best.get("country", ""),
                    best.get("state", ""))

        elif response.status_code == 401:
            print("[ERROR] Invalid API key.")
            return None
        else:
            print(f"[ERROR] Geocoding API error: HTTP {response.status_code}")
            return None

    except requests.exceptions.ConnectionError:
        print("[ERROR] No internet connection.")
        return None
    except requests.exceptions.Timeout:
        print("[ERROR] Geocoding request timed out.")
        return None
    except Exception as e:
        print(f"[ERROR] Geocoding failed: {e}")
        return None


# -----------------------------------------------------------------------------
# Function: get_all_city_matches
# Purpose : Returns up to 5 geocoding matches for a query so the GUI can
#           show the user ALL possible cities and let them pick the right one.
# Params  : city_query (str)
# Returns : list of dicts with keys: name, country, state, lat, lon
# -----------------------------------------------------------------------------
def get_all_city_matches(city_query: str) -> list:
    """
    Return all geocoding matches for a city name query (up to 5).
    Used by the GUI to show a disambiguation dialog when the result
    might not be what the user intended.

    Returns:
        list of dicts: [{name, country, state, lat, lon}, ...]
        Empty list if nothing found or error occurred.
    """
    if API_KEY == "YOUR_API_KEY_HERE":
        return []

    city_query = city_query.strip()
    if not city_query:
        return []

    parts        = [p.strip() for p in city_query.split(",")]
    city_part    = parts[0]
    country_code = parts[1].upper() if len(parts) >= 2 else None
    geo_query    = f"{city_part},{country_code}" if country_code else city_part

    params = {"q": geo_query, "limit": 5, "appid": API_KEY}

    try:
        response = requests.get(GEO_URL, params=params, timeout=10)
        if response.status_code == 200:
            results = response.json()
            matches = []
            for r in results:
                matches.append({
                    "name":    r.get("name", city_part),
                    "country": r.get("country", ""),
                    "state":   r.get("state", ""),
                    "lat":     r.get("lat", 0),
                    "lon":     r.get("lon", 0),
                })
            return matches
        return []
    except Exception:
        return []


# -----------------------------------------------------------------------------
# Function: fetch_weather
# Purpose : Fetches accurate weather for any city using a 2-step approach:
#           Step 1 → Geocoding API: city name → precise lat/lon coordinates
#           Step 2 → Weather API:   lat/lon   → actual weather data
#           This eliminates city name ambiguity entirely.
# Params  : city_name (str) - e.g. "Hyderabad", "Hyderabad, IN", "Paris, FR"
# Returns : dict with weather data  OR  None if an error occurred
# -----------------------------------------------------------------------------
def fetch_weather(city_name: str) -> dict | None:
    """
    Fetch accurate current weather data for any city worldwide.

    Uses a 2-step process for maximum accuracy:
      1. Geocoding API resolves the city name to exact lat/lon coordinates.
      2. Weather API fetches live data using those coordinates.

    This approach correctly handles:
      - "Hyderabad" → Hyderabad, India (not Pakistan's Hyderabad)
      - "Springfield" → Picks the most relevant match
      - Indian, Asian, European city names with Unicode characters
      - Cities with the same name in multiple countries (use "City, CC" format)

    Args:
        city_name (str): City name. Optionally append country code for precision.
                         Examples: "Mumbai", "Mumbai, IN", "London, GB"

    Returns:
        dict: Parsed weather data, or None on failure.
    """

    # ── Validate API key ──
    if API_KEY == "YOUR_API_KEY_HERE":
        print("[ERROR] API key not configured!")
        print("        Please open config.py and replace 'YOUR_API_KEY_HERE'")
        print("        with your actual OpenWeatherMap API key.")
        return None

    # ── Validate input ──
    city_name = city_name.strip()
    if not city_name:
        print("[ERROR] City name cannot be empty.")
        return None

    print(f"[INFO] Resolving city: '{city_name}'...")

    # ── Step 1: Resolve city → coordinates ──
    geo_result = _resolve_city_coordinates(city_name)

    if geo_result is None:
        print(f"[ERROR] City '{city_name}' could not be found.")
        print("        Tips:")
        print("          • Check the spelling (use English city names)")
        print("          • Add country code for accuracy: 'Hyderabad, IN'")
        print("          • Try a nearby major city")
        return None

    lat, lon, resolved_name, country, state = geo_result
    print(f"[INFO] Resolved → {resolved_name}, {country}  (lat={lat:.4f}, lon={lon:.4f})")

    # ── Step 2: Fetch weather using coordinates ──
    params = {
        "lat":   lat,
        "lon":   lon,
        "appid": API_KEY,
        "units": UNITS,       # metric = Celsius
    }

    try:
        response = requests.get(WEATHER_BY_COORD_URL, params=params, timeout=10)

        if response.status_code == 200:
            raw_data = response.json()
            # Override city name with the geocoded name for consistency
            raw_data["name"] = resolved_name
            if "sys" not in raw_data:
                raw_data["sys"] = {}
            raw_data["sys"]["country"] = country
            return parse_weather_data(raw_data)

        elif response.status_code == 401:
            print("[ERROR] Invalid API key. Please check your API_KEY in config.py")
            return None

        elif response.status_code == 429:
            print("[ERROR] API rate limit exceeded. Please wait and try again.")
            return None

        else:
            print(f"[ERROR] Weather API error: HTTP {response.status_code}")
            return None

    except requests.exceptions.ConnectionError:
        print("[ERROR] No internet connection. Please check your network.")
        return None

    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out. The server may be slow. Try again.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] A network error occurred: {e}")
        return None


# -----------------------------------------------------------------------------
# Function: fetch_weather_by_coords
# Purpose : Fetch weather directly using known lat/lon + city name/country.
#           Called by the GUI after the user confirms a city from the
#           disambiguation dialog.
# -----------------------------------------------------------------------------
def fetch_weather_by_coords(lat: float, lon: float,
                             city_name: str, country: str) -> dict | None:
    """
    Fetch weather using exact coordinates. Used after user confirms a city
    from the disambiguation picker.

    Args:
        lat, lon (float): GPS coordinates.
        city_name (str): Resolved city name to label the result.
        country (str): 2-letter country code.

    Returns:
        dict: Parsed weather data, or None on failure.
    """
    params = {
        "lat":   lat,
        "lon":   lon,
        "appid": API_KEY,
        "units": UNITS,
    }
    try:
        response = requests.get(WEATHER_BY_COORD_URL, params=params, timeout=10)
        if response.status_code == 200:
            raw_data = response.json()
            raw_data["name"] = city_name
            if "sys" not in raw_data:
                raw_data["sys"] = {}
            raw_data["sys"]["country"] = country
            return parse_weather_data(raw_data)
        print(f"[ERROR] Weather API error: HTTP {response.status_code}")
        return None
    except Exception as e:
        print(f"[ERROR] fetch_weather_by_coords failed: {e}")
        return None
# Purpose : Extracts the fields we care about from the raw API JSON response
# Params  : raw_data (dict) - The full JSON response from OpenWeatherMap
# Returns : A clean, flat dictionary with only the fields we need
# -----------------------------------------------------------------------------
def parse_weather_data(raw_data: dict) -> dict:
    """
    Parse the raw JSON response from OpenWeatherMap into a clean dictionary.

    The raw API response looks like:
    {
        "name": "London",
        "sys": {"country": "GB", "sunrise": ..., "sunset": ...},
        "main": {"temp": 15.2, "feels_like": 13.1, "humidity": 72, "pressure": 1012},
        "weather": [{"main": "Clouds", "description": "overcast clouds"}],
        "wind": {"speed": 5.1, "deg": 240},
        "visibility": 10000,
        "clouds": {"all": 90},
        ...
    }

    We flatten this into a simple dictionary for easy use throughout the app.
    """
    from datetime import datetime

    parsed = {
        # City & Location info
        "city":        raw_data.get("name", "Unknown"),
        "country":     raw_data.get("sys", {}).get("country", "N/A"),

        # Temperature data (all in Celsius when UNITS = "metric")
        "temperature": raw_data.get("main", {}).get("temp", 0),
        "feels_like":  raw_data.get("main", {}).get("feels_like", 0),
        "temp_min":    raw_data.get("main", {}).get("temp_min", 0),
        "temp_max":    raw_data.get("main", {}).get("temp_max", 0),

        # Atmospheric data
        "humidity":    raw_data.get("main", {}).get("humidity", 0),     # %
        "pressure":    raw_data.get("main", {}).get("pressure", 0),     # hPa

        # Wind data
        "wind_speed":  raw_data.get("wind", {}).get("speed", 0),        # m/s
        "wind_deg":    raw_data.get("wind", {}).get("deg", 0),          # degrees

        # Weather condition (first element of the list)
        "condition":   raw_data.get("weather", [{}])[0].get("main", "N/A"),
        "description": raw_data.get("weather", [{}])[0].get("description", "N/A"),

        # Visibility (in meters, convert to km)
        "visibility":  raw_data.get("visibility", 0) / 1000,

        # Cloud coverage percentage
        "clouds":      raw_data.get("clouds", {}).get("all", 0),

        # Sunrise and sunset times (convert UNIX timestamp → readable time)
        "sunrise": datetime.fromtimestamp(
            raw_data.get("sys", {}).get("sunrise", 0)
        ).strftime("%H:%M"),

        "sunset": datetime.fromtimestamp(
            raw_data.get("sys", {}).get("sunset", 0)
        ).strftime("%H:%M"),

        # Timestamp when the data was fetched
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date":      datetime.now().strftime("%Y-%m-%d"),
    }

    return parsed


# -----------------------------------------------------------------------------
# Function: get_wind_direction
# Purpose : Converts a wind degree (0-360) to a compass direction string
# Params  : degrees (float)
# Returns : String like "N", "SW", "ENE", etc.
# -----------------------------------------------------------------------------
def get_wind_direction(degrees: float) -> str:
    """Convert wind direction in degrees to a compass direction label."""
    directions = [
        "N", "NNE", "NE", "ENE",
        "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW",
        "W", "WNW", "NW", "NNW"
    ]
    # Each sector covers 360/16 = 22.5 degrees
    index = round(degrees / 22.5) % 16
    return directions[index]


# -----------------------------------------------------------------------------
# Function: get_weather_emoji
# Purpose : Returns an emoji representing the current weather condition
# Params  : condition (str) - e.g., "Clear", "Rain", "Snow"
# Returns : Emoji string
# -----------------------------------------------------------------------------
def get_weather_emoji(condition: str) -> str:
    """Return a weather emoji based on the condition string."""
    emoji_map = {
        "Clear":        "☀️",
        "Clouds":       "☁️",
        "Rain":         "🌧️",
        "Drizzle":      "🌦️",
        "Thunderstorm": "⛈️",
        "Snow":         "❄️",
        "Mist":         "🌫️",
        "Fog":          "🌫️",
        "Haze":         "🌫️",
        "Smoke":        "💨",
        "Dust":         "🌪️",
        "Sand":         "🌪️",
        "Ash":          "🌋",
        "Squall":       "💨",
        "Tornado":      "🌪️",
    }
    return emoji_map.get(condition, "🌡️")   # Default emoji if unknown
