# =============================================================================
# storage.py - CSV Data Storage Handler
# =============================================================================
# This module handles all file I/O operations for the weather application.
# It saves weather records to a CSV file and loads them back for analysis.
#
# CSV Format (weather_data.csv):
#   timestamp, date, city, country, temperature, feels_like, temp_min,
#   temp_max, humidity, pressure, wind_speed, wind_deg, condition,
#   description, visibility, clouds
# =============================================================================

import csv                        # Built-in CSV reader/writer
import os                         # For file existence checks
import pandas as pd               # For powerful data manipulation
from datetime import datetime     # For date/time operations
from config import CSV_FILE       # Path to the CSV storage file


# The exact column headers used in the CSV file
# These must stay consistent across save/load operations
CSV_COLUMNS = [
    "timestamp", "date", "city", "country",
    "temperature", "feels_like", "temp_min", "temp_max",
    "humidity", "pressure",
    "wind_speed", "wind_deg",
    "condition", "description",
    "visibility", "clouds"
]


# -----------------------------------------------------------------------------
# Function: save_weather
# Purpose : Appends a single weather record to the CSV file
# Params  : weather_data (dict) - The parsed weather dict from api.py
# Returns : True on success, False on failure
# -----------------------------------------------------------------------------
def save_weather(weather_data: dict) -> bool:
    """
    Save a weather record to the CSV file.
    If the file doesn't exist, it creates it with a header row first.

    Args:
        weather_data (dict): Parsed weather data from api.fetch_weather().

    Returns:
        bool: True if saved successfully, False otherwise.
    """
    try:
        # Check if file already exists (to decide whether to write header)
        file_exists = os.path.exists(CSV_FILE)

        # Open file in append mode ('a') so we don't overwrite old records
        # newline='' is required for csv module on Windows to avoid blank rows
        with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)

            # Write header only if this is a brand-new file
            if not file_exists:
                writer.writeheader()
                print(f"[INFO] Created new CSV file: {CSV_FILE}")

            # Build the row from weather_data, using only the columns we need
            # .get(col, "") uses empty string if a key is missing (safe default)
            row = {col: weather_data.get(col, "") for col in CSV_COLUMNS}
            writer.writerow(row)

        print(f"[INFO] Weather data for '{weather_data.get('city')}' saved successfully.")
        return True

    except PermissionError:
        print(f"[ERROR] Permission denied writing to '{CSV_FILE}'.")
        print("        Close the file if it's open in Excel, then try again.")
        return False

    except Exception as e:
        print(f"[ERROR] Failed to save weather data: {e}")
        return False


# -----------------------------------------------------------------------------
# Function: load_all_data
# Purpose : Loads the entire CSV file into a Pandas DataFrame
# Returns : DataFrame with all historical records, or empty DataFrame
# -----------------------------------------------------------------------------
def load_all_data() -> pd.DataFrame:
    """
    Load all saved weather records from the CSV file into a DataFrame.

    Returns:
        pd.DataFrame: All records, or empty DataFrame if no file/data found.
    """
    # Check if the storage file exists at all
    if not os.path.exists(CSV_FILE):
        print(f"[INFO] No data file found at '{CSV_FILE}'. Start fetching weather!")
        return pd.DataFrame(columns=CSV_COLUMNS)

    try:
        df = pd.read_csv(CSV_FILE, encoding="utf-8")

        # Ensure the DataFrame has all expected columns
        # (handles old/partial files gracefully)
        for col in CSV_COLUMNS:
            if col not in df.columns:
                df[col] = None

        # Convert numeric columns to proper numeric types
        # errors='coerce' turns unparseable values to NaN instead of crashing
        numeric_cols = [
            "temperature", "feels_like", "temp_min", "temp_max",
            "humidity", "pressure", "wind_speed", "visibility", "clouds"
        ]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Ensure date column is a proper datetime type for analysis
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        if df.empty:
            print("[INFO] CSV file exists but contains no records.")

        return df

    except pd.errors.EmptyDataError:
        # File exists but is completely empty (just a header or nothing)
        print("[INFO] CSV file is empty.")
        return pd.DataFrame(columns=CSV_COLUMNS)

    except Exception as e:
        print(f"[ERROR] Failed to load weather data: {e}")
        return pd.DataFrame(columns=CSV_COLUMNS)


# -----------------------------------------------------------------------------
# Function: load_city_data
# Purpose : Loads records for a specific city only
# Params  : city_name (str)
# Returns : Filtered DataFrame for that city
# -----------------------------------------------------------------------------
def load_city_data(city_name: str) -> pd.DataFrame:
    """
    Load all saved records for a specific city.

    Args:
        city_name (str): The city to filter by (case-insensitive).

    Returns:
        pd.DataFrame: Records for that city, sorted by date ascending.
    """
    df = load_all_data()

    if df.empty:
        return df

    # Case-insensitive city name match
    city_df = df[df["city"].str.lower() == city_name.strip().lower()]

    if city_df.empty:
        print(f"[INFO] No stored data found for city: '{city_name}'")

    return city_df.sort_values("date").reset_index(drop=True)


# -----------------------------------------------------------------------------
# Function: get_all_cities
# Purpose : Returns a sorted list of all unique city names in storage
# Returns : List of city name strings
# -----------------------------------------------------------------------------
def get_all_cities() -> list:
    """Return a list of all unique city names stored in the CSV."""
    df = load_all_data()
    if df.empty or "city" not in df.columns:
        return []
    return sorted(df["city"].dropna().unique().tolist())


# -----------------------------------------------------------------------------
# Function: clear_all_data
# Purpose : Deletes the CSV file (for testing/resetting purposes)
# Returns : True if deleted, False otherwise
# -----------------------------------------------------------------------------
def clear_all_data() -> bool:
    """Delete the CSV data file. Use with caution — data cannot be recovered."""
    if os.path.exists(CSV_FILE):
        try:
            os.remove(CSV_FILE)
            print(f"[INFO] Data file '{CSV_FILE}' has been deleted.")
            return True
        except Exception as e:
            print(f"[ERROR] Could not delete file: {e}")
            return False
    else:
        print("[INFO] No data file exists to delete.")
        return False


# -----------------------------------------------------------------------------
# Function: get_record_count
# Purpose : Returns the total number of records stored in the CSV
# -----------------------------------------------------------------------------
def get_record_count() -> int:
    """Return the total number of weather records in the CSV file."""
    df = load_all_data()
    return len(df)


# -----------------------------------------------------------------------------
# Function: check_duplicate
# Purpose : Checks if a record for the same city on the same date already exists
#           (prevents excessive duplicate entries on the same day)
# Params  : city (str), date (str in 'YYYY-MM-DD' format)
# Returns : True if duplicate found, False otherwise
# -----------------------------------------------------------------------------
def check_duplicate(city: str, date: str) -> bool:
    """
    Check if a weather record for a city on a given date already exists.
    Used to avoid flooding the CSV with identical daily records.
    """
    df = load_all_data()
    if df.empty:
        return False

    # Normalize for comparison
    date_check = pd.to_datetime(date, errors="coerce")
    matches = df[
        (df["city"].str.lower() == city.lower()) &
        (df["date"] == date_check)
    ]
    return not matches.empty
