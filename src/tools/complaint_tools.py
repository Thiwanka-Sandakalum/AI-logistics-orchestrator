"""Tools for filing complaints and reporting issues."""

import logging
from typing import Optional

from langchain.tools import tool
from pydantic import ValidationError
from src.tools.schemas import (
    ComplaintRequest,
    ComplaintResponse,
)
from src.storage.sqlite_db import get_sqlite_store

logger = logging.getLogger(__name__)


@tool(args_schema=ComplaintRequest)
def file_complaint(
    tracking_number: str,
    issue_type: str,
    description: str,
    contact_email: str,
    contact_phone: Optional[str] = None,
) -> dict:
    """
    File a complaint or damage report for a shipment.

    ⚠️ WARNING: This tool requires human approval before execution.

    This tool creates a formal complaint ticket for shipment issues such as
    damage, missing contents, or late delivery. A support representative will
    investigate and follow up with the customer.

    Args:
        tracking_number: 9-digit tracking number of the affected shipment
        issue_type: Category of complaint:
            - "missing": Items missing from shipment
            - "damaged": Package or contents damaged
            - "late": Delivery is late or delayed
            - "other": Other issues
        description: Detailed explanation of the problem (10-1000 characters).
                    Include specific details like damage photos reference or
                    missing item counts.
        contact_email: Email address for follow-up communication
        contact_phone: Phone number for follow-up (optional)

    Returns:
        A dictionary containing:
        - ticket_id: Unique ticket identifier for tracking the complaint
        - status: Current status of the complaint investigation
        - next_steps: What the customer should expect next
        - estimated_resolution: Expected resolution date (if available)

    Example:
        >>> file_complaint(
        ...     tracking_number="123456789",
        ...     issue_type="damaged",
        ...     description="Package arrived with large dent and item inside is broken",
        ...     contact_email="customer@example.com",
        ...     contact_phone="+1-555-0123"
        ... )
        {
            "ticket_id": "TICKET-001",
            "status": "received",
            "next_steps": "Our team will investigate and contact you within 24 hours",
            "estimated_resolution": "2026-04-28"
        }
    """
    try:
        # Validate input
        request = ComplaintRequest(
            tracking_number=tracking_number,
            issue_type=issue_type,
            description=description,
            contact_email=contact_email,
            contact_phone=contact_phone,
        )

        store = get_sqlite_store()
        response_data = store.file_complaint(request.model_dump(exclude_none=True))

        # Parse and validate response
        response = ComplaintResponse(**response_data)
        logger.info("Complaint filed with ticket ID: %s", response.ticket_id)
        return response.model_dump()

    except ValidationError as e:
        logger.warning("Validation error for file_complaint: %s", e)
        return {
            "error": True,
            "message": f"Invalid complaint data: {str(e)}",
        }
    except ValueError as e:
        logger.warning("Validation error for file_complaint: %s", e)
        return {
            "error": True,
            "message": f"Invalid complaint data: {str(e)}",
        }
    except Exception as e:
        logger.error("Error filing complaint: %s", e)
        return {
            "error": True,
            "message": "Could not file complaint right now. Please try again shortly.",
        }
