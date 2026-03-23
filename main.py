# =============================================================================
# main.py - Application Entry Point
# =============================================================================
# This is the MAIN file to run the Weather Monitoring & Analysis System.
#
# HOW TO RUN:
#   python main.py          → Launches the full GUI application
#   python main.py --cli    → Launches the CLI (text-based) version
#
# PREREQUISITES:
#   1. Install dependencies:
#      pip install requests pandas matplotlib
#
#   2. Get your free API key from https://openweathermap.org/api
#
#   3. Open config.py and replace "YOUR_API_KEY_HERE" with your key
# =============================================================================

import sys
import os

# Add the project directory to Python path (good practice for imports)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# =============================================================================
# ── Dependency Check ─────────────────────────────────────────────────────────
# =============================================================================

def check_dependencies():
    """
    Verify that all required third-party packages are installed.
    If any are missing, print instructions and exit.
    """
    missing = []
    packages = {
        "requests":    "requests",
        "pandas":      "pandas",
        "matplotlib":  "matplotlib",
    }

    for module_name, pip_name in packages.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(pip_name)

    if missing:
        print("\n" + "="*55)
        print("  ❌  Missing Required Packages")
        print("="*55)
        print(f"\n  The following packages are not installed:\n")
        for pkg in missing:
            print(f"    •  {pkg}")
        print(f"\n  Install them by running:\n")
        print(f"    pip install {' '.join(missing)}\n")
        print("="*55 + "\n")
        sys.exit(1)


# =============================================================================
# ── GUI Launcher / Theme Selector ────────────────────────────────────────────
# =============================================================================

def _show_theme_selector():
    """
    Show a small Tkinter dialog that asks the user which GUI theme to use.
    Returns 'classic' or 'modern'. Returns None if the window is closed.
    """
    import tkinter as tk
    from tkinter import ttk

    choice = {"value": None}

    sel = tk.Tk()
    sel.title("Weather Monitor — Choose Interface")
    sel.resizable(False, False)
    sel.configure(bg="#0d1117")

    # Centre on screen
    sel.update_idletasks()
    sw = sel.winfo_screenwidth()
    sh = sel.winfo_screenheight()
    w, h = 480, 320
    sel.geometry(f"{w}x{h}+{sw//2 - w//2}+{sh//2 - h//2}")

    # ── Title ──────────────────────────────────────────────────────────────
    tk.Label(sel,
             text="⛅  Weather Monitor",
             font=("Segoe UI", 18, "bold"),
             bg="#0d1117", fg="#58a6ff"
             ).pack(pady=(28, 4))

    tk.Label(sel,
             text="Choose which interface to launch:",
             font=("Segoe UI", 11),
             bg="#0d1117", fg="#8b949e"
             ).pack(pady=(0, 20))

    # ── Two option buttons ─────────────────────────────────────────────────
    btn_frame = tk.Frame(sel, bg="#0d1117")
    btn_frame.pack()

    def _pick(v):
        choice["value"] = v
        sel.destroy()

    # Classic button
    classic_btn = tk.Frame(btn_frame, bg="#161b22",
                            padx=20, pady=18, cursor="hand2")
    classic_btn.grid(row=0, column=0, padx=12)
    tk.Label(classic_btn, text="🎨", font=("Segoe UI", 26),
             bg="#161b22", fg="#e6edf3").pack()
    tk.Label(classic_btn, text="Classic",
             font=("Segoe UI", 13, "bold"),
             bg="#161b22", fg="#e6edf3").pack(pady=(4, 2))
    tk.Label(classic_btn, text="Original dark-blue\nnotebook-tab UI",
             font=("Segoe UI", 9), bg="#161b22", fg="#8b949e",
             justify="center").pack()
    for w in [classic_btn] + classic_btn.winfo_children():
        w.bind("<Button-1>", lambda e: _pick("classic"))
        w.bind("<Enter>",    lambda e: classic_btn.configure(bg="#1f6feb"))
        w.bind("<Leave>",    lambda e: classic_btn.configure(bg="#161b22"))

    # Modern button
    modern_btn = tk.Frame(btn_frame, bg="#161b22",
                           padx=20, pady=18, cursor="hand2")
    modern_btn.grid(row=0, column=1, padx=12)
    tk.Label(modern_btn, text="✨", font=("Segoe UI", 26),
             bg="#161b22", fg="#e6edf3").pack()
    tk.Label(modern_btn, text="Modern",
             font=("Segoe UI", 13, "bold"),
             bg="#161b22", fg="#e6edf3").pack(pady=(4, 2))
    tk.Label(modern_btn, text="Sidebar nav, tile cards\n& animated loader",
             font=("Segoe UI", 9), bg="#161b22", fg="#8b949e",
             justify="center").pack()
    for w in [modern_btn] + modern_btn.winfo_children():
        w.bind("<Button-1>", lambda e: _pick("modern"))
        w.bind("<Enter>",    lambda e: modern_btn.configure(bg="#1f6feb"))
        w.bind("<Leave>",    lambda e: modern_btn.configure(bg="#161b22"))

    # Refresh children after grid
    sel.update_idletasks()
    for child in classic_btn.winfo_children():
        child.bind("<Button-1>", lambda e: _pick("classic"))
        child.bind("<Enter>",    lambda e: classic_btn.configure(bg="#1f6feb"))
        child.bind("<Leave>",    lambda e: classic_btn.configure(bg="#161b22"))
    for child in modern_btn.winfo_children():
        child.bind("<Button-1>", lambda e: _pick("modern"))
        child.bind("<Enter>",    lambda e: modern_btn.configure(bg="#1f6feb"))
        child.bind("<Leave>",    lambda e: modern_btn.configure(bg="#161b22"))

    tk.Label(sel,
             text="You can always relaunch to switch themes.",
             font=("Segoe UI", 8),
             bg="#0d1117", fg="#484f58"
             ).pack(side="bottom", pady=12)

    sel.protocol("WM_DELETE_WINDOW", sel.destroy)
    sel.mainloop()
    return choice["value"]


