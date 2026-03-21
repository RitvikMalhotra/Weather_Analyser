# =============================================================================
# gui_modern.py  –  Modern UI  for the Weather Monitoring & Analysis System
# =============================================================================
# Design language:
#   • Flat / card-based layout with rounded visual sections
#   • Soft gradient-like colour palette (deep slate + vibrant accents)
#   • Large weather stat "tiles" on the Current Weather tab
#   • Animated loading dot indicator
#   • Sidebar navigation instead of notebook tabs
#   • Compact, icon-driven control bars
# =============================================================================

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from datetime import datetime
import pandas as pd

from api      import (fetch_weather, fetch_weather_by_coords,
                       get_all_city_matches, get_weather_emoji, get_wind_direction)
from storage  import save_weather, load_all_data, get_all_cities, get_record_count
from analysis import (
    get_hottest_day, get_coldest_day, compare_cities,
    get_temperature_trend, get_humidity_pressure_data,
    get_statistics_summary, check_weather_alerts, get_monthly_averages
)
from charts import (
    plot_temperature_trend, plot_humidity_pressure,
    plot_city_comparison, plot_monthly_averages
)
from config import (
    API_KEY, CSV_FILE, UNITS, TEMP_UNIT_LABEL
)

# ── Modern colour palette ──────────────────────────────────────────────────
M_BG          = "#0d1117"   # Near-black background
M_SURFACE     = "#161b22"   # Card / surface
M_SURFACE2    = "#21262d"   # Raised card
M_BORDER      = "#30363d"   # Subtle border
M_ACCENT      = "#58a6ff"   # Blue accent
M_ACCENT2     = "#3fb950"   # Green accent
M_RED         = "#f85149"   # Red / danger
M_ORANGE      = "#e3b341"   # Warning
M_TEXT        = "#e6edf3"   # Primary text
M_TEXT2       = "#8b949e"   # Secondary text
M_SIDEBAR     = "#010409"   # Sidebar background
M_SEL         = "#1f6feb"   # Selected sidebar item

# ── Modern fonts ──────────────────────────────────────────────────────────
MF_TITLE  = ("Segoe UI", 18, "bold")
MF_HEAD   = ("Segoe UI", 13, "bold")
MF_BODY   = ("Segoe UI", 11)
MF_SMALL  = ("Segoe UI", 9)
MF_MONO   = ("Consolas", 10)
MF_GIANT  = ("Segoe UI", 44, "bold")
MF_BIG    = ("Segoe UI", 22, "bold")

# Sidebar navigation items: (label, icon)
NAV_ITEMS = [
    ("Current Weather",  "🌤"),
    ("Compare Cities",   "⚖"),
    ("Trends & Charts",  "📈"),
    ("Analysis",         "📊"),
    ("Data Log",         "🗃"),
]


