"""Pydantic schemas for tool inputs and outputs.

These schemas define strict contracts for:
- Tool input validation
- API request/response mapping
- Type-safe tool argument handling
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ============================================================================
# TRACKING / SHIPMENT STATUS
# ============================================================================


class TrackingRequest(BaseModel):
    """Input schema for track_shipment tool."""

    model_config = ConfigDict(json_schema_extra={"example": {"tracking_number": "123456789"}})

    tracking_number: str = Field(
        ...,
        description="9-digit tracking number (e.g., 123456789)",
        pattern=r"^\d{9}$",
    )


class TrackingResponse(BaseModel):
    """Response schema from shipment tracking API."""

    tracking_number: str
    status: str  # "in_transit", "delivered", "pending", "exception"
    current_location: str
    estimated_delivery: Optional[str] = None
    last_update: str
    carrier: Optional[str] = None


# ============================================================================
# RATE INQUIRY / SHIPPING QUOTES
# ============================================================================


class RateInquiryRequest(BaseModel):
    """Input schema for get_shipping_quote tool."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "origin_zip": "90210",
                "destination_zip": "10001",
                "weight_lbs": 5.5,
                "service_type": "ground",
            }
        }
    )

    origin_zip: str = Field(
        ...,
        description="Origin postal/ZIP code",
        pattern=r"^[A-Za-z0-9-]{3,10}$",
    )
    destination_zip: str = Field(
        ...,
        description="Destination postal/ZIP code",
        pattern=r"^[A-Za-z0-9-]{3,10}$",
    )
    weight_lbs: float = Field(
        ...,
        gt=0,
        description="Package weight in pounds",
    )
    service_type: str = Field(
        default="ground",
        description="Service type: ground, express, priority, or overnight",
        pattern=r"^(ground|express|priority|overnight)$",
    )


class DistanceAndRateRequest(BaseModel):
    """Input schema for calculate_distance_and_rates tool."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "origin_zip": "90210",
                "destination_zip": "10001",
                "weight_lbs": 5.5,
                "length_inches": 12,
                "width_inches": 9,
                "height_inches": 6,
                "is_residential": True,
            }
        }
    )

    origin_zip: str = Field(
        ...,
        description="5-digit origin ZIP code",
        pattern=r"^\d{5}$",
    )
    destination_zip: str = Field(
        ...,
        description="5-digit destination ZIP code",
        pattern=r"^\d{5}$",
    )
    weight_lbs: float = Field(..., gt=0, description="Package weight in pounds")
    length_inches: Optional[float] = Field(None, gt=0)
    width_inches: Optional[float] = Field(None, gt=0)
    height_inches: Optional[float] = Field(None, gt=0)
    is_residential: bool = False

    @model_validator(mode="after")
    def validate_dimensions(self) -> "DistanceAndRateRequest":
        provided = [
            self.length_inches is not None,
            self.width_inches is not None,
            self.height_inches is not None,
        ]
        if any(provided) and not all(provided):
            raise ValueError(
                "length_inches, width_inches, and height_inches must be provided together"
            )
        return self


class RateOption(BaseModel):
    """Single rate option."""

    service_type: str
    cost: float
    estimated_delivery_days: int
    carrier: Optional[str] = None


class RateInquiryResponse(BaseModel):
    """Response schema from rate inquiry API."""

    rates: List[RateOption] = Field(..., description="Available shipping rates")
    origin_zip: str
    destination_zip: str
    weight_lbs: float


# ============================================================================
# CREATE SHIPMENT
# ============================================================================


class CreateShipmentRequest(BaseModel):
    """Input schema for create_shipment tool."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sender_name": "John Doe",
                "sender_address": "123 Main St",
                "sender_city": "Los Angeles",
                "sender_state": "CA",
                "sender_zip": "90210",
                "recipient_name": "Jane Smith",
                "recipient_address": "456 Broadway",
                "recipient_city": "New York",
                "recipient_state": "NY",
                "recipient_zip": "10001",
                "weight_lbs": 5.5,
                "service_type": "ground",
                "description": "Documents",
            }
        }
    )

    sender_name: str = Field(..., min_length=1, max_length=100)
    sender_address: str = Field(..., min_length=5, max_length=100)
    sender_city: str = Field(..., min_length=1, max_length=50)
    sender_state: str = Field(..., pattern=r"^[A-Z]{2}$")
    sender_zip: str = Field(..., pattern=r"^\d{5}$")
    recipient_name: str = Field(..., min_length=1, max_length=100)
    recipient_address: str = Field(..., min_length=5, max_length=100)
    recipient_city: str = Field(..., min_length=1, max_length=50)
    recipient_state: str = Field(..., pattern=r"^[A-Z]{2}$")
    recipient_zip: str = Field(..., pattern=r"^\d{5}$")
    weight_lbs: float = Field(..., gt=0, description="Weight in pounds")
    service_type: str = Field(
        default="ground",
        pattern=r"^(ground|express|priority|overnight)$",
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Package contents description",
    )


class CreateShipmentResponse(BaseModel):
    """Response schema from create shipment API."""

    tracking_number: str
    estimated_delivery: str
    total_cost: float
    confirmation_id: str
    carrier: Optional[str] = None


# ============================================================================
# FILE COMPLAINT
# ============================================================================


class ComplaintRequest(BaseModel):
    """Input schema for file_complaint tool."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tracking_number": "123456789",
                "issue_type": "damaged",
                "description": "The package arrived with a large dent on the side and the contents appear damaged.",
                "contact_email": "customer@example.com",
                "contact_phone": "+1-555-0123",
            }
        }
    )

    tracking_number: str = Field(
        ...,
        description="9-digit tracking number",
        pattern=r"^\d{9}$",
    )
    issue_type: str = Field(
        ...,
        description="Type of complaint: missing, damaged, late, or other",
        pattern=r"^(missing|damaged|late|other)$",
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Detailed complaint description",
    )
    contact_email: str = Field(..., description="Email for complaint follow-up")
    contact_phone: Optional[str] = None


class ComplaintResponse(BaseModel):
    """Response schema from complaint filing API."""

    ticket_id: str
    status: str  # "received", "investigating", "resolved", etc.
    next_steps: str
    estimated_resolution: Optional[str] = None


# ============================================================================
# CUSTOMER LOOKUP
# ============================================================================


class CustomerLookupRequest(BaseModel):
    """Input schema for lookup_customer tool."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"phone_or_email": "5551234567"},
                {"phone_or_email": "customer@example.com"},
            ]
        }
    )

    phone_or_email: str = Field(
        ...,
        description="Phone number (10 digits) or email address",
    )


class ShipmentSummary(BaseModel):
    """Summary of a shipment for customer lookup."""

    tracking_number: str
    status: str
    destination_city: str
    destination_state: str
    estimated_delivery: Optional[str] = None


class CustomerLookupResponse(BaseModel):
    """Response schema from customer lookup API."""

    customer_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    recent_shipments: List[ShipmentSummary] = Field(
        default_factory=list,
        description="Last 5 shipments",
    )
    total_shipments: int
    account_status: str = "active"


# ============================================================================
# ERROR RESPONSES
# ============================================================================


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: bool = True
    message: str
    code: Optional[str] = None
    details: Optional[dict] = None
