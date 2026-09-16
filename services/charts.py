"""
Weather analytics & chart generation using Matplotlib.
Renders visually striking 24-hour temperature and rain probability charts for Telegram.
"""
import io
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
from typing import Dict, Any, Optional

def generate_weather_chart(weather_data: Dict[str, Any], city_name: str, lang: str = "bn") -> Optional[io.BytesIO]:
    """
    Generate a dual-plot chart:
    Top: 24-Hour Temperature Curve (°C)
    Bottom: Rain Probability Bars (%)
    Returns BytesIO containing the PNG image.
    """
    hourly = weather_data.get("hourly", {})
    times = hourly.get("time", [])[:24]
    temps = hourly.get("temperature_2m", [])[:24]
    rain_probs = hourly.get("precipitation_probability", [])[:24]

    if not times or not temps:
        return None

    # Format time labels (e.g. "14:00", "17:00")
    formatted_hours = [t.split("T")[1][:5] for t in times]

    # Chart Styling
    plt.style.use("dark_background")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True, gridspec_kw={'height_ratios': [2, 1]})
    fig.patch.set_facecolor('#1e1e2e')
    ax1.set_facecolor('#1e1e2e')
    ax2.set_facecolor('#1e1e2e')

    # Top Plot: Temperature
    line_color = '#f38ba8' if max(temps) > 28 else '#89b4fa'
    ax1.plot(formatted_hours, temps, color=line_color, linewidth=2.5, marker='o', markersize=4, label='Temperature (°C)')
    ax1.fill_between(formatted_hours, temps, min(temps) - 2, color=line_color, alpha=0.2)
    
    temp_title = f"24-Hour Temperature & Rain Forecast — {city_name}"
    ax1.set_title(temp_title, fontsize=14, fontweight='bold', color='#cdd6f4', pad=12)
    ax1.set_ylabel('Temp (°C)', color='#cdd6f4', fontsize=11)
    ax1.grid(True, linestyle='--', alpha=0.2, color='#6c7086')
    ax1.tick_params(colors='#bac2de')

    # Annotate max and min temp on line
    max_t = max(temps)
    min_t = min(temps)
    max_idx = temps.index(max_t)
    min_idx = temps.index(min_t)
    ax1.annotate(f"{max_t:.1f}°C", (formatted_hours[max_idx], max_t), textcoords="offset points", xytext=(0, 7),
                 ha='center', fontsize=10, color='#f9e2af', fontweight='bold')
    ax1.annotate(f"{min_t:.1f}°C", (formatted_hours[min_idx], min_t), textcoords="offset points", xytext=(0, -14),
                 ha='center', fontsize=10, color='#a6e3a1', fontweight='bold')

    # Bottom Plot: Rain Probability
    bar_color = '#74c7ec'
    ax2.bar(formatted_hours, rain_probs, color=bar_color, alpha=0.85, width=0.6, label='Rain Probability (%)')
    ax2.set_ylabel('Rain Prob (%)', color='#cdd6f4', fontsize=11)
    ax2.set_ylim(0, 100)
    ax2.grid(True, linestyle='--', alpha=0.2, color='#6c7086')
    ax2.tick_params(colors='#bac2de')

    # X-axis formatting: show label every 3 hours
    plt.xticks(range(0, len(formatted_hours), 3), formatted_hours[::3], rotation=0, fontsize=10)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=130, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf
