# src/extract/weather.py
import logging
from datetime import datetime, timedelta
from typing import Any

from src.extract.base import BaseExtractor
from src import config

logger = logging.getLogger(__name__)

class WeatherExtractor(BaseExtractor):
    """
    Extracts historical hourly weather data from the Open-Meteo archive API.
    Inherits HTTP handling, retries, and session management from BaseExtractor.
    """

    def __init__(self):
        """
        Initialise with Open-Meteo base URL.
        No API key required for Open-Meteo.
        """
        super().__init__(config.OPEN_METEO_BASE_URL)
    
    def _build_date_range(self) -> tuple[str, str]:
        """
        Calculate start and end dates for the query window
        based on LOOKBACK_DAYS in config.

        Returns:
            Tuple of (start_date, end_date) as strings in YYYY-MM-DD format
        """

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days = config.LOOKBACK_DAYS)).strftime("%Y-%m-%d")
        return start_date, end_date
    
    def _build_params(self, lat: float, lon: float,start_date: str, end_date: str) -> dict[str, Any]:
        """
        Build the query parameter dictionary for the Open-Meteo API request.
        Refer to Open-Meteo archive docs for required parameter names.

        Args:
            lat:        Latitude of the location
            lon:        Longitude of the location
            start_date: Start date of the query window (YYYY-MM-DD)
            end_date:   End date of the query window (YYYY-MM-DD)

        Returns:
            Dictionary of query parameters ready to pass to _get()
        """
        
        params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": start_date,
                "end_date": end_date,
                "hourly": config.WEATHER_VARIABLES
        }
        return params

    def fetch(self, city: str) -> dict[str, Any]:
        """
        Fetch historical weather data for a single city.
        Looks up coordinates from config.CITIES.

        Adds 'city' and 'extracted_at' keys to the response 
        before returning, so downstream code knows the source
        and when the data was pulled.

        Args: 
            city: City name - must match a key in config.CITIES

        Returns:
            Raw API response as a dict, enriched with metadata keys

        Raises:
            KeyError: If city is not found in config.CITIES
        """
        try:
            lat=config.CITIES[city]["lat"]
            lon=config.CITIES[city]["lon"]
            response = self._get("", self._build_params(lat, lon, *self._build_date_range()))
            response["city"] = city
            response["extracted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
           
            return response
        except KeyError:
            raise KeyError(f"City '{city}' not found in config.CITIES")

    def fetch_all(self) -> list[dict[str, Any]]:
        """
        Fetch weather data for all cities defined in congig.CITIES.
        Logs progress for each city.

        Returns:
            List of enriched response dicts, one per city
        """
        results = []

        for city in config.CITIES:
            logger.info(f"Fetching weather data for {city}")
            results.append(self.fetch(city))
        return results