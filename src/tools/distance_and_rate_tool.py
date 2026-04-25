"""Tool for calculating realistic shipping distance and rates."""

import logging
from typing import Optional

from langchain.tools import tool
from pydantic import ValidationError
from src.tools.distance_calculator import get_distance_calculator
from src.tools.rate_engine import get_rate_engine
from src.tools.schemas import DistanceAndRateRequest

logger = logging.getLogger(__name__)


@tool(args_schema=DistanceAndRateRequest)
def calculate_distance_and_rates(
    origin_zip: str,
    destination_zip: str,
    weight_lbs: float,
    length_inches: Optional[float] = None,
    width_inches: Optional[float] = None,
    height_inches: Optional[float] = None,
    is_residential: bool = False,
) -> dict:
    """
    Calculate realistic shipping distance, zones, and multi-service rates.

    This tool estimates distance using US ZIP code zones and calculates
    realistic FedEx-aligned rates based on multiple factors: weight, distance,
    dimensional weight, service type, and surcharges (fuel, residential, oversize).

    Args:
        origin_zip: 5-digit origin ZIP code (e.g., "90210")
        destination_zip: 5-digit destination ZIP code (e.g., "10001")
        weight_lbs: Actual package weight in pounds (must be > 0)
        length_inches: Package length in inches (optional, for dimensional weight)
        width_inches: Package width in inches (optional, for dimensional weight)
        height_inches: Package height in inches (optional, for dimensional weight)
        is_residential: True if delivery to residential address (adds $5 surcharge)

    Returns:
        A dictionary containing:
        - distance_info: Estimated distance, zone, and zone name
        - service_rates: List of available services with costs
            - service_name: e.g., "FedEx Ground"
            - service_type: ground, express, priority, overnight
            - base_rate: Service base cost
            - zone_surcharge: Distance-based surcharge
            - weight_charge: Weight-based surcharge
            - total_cost: Final calculated cost
            - delivery_days: Expected delivery time
        - lowest_cost: Cheapest option
        - fastest: Fastest option

    Example:
        >>> calculate_distance_and_rates(
        ...     origin_zip="90210",
        ...     destination_zip="10001",
        ...     weight_lbs=5.5,
        ...     length_inches=12,
        ...     width_inches=9,
        ...     height_inches=6,
        ...     is_residential=True
        ... )
        {
            "distance_info": {
                "distance_miles": 2500,
                "zone": 8,
                "zone_name": "Maximum Distance"
            },
            "service_rates": [
                {
                    "service_name": "FedEx Ground",
                    "total_cost": 42.75,
                    "delivery_days": 5,
                    ...
                }
            ],
            "lowest_cost": {...},
            "fastest": {...}
        }
    """
    try:
        # Validate and normalize inputs.
        request = DistanceAndRateRequest(
            origin_zip=origin_zip,
            destination_zip=destination_zip,
            weight_lbs=weight_lbs,
            length_inches=length_inches,
            width_inches=width_inches,
            height_inches=height_inches,
            is_residential=is_residential,
        )

        # Calculate distance
        distance_calc = get_distance_calculator()
        distance_info = distance_calc.calculate_distance(
            request.origin_zip,
            request.destination_zip,
        )

        # Prepare dimensions tuple if provided
        dimensions = None
        if (
            request.length_inches is not None
            and request.width_inches is not None
            and request.height_inches is not None
        ):
            dimensions = (
                request.length_inches,
                request.width_inches,
                request.height_inches,
            )

        # Calculate rates for all services
        rate_engine = get_rate_engine()
        service_rates = rate_engine.compare_services(
            origin_zip=request.origin_zip,
            destination_zip=request.destination_zip,
            weight_lbs=request.weight_lbs,
            actual_dimensions=dimensions,
            is_residential=request.is_residential,
        )

        if not service_rates:
            raise ValueError("Could not calculate rates for any service")

        # Find lowest cost and fastest options
        lowest_cost = min(service_rates, key=lambda r: r["total_cost"])
        fastest = min(service_rates, key=lambda r: r["delivery_days"])

        # Simplify service rates for response (remove internal details)
        simplified_rates = [
            {
                "service_name": rate["service_name"],
                "service_type": rate["service_type"],
                "total_cost": rate["total_cost"],
                "delivery_days": rate["delivery_days"],
                "estimated_distance_miles": rate["estimated_distance_miles"],
                "zone": rate["zone"],
                "zone_name": rate["zone_name"],
                "billable_weight": rate["billable_weight"],
                "base_rate": rate["base_rate"],
                "fuel_surcharge": rate["fuel_surcharge"],
                "zone_surcharge": rate["zone_surcharge"],
            }
            for rate in service_rates
        ]

        logger.info(
            f"Calculated rates for {origin_zip} -> {destination_zip}, "
            f"weight {request.weight_lbs} lbs: lowest cost ${lowest_cost['total_cost']}"
        )

        return {
            "distance_info": {
                "origin_zip": distance_info["origin_zip"],
                "destination_zip": distance_info["destination_zip"],
                "distance_miles": distance_info["distance_miles"],
                "distance_band": distance_info["distance_band"],
                "zone": distance_info["zone"],
                "zone_name": distance_info["zone_name"],
            },
            "service_rates": simplified_rates,
            "lowest_cost_option": {
                "service_name": lowest_cost["service_name"],
                "service_type": lowest_cost["service_type"],
                "total_cost": lowest_cost["total_cost"],
                "delivery_days": lowest_cost["delivery_days"],
            },
            "fastest_option": {
                "service_name": fastest["service_name"],
                "service_type": fastest["service_type"],
                "total_cost": fastest["total_cost"],
                "delivery_days": fastest["delivery_days"],
            },
            "weight_info": {
                "actual_weight_lbs": request.weight_lbs,
                "billable_weight_lbs": lowest_cost.get("billable_weight", request.weight_lbs),
                "dimensional_weight_lbs": lowest_cost.get("dimensional_weight", 0),
            },
        }

    except ValidationError as e:
        logger.warning("Validation error in calculate_distance_and_rates: %s", e)
        return {
            "error": True,
            "message": f"Invalid input: {str(e)}",
        }
    except ValueError as e:
        logger.warning(f"Validation error in calculate_distance_and_rates: {str(e)}")
        return {
            "error": True,
            "message": f"Invalid input: {str(e)}",
        }
    except Exception as e:
        logger.error(f"Error calculating distance and rates: {str(e)}")
        return {
            "error": True,
            "message": f"Could not calculate rates: {str(e)}",
        }
