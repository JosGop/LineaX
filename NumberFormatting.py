"""
NumberFormatting.py - Utility functions for displaying numerical values

Provides consistent number formatting across the application:
- Uses standard form (×10^x) instead of scientific notation (e notation)
- Shows normal decimal format when -3 < exponent < 5
- Properly formats uncertainties with ± symbol
"""

import math
from typing import Tuple, Optional


def format_number(value: float, sig_figs: int = 4) -> str:
    """
    Format a number using standard form or decimal notation.

    Rules:
    - If exponent is between -3 and 5 (exclusive), use decimal notation
    - Otherwise, use standard form: coefficient × 10^exponent

    Args:
        value: The number to format
        sig_figs: Number of significant figures (default: 4)

    Returns:
        Formatted string representation

    Examples:
        0.00123 → "0.00123"
        0.000123 → "1.23×10⁻⁴"
        12345 → "12345"
        123456 → "1.235×10⁵"
    """
    if value == 0:
        return "0"

    # Handle negative numbers
    sign = "-" if value < 0 else ""
    abs_value = abs(value)

    # Calculate the exponent
    exponent = math.floor(math.log10(abs_value))

    # Use decimal notation if -3 <= exponent <= 4
    if -3 <= exponent <= 4:
        # Determine decimal places needed
        if exponent >= 0:
            # For numbers >= 1, show enough decimals for sig_figs
            decimal_places = max(0, sig_figs - exponent - 1)
        else:
            # For numbers < 1, show enough decimals to reach sig_figs
            decimal_places = sig_figs - exponent - 1

        # Format with appropriate decimal places
        formatted = f"{abs_value:.{decimal_places}f}"

        # Remove trailing zeros after decimal point
        if '.' in formatted:
            formatted = formatted.rstrip('0').rstrip('.')

        return sign + formatted

    # Use standard form for very small or very large numbers
    coefficient = abs_value / (10 ** exponent)

    # Round coefficient to sig_figs
    coefficient_rounded = round(coefficient, sig_figs - 1)

    # Format coefficient (remove trailing zeros)
    coef_str = f"{coefficient_rounded:.{sig_figs - 1}f}".rstrip('0').rstrip('.')

    # Format exponent with superscript
    exp_str = format_exponent(exponent)

    return f"{sign}{coef_str}×10{exp_str}"


def format_number_with_uncertainty(value: float, uncertainty: float, sig_figs: int = 3) -> str:
    """
    Format a number with its uncertainty.

    The uncertainty determines the precision of the value display.

    Args:
        value: The measured value
        uncertainty: The uncertainty in the measurement
        sig_figs: Significant figures for uncertainty (default: 3)

    Returns:
        Formatted string like "5.09×10⁻² ± 7.59×10⁻⁴"

    Examples:
        (5.0912e-2, 7.594e-4) → "5.09×10⁻² ± 7.59×10⁻⁴"
        (510.79, 5.2) → "510.8 ± 5.2"
    """
    if uncertainty == 0:
        return format_number(value, sig_figs)

    # Format the value and uncertainty separately
    value_str = format_number(value, sig_figs)
    uncertainty_str = format_number(uncertainty, sig_figs)

    return f"{value_str} ± {uncertainty_str}"


def format_exponent(exponent: int) -> str:
    """
    Format an exponent with superscript characters.

    Args:
        exponent: The exponent value (e.g., -4, 2, 10)

    Returns:
        Superscript string (e.g., "⁻⁴", "²", "¹⁰")
    """
    superscript_map = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
        '-': '⁻', '+': '⁺'
    }

    exp_str = str(exponent)
    return ''.join(superscript_map.get(c, c) for c in exp_str)


def format_percentage(value: float, decimal_places: int = 2) -> str:
    """
    Format a percentage value.

    Args:
        value: The percentage value
        decimal_places: Number of decimal places (default: 2)

    Returns:
        Formatted string like "5.23%"
    """
    return f"{value:.{decimal_places}f}%"


def format_scientific_for_display(value: float) -> str:
    """
    Format for displaying in equation forms (using ^ for exponent).

    This is used in equations where Unicode superscripts might not render well.

    Args:
        value: The number to format

    Returns:
        Formatted string like "5.09×10^-2" or "510.79"
    """
    if value == 0:
        return "0"

    sign = "-" if value < 0 else ""
    abs_value = abs(value)

    exponent = math.floor(math.log10(abs_value))

    # Use decimal notation if -3 <= exponent <= 4
    if -3 <= exponent <= 4:
        if exponent >= 0:
            decimal_places = max(0, 4 - exponent - 1)
        else:
            decimal_places = 4 - exponent - 1

        formatted = f"{abs_value:.{decimal_places}f}"
        if '.' in formatted:
            formatted = formatted.rstrip('0').rstrip('.')

        return sign + formatted

    # Use standard form with ^ for exponent
    coefficient = abs_value / (10 ** exponent)
    coefficient_rounded = round(coefficient, 3)
    coef_str = f"{coefficient_rounded:.3f}".rstrip('0').rstrip('.')

    return f"{sign}{coef_str}×10^{exponent}"


# Test the formatting functions
if __name__ == "__main__":
    print("Number Formatting Tests")
    print("=" * 60)

    test_cases = [
        (0.00123, "Normal decimal (small)"),
        (0.000123, "Standard form (very small)"),
        (12345, "Normal decimal (medium)"),
        (123456, "Standard form (large)"),
        (5.0912e-2, "Standard form example"),
        (510.79, "Normal decimal"),
        (-0.05, "Negative decimal"),
        (6.1302e-2, "Should be decimal"),
        (1.7713e-2, "Should be decimal"),
        (5.167e-2, "Should be decimal"),
        (0.0001, "Boundary case"),
        (10000, "Boundary case"),
    ]

    for value, description in test_cases:
        formatted = format_number(value)
        print(f"{value:12.6e} → {formatted:20s} # {description}")

    print("\n" + "=" * 60)
    print("With Uncertainty Tests")
    print("=" * 60)

    uncertainty_cases = [
        (5.0912e-2, 7.594e-4),
        (510.79, 5.2),
        (0.00123, 0.00005),
        (123456, 234),
    ]

    for value, uncertainty in uncertainty_cases:
        formatted = format_number_with_uncertainty(value, uncertainty)
        print(f"{value:.4e} ± {uncertainty:.4e}")
        print(f"  → {formatted}")
        print()