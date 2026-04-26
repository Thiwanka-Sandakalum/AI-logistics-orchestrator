"""Realistic multi-factor rate engine based on Loomis pricing structure."""

import logging
from functools import cache
from typing import Dict, Optional

from src.tools.box_definitions import (
    BOX_CATALOG,
    BoxSize,
    billable_weight,
    calculate_dimensional_weight,
)
from src.tools.distance_calculator import get_distance_calculator

logger = logging.getLogger(__name__)


class ServiceOption:
    """A shipping service offering."""

    def __init__(
        self,
        name: str,
        service_type: str,
        base_rate: float,
        delivery_days: int,
    ):
        self.name = name
        self.service_type = service_type
        self.base_rate = base_rate
        self.delivery_days = delivery_days


# Loomis-aligned service options
SERVICES = {
    "ground": ServiceOption(
        name="Loomis Ground",
        service_type="ground",
        base_rate=8.50,
        delivery_days=5,
    ),
    "priority": ServiceOption(
        name="Loomis Priority",
        service_type="priority",
        base_rate=24.00,
        delivery_days=2,
    ),
    "express": ServiceOption(
        name="Loomis 2Day",
        service_type="express",
        base_rate=16.50,
        delivery_days=2,
    ),
    "overnight": ServiceOption(
        name="Loomis Express",
        service_type="overnight",
        base_rate=45.00,
        delivery_days=1,
    ),
}


class RateEngine:
    """
    Multi-factor rate calculation engine.
    
    Factors:
    1. Base service rate
    2. Weight surcharge
    3. Zone/distance surcharge
    4. Dimensional weight penalty
    5. Fuel surcharge
    6. Residential delivery surcharge
    7. Box type surcharge
    8. Oversize surcharge
    """

    def __init__(self):
        self.distance_calc = get_distance_calculator()
        self.fuel_surcharge_pct = 0.08  # 8% fuel surcharge (realistic)
        self.residential_surcharge = 5.00  # $5 residential delivery
        self.oversize_surcharge = 8.50  # $8.50 for oversize

    def calculate_rate(
        self,
        origin_zip: str,
        destination_zip: str,
        weight_lbs: float,
        service_type: str = "ground",
        box_size: Optional[BoxSize] = None,
        actual_dimensions: Optional[tuple] = None,
        is_residential: bool = False,
    ) -> Dict[str, any]:
        """
        Calculate shipping rate for a package.

        Args:
            origin_zip: Origin ZIP code
            destination_zip: Destination ZIP code
            weight_lbs: Actual package weight
            service_type: ground, express, priority, overnight
            box_size: BoxSize enum or None for custom
            actual_dimensions: (length, width, height) in inches or None
            is_residential: True if residential delivery (adds surcharge)

        Returns:
            Dictionary with:
            - service_name: Service name
            - base_rate: Service base rate
            - weight_charge: Weight-based surcharge
            - zone_surcharge: Distance-based surcharge
            - dimensional_penalty: Oversize/dim-weight penalty
            - fuel_surcharge: Fuel surcharge
            - residential_surcharge: Residential delivery fee
            - box_surcharge: Box type surcharge
            - total_cost: Final cost
            - delivery_days: Expected delivery days
            - details: Breakdown of all factors
        """
        service = SERVICES.get(service_type)
        if not service:
            raise ValueError(
                f"Unknown service type: {service_type}. "
                f"Valid options: {list(SERVICES.keys())}"
            )

        # Calculate distance/zone
        distance_info = self.distance_calc.calculate_distance(
            origin_zip, destination_zip
        )
        zone = distance_info["zone"]

        # Calculate dimensional weight
        dim_weight = 0.0
        dimensional_penalty = 0.0
        if actual_dimensions:
            length, width, height = actual_dimensions
            dim_weight = calculate_dimensional_weight(length, width, height)
            billable = billable_weight(weight_lbs, dim_weight)

            # If dimensional weight is significantly higher, penalize
            if billable > weight_lbs:
                dimensional_penalty = (billable - weight_lbs) * 0.50  # $0.50 per lb
        else:
            billable = weight_lbs

        # Weight surcharge (per lb over 1 lb)
        weight_charge = 0.0
        if billable > 1.0:
            weight_charge = (billable - 1.0) * 0.25  # $0.25 per additional lb

        # Zone surcharge (roughly $0 for zone 1 to $15 for zone 8)
        zone_surcharge = (zone - 1) * 2.0  # $2 per zone level

        # Box type surcharge
        box_surcharge = 0.0
        if box_size and box_size in BOX_CATALOG:
            box_surcharge = BOX_CATALOG[box_size].base_surcharge

        # Oversize surcharge
        oversize_surcharge = 0.0
        if actual_dimensions:
            length, width, height = actual_dimensions
            # Check if any dimension is excessive
            if (
                length > 30
                or width > 20
                or height > 15
                or (length + 2 * (width + height)) > 130
            ):
                oversize_surcharge = self.oversize_surcharge

        # Subtotal before fuel
        subtotal = (
            service.base_rate
            + weight_charge
            + zone_surcharge
            + dimensional_penalty
            + box_surcharge
            + oversize_surcharge
        )

        # Fuel surcharge (applied to subtotal)
        fuel_surcharge = round(subtotal * self.fuel_surcharge_pct, 2)

        # Residential surcharge
        residential_surcharge = self.residential_surcharge if is_residential else 0.0

        # Total cost
        total_cost = round(
            subtotal + fuel_surcharge + residential_surcharge, 2
        )

        return {
            "service_name": service.name,
            "service_type": service_type,
            "base_rate": round(service.base_rate, 2),
            "weight_charge": round(weight_charge, 2),
            "zone": zone,
            "zone_name": distance_info["zone_name"],
            "zone_surcharge": round(zone_surcharge, 2),
            "dimensional_penalty": round(dimensional_penalty, 2),
            "box_surcharge": round(box_surcharge, 2),
            "oversize_surcharge": round(oversize_surcharge, 2),
            "fuel_surcharge": fuel_surcharge,
            "residential_surcharge": round(residential_surcharge, 2),
            "total_cost": total_cost,
            "delivery_days": service.delivery_days,
            "estimated_distance_miles": distance_info["distance_miles"],
            "billable_weight": round(billable, 2),
            "actual_weight": round(weight_lbs, 2),
            "dimensional_weight": round(dim_weight, 2),
        }

    def compare_services(
        self,
        origin_zip: str,
        destination_zip: str,
        weight_lbs: float,
        actual_dimensions: Optional[tuple] = None,
        is_residential: bool = False,
    ) -> list:
        """
        Get rate comparison for all service types.

        Returns:
            List of rate dictionaries, sorted by cost
        """
        rates = []
        for service_type in SERVICES.keys():
            try:
                rate = self.calculate_rate(
                    origin_zip=origin_zip,
                    destination_zip=destination_zip,
                    weight_lbs=weight_lbs,
                    service_type=service_type,
                    actual_dimensions=actual_dimensions,
                    is_residential=is_residential,
                )
                rates.append(rate)
            except Exception as e:
                logger.warning("Failed to calculate rate for %s: %s", service_type, e)

        # Sort by cost
        return sorted(rates, key=lambda r: r["total_cost"])


@cache
def get_rate_engine() -> RateEngine:
    """Get singleton rate engine."""
    return RateEngine()
