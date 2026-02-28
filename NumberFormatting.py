"""NumberFormatting.py — Consistent number display utilities for LineaX.

All result values displayed to the user pass through one of the four public
functions here to ensure consistent significant figures and notation, satisfying
success criterion 2.3.1 (results must be presented to an appropriate precision).

Standard form is used for very large or very small values (exponent outside
-3 to +4) to match the OCR Physics A convention for scientific notation.
"""

# math provides floor and log10 for computing the decimal exponent of a number,
# as well as isnan and isinf for guarding against degenerate floating-point values.
import math

# Optional is used in type hints to indicate that a value may be None.
from typing import Optional

# Translation table mapping ASCII digit/sign characters to Unicode superscript equivalents,
# used to render exponents as e.g. ×10² rather than ×10^2.
_SUPERSCRIPT = str.maketrans('0123456789+-', '⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻')


def format_exponent(exponent: int) -> str:
    """Return the exponent as a Unicode superscript string.

    str.translate applies the _SUPERSCRIPT mapping character by character,
    converting each ASCII digit to its Unicode superscript equivalent.
    """
    return str(exponent).translate(_SUPERSCRIPT)


def format_number(value: float, sig_figs: int = 4) -> str:
    """Format a number in decimal notation or standard form to sig_figs significant figures.

    Decision rule (implements the display logic in Section 3.2.2, Results Panel):
      - Returns decimal notation when -3 <= exponent <= 4 (e.g. 0.001 to 9999).
      - Returns standard form (×10ⁿ with Unicode superscript) outside that range.

    math.log10 computes the base-10 logarithm; math.floor converts it to an integer
    exponent, giving the order of magnitude of the value.
    rstrip('0').rstrip('.') removes trailing zeros and the trailing decimal point
    from the formatted string to produce clean output (e.g. '1.50' becomes '1.5').
    """
    if value is None:
        return "N/A"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "N/A"

    # Guard against non-finite values before attempting logarithm.
    if math.isnan(value):
        return "NaN"
    if math.isinf(value):
        return "-∞" if value < 0 else "∞"
    if value == 0:
        return "0"

    try:
        sign = "-" if value < 0 else ""
        abs_value = abs(value)

        # math.floor(math.log10(x)) gives the integer exponent of x in base 10.
        exponent = math.floor(math.log10(abs_value))

        if -3 <= exponent <= 4:
            # Decimal notation: compute required decimal places from sig_figs and exponent.
            decimal_places = max(0, sig_figs - exponent - 1) if exponent >= 0 else sig_figs - exponent - 1
            formatted = f"{abs_value:.{decimal_places}f}"
            if '.' in formatted:
                formatted = formatted.rstrip('0').rstrip('.')
            return sign + formatted

        # Standard form: divide by 10^exponent to get coefficient in [1, 10).
        coef_str = f"{abs_value / (10 ** exponent):.{sig_figs - 1}f}".rstrip('0').rstrip('.')
        return f"{sign}{coef_str}×10{format_exponent(exponent)}"

    except (ValueError, OverflowError, ZeroDivisionError):
        # Fallback to Python's built-in general format for edge cases.
        return f"{value:.{sig_figs}g}"


def format_number_with_uncertainty(value: float, uncertainty: float, sig_figs: int = 3) -> str:
    """Format a value with its uncertainty as 'value ± uncertainty'.

    Both value and uncertainty are formatted independently via format_number so
    they share the same significant figures and notation convention.
    Used to display gradient and intercept results on Screen 3a and Screen 4,
    satisfying success criterion 2.3.1.
    """
    try:
        uncertainty = float(uncertainty) if uncertainty is not None else 0.0
    except (TypeError, ValueError):
        uncertainty = 0.0

    # isnan / isinf guard against propagated floating-point errors from regression.
    if math.isnan(uncertainty) or math.isinf(uncertainty):
        uncertainty = 0.0

    if uncertainty == 0:
        return format_number(value, sig_figs)
    return f"{format_number(value, sig_figs)} ± {format_number(uncertainty, sig_figs)}"


def format_percentage(value: float, decimal_places: int = 2) -> str:
    """Return a percentage string, e.g. '5.23%'.

    Used to display worst-fit percentage differences on Screen 3a (Algorithm 5,
    Section 3.2.2) and percentage difference comparisons on Screen 4.
    """
    return f"{value:.{decimal_places}f}%"


def format_scientific_for_display(value: float) -> str:
    """Format a number using ^ notation for Matplotlib annotation compatibility.

    Matplotlib's mathtext renderer uses ^ for superscripts in axis annotations,
    so this function returns strings such as '1.23×10^-4' rather than '1.23×10⁻⁴'.
    The logic mirrors format_number but always uses ^ rather than Unicode superscripts.
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
        (0.00123, "Normal decimal (small)"), (0.000123, "Standard form (very small)"),
        (12345, "Normal decimal (medium)"), (123456, "Standard form (large)"),
        (5.0912e-2, "Standard form example"), (510.79, "Normal decimal"),
        (-0.05, "Negative decimal"), (6.1302e-2, "Should be decimal"),
        (1.7713e-2, "Should be decimal"), (5.167e-2, "Should be decimal"),
        (0.0001, "Boundary case"), (10000, "Boundary case"),
    ]
    for value, description in test_cases:
        print(f"{value:12.6e} -> {format_number(value):20s} # {description}")
    print("\nWith Uncertainty Tests")
    for value, uncertainty in [(5.0912e-2, 7.594e-4), (510.79, 5.2), (0.00123, 0.00005), (123456, 234)]:
        print(f"{value:.4e} +/- {uncertainty:.4e}")
        print(f"  -> {format_number_with_uncertainty(value, uncertainty)}\n")