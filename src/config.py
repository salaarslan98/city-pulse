# src/config.py
import os
from pathlib import Path
from dotenv import load_dotenv
import warnings

load_dotenv()

# --- Paths ---
# Root of the project, used to build all other paths relative to it.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Path to the DuckDB file - should land in the data/ directory
DB_PATH: Path = PROJECT_ROOT/ "data" / "city_pulse.duckdb"

# --- API Credentials ---
OPENAQ_API_KEY: str = os.getenv("OPENAQ_API_KEY", "")
if not OPENAQ_API_KEY:
	warnings.warn("OPENAQ_API_KEY is not set. Air quality extraction will fail.")

# --- Cities ---
# Each city needs a name, latitude, and longitude
# Both APIs will use these coordinates
CITIES: dict = {
	"Lahore": {
		"lat": 31.5204,
		"lon": 74.3587,
		},
	"Milan": {
		"lat": 45.4642,
		"lon": 9.1900,
		},
	"London": {
		"lat": 51.5074,
		"lon":  -0.1278,
		}
	}

# --- Date Range ---
# Controls how far back the pipeline pulls data on each run
# Keep this small for development
LOOKBACK_DAYS: int = 7

# --- Weather API ---
# Open-Meteo is free and needs no API key
# These are the variables you want returned = check the Open-Meteo docs
# for the full list of available field names
OPEN_METEO_BASE_URL: str = "https://archive-api.open-meteo.com/v1/archive"
WEATHER_VARIABLES: list[str] = [
	"dew_point_2m",
	"temperature_2m",
	"relative_humidity_2m",
	"apparent_temperature",
	"wind_speed_10m",
	"wind_speed_80m",
	"temperature_80m",
	"temperature_120m",
	"precipitation",
	"cloud_cover",
	"visibility"
]

# --- Air Quality API ---
# OpenAQ is free and needs no API key
OPENAQ_BASE_URL: str = "https://api.openaq.org/v3"
AQ_PARAMETERS: list[str] = [
	"pm25",
	"pm10",
	"o3",
	"no2",
	"so2",
	"co"
]