# =============================================================================
class ModernWeatherApp:
    """Modern-UI Weather App using a sidebar + content pane layout."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self._setup_window()
        self._apply_styles()
        self._build_layout()

        self.last_weather_data   = None
        self.last_compare_result = None
        self.last_fetched_city   = ""
        self._anim_job           = None   # for loading animation

    # ─────────────────────────────────────────────────────────────────────
    # Window & layout scaffolding
    # ─────────────────────────────────────────────────────────────────────

    def _setup_window(self):
        self.root.title("⛅  Weather Monitor  —  Modern UI")
        self.root.geometry("1120x740")
        self.root.minsize(950, 640)
        self.root.configure(bg=M_BG)
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w, h = 1120, 740
        self.root.geometry(f"{w}x{h}+{sw//2 - w//2}+{sh//2 - h//2}")

    def _apply_styles(self):
        s = ttk.Style()
        s.theme_use("clam")

        s.configure("TFrame",      background=M_BG)
        s.configure("Surface.TFrame", background=M_SURFACE)
        s.configure("Surface2.TFrame", background=M_SURFACE2)

        s.configure("TLabel",      background=M_BG, foreground=M_TEXT,
                    font=MF_BODY)
        s.configure("Dim.TLabel",  background=M_SURFACE, foreground=M_TEXT2,
                    font=MF_SMALL)

        s.configure("Accent.TButton",
                    background=M_ACCENT, foreground="#ffffff",
                    font=MF_BODY, borderwidth=0, focusthickness=0, padding=(12, 7))
        s.map("Accent.TButton",
              background=[("active", "#388bfd"), ("pressed", "#1158c7")])

        s.configure("Green.TButton",
                    background=M_ACCENT2, foreground="#000000",
                    font=MF_BODY, borderwidth=0, focusthickness=0, padding=(12, 7))
        s.map("Green.TButton",
              background=[("active", "#2ea043")])

        s.configure("Ghost.TButton",
                    background=M_SURFACE2, foreground=M_TEXT,
                    font=MF_SMALL, borderwidth=0, focusthickness=0, padding=(8, 5))
        s.map("Ghost.TButton",
              background=[("active", M_SEL)])

        s.configure("TEntry",
                    fieldbackground=M_SURFACE2, foreground=M_TEXT,
                    insertcolor=M_TEXT, font=MF_BODY,
                    borderwidth=1, relief="flat")

        s.configure("Treeview",
                    background=M_SURFACE, foreground=M_TEXT,
                    fieldbackground=M_SURFACE, font=MF_SMALL, rowheight=24)
        s.configure("Treeview.Heading",
                    background=M_SURFACE2, foreground=M_ACCENT,
                    font=("Segoe UI", 9, "bold"))
        s.map("Treeview", background=[("selected", M_SEL)])

        s.configure("TScrollbar",
                    background=M_SURFACE2, troughcolor=M_BG,
                    arrowcolor=M_TEXT2)
        s.configure("TSeparator", background=M_BORDER)

    def _build_layout(self):
        """Build the top-bar + sidebar + content pane scaffold."""
        # ── Top bar ──────────────────────────────────────────────────────
        self._build_topbar()

        # ── Pre-create status StringVars so pages built below can call
        #    _update_status() without AttributeError ──────────────────────
        self.status_var       = tk.StringVar(
            value="  Ready  •  Select a city and click Fetch Weather")
        self.status_count_var = tk.StringVar(
            value=f"Records: {get_record_count()}")

        # ── Body (sidebar | content) ──────────────────────────────────────
        body = tk.Frame(self.root, bg=M_BG)
        body.pack(fill="both", expand=True)

        self._build_sidebar(body)
        self._build_content_area(body)

        # ── Status bar (packed last so it sits at the bottom) ─────────────
        self._build_statusbar()

        # Select first page (after layout is done so geometry is available)
        self._active_nav  = None
        self._anim_slide_job = None
        self._current_page_idx = None
        self.root.after(50, lambda: self._select_nav(0))

        # Keep the active page filling the container when window is resized
        def _on_resize(e):
            idx = getattr(self, "_current_page_idx", None)
            if idx is not None and not getattr(self, "_anim_slide_job", None):
                W = self._page_container.winfo_width()
                H = self._page_container.winfo_height()
                self._pages[idx].place(x=0, y=0, width=W, height=H)
        self._page_container.bind("<Configure>", _on_resize)

    # ─────────────────────────────────────────────────────────────────────
    # Top bar
    # ─────────────────────────────────────────────────────────────────────

    def _build_topbar(self):
        bar = tk.Frame(self.root, bg=M_SURFACE, height=52)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        # Left: logo + title
        tk.Label(bar, text="⛅", font=("Segoe UI", 20),
                 bg=M_SURFACE, fg=M_ACCENT
                 ).pack(side="left", padx=(16, 6), pady=8)
        tk.Label(bar, text="Weather Monitor",
                 font=MF_TITLE, bg=M_SURFACE, fg=M_TEXT
                 ).pack(side="left", pady=8)

        tk.Label(bar, text="Modern UI",
                 font=MF_SMALL, bg=M_SURFACE, fg=M_TEXT2
                 ).pack(side="left", padx=(6, 0), pady=18)

        # Right: live clock
        self.clock_var = tk.StringVar()
        tk.Label(bar, textvariable=self.clock_var,
                 font=MF_SMALL, bg=M_SURFACE, fg=M_TEXT2
                 ).pack(side="right", padx=20)
        self._tick_clock()

    def _tick_clock(self):
        self.clock_var.set(datetime.now().strftime("%A, %d %b %Y   %H:%M:%S"))
        self.root.after(1000, self._tick_clock)

    # ─────────────────────────────────────────────────────────────────────
    # Sidebar
    # ─────────────────────────────────────────────────────────────────────

    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=M_SIDEBAR, width=190)
        sb.pack(fill="y", side="left")
        sb.pack_propagate(False)

        # Section label
        tk.Label(sb, text="  NAVIGATION",
                 font=("Segoe UI", 8, "bold"),
                 bg=M_SIDEBAR, fg=M_TEXT2
                 ).pack(anchor="w", padx=12, pady=(18, 6))

        self._nav_buttons = []
        for i, (label, icon) in enumerate(NAV_ITEMS):
            btn = tk.Label(
                sb,
                text=f"  {icon}   {label}",
                font=MF_BODY,
                bg=M_SIDEBAR, fg=M_TEXT2,
                anchor="w", cursor="hand2",
                padx=12, pady=10,
            )
            btn.pack(fill="x")
            btn.bind("<Button-1>", lambda e, idx=i: self._select_nav(idx))
            btn.bind("<Enter>",    lambda e, b=btn: b.configure(bg="#1c2128") if b != self._active_nav else None)
            btn.bind("<Leave>",    lambda e, b=btn: b.configure(bg=M_SIDEBAR) if b != self._active_nav else None)
            self._nav_buttons.append(btn)

        # Bottom: record count badge
        self._sb_count_var = tk.StringVar()
        self._sb_count_var.set(f"📁 {get_record_count()} records")
        tk.Label(sb, textvariable=self._sb_count_var,
                 font=MF_SMALL, bg=M_SIDEBAR, fg=M_TEXT2
                 ).pack(side="bottom", pady=14, padx=12, anchor="w")

    def _select_nav(self, idx: int):
        """Switch page with an ultra-smooth time-based slide animation."""
        if idx == getattr(self, "_current_page_idx", None):
            return   # already on this page

        prev_idx = getattr(self, "_current_page_idx", None)
        self._current_page_idx = idx

        # ── Update sidebar highlight ──────────────────────────────────
        for btn in self._nav_buttons:
            btn.configure(bg=M_SIDEBAR, fg=M_TEXT2)
        self._nav_buttons[idx].configure(bg=M_SEL, fg="#ffffff")
        self._active_nav = self._nav_buttons[idx]

        # ── Cancel any in-progress animation ─────────────────────────
        if getattr(self, "_anim_slide_job", None):
            self.root.after_cancel(self._anim_slide_job)
            self._anim_slide_job = None

        new_page  = self._pages[idx]
        prev_page = self._pages[prev_idx] if prev_idx is not None else None

        # Direction: +1 = slide left (forward), -1 = slide right (backward)
        direction = 1 if (prev_idx is None or idx > prev_idx) else -1

        container = self._page_container
        container.update_idletasks()
        W = container.winfo_width()  or 900
        H = container.winfo_height() or 600

        # Place new page just off-screen
        new_page.place(x=direction * W, y=0, width=W, height=H)
        new_page.lift()

        # ── Time-based animation parameters ──────────────────────────
        DURATION_MS = 320       # slightly longer for a luxurious feel
        FRAME_MS    = 8         # ~120 fps target

        import time
        t_start = time.perf_counter()

        def _ease_in_out_cubic(x: float) -> float:
            """
            Cubic ease-in-out:
              • Starts slow  → feels gentle, no sharp jolt
              • Peaks speed in the middle
              • Ends slow    → lands softly with no snap
            Formula: 4x³          for x < 0.5
                     1-(-2x+2)³/2  for x >= 0.5
            """
            if x < 0.5:
                return 4.0 * x * x * x
            else:
                return 1.0 - (-2.0 * x + 2.0) ** 3 / 2.0

        def _frame():
            elapsed  = (time.perf_counter() - t_start) * 1000   # ms
            progress = min(elapsed / DURATION_MS, 1.0)
            t        = _ease_in_out_cubic(progress)

            # Pixel positions — round() rather than int() for less jitter
            new_x  = round(direction * W * (1.0 - t))
            prev_x = new_x - direction * W

            new_page.place(x=new_x, y=0, width=W, height=H)
            if prev_page:
                prev_page.place(x=prev_x, y=0, width=W, height=H)

            if progress < 1.0:
                self._anim_slide_job = self.root.after(FRAME_MS, _frame)
            else:
                # Final frame: snap exactly into place and tidy up
                new_page.place(x=0, y=0, width=W, height=H)
                if prev_page:
                    prev_page.place_forget()
                self._anim_slide_job = None

        _frame()

    # ─────────────────────────────────────────────────────────────────────
    # Content area — hosts one frame per page
    # ─────────────────────────────────────────────────────────────────────

    def _build_content_area(self, parent):
        # Use a plain frame as the clipping container; pages are placed inside it
        container = tk.Frame(parent, bg=M_BG)
        container.pack(fill="both", expand=True, side="left")
        self._page_container = container

        self._pages = []
        builders = [
            self._build_page_current,
            self._build_page_compare,
            self._build_page_trends,
            self._build_page_analysis,
            self._build_page_datalog,
        ]
        for build_fn in builders:
            page = tk.Frame(container, bg=M_BG)
            build_fn(page)
            self._pages.append(page)

    # ─────────────────────────────────────────────────────────────────────
    # Status bar
    # ─────────────────────────────────────────────────────────────────────

    def _build_statusbar(self):
        bar = tk.Frame(self.root, bg=M_SURFACE, height=26)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        # status_var / status_count_var are pre-created in _build_layout;
        # here we just attach the labels to them.
        tk.Label(bar, textvariable=self.status_var,
                 font=MF_SMALL, bg=M_SURFACE, fg=M_TEXT2, anchor="w"
                 ).pack(side="left", padx=10, fill="x", expand=True)

        tk.Label(bar, textvariable=self.status_count_var,
                 font=MF_SMALL, bg=M_SURFACE, fg=M_ACCENT
                 ).pack(side="right", padx=12)

    def _update_status(self, msg: str):
        self.status_var.set(f"  {msg}")
        count = get_record_count()
        self.status_count_var.set(f"Records: {count}")
        self._sb_count_var.set(f"📁 {count} records")

    # ─────────────────────────────────────────────────────────────────────
    # Helper: section card
    # ─────────────────────────────────────────────────────────────────────

    def _card(self, parent, **grid_kw):
        """Return a raised card frame."""
        f = tk.Frame(parent, bg=M_SURFACE, bd=0, relief="flat")
        return f

    def _section_title(self, parent, text: str):
        tk.Label(parent, text=text, font=MF_HEAD,
                 bg=M_BG, fg=M_ACCENT
                 ).pack(anchor="w", padx=18, pady=(16, 4))

    # ─────────────────────────────────────────────────────────────────────
    # PAGE 1 — Current Weather
    # ─────────────────────────────────────────────────────────────────────

    def _build_page_current(self, page):
        # ── Search bar ───────────────────────────────────────────────────
        search = tk.Frame(page, bg=M_SURFACE, pady=14)
        search.pack(fill="x", padx=18, pady=(14, 0))

        tk.Label(search, text="🌍  City Name",
                 font=MF_HEAD, bg=M_SURFACE, fg=M_TEXT
                 ).pack(side="left", padx=(16, 10))

        self.city_var = tk.StringVar()
        city_entry = ttk.Entry(search, textvariable=self.city_var,
                               font=MF_BODY, width=26)
        city_entry.pack(side="left", ipady=5, padx=(0, 10))
        city_entry.bind("<Return>", lambda e: self._fetch_weather())

        # Placeholder
        _PH = "e.g. Hyderabad  or  Hyderabad, IN"
        city_entry.insert(0, _PH)
        city_entry.configure(foreground=M_TEXT2)
        def _fi(e):
            if city_entry.get() == _PH:
                city_entry.delete(0, "end")
                city_entry.configure(foreground=M_TEXT)
        def _fo(e):
            if not city_entry.get().strip():
                city_entry.insert(0, _PH)
                city_entry.configure(foreground=M_TEXT2)
        city_entry.bind("<FocusIn>",  _fi)
        city_entry.bind("<FocusOut>", _fo)

        self.fetch_btn = ttk.Button(search, text="⚡  Fetch Weather",
                                    style="Accent.TButton",
                                    command=self._fetch_weather)
        self.fetch_btn.pack(side="left", padx=6)

        # Loading label
        self.loading_var = tk.StringVar(value="")
        tk.Label(search, textvariable=self.loading_var,
                 font=MF_SMALL, bg=M_SURFACE, fg=M_ORANGE
                 ).pack(side="left", padx=12)

        # Auto-save badge
        tk.Label(search, text="💾 Auto-saved",
                 font=MF_SMALL, bg=M_SURFACE, fg=M_ACCENT2
                 ).pack(side="right", padx=16)

        # ── History info strip ────────────────────────────────────────────
        self.hist_strip = tk.Frame(page, bg=M_SEL, height=24)
        self.hist_strip.pack(fill="x", padx=18, pady=(4, 0))
        self.hist_strip.pack_propagate(False)
        self.history_info_var = tk.StringVar(
            value="  📋  Fetch a city to start building your weather history")
        tk.Label(self.hist_strip, textvariable=self.history_info_var,
                 font=MF_SMALL, bg=M_SEL, fg="#ffffff", anchor="w"
                 ).pack(side="left", padx=8)

        # ── Body split: tiles | alerts ────────────────────────────────────
        body = tk.Frame(page, bg=M_BG)
        body.pack(fill="both", expand=True, padx=18, pady=10)

        # Left: weather display area
        self.weather_area = tk.Frame(body, bg=M_BG)
        self.weather_area.pack(side="left", fill="both", expand=True,
                               padx=(0, 10))

        # Placeholder
        self._weather_placeholder = tk.Label(
            self.weather_area,
            text="Enter a city above and click\n⚡ Fetch Weather",
            font=("Segoe UI", 14), bg=M_BG, fg=M_TEXT2, justify="center"
        )
        self._weather_placeholder.pack(expand=True)

        # Right: alerts panel
        alert_card = tk.Frame(body, bg=M_SURFACE, width=240)
        alert_card.pack(side="right", fill="y")
        alert_card.pack_propagate(False)

        tk.Label(alert_card, text="⚠  Weather Alerts",
                 font=MF_HEAD, bg=M_SURFACE, fg=M_RED
                 ).pack(pady=(14, 4), padx=12)

        sep = tk.Frame(alert_card, bg=M_BORDER, height=1)
        sep.pack(fill="x", padx=12)

        self.alerts_text = scrolledtext.ScrolledText(
            alert_card,
            font=MF_SMALL, bg=M_SURFACE, fg=M_TEXT,
            state="disabled", wrap="word", relief="flat", bd=0
        )
        self.alerts_text.pack(fill="both", expand=True, padx=8, pady=8)

    # ── Fetch flow (same logic as classic, calls shared helpers) ──────────

    def _fetch_weather(self):
        _PH = "e.g. Hyderabad  or  Hyderabad, IN"
        city = self.city_var.get().strip()
        if not city or city == _PH:
            messagebox.showwarning("Input Required",
                                   "Please type a city name first.\n\n"
                                   "Examples:  Hyderabad, IN  •  London, GB")
            return

        self._start_loading("Resolving city…")
        self.fetch_btn.state(["disabled"])

        def _worker():
            matches = get_all_city_matches(city)
            self.root.after(0, lambda: self._on_matches(city, matches))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_matches(self, query: str, matches: list):
        self._stop_loading()
        self.fetch_btn.state(["!disabled"])

        if not matches:
            messagebox.showerror("City Not Found",
                                 f"No city found for '{query}'.\n\n"
                                 "💡 Try adding a country code:\n"
                                 "   London, GB  |  Paris, FR  |  Mumbai, IN")
            return
        if len(matches) == 1:
            self._confirm_single(matches[0])
        else:
            self._show_picker(matches)

    def _city_label(self, m: dict) -> str:
        parts = [m["name"]]
        if m.get("state"):
            parts.append(m["state"])
        parts.append(m["country"])
        return ", ".join(parts)

    def _confirm_single(self, m: dict):
        label = self._city_label(m)
        if messagebox.askyesno("Confirm City",
                               f"Found:\n\n  📍  {label}\n\nFetch weather?",
                               icon="question"):
            self._do_fetch(m)

    def _show_picker(self, matches: list):
        dlg = tk.Toplevel(self.root)
        dlg.title("Select city")
        dlg.configure(bg=M_BG)
        dlg.resizable(False, True)
        dlg.grab_set()

        tk.Label(dlg,
                 text="Multiple cities match your search.\nChoose the correct one:",
                 font=MF_BODY, bg=M_BG, fg=M_TEXT, justify="center"
                 ).pack(pady=(18, 8))

        rf = tk.Frame(dlg, bg=M_BG)
        rf.pack(fill="x", padx=8, pady=4)

        cv = tk.IntVar(value=0)
        for i, m in enumerate(matches):
            tk.Radiobutton(
                rf, text=f"  📍  {self._city_label(m)}",
                variable=cv, value=i,
                bg=M_BG, fg=M_TEXT,
                selectcolor=M_SEL,
                activebackground=M_BG, activeforeground=M_TEXT,
                font=MF_BODY, anchor="w"
            ).pack(fill="x", padx=16, pady=4)

        bf = tk.Frame(dlg, bg=M_BG)
        bf.pack(pady=16)

        def _ok():
            chosen = matches[cv.get()]
            dlg.destroy()
            self._do_fetch(chosen)

        ttk.Button(bf, text="✅  Fetch Weather",
                   style="Accent.TButton", command=_ok
                   ).pack(side="left", padx=8)
        ttk.Button(bf, text="✖  Cancel",
                   style="Ghost.TButton", command=dlg.destroy
                   ).pack(side="left", padx=8)

        dlg.protocol("WM_DELETE_WINDOW", dlg.destroy)

        dlg.update_idletasks()
        dw = 460
        dh = min(dlg.winfo_reqheight() + 20,
                 int(dlg.winfo_screenheight() * 0.9))
        x = self.root.winfo_rootx() + self.root.winfo_width()  // 2 - dw // 2
        y = self.root.winfo_rooty() + self.root.winfo_height() // 2 - dh // 2
        dlg.geometry(f"{dw}x{dh}+{x}+{y}")

    def _do_fetch(self, m: dict):
        self._start_loading("Fetching live weather…")
        self.fetch_btn.state(["disabled"])
        lat, lon, name, country = m["lat"], m["lon"], m["name"], m["country"]

        def _worker():
            data = fetch_weather_by_coords(lat, lon, name, country)
            self.root.after(0, lambda: self._on_weather_fetched(data))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_weather_fetched(self, data):
        self._stop_loading()
        self.fetch_btn.state(["!disabled"])

        if data is None:
            messagebox.showerror("Failed",
                                 "Could not retrieve weather data.\n\n"
                                 "Check your internet connection and API key.")
            return

        self.last_weather_data = data
        city_name = data["city"]

        save_weather(data)

        self.last_fetched_city = city_name
        self.trend_city_var.set(city_name)
        self.analysis_city_var.set(city_name)

        from storage import load_city_data
        recs = load_city_data(city_name)
        n = len(recs)
        if n == 1:
            hmsg = (f"  📋  First record saved for {city_name}! "
                    f"Fetch again later to build trends.")
        else:
            first = str(recs["date"].min())[:10]
            hmsg = (f"  📋  {city_name}  •  {n} records since {first}  "
                    f"•  Visit Trends page for charts")
        self.history_info_var.set(hmsg)

        self._render_weather(data)
        self._render_alerts(data)
        self._refresh_table()
        self._update_status(f"✅  {city_name}, {data['country']}  —  "
                            f"{data['timestamp']}")

    def _render_weather(self, d: dict):
        """Build the modern tile grid for the current weather page."""
        for w in self.weather_area.winfo_children():
            w.destroy()

        emoji = get_weather_emoji(d.get("condition", ""))

        # ── Hero row: city + big temp ────────────────────────────────────
        hero = tk.Frame(self.weather_area, bg=M_SURFACE)
        hero.pack(fill="x", pady=(0, 8))

        left = tk.Frame(hero, bg=M_SURFACE)
        left.pack(side="left", padx=20, pady=16, fill="both", expand=True)

        tk.Label(left,
                 text=f"{emoji}  {d.get('city', '')}, {d.get('country', '')}",
                 font=MF_BIG, bg=M_SURFACE, fg=M_TEXT
                 ).pack(anchor="w")

        tk.Label(left,
                 text=d.get("description", "").title(),
                 font=("Segoe UI", 12, "italic"),
                 bg=M_SURFACE, fg=M_TEXT2
                 ).pack(anchor="w", pady=(2, 0))

        tk.Label(left,
                 text=f"↓ {d.get('temp_min',0):.1f}  ↑ {d.get('temp_max',0):.1f}  "
                      f"  Feels like {d.get('feels_like',0):.1f}{TEMP_UNIT_LABEL}",
                 font=MF_SMALL, bg=M_SURFACE, fg=M_TEXT2
                 ).pack(anchor="w", pady=(4, 0))

        # Big temperature
        tk.Label(hero,
                 text=f"{d.get('temperature', 0):.1f}{TEMP_UNIT_LABEL}",
                 font=MF_GIANT,
                 bg=M_SURFACE, fg=M_ACCENT
                 ).pack(side="right", padx=30, pady=16)

        # ── Stat tiles row ────────────────────────────────────────────────
        tiles_row = tk.Frame(self.weather_area, bg=M_BG)
        tiles_row.pack(fill="x", pady=(0, 8))

        tiles = [
            ("💧", "Humidity",    f"{d.get('humidity', 0)} %"),
            ("📊", "Pressure",    f"{d.get('pressure', 0)} hPa"),
            ("💨", "Wind",        f"{d.get('wind_speed', 0)} m/s  "
                                  f"{get_wind_direction(d.get('wind_deg', 0))}"),
            ("👁", "Visibility",  f"{d.get('visibility', 0):.1f} km"),
            ("☁", "Cloud Cover", f"{d.get('clouds', 0)} %"),
            ("🌅", "Sunrise",     d.get("sunrise", "N/A")),
            ("🌇", "Sunset",      d.get("sunset",  "N/A")),
            ("📅", "Recorded",    d.get("timestamp", "")[:16]),
        ]

        n_cols = 4
        for i, (icon, label, value) in enumerate(tiles):
            col = i % n_cols
            row = i // n_cols
            tile = tk.Frame(tiles_row, bg=M_SURFACE2,
                            padx=14, pady=12)
            tile.grid(row=row, column=col, sticky="nsew",
                      padx=5, pady=5)
            tiles_row.columnconfigure(col, weight=1)

            tk.Label(tile, text=f"{icon}  {label}",
                     font=MF_SMALL, bg=M_SURFACE2, fg=M_TEXT2
                     ).pack(anchor="w")
            tk.Label(tile, text=value,
                     font=("Segoe UI", 13, "bold"),
                     bg=M_SURFACE2, fg=M_TEXT
                     ).pack(anchor="w", pady=(2, 0))

    def _render_alerts(self, data: dict):
        from analysis import check_weather_alerts
        alerts = check_weather_alerts(data)
        self.alerts_text.configure(state="normal")
        self.alerts_text.delete("1.0", "end")
        if not alerts:
            self.alerts_text.insert("end",
                "✅  No active alerts.\n\nAll conditions are within normal ranges.")
        else:
            for a in alerts:
                self.alerts_text.insert("end", a + "\n\n")
        self.alerts_text.configure(state="disabled")

    # ── Animated loading dots ─────────────────────────────────────────────

    def _start_loading(self, base: str = "Loading"):
        self._loading_base = base
        self._loading_step = 0
        self._animate_loading()

    def _animate_loading(self):
        dots = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.loading_var.set(
            f"{dots[self._loading_step % len(dots)]}  {self._loading_base}")
        self._loading_step += 1
        self._anim_job = self.root.after(80, self._animate_loading)

    def _stop_loading(self):
        if self._anim_job:
            self.root.after_cancel(self._anim_job)
            self._anim_job = None
        self.loading_var.set("")

    # ─────────────────────────────────────────────────────────────────────
    # PAGE 2 — Compare Cities
    # ─────────────────────────────────────────────────────────────────────

    def _build_page_compare(self, page):
        self._section_title(page, "⚖  Compare Two Cities")

        ctrl = tk.Frame(page, bg=M_SURFACE, pady=12)
        ctrl.pack(fill="x", padx=18, pady=(0, 10))

        for lbl_text, var_attr in [("City 1:", "cmp_c1"), ("City 2:", "cmp_c2")]:
            tk.Label(ctrl, text=lbl_text, font=MF_BODY,
                     bg=M_SURFACE, fg=M_TEXT
                     ).pack(side="left", padx=(14, 6))
            var = tk.StringVar()
            setattr(self, var_attr + "_var", var)
            ttk.Entry(ctrl, textvariable=var, font=MF_BODY, width=18
                      ).pack(side="left", padx=(0, 12), ipady=5)

        self.cmp_btn = ttk.Button(ctrl, text="🔍  Compare",
                                  style="Accent.TButton",
                                  command=self._compare)
        self.cmp_btn.pack(side="left", padx=6)

        self.cmp_loading_var = tk.StringVar(value="")
        tk.Label(ctrl, textvariable=self.cmp_loading_var,
                 font=MF_SMALL, bg=M_SURFACE, fg=M_ORANGE
                 ).pack(side="left", padx=10)

        self.cmp_area = tk.Frame(page, bg=M_BG)
        self.cmp_area.pack(fill="both", expand=True, padx=18, pady=4)

        tk.Label(self.cmp_area,
                 text="Enter two cities above and click 🔍 Compare",
                 font=("Segoe UI", 13), bg=M_BG, fg=M_TEXT2
                 ).pack(expand=True)

    def _compare(self):
        c1 = self.cmp_c1_var.get().strip()
        c2 = self.cmp_c2_var.get().strip()
        if not c1 or not c2:
            messagebox.showwarning("Input Required", "Enter both city names.")
            return
        if c1.lower() == c2.lower():
            messagebox.showwarning("Same City", "Enter two different cities.")
            return

        self.cmp_loading_var.set("⏳ Fetching…")
        self.cmp_btn.state(["disabled"])

        def _w():
            d1 = fetch_weather(c1)
            d2 = fetch_weather(c2)
            self.root.after(0, lambda: self._on_compare(d1, d2))

        threading.Thread(target=_w, daemon=True).start()

    def _on_compare(self, d1, d2):
        self.cmp_loading_var.set("")
        self.cmp_btn.state(["!disabled"])

        if d1 is None or d2 is None:
            failed = ([self.cmp_c1_var.get()] if d1 is None else []) + \
                     ([self.cmp_c2_var.get()] if d2 is None else [])
            messagebox.showerror("Not Found",
                                 f"Could not fetch: {', '.join(failed)}\n"
                                 "Try adding a country code.")
            return

        result = compare_cities(d1, d2)
        self.last_compare_result = result
        self._render_compare(result)
        self._update_status(f"⚖  Compared {d1['city']} vs {d2['city']}")

    def _render_compare(self, r: dict):
        for w in self.cmp_area.winfo_children():
            w.destroy()

        diff   = r.get("temp_difference", 0)
        hotter = r.get("hotter_city", "—")
        banner = (f"🔥 {hotter} is warmer by {diff}{TEMP_UNIT_LABEL}"
                  if diff > 0 else "🤝 Same temperature")

        tk.Label(self.cmp_area, text=banner,
                 font=("Segoe UI", 13, "bold"),
                 bg=M_BG, fg=M_ACCENT2
                 ).pack(pady=(6, 2))
        tk.Label(self.cmp_area,
                 text=f"💧 {r.get('more_humid_city','—')} is more humid",
                 font=MF_BODY, bg=M_BG, fg=M_ACCENT
                 ).pack(pady=(0, 10))

        cards = tk.Frame(self.cmp_area, bg=M_BG)
        cards.pack(fill="both", expand=True)
        cards.columnconfigure(0, weight=1)
        cards.columnconfigure(1, weight=1)

        for num, col in [(1, 0), (2, 1)]:
            p = f"city{num}_"
            city    = r.get(f"city{num}",          "N/A")
            country = r.get(f"city{num}_country",  "")
            temp    = r.get(f"{p}temp",            0)
            feels   = r.get(f"{p}feels_like",      0)
            hum     = r.get(f"{p}humidity",        0)
            pres    = r.get(f"{p}pressure",        0)
            wind    = r.get(f"{p}wind",            0)
            cond    = r.get(f"{p}condition",       "N/A")
            desc    = r.get(f"{p}desc",            "")
            emj     = get_weather_emoji(cond)

            card = tk.Frame(cards, bg=M_SURFACE, padx=16, pady=16)
            card.grid(row=0, column=col, sticky="nsew", padx=8, pady=4)

            tk.Label(card, text=f"{emj}  {city}, {country}",
                     font=MF_HEAD, bg=M_SURFACE, fg=M_TEXT
                     ).pack(anchor="w")
            tk.Label(card, text=desc.title(),
                     font=("Segoe UI", 10, "italic"),
                     bg=M_SURFACE, fg=M_TEXT2
                     ).pack(anchor="w", pady=(2, 6))
            tk.Label(card, text=f"{temp:.1f}{TEMP_UNIT_LABEL}",
                     font=MF_GIANT, bg=M_SURFACE, fg=M_ACCENT
                     ).pack()
            tk.Label(card, text=f"Feels like {feels:.1f}{TEMP_UNIT_LABEL}",
                     font=MF_SMALL, bg=M_SURFACE, fg=M_TEXT2
                     ).pack(pady=(0, 10))

            sep = tk.Frame(card, bg=M_BORDER, height=1)
            sep.pack(fill="x")

            for lbl, val in [("💧 Humidity", f"{hum} %"),
                              ("📊 Pressure", f"{pres} hPa"),
                              ("💨 Wind",     f"{wind} m/s")]:
                row_f = tk.Frame(card, bg=M_SURFACE)
                row_f.pack(fill="x", pady=3)
                tk.Label(row_f, text=lbl, font=MF_SMALL,
                         bg=M_SURFACE, fg=M_TEXT2, width=14, anchor="w"
                         ).pack(side="left")
                tk.Label(row_f, text=val, font=("Segoe UI", 10, "bold"),
                         bg=M_SURFACE, fg=M_TEXT, anchor="e"
                         ).pack(side="right")

    # ─────────────────────────────────────────────────────────────────────
    # PAGE 3 — Trends & Charts
    # ─────────────────────────────────────────────────────────────────────

    def _build_page_trends(self, page):
        self._section_title(page, "📈  Trends & Charts")

        ctrl = tk.Frame(page, bg=M_SURFACE, pady=10)
        ctrl.pack(fill="x", padx=18, pady=(0, 6))

        tk.Label(ctrl, text="📍 City:", font=MF_BODY,
                 bg=M_SURFACE, fg=M_TEXT
                 ).pack(side="left", padx=(14, 8))

        self.trend_city_var = tk.StringVar()
        ttk.Entry(ctrl, textvariable=self.trend_city_var,
                  font=MF_BODY, width=22
                  ).pack(side="left", padx=(0, 10), ipady=5)

        for text, cmd in [("🌡 Temperature", self._trend_temp),
                          ("📊 Humidity & Pressure", self._trend_hum),
                          ("📅 Monthly Averages",    self._trend_monthly)]:
            ttk.Button(ctrl, text=text, style="Ghost.TButton",
                       command=cmd
                       ).pack(side="left", padx=4)

        info = tk.Frame(page, bg="#0d1e38", height=26)
        info.pack(fill="x", padx=18, pady=(0, 4))
        info.pack_propagate(False)
        tk.Label(info,
                 text="  ℹ  History is built automatically — fetch the same city on "
                      "multiple days to grow your dataset.",
                 font=MF_SMALL, bg="#0d1e38", fg=M_TEXT2, anchor="w"
                 ).pack(side="left", padx=8)

        self.chart_frame = tk.Frame(page, bg=M_BG)
        self.chart_frame.pack(fill="both", expand=True, padx=18, pady=4)

        tk.Label(self.chart_frame,
                 text="📍 Enter a city and click a chart button",
                 font=("Segoe UI", 13), bg=M_BG, fg=M_TEXT2
                 ).pack(expand=True)

    def _trend_temp(self):
        city = self.trend_city_var.get().strip()
        if not city:
            messagebox.showwarning("Input Required", "Enter a city name first.")
            return
        df = get_temperature_trend(city)
        if df.empty:
            messagebox.showinfo("No History",
                                f"No data for '{city}'. Fetch it first.")
            return
        plot_temperature_trend(self.chart_frame, city.title(), df)
        self._update_status(f"📈 Temperature trend — {city}")

    def _trend_hum(self):
        city = self.trend_city_var.get().strip()
        if not city:
            messagebox.showwarning("Input Required", "Enter a city name first.")
            return
        df = get_humidity_pressure_data(city)
        if df.empty:
            messagebox.showinfo("No History",
                                f"No data for '{city}'. Fetch it first.")
            return
        plot_humidity_pressure(self.chart_frame, city.title(), df)
        self._update_status(f"📊 Humidity/Pressure — {city}")

    def _trend_monthly(self):
        city = self.trend_city_var.get().strip()
        if not city:
            messagebox.showwarning("Input Required", "Enter a city name first.")
            return
        df = get_monthly_averages(city)
        if df.empty:
            messagebox.showinfo("No History",
                                f"No monthly data for '{city}'.")
            return
        plot_monthly_averages(self.chart_frame, city.title(), df)
        self._update_status(f"📅 Monthly averages — {city}")

    # ─────────────────────────────────────────────────────────────────────
    # PAGE 4 — Analysis
    # ─────────────────────────────────────────────────────────────────────

    def _build_page_analysis(self, page):
        self._section_title(page, "📊  Analysis")

        ctrl = tk.Frame(page, bg=M_SURFACE, pady=10)
        ctrl.pack(fill="x", padx=18, pady=(0, 6))

        tk.Label(ctrl, text="📍 City (optional):", font=MF_BODY,
                 bg=M_SURFACE, fg=M_TEXT
                 ).pack(side="left", padx=(14, 8))

        self.analysis_city_var = tk.StringVar()
        ttk.Entry(ctrl, textvariable=self.analysis_city_var,
                  font=MF_BODY, width=20
                  ).pack(side="left", padx=(0, 10), ipady=5)

        for text, cmd in [("🔥 Hottest",    self._hottest),
                          ("🧊 Coldest",    self._coldest),
                          ("📈 Statistics", self._stats),
                          ("🏙 All Cities", self._all_cities)]:
            ttk.Button(ctrl, text=text, style="Ghost.TButton",
                       command=cmd
                       ).pack(side="left", padx=4)

        self.analysis_text = scrolledtext.ScrolledText(
            page, font=MF_MONO, bg=M_SURFACE, fg=M_TEXT,
            state="disabled", wrap="word", relief="flat", bd=0
        )
        self.analysis_text.pack(fill="both", expand=True, padx=18, pady=8)

        self._write_analysis(
            "\n  Welcome to the Analysis Panel!\n\n"
            "  ► Enter a city then click a button above.\n"
            "  ► Leave city blank for all stored cities.\n\n"
            "  Fetch some weather data first to populate results.")

    def _write_analysis(self, text: str):
        self.analysis_text.configure(state="normal")
        self.analysis_text.delete("1.0", "end")
        self.analysis_text.insert("end", text)
        self.analysis_text.configure(state="disabled")

    def _hottest(self):
        city = self.analysis_city_var.get().strip() or None
        r = get_hottest_day(city)
        if not r:
            self._write_analysis(
                f"\n  ❌  No data found{' for ' + city if city else ''}.\n\n"
                "  Please fetch weather data first.")
            return
        self._write_analysis(
            f"\n  🔥  HOTTEST DAY\n  {'─'*40}\n"
            f"  City        : {r['city']}\n"
            f"  Date        : {r['date']}\n"
            f"  Temperature : {r['temperature']}{TEMP_UNIT_LABEL}\n"
            f"  Condition   : {r['condition']}\n"
            f"  Humidity    : {r['humidity']} %\n")

    def _coldest(self):
        city = self.analysis_city_var.get().strip() or None
        r = get_coldest_day(city)
        if not r:
            self._write_analysis(
                f"\n  ❌  No data found{' for ' + city if city else ''}.\n\n"
                "  Please fetch weather data first.")
            return
        self._write_analysis(
            f"\n  🧊  COLDEST DAY\n  {'─'*40}\n"
            f"  City        : {r['city']}\n"
            f"  Date        : {r['date']}\n"
            f"  Temperature : {r['temperature']}{TEMP_UNIT_LABEL}\n"
            f"  Condition   : {r['condition']}\n"
            f"  Humidity    : {r['humidity']} %\n")

    def _stats(self):
        city = self.analysis_city_var.get().strip()
        if not city:
            messagebox.showinfo("City Required",
                                "Enter a city name for statistics.")
            return
        s = get_statistics_summary(city)
        if "error" in s:
            self._write_analysis(f"\n  ❌  {s['error']}")
            return
        self._write_analysis(
            f"\n  📊  STATISTICS — {s['city'].upper()}\n  {'─'*40}\n"
            f"  Records    : {s['total_records']}\n"
            f"  Date Range : {s['first_record']}  →  {s['last_record']}\n\n"
            f"  TEMPERATURE\n"
            f"  avg {s['avg_temp']}{TEMP_UNIT_LABEL}   min {s['min_temp']}{TEMP_UNIT_LABEL}"
            f"   max {s['max_temp']}{TEMP_UNIT_LABEL}   σ {s['temp_std']}{TEMP_UNIT_LABEL}\n\n"
            f"  HUMIDITY\n"
            f"  avg {s['avg_humidity']}%   min {s['min_humidity']}%"
            f"   max {s['max_humidity']}%\n\n"
            f"  PRESSURE\n"
            f"  avg {s['avg_pressure']} hPa   min {s['min_pressure']} hPa"
            f"   max {s['max_pressure']} hPa\n\n"
            f"  Wind (avg)  : {s['avg_wind_speed']} m/s\n"
            f"  Common Cond.: {s['most_common_cond']}\n")

    def _all_cities(self):
        cities = get_all_cities()
        if not cities:
            self._write_analysis("\n  📭  No data stored yet.")
            return
        text = f"\n  🏙  CITIES  ({len(cities)})\n  {'─'*40}\n"
        for i, c in enumerate(cities, 1):
            text += f"  {i:3}.  {c}\n"
        self._write_analysis(text)

    # ─────────────────────────────────────────────────────────────────────
    # PAGE 5 — Data Log
    # ─────────────────────────────────────────────────────────────────────

    def _build_page_datalog(self, page):
        self._section_title(page, "🗃  Data Log")

        ctrl = tk.Frame(page, bg=M_SURFACE, pady=8)
        ctrl.pack(fill="x", padx=18, pady=(0, 6))

        ttk.Button(ctrl, text="🔄  Refresh",
                   style="Ghost.TButton",
                   command=self._refresh_table
                   ).pack(side="left", padx=(14, 8))

        self.rec_count_var = tk.StringVar(value="Records: —")
        tk.Label(ctrl, textvariable=self.rec_count_var,
                 font=MF_BODY, bg=M_SURFACE, fg=M_ACCENT
                 ).pack(side="left", padx=8)

        tk.Label(ctrl, text="🔍 Filter:", font=MF_SMALL,
                 bg=M_SURFACE, fg=M_TEXT2
                 ).pack(side="left", padx=(20, 6))

        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *_: self._apply_filter())
        ttk.Entry(ctrl, textvariable=self.filter_var,
                  font=MF_SMALL, width=18
                  ).pack(side="left", padx=(0, 8), ipady=3)

        # Table
        tbl = tk.Frame(page, bg=M_BG)
        tbl.pack(fill="both", expand=True, padx=18, pady=(0, 10))

        cols = ("date", "city", "country", "temp",
                "humidity", "pressure", "wind", "condition")
        self.tree = ttk.Treeview(tbl, columns=cols,
                                 show="headings", selectmode="browse")

        cfg = {
            "date":      ("📅 Date",         100),
            "city":      ("🏙 City",          110),
            "country":   ("🌐 Country",        70),
            "temp":      (f"🌡 Temp",          80),
            "humidity":  ("💧 Humidity %",     90),
            "pressure":  ("📊 Pressure hPa",  100),
            "wind":      ("💨 Wind m/s",        85),
            "condition": ("⛅ Condition",      110),
        }
        for col, (head, width) in cfg.items():
            self.tree.heading(col, text=head)
            self.tree.column(col,  width=width, anchor="center", minwidth=50)

        vsb = ttk.Scrollbar(tbl, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(tbl, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tbl.rowconfigure(0, weight=1)
        tbl.columnconfigure(0, weight=1)

        self.tree.tag_configure("odd",  background=M_SURFACE)
        self.tree.tag_configure("even", background=M_SURFACE2)

        self._refresh_table()

    def _refresh_table(self):
        df = load_all_data()
        self._all_records = df
        self._populate_tree(df)
        n = len(df)
        self.rec_count_var.set(f"Records: {n}")
        self._update_status(f"🗃  Data log refreshed — {n} records")

    def _apply_filter(self):
        q = self.filter_var.get().strip().lower()
        if hasattr(self, "_all_records") and not self._all_records.empty:
            filtered = (self._all_records[
                self._all_records["city"].str.lower().str.contains(q, na=False)]
                if q else self._all_records)
            self._populate_tree(filtered)

    def _populate_tree(self, df):
        for item in self.tree.get_children():
            self.tree.delete(item)
        if df.empty:
            return
        for idx, row in df.iterrows():
            tag = "odd" if idx % 2 == 0 else "even"
            self.tree.insert("", "end", tag=tag, values=(
                str(row.get("date", ""))[:10],
                row.get("city",        ""),
                row.get("country",     ""),
                f"{row.get('temperature',''):.1f}"
                if pd.notna(row.get("temperature")) else "",
                row.get("humidity",   ""),
                row.get("pressure",   ""),
                row.get("wind_speed", ""),
                row.get("condition",  ""),
            ))


# =============================================================================
if __name__ == "__main__":
    root = tk.Tk()
    ModernWeatherApp(root)
    root.mainloop()
