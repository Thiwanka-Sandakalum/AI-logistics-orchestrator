"""Tools for shipment tracking and creation."""

import logging
from typing import Optional

from langchain.tools import tool
from pydantic import ValidationError
from src.tools.schemas import (
    TrackingRequest,
    TrackingResponse,
    CreateShipmentRequest,
    CreateShipmentResponse,
)
from src.sqlite_db import get_sqlite_store

logger = logging.getLogger(__name__)


@tool(args_schema=TrackingRequest)
def track_shipment(tracking_number: str) -> dict:
    """
    Track the real-time status of a shipment using its tracking number.

    This tool returns the current location, status, estimated delivery date,
    and last update time for any shipment in the system.

    Args:
        tracking_number: A 9-digit tracking number (e.g., "123456789")

    Returns:
        A dictionary containing:
        - tracking_number: The tracking number
        - status: Current status (in_transit, delivered, pending, exception)
        - current_location: Where the package currently is
        - estimated_delivery: Estimated delivery date (may be None)
        - last_update: When the status was last updated
        - carrier: Carrier name (optional)

    Example:
        >>> track_shipment("123456789")
        {
            "tracking_number": "123456789",
            "status": "in_transit",
            "current_location": "Chicago, IL",
            "estimated_delivery": "2026-04-26",
            "last_update": "2026-04-24T10:30:00Z",
            "carrier": "Loomis"
        }
    """
    try:
        # Validate input
        request = TrackingRequest(tracking_number=tracking_number)

        store = get_sqlite_store()
        response_data = store.get_tracking(request.tracking_number)
        if response_data is None:
            raise ValueError("Resource not found. Please verify the tracking number or ID.")

        # Parse and validate response
        response = TrackingResponse(**response_data)
        logger.info("Successfully tracked shipment: %s", tracking_number)
        return response.model_dump()

    except ValidationError as e:
        logger.warning("Validation error for tracking_number: %s", e)
        return {
            "error": True,
            "message": f"Invalid tracking number. {str(e)}",
        }
    except ValueError as e:
        logger.warning("Validation error for tracking_number: %s", e)
        return {
            "error": True,
            "message": f"Invalid tracking number. {str(e)}",
        }
    except Exception as e:
        logger.error("Error tracking shipment %s: %s", tracking_number, e)
        return {
            "error": True,
            "message": f"Could not track shipment: {str(e)}",
        }


@tool(args_schema=CreateShipmentRequest)
def create_shipment(
    sender_name: str,
    sender_address: str,
    sender_city: str,
    sender_state: str,
    sender_zip: str,
    recipient_name: str,
    recipient_address: str,
    recipient_city: str,
    recipient_state: str,
    recipient_zip: str,
    weight_lbs: float,
    service_type: str = "ground",
    description: Optional[str] = None,
) -> dict:
    """
    Create a new shipment and generate a tracking number.

    ⚠️ WARNING: This tool requires human approval before execution.

    This tool creates a new shipment in the system, validates all addresses,
    calculates shipping costs, and returns a tracking number for the customer.

    Args:
        sender_name: Full name of the sender
        sender_address: Street address of the sender
        sender_city: City of the sender
        sender_state: 2-letter state code (e.g., "CA")
        sender_zip: 5-digit ZIP code of the sender
        recipient_name: Full name of the recipient
        recipient_address: Street address of the recipient
        recipient_city: City of the recipient
        recipient_state: 2-letter state code (e.g., "NY")
        recipient_zip: 5-digit ZIP code of the recipient
        weight_lbs: Package weight in pounds (must be > 0)
        service_type: One of "ground", "express", "priority", or "overnight" (default: "ground")
        description: Description of package contents (optional)

    Returns:
        A dictionary containing:
        - tracking_number: 9-digit tracking number for the shipment
        - estimated_delivery: Expected delivery date
        - total_cost: Cost of the shipment
        - confirmation_id: Reference ID for this transaction
        - carrier: Carrier name (optional)

    Example:
        >>> create_shipment(
        ...     sender_name="John Doe",
        ...     sender_address="123 Main St",
        ...     sender_city="Los Angeles",
        ...     sender_state="CA",
        ...     sender_zip="90210",
        ...     recipient_name="Jane Smith",
        ...     recipient_address="456 Broadway",
        ...     recipient_city="New York",
        ...     recipient_state="NY",
        ...     recipient_zip="10001",
        ...     weight_lbs=5.5,
        ...     service_type="ground"
        ... )
    """
    try:
        # Validate input
        request = CreateShipmentRequest(
            sender_name=sender_name,
            sender_address=sender_address,
            sender_city=sender_city,
            sender_state=sender_state,
            sender_zip=sender_zip,
            recipient_name=recipient_name,
            recipient_address=recipient_address,
            recipient_city=recipient_city,
            recipient_state=recipient_state,
            recipient_zip=recipient_zip,
            weight_lbs=weight_lbs,
            service_type=service_type,
            description=description,
        )

        store = get_sqlite_store()
        response_data = store.create_shipment(request.model_dump(exclude_none=True))

        # Parse and validate response
        response = CreateShipmentResponse(**response_data)
        logger.info("Successfully created shipment: %s", response.tracking_number)
        return response.model_dump()

    except ValidationError as e:
        logger.warning("Validation error for create_shipment: %s", e)
        return {
            "error": True,
            "message": f"Invalid shipment data: {str(e)}",
        }
    except ValueError as e:
        logger.warning("Validation error for create_shipment: %s", e)
        return {
            "error": True,
            "message": f"Invalid shipment data: {str(e)}",
        }
    except Exception as e:
        logger.error("Error creating shipment: %s", e)
        return {
            "error": True,
            "message": f"Could not create shipment: {str(e)}",
        }
