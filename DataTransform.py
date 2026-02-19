"""
DataTransform.py

Handles transformation of raw experimental data for linearisation.
Transforms both numerical values and axis titles based on the equation type.
Supports log, exp, power, reciprocal, and square-root transformations.
"""

import numpy as np
import sympy as sp
from typing import Tuple, Optional, Dict
from LineaX_Classes import InputData


class DataTransformer:
    """
    Transforms experimental data based on linearisation requirements.

    Supported transforms: ln(x), exp(x), x^n, 1/x, sqrt(x), applied to
    either axis independently, with correct error propagation throughout.
    """

    def __init__(self, input_data: InputData):
        self.raw_data = input_data
        self.transformed_data: Optional[InputData] = None
        self.transformation_applied: Optional[Dict] = None

    def transform_for_linearisation(
            self,
            x_transform: Optional[str] = None,
            y_transform: Optional[str] = None,
            x_var: str = "x",
            y_var: str = "y"
    ) -> InputData:
        """
        Apply axis transformations to produce a linearised dataset.

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

        Returns:
            Tuple of (transformed_values, transformed_errors, new_title).
        """
        if transform is None or transform == var_name:
            return values, errors, original_title

        t = transform.lower().replace(" ", "")

        if "ln(" in t or "log(" in t:
            return *self._apply_log_transform(values, errors), f"ln({original_title})"
        if "exp(" in t:
            return *self._apply_exp_transform(values, errors), f"exp({original_title})"
        if "sqrt(" in t:
            return *self._apply_sqrt_transform(values, errors), f"\u221a{original_title}"
        if t.startswith("1/"):
            return *self._apply_reciprocal_transform(values, errors), f"1/{original_title}"
        if "**" in t or "^" in t:
            power = self._extract_power(t)
            return *self._apply_power_transform(values, errors, power), f"{original_title}^{power}"

        return values, errors, original_title

    def _apply_log_transform(self, values: np.ndarray, errors: Optional[np.ndarray]) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Apply ln; propagates error as Δln(x) = Δx/x."""
        if np.any(values <= 0):
            raise ValueError("Cannot take logarithm of non-positive values")
        new_vals = np.log(values)
        return new_vals, (errors / values if errors is not None else None)

    def _apply_exp_transform(self, values: np.ndarray, errors: Optional[np.ndarray]) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Apply exp; propagates error as Δexp(x) = exp(x)·Δx."""
        new_vals = np.exp(values)
        return new_vals, (new_vals * errors if errors is not None else None)

    def _apply_power_transform(self, values: np.ndarray, errors: Optional[np.ndarray], power: float) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Apply x^n; propagates error as Δ(x^n) = n·x^(n-1)·Δx."""
        new_vals = np.power(values, power)
        new_errs = np.abs(power * np.power(values, power - 1) * errors) if errors is not None else None
        return new_vals, new_errs

    def _apply_reciprocal_transform(self, values: np.ndarray, errors: Optional[np.ndarray]) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Apply 1/x; propagates error as Δ(1/x) = Δx/x²."""
        if np.any(values == 0):
            raise ValueError("Cannot take reciprocal of zero")
        new_vals = 1.0 / values
        return new_vals, (errors / (values ** 2) if errors is not None else None)

    def _apply_sqrt_transform(self, values: np.ndarray, errors: Optional[np.ndarray]) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Apply √x; propagates error as Δ√x = Δx / (2√x)."""
        if np.any(values < 0):
            raise ValueError("Cannot take square root of negative values")
        new_vals = np.sqrt(values)
        return new_vals, (errors / (2 * new_vals) if errors is not None else None)

    def _extract_power(self, transform_str: str) -> float:
        """Extract the exponent value from a power transform string (x**n or x^n)."""
        sep = "**" if "**" in transform_str else "^"
        try:
            return float(transform_str.split(sep)[1].strip("()"))
        except (IndexError, ValueError):
            return 1.0

    def get_transformation_info(self) -> Dict[str, str]:
        """Return a summary dict of applied transformations."""
        if self.transformation_applied is None:
            return {"status": "No transformation applied", "x_transform": "x", "y_transform": "y"}
        return {"status": "Transformation applied", **self.transformation_applied}

    def revert_to_raw(self) -> InputData:
        """Return the original, untransformed InputData."""
        return self.raw_data


def identify_required_transformations(linearised_eq: sp.Eq, x_var: str, y_var: str) -> Tuple[str, str]:
    """
    Identify axis transformations needed from a linearised SymPy equation.

    Returns:
        Tuple of (x_transform, y_transform) as strings.
    """
    lhs, rhs = linearised_eq.lhs, linearised_eq.rhs
    x_sym = sp.Symbol(x_var)

    # Determine y-axis transform from LHS structure
    if isinstance(lhs, sp.log):
        y_transform = f"ln({y_var})"
    elif isinstance(lhs, sp.Pow):
        y_transform = f"{y_var}**{lhs.args[1]}"
    else:
        y_transform = y_var

    # Determine x-axis transform by traversing RHS
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