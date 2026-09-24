"""
weather_api.py
Handles all interactions with the OpenWeatherMap REST API:
- Loads the API key securely from .env
- Validates inputs and configuration
- Sends HTTP GET requests using the requests library
- Parses JSON responses into structured weather data
- Implements comprehensive error handling for network, authorization, and invalid input issues
"""

import os
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenWeatherMap API Endpoint
BASE_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

# Mapping of OpenWeatherMap weather conditions to clean emoji icons
WEATHER_EMOJIS = {
    "Clear": "☀️",
    "Clouds": "☁️",
    "Rain": "🌧️",
    "Drizzle": "🌦️",
    "Thunderstorm": "⛈️",
    "Snow": "❄️",
    "Mist": "🌫️",
    "Smoke": "🌫️",
    "Haze": "🌫️",
    "Dust": "💨",
    "Fog": "🌫️",
    "Sand": "💨",
    "Ash": "🌋",
    "Squall": "💨",
    "Tornado": "🌪️",
}


class WeatherAPIError(Exception):
    """Custom exception raised for predictable Weather API errors."""
    pass


def get_api_key(reload_env: bool = True) -> str:
    """
    Retrieve the OpenWeatherMap API key from environment variables.
    
    Args:
        reload_env (bool): Whether to re-read the .env file from disk (default: True).

    Returns:
        str: Valid API key string.
        
    Raises:
        WeatherAPIError: If key is not found or is still the default placeholder.
    """
    # Reload environment in case .env was edited while app is running
    if reload_env:
        load_dotenv(override=True)
    api_key = os.getenv("OPENWEATHERMAP_API_KEY", "").strip()

    if not api_key:
        raise WeatherAPIError(
            "API key not found!\n"
            "Please create or update the '.env' file with your OpenWeatherMap key:\n"
            "OPENWEATHERMAP_API_KEY=your_actual_key"
        )
    
    if api_key == "your_api_key_here":
        raise WeatherAPIError(
            "Default placeholder API key detected!\n"
            "Please open the '.env' file and replace 'your_api_key_here' with your real "
            "free API key from https://openweathermap.org/api"
        )
        
    return api_key


def fetch_weather_data(city_name: str, units: str = "metric", custom_api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch and parse current weather information for a specified city from OpenWeatherMap.

    Args:
        city_name (str): Name of the city (e.g., 'London', 'Tokyo', 'New York').
        units (str): Temperature unit system ('metric' for Celsius, 'imperial' for Fahrenheit).
        custom_api_key (Optional[str]): Explicit API key if overriding .env.

    Returns:
        Dict[str, Any]: Parsed weather information containing:
            - city (str): City name
            - country (str): Country code
            - temperature (float): Current temperature
            - feels_like (float): Feels-like temperature
            - condition (str): Short weather condition (e.g. 'Clouds', 'Rain')
            - description (str): Detailed weather description (e.g. 'scattered clouds')
            - humidity (int): Humidity percentage
            - wind_speed (float): Wind speed (m/s for metric, mph for imperial)
            - pressure (int): Atmospheric pressure in hPa
            - emoji (str): Unicode weather emoji
            - units (str): The unit system used ('metric' or 'imperial')

    Raises:
        WeatherAPIError: For invalid inputs, invalid keys, cities not found, or network issues.
    """
    # 1. Input validation
    clean_city = city_name.strip() if city_name else ""
    if not clean_city:
        raise WeatherAPIError("Please enter a city name to search.")

    # 2. API Key resolution
    api_key = custom_api_key.strip() if custom_api_key else get_api_key()

    # 3. Prepare parameters for HTTP GET request
    params = {
        "q": clean_city,
        "appid": api_key,
        "units": units
    }

    # 4. Make HTTP GET request to OpenWeatherMap REST API
    try:
        response = requests.get(BASE_WEATHER_URL, params=params, timeout=10)
    except requests.exceptions.ConnectionError:
        raise WeatherAPIError(
            "Network Connection Error:\n"
            "Unable to reach OpenWeatherMap servers. Please check your internet connection."
        )
    except requests.exceptions.Timeout:
        raise WeatherAPIError(
            "Connection Timeout:\n"
            "The weather server took too long to respond. Please try again in a moment."
        )
    except requests.exceptions.RequestException as e:
        raise WeatherAPIError(f"HTTP Request failed: {str(e)}")

    # 5. Parse JSON response and handle HTTP status codes
    try:
        data = response.json()
    except Exception:
        raise WeatherAPIError("Failed to parse response from OpenWeatherMap. Invalid JSON received.")

    status_code = response.status_code

    if status_code == 200:
        # Successful response: Parse required weather metrics
        try:
            weather_element = data["weather"][0]
            condition = weather_element.get("main", "Unknown")
            description = weather_element.get("description", "Unknown").capitalize()
            emoji = WEATHER_EMOJIS.get(condition, "🌤️")

            parsed_data = {
                "city": data.get("name", clean_city),
                "country": data.get("sys", {}).get("country", ""),
                "temperature": round(data["main"]["temp"], 1),
                "feels_like": round(data["main"]["feels_like"], 1),
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "wind_speed": round(data.get("wind", {}).get("speed", 0.0), 1),
                "condition": condition,
                "description": description,
                "emoji": emoji,
                "units": units,
            }
            return parsed_data
        except (KeyError, IndexError, TypeError) as e:
            raise WeatherAPIError(f"Incomplete weather data received from API: missing {str(e)}")

    elif status_code == 404:
        raise WeatherAPIError(
            f"City '{clean_city}' not found!\n"
            "Please check the spelling or try adding a country code (e.g., 'Paris, FR')."
        )
    elif status_code == 401:
        raise WeatherAPIError(
            "Unauthorized (Invalid API Key)!\n"
            "Your OpenWeatherMap API key is invalid or not yet activated.\n"
            "(Note: New OpenWeatherMap keys can take 10-30 minutes to activate after creation)."
        )
    elif status_code == 429:
        raise WeatherAPIError(
            "API Rate Limit Exceeded!\n"
            "You have made too many requests in a short period. Please wait and try again."
        )
    else:
        # Other API errors (500, etc.)
        api_message = data.get("message", "Unknown error")
        raise WeatherAPIError(f"OpenWeatherMap Error (Code {status_code}): {api_message}")
