# =============================================================================
# analysis.py - Weather Analysis & Trend Module
# =============================================================================
# This module handles all data analysis operations including:
#   - Finding hottest/coldest days
#   - Comparing two cities side-by-side
#   - Temperature trend analysis (weekly/monthly)
#   - Weather alerts detection
#   - Statistical summaries
# =============================================================================

import pandas as pd               # For data analysis
import numpy as np                # For numerical operations
from storage import load_city_data, load_all_data, get_all_cities
from config import TEMP_UNIT_LABEL


# =============================================================================
# ── SECTION 1: Hottest & Coldest Day Analysis ────────────────────────────────
# =============================================================================

def get_hottest_day(city_name: str = None) -> dict:
    """
    Find the day with the highest recorded temperature.

    Args:
        city_name (str, optional): Limit search to a specific city.
                                   If None, searches all cities.

    Returns:
        dict with keys: city, date, temperature, condition
              or empty dict if no data.
    """
    df = load_city_data(city_name) if city_name else load_all_data()

    if df.empty:
        return {}

    # Drop rows where temperature is NaN before finding max
    df_clean = df.dropna(subset=["temperature"])
    if df_clean.empty:
        return {}

    # Find the row with the maximum temperature
    hottest_row = df_clean.loc[df_clean["temperature"].idxmax()]

    return {
        "city":        hottest_row.get("city", "N/A"),
        "date":        str(hottest_row.get("date", "N/A"))[:10],   # YYYY-MM-DD
        "temperature": round(float(hottest_row.get("temperature", 0)), 1),
        "condition":   hottest_row.get("condition", "N/A"),
        "humidity":    hottest_row.get("humidity", "N/A"),
    }


def get_coldest_day(city_name: str = None) -> dict:
    """
    Find the day with the lowest recorded temperature.

    Args:
        city_name (str, optional): Limit search to a specific city.
                                   If None, searches all cities.

    Returns:
        dict with keys: city, date, temperature, condition
              or empty dict if no data.
    """
    df = load_city_data(city_name) if city_name else load_all_data()

    if df.empty:
        return {}

    df_clean = df.dropna(subset=["temperature"])
    if df_clean.empty:
        return {}

    # Find the row with the minimum temperature
    coldest_row = df_clean.loc[df_clean["temperature"].idxmin()]

    return {
        "city":        coldest_row.get("city", "N/A"),
        "date":        str(coldest_row.get("date", "N/A"))[:10],
        "temperature": round(float(coldest_row.get("temperature", 0)), 1),
        "condition":   coldest_row.get("condition", "N/A"),
        "humidity":    coldest_row.get("humidity", "N/A"),
    }


# =============================================================================
# ── SECTION 2: City Comparison ───────────────────────────────────────────────
# =============================================================================

def compare_cities(city1_data: dict, city2_data: dict) -> dict:
    """
    Compare two cities' current weather data side by side.

    Args:
        city1_data (dict): Parsed weather dict for city 1 (from api.py).
        city2_data (dict): Parsed weather dict for city 2 (from api.py).

    Returns:
        dict with comparison results including which city is hotter, etc.
    """
    if not city1_data or not city2_data:
        return {"error": "One or both cities returned no data."}

    c1_temp = city1_data.get("temperature", 0)
    c2_temp = city2_data.get("temperature", 0)
    c1_hum  = city1_data.get("humidity", 0)
    c2_hum  = city2_data.get("humidity", 0)

    # Determine which city is hotter
    if c1_temp > c2_temp:
        hotter_city  = city1_data.get("city")
        temp_diff    = round(c1_temp - c2_temp, 1)
    elif c2_temp > c1_temp:
        hotter_city  = city2_data.get("city")
        temp_diff    = round(c2_temp - c1_temp, 1)
    else:
        hotter_city  = "Both cities"
        temp_diff    = 0.0

    # Determine which city is more humid
    if c1_hum > c2_hum:
        more_humid_city = city1_data.get("city")
    elif c2_hum > c1_hum:
        more_humid_city = city2_data.get("city")
    else:
        more_humid_city = "Both cities"

    return {
        # City 1 details
        "city1":             city1_data.get("city"),
        "city1_country":     city1_data.get("country"),
        "city1_temp":        c1_temp,
        "city1_feels_like":  city1_data.get("feels_like"),
        "city1_humidity":    c1_hum,
        "city1_pressure":    city1_data.get("pressure"),
        "city1_wind":        city1_data.get("wind_speed"),
        "city1_condition":   city1_data.get("condition"),
        "city1_desc":        city1_data.get("description"),

        # City 2 details
        "city2":             city2_data.get("city"),
        "city2_country":     city2_data.get("country"),
        "city2_temp":        c2_temp,
        "city2_feels_like":  city2_data.get("feels_like"),
        "city2_humidity":    c2_hum,
        "city2_pressure":    city2_data.get("pressure"),
        "city2_wind":        city2_data.get("wind_speed"),
        "city2_condition":   city2_data.get("condition"),
        "city2_desc":        city2_data.get("description"),

        # Comparison verdicts
        "hotter_city":       hotter_city,
        "temp_difference":   temp_diff,
        "more_humid_city":   more_humid_city,
    }


