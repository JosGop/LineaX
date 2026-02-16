"""
DataTransform.py

This module handles transformation of raw experimental data based on
linearisation requirements. It transforms both numerical values and axis titles
when an equation needs to be linearised for analysis.
"""

import numpy as np
import sympy as sp
from typing import Tuple, Optional, Dict
from LineaX_Classes import InputData


class DataTransformer:
    """
    Transforms experimental data based on linearisation requirements.

    Supports transformations for:
    - Exponential equations: y -> ln(y)
    - Power equations: x -> x^n
    - Reciprocal equations: x -> 1/x
    - Logarithmic transformations on either or both axes
    """

    def __init__(self, input_data: InputData):
        """
        Initialize transformer with raw input data.

        Args:
            input_data: InputData instance containing raw measurements
        """
        self.raw_data = input_data
        self.transformed_data = None
        self.transformation_applied = None

    def transform_for_linearisation(
            self,
            x_transform: Optional[str] = None,
            y_transform: Optional[str] = None,
            x_var: str = "x",
            y_var: str = "y"
    ) -> InputData:
        """
        Transform data based on linearisation requirements.

        Args:
            x_transform: Transformation to apply to x-axis (e.g., "x", "x**2", "1/x", "ln(x)")
            y_transform: Transformation to apply to y-axis (e.g., "y", "ln(y)", "y**2")
            x_var: The variable name used in transformations for x
            y_var: The variable name used in transformations for y

        Returns:
            InputData instance with transformed values and updated titles
        """
        # Create new InputData for transformed values
        self.transformed_data = InputData()

        # Transform x values
        x_vals, x_err, x_title = self._transform_axis(
            self.raw_data.x_values,
            self.raw_data.x_error,
            self.raw_data.x_title,
            x_transform,
            x_var
        )

        # Transform y values
        y_vals, y_err, y_title = self._transform_axis(
            self.raw_data.y_values,
            self.raw_data.y_error,
            self.raw_data.y_title,
            y_transform,
            y_var
        )

        # Store transformed data
        self.transformed_data.x_values = x_vals
        self.transformed_data.x_error = x_err
        self.transformed_data.x_title = x_title

        self.transformed_data.y_values = y_vals
        self.transformed_data.y_error = y_err
        self.transformed_data.y_title = y_title

        # Track what transformations were applied
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
        Transform a single axis (x or y) according to the specified transformation.

        Args:
            values: Original data values
            errors: Original error values (can be None)
            original_title: Original axis title
            transform: Transformation string (e.g., "ln(x)", "x**2", "1/x")
            var_name: Variable name to replace in transform string

        Returns:
            Tuple of (transformed_values, transformed_errors, new_title)
        """
        # If no transform specified, return original data
        if transform is None or transform == var_name:
            return values, errors, original_title

        # Parse the transformation
        transform_lower = transform.lower().replace(" ", "")

        # Apply transformation based on type
        if "ln(" in transform_lower or "log(" in transform_lower:
            # Logarithmic transformation
            new_values, new_errors = self._apply_log_transform(values, errors)
            new_title = f"ln({original_title})"

        elif "exp(" in transform_lower:
            # Exponential transformation
            new_values, new_errors = self._apply_exp_transform(values, errors)
            new_title = f"exp({original_title})"

        elif "**" in transform_lower or "^" in transform_lower:
            # Power transformation (e.g., x**2, x^3)
            power = self._extract_power(transform_lower)
            new_values, new_errors = self._apply_power_transform(values, errors, power)
            new_title = f"{original_title}^{power}"

        elif "/" in transform_lower and transform_lower.startswith("1/"):
            # Reciprocal transformation
            new_values, new_errors = self._apply_reciprocal_transform(values, errors)
            new_title = f"1/{original_title}"

        elif "sqrt(" in transform_lower:
            # Square root transformation
            new_values, new_errors = self._apply_sqrt_transform(values, errors)
            new_title = f"√{original_title}"

        else:
            # No recognized transformation, return original
            new_values = values
            new_errors = errors
            new_title = original_title

        return new_values, new_errors, new_title

    def _apply_log_transform(
            self,
            values: np.ndarray,
            errors: Optional[np.ndarray]
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Apply natural logarithm transformation."""
        # Check for non-positive values
        if np.any(values <= 0):
            raise ValueError("Cannot take logarithm of non-positive values")

        new_values = np.log(values)

        # Error propagation for ln(x): Δ(ln(x)) = Δx / x
        if errors is not None:
            new_errors = errors / values
        else:
            new_errors = None

        return new_values, new_errors

    def _apply_exp_transform(
            self,
            values: np.ndarray,
            errors: Optional[np.ndarray]
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Apply exponential transformation."""
        new_values = np.exp(values)

        # Error propagation for exp(x): Δ(exp(x)) = exp(x) * Δx
        if errors is not None:
            new_errors = new_values * errors
        else:
            new_errors = None

        return new_values, new_errors

    def _apply_power_transform(
            self,
            values: np.ndarray,
            errors: Optional[np.ndarray],
            power: float
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Apply power transformation (x^n)."""
        new_values = np.power(values, power)

        # Error propagation for x^n: Δ(x^n) = n * x^(n-1) * Δx
        if errors is not None:
            new_errors = np.abs(power * np.power(values, power - 1) * errors)
        else:
            new_errors = None

        return new_values, new_errors

    def _apply_reciprocal_transform(
            self,
            values: np.ndarray,
            errors: Optional[np.ndarray]
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Apply reciprocal transformation (1/x)."""
        # Check for zero values
        if np.any(values == 0):
            raise ValueError("Cannot take reciprocal of zero")

        new_values = 1.0 / values

        # Error propagation for 1/x: Δ(1/x) = Δx / x^2
        if errors is not None:
            new_errors = errors / (values ** 2)
        else:
            new_errors = None

        return new_values, new_errors

    def _apply_sqrt_transform(
            self,
            values: np.ndarray,
            errors: Optional[np.ndarray]
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Apply square root transformation."""
        # Check for negative values
        if np.any(values < 0):
            raise ValueError("Cannot take square root of negative values")

        new_values = np.sqrt(values)

        # Error propagation for √x: Δ(√x) = Δx / (2√x)
        if errors is not None:
            new_errors = errors / (2 * new_values)
        else:
            new_errors = None

        return new_values, new_errors

    def _extract_power(self, transform_str: str) -> float:
        """Extract the power value from a power transformation string."""
        # Handle both ** and ^ notation
        if "**" in transform_str:
            parts = transform_str.split("**")
        elif "^" in transform_str:
            parts = transform_str.split("^")
        else:
            return 1.0

        try:
            # Get the number after ** or ^
            power_str = parts[1].strip()
            # Handle parentheses
            power_str = power_str.replace("(", "").replace(")", "")
            return float(power_str)
        except (IndexError, ValueError):
            return 1.0

    def get_transformation_info(self) -> Dict[str, str]:
        """
        Get information about applied transformations.

        Returns:
            Dictionary containing transformation details
        """
        if self.transformation_applied is None:
            return {
                "status": "No transformation applied",
                "x_transform": "x",
                "y_transform": "y"
            }

        return {
            "status": "Transformation applied",
            "x_transform": self.transformation_applied["x_transform"],
            "y_transform": self.transformation_applied["y_transform"],
            "x_title": self.transformation_applied["x_title"],
            "y_title": self.transformation_applied["y_title"]
        }

    def revert_to_raw(self) -> InputData:
        """
        Return the original raw data without transformations.

        Returns:
            InputData instance with raw measurements
        """
        return self.raw_data


def identify_required_transformations(linearised_eq: sp.Eq, x_var: str, y_var: str) -> Tuple[str, str]:
    """
    Identify what transformations are needed for x and y axes from a linearised equation.

    Args:
        linearised_eq: The linearised SymPy equation
        x_var: The x variable name
        y_var: The y variable name

    Returns:
        Tuple of (x_transform, y_transform) as strings
    """
    lhs = linearised_eq.lhs
    rhs = linearised_eq.rhs

    # Determine y-axis transformation
    y_transform = y_var
    if isinstance(lhs, sp.log):
        y_transform = f"ln({y_var})"
    elif isinstance(lhs, sp.Pow):
        power = lhs.args[1]
        y_transform = f"{y_var}**{power}"

    # Determine x-axis transformation by examining RHS
    x_transform = x_var

    # Look for x in various forms in the RHS
    x_sym = sp.Symbol(x_var)

    # Check if x appears as x^n
    for term in sp.preorder_traversal(rhs):
        if isinstance(term, sp.Pow) and term.args[0] == x_sym:
            power = term.args[1]
            x_transform = f"{x_var}**{power}"
            break
        elif isinstance(term, sp.Mul):
            # Check for 1/x (appears as x**-1)
            for factor in term.args:
                if isinstance(factor, sp.Pow) and factor.args[0] == x_sym:
                    power = factor.args[1]
                    if power == -1:
                        x_transform = f"1/{x_var}"
                    else:
                        x_transform = f"{x_var}**{power}"
                    break

    return x_transform, y_transform