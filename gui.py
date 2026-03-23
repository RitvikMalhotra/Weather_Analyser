# =============================================================================
# gui.py - Tkinter GUI Interface
# =============================================================================
# This module builds the complete graphical user interface for the
# Weather Monitoring & Analysis System using Tkinter.
#
# The GUI is organized into tabs:
#   Tab 1 - 🌤️  Current Weather   → Fetch & display real-time weather
#   Tab 2 - 🌍  Compare Cities    → Side-by-side city comparison
#   Tab 3 - 📈  Trends & Charts   → Temperature/humidity/pressure graphs
#   Tab 4 - 📊  Analysis          → Stats, hottest/coldest, averages
#   Tab 5 - 📋  Data Log          → View all stored CSV records
# =============================================================================

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading                 # For running API calls without freezing the UI
from datetime import datetime
import pandas as pd              # For data operations in the Data Log tab

# Import our custom modules
from api      import (fetch_weather, fetch_weather_by_coords,
                       get_all_city_matches, get_weather_emoji, get_wind_direction,
                       fetch_historical_weather)
from storage  import save_weather, load_all_data, get_all_cities, get_record_count
from analysis import (
    get_hottest_day, get_coldest_day, compare_cities,
    get_temperature_trend, get_humidity_pressure_data,
    get_statistics_summary, check_weather_alerts,
    get_monthly_averages
)
from charts import (
    plot_temperature_trend, plot_humidity_pressure,
    plot_city_comparison, plot_monthly_averages
)
from config import *


# =============================================================================
# ── WeatherApp Class ──────────────────────────────────────────────────────────
# =============================================================================

