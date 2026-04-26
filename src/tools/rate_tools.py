"""Tools for shipping rate inquiries and quotes."""

import logging
from langchain.tools import tool
from pydantic import ValidationError
from src.tools.schemas import (
    RateInquiryRequest,
    RateInquiryResponse,
)
from src.storage.sqlite_db import get_sqlite_store

logger = logging.getLogger(__name__)


@tool(args_schema=RateInquiryRequest)
def get_shipping_quote(
    origin_zip: str,
    destination_zip: str,
    weight_lbs: float,
    service_type: str = "ground",
) -> dict:
    """
    Get shipping rate for a requested service between two locations.

    This tool returns a rate for the selected service_type,
    including carrier and estimated delivery time. Use this to provide
    customers with pricing before they commit to creating a shipment.

    Args:
        origin_zip: 5-digit ZIP code of the origin location
        destination_zip: 5-digit ZIP code of the destination location
        weight_lbs: Package weight in pounds (must be > 0)
        service_type: One of "ground", "express", "priority", or "overnight" (default: "ground")

    Returns:
        A dictionary containing:
        - rates: List of available shipping options with cost and delivery time
        - origin_zip: The origin ZIP code
        - destination_zip: The destination ZIP code
        - weight_lbs: The package weight

    Each rate includes:
        - service_type: ground, express, priority, or overnight
        - cost: Shipping cost in dollars
        - estimated_delivery_days: Number of days to delivery
        - carrier: Carrier name (optional)

    Example:
        >>> get_shipping_quote(
        ...     origin_zip="90210",
        ...     destination_zip="10001",
        ...     weight_lbs=5.5,
        ...     service_type="ground"
        ... )
        {
            "rates": [
                {"service_type": "ground", "cost": 15.99, "estimated_delivery_days": 3},
                {"service_type": "priority", "cost": 25.99, "estimated_delivery_days": 2}
            ],
            "origin_zip": "90210",
            "destination_zip": "10001",
            "weight_lbs": 5.5
        }
    """
    try:
        # Validate input
        request = RateInquiryRequest(
            origin_zip=origin_zip,
            destination_zip=destination_zip,
            weight_lbs=weight_lbs,
            service_type=service_type,
        )

        store = get_sqlite_store()
        response_data = store.get_rates(
            origin_zip=request.origin_zip,
            destination_zip=request.destination_zip,
            weight_lbs=request.weight_lbs,
            service_type=request.service_type,
        )

        # Parse and validate response
        response = RateInquiryResponse(**response_data)
        logger.info("Retrieved %d rate options for %s -> %s", len(response.rates), origin_zip, destination_zip)
        return response.model_dump()

    except ValidationError as e:
        logger.warning("Validation error for get_shipping_quote: %s", e)
        return {
            "error": True,
            "message": f"Invalid location or weight: {str(e)}",
        }
    except ValueError as e:
        logger.warning("Validation error for get_shipping_quote: %s", e)
        return {
            "error": True,
            "message": f"Invalid location or weight: {str(e)}",
        }
    except Exception as e:
        logger.error("Error getting shipping quote: %s", e)
        return {
            "error": True,
            "message": "Could not retrieve rates right now. Please try again shortly.",
        }
