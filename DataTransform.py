"""DataTransform.py — Transformation of raw experimental data for linearisation (Algorithm 2).

DataTransformer applies axis transformations to an InputData instance and propagates
measurement uncertainties through each transform using standard error propagation rules
(Algorithm 6, Section 3.2.2). The resulting transformed InputData is stored in
ScreenManager by AnalysisMethodScreen and passed to LinearGraphResultsScreen.

Error propagation formulas implemented here:
  ln(x)  : Δln(x)     = Δx / x
  exp(x) : Δexp(x)    = exp(x) · Δx
  x^n    : Δ(x^n)     = n · x^(n−1) · Δx
  1/x    : Δ(1/x)     = Δx / x²
  √x     : Δ√x        = Δx / (2√x)
"""

# numpy provides vectorised array operations used for all numerical transforms.
# np.log, np.exp, np.power, np.sqrt operate element-wise on entire arrays,
# avoiding explicit Python loops and matching the error propagation formulas above.
import numpy as np

# sympy is a symbolic mathematics library; used here only in identify_required_transformations
# to inspect SymPy expression structure (sp.log, sp.Pow, sp.Mul) and extract transform labels.
import sympy as sp

# Tuple and Optional support type hints for multi-value returns and nullable parameters.
from typing import Tuple, Optional, Dict

# InputData is the data container populated by Screen 1 and transformed here.
from LineaX_Classes import InputData


