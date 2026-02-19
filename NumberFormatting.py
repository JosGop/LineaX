"""
NumberFormatting.py

Utility functions for displaying numerical values consistently across LineaX.
Implements the number display requirements from Section 3.2.2 (Key Variables,
Data Structures, and Validation) — specifically the annotation_text, gradient,
gradient_uncertainty, and R_squared variables, which must be formatted to a
consistent number of significant figures. The standard form threshold (exponent
outside [-3, 4]) corresponds to the sig_figs validation rule in user_settings
(Section 3.2.2). Also satisfies the success criterion in Section 3.1.4 (Measurable
Success Criteria) that results must be presented to an appropriate number of
significant figures, with correct scientific notation for very large or small values.
"""

import math
from typing import Optional

# Superscript character map for exponent formatting in standard form display
_SUPERSCRIPT = str.maketrans('0123456789+-', '⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻')


def format_exponent(exponent: int) -> str:
    """
    Return the exponent as a superscript Unicode string.

    Used by format_number() to render standard form notation (e.g., ×10⁻⁴) in
    graph annotations and results panels. Unicode superscripts ensure the notation
    displays correctly in Tkinter labels without requiring LaTeX rendering, consistent
    with the accessibility requirements in Section 3.1.4 (Limitations).
    """
    return str(exponent).translate(_SUPERSCRIPT)


def format_number(value: float, sig_figs: int = 4) -> str:
    """
    Format a number using decimal notation or standard form.

    Implements the number display logic required across multiple screens: the gradient
    and intercept values on Screen 3a (Linear Graph Output), the R² value on Screen 3b
    (Automated Graph Output), and the physical constant results on Screen 4 (Gradient
    Analysis & Results), all described in Section 3.2.2 (User Interface). Switches
    between decimal and standard form based on the exponent range, consistent with the
    sig_figs validation rule (2–6) from the user_settings variable in the Key Variables
    table (Section 3.2.2).

    Uses decimal notation when -3 ≤ exponent ≤ 4; standard form (×10ⁿ) otherwise.

    Args:
        value: The number to format.
        sig_figs: Number of significant figures (default 4).

    Returns:
        Formatted string, e.g. "0.00123" or "1.23×10⁻⁴".
    """
    if value is None:
        return "—"  # em-dash indicates missing value consistently across all result panels
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
            # Decimal notation range — strip trailing zeros for clean presentation
            decimal_places = max(0, sig_figs - exponent - 1) if exponent >= 0 else sig_figs - exponent - 1
            formatted = f"{abs_value:.{decimal_places}f}"
            if '.' in formatted:
                formatted = formatted.rstrip('0').rstrip('.')
            return sign + formatted

        # Standard form for values outside the decimal range
        coef_str = f"{abs_value / (10 ** exponent):.{sig_figs - 1}f}".rstrip('0').rstrip('.')
        return f"{sign}{coef_str}×10{format_exponent(exponent)}"

    except (ValueError, OverflowError, ZeroDivisionError):
        return f"{value:.{sig_figs}g}"  # fallback to Python's own general format


def format_number_with_uncertainty(value: float, uncertainty: float, sig_figs: int = 3) -> str:
    """
    Format a value with its uncertainty as "value ± uncertainty".

    Used to display the gradient and physical constant results on Screen 4 (Section
    3.2.2, User Interface — Gradient Analysis & Results), e.g. "k = 48.5 ± 2.1 N/m".
    Also used for the gradient_uncertainty variable from the Key Variables table
    (Section 3.2.2), which is computed by Algorithm 5 (worst-fit line calculation).
    Handles NaN and Inf uncertainties gracefully, as required by the validation rule
    that gradient_uncertainty must be non-negative (Section 3.2.2, Key Variables).

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
        uncertainty = 0.0  # treat non-finite uncertainty as zero to prevent display errors

    if uncertainty == 0:
        return format_number(value, sig_figs)  # omit ± 0 for cleaner result presentation
    return f"{format_number(value, sig_figs)} ± {format_number(uncertainty, sig_figs)}"


def format_percentage(value: float, decimal_places: int = 2) -> str:
    """
    Return a percentage string, e.g. "5.23%".

    Used to display the percentage difference between experimental and accepted values
    on Screen 4 (Section 3.2.2, Section 3: Compare with Known Value), computed as
    |(experimental - accepted) / accepted| × 100%.
    """
    return f"{value:.{decimal_places}f}%"


def format_scientific_for_display(value: float) -> str:
    """
    Format a number for display in equations using ^ notation.

    Alternative to format_number() for contexts where Unicode superscripts may not
    render correctly, such as equation annotation strings (annotation_text variable,
    Section 3.2.2 Key Variables) that are passed to Matplotlib ax.annotate(). Uses
    ×10^n notation instead of Unicode superscripts to ensure compatibility across
    rendering backends.

    Returns:
        Formatted string, e.g. "5.09×10^-2" or "510.79".
    """
    if value == 0:
        return "0"

    sign = "-" if value < 0 else ""
    abs_value = abs(value)
    exponent = math.floor(math.log10(abs_value))

    if -3 <= exponent <= 4:
        # Same decimal range as format_number but with ^ notation
        decimal_places = max(0, 4 - exponent - 1) if exponent >= 0 else 4 - exponent - 1
        formatted = f"{abs_value:.{decimal_places}f}"
        if '.' in formatted:
            formatted = formatted.rstrip('0').rstrip('.')
        return sign + formatted

    # Standard form with caret notation for Matplotlib compatibility
    coef_str = f"{abs_value / (10 ** exponent):.3f}".rstrip('0').rstrip('.')
    return f"{sign}{coef_str}×10^{exponent}"


if __name__ == "__main__":
    """
    Manual test cases for white-box testing during Stage 1 development (Section 3.2.3).

    Each case corresponds to a boundary or typical value from the Extreme Values and
    Computation Accuracy test scenarios in the Stage 1 testing table (Section 3.2.3).
    Verifies that format_number() correctly switches between decimal and standard form
    at the ±3/4 exponent boundaries, and that format_number_with_uncertainty() produces
    the ± notation expected on Screen 4 (Section 3.2.2, User Interface).
    """
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