# =============================================================================
# ── SECTION 3: Trend Analysis ────────────────────────────────────────────────
# =============================================================================

def get_temperature_trend(city_name: str) -> pd.DataFrame:
    """
    Return a DataFrame of temperature readings over time for a city.
    Used to plot temperature trend graphs.

    Args:
        city_name (str): City to analyse.

    Returns:
        pd.DataFrame with columns: date, temperature, feels_like, temp_min, temp_max
    """
    df = load_city_data(city_name)
    if df.empty:
        return pd.DataFrame()

    # Select only the columns needed for the trend graph
    trend_cols = ["date", "temperature", "feels_like", "temp_min", "temp_max"]
    trend_df = df[trend_cols].dropna(subset=["temperature"]).copy()

    # Group by date and compute daily averages
    # (handles multiple readings per day gracefully)
    trend_df = (
        trend_df
        .groupby("date", as_index=False)
        .agg({
            "temperature": "mean",
            "feels_like":  "mean",
            "temp_min":    "min",
            "temp_max":    "max",
        })
        .sort_values("date")
    )

    # Round all temperature values to 1 decimal place
    for col in ["temperature", "feels_like", "temp_min", "temp_max"]:
        trend_df[col] = trend_df[col].round(1)

    return trend_df


def get_humidity_pressure_data(city_name: str) -> pd.DataFrame:
    """
    Return a DataFrame of humidity and pressure over time for a city.
    Used to plot humidity/pressure bar/line charts.

    Args:
        city_name (str): City to analyse.

    Returns:
        pd.DataFrame with columns: date, humidity, pressure
    """
    df = load_city_data(city_name)
    if df.empty:
        return pd.DataFrame()

    cols_needed = ["date", "humidity", "pressure"]
    hp_df = df[cols_needed].dropna(subset=["humidity", "pressure"]).copy()

    # Daily averages grouped by date
    hp_df = (
        hp_df
        .groupby("date", as_index=False)
        .mean()
        .sort_values("date")
    )

    hp_df["humidity"] = hp_df["humidity"].round(1)
    hp_df["pressure"] = hp_df["pressure"].round(1)

    return hp_df


def get_statistics_summary(city_name: str) -> dict:
    """
    Compute a statistical summary for a city's weather history.

    Args:
        city_name (str): City to summarise.

    Returns:
        dict with avg/min/max for temp, humidity, pressure.
    """
    df = load_city_data(city_name)

    if df.empty:
        return {"error": f"No data found for '{city_name}'."}

    # Filter out rows with missing temperature
    df_clean = df.dropna(subset=["temperature"])

    if df_clean.empty:
        return {"error": "Data found but temperature values are missing."}

    # Most frequent weather condition
    most_common_condition = (
        df_clean["condition"].mode()[0]
        if not df_clean["condition"].empty
        else "N/A"
    )

    return {
        "city":              city_name.title(),
        "total_records":     len(df_clean),

        # Temperature stats
        "avg_temp":          round(df_clean["temperature"].mean(), 1),
        "max_temp":          round(df_clean["temperature"].max(), 1),
        "min_temp":          round(df_clean["temperature"].min(), 1),
        "temp_std":          round(df_clean["temperature"].std(), 1),

        # Humidity stats
        "avg_humidity":      round(df_clean["humidity"].mean(), 1),
        "max_humidity":      round(df_clean["humidity"].max(), 1),
        "min_humidity":      round(df_clean["humidity"].min(), 1),

        # Pressure stats
        "avg_pressure":      round(df_clean["pressure"].mean(), 1),
        "max_pressure":      round(df_clean["pressure"].max(), 1),
        "min_pressure":      round(df_clean["pressure"].min(), 1),

        # Other
        "avg_wind_speed":    round(df_clean["wind_speed"].mean(), 1),
        "most_common_cond":  most_common_condition,

        # Date range
        "first_record":      str(df_clean["date"].min())[:10],
        "last_record":       str(df_clean["date"].max())[:10],
    }


# =============================================================================
# ── SECTION 4: Weather Alerts ────────────────────────────────────────────────
# =============================================================================

# Alert thresholds — these values can be tuned as needed
ALERT_THRESHOLDS = {
    "extreme_heat":    40.0,    # °C
    "high_heat":       35.0,    # °C
    "freezing":         0.0,    # °C
    "high_humidity":   85,      # %
    "low_humidity":    20,      # %
    "high_wind":       15.0,    # m/s (~54 km/h)
    "storm_wind":      25.0,    # m/s (~90 km/h)
    "high_pressure":  1030,     # hPa
    "low_pressure":    980,     # hPa
}


