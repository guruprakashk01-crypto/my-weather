"""
main.py
A modern, user-friendly Weather Application built with Python and Tkinter.
Communicates with OpenWeatherMap REST API to fetch and display real-time weather.
"""

import os
import sys
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# Import our custom API helper module
import weather_api
from weather_api import WeatherAPIError, fetch_weather_data, get_api_key

# ----------------- UI Color Palette & Styling -----------------
BG_MAIN = "#0f172a"        # Dark slate background
BG_CARD = "#1e293b"        # Card container background
BG_SUB_CARD = "#334155"    # Metric sub-card background
TEXT_MAIN = "#f8fafc"      # Bright white text
TEXT_MUTED = "#94a3b8"     # Secondary subtle grey text
ACCENT_BLUE = "#38bdf8"    # Sky blue accent
ACCENT_HOVER = "#0284c7"   # Deeper blue hover
BORDER_COLOR = "#475569"   # Card border subtle grey


class WeatherApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Weather Forecast App")
        self.root.geometry("480x700")
        self.root.minsize(420, 620)
        self.root.configure(bg=BG_MAIN)

        # Track active units: 'metric' (°C) or 'imperial' (°F)
        self.unit_var = tk.StringVar(value="metric")

        # Build UI layout
        self._setup_styles()
        self._build_header()
        self._build_search_bar()
        self._build_quick_chips()
        self._build_weather_display()
        self._build_footer()

        # Check API key configuration on launch
        self.root.after(300, self._check_initial_api_key)

    def _setup_styles(self):
        """Configure ttk styles for clean appearance."""
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Radio button styling for unit selector
        self.style.configure(
            "Unit.TRadiobutton",
            background=BG_MAIN,
            foreground=TEXT_MUTED,
            font=("Segoe UI", 9, "bold"),
            focuscolor=BG_MAIN,
        )
        self.style.map(
            "Unit.TRadiobutton",
            foreground=[("selected", ACCENT_BLUE), ("active", TEXT_MAIN)],
            background=[("selected", BG_MAIN), ("active", BG_MAIN)],
        )

    def _build_header(self):
        """Creates top title header and settings button."""
        header_frame = tk.Frame(self.root, bg=BG_MAIN)
        header_frame.pack(fill="x", padx=24, pady=(20, 10))

        title_label = tk.Label(
            header_frame,
            text="🌤️ Weather App",
            font=("Segoe UI", 20, "bold"),
            fg=TEXT_MAIN,
            bg=BG_MAIN,
        )
        title_label.pack(side="left")

        # API Key Settings Button
        self.key_btn = tk.Button(
            header_frame,
            text="⚙️ API Key",
            font=("Segoe UI", 9, "bold"),
            bg=BG_CARD,
            fg=ACCENT_BLUE,
            activebackground=BG_SUB_CARD,
            activeforeground=TEXT_MAIN,
            relief="flat",
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._open_api_key_dialog,
        )
        self.key_btn.pack(side="right")

    def _build_search_bar(self):
        """Builds city input box, search button, and unit toggle."""
        search_card = tk.Frame(self.root, bg=BG_CARD, padx=14, pady=12, relief="flat")
        search_card.pack(fill="x", padx=24, pady=8)

        # Input & Button Row
        row = tk.Frame(search_card, bg=BG_CARD)
        row.pack(fill="x")

        self.city_entry = tk.Entry(
            row,
            font=("Segoe UI", 12),
            bg=BG_SUB_CARD,
            fg=TEXT_MAIN,
            insertbackground=TEXT_MAIN,
            relief="flat",
            bd=6,
        )
        self.city_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.city_entry.insert(0, "London")
        self.city_entry.bind("<Return>", lambda event: self.search_weather())

        self.search_btn = tk.Button(
            row,
            text="Search",
            font=("Segoe UI", 10, "bold"),
            bg=ACCENT_BLUE,
            fg="#0f172a",
            activebackground=ACCENT_HOVER,
            activeforeground=TEXT_MAIN,
            relief="flat",
            bd=0,
            padx=16,
            pady=6,
            cursor="hand2",
            command=self.search_weather,
        )
        self.search_btn.pack(side="right")

        # Units Toggle Row (°C vs °F)
        unit_row = tk.Frame(search_card, bg=BG_CARD)
        unit_row.pack(fill="x", pady=(10, 0))

        unit_label = tk.Label(
            unit_row,
            text="Temperature Unit:",
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=BG_CARD,
        )
        unit_label.pack(side="left")

        rb_c = ttk.Radiobutton(
            unit_row,
            text="°C (Celsius)",
            value="metric",
            variable=self.unit_var,
            style="Unit.TRadiobutton",
            command=self._on_unit_change,
        )
        rb_c.pack(side="left", padx=(12, 6))

        rb_f = ttk.Radiobutton(
            unit_row,
            text="°F (Fahrenheit)",
            value="imperial",
            variable=self.unit_var,
            style="Unit.TRadiobutton",
            command=self._on_unit_change,
        )
        rb_f.pack(side="left", padx=6)

    def _build_quick_chips(self):
        """Provides quick one-click city suggestions for testing."""
        chip_frame = tk.Frame(self.root, bg=BG_MAIN)
        chip_frame.pack(fill="x", padx=24, pady=(2, 8))

        quick_cities = ["London", "New York", "Tokyo", "Paris", "Sydney"]
        for city in quick_cities:
            btn = tk.Button(
                chip_frame,
                text=city,
                font=("Segoe UI", 8),
                bg=BG_CARD,
                fg=TEXT_MUTED,
                activebackground=BG_SUB_CARD,
                activeforeground=TEXT_MAIN,
                relief="flat",
                bd=0,
                padx=8,
                pady=2,
                cursor="hand2",
                command=lambda c=city: self._quick_search(c),
            )
            btn.pack(side="left", padx=(0, 6))

    def _build_weather_display(self):
        """Constructs the primary weather details card and metric tiles."""
        self.weather_card = tk.Frame(self.root, bg=BG_CARD, padx=20, pady=18)
        self.weather_card.pack(fill="both", expand=True, padx=24, pady=8)

        # Initial Welcome / Placeholder state
        self.placeholder_label = tk.Label(
            self.weather_card,
            text="🔍\n\nEnter a city name above\nand click 'Search' to view\nreal-time weather data.",
            font=("Segoe UI", 12),
            fg=TEXT_MUTED,
            bg=BG_CARD,
            justify="center",
        )
        self.placeholder_label.pack(expand=True, pady=40)

        # Weather Details Container (hidden until first search)
        self.details_container = tk.Frame(self.weather_card, bg=BG_CARD)

        # 1. City & Country Label
        self.city_label = tk.Label(
            self.details_container,
            text="--",
            font=("Segoe UI", 18, "bold"),
            fg=TEXT_MAIN,
            bg=BG_CARD,
        )
        self.city_label.pack(anchor="center", pady=(0, 2))

        # 2. Main Weather Icon / Emoji & Condition Text
        self.condition_emoji = tk.Label(
            self.details_container,
            text="☀️",
            font=("Segoe UI", 48),
            bg=BG_CARD,
        )
        self.condition_emoji.pack(anchor="center")

        # 3. Main Temperature
        self.temp_label = tk.Label(
            self.details_container,
            text="--°C",
            font=("Segoe UI", 34, "bold"),
            fg=ACCENT_BLUE,
            bg=BG_CARD,
        )
        self.temp_label.pack(anchor="center")

        # 4. Description and Feels-Like
        self.desc_label = tk.Label(
            self.details_container,
            text="--",
            font=("Segoe UI", 12, "italic"),
            fg=TEXT_MAIN,
            bg=BG_CARD,
        )
        self.desc_label.pack(anchor="center", pady=(2, 2))

        self.feels_like_label = tk.Label(
            self.details_container,
            text="Feels like: --",
            font=("Segoe UI", 10),
            fg=TEXT_MUTED,
            bg=BG_CARD,
        )
        self.feels_like_label.pack(anchor="center", pady=(0, 14))

        # 5. Grid of Details (Humidity, Wind Speed, Pressure, Condition)
        metrics_grid = tk.Frame(self.details_container, bg=BG_CARD)
        metrics_grid.pack(fill="x", pady=6)
        metrics_grid.columnconfigure(0, weight=1)
        metrics_grid.columnconfigure(1, weight=1)

        # Tile 1: Humidity
        self.tile_humidity_val = self._create_metric_tile(
            metrics_grid, row=0, col=0, icon="💧", title="Humidity", default="--"
        )
        # Tile 2: Wind Speed
        self.tile_wind_val = self._create_metric_tile(
            metrics_grid, row=0, col=1, icon="💨", title="Wind Speed", default="--"
        )
        # Tile 3: Pressure
        self.tile_pressure_val = self._create_metric_tile(
            metrics_grid, row=1, col=0, icon="⏱️", title="Pressure", default="--"
        )
        # Tile 4: Weather Condition
        self.tile_condition_val = self._create_metric_tile(
            metrics_grid, row=1, col=1, icon="☁️", title="Condition", default="--"
        )

    def _create_metric_tile(self, parent, row: int, col: int, icon: str, title: str, default: str) -> tk.Label:
        """Helper to create standardized metric tiles in the 2x2 grid."""
        tile = tk.Frame(parent, bg=BG_SUB_CARD, padx=12, pady=10)
        tile.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        header = tk.Label(
            tile,
            text=f"{icon} {title}",
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=BG_SUB_CARD,
        )
        header.pack(anchor="w")

        val_label = tk.Label(
            tile,
            text=default,
            font=("Segoe UI", 12, "bold"),
            fg=TEXT_MAIN,
            bg=BG_SUB_CARD,
        )
        val_label.pack(anchor="w", pady=(2, 0))
        return val_label

    def _build_footer(self):
        """Status bar and last-updated label."""
        footer_frame = tk.Frame(self.root, bg=BG_MAIN)
        footer_frame.pack(fill="x", padx=24, pady=(6, 12))

        self.status_label = tk.Label(
            footer_frame,
            text="Ready",
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=BG_MAIN,
        )
        self.status_label.pack(side="left")

        self.time_label = tk.Label(
            footer_frame,
            text="",
            font=("Segoe UI", 8),
            fg=TEXT_MUTED,
            bg=BG_MAIN,
        )
        self.time_label.pack(side="right")

    # ----------------- Event Handlers & Logic -----------------

    def _quick_search(self, city: str):
        """Trigger search from one of the quick city chips."""
        self.city_entry.delete(0, tk.END)
        self.city_entry.insert(0, city)
        self.search_weather()

    def _on_unit_change(self):
        """Refetch or refresh data when user toggles between °C and °F."""
        if hasattr(self, "_last_city") and self._last_city:
            self.search_weather()

    def _check_initial_api_key(self):
        """Prompt user with setup guidance if API key is not configured."""
        try:
            get_api_key()
        except WeatherAPIError:
            self.status_label.config(text="⚠️ API key required. Click '⚙️ API Key' to configure.")

    def _open_api_key_dialog(self):
        """Dialog to easily view and update OpenWeatherMap API Key without manual file editing."""
        current_key = os.getenv("OPENWEATHERMAP_API_KEY", "")
        if current_key == "your_api_key_here":
            current_key = ""

        new_key = simpledialog.askstring(
            "API Key Configuration",
            "Enter your OpenWeatherMap API Key:\n\n"
            "(Get a free key from https://openweathermap.org/api)",
            initialvalue=current_key,
            parent=self.root,
        )

        if new_key is not None:
            new_key = new_key.strip()
            if not new_key:
                messagebox.showwarning(
                    "Warning",
                    "API key cannot be empty! Please provide a valid key.",
                    parent=self.root,
                )
                return

            # Save key to .env file
            env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
            try:
                with open(env_path, "w", encoding="utf-8") as f:
                    f.write("# OpenWeatherMap API Configuration\n")
                    f.write(f"OPENWEATHERMAP_API_KEY={new_key}\n")

                os.environ["OPENWEATHERMAP_API_KEY"] = new_key
                self.status_label.config(text="API key updated successfully!")
                messagebox.showinfo(
                    "Success",
                    "API key saved to .env!\nYou can now search for any city.",
                    parent=self.root,
                )
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Failed to write to .env file: {str(e)}",
                    parent=self.root,
                )

    def search_weather(self):
        """Initiate background thread to fetch weather without freezing GUI."""
        city_name = self.city_entry.get().strip()
        if not city_name:
            messagebox.showwarning("Input Required", "Please enter a city name to search.", parent=self.root)
            return

        # Update UI state to loading
        self.search_btn.config(state="disabled", text="Searching...")
        self.status_label.config(text=f"Fetching weather for '{city_name}'...")

        # Run network request in daemon thread so GUI stays fluid
        thread = threading.Thread(target=self._fetch_weather_worker, args=(city_name,), daemon=True)
        thread.start()

    def _fetch_weather_worker(self, city_name: str):
        """Worker thread executing the HTTP GET request."""
        units = self.unit_var.get()
        try:
            weather_data = fetch_weather_data(city_name, units=units)
            # Schedule UI update on Tkinter main thread
            self.root.after(0, self._handle_fetch_success, weather_data)
        except WeatherAPIError as err:
            self.root.after(0, self._handle_fetch_error, str(err))
        except Exception as err:
            self.root.after(0, self._handle_fetch_error, f"An unexpected error occurred: {str(err)}")

    def _handle_fetch_success(self, data: dict):
        """Update GUI widgets with received weather data."""
        self.search_btn.config(state="normal", text="Search")
        self.status_label.config(text="Weather data updated.")

        self._last_city = data["city"]

        # Unit symbol
        unit_symbol = "°C" if data["units"] == "metric" else "°F"
        wind_unit = "m/s" if data["units"] == "metric" else "mph"

        # Hide placeholder and show weather details
        self.placeholder_label.pack_forget()
        self.details_container.pack(fill="both", expand=True)

        # Populate labels
        country_suffix = f", {data['country']}" if data["country"] else ""
        self.city_label.config(text=f"{data['city']}{country_suffix}")
        self.condition_emoji.config(text=data["emoji"])
        self.temp_label.config(text=f"{data['temperature']} {unit_symbol}")
        self.desc_label.config(text=data["description"])
        self.feels_like_label.config(text=f"Feels like {data['feels_like']} {unit_symbol}")

        # Populate metric tiles
        self.tile_humidity_val.config(text=f"{data['humidity']}%")
        self.tile_wind_val.config(text=f"{data['wind_speed']} {wind_unit}")
        self.tile_pressure_val.config(text=f"{data['pressure']} hPa")
        self.tile_condition_val.config(text=data["condition"])

        # Timestamp
        now_str = datetime.now().strftime("%I:%M %p")
        self.time_label.config(text=f"Updated: {now_str}")

    def _handle_fetch_error(self, error_message: str):
        """Handle error state and show helpful dialog."""
        self.search_btn.config(state="normal", text="Search")
        self.status_label.config(text="Error fetching weather.")

        # Show user-friendly error popup
        messagebox.showerror("Weather App Error", error_message, parent=self.root)


def main():
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
