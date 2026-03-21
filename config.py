# =============================================================================
# config.py - Configuration File
# =============================================================================
# This file stores all global settings like API keys, URLs, and file paths.
# To use this project, replace "YOUR_API_KEY_HERE" with your actual API key
# from https://openweathermap.org/api (Free tier works fine)
# =============================================================================

# -------------------------
# 🔑 OpenWeatherMap API Key
# -------------------------
# Step 1: Go to https://openweathermap.org/
# Step 2: Sign up for a free account
# Step 3: Navigate to "API Keys" in your profile
# Step 4: Copy your API key and paste it below
API_KEY = "b46424e54e3e4cc950fc39c4405cb7e2"

# -------------------------
# 🌐 API Base URL
# -------------------------
# This is the endpoint for current weather data (free tier)
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# -------------------------
# 📁 CSV Storage File Path
# -------------------------
# All fetched weather records will be saved to this file
CSV_FILE = "weather_data.csv"

# -------------------------
# 🌡️ Default Units
# -------------------------
# "metric"   → Celsius (recommended)
# "imperial" → Fahrenheit
# "standard" → Kelvin
UNITS = "metric"
TEMP_UNIT_LABEL = "°C"   # Display label for temperature

# -------------------------
# 🎨 GUI Theme Colors
# -------------------------
BG_COLOR       = "#1a1a2e"   # Dark navy background
FRAME_COLOR    = "#16213e"   # Slightly lighter frame
ACCENT_COLOR   = "#0f3460"   # Deep blue accent
BUTTON_COLOR   = "#e94560"   # Vibrant red-pink buttons
TEXT_COLOR     = "#eaeaea"   # Light grey text
HIGHLIGHT_COLOR= "#00b4d8"   # Cyan highlight
SUCCESS_COLOR  = "#4caf50"   # Green for good states
WARNING_COLOR  = "#ff9800"   # Orange for warnings

FONT_TITLE  = ("Segoe UI", 20, "bold")
FONT_HEADER = ("Segoe UI", 13, "bold")
FONT_BODY   = ("Segoe UI", 11)
FONT_SMALL  = ("Segoe UI", 9)
FONT_MONO   = ("Courier New", 10)
