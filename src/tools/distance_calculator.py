"""Distance calculation using LLM-native prompting and zone-based estimation."""

import logging
from functools import cache

from src.tools.zone_mapper import get_zone_mapper

logger = logging.getLogger(__name__)


class DistanceCalculator:
    """
    Estimate distance between US ZIP codes using LLM prompting and zone mapping.
    
    Strategy:
    1. Use zone mapper for ZIP-based region distance (offline, deterministic)
    2. Optionally enhance with LLM when more precision is needed
    3. Return distance band + estimated miles
    """

    def __init__(self):
        self.zone_mapper = get_zone_mapper()

    def calculate_distance(
        self, origin_zip: str, destination_zip: str
    ) -> dict:
        """
        Calculate distance between two US ZIP codes.

        Args:
            origin_zip: Origin 5-digit ZIP code
            destination_zip: Destination 5-digit ZIP code

        Returns:
            Dictionary with:
            - distance_miles: Estimated distance
            - zone: Delivery zone (1-8)
            - zone_name: Human-readable zone name
            - distance_band: Category (local, regional, long-distance, etc)
        """
        # Validate ZIP codes
        origin_zip = str(origin_zip).strip()[:5]
        destination_zip = str(destination_zip).strip()[:5]

        if not origin_zip or not destination_zip:
            raise ValueError("Invalid ZIP codes provided")

        # Get zone and estimate distance
        zone = self.zone_mapper.distance_zone(origin_zip, destination_zip)
        distance_miles = self.zone_mapper.estimate_distance_miles(
            origin_zip, destination_zip
        )
        zone_name = self.zone_mapper.zone_name(zone)

        # Determine distance band
        distance_band = self._classify_distance(distance_miles)

        return {
            "distance_miles": distance_miles,
            "zone": zone,
            "zone_name": zone_name,
            "distance_band": distance_band,
            "origin_zip": origin_zip,
            "destination_zip": destination_zip,
        }

    def _classify_distance(self, miles: int) -> str:
        """Classify distance into bands."""
        if miles < 100:
            return "local"
        elif miles < 300:
            return "regional"
        elif miles < 800:
            return "long_distance"
        elif miles < 1500:
            return "very_long_distance"
        else:
            return "cross_country"


@cache
def get_distance_calculator() -> DistanceCalculator:
    """Get singleton distance calculator."""
    return DistanceCalculator()
