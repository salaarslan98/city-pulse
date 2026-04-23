# src/extract/base.py
import logging
import time
import requests
from typing import Any

logger = logging.getLogger(__name__)

class BaseExtractor():
    """
    Shared HTTP client for all data source extractors.
    Handles session management, authentication headers,
    retries with exponential backoff, and rate limiting.
    """

    def __init__(
        self, 
        base_url: str, 
        api_key: str = "",
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        rate_limit_pause: float = 1.0
        ):

        """ 
        Initialise the extractor with a base URL and optional auth.

        Args:
        base_url:           Root URL for the API (no trailing slash)
        api_key:            Optional API key for authentication - added to headers if provided
        max_retries:        Maximum number of retries after a failed request
        backoff_factor:     Multiplier for wait time between retries e.g. factor = 2 -> waits 1s, 2s, 4s, 8s, 16s, etc... between attempts
        rate_limit_pause:   Seconds to wait between successful requests to avoid overwhelming the API
        """

        self.base_url = base_url
        self.api_key = api_key
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.rate_limit_pause = rate_limit_pause
        self.session = self._build_session(api_key)

    def _build_session(self, api_key: str) -> requests.Session:
        """
        Create and configure a requests.Session with appropriate headers.
        If an api_key is provided, add it as an Authorization header.

        Args:
            api_key: API key string, or empty string if not required

        Returns:
            A configured requests.Session object
        """
        session = requests.Session()
        if api_key:
            session.headers.update({"Authorization": f"Bearer {api_key}"})
        return session

    def _get(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """ 
        Make a GET request to the API with retry and backoff logic.
        Waits rate_limit_pause seconds after each successful request.

        On failure, retries up to max_retries times.
        wait time between retries = backoff_factor ^ attempt number (backoff_factor**attempt_number)
        
        Logs each retry attempt and the reason for failure. 
        Raises an exception if all retries are exhausted.

        Args:
            endpoint: Path to append to base_url (e.g. "/locations")
            params:   Query parameters to include in the request

        Returns:
            Parsed JSON response as a dictionary

        Raises:
            requests.HTTPError:   If the server returns a 4xx or 5xx response
            requests.exceptions.RequestException: If the request fails entirely
        """
        url = f"{self.base_url}{endpoint}"
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(url, params = params)
                response.raise_for_status()
                time.sleep(self.rate_limit_pause)
                return response.json()
            except (requests.HTTPError, requests.exceptions.RequestException) as e:
                if attempt < self.max_retries:
                    wait_time = self.backoff_factor ** attempt
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {self.max_retries} retries exhausted. Reason: {e}")
                    raise




        


