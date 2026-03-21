# =============================================================================
# charts.py - Matplotlib Chart Generation Module
# =============================================================================
# This module handles all chart/graph creation using Matplotlib.
# Charts are embedded directly inside the Tkinter GUI window using
# FigureCanvasTkAgg — no external windows needed.
#
# Charts available:
#   1. Temperature trend line graph
#   2. Humidity & Pressure bar charts
#   3. City comparison bar chart
#   4. Weekly/Monthly average charts
# =============================================================================

import matplotlib
matplotlib.use("TkAgg")                            # Use Tkinter-compatible backend

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import pandas as pd
from config import TEMP_UNIT_LABEL


# =============================================================================
# ── Colour Palette ────────────────────────────────────────────────────────────
# A consistent dark theme for all charts matching the GUI
# =============================================================================
CHART_BG      = "#1a1a2e"
AXIS_BG       = "#16213e"
GRID_COLOR    = "#2a2a4e"
TEXT_COLOR    = "#eaeaea"
COLOR_TEMP    = "#e94560"
COLOR_FEEL    = "#ff9800"
COLOR_MIN     = "#00b4d8"
COLOR_MAX     = "#f72585"
COLOR_HUM     = "#4cc9f0"
COLOR_PRES    = "#7209b7"
COLOR_BAR1    = "#e94560"
COLOR_BAR2    = "#00b4d8"


def _apply_dark_style(ax, fig):
    """Apply the dark theme to a Matplotlib axes/figure consistently."""
    fig.patch.set_facecolor(CHART_BG)
    ax.set_facecolor(AXIS_BG)
    ax.tick_params(colors=TEXT_COLOR, labelsize=9)
    ax.xaxis.label.set_color(TEXT_COLOR)
    ax.yaxis.label.set_color(TEXT_COLOR)
    ax.title.set_color(TEXT_COLOR)
    ax.spines["bottom"].set_color(GRID_COLOR)
    ax.spines["top"].set_color(GRID_COLOR)
    ax.spines["left"].set_color(GRID_COLOR)
    ax.spines["right"].set_color(GRID_COLOR)
    ax.grid(True, color=GRID_COLOR, linestyle="--", alpha=0.6)


# =============================================================================
# ── Chart 1: Temperature Trend Line Graph ────────────────────────────────────
# =============================================================================

def plot_temperature_trend(parent_frame, city_name: str, trend_df: pd.DataFrame):
    """
    Draw a line graph showing temperature trends over time for a city.
    Embeds the chart into the given Tkinter parent_frame.

    Args:
        parent_frame: Tkinter widget to embed the chart inside.
        city_name (str): Name of the city (for title).
        trend_df (pd.DataFrame): Output from analysis.get_temperature_trend().
    """
    # Clear any existing widgets in the frame
    for widget in parent_frame.winfo_children():
        widget.destroy()

    if trend_df.empty:
        _show_no_data_message(parent_frame, city_name)
        return

    # Create the Matplotlib figure
    fig = Figure(figsize=(9, 4), dpi=100)
    ax  = fig.add_subplot(111)

    dates = trend_df["date"]

    # Plot each temperature line
    ax.plot(dates, trend_df["temperature"], color=COLOR_TEMP,  lw=2,
            marker="o", ms=5, label=f"Avg Temp ({TEMP_UNIT_LABEL})")
    ax.plot(dates, trend_df["feels_like"],  color=COLOR_FEEL,  lw=1.5,
            linestyle="--", marker="s", ms=4, label="Feels Like")
    ax.plot(dates, trend_df["temp_min"],    color=COLOR_MIN,   lw=1.5,
            linestyle=":", marker="^", ms=4, label="Min Temp")
    ax.plot(dates, trend_df["temp_max"],    color=COLOR_MAX,   lw=1.5,
            linestyle=":", marker="v", ms=4, label="Max Temp")

    # Shade area between min and max temperature
    ax.fill_between(dates, trend_df["temp_min"], trend_df["temp_max"],
                    alpha=0.1, color=COLOR_TEMP)

    # Titles & labels
    ax.set_title(f"🌡️  Temperature Trend — {city_name}", fontsize=12, pad=10)
    ax.set_xlabel("Date", fontsize=10)
    ax.set_ylabel(f"Temperature ({TEMP_UNIT_LABEL})", fontsize=10)

    # Format x-axis dates nicely
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    fig.autofmt_xdate(rotation=30)

    # Legend
    legend = ax.legend(facecolor=AXIS_BG, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR,
                       fontsize=8)

    _apply_dark_style(ax, fig)
    fig.tight_layout()

    # Embed chart into Tkinter frame
    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)


