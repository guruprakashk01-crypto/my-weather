Weather Data Fetcher

A Python application that fetches and displays real-time weather data using the OpenWeatherMap API.

Features
Fetches real-time weather data via REST API calls to OpenWeatherMap
Parses JSON responses to extract relevant weather information
Displays weather data in a clean, readable format
Includes error handling for reliable data retrieval (handles network issues, invalid city names, API errors, etc.)
Tech Stack
Language: Python
API: OpenWeatherMap API (REST)
Data Format: JSON
Prerequisites
Python 3.7+
An OpenWeatherMap API key (get one free here)
requests library
Installation
Clone the repository:
bash
   git clone https://github.com/your-username/your-repo-name.git
   cd your-repo-name
Install dependencies:
bash
   pip install requests
Set up your API key:
Create a .env file or set an environment variable:
bash
     export OPENWEATHER_API_KEY="your_api_key_here"
Usage

Run the application:

bash
python weather_app.py

Enter a city name when prompted, and the app will display the current weather conditions, including temperature, humidity, and general weather description.

Example Output
Enter city name: London
--------------------------------
City: London
Temperature: 15°C
Weather: Cloudy
Humidity: 72%
--------------------------------
Error Handling

The application gracefully handles:

Invalid or misspelled city names
Network connectivity issues
API request failures / rate limits
Malformed or missing JSON data
Project Structure
.
├── weather_app.py      # Main application script
├── README.md            # Project documentation
└── requirements.txt      # Python dependencies
License

This project is open source and available under the MIT License.
Your Name
Guruprakash K
