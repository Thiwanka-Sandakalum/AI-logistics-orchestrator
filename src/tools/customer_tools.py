"""Tools for customer lookup and profile information."""

import logging
from langchain.tools import tool
from pydantic import ValidationError
from src.tools.schemas import (
    CustomerLookupRequest,
    CustomerLookupResponse,
)
from src.sqlite_db import get_sqlite_store

logger = logging.getLogger(__name__)


@tool(args_schema=CustomerLookupRequest)
def lookup_customer(phone_or_email: str) -> dict:
    """
    Find a customer account by phone number or email address.

    This tool retrieves customer profile information and recent shipment history
    using their contact details. Useful for verifying customer identity and
    showing them their active and past shipments.

    Args:
        phone_or_email: Either a 10-digit phone number (e.g., "5551234567")
                       or an email address (e.g., "customer@example.com")

    Returns:
        A dictionary containing:
        - customer_id: Unique customer identifier
        - name: Full name of the customer
        - email: Email address (optional)
        - phone: Phone number (optional)
        - recent_shipments: List of the last 5 shipments with:
            - tracking_number: 9-digit tracking number
            - status: Current shipment status
            - destination_city: Destination city
            - destination_state: Destination state
            - estimated_delivery: Estimated delivery date (may be None)
        - total_shipments: Total number of shipments on record
        - account_status: Status of the account (e.g., "active")

    Example:
        >>> lookup_customer("5551234567")
        {
            "customer_id": "CUST-12345",
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "5551234567",
            "recent_shipments": [
                {
                    "tracking_number": "987654321",
                    "status": "delivered",
                    "destination_city": "New York",
                    "destination_state": "NY",
                    "estimated_delivery": None
                }
            ],
            "total_shipments": 5,
            "account_status": "active"
        }
    """
    try:
        # Validate input
        request = CustomerLookupRequest(phone_or_email=phone_or_email)

        store = get_sqlite_store()
        response_data = store.lookup_customer(request.phone_or_email)

        # Parse and validate response
        response = CustomerLookupResponse(**response_data)
        logger.info("Found customer: %s with %d shipments", response.customer_id, response.total_shipments)
        return response.model_dump()

    except ValidationError as e:
        logger.warning("Validation error for lookup_customer: %s", e)
        return {
            "error": True,
            "message": f"Invalid contact information: {str(e)}",
        }
    except ValueError as e:
        logger.warning("Validation error for lookup_customer: %s", e)
        return {
            "error": True,
            "message": f"Invalid contact information: {str(e)}",
        }
    except Exception as e:
        logger.error("Error looking up customer: %s", e)
        return {
            "error": True,
            "message": f"Could not find customer: {str(e)}",
        }