# =============================================================================
# ── Chart 2: Humidity & Pressure Bar Charts ──────────────────────────────────
# =============================================================================

def plot_humidity_pressure(parent_frame, city_name: str, hp_df: pd.DataFrame):
    """
    Draw side-by-side bar charts for humidity and pressure over time.
    Embeds the chart into the given Tkinter parent_frame.

    Args:
        parent_frame: Tkinter widget to embed the chart inside.
        city_name (str): Name of the city (for title).
        hp_df (pd.DataFrame): Output from analysis.get_humidity_pressure_data().
    """
    for widget in parent_frame.winfo_children():
        widget.destroy()

    if hp_df.empty:
        _show_no_data_message(parent_frame, city_name)
        return

    # Create a figure with 2 subplots stacked vertically
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 5), dpi=100)

    date_labels = [str(d)[:10] for d in hp_df["date"]]
    x_pos       = range(len(date_labels))

    # ── Top subplot: Humidity ──
    bars1 = ax1.bar(x_pos, hp_df["humidity"], color=COLOR_HUM, alpha=0.85, width=0.6)
    ax1.set_title(f"💧  Humidity Trend — {city_name}", fontsize=11)
    ax1.set_ylabel("Humidity (%)", fontsize=9)
    ax1.set_xticks(list(x_pos))
    ax1.set_xticklabels(date_labels, rotation=30, ha="right", fontsize=8)
    # Add value labels on top of each bar
    for bar in bars1:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2., h + 0.5,
                 f"{h:.0f}%", ha="center", va="bottom",
                 fontsize=7, color=TEXT_COLOR)

    # ── Bottom subplot: Pressure ──
    bars2 = ax2.bar(x_pos, hp_df["pressure"], color=COLOR_PRES, alpha=0.85, width=0.6)
    ax2.set_title(f"📊  Pressure Trend — {city_name}", fontsize=11)
    ax2.set_ylabel("Pressure (hPa)", fontsize=9)
    ax2.set_xticks(list(x_pos))
    ax2.set_xticklabels(date_labels, rotation=30, ha="right", fontsize=8)
    for bar in bars2:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2., h + 0.5,
                 f"{h:.0f}", ha="center", va="bottom",
                 fontsize=7, color=TEXT_COLOR)

    # Apply dark theme to both axes
    for ax, f in [(ax1, fig), (ax2, fig)]:
        _apply_dark_style(ax, f)

    fig.patch.set_facecolor(CHART_BG)
    fig.tight_layout(pad=2.0)

    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)


# =============================================================================
# ── Chart 3: City Comparison Bar Chart ───────────────────────────────────────
# =============================================================================