class DataTransformer:
    """Transforms experimental data based on linearisation requirements (Algorithm 2 / 6).

    Wraps a raw InputData instance and produces a new transformed InputData via
    transform_for_linearisation(). Each axis is routed through _transform_axis,
    which dispatches to the appropriate helper (_apply_log_transform etc.) based
    on the transform label string produced by AnalysisMethodScreen._identify_transforms.
    """

    def __init__(self, input_data: InputData):
        # raw_data is the original dataset; stored so revert_to_raw() can recover it.
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
        """Apply axis transformations and return a linearised InputData instance.

        Delegates each axis to _transform_axis, then assembles a new InputData with
        the transformed values, propagated errors and updated axis titles.
        Called by AnalysisMethodScreen._linearise_equation after Algorithm 2 determines
        the required transforms. The result is deposited into ScreenManager for
        LinearGraphResultsScreen (Section 3.2.1, Data Flow).
        """
        self.transformed_data = InputData()

        x_vals, x_err, x_title = self._transform_axis(
            self.raw_data.x_values, self.raw_data.x_error,
            self.raw_data.x_title, x_transform, x_var
        )
        y_vals, y_err, y_title = self._transform_axis(
            self.raw_data.y_values, self.raw_data.y_error,
            self.raw_data.y_title, y_transform, y_var
        )

        self.transformed_data.x_values = x_vals
        self.transformed_data.x_error  = x_err
        self.transformed_data.x_title  = x_title
        self.transformed_data.y_values = y_vals
        self.transformed_data.y_error  = y_err
        self.transformed_data.y_title  = y_title

        # Record what was applied so get_transformation_info() can report it.
        self.transformation_applied = {
            "x_transform": x_transform or "x",
            "y_transform": y_transform or "y",
            "x_title": x_title,
            "y_title": y_title,
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
        """Route a single axis to the appropriate transform helper (Algorithm 6, Section 3.2.2).

        The transform label string (produced by _identify_transforms in AnalysisMethod.py)
        is lowercased and stripped, then matched against known patterns:
          'ln(' or 'log(' → logarithmic transform
          'exp('          → exponential transform
          'sqrt('         → square root transform
          '1/'            → reciprocal transform
          '**' or '^'     → power transform (exponent extracted by _extract_power)
        Returns the transformed values, propagated errors and the new axis title.
        """
        if transform is None or transform == var_name:
            return values, errors, original_title

        t = transform.lower().replace(" ", "")

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

        return values, errors, original_title

    def _apply_log_transform(self, values, errors):
        """Apply natural logarithm and propagate error: Δln(x) = Δx / x (Algorithm 6).

        np.log computes the natural logarithm element-wise.
        Raises ValueError if any value is non-positive, since ln(x) is undefined for x ≤ 0.
        """
        if np.any(values <= 0):
            raise ValueError("Cannot take logarithm of non-positive values")
        new_vals = np.log(values)
        # Error propagation: derivative of ln(x) is 1/x.
        return new_vals, (errors / values if errors is not None else None)

    def _apply_exp_transform(self, values, errors):
        """Apply exponential and propagate error: Δexp(x) = exp(x) · Δx (Algorithm 6).

        np.exp computes e^x element-wise. The derivative of exp(x) is exp(x) itself,
        so the propagated error is the product of the transform result and the input error.
        """
        new_vals = np.exp(values)
        return new_vals, (new_vals * errors if errors is not None else None)

    def _apply_power_transform(self, values, errors, power: float):
        """Apply x^n and propagate error: Δ(x^n) = n · x^(n−1) · Δx (Algorithm 6).

        np.power(values, power) raises each element to the given power.
        np.abs ensures the propagated error is always non-negative regardless of sign.
        """
        new_vals = np.power(values, power)
        new_errs = np.abs(power * np.power(values, power - 1) * errors) if errors is not None else None
        return new_vals, new_errs

    def _apply_reciprocal_transform(self, values, errors):
        """Apply 1/x and propagate error: Δ(1/x) = Δx / x² (Algorithm 6).

        Raises ValueError if any value is zero to prevent division by zero.
        """
        if np.any(values == 0):
            raise ValueError("Cannot take reciprocal of zero")
        new_vals = 1.0 / values
        # Error propagation: derivative of 1/x is -1/x²; magnitude used for error.
        return new_vals, (errors / (values ** 2) if errors is not None else None)

    def _apply_sqrt_transform(self, values, errors):
        """Apply √x and propagate error: Δ√x = Δx / (2√x) (Algorithm 6).

        np.sqrt computes the element-wise square root.
        Raises ValueError for negative inputs since real square roots are undefined there.
        """
        if np.any(values < 0):
            raise ValueError("Cannot take square root of negative values")
        new_vals = np.sqrt(values)
        # Error propagation: derivative of √x is 1/(2√x).
        return new_vals, (errors / (2 * new_vals) if errors is not None else None)

    def _extract_power(self, transform_str: str) -> float:
        """Extract the numeric exponent from a power transform string.

        Supports both '**' (Python notation, e.g. 'x**2') and '^' (caret notation).
        str.split splits on the separator; the second element is the exponent string.
        strip('()') removes any enclosing parentheses before float conversion.
        Returns 1.0 as a safe fallback if parsing fails.
        """
        sep = "**" if "**" in transform_str else "^"
        try:
            return float(transform_str.split(sep)[1].strip("()"))
        except (IndexError, ValueError):
            return 1.0

    def get_transformation_info(self) -> Dict[str, str]:
        """Return a summary dict of applied transformations.

        Used by GradientAnalysisScreen to populate the 'Selected Equation' section
        with the transformation labels (x_title, y_title).
        """
        if self.transformation_applied is None:
            return {"status": "No transformation applied", "x_transform": "x", "y_transform": "y"}
        return {"status": "Transformation applied", **self.transformation_applied}

    def revert_to_raw(self) -> InputData:
        """Return the original untransformed InputData.

        Called by AnalysisMethodScreen.revert_to_raw_data() to restore the dataset
        for re-analysis with a different equation (Section 3.2.1, Branch 4).
        """
        return self.raw_data


def identify_required_transformations(linearised_eq: sp.Eq, x_var: str, y_var: str) -> Tuple[str, str]:
    """Identify axis transformations needed from a linearised SymPy equation.

    Inspects the LHS of linearised_eq for y-axis transforms:
      sp.log instance → 'ln(y_var)'
      sp.Pow instance → 'y_var**n'
    Inspects the RHS (via sp.preorder_traversal) for x-axis transforms:
      sp.Pow with base x_sym and exponent -1 → '1/x_var'
      sp.Pow with other exponent             → 'x_var**n'

    sp.preorder_traversal walks the expression tree depth-first, visiting every
    sub-expression so nested powers inside products (sp.Mul) are also detected.
    """
    lhs, rhs = linearised_eq.lhs, linearised_eq.rhs
    x_sym = sp.Symbol(x_var)

    # Detect y-axis transform from LHS structure.
    if isinstance(lhs, sp.log):
        y_transform = f"ln({y_var})"
    elif isinstance(lhs, sp.Pow):
        y_transform = f"{y_var}**{lhs.args[1]}"
    else:
        y_transform = y_var

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

