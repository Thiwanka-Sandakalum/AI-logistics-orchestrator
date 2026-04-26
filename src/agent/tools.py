"""Tool registry for the courier assistant agent."""

from src.tools.complaint_tools import file_complaint
from src.tools.customer_tools import lookup_customer
from src.tools.rate_tools import get_shipping_quote
from src.tools.shipment_tools import create_shipment, get_shipment_details, track_shipment

TOOLS = [
    track_shipment,
    create_shipment,
    get_shipment_details,
    lookup_customer,
    file_complaint,
    get_shipping_quote,
]
