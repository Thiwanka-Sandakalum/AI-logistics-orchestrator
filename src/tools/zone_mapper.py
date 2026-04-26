"""US zone mapping for Loomis-like distance-based pricing."""

from functools import cache
from typing import Tuple


class ZoneMapper:
    """Map US ZIP codes to delivery zones based on distance."""

    # Loomis uses 8 zones (1-8), where 1 is same/adjacent and 8 is cross-country max
    # Simplified: Zone is based on ZIP prefix distance
    # Format: (origin_zip_prefix, destination_zip_prefix) -> zone

    def __init__(self):
        """Initialize zone lookup tables."""
        # ZIP prefixes by region (first digit or first 3 digits)
        # 0: Northeast (NY, PA, NJ, etc)
        # 1: New England
        # 2: Atlantic (DC, MD, VA, etc)
        # 3: Southeast
        # 4: Midwest (KY, TN, MS, AL)
        # 5: Central (OK, TX, AR, LA)
        # 6: Southwest (NM, AZ, NV)
        # 7: Mountain (CO, WY, MT, UT, ID)
        # 8: Pacific (CA, OR, WA, HI)
        # 9: Alaska, Military, Other

    def zip_to_region(self, zip_code: str) -> int:
        """
        Map a ZIP code to its region (0-9).
        Uses first digit as primary region indicator.

        Args:
            zip_code: 5-digit ZIP code (e.g., "90210")

        Returns:
            Region ID (0-9)
        """
        if not zip_code or len(zip_code) < 1:
            return 5  # Default to central

        try:
            first_digit = int(zip_code[0])
            return first_digit
        except ValueError:
            return 5

    def distance_zone(self, origin_zip: str, destination_zip: str) -> int:
        """
        Calculate Loomis-like zone (1-8) based on ZIP code regions.

        Zone 1: Same region (local)
        Zone 2: Adjacent region
        Zone 3-5: Increasing distance
        Zone 6-8: Cross-country (longest distance)

        Args:
            origin_zip: Origin 5-digit ZIP
            destination_zip: Destination 5-digit ZIP

        Returns:
            Zone (1-8)
        """
        origin_region = self.zip_to_region(origin_zip)
        dest_region = self.zip_to_region(destination_zip)

        region_diff = abs(origin_region - dest_region)

        # Zone calculation based on region distance
        if region_diff == 0:
            zone = 1
        elif region_diff == 1:
            zone = 2
        elif region_diff == 2:
            zone = 3
        elif region_diff == 3:
            zone = 4
        elif region_diff == 4:
            zone = 5
        elif region_diff == 5:
            zone = 6
        elif region_diff == 6:
            zone = 7
        else:
            zone = 8

        # Cap at zone 8
        return min(zone, 8)

    def estimate_distance_miles(
        self, origin_zip: str, destination_zip: str
    ) -> int:
        """
        Rough estimate of distance in miles based on zone.
        Used for display/reference only.

        Args:
            origin_zip: Origin ZIP
            destination_zip: Destination ZIP

        Returns:
            Estimated distance in miles
        """
        zone = self.distance_zone(origin_zip, destination_zip)

        # Zone -> typical distance mapping (rough)
        zone_distance_map = {
            1: 50,     # Local
            2: 200,    # Regional
            3: 400,
            4: 700,
            5: 1000,
            6: 1400,
            7: 1800,
            8: 2500,   # Cross-country
        }
        return zone_distance_map.get(zone, 2500)

    def zone_name(self, zone: int) -> str:
        """Get human-readable zone name."""
        names = {
            1: "Local",
            2: "Regional",
            3: "Adjacent Region",
            4: "Distant",
            5: "Very Distant",
            6: "Long Distance",
            7: "Far Cross-Country",
            8: "Maximum Distance",
        }
        return names.get(zone, "Unknown")


@cache
def get_zone_mapper() -> ZoneMapper:
    """Get singleton zone mapper."""
    return ZoneMapper()