def check_weather_alerts(weather_data: dict) -> list:
    """
    Analyse current weather data and generate alert messages if
    any values exceed defined safety thresholds.

    Args:
        weather_data (dict): Parsed weather data from api.py.

    Returns:
        list of alert strings. Empty list = no alerts.
    """
    alerts = []

    temp      = weather_data.get("temperature", 0)
    humidity  = weather_data.get("humidity", 0)
    wind      = weather_data.get("wind_speed", 0)
    pressure  = weather_data.get("pressure", 1013)
    condition = weather_data.get("condition", "")

    # ── Temperature Alerts ──
    if temp >= ALERT_THRESHOLDS["extreme_heat"]:
        alerts.append(f"🔴 EXTREME HEAT WARNING: {temp}{TEMP_UNIT_LABEL} — Stay indoors!")
    elif temp >= ALERT_THRESHOLDS["high_heat"]:
        alerts.append(f"🟠 HIGH HEAT ALERT: {temp}{TEMP_UNIT_LABEL} — Stay hydrated.")
    elif temp <= ALERT_THRESHOLDS["freezing"]:
        alerts.append(f"🔵 FREEZING TEMPERATURE: {temp}{TEMP_UNIT_LABEL} — Dress warmly!")

    # ── Humidity Alerts ──
    if humidity >= ALERT_THRESHOLDS["high_humidity"]:
        alerts.append(f"💧 HIGH HUMIDITY: {humidity}% — Feels very sticky and humid.")
    elif humidity <= ALERT_THRESHOLDS["low_humidity"]:
        alerts.append(f"🏜️ LOW HUMIDITY: {humidity}% — Air is very dry.")

    # ── Wind Alerts ──
    if wind >= ALERT_THRESHOLDS["storm_wind"]:
        alerts.append(f"🌪️ STORM WARNING: Wind speed {wind} m/s — Dangerous conditions!")
    elif wind >= ALERT_THRESHOLDS["high_wind"]:
        alerts.append(f"💨 HIGH WIND ALERT: {wind} m/s — Secure loose objects.")

    # ── Pressure Alerts ──
    if pressure >= ALERT_THRESHOLDS["high_pressure"]:
        alerts.append(f"📈 HIGH PRESSURE: {pressure} hPa — Stable, dry weather likely.")
    elif pressure <= ALERT_THRESHOLDS["low_pressure"]:
        alerts.append(f"📉 LOW PRESSURE: {pressure} hPa — Stormy weather possible.")

    # ── Condition-Based Alerts ──
    if condition == "Thunderstorm":
        alerts.append("⛈️ THUNDERSTORM ALERT: Avoid outdoor activities!")
    elif condition == "Snow":
        alerts.append("❄️ SNOWFALL ALERT: Roads may be icy — drive carefully.")
    elif condition in ("Tornado",):
        alerts.append("🌪️ TORNADO WARNING: Seek shelter immediately!")

    return alerts


# =============================================================================
# ── SECTION 5: Historical Averages ───────────────────────────────────────────
# =============================================================================

def get_weekly_averages(city_name: str) -> pd.DataFrame:
    """
    Compute weekly average temperature and humidity for a city.

    Returns:
        pd.DataFrame grouped by week with mean values.
    """
    df = load_city_data(city_name)
    if df.empty:
        return pd.DataFrame()

    df_clean = df.dropna(subset=["temperature", "date"]).copy()
    df_clean["week"] = df_clean["date"].dt.to_period("W").astype(str)

    weekly = (
        df_clean
        .groupby("week")
        .agg(
            avg_temp=("temperature", "mean"),
            avg_humidity=("humidity", "mean"),
            avg_pressure=("pressure", "mean"),
        )
        .reset_index()
    )
    weekly["avg_temp"]     = weekly["avg_temp"].round(1)
    weekly["avg_humidity"] = weekly["avg_humidity"].round(1)
    weekly["avg_pressure"] = weekly["avg_pressure"].round(1)

    return weekly


def get_monthly_averages(city_name: str) -> pd.DataFrame:
    """
    Compute monthly average temperature and humidity for a city.

    Returns:
        pd.DataFrame grouped by month with mean values.
    """
    df = load_city_data(city_name)
    if df.empty:
        return pd.DataFrame()

    df_clean = df.dropna(subset=["temperature", "date"]).copy()
    df_clean["month"] = df_clean["date"].dt.to_period("M").astype(str)

    monthly = (
        df_clean
        .groupby("month")
        .agg(
            avg_temp=("temperature", "mean"),
            avg_humidity=("humidity", "mean"),
            avg_pressure=("pressure", "mean"),
        )
        .reset_index()
    )
    monthly["avg_temp"]     = monthly["avg_temp"].round(1)
    monthly["avg_humidity"] = monthly["avg_humidity"].round(1)
    monthly["avg_pressure"] = monthly["avg_pressure"].round(1)

    return monthly
