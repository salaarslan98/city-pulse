# src/extract/air_quality.py
import logging
from datetime import datetime, timedelta
from typing import Any

from src.extract.base import BaseExtractor
from src import config

logger = logging.getLogger(__name__)

class AirQualityExtractor(BaseExtractor):
    """
    Extracts air quality measurements from the OPENAQ v3 API.
    Inherits HTTP handling, retries, and session management from BaseExtractor.
    """
    
    def __init__(self):
        """
        Initialise with OpenAQ base URL and API key from config.
        Raises a ValueError if the API key is not set.
        """
        if not config.OPENAQ_API_KEY:
            raise ValueError("OpenAQ API key not set in config.py, Air quality extraction will fail")
        super().__init__(config.OPENAQ_BASE_URL, config.OPENAQ_API_KEY)
    
    def _build_date_range(self) -> tuple[str, str]:
        """
        Calculate start and end dates for the query window
        based on LOOKBACK_DAYS in config.
        OpenAQ expects ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ


        Returns:
            Tuple of (date_from, date_to) as ISO 8601 strings
        """

        date_to = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        date_from = (datetime.now() - timedelta(days = config.LOOKBACK_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
        return date_from, date_to

    def _get_location_ids(self, lat: float, lon: float, radius: int = 25000) -> list[int]:
        """
        Find OpenAQ monitoring station IDs near a given coordinate.
        Uses the /locations endpoint with a radius search.

        Args:
            lat:    Latitude of the city centre
            lon:    Longitude of the city centre
            radius: Search radius in metres (default 25km)

        Returns:
            List of location IDs found within the radius.
            Returns an empty list if none are found.
        """
        parameters = {
            "coordinates": f"{lat},{lon}", 
            "radius":radius
        }
        location_ids = []
        response = self._get("/locations", parameters)
        
        if not response["results"]:
            return location_ids
        else:
            for location in response["results"]:
                location_ids.append(location["id"])
            return location_ids
    
    def _build_params(self, location_id: int, date_from: str, date_to:str) -> dict[str, Any]:
        """
        Build query parameters for the /measurements endpoint.

        Args:
            location_id: OpenAQ location ID to query
            date_from:   Start date of the query window (ISO 8601)
            date_to:     End date of the query window (ISO 8601)

        Returns:
            Dictionary of query parameters
        """
        params = {
            "locations_id": location_id,
            "date_from": date_from,
            "date_to": date_to
        }
    

        return params

    def fetch(self, city: str) -> dict[str, Any]:
        """
        Fetch air quality measurements for a single city.

        Finds all monitoring stations within 25km of the city centre,
        fetches measurements from each, and combines the results.

        Adds 'city' and 'extracted_at' keys before returning.

        Args:
            city: City name — must match a key in config.CITIES

        Returns:
            Dict with keys: 'city', 'extracted_at', 'results'
            where 'results' is a list of measurement records

        Raises:
            KeyError:   If city is not found in config.CITIES
            ValueError: If no monitoring stations are found near the city
        """
        try:
            results = []

            lat=config.CITIES[city]["lat"]
            lon=config.CITIES[city]["lon"]
            location_ids = self._get_location_ids(lat, lon)
            if not location_ids:
                raise ValueError(f"No monitoring stations found near {city}")

            else:
                for location in location_ids:
                    response = self._get("/measurements", self._build_params(location, *self._build_date_range()))
                    results.extend(response["results"])  

           
            return {
                    "city": city,
                    "extracted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "results": results
                }
        except KeyError:
            raise KeyError(f"City '{city}' not found in config.CITIES")

    def fetch_all(self) -> list[dict[str, Any]]:
        """
        Fetch air quality data for all cities in config.CITIES.
        Logs progress for each city.

        Returns:
            List of enriched response dicts, one per city
        """
        results = []

        for city in config.CITIES:
            logger.info(f"Fetching weather data for {city}")
            results.append(self.fetch(city))
        return results


        
        