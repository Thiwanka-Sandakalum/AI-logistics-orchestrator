"""Standard box sizes and package type definitions for realistic shipping."""

from enum import Enum
from typing import NamedTuple, Optional


class BoxSize(Enum):
    """Standard FedEx-like box sizes."""
    ENVELOPE = "envelope"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EXTRA_LARGE = "extra_large"
    CUSTOM = "custom"


class BoxDimensions(NamedTuple):
    """Box dimensions in inches."""
    length: float
    width: float
    height: float

    def volume(self) -> float:
        """Calculate volume in cubic inches."""
        return self.length * self.width * self.height

    def perimeter_girth(self) -> float:
        """Calculate perimeter + girth for oversize penalties."""
        perimeter = 2 * (self.width + self.height)
        return self.length + perimeter


class PackageType(NamedTuple):
    """Package type with size constraints and default handling."""
    size: BoxSize
    dimensions: BoxDimensions
    max_weight_lbs: float
    dim_weight_divisor: int  # 139 for FedEx, 166 for UPS
    is_oversize: bool
    base_surcharge: float  # Additional charge for this box type


# FedEx-aligned standard packages
BOX_CATALOG = {
    BoxSize.ENVELOPE: PackageType(
        size=BoxSize.ENVELOPE,
        dimensions=BoxDimensions(length=12.5, width=9.5, height=0.75),
        max_weight_lbs=70,
        dim_weight_divisor=139,
        is_oversize=False,
        base_surcharge=0.0,
    ),
    BoxSize.SMALL: PackageType(
        size=BoxSize.SMALL,
        dimensions=BoxDimensions(length=12, width=9, height=6),
        max_weight_lbs=70,
        dim_weight_divisor=139,
        is_oversize=False,
        base_surcharge=1.50,
    ),
    BoxSize.MEDIUM: PackageType(
        size=BoxSize.MEDIUM,
        dimensions=BoxDimensions(length=20, width=15, height=12),
        max_weight_lbs=70,
        dim_weight_divisor=139,
        is_oversize=False,
        base_surcharge=3.00,
    ),
    BoxSize.LARGE: PackageType(
        size=BoxSize.LARGE,
        dimensions=BoxDimensions(length=30, width=20, height=15),
        max_weight_lbs=100,
        dim_weight_divisor=139,
        is_oversize=True,
        base_surcharge=6.00,
    ),
    BoxSize.EXTRA_LARGE: PackageType(
        size=BoxSize.EXTRA_LARGE,
        dimensions=BoxDimensions(length=36, width=24, height=18),
        max_weight_lbs=150,
        dim_weight_divisor=139,
        is_oversize=True,
        base_surcharge=9.00,
    ),
}


def calculate_dimensional_weight(
    length: float, width: float, height: float, divisor: int = 139
) -> float:
    """
    Calculate dimensional (billable) weight.
    
    FedEx uses divisor of 139 cubic inches per pound.
    
    Args:
        length: Length in inches
        width: Width in inches
        height: Height in inches
        divisor: Cubic inches per pound (default 139 for FedEx)
    
    Returns:
        Dimensional weight in pounds
    """
    volume = length * width * height
    dim_weight = volume / divisor
    return round(dim_weight, 2)


def billable_weight(actual_weight_lbs: float, dimensional_weight_lbs: float) -> float:
    """
    Billable weight is the greater of actual or dimensional weight.
    
    Args:
        actual_weight_lbs: Actual weight
        dimensional_weight_lbs: Calculated dimensional weight
    
    Returns:
        Weight to use for billing
    """
    return max(actual_weight_lbs, dimensional_weight_lbs)


def suggest_box_size(
    actual_weight_lbs: float,
    length: float,
    width: float,
    height: float,
) -> BoxSize:
    """
    Suggest the smallest box that fits the package.
    
    Args:
        actual_weight_lbs: Package weight
        length, width, height: Package dimensions in inches
    
    Returns:
        Suggested BoxSize
    """
    dim_weight = calculate_dimensional_weight(length, width, height)
    billable = billable_weight(actual_weight_lbs, dim_weight)

    # Check each box in order of size
    for box_size in [
        BoxSize.ENVELOPE,
        BoxSize.SMALL,
        BoxSize.MEDIUM,
        BoxSize.LARGE,
        BoxSize.EXTRA_LARGE,
    ]:
        pkg = BOX_CATALOG.get(box_size)
        if pkg is None:
            continue

        # Check if package fits physically and weight-wise
        dims_fit = (
            length <= pkg.dimensions.length
            and width <= pkg.dimensions.width
            and height <= pkg.dimensions.height
        )
        weight_ok = billable <= pkg.max_weight_lbs

        if dims_fit and weight_ok:
            return box_size

    # Default to extra large if nothing fits
    return BoxSize.EXTRA_LARGE
