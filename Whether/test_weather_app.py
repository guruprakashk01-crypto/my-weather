"""
test_weather_app.py
Automated test suite verifying the OpenWeatherMap API integration,
JSON parsing, and error handling edge cases using unittest and mock responses.
"""

import unittest
from unittest.mock import patch, MagicMock
import requests
import weather_api
from weather_api import fetch_weather_data, WeatherAPIError, get_api_key

# Mock OpenWeatherMap JSON response for London
MOCK_WEATHER_JSON = {
    "coord": {"lon": -0.1257, "lat": 51.5085},
    "weather": [
        {
            "id": 803,
            "main": "Clouds",
            "description": "broken clouds",
            "icon": "04d"
        }
    ],
    "base": "stations",
    "main": {
        "temp": 15.6,
        "feels_like": 14.8,
        "temp_min": 13.9,
        "temp_max": 17.2,
        "pressure": 1018,
        "humidity": 72
    },
    "visibility": 10000,
    "wind": {
        "speed": 4.1,
        "deg": 230
    },
    "clouds": {"all": 75},
    "dt": 1690000000,
    "sys": {
        "type": 2,
        "id": 2075535,
        "country": "GB",
        "sunrise": 1689999000,
        "sunset": 1690050000
    },
    "timezone": 3600,
    "id": 2643743,
    "name": "London",
    "cod": 200
}


class TestWeatherAPI(unittest.TestCase):

    def test_empty_city_validation(self):
        """Ensure empty or whitespace-only city names raise WeatherAPIError."""
        with self.assertRaises(WeatherAPIError) as ctx:
            fetch_weather_data("", custom_api_key="dummy_key")
        self.assertIn("Please enter a city name", str(ctx.exception))

        with self.assertRaises(WeatherAPIError) as ctx:
            fetch_weather_data("   ", custom_api_key="dummy_key")
        self.assertIn("Please enter a city name", str(ctx.exception))

    def test_placeholder_api_key(self):
        """Ensure placeholder API key is caught with clear error."""
        with patch.dict("os.environ", {"OPENWEATHERMAP_API_KEY": "your_api_key_here"}):
            with self.assertRaises(WeatherAPIError) as ctx:
                get_api_key(reload_env=False)
            self.assertIn("Default placeholder API key detected", str(ctx.exception))

    def test_missing_api_key(self):
        """Ensure missing API key is caught with clear error."""
        with patch.dict("os.environ", {"OPENWEATHERMAP_API_KEY": ""}):
            with self.assertRaises(WeatherAPIError) as ctx:
                get_api_key(reload_env=False)
            self.assertIn("API key not found", str(ctx.exception))

    @patch("requests.get")
    def test_successful_fetch_and_parsing(self, mock_get):
        """Verify successful API response is properly parsed with all required fields."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_WEATHER_JSON
        mock_get.return_value = mock_response

        data = fetch_weather_data("London", units="metric", custom_api_key="dummy_valid_key")

        # Verify all required weather metrics
        self.assertEqual(data["city"], "London")
        self.assertEqual(data["country"], "GB")
        self.assertEqual(data["temperature"], 15.6)
        self.assertEqual(data["feels_like"], 14.8)
        self.assertEqual(data["condition"], "Clouds")
        self.assertEqual(data["description"], "Broken clouds")
        self.assertEqual(data["humidity"], 72)
        self.assertEqual(data["wind_speed"], 4.1)
        self.assertEqual(data["pressure"], 1018)
        self.assertEqual(data["emoji"], "☁️")
        self.assertEqual(data["units"], "metric")

    @patch("requests.get")
    def test_city_not_found_404(self, mock_get):
        """Ensure HTTP 404 returns user-friendly city not found message."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"cod": "404", "message": "city not found"}
        mock_get.return_value = mock_response

        with self.assertRaises(WeatherAPIError) as ctx:
            fetch_weather_data("InvalidCityNameXYZ123", custom_api_key="dummy_key")
        self.assertIn("City 'InvalidCityNameXYZ123' not found", str(ctx.exception))

    @patch("requests.get")
    def test_invalid_api_key_401(self, mock_get):
        """Ensure HTTP 401 raises invalid key guidance."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"cod": 401, "message": "Invalid API key"}
        mock_get.return_value = mock_response

        with self.assertRaises(WeatherAPIError) as ctx:
            fetch_weather_data("Tokyo", custom_api_key="invalid_bad_key")
        self.assertIn("Invalid API Key", str(ctx.exception))

    @patch("requests.get")
    def test_network_connection_error(self, mock_get):
        """Ensure requests.exceptions.ConnectionError is caught gracefully."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        with self.assertRaises(WeatherAPIError) as ctx:
            fetch_weather_data("Paris", custom_api_key="dummy_key")
        self.assertIn("Network Connection Error", str(ctx.exception))

    @patch("requests.get")
    def test_network_timeout_error(self, mock_get):
        """Ensure requests.exceptions.Timeout is caught gracefully."""
        mock_get.side_effect = requests.exceptions.Timeout("Read timed out")

        with self.assertRaises(WeatherAPIError) as ctx:
            fetch_weather_data("Paris", custom_api_key="dummy_key")
        self.assertIn("Connection Timeout", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
