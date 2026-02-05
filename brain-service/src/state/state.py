"""
Shared state model for Brain Service (Pydantic).
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class BrainState(BaseModel):
    session_id: Optional[str] = None  # For agent context and history
    intent: str
    shipment: Optional[Dict[str, Any]] = None
    rates: Optional[List[Dict[str, Any]]] = None
    label: Optional[Dict[str, Any]] = None
    tracking: Optional[Dict[str, Any]] = None
    approval_required: bool = False
    approved: bool = False
    error: Optional[str] = None
    error_code: Optional[str] = None  # e.g., 'MISSING_SLOT', 'MCP_ERROR', 'UNKNOWN_INTENT'
    error_details: Optional[dict] = None  # Additional structured info for error correction