# =============================================================================
# ── GUI Mode ─────────────────────────────────────────────────────────────────
# =============================================================================

def launch_gui():
    """Show the theme selector, then launch the chosen GUI."""
    import tkinter as tk

    theme = _show_theme_selector()

    if theme is None:
        print("[INFO] No theme selected — exiting.")
        return

    print(f"[INFO] Launching {theme.capitalize()} UI...")

    root = tk.Tk()

    def on_close():
        print("[INFO] Application closed by user.")
        root.quit()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    if theme == "modern":
        from gui_modern import ModernWeatherApp
        ModernWeatherApp(root)
    else:
        from gui import WeatherApp
        WeatherApp(root)

    root.mainloop()


# =============================================================================
# ── CLI Mode ─────────────────────────────────────────────────────────────────
# =============================================================================

def launch_cli():
    """
    Launch the text-based command-line interface.
    Useful for environments without a display or for quick testing.
    """
    from api      import fetch_weather, get_weather_emoji, get_wind_direction, \
                         fetch_historical_weather
    from storage  import save_weather, get_all_cities, get_record_count
    from analysis import (
        get_hottest_day, get_coldest_day, compare_cities,
        get_statistics_summary, check_weather_alerts
    )
    from config   import TEMP_UNIT_LABEL, API_KEY

    def print_banner():
        print("\n" + "="*55)
        print("  🌦️   Weather Monitoring & Analysis System")
        print("  CLI Edition")
        print("="*55)

    def print_weather(data):
        """Pretty-print weather data to the terminal."""
        emoji = get_weather_emoji(data.get("condition", ""))
        wind_dir = get_wind_direction(data.get("wind_deg", 0))
        print(f"""
  ┌─────────────────────────────────────────┐
  │  {emoji}  {data['city']}, {data['country']}
  ├─────────────────────────────────────────┤
  │  Condition   : {data['condition']} — {data['description'].title()}
  │  Temperature : {data['temperature']:.1f}{TEMP_UNIT_LABEL}  (Feels like {data['feels_like']:.1f}{TEMP_UNIT_LABEL})
  │  Min / Max   : {data['temp_min']:.1f}{TEMP_UNIT_LABEL} / {data['temp_max']:.1f}{TEMP_UNIT_LABEL}
  │  Humidity    : {data['humidity']} %
  │  Pressure    : {data['pressure']} hPa
  │  Wind        : {data['wind_speed']} m/s  {wind_dir}
  │  Visibility  : {data['visibility']:.1f} km
  │  Cloud Cover : {data['clouds']} %
  │  Sunrise     : {data['sunrise']}   Sunset: {data['sunset']}
  │  Recorded    : {data['timestamp']}
  └─────────────────────────────────────────┘""")

        # Check for alerts
        alerts = check_weather_alerts(data)
        if alerts:
            print("\n  ⚠️  WEATHER ALERTS:")
            for alert in alerts:
                print(f"     {alert}")

    def main_menu():
        print_banner()

        if API_KEY == "YOUR_API_KEY_HERE":
            print("\n  ⚠️  WARNING: API key not set!")
            print("  Open config.py and replace 'YOUR_API_KEY_HERE'")
            print(f"  Total stored records: {get_record_count()}\n")

        while True:
            print(f"""
  ─── MAIN MENU ───────────────────────────
  [1]  Get Current Weather
  [2]  Compare Two Cities
  [3]  Show Hottest / Coldest Day
  [4]  City Statistics Summary
  [5]  List All Stored Cities
  [6]  Historical Weather by Date
  [0]  Exit
  ─────────────────────────────────────────""")

            choice = input("  Enter choice: ").strip()

            # ── Option 1: Get Current Weather ──
            if choice == "1":
                city = input("\n  Enter city name: ").strip()
                if not city:
                    print("  [!] City name cannot be empty.")
                    continue

                print(f"\n  ⏳ Fetching weather for '{city}'...")
                data = fetch_weather(city)

                if data:
                    print_weather(data)
                    save_choice = input("\n  Save to CSV? (y/n): ").strip().lower()
                    if save_choice == "y":
                        save_weather(data)
                        print(f"  ✅ Saved! Total records: {get_record_count()}")
                else:
                    print("  ❌ Failed to fetch weather. Check city name and API key.")

            # ── Option 2: Compare Cities ──
            elif choice == "2":
                city1 = input("\n  Enter city 1: ").strip()
                city2 = input("  Enter city 2: ").strip()

                if not city1 or not city2:
                    print("  [!] Both city names are required.")
                    continue

                print(f"\n  ⏳ Fetching data for both cities...")
                data1 = fetch_weather(city1)
                data2 = fetch_weather(city2)

                if data1 and data2:
                    result = compare_cities(data1, data2)
                    print(f"""
  ┌─ COMPARISON: {result['city1']} vs {result['city2']} ─────────────
  │
  │  {result['city1']} ({result['city1_country']})
  │     Temperature : {result['city1_temp']:.1f}{TEMP_UNIT_LABEL}
  │     Humidity    : {result['city1_humidity']} %
  │     Pressure    : {result['city1_pressure']} hPa
  │     Condition   : {result['city1_condition']}
  │
  │  {result['city2']} ({result['city2_country']})
  │     Temperature : {result['city2_temp']:.1f}{TEMP_UNIT_LABEL}
  │     Humidity    : {result['city2_humidity']} %
  │     Pressure    : {result['city2_pressure']} hPa
  │     Condition   : {result['city2_condition']}
  │
  │  🏆 Warmer city  : {result['hotter_city']} (+{result['temp_difference']}{TEMP_UNIT_LABEL})
  │  💧 More humid   : {result['more_humid_city']}
  └───────────────────────────────────────────""")
                else:
                    print("  ❌ Could not fetch one or both cities.")

            # ── Option 3: Hottest / Coldest ──
            elif choice == "3":
                city_filter = input(
                    "\n  Enter city to filter (or press Enter for all): "
                ).strip() or None

                hot  = get_hottest_day(city_filter)
                cold = get_coldest_day(city_filter)

                scope = f"'{city_filter}'" if city_filter else "all cities"

                if hot:
                    print(f"\n  🔥 HOTTEST ({scope}): {hot['city']} — "
                          f"{hot['temperature']}{TEMP_UNIT_LABEL} on {hot['date']}")
                else:
                    print(f"\n  ❌ No data for {scope}")

                if cold:
                    print(f"  🧊 COLDEST ({scope}): {cold['city']} — "
                          f"{cold['temperature']}{TEMP_UNIT_LABEL} on {cold['date']}")
                else:
                    print(f"  ❌ No coldest data for {scope}")

            # ── Option 4: Statistics ──
            elif choice == "4":
                city = input("\n  Enter city name: ").strip()
                if not city:
                    print("  [!] City name required.")
                    continue

                stats = get_statistics_summary(city)
                if "error" in stats:
                    print(f"  ❌ {stats['error']}")
                else:
                    print(f"""
  ─── STATISTICS: {stats['city']} ────────────────
  Records       : {stats['total_records']}
  Date Range    : {stats['first_record']} → {stats['last_record']}

  Temperature   : avg {stats['avg_temp']}{TEMP_UNIT_LABEL}  |  min {stats['min_temp']}{TEMP_UNIT_LABEL}  |  max {stats['max_temp']}{TEMP_UNIT_LABEL}
  Humidity      : avg {stats['avg_humidity']}%  |  min {stats['min_humidity']}%  |  max {stats['max_humidity']}%
  Pressure      : avg {stats['avg_pressure']} hPa
  Wind Speed    : avg {stats['avg_wind_speed']} m/s
  Common Cond.  : {stats['most_common_cond']}
  ─────────────────────────────────────────""")

            # ── Option 5: List Cities ──
            elif choice == "5":
                cities = get_all_cities()
                if cities:
                    print(f"\n  🏙️  Cities with stored data ({len(cities)}):")
                    for i, c in enumerate(cities, 1):
                        print(f"    {i:3}.  {c}")
                else:
                    print("\n  📭 No weather data stored yet.")

            # ── Option 6: Historical Weather by Date ──
            elif choice == "6":
                city = input("\n  Enter city name (optionally: City, CC  e.g. Paris, FR): ").strip()
                if not city:
                    print("  [!] City name cannot be empty.")
                    continue
                date = input("  Enter date (YYYY-MM-DD, must be a past date): ").strip()
                if not date:
                    print("  [!] Date cannot be empty.")
                    continue

                print(f"\n  ⏳ Fetching historical weather for '{city}' on {date}…")
                try:
                    result = fetch_historical_weather(city, date)
                    if result is None:
                        print("  ❌ Could not retrieve data. "
                              "Check city spelling, add country code, "
                              "or try a different date.")
                    else:
                        def _fv(v, unit):
                            return f"{v:.1f} {unit}" if v is not None else "N/A"

                        print(f"""
  ┌─────────────────────────────────────────────┐
  │  📅  Historical Weather
  ├─────────────────────────────────────────────┤
  │  City          : {result['city']}, {result['country']}
  │  Date          : {result['date']}
  ├─────────────────────────────────────────────┤
  │  🔺 Max Temp   : {_fv(result['temp_max'], '°C')}
  │  🔻 Min Temp   : {_fv(result['temp_min'], '°C')}
  │  🌡️  Avg Temp  : {_fv(result['temp_avg'], '°C')}
  ├─────────────────────────────────────────────┤
  │  🌧️  Precipitation : {_fv(result['precipitation'], 'mm')}
  │  💨 Max Wind       : {_fv(result['windspeed_max'], 'km/h')}
  │  ☀️  Sunshine       : {_fv(result['sunshine_hours'], 'hrs')}
  └─────────────────────────────────────────────┘""")
                except ValueError as e:
                    print(f"  ❌ Invalid input: {e}")

            # ── Option 0: Exit ──
            elif choice == "0":
                print("\n  Goodbye! 👋\n")
                sys.exit(0)

            else:
                print("\n  [!] Invalid choice. Enter 0-6.")

    main_menu()


# =============================================================================
# ── Entry Point ───────────────────────────────────────────────────────────────
# =============================================================================

if __name__ == "__main__":
    # First check all packages are installed
    check_dependencies()

    # Choose mode based on command-line argument
    if "--cli" in sys.argv:
        launch_cli()
    else:
        launch_gui()
