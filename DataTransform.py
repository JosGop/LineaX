"""
DataTransform.py

Handles transformation of raw experimental data for linearisation.
Implements Algorithm 2 from Section 3.2.2 (Linearise to the form y = mx + c)
and the 'Assign apt. x and y values with respect to equation' sub-component from
Section 3.2.1 (Branch 3 — Linear). Transforms both numerical values and axis titles
based on the equation type, with correct error propagation throughout. The supported
transforms (ln, exp, power, reciprocal, sqrt) correspond directly to the examples
given in Section 3.2.1: exponential → Y = ln(I), power law → Y = log(y), X = log(x).
"""

import numpy as np
import sympy as sp
from typing import Tuple, Optional, Dict
from LineaX_Classes import InputData


class DataTransformer:
    """
    Transforms experimental data based on linearisation requirements.

    Implements the data transformation step described in the 'Manipulate user values
    if required' sub-component of Section 3.2.1 (Branch 3 — Linear) and Algorithm 2
    from Section 3.2.2. Stores transformation metadata in transformation_applied so
    that axis labels can be updated automatically (e.g., "Force" → "ln(Force)"),
    as required by Section 3.2.2 (User Interface) and the x_label / y_label variables
    in the Key Variables table (Section 3.2.2).

    Supported transforms: ln(x), exp(x), x^n, 1/x, sqrt(x), applied to
    either axis independently, with correct error propagation throughout.
    """

    def __init__(self, input_data: InputData):
        self.raw_data = input_data           # original untransformed InputData from Stage 1
        self.transformed_data: Optional[InputData] = None      # result of transform_for_linearisation()
        self.transformation_applied: Optional[Dict] = None     # records what transforms were used

    def transform_for_linearisation(
            self,
            x_transform: Optional[str] = None,
            y_transform: Optional[str] = None,
            x_var: str = "x",
            y_var: str = "y"
    ) -> InputData:
        """
        Apply axis transformations to produce a linearised dataset.

        Core method of Algorithm 2 (Section 3.2.2). Takes transformation strings derived
        from the selected scientific equation (e.g., "ln(y)" for exponential decay) and
        delegates to _transform_axis() for each axis. The returned InputData has updated
        axis titles (e.g., "ln(Intensity)") satisfying the label update requirement in
        Section 3.2.1 (Sub-sub-component: Assign apt. x and y values) and stores a
        transformation_applied dict for downstream use in GradientAnalysis.py.

        Args:
            x_transform: Transformation string for x-axis (e.g. "x**2", "1/x", "ln(x)").
            y_transform: Transformation string for y-axis (e.g. "ln(y)", "y**2").
            x_var: Variable name used in x transformation strings.
            y_var: Variable name used in y transformation strings.

        Returns:
            InputData with transformed values and updated axis titles.
        """
        self.transformed_data = InputData()

        x_vals, x_err, x_title = self._transform_axis(
            self.raw_data.x_values, self.raw_data.x_error, self.raw_data.x_title, x_transform, x_var
        )
        y_vals, y_err, y_title = self._transform_axis(
            self.raw_data.y_values, self.raw_data.y_error, self.raw_data.y_title, y_transform, y_var
        )

        self.transformed_data.x_values, self.transformed_data.x_error, self.transformed_data.x_title = x_vals, x_err, x_title
        self.transformed_data.y_values, self.transformed_data.y_error, self.transformed_data.y_title = y_vals, y_err, y_title

        # Record the applied transforms for reference by GradientAnalysis and axis labelling
        self.transformation_applied = {
            "x_transform": x_transform or "x",
            "y_transform": y_transform or "y",
            "x_title": x_title,
            "y_title": y_title
        }
        return self.transformed_data

    def _transform_axis(
            self,
            values: np.ndarray,
            errors: Optional[np.ndarray],
            original_title: str,
            transform: Optional[str],
            var_name: str
    ) -> Tuple[np.ndarray, Optional[np.ndarray], str]:
        """
        Transform a single axis according to the transform string.

        Routes to the appropriate private helper based on the transform string pattern,
        implementing the conditional logic of Algorithm 2 (Section 3.2.2). Also updates
        the axis title with the correct mathematical notation (e.g., "ln(Force)") to
        satisfy the axis label requirement from Section 3.2.1 (Assign apt. x and y values).
        Error propagation rules follow standard physics uncertainty analysis, as expected
        by the OCR A-Level specification cited in Section 3.2.2.

        Returns:
            Tuple of (transformed_values, transformed_errors, new_title).
        """
        if transform is None or transform == var_name:
            return values, errors, original_title  # no transformation needed; pass through unchanged

        t = transform.lower().replace(" ", "")

        # Route to the correct transform based on string pattern
        if "ln(" in t or "log(" in t:
            return *self._apply_log_transform(values, errors), f"ln({original_title})"
        if "exp(" in t:
            return *self._apply_exp_transform(values, errors), f"exp({original_title})"
        if "sqrt(" in t:
            return *self._apply_sqrt_transform(values, errors), f"√{original_title}"
        if t.startswith("1/"):
            return *self._apply_reciprocal_transform(values, errors), f"1/{original_title}"
        if "**" in t or "^" in t:
            power = self._extract_power(t)
            return *self._apply_power_transform(values, errors, power), f"{original_title}^{power}"

        return values, errors, original_title  # unrecognised pattern; leave unchanged

    def _apply_log_transform(self, values: np.ndarray, errors: Optional[np.ndarray]) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Apply ln; propagates error as Δln(x) = Δx/x.

        Used for exponential linearisation (e.g., A = A0·exp(-λt) → ln(A) = -λt + ln(A0))
        as described in Section 3.2.1 (Sub-sub-component: Linearise to y = mx + c) and
        Algorithm 2 from Section 3.2.2. Raises ValueError for non-positive values, implementing
        the 'Manipulate user values if required' guard described in Section 3.2.1.
        """
        if np.any(values <= 0):
            raise ValueError("Cannot take logarithm of non-positive values")
        new_vals = np.log(values)
        return new_vals, (errors / values if errors is not None else None)  # Δln(x) = Δx / x

    def _apply_exp_transform(self, values: np.ndarray, errors: Optional[np.ndarray]) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Apply exp; propagates error as Δexp(x) = exp(x)·Δx.

        Standard chain-rule uncertainty propagation for exponential transform, used when
        the inverse of a log linearisation is needed. Error propagation follows OCR Physics
        A uncertainty analysis conventions referenced in Section 3.2.2.
        """
        new_vals = np.exp(values)
        return new_vals, (new_vals * errors if errors is not None else None)  # Δexp(x) = exp(x)·Δx

    def _apply_power_transform(self, values: np.ndarray, errors: Optional[np.ndarray], power: float) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Apply x^n; propagates error as Δ(x^n) = n·x^(n-1)·Δx.

        Supports power-law linearisation (e.g., y = A·x^b → y^(1/b) = A^(1/b)·x) from
        Section 3.2.1. The absolute value in the error term ensures non-negative uncertainties
        when n < 1, consistent with the validation requirement for positive uncertainties in
        the Key Variables table (Section 3.2.2).
        """
        new_vals = np.power(values, power)
        new_errs = np.abs(power * np.power(values, power - 1) * errors) if errors is not None else None
        return new_vals, new_errs

    def _apply_reciprocal_transform(self, values: np.ndarray, errors: Optional[np.ndarray]) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Apply 1/x; propagates error as Δ(1/x) = Δx/x².

        Supports the reciprocal linearisation type (e.g., density ρ = m/V → 1/V = ρ/m),
        identified in Equations.py for equations tagged linearisation_type="reciprocal".
        Guards against division by zero before transformation, consistent with Algorithm 2
        input validation described in Section 3.2.1 (Manipulate user values if required).
        """
        if np.any(values == 0):
            raise ValueError("Cannot take reciprocal of zero")
        new_vals = 1.0 / values
        return new_vals, (errors / (values ** 2) if errors is not None else None)  # Δ(1/x) = Δx / x²

    def _apply_sqrt_transform(self, values: np.ndarray, errors: Optional[np.ndarray]) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Apply √x; propagates error as Δ√x = Δx / (2√x).

        Supports square-root linearisations for equations such as SUVAT where s ∝ t².
        Raises ValueError for negative values to prevent NaN propagation, satisfying the
        finite-value check required before regression in Section 3.2.1 (Ensure consistency
        with results sub-component).
        """
        if np.any(values < 0):
            raise ValueError("Cannot take square root of negative values")
        new_vals = np.sqrt(values)
        return new_vals, (errors / (2 * new_vals) if errors is not None else None)  # Δ√x = Δx / (2√x)

    def _extract_power(self, transform_str: str) -> float:
        """
        Extract the exponent value from a power transform string (x**n or x^n).

        Parses the transform string produced by identify_required_transformations() to
        obtain the numeric exponent. Falls back to 1.0 if parsing fails, preventing
        crashes from malformed transform strings as required by the robustness goals
        in Section 3.1.4 (Solution Requirements).
        """
        sep = "**" if "**" in transform_str else "^"
        try:
            return float(transform_str.split(sep)[1].strip("()"))
        except (IndexError, ValueError):
            return 1.0  # safe fallback; leaves values unchanged if exponent cannot be determined

    def get_transformation_info(self) -> Dict[str, str]:
        """
        Return a summary dict of applied transformations.

        Used by graph display modules to populate axis labels and annotation text after
        linearisation, as required by Section 3.2.2 (annotation_text and x_label/y_label
        variables in the Key Variables table).
        """
        if self.transformation_applied is None:
            return {"status": "No transformation applied", "x_transform": "x", "y_transform": "y"}
        return {"status": "Transformation applied", **self.transformation_applied}

    def revert_to_raw(self) -> InputData:
        """
        Return the original, untransformed InputData.

        Supports the 'Fit other Models' sub-component in Section 3.2.1 (Branch 4 —
        Graphs Options) where users can re-run analysis with a different model while
        preserving the original dataset. Also used by ScreenManager.get_raw_data()
        to retrieve the pre-transformation data.
        """
        return self.raw_data


def identify_required_transformations(linearised_eq: sp.Eq, x_var: str, y_var: str) -> Tuple[str, str]:
    """
    Identify axis transformations needed from a linearised SymPy equation.

    Companion function to DataTransformer.transform_for_linearisation(). Inspects
    the structure of a SymPy Eq produced by Algorithm 2 (Section 3.2.2) to determine
    which transforms were applied to each axis, returning transform strings compatible
    with _transform_axis(). Supports the 'Ensure consistency with results' sub-component
    of Section 3.2.1 by enabling cross-validation between the symbolic equation and the
    numeric transformation.

    Returns:
        Tuple of (x_transform, y_transform) as strings.
    """
    lhs, rhs = linearised_eq.lhs, linearised_eq.rhs
    x_sym = sp.Symbol(x_var)

    # Determine y-axis transform from LHS structure (e.g., ln(y) → "ln(y_var)")
    if isinstance(lhs, sp.log):
        y_transform = f"ln({y_var})"
    elif isinstance(lhs, sp.Pow):
        y_transform = f"{y_var}**{lhs.args[1]}"
    else:
        y_transform = y_var  # no y transformation detected

    # Determine x-axis transform by traversing RHS for power or reciprocal terms in x
    x_transform = x_var
    for term in sp.preorder_traversal(rhs):
        if isinstance(term, sp.Pow) and term.args[0] == x_sym:
            power = term.args[1]
            x_transform = f"1/{x_var}" if power == -1 else f"{x_var}**{power}"
            break
        if isinstance(term, sp.Mul):
            for factor in term.args:
                if isinstance(factor, sp.Pow) and factor.args[0] == x_sym:
                    power = factor.args[1]
                    x_transform = f"1/{x_var}" if power == -1 else f"{x_var}**{power}"
                    break

    return x_transform, y_transform