def plot_city_comparison(parent_frame, comparison: dict):
    """
    Draw a grouped bar chart comparing weather metrics of two cities.

    Args:
        parent_frame: Tkinter widget to embed the chart inside.
        comparison (dict): Output from analysis.compare_cities().
    """
    for widget in parent_frame.winfo_children():
        widget.destroy()

    if not comparison or "error" in comparison:
        _show_no_data_message(parent_frame, "Comparison")
        return

    city1 = comparison.get("city1", "City 1")
    city2 = comparison.get("city2", "City 2")

    # Metrics to compare
    metrics  = ["Temperature (°C)", "Humidity (%)", "Pressure (hPa)", "Wind (m/s)"]
    values1  = [
        comparison.get("city1_temp",     0),
        comparison.get("city1_humidity", 0),
        comparison.get("city1_pressure", 0) / 10,   # Scale down for visual balance
        comparison.get("city1_wind",     0),
    ]
    values2  = [
        comparison.get("city2_temp",     0),
        comparison.get("city2_humidity", 0),
        comparison.get("city2_pressure", 0) / 10,
        comparison.get("city2_wind",     0),
    ]

    fig = Figure(figsize=(9, 4), dpi=100)
    ax  = fig.add_subplot(111)

    x      = range(len(metrics))
    width  = 0.35

    # Draw grouped bars
    bars1 = ax.bar([i - width/2 for i in x], values1, width,
                   label=city1, color=COLOR_BAR1, alpha=0.85)
    bars2 = ax.bar([i + width/2 for i in x], values2, width,
                   label=city2, color=COLOR_BAR2, alpha=0.85)

    # Add value labels above bars
    for bar in bars1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 0.3,
                f"{h:.1f}", ha="center", va="bottom", fontsize=8, color=TEXT_COLOR)
    for bar in bars2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 0.3,
                f"{h:.1f}", ha="center", va="bottom", fontsize=8, color=TEXT_COLOR)

    ax.set_title(f"🌍  City Comparison: {city1} vs {city2}", fontsize=12)
    ax.set_ylabel("Value", fontsize=10)
    ax.set_xticks(list(x))
    ax.set_xticklabels(metrics, fontsize=9)
    ax.legend(facecolor=AXIS_BG, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR, fontsize=9)

    # Note about scaled pressure
    ax.annotate("* Pressure divided by 10 for visual scale",
                xy=(0.01, 0.02), xycoords="axes fraction",
                fontsize=7, color="#aaaaaa")

    _apply_dark_style(ax, fig)
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)


# =============================================================================
# ── Chart 4: Monthly/Weekly Averages ─────────────────────────────────────────
# =============================================================================

def plot_monthly_averages(parent_frame, city_name: str, monthly_df: pd.DataFrame):
    """
    Draw a multi-line chart for monthly average temperature, humidity, pressure.

    Args:
        parent_frame: Tkinter widget to embed the chart.
        city_name (str): City name for title.
        monthly_df (pd.DataFrame): Output from analysis.get_monthly_averages().
    """
    for widget in parent_frame.winfo_children():
        widget.destroy()

    if monthly_df.empty:
        _show_no_data_message(parent_frame, city_name)
        return

    fig, ax = plt.subplots(figsize=(9, 4), dpi=100)

    months = monthly_df["month"].astype(str)
    x_pos  = range(len(months))

    ax.plot(list(x_pos), monthly_df["avg_temp"],
            color=COLOR_TEMP, lw=2, marker="o", ms=6, label="Avg Temp (°C)")
    ax.plot(list(x_pos), monthly_df["avg_humidity"],
            color=COLOR_HUM,  lw=2, marker="s", ms=5, label="Avg Humidity (%)")

    ax.set_title(f"📅  Monthly Averages — {city_name}", fontsize=12)
    ax.set_xlabel("Month", fontsize=10)
    ax.set_ylabel("Value", fontsize=10)
    ax.set_xticks(list(x_pos))
    ax.set_xticklabels(list(months), rotation=30, ha="right", fontsize=8)
    ax.legend(facecolor=AXIS_BG, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR, fontsize=9)

    _apply_dark_style(ax, fig)
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)


# =============================================================================
# ── Helper: No Data Message ───────────────────────────────────────────────────
# =============================================================================

def _show_no_data_message(parent_frame, city_name: str):
    """Display a placeholder chart when no data is available."""
    import tkinter as tk

    lbl = tk.Label(
        parent_frame,
        text=f"📭  No stored data found for '{city_name}'.\n\n"
             "Fetch weather data first, then view trends.",
        font=("Segoe UI", 12),
        bg="#1a1a2e",
        fg="#aaaaaa",
        justify="center",
    )
    lbl.pack(expand=True)
