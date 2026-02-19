"""
NumberFormatting.py - Utility functions for displaying numerical values.

Provides consistent number formatting across the application:
- Standard form (×10^x) for exponents outside [-3, 4]; decimal notation otherwise.
- Uncertainty display with ± symbol.
"""

import math
from typing import Optional

# Superscript character map for exponent formatting
_SUPERSCRIPT = str.maketrans('0123456789+-', '⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻')


def format_exponent(exponent: int) -> str:
    """Return the exponent as a superscript Unicode string."""
    return str(exponent).translate(_SUPERSCRIPT)


def format_number(value: float, sig_figs: int = 4) -> str:
    """
    Format a number using decimal notation or standard form.

    Uses decimal notation when -3 ≤ exponent ≤ 4; standard form (×10ⁿ) otherwise.

    Args:
        value: The number to format.
        sig_figs: Number of significant figures (default 4).

    Returns:
        Formatted string, e.g. "0.00123" or "1.23×10⁻⁴".
    """
    if value is None:
        return "—"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "—"
    if math.isnan(value):
        return "NaN"
    if math.isinf(value):
        return "-∞" if value < 0 else "∞"
    if value == 0:
        return "0"

    try:
        sign = "-" if value < 0 else ""
        abs_value = abs(value)
        exponent = math.floor(math.log10(abs_value))

        if -3 <= exponent <= 4:
            decimal_places = max(0, sig_figs - exponent - 1) if exponent >= 0 else sig_figs - exponent - 1
            formatted = f"{abs_value:.{decimal_places}f}"
            if '.' in formatted:
                formatted = formatted.rstrip('0').rstrip('.')
            return sign + formatted

        # Standard form
        coef_str = f"{abs_value / (10 ** exponent):.{sig_figs - 1}f}".rstrip('0').rstrip('.')
        return f"{sign}{coef_str}×10{format_exponent(exponent)}"

    except (ValueError, OverflowError, ZeroDivisionError):
        return f"{value:.{sig_figs}g}"


def format_number_with_uncertainty(value: float, uncertainty: float, sig_figs: int = 3) -> str:
    """
    Format a value with its uncertainty as "value ± uncertainty".

    Args:
        value: The measured value.
        uncertainty: The measurement uncertainty.
        sig_figs: Significant figures for both numbers (default 3).

    Returns:
        Formatted string, e.g. "5.09×10⁻² ± 7.59×10⁻⁴".
    """
    try:
        uncertainty = float(uncertainty) if uncertainty is not None else 0.0
    except (TypeError, ValueError):
        uncertainty = 0.0
    if math.isnan(uncertainty) or math.isinf(uncertainty):
        uncertainty = 0.0

    if uncertainty == 0:
        return format_number(value, sig_figs)
    return f"{format_number(value, sig_figs)} ± {format_number(uncertainty, sig_figs)}"


def format_percentage(value: float, decimal_places: int = 2) -> str:
    """Return a percentage string, e.g. "5.23%"."""
    return f"{value:.{decimal_places}f}%"


def format_scientific_for_display(value: float) -> str:
    """
    Format a number for display in equations using ^ notation.

    Used where Unicode superscripts may not render correctly.

    Returns:
        Formatted string, e.g. "5.09×10^-2" or "510.79".
    """
    if value == 0:
        return "0"

    sign = "-" if value < 0 else ""
    abs_value = abs(value)
    exponent = math.floor(math.log10(abs_value))

    if -3 <= exponent <= 4:
        decimal_places = max(0, 4 - exponent - 1) if exponent >= 0 else 4 - exponent - 1
        formatted = f"{abs_value:.{decimal_places}f}"
        if '.' in formatted:
            formatted = formatted.rstrip('0').rstrip('.')
        return sign + formatted

    coef_str = f"{abs_value / (10 ** exponent):.3f}".rstrip('0').rstrip('.')
    return f"{sign}{coef_str}×10^{exponent}"


if __name__ == "__main__":
    print("Number Formatting Tests")

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
        print(f"{value:12.6e} → {format_number(value):20s} # {description}")

    print("\nWith Uncertainty Tests")
    for value, uncertainty in [(5.0912e-2, 7.594e-4), (510.79, 5.2), (0.00123, 0.00005), (123456, 234)]:
        print(f"{value:.4e} ± {uncertainty:.4e}")
        print(f"  → {format_number_with_uncertainty(value, uncertainty)}\n")