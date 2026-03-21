# 🌦️ Weather Monitoring & Analysis System

A complete Python desktop application for real-time weather monitoring, data storage, trend analysis, and visualisation — built with **Tkinter**, **Matplotlib**, **Pandas**, and the **OpenWeatherMap API**.

---

## 📁 Project Structure

```
PPS_Weather_Project/
│
├── main.py            ← ▶ ENTRY POINT — run this file
├── config.py          ← ⚙️  Settings: API key, colors, file paths
├── api.py             ← 🌐 API calls and JSON parsing
├── storage.py         ← 💾 CSV read/write operations
├── analysis.py        ← 📊 Trend analysis, stats, alerts
├── charts.py          ← 📈 Matplotlib chart generation
├── gui.py             ← 🖥️  Tkinter GUI (5 tabs)
│
├── weather_data.csv   ← 📋 Sample data (auto-created on first save)
├── requirements.txt   ← 📦 Python dependencies
└── README.md          ← 📖 This file
```

---

## ⚡ Quick Start

### Step 1 — Install Python
Make sure Python 3.8 or higher is installed.  
Download: https://www.python.org/downloads/

### Step 2 — Install Dependencies
```bash
pip install -r requirements.txt
```
Or manually:
```bash
pip install requests pandas matplotlib
```

### Step 3 — Get a Free API Key
1. Go to https://openweathermap.org/
2. Click **Sign Up** (free account)
3. Go to **My Profile → API Keys**
4. Copy your API key

### Step 4 — Add Your API Key
Open `config.py` and replace:
```python
API_KEY = "YOUR_API_KEY_HERE"
```
with your actual key:
```python
API_KEY = "abc123youractualkey456"
```

### Step 5 — Run the Application
```bash
# Launch GUI (recommended)
python main.py

# Launch CLI (text-based mode)
python main.py --cli
```

---

## 🖥️ GUI Features

The application has **5 tabs**:

| Tab | Feature |
|-----|---------|
| 🌤️ **Current Weather** | Fetch live weather, view all stats, see alerts |
| 🌍 **Compare Cities** | Side-by-side comparison of two cities |
| 📈 **Trends & Charts** | Temperature trend, humidity/pressure charts, monthly averages |
| 📊 **Analysis** | Statistics summary, hottest/coldest day, city list |
| 📋 **Data Log** | Browse all stored CSV records with live filtering |

---

## 📋 CSV Format

The `weather_data.csv` file stores all saved weather records:

| Column | Description |
|--------|-------------|
| `timestamp` | Full datetime when data was fetched |
| `date` | Date in YYYY-MM-DD format |
| `city` | City name |
| `country` | 2-letter country code |
| `temperature` | Temperature in °C |
| `feels_like` | Feels-like temperature in °C |
| `temp_min` | Minimum temperature °C |
| `temp_max` | Maximum temperature °C |
| `humidity` | Relative humidity % |
| `pressure` | Atmospheric pressure hPa |
| `wind_speed` | Wind speed in m/s |
| `wind_deg` | Wind direction in degrees |
| `condition` | Main condition (Clear, Rain, etc.) |
| `description` | Detailed description |
| `visibility` | Visibility in km |
| `clouds` | Cloud coverage % |

---

## 🔧 Configuration (config.py)

| Setting | Default | Description |
|---------|---------|-------------|
| `API_KEY` | `"YOUR_API_KEY_HERE"` | **Replace with your key** |
| `UNITS` | `"metric"` | `metric`=°C, `imperial`=°F |
| `CSV_FILE` | `"weather_data.csv"` | Storage file path |

---

## ⚠️ Weather Alerts

The system automatically alerts you when:

| Condition | Threshold |
|-----------|-----------|
| 🔴 Extreme Heat | ≥ 40°C |
| 🟠 High Heat | ≥ 35°C |
| 🔵 Freezing | ≤ 0°C |
| 💧 High Humidity | ≥ 85% |
| 💨 High Wind | ≥ 15 m/s |
| 🌪️ Storm Wind | ≥ 25 m/s |
| ⛈️ Thunderstorm | Condition-based |

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| `API key not configured` | Open `config.py`, replace the placeholder key |
| `City not found` | Check spelling — use English city names |
| `No internet connection` | Check your network/firewall settings |
| `No stored data` | Fetch weather for a city, then click "Save to CSV" |
| Charts not showing | Make sure data is saved for the city you're querying |
| `tkinter not found` (Linux) | Run: `sudo apt-get install python3-tk` |

---

## 📦 Tech Stack

| Library | Version | Purpose |
|---------|---------|---------|
| `requests` | ≥ 2.28 | HTTP API calls |
| `pandas` | ≥ 1.5 | Data storage and analysis |
| `matplotlib` | ≥ 3.6 | Charts and graphs |
| `tkinter` | built-in | GUI framework |

---

## 🎓 Learning Concepts Covered

- ✅ REST API calls with `requests`
- ✅ JSON parsing (nested dictionaries)
- ✅ CSV file read/write with `csv` and `pandas`
- ✅ Exception handling (network, file I/O, invalid input)
- ✅ Modular Python project structure
- ✅ Tkinter GUI with tabs, frames, and widgets
- ✅ Matplotlib embedded in Tkinter (FigureCanvasTkAgg)
- ✅ Multi-threading (API calls in background thread)
- ✅ Data analysis with pandas (groupby, aggregation, statistics)

---

*Built with Python 3 • OpenWeatherMap Free API*