class WeatherApp:
    """
    Main application class. Creates and manages the entire GUI window.
    All tabs and their widgets are set up in the __init__ method.
    """

    def __init__(self, root: tk.Tk):
        """
        Initialize the Weather App GUI.

        Args:
            root (tk.Tk): The main Tkinter window instance.
        """
        self.root = root
        self._setup_window()
        self._apply_styles()
        self._build_header()
        self._build_status_bar()   # Build status bar BEFORE tabs so status_var exists
        self._build_tabs()

        # Keep track of the last fetched weather data (used across tabs)
        self.last_weather_data = None
        self.last_compare_result = None
        # Track last successfully fetched city name (for auto-populating other tabs)
        self.last_fetched_city = ""

    # -------------------------------------------------------------------------
    # Window Setup
    # -------------------------------------------------------------------------

    def _setup_window(self):
        """Configure the main window properties."""
        self.root.title("🌦️  Weather Monitoring & Analysis System")
        self.root.geometry("1050x720")
        self.root.minsize(900, 620)
        self.root.configure(bg=BG_COLOR)
        # Center the window on screen
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth()  // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"+{x}+{y}")

    def _apply_styles(self):
        """Apply ttk styles for consistent dark theme across all widgets."""
        style = ttk.Style()
        style.theme_use("clam")

        # Notebook (tab container)
        style.configure("TNotebook",
                         background=BG_COLOR, borderwidth=0)
        style.configure("TNotebook.Tab",
                         background=ACCENT_COLOR, foreground=TEXT_COLOR,
                         font=FONT_BODY, padding=(12, 6))
        style.map("TNotebook.Tab",
                  background=[("selected", BUTTON_COLOR)],
                  foreground=[("selected", "#ffffff")])

        # Frames
        style.configure("TFrame",   background=BG_COLOR)
        style.configure("Card.TFrame", background=FRAME_COLOR, relief="flat")

        # Labels
        style.configure("TLabel",
                         background=BG_COLOR, foreground=TEXT_COLOR,
                         font=FONT_BODY)
        style.configure("Header.TLabel",
                         background=BG_COLOR, foreground=HIGHLIGHT_COLOR,
                         font=FONT_HEADER)
        style.configure("Card.TLabel",
                         background=FRAME_COLOR, foreground=TEXT_COLOR,
                         font=FONT_BODY)
        style.configure("Value.TLabel",
                         background=FRAME_COLOR, foreground=HIGHLIGHT_COLOR,
                         font=("Segoe UI", 14, "bold"))

        # Buttons
        style.configure("TButton",
                         background=BUTTON_COLOR, foreground="#ffffff",
                         font=FONT_BODY, borderwidth=0, focusthickness=0,
                         padding=(10, 6))
        style.map("TButton",
                  background=[("active", "#c73652"), ("pressed", "#a52d43")])

        style.configure("Secondary.TButton",
                         background=ACCENT_COLOR, foreground=TEXT_COLOR,
                         font=FONT_SMALL)
        style.map("Secondary.TButton",
                  background=[("active", "#1a5090")])

        # Entry fields
        style.configure("TEntry",
                         fieldbackground=ACCENT_COLOR, foreground=TEXT_COLOR,
                         insertcolor=TEXT_COLOR, font=FONT_BODY,
                         borderwidth=1)

        # Treeview (for data table)
        style.configure("Treeview",
                         background=FRAME_COLOR, foreground=TEXT_COLOR,
                         fieldbackground=FRAME_COLOR, font=FONT_SMALL,
                         rowheight=22)
        style.configure("Treeview.Heading",
                         background=ACCENT_COLOR, foreground=HIGHLIGHT_COLOR,
                         font=("Segoe UI", 9, "bold"))
        style.map("Treeview",
                  background=[("selected", BUTTON_COLOR)])

        # Separators
        style.configure("TSeparator", background=ACCENT_COLOR)

        # Scrollbar
        style.configure("TScrollbar",
                         background=ACCENT_COLOR, troughcolor=BG_COLOR,
                         arrowcolor=TEXT_COLOR)

    # -------------------------------------------------------------------------
    # Header
    # -------------------------------------------------------------------------

    def _build_header(self):
        """Build the top header bar with title and clock."""
        header = tk.Frame(self.root, bg=ACCENT_COLOR, height=60)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        # App title
        title_lbl = tk.Label(
            header,
            text="🌦️   Weather Monitoring & Analysis System",
            font=FONT_TITLE, bg=ACCENT_COLOR, fg=TEXT_COLOR
        )
        title_lbl.pack(side="left", padx=20, pady=10)

        # Live clock (top-right)
        self.clock_var = tk.StringVar()
        clock_lbl = tk.Label(
            header,
            textvariable=self.clock_var,
            font=FONT_SMALL, bg=ACCENT_COLOR, fg=HIGHLIGHT_COLOR
        )
        clock_lbl.pack(side="right", padx=20)
        self._update_clock()

    def _update_clock(self):
        """Update the clock label every second."""
        now = datetime.now().strftime("%A, %d %B %Y   %H:%M:%S")
        self.clock_var.set(now)
        self.root.after(1000, self._update_clock)

    # -------------------------------------------------------------------------
    # Tabs
    # -------------------------------------------------------------------------

    def _build_tabs(self):
        """Create the main notebook widget and all its tabs."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(8, 4))

        # Create each tab frame
        self.tab_current  = ttk.Frame(self.notebook)
        self.tab_compare  = ttk.Frame(self.notebook)
        self.tab_trends   = ttk.Frame(self.notebook)
        self.tab_analysis = ttk.Frame(self.notebook)
        self.tab_data     = ttk.Frame(self.notebook)
        self.tab_history  = ttk.Frame(self.notebook)

        # Add tabs to notebook
        self.notebook.add(self.tab_current,  text="  🌤️  Current Weather  ")
        self.notebook.add(self.tab_compare,  text="  🌍  Compare Cities  ")
        self.notebook.add(self.tab_trends,   text="  📈  Trends & Charts  ")
        self.notebook.add(self.tab_analysis, text="  📊  Analysis  ")
        self.notebook.add(self.tab_data,     text="  📋  Data Log  ")
        self.notebook.add(self.tab_history,  text="  📅  Historical  ")

        # Build each tab content
        self._build_current_weather_tab()
        self._build_compare_tab()
        self._build_trends_tab()
        self._build_analysis_tab()
        self._build_data_tab()
        self._build_history_tab()

    # =========================================================================
    # ── TAB 1: Current Weather ────────────────────────────────────────────────
    # =========================================================================

    def _build_current_weather_tab(self):
        """Build the Current Weather tab layout."""
        tab = self.tab_current
        tab.configure(style="TFrame")

        # ── Input Row ──
        input_frame = tk.Frame(tab, bg=FRAME_COLOR, pady=10)
        input_frame.pack(fill="x", padx=15, pady=(10, 5))

        tk.Label(input_frame, text="🏙️  City Name:",
                 font=FONT_HEADER, bg=FRAME_COLOR, fg=HIGHLIGHT_COLOR
                 ).pack(side="left", padx=(15, 8))

        self.city_var = tk.StringVar()
        city_entry = ttk.Entry(input_frame, textvariable=self.city_var,
                               font=FONT_BODY, width=28)
        city_entry.pack(side="left", padx=(0, 10), ipady=4)
        city_entry.bind("<Return>", lambda e: self._fetch_current_weather())

        # Placeholder hint text in the entry box
        city_entry.insert(0, "e.g. Hyderabad  or  Hyderabad, IN")
        city_entry.config(foreground="#666688")
        def _on_focus_in(e):
            if city_entry.get() == "e.g. Hyderabad  or  Hyderabad, IN":
                city_entry.delete(0, "end")
                city_entry.config(foreground=TEXT_COLOR)
        def _on_focus_out(e):
            if not city_entry.get().strip():
                city_entry.insert(0, "e.g. Hyderabad  or  Hyderabad, IN")
                city_entry.config(foreground="#666688")
        city_entry.bind("<FocusIn>",  _on_focus_in)
        city_entry.bind("<FocusOut>", _on_focus_out)

        self.fetch_btn = ttk.Button(input_frame, text="⚡  Get Weather",
                                    command=self._fetch_current_weather)
        self.fetch_btn.pack(side="left", padx=5)

        # Auto-save notice label (replaces manual save button)
        tk.Label(input_frame,
                 text="💾 Auto-saved to history on each fetch",
                 font=FONT_SMALL, bg=FRAME_COLOR, fg="#4caf50"
                 ).pack(side="left", padx=14)

        # ── Spinner label (shown while loading) ──
        self.loading_var = tk.StringVar(value="")
        tk.Label(input_frame, textvariable=self.loading_var,
                 font=FONT_SMALL, bg=FRAME_COLOR, fg=WARNING_COLOR
                 ).pack(side="left", padx=10)

        # ── History info bar (shows record count for this city) ──
        self.history_bar = tk.Frame(tab, bg=ACCENT_COLOR, height=26)
        self.history_bar.pack(fill="x", padx=15, pady=(0, 4))
        self.history_bar.pack_propagate(False)
        self.history_info_var = tk.StringVar(
            value="  📋  Fetch a city to see its live weather — history builds automatically each time you fetch.")
        tk.Label(self.history_bar, textvariable=self.history_info_var,
                 font=FONT_SMALL, bg=ACCENT_COLOR, fg=HIGHLIGHT_COLOR, anchor="w"
                 ).pack(side="left", padx=8, fill="x", expand=True)

        # ── Main Results Area (split: left = weather card, right = alerts) ──
        results_frame = tk.Frame(tab, bg=BG_COLOR)
        results_frame.pack(fill="both", expand=True, padx=15, pady=5)

        # Left: Weather data card
        self.weather_card = tk.Frame(results_frame, bg=FRAME_COLOR,
                                     bd=0, relief="flat")
        self.weather_card.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # Placeholder text before first fetch
        self.weather_placeholder = tk.Label(
            self.weather_card,
            text="Enter a city name above and click\n⚡ Get Weather to see live data",
            font=("Segoe UI", 13), bg=FRAME_COLOR, fg="#555577",
            justify="center"
        )
        self.weather_placeholder.pack(expand=True)

        # Right: Alerts panel
        alert_panel = tk.Frame(results_frame, bg=FRAME_COLOR, width=260)
        alert_panel.pack(side="right", fill="y", padx=(0, 0))
        alert_panel.pack_propagate(False)

        tk.Label(alert_panel, text="⚠️  Weather Alerts",
                 font=FONT_HEADER, bg=FRAME_COLOR, fg=WARNING_COLOR
                 ).pack(pady=(12, 5), padx=10)

        ttk.Separator(alert_panel, orient="horizontal").pack(fill="x", padx=10)

        self.alerts_text = scrolledtext.ScrolledText(
            alert_panel,
            font=FONT_SMALL, bg="#1a1a2e", fg=TEXT_COLOR,
            state="disabled", wrap="word",
            relief="flat", bd=0, height=20
        )
        self.alerts_text.pack(fill="both", expand=True, padx=8, pady=8)

    def _fetch_current_weather(self):
        """
        Step 1 of 2 — Resolve city name to geocoding matches.
        If multiple cities share the name, show a picker dialog.
        Runs the geocoding call in a background thread so the UI stays responsive.
        """
        city = self.city_var.get().strip()
        # Guard: ignore if placeholder text is still present or field is empty
        if not city or city == "e.g. Hyderabad  or  Hyderabad, IN":
            messagebox.showwarning("Input Required",
                                   "Please type a city name before fetching.\n\n"
                                   "Examples:\n"
                                   "  Hyderabad\n"
                                   "  Hyderabad, IN\n"
                                   "  London, GB")
            return

        # Show resolving indicator and disable button
        self.loading_var.set("⏳ Resolving city…")
        self.fetch_btn.state(["disabled"])

        def _worker():
            matches = get_all_city_matches(city)
            self.root.after(0, lambda: self._on_matches_resolved(city, matches))

        threading.Thread(target=_worker, daemon=True).start()

    # ------------------------------------------------------------------
    def _on_matches_resolved(self, original_query: str, matches: list):
        """
        Step 2a — Called back on the main thread with geocoding results.
        • 0 matches  → show error
        • 1 match    → ask the user to confirm before fetching
        • 2-5 matches → show a picker dialog listing all options
        """
        self.loading_var.set("")
        self.fetch_btn.state(["!disabled"])

        if not matches:
            messagebox.showerror(
                "City Not Found",
                f"No city found for  '{original_query}'.\n\n"
                "💡 Tips:\n"
                "  • Check spelling (use English city names)\n"
                "  • Add a country code:  London, GB  |  Paris, FR\n"
                "  • Check your internet connection\n"
                "  • Verify the API key in config.py"
            )
            return

        if len(matches) == 1:
            m = matches[0]
            self._show_confirm_dialog(m)
        else:
            self._show_picker_dialog(matches)

    # ------------------------------------------------------------------
    def _city_label(self, m: dict) -> str:
        """Build a human-readable label for a geocoding match dict."""
        parts = [m["name"]]
        if m.get("state"):
            parts.append(m["state"])
        parts.append(m["country"])
        return ", ".join(parts)

    # ------------------------------------------------------------------
    def _show_confirm_dialog(self, m: dict):
        """
        Single-match confirmation dialog — shows the resolved city name
        and asks the user to confirm before fetching weather.
        """
        label = self._city_label(m)
        answer = messagebox.askyesno(
            "Confirm City",
            f"The following city was found:\n\n"
            f"  📍  {label}\n\n"
            f"Fetch weather for this city?",
            icon="question"
        )
        if answer:
            self._do_fetch_by_coords(m)

    # ------------------------------------------------------------------
    def _show_picker_dialog(self, matches: list):
        """
        Multi-match picker dialog — shows a radio-button list of all
        geocoding matches so the user can select the correct city.
        """
        dlg = tk.Toplevel(self.root)
        dlg.title("Select the correct city")
        dlg.configure(bg=BG_COLOR)
        dlg.resizable(False, True)
        dlg.grab_set()                # modal

        # ── Header label ──────────────────────────────────────────────
        tk.Label(
            dlg, text="Multiple cities match your search.\nChoose the correct one:",
            bg=BG_COLOR, fg=TEXT_COLOR, font=FONT_BODY, justify="center"
        ).pack(pady=(16, 8))

        # ── Radio buttons ─────────────────────────────────────────────
        radio_frame = tk.Frame(dlg, bg=BG_COLOR)
        radio_frame.pack(fill="x", padx=8, pady=4)

        choice_var = tk.IntVar(value=0)
        for i, m in enumerate(matches):
            tk.Radiobutton(
                radio_frame,
                text=f"  📍  {self._city_label(m)}",
                variable=choice_var, value=i,
                bg=BG_COLOR, fg=TEXT_COLOR,
                selectcolor=ACCENT_COLOR,
                activebackground=BG_COLOR, activeforeground=TEXT_COLOR,
                font=FONT_BODY, anchor="w"
            ).pack(fill="x", padx=16, pady=4)

        # ── Buttons ───────────────────────────────────────────────────
        btn_frame = tk.Frame(dlg, bg=BG_COLOR)
        btn_frame.pack(pady=16)

        def _confirm():
            chosen = matches[choice_var.get()]
            dlg.destroy()
            self._do_fetch_by_coords(chosen)

        def _cancel():
            dlg.destroy()

        ttk.Button(btn_frame, text="✅  Fetch Weather", command=_confirm).pack(
            side="left", padx=8)
        ttk.Button(btn_frame, text="✖  Cancel", command=_cancel).pack(
            side="left", padx=8)

        dlg.protocol("WM_DELETE_WINDOW", _cancel)

        # ── Size & centre AFTER all widgets are packed ─────────────────
        dlg.update_idletasks()
        dw = 460
        # Calculate height from content, then cap at 90 % of screen height
        content_h = dlg.winfo_reqheight()
        screen_h  = dlg.winfo_screenheight()
        dh = min(content_h + 20, int(screen_h * 0.9))
        pw = self.root.winfo_width()
        ph = self.root.winfo_height()
        px = self.root.winfo_rootx()
        py = self.root.winfo_rooty()
        x = px + pw // 2 - dw // 2
        y = py + ph // 2 - dh // 2
        dlg.geometry(f"{dw}x{dh}+{x}+{y}")

    # ------------------------------------------------------------------
    def _do_fetch_by_coords(self, m: dict):
        """
        Step 2b — Called after the user confirms a city.
        Fetches live weather using the exact coordinates of the chosen city.
        """
        self.loading_var.set("⏳ Fetching live weather…")
        self.fetch_btn.state(["disabled"])

        lat, lon = m["lat"], m["lon"]
        name, country = m["name"], m["country"]

        def _worker():
            data = fetch_weather_by_coords(lat, lon, name, country)
            self.root.after(0, lambda: self._on_weather_fetched(data))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_weather_fetched(self, data: dict):
        """Callback executed on the main thread when weather data arrives."""
        self.loading_var.set("")
        self.fetch_btn.state(["!disabled"])

        if data is None:
            city_typed = self.city_var.get().strip()
            messagebox.showerror(
                "City Not Found",
                f"Could not retrieve weather for  '{city_typed}'.\n\n"
                "💡 Tips for accurate results:\n"
                "  • Check spelling  (use English city names)\n"
                "  • Add country code for precision:\n"
                "       Hyderabad, IN\n"
                "       London, GB\n"
                "       Paris, FR\n"
                "       New York, US\n\n"
                "  • Check your internet connection\n"
                "  • Verify the API key in config.py"
            )
            return

        self.last_weather_data = data
        city_name = data["city"]

        # ── AUTO-SAVE to CSV on every successful fetch ──
        save_weather(data)

        # ── Auto-populate the city field in Trends and Analysis tabs ──
        self.last_fetched_city = city_name
        self.trend_city_var.set(city_name)
        self.analysis_city_var.set(city_name)

        # ── Update the history info bar ──
        from storage import load_city_data
        city_records = load_city_data(city_name)
        rec_count = len(city_records)
        if rec_count == 1:
            history_msg = (f"  📋  First record saved for {city_name}! "
                           f"Fetch again tomorrow to start building trends.")
        else:
            first_date = str(city_records["date"].min())[:10]
            history_msg = (f"  📋  {city_name} has {rec_count} saved records "
                           f"since {first_date}  •  "
                           f"Go to 📈 Trends tab to view charts")
        self.history_info_var.set(history_msg)

        self._display_weather_card(data)
        self._display_alerts(data)
        self._refresh_data_table()
        self._update_status(f"✅ Live weather fetched & saved — {city_name}, "
                            f"{data['country']}  •  {data['timestamp']}")

    def _display_weather_card(self, data: dict):
        """Render the weather data into the results card."""
        # Clear old widgets
        for w in self.weather_card.winfo_children():
            w.destroy()

        emoji = get_weather_emoji(data.get("condition", ""))
        city_full = f"{data.get('city', 'N/A')}, {data.get('country', '')}"

        # ── City Title & Condition ──
        tk.Label(self.weather_card,
                 text=f"{emoji}  {city_full}",
                 font=("Segoe UI", 18, "bold"),
                 bg=FRAME_COLOR, fg=HIGHLIGHT_COLOR
                 ).pack(pady=(18, 2))

        tk.Label(self.weather_card,
                 text=f"{data.get('description', '').title()}",
                 font=("Segoe UI", 12, "italic"),
                 bg=FRAME_COLOR, fg=TEXT_COLOR
                 ).pack(pady=(0, 6))

        # ── Big Temperature Display ──
        tk.Label(self.weather_card,
                 text=f"{data.get('temperature', 0):.1f}{TEMP_UNIT_LABEL}",
                 font=("Segoe UI", 42, "bold"),
                 bg=FRAME_COLOR, fg=BUTTON_COLOR
                 ).pack(pady=(4, 0))

        tk.Label(self.weather_card,
                 text=f"Feels like  {data.get('feels_like', 0):.1f}{TEMP_UNIT_LABEL}   "
                      f"↓ {data.get('temp_min', 0):.1f}  ↑ {data.get('temp_max', 0):.1f}",
                 font=FONT_SMALL, bg=FRAME_COLOR, fg="#aaaaaa"
                 ).pack(pady=(0, 12))

        ttk.Separator(self.weather_card, orient="horizontal").pack(fill="x", padx=20)

        # ── Details Grid ──
        grid = tk.Frame(self.weather_card, bg=FRAME_COLOR)
        grid.pack(fill="x", padx=20, pady=12)

        details = [
            ("💧 Humidity",     f"{data.get('humidity', 0)} %"),
            ("📊 Pressure",     f"{data.get('pressure', 0)} hPa"),
            ("💨 Wind",         f"{data.get('wind_speed', 0)} m/s  "
                                f"{get_wind_direction(data.get('wind_deg', 0))}"),
            ("👁️ Visibility",   f"{data.get('visibility', 0):.1f} km"),
            ("☁️ Cloud Cover",  f"{data.get('clouds', 0)} %"),
            ("🌅 Sunrise",      data.get("sunrise", "N/A")),
            ("🌇 Sunset",       data.get("sunset", "N/A")),
            ("📅 Recorded",     data.get("timestamp", "N/A")),
        ]

        for i, (label, value) in enumerate(details):
            row = i // 2
            col_offset = (i % 2) * 2

            tk.Label(grid, text=label + ":",
                     font=("Segoe UI", 10, "bold"),
                     bg=FRAME_COLOR, fg="#aaaaaa", anchor="e"
                     ).grid(row=row, column=col_offset, sticky="e",
                             padx=(8, 4), pady=4)

            tk.Label(grid, text=value,
                     font=("Segoe UI", 10),
                     bg=FRAME_COLOR, fg=TEXT_COLOR, anchor="w"
                     ).grid(row=row, column=col_offset + 1, sticky="w",
                             padx=(0, 20), pady=4)

    def _display_alerts(self, data: dict):
        """Display weather alerts in the alert panel."""
        alerts = check_weather_alerts(data)

        self.alerts_text.configure(state="normal")
        self.alerts_text.delete("1.0", "end")

        if not alerts:
            self.alerts_text.insert("end",
                "✅  No active weather alerts.\n\n"
                "Current conditions are within\nnormal safe ranges.")
        else:
            for alert in alerts:
                self.alerts_text.insert("end", alert + "\n\n")

        self.alerts_text.configure(state="disabled")

    # =========================================================================
    # ── TAB 2: Compare Cities ─────────────────────────────────────────────────
    # =========================================================================

    def _build_compare_tab(self):
        """Build the Compare Cities tab."""
        tab = self.tab_compare

        # ── Input Row ──
        input_frame = tk.Frame(tab, bg=FRAME_COLOR, pady=10)
        input_frame.pack(fill="x", padx=15, pady=(10, 5))

        tk.Label(input_frame, text="City 1:", font=FONT_HEADER,
                 bg=FRAME_COLOR, fg=HIGHLIGHT_COLOR
                 ).pack(side="left", padx=(15, 6))

        self.compare_city1_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.compare_city1_var,
                  font=FONT_BODY, width=20
                  ).pack(side="left", padx=(0, 15), ipady=4)

        tk.Label(input_frame, text="City 2:", font=FONT_HEADER,
                 bg=FRAME_COLOR, fg=HIGHLIGHT_COLOR
                 ).pack(side="left", padx=(0, 6))

        self.compare_city2_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.compare_city2_var,
                  font=FONT_BODY, width=20
                  ).pack(side="left", padx=(0, 15), ipady=4)

        self.compare_btn = ttk.Button(input_frame, text="🔍  Compare",
                                      command=self._compare_cities)
        self.compare_btn.pack(side="left", padx=5)

        self.compare_loading_var = tk.StringVar(value="")
        tk.Label(input_frame, textvariable=self.compare_loading_var,
                 font=FONT_SMALL, bg=FRAME_COLOR, fg=WARNING_COLOR
                 ).pack(side="left", padx=10)

        # ── Results Frame ──
        self.compare_results_frame = tk.Frame(tab, bg=BG_COLOR)
        self.compare_results_frame.pack(fill="both", expand=True, padx=15, pady=8)

        # Placeholder
        self.compare_placeholder = tk.Label(
            self.compare_results_frame,
            text="Enter two city names above and click\n🔍 Compare to see side-by-side results",
            font=("Segoe UI", 13), bg=BG_COLOR, fg="#555577", justify="center"
        )
        self.compare_placeholder.pack(expand=True)

    def _compare_cities(self):
        """Fetch weather for two cities and compare them."""
        city1 = self.compare_city1_var.get().strip()
        city2 = self.compare_city2_var.get().strip()

        if not city1 or not city2:
            messagebox.showwarning("Input Required",
                                   "Please enter both city names.")
            return

        if city1.lower() == city2.lower():
            messagebox.showwarning("Same City",
                                   "Please enter two different city names.")
            return

        self.compare_loading_var.set("⏳ Fetching both cities...")
        self.compare_btn.state(["disabled"])

        def _worker():
            data1 = fetch_weather(city1)
            data2 = fetch_weather(city2)
            self.root.after(0, lambda: self._on_compare_done(data1, data2))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_compare_done(self, data1, data2):
        """Callback when both city fetches complete."""
        self.compare_loading_var.set("")
        self.compare_btn.state(["!disabled"])

        if data1 is None or data2 is None:
            failed = []
            if data1 is None: failed.append(self.compare_city1_var.get())
            if data2 is None: failed.append(self.compare_city2_var.get())
            messagebox.showerror(
                "City Not Found",
                f"Could not fetch data for:  {', '.join(failed)}\n\n"
                "💡 Try adding a country code:\n"
                "       Hyderabad, IN  •  London, GB\n"
                "       Paris, FR      •  New York, US"
            )
            return

        result = compare_cities(data1, data2)
        self.last_compare_result = result
        self._display_comparison(result)
        self._update_status(
            f"🌍 Compared {data1['city']} vs {data2['city']}")

    def _display_comparison(self, result: dict):
        """Render the comparison results in the tab."""
        # Clear old content
        for w in self.compare_results_frame.winfo_children():
            w.destroy()

        c1 = result.get("city1", "City 1")
        c2 = result.get("city2", "City 2")

        # ── Verdict Banner ──
        hotter  = result.get("hotter_city", "—")
        diff    = result.get("temp_difference", 0)
        verdict = (f"🔥 {hotter} is warmer by {diff}{TEMP_UNIT_LABEL}"
                   if diff > 0 else "🤝 Both cities have the same temperature")

        tk.Label(self.compare_results_frame, text=verdict,
                 font=("Segoe UI", 13, "bold"),
                 bg=BG_COLOR, fg=SUCCESS_COLOR
                 ).pack(pady=(8, 4))

        humid_city = result.get("more_humid_city", "—")
        tk.Label(self.compare_results_frame,
                 text=f"💧 {humid_city} is more humid",
                 font=FONT_BODY, bg=BG_COLOR, fg=HIGHLIGHT_COLOR
                 ).pack(pady=(0, 12))

        # ── Side-by-side cards ──
        cards_frame = tk.Frame(self.compare_results_frame, bg=BG_COLOR)
        cards_frame.pack(fill="both", expand=True, padx=10)
        cards_frame.columnconfigure(0, weight=1)
        cards_frame.columnconfigure(1, weight=1)

        self._build_city_card(cards_frame, result, city_num=1, col=0)
        self._build_city_card(cards_frame, result, city_num=2, col=1)

    def _build_city_card(self, parent, result, city_num: int, col: int):
        """Build a single city comparison card widget."""
        prefix = f"city{city_num}_"

        city      = result.get(f"city{city_num}",          "N/A")
        country   = result.get(f"city{city_num}_country",  "")
        temp      = result.get(f"{prefix}temp",            0)
        feels     = result.get(f"{prefix}feels_like",      0)
        humidity  = result.get(f"{prefix}humidity",        0)
        pressure  = result.get(f"{prefix}pressure",        0)
        wind      = result.get(f"{prefix}wind",            0)
        condition = result.get(f"{prefix}condition",       "N/A")
        desc      = result.get(f"{prefix}desc",            "")

        emoji = get_weather_emoji(condition)

        card = tk.Frame(parent, bg=FRAME_COLOR, bd=0, relief="flat")
        card.grid(row=0, column=col, sticky="nsew", padx=8, pady=4)

        tk.Label(card, text=f"{emoji}  {city}, {country}",
                 font=FONT_HEADER, bg=FRAME_COLOR, fg=HIGHLIGHT_COLOR
                 ).pack(pady=(14, 4))

        tk.Label(card, text=desc.title(),
                 font=("Segoe UI", 10, "italic"),
                 bg=FRAME_COLOR, fg="#aaaaaa"
                 ).pack(pady=(0, 6))

        tk.Label(card, text=f"{temp:.1f}{TEMP_UNIT_LABEL}",
                 font=("Segoe UI", 36, "bold"),
                 bg=FRAME_COLOR, fg=BUTTON_COLOR
                 ).pack()

        tk.Label(card,
                 text=f"Feels like {feels:.1f}{TEMP_UNIT_LABEL}",
                 font=FONT_SMALL, bg=FRAME_COLOR, fg="#888888"
                 ).pack(pady=(0, 10))

        ttk.Separator(card, orient="horizontal").pack(fill="x", padx=16)

        metrics = [
            ("💧 Humidity",  f"{humidity} %"),
            ("📊 Pressure",  f"{pressure} hPa"),
            ("💨 Wind",      f"{wind} m/s"),
        ]
        for label, value in metrics:
            row_f = tk.Frame(card, bg=FRAME_COLOR)
            row_f.pack(fill="x", padx=16, pady=3)
            tk.Label(row_f, text=label, font=FONT_SMALL,
                     bg=FRAME_COLOR, fg="#888888", width=14, anchor="w"
                     ).pack(side="left")
            tk.Label(row_f, text=value, font=("Segoe UI", 10, "bold"),
                     bg=FRAME_COLOR, fg=TEXT_COLOR, anchor="e"
                     ).pack(side="right")

    # =========================================================================
    # ── TAB 3: Trends & Charts ────────────────────────────────────────────────
    # =========================================================================

    def _build_trends_tab(self):
        """Build the Trends & Charts tab."""
        tab = self.tab_trends

        # ── Input Row ──
        ctrl = tk.Frame(tab, bg=FRAME_COLOR, pady=8)
        ctrl.pack(fill="x", padx=15, pady=(10, 5))

        tk.Label(ctrl, text="📍 City:", font=FONT_HEADER,
                 bg=FRAME_COLOR, fg=HIGHLIGHT_COLOR
                 ).pack(side="left", padx=(15, 8))

        self.trend_city_var = tk.StringVar()
        ttk.Entry(ctrl, textvariable=self.trend_city_var,
                  font=FONT_BODY, width=22
                  ).pack(side="left", padx=(0, 10), ipady=4)

        ttk.Button(ctrl, text="🌡️ Temperature Trend",
                   command=self._show_temp_trend
                   ).pack(side="left", padx=5)

        ttk.Button(ctrl, text="📊 Humidity & Pressure",
                   command=self._show_hum_pressure
                   ).pack(side="left", padx=5)

        ttk.Button(ctrl, text="📅 Monthly Averages",
                   command=self._show_monthly_avg
                   ).pack(side="left", padx=5)

        # ── Info bar explaining how history works ──
        info = tk.Frame(tab, bg="#0f3460", height=28)
        info.pack(fill="x", padx=15, pady=(0, 4))
        info.pack_propagate(False)
        tk.Label(info,
                 text="  ℹ️  History builds automatically — every time you fetch a city on the "
                      "Current Weather tab, it is saved. Fetch the same city on multiple days "
                      "to see trends grow.",
                 font=FONT_SMALL, bg="#0f3460", fg=HIGHLIGHT_COLOR, anchor="w"
                 ).pack(side="left", padx=8, fill="x")

        # ── Chart area ──
        self.chart_frame = tk.Frame(tab, bg=BG_COLOR)
        self.chart_frame.pack(fill="both", expand=True, padx=15, pady=(4, 8))

        tk.Label(self.chart_frame,
                 text="📍 Enter a city name above (auto-filled after fetching)\n"
                      "then click a chart button to visualise its history.",
                 font=("Segoe UI", 13), bg=BG_COLOR, fg="#555577",
                 justify="center"
                 ).pack(expand=True)

    def _show_temp_trend(self):
        city = self.trend_city_var.get().strip()
        if not city:
            messagebox.showwarning("Input Required", "Enter a city name first.")
            return
        trend_df = get_temperature_trend(city)
        if trend_df.empty:
            messagebox.showinfo(
                "No History Yet",
                f"No stored records found for '{city}'.\n\n"
                "👉 Go to the  🌤️ Current Weather  tab,\n"
                f"   fetch '{city}', then come back here.\n\n"
                "Each fetch is saved automatically — fetch on\n"
                "multiple days to build a meaningful trend."
            )
            return
        plot_temperature_trend(self.chart_frame, city.title(), trend_df)
        self._update_status(f"📈 Temperature trend displayed for {city.title()}")

    def _show_hum_pressure(self):
        city = self.trend_city_var.get().strip()
        if not city:
            messagebox.showwarning("Input Required", "Enter a city name first.")
            return
        hp_df = get_humidity_pressure_data(city)
        if hp_df.empty:
            messagebox.showinfo(
                "No History Yet",
                f"No stored records found for '{city}'.\n\n"
                "👉 Go to the  🌤️ Current Weather  tab,\n"
                f"   fetch '{city}', then come back here."
            )
            return
        plot_humidity_pressure(self.chart_frame, city.title(), hp_df)
        self._update_status(f"📊 Humidity/Pressure chart for {city.title()}")

    def _show_monthly_avg(self):
        city = self.trend_city_var.get().strip()
        if not city:
            messagebox.showwarning("Input Required", "Enter a city name first.")
            return
        monthly_df = get_monthly_averages(city)
        if monthly_df.empty:
            messagebox.showinfo(
                "No History Yet",
                f"No stored records found for '{city}'.\n\n"
                "👉 Go to the  🌤️ Current Weather  tab,\n"
                f"   fetch '{city}', then come back here.\n\n"
                "Monthly averages need data across multiple months."
            )
            return
        plot_monthly_averages(self.chart_frame, city.title(), monthly_df)
        self._update_status(f"📅 Monthly averages chart for {city.title()}")

    # =========================================================================
    # ── TAB 4: Analysis ───────────────────────────────────────────────────────
    # =========================================================================

    def _build_analysis_tab(self):
        """Build the Analysis tab with stats and extreme records."""
        tab = self.tab_analysis

        # ── Controls ──
        ctrl = tk.Frame(tab, bg=FRAME_COLOR, pady=8)
        ctrl.pack(fill="x", padx=15, pady=(10, 5))

        tk.Label(ctrl, text="📍 City (optional):", font=FONT_HEADER,
                 bg=FRAME_COLOR, fg=HIGHLIGHT_COLOR
                 ).pack(side="left", padx=(15, 8))

        self.analysis_city_var = tk.StringVar()
        ttk.Entry(ctrl, textvariable=self.analysis_city_var,
                  font=FONT_BODY, width=20
                  ).pack(side="left", padx=(0, 10), ipady=4)

        ttk.Button(ctrl, text="🔥 Hottest Day",
                   command=self._show_hottest
                   ).pack(side="left", padx=5)

        ttk.Button(ctrl, text="🧊 Coldest Day",
                   command=self._show_coldest
                   ).pack(side="left", padx=5)

        ttk.Button(ctrl, text="📈 Statistics",
                   command=self._show_statistics
                   ).pack(side="left", padx=5)

        ttk.Button(ctrl, text="🏙️ All Cities",
                   command=self._show_all_cities,
                   style="Secondary.TButton"
                   ).pack(side="left", padx=5)

        # ── Results Text Area ──
        self.analysis_text = scrolledtext.ScrolledText(
            tab, font=FONT_MONO, bg=FRAME_COLOR, fg=TEXT_COLOR,
            state="disabled", wrap="word", relief="flat", bd=0
        )
        self.analysis_text.pack(fill="both", expand=True, padx=15, pady=8)

        # Initial help text
        self._write_analysis("\n  Welcome to the Analysis Panel!\n\n"
                             "  ► Enter a city name (optional) then click a button.\n"
                             "  ► Leave city blank to search across ALL stored cities.\n\n"
                             "  Make sure you have fetched & saved weather data first.")

    def _write_analysis(self, text: str):
        """Write text to the analysis output box."""
        self.analysis_text.configure(state="normal")
        self.analysis_text.delete("1.0", "end")
        self.analysis_text.insert("end", text)
        self.analysis_text.configure(state="disabled")

    def _show_hottest(self):
        city = self.analysis_city_var.get().strip() or None
        result = get_hottest_day(city)
        if not result:
            self._write_analysis(
                f"\n  ❌  No data found{' for ' + city if city else ''}.\n\n"
                "  Please fetch and save weather data first.")
            return
        text = (
            f"\n  🔥  HOTTEST DAY RECORDED\n"
            f"  {'─'*40}\n"
            f"  City        : {result['city']}\n"
            f"  Date        : {result['date']}\n"
            f"  Temperature : {result['temperature']}{TEMP_UNIT_LABEL}\n"
            f"  Condition   : {result['condition']}\n"
            f"  Humidity    : {result['humidity']} %\n"
        )
        self._write_analysis(text)

    def _show_coldest(self):
        city = self.analysis_city_var.get().strip() or None
        result = get_coldest_day(city)
        if not result:
            self._write_analysis(
                f"\n  ❌  No data found{' for ' + city if city else ''}.\n\n"
                "  Please fetch and save weather data first.")
            return
        text = (
            f"\n  🧊  COLDEST DAY RECORDED\n"
            f"  {'─'*40}\n"
            f"  City        : {result['city']}\n"
            f"  Date        : {result['date']}\n"
            f"  Temperature : {result['temperature']}{TEMP_UNIT_LABEL}\n"
            f"  Condition   : {result['condition']}\n"
            f"  Humidity    : {result['humidity']} %\n"
        )
        self._write_analysis(text)

    def _show_statistics(self):
        city = self.analysis_city_var.get().strip()
        if not city:
            messagebox.showinfo("City Required",
                                "Please enter a city name for statistics.")
            return

        stats = get_statistics_summary(city)
        if "error" in stats:
            self._write_analysis(f"\n  ❌  {stats['error']}")
            return

        text = (
            f"\n  📊  WEATHER STATISTICS — {stats['city'].upper()}\n"
            f"  {'─'*40}\n"
            f"  Total Records     : {stats['total_records']}\n"
            f"  Date Range        : {stats['first_record']}  →  {stats['last_record']}\n\n"
            f"  TEMPERATURE ({TEMP_UNIT_LABEL})\n"
            f"  ├─ Average        : {stats['avg_temp']}{TEMP_UNIT_LABEL}\n"
            f"  ├─ Maximum        : {stats['max_temp']}{TEMP_UNIT_LABEL}\n"
            f"  ├─ Minimum        : {stats['min_temp']}{TEMP_UNIT_LABEL}\n"
            f"  └─ Std Deviation  : ±{stats['temp_std']}{TEMP_UNIT_LABEL}\n\n"
            f"  HUMIDITY (%)\n"
            f"  ├─ Average        : {stats['avg_humidity']}%\n"
            f"  ├─ Maximum        : {stats['max_humidity']}%\n"
            f"  └─ Minimum        : {stats['min_humidity']}%\n\n"
            f"  PRESSURE (hPa)\n"
            f"  ├─ Average        : {stats['avg_pressure']} hPa\n"
            f"  ├─ Maximum        : {stats['max_pressure']} hPa\n"
            f"  └─ Minimum        : {stats['min_pressure']} hPa\n\n"
            f"  Average Wind Speed  : {stats['avg_wind_speed']} m/s\n"
            f"  Most Common Cond.   : {stats['most_common_cond']}\n"
        )
        self._write_analysis(text)

    def _show_all_cities(self):
        cities = get_all_cities()
        if not cities:
            self._write_analysis("\n  📭  No weather data has been stored yet.\n\n"
                                 "  Fetch and save weather data to see cities here.")
            return
        text = f"\n  🏙️  CITIES WITH STORED WEATHER DATA  ({len(cities)} cities)\n"
        text += f"  {'─'*40}\n"
        for i, c in enumerate(cities, 1):
            text += f"  {i:3}.  {c}\n"
        self._write_analysis(text)

    # =========================================================================
    # ── TAB 5: Data Log ───────────────────────────────────────────────────────
    # =========================================================================

    def _build_data_tab(self):
        """Build the Data Log tab with a table view of the CSV."""
        tab = self.tab_data

        # ── Controls ──
        ctrl = tk.Frame(tab, bg=FRAME_COLOR, pady=8)
        ctrl.pack(fill="x", padx=15, pady=(10, 5))

        ttk.Button(ctrl, text="🔄  Refresh",
                   command=self._refresh_data_table
                   ).pack(side="left", padx=(15, 8))

        # Record count label
        self.record_count_var = tk.StringVar(value="Records: —")
        tk.Label(ctrl, textvariable=self.record_count_var,
                 font=FONT_BODY, bg=FRAME_COLOR, fg=HIGHLIGHT_COLOR
                 ).pack(side="left", padx=10)

        # Search/filter
        tk.Label(ctrl, text="🔍 Filter city:", font=FONT_SMALL,
                 bg=FRAME_COLOR, fg="#aaaaaa"
                 ).pack(side="left", padx=(20, 6))

        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *_: self._apply_filter())
        ttk.Entry(ctrl, textvariable=self.filter_var, width=18,
                  font=FONT_SMALL
                  ).pack(side="left", padx=(0, 8), ipady=3)

        # ── Treeview table ──
        table_frame = tk.Frame(tab, bg=BG_COLOR)
        table_frame.pack(fill="both", expand=True, padx=15, pady=8)

        columns = ("date", "city", "country", "temp", "humidity",
                   "pressure", "wind", "condition")

        self.tree = ttk.Treeview(table_frame, columns=columns,
                                 show="headings", selectmode="browse")

        # Column headers and widths
        col_cfg = {
            "date":      ("📅 Date",        100),
            "city":      ("🏙️ City",        110),
            "country":   ("🌐 Country",     70),
            "temp":      (f"🌡️ Temp ({TEMP_UNIT_LABEL})", 80),
            "humidity":  ("💧 Humidity %",  90),
            "pressure":  ("📊 Pressure hPa",100),
            "wind":      ("💨 Wind m/s",    85),
            "condition": ("⛅ Condition",   110),
        }
        for col, (heading, width) in col_cfg.items():
            self.tree.heading(col, text=heading)
            self.tree.column(col,  width=width, anchor="center", minwidth=60)

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # Alternate row colours for readability
        self.tree.tag_configure("odd",  background=FRAME_COLOR)
        self.tree.tag_configure("even", background="#1e2240")

        # Load initial data
        self._refresh_data_table()

    def _refresh_data_table(self):
        """Reload all records from CSV into the table."""
        df = load_all_data()
        self._all_records = df    # Keep in memory for filtering
        self._populate_tree(df)
        count = len(df)
        self.record_count_var.set(f"Records: {count}")
        self._update_status(f"📋 Data log refreshed — {count} records loaded")

    def _apply_filter(self):
        """Filter the table rows by city name as user types."""
        query = self.filter_var.get().strip().lower()
        if hasattr(self, "_all_records") and not self._all_records.empty:
            if query:
                filtered = self._all_records[
                    self._all_records["city"].str.lower().str.contains(query, na=False)
                ]
            else:
                filtered = self._all_records
            self._populate_tree(filtered)

    def _populate_tree(self, df):
        """Fill the Treeview with rows from a DataFrame."""
        # Clear existing rows
        for item in self.tree.get_children():
            self.tree.delete(item)

        if df.empty:
            return

        for idx, row in df.iterrows():
            tag = "odd" if idx % 2 == 0 else "even"
            date_str = str(row.get("date", ""))[:10]
            self.tree.insert("", "end", tag=tag, values=(
                date_str,
                row.get("city",         ""),
                row.get("country",      ""),
                f"{row.get('temperature', ''):.1f}" if pd.notna(row.get("temperature")) else "",
                row.get("humidity",     ""),
                row.get("pressure",     ""),
                row.get("wind_speed",   ""),
                row.get("condition",    ""),
            ))

    # =========================================================================
    # ── Status Bar ────────────────────────────────────────────────────────────
    # =========================================================================

    def _build_status_bar(self):
        """Build the bottom status bar."""
        status_bar = tk.Frame(self.root, bg=ACCENT_COLOR, height=24)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)

        self.status_var = tk.StringVar(
            value="  Ready  •  Enter a city name and click 'Get Weather' to begin.")
        tk.Label(status_bar, textvariable=self.status_var,
                 font=FONT_SMALL, bg=ACCENT_COLOR, fg=TEXT_COLOR,
                 anchor="w"
                 ).pack(side="left", padx=8, fill="x", expand=True)

        # Total record count on right
        self.status_count_var = tk.StringVar(
            value=f"CSV Records: {get_record_count()}")
        tk.Label(status_bar, textvariable=self.status_count_var,
                 font=FONT_SMALL, bg=ACCENT_COLOR, fg=HIGHLIGHT_COLOR
                 ).pack(side="right", padx=12)

    def _update_status(self, message: str):
        """Update the status bar message and record count."""
        self.status_var.set(f"  {message}")
        self.status_count_var.set(f"CSV Records: {get_record_count()}")

    # =========================================================================
    # ── TAB 6: Historical Weather ─────────────────────────────────────────────
    # =========================================================================

    def _build_history_tab(self):
        """Build the Historical Weather tab (Open-Meteo archive, free)."""
        tab = self.tab_history

        # ── Input row ────────────────────────────────────────────────────────
        inp = tk.Frame(tab, bg=FRAME_COLOR, pady=12)
        inp.pack(fill="x", padx=15, pady=(10, 5))

        tk.Label(inp, text="🏙️  City:",
                 font=FONT_HEADER, bg=FRAME_COLOR, fg=HIGHLIGHT_COLOR
                 ).pack(side="left", padx=(15, 6))

        self.hist_city_var = tk.StringVar()
        ttk.Entry(inp, textvariable=self.hist_city_var,
                  font=FONT_BODY, width=22
                  ).pack(side="left", ipady=4, padx=(0, 14))

        tk.Label(inp, text="📅  Date (YYYY-MM-DD):",
                 font=FONT_HEADER, bg=FRAME_COLOR, fg=HIGHLIGHT_COLOR
                 ).pack(side="left", padx=(0, 6))

        self.hist_date_var = tk.StringVar()
        date_entry = ttk.Entry(inp, textvariable=self.hist_date_var,
                               font=FONT_BODY, width=14)
        date_entry.pack(side="left", ipady=4, padx=(0, 12))
        # default to yesterday
        from datetime import date, timedelta
        date_entry.insert(0, (date.today() - timedelta(days=1)).isoformat())

        self.hist_btn = ttk.Button(inp, text="🔍  Fetch History",
                                   command=self._fetch_history)
        self.hist_btn.pack(side="left", padx=4)

        self.hist_loading_var = tk.StringVar(value="")
        tk.Label(inp, textvariable=self.hist_loading_var,
                 font=FONT_SMALL, bg=FRAME_COLOR, fg=WARNING_COLOR
                 ).pack(side="left", padx=10)

        # ── Info banner ───────────────────────────────────────────────────────
        banner = tk.Frame(tab, bg="#0f3460", height=26)
        banner.pack(fill="x", padx=15, pady=(0, 4))
        banner.pack_propagate(False)
        tk.Label(banner,
                 text="  ℹ️  Powered by Open-Meteo Archive API  •  "
                      "Free, no API key  •  Data available from 1940 onwards",
                 font=FONT_SMALL, bg="#0f3460", fg=HIGHLIGHT_COLOR, anchor="w"
                 ).pack(side="left", padx=8)

        # ── Result card ───────────────────────────────────────────────────────
        self.hist_card = tk.Frame(tab, bg=FRAME_COLOR)
        self.hist_card.pack(fill="both", expand=True, padx=15, pady=6)

        tk.Label(self.hist_card,
                 text="Enter a city and a past date above, then click\n"
                      "🔍 Fetch History to see the archived weather data.",
                 font=("Segoe UI", 13), bg=FRAME_COLOR, fg="#555577",
                 justify="center"
                 ).pack(expand=True)

    def _fetch_history(self):
        """Validate input and kick off background historical fetch."""
        city = self.hist_city_var.get().strip()
        date = self.hist_date_var.get().strip()

        if not city:
            messagebox.showwarning("Input Required", "Please enter a city name.")
            return
        if not date:
            messagebox.showwarning("Input Required",
                                   "Please enter a date in YYYY-MM-DD format.")
            return

        self.hist_loading_var.set("⏳ Fetching archive…")
        self.hist_btn.state(["disabled"])

        def _worker():
            try:
                result = fetch_historical_weather(city, date)
                self.root.after(0, lambda: self._on_history_fetched(result, city, date))
            except ValueError as e:
                self.root.after(0, lambda err=str(e): self._on_history_error(err))
            except Exception as e:
                self.root.after(0, lambda err=str(e): self._on_history_error(err))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_history_error(self, msg: str):
        self.hist_loading_var.set("")
        self.hist_btn.state(["!disabled"])
        messagebox.showerror("Error", msg)

    def _on_history_fetched(self, result, city, date):
        self.hist_loading_var.set("")
        self.hist_btn.state(["!disabled"])

        if result is None:
            messagebox.showerror(
                "Not Found",
                f"Could not retrieve historical data for '{city}' on {date}.\n\n"
                "Tips:\n"
                "  • Check city spelling\n"
                "  • Add country code: London, GB\n"
                "  • Check your internet connection"
            )
            return

        self._render_history_card(result)
        self._update_status(
            f"📅 Historical data loaded — {result['city']}, "
            f"{result['country']} on {result['date']}")

    def _render_history_card(self, r: dict):
        """Render historical weather result into the card frame."""
        for w in self.hist_card.winfo_children():
            w.destroy()

        city_full = f"{r['city']}, {r['country']}"

        # ── Header ────────────────────────────────────────────────────────
        tk.Label(self.hist_card,
                 text=f"📍  {city_full}",
                 font=("Segoe UI", 18, "bold"),
                 bg=FRAME_COLOR, fg=HIGHLIGHT_COLOR
                 ).pack(pady=(18, 2))

        tk.Label(self.hist_card,
                 text=f"📅  {r['date']}",
                 font=("Segoe UI", 12),
                 bg=FRAME_COLOR, fg="#aaaaaa"
                 ).pack(pady=(0, 12))

        ttk.Separator(self.hist_card, orient="horizontal").pack(fill="x", padx=30)

        # ── Temperature row ───────────────────────────────────────────────
        temp_row = tk.Frame(self.hist_card, bg=FRAME_COLOR)
        temp_row.pack(pady=18)

        def _tile(parent, icon, label, value, color):
            f = tk.Frame(parent, bg="#1e2240", padx=22, pady=14)
            f.pack(side="left", padx=10)
            tk.Label(f, text=icon, font=("Segoe UI", 22),
                     bg="#1e2240", fg=color).pack()
            tk.Label(f, text=label, font=FONT_SMALL,
                     bg="#1e2240", fg="#888888").pack(pady=(2, 0))
            tk.Label(f, text=value, font=("Segoe UI", 16, "bold"),
                     bg="#1e2240", fg=color).pack()

        def _fmt_t(v):
            return f"{v:.1f} °C" if v is not None else "N/A"

        _tile(temp_row, "🔺", "Max Temp",  _fmt_t(r["temp_max"]),  BUTTON_COLOR)
        _tile(temp_row, "🔻", "Min Temp",  _fmt_t(r["temp_min"]),  "#00b4d8")
        _tile(temp_row, "🌡️", "Avg Temp",  _fmt_t(r["temp_avg"]),  "#4caf50")

        ttk.Separator(self.hist_card, orient="horizontal").pack(fill="x", padx=30)

        # ── Extra metrics ─────────────────────────────────────────────────
        extra_row = tk.Frame(self.hist_card, bg=FRAME_COLOR)
        extra_row.pack(pady=14)

        _tile(extra_row, "🌧️", "Precipitation",
              f"{r['precipitation']:.1f} mm", "#00b4d8")
        _tile(extra_row, "💨", "Max Wind",
              f"{r['windspeed_max']:.1f} km/h", WARNING_COLOR)
        _tile(extra_row, "☀️", "Sunshine",
              f"{r['sunshine_hours']:.1f} hrs", "#ffcc00")


# =============================================================================
# ── Module Entry Point (for testing gui.py directly) ─────────────────────────
# =============================================================================

if __name__ == "__main__":
    root = tk.Tk()
    app  = WeatherApp(root)
    root.mainloop()
