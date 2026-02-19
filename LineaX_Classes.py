"""
LineaX_Classes.py

Core data structures and abstract base classes for the LineaX application.
Defined in Section 3.3 Development (Stage 1) as the foundational layer that
all downstream modules — regression, uncertainty analysis, and plotting — depend on.
These classes implement the data abstraction described in Section 3.2.2 (Structure
of the Solution) and the key variables table in Section 3.2.2 (Key Variables,
Data Structures, and Validation).
"""

from abc import ABC, abstractmethod
import csv
from decimal import Decimal
import numpy as np
from typing import List, Optional, Dict
import pandas as pd


def resolution(num) -> Decimal:
    """
    Return the resolution (smallest measurable unit) of a number from its decimal representation.

    Implements Algorithm 3 from Section 3.2.2: the first step in automated error
    estimation, which identifies the minimum resolution present in a dataset.
    Resolution corresponds to the physical precision of the measuring instrument —
    e.g., a ruler marked to 1 mm has resolution 0.001 m. Used by find_error()
    to derive uncertainty when the user provides none.
    """
    d = Decimal(str(num))
    return Decimal(f'1e{d.as_tuple().exponent}')


def find_error(inputs: list, axis_err=None) -> np.ndarray:
    """
    Return axis_err as a numpy array, or derive uniform error from the minimum resolution of inputs.

    Implements Algorithm 4 from Section 3.2.2: determines the appropriate uncertainty
    values for each data point, using user-supplied errors if available, otherwise
    applying resolution-based estimation via resolution(). Described in Section 3.2.1
    (Sub-component: Automated Error Value Generation) — this function activates when
    the uncertainty column is left blank. Ensures every data point has a valid
    uncertainty value before worst-fit line calculations can proceed.
    """
    if axis_err is not None:
        return np.array(axis_err)
    min_res = float(min(resolution(v) for v in inputs))  # smallest increment across all values
    return np.full(len(inputs), min_res)  # uniform resolution-based uncertainty applied to all points


class InputData:
    """
    Central container for all experimental values entered by the user.

    Defined in Section 3.3 Development (Stage 1) as the primary data abstraction
    layer. Ensures that downstream components (regression, uncertainty analysis,
    plotting) interact with a consistent, validated structure regardless of whether
    data originates from manual entry or file import. Corresponds to the variables
    x_values, y_values, x_error, y_error, x_title, y_title in the Key Variables
    table (Section 3.2.2).
    """

    def __init__(
        self,
        x_values: Optional[List[float]] = None,
        y_values: Optional[List[float]] = None,
        x_error: Optional[List[float]] = None,
        y_error: Optional[List[float]] = None,
        x_title: Optional[str] = None,
        y_title: Optional[str] = None,
    ):
        # Convert lists to numpy arrays immediately; use empty arrays as safe defaults
        self.x_values = np.array(x_values, dtype=float) if x_values is not None else np.array([], dtype=float)
        self.y_values = np.array(y_values, dtype=float) if y_values is not None else np.array([], dtype=float)
        self.x_error = np.array(x_error, dtype=float) if x_error is not None else None
        self.y_error = np.array(y_error, dtype=float) if y_error is not None else None
        self.x_title = x_title  # column header used as axis label in graph output
        self.y_title = y_title  # column header used as axis label in graph output

    def _populate(self, x_data, y_data, x_title, y_title, x_err=None, y_err=None):
        """
        Shared helper: convert list data to numpy arrays and compute errors.

        Called by read_excel(), read_csv_file(), and get_manual_data() to centralise
        array conversion and uncertainty derivation in one place. Calls find_error()
        (Algorithm 4) to assign or compute uncertainties, satisfying the requirement
        in Section 3.2.1 that every dataset has uncertainty information before analysis.
        """
        self.x_values = np.array(x_data, dtype=float)
        self.y_values = np.array(y_data, dtype=float)
        self.x_error = find_error(x_data, x_err)  # derive or wrap x uncertainties
        self.y_error = find_error(y_data, y_err)  # derive or wrap y uncertainties
        self.x_title = x_title
        self.y_title = y_title

    def read_excel(self, filepath, x: int, y: int, x_err_col=None, y_err_col=None):
        """
        Populate InputData from an Excel file.

        Supports the 'Import CSV/Excel' branch of Section 3.2.1 (Branch 1).
        Column indices are 1-based to match the user-facing column mapping interface
        described in Section 3.2.1 (Sub-component: User to allocate columns for values
        and/or errors). Preserves integer types where present to maintain resolution
        accuracy for Algorithm 3.
        """
        df = pd.read_excel(filepath)
        # Preserve int if already int, otherwise convert to float
        to_num = lambda col: [int(v) if isinstance(v, int) else float(v) for v in df.iloc[:, col - 1]]
        self._populate(to_num(x), to_num(y), df.columns[x - 1], df.columns[y - 1], x_err_col, y_err_col)

    def read_csv_file(self, filepath, x_col: int, y_col: int, x_err_col=None, y_err_col=None):
        """
        Populate InputData from a CSV file.

        Supports the 'Import CSV/Excel' branch of Section 3.2.1 (Branch 1). Column
        headers are extracted from the first row and stored as axis titles, satisfying
        the requirement that axis labels reflect the imported data source (Section 3.2.2,
        User Interface). Column indices are 1-based to match the mapping UI.
        """
        x_data, y_data = [], []
        with open(filepath, newline='') as file:
            reader = csv.reader(file)
            header = next(reader, None)  # extract column names for axis labelling
            x_title, y_title = header[x_col - 1], header[y_col - 1]
            for row in reader:
                x_data.append(float(row[x_col - 1]))
                y_data.append(float(row[y_col - 1]))
        self._populate(x_data, y_data, x_title, y_title, x_err_col, y_err_col)

    def get_manual_data(self, x_vals, y_vals, x_err_vals=None, y_err_vals=None, x_title=None, y_title=None):
        """
        Populate InputData from manual spreadsheet-style entry.

        Supports the 'Manual Entry' branch of Section 3.2.1 (Branch 2) and the
        Data Input Screen described in Section 3.3 (Stage 2). Values are converted
        to floats and stored as numpy arrays. Calls find_error() (Algorithm 4) to
        generate resolution-based uncertainty if no explicit errors are provided,
        as required by the Automated Error Value Generation sub-component.
        """
        self._populate(
            [float(v) for v in x_vals], [float(v) for v in y_vals],
            x_title or "X", y_title or "Y", x_err_vals, y_err_vals
        )


class Graph(ABC):
    """
    Abstract base class for all graph types in LineaX.

    Part of the OOP architecture described in Section 3.3 Development (Stage 1).
    Enforces a common interface across LinearGraph and NonLinearGraph, supporting
    the 'Graphs' branch (Branch 4) of the decomposition in Section 3.2.1. The
    abstract calculate_coeffs() method ensures every concrete graph type implements
    its own regression logic, as required by the automated and scientific equation
    pathways in Section 3.2.1 (Branch 3).
    """
    def __init__(self, title: str, x_axis_name: str, y_axis_name: str, equation: Optional[str] = None):
        self.title = title          # displayed as chart title on the graph output screen
        self.x_axis_name = x_axis_name  # axis label, updated after transformation (e.g., "ln(Force)")
        self.y_axis_name = y_axis_name  # axis label, updated after transformation
        self.equation = equation    # optional equation string associated with this graph

    @abstractmethod
    def calculate_coeffs(self):
        """Subclasses must implement regression coefficient calculation."""
        pass


class NonLinearGraph(Graph):
    """
    Represents a graph fitted by the automated model selection pathway.

    Supports the 'Automated' sub-component of Section 3.2.1 (Branch 3) and
    Algorithm 8 from Section 3.2.2, which fits multiple models and evaluates
    accuracy using R². Stores R² values for all tested models in r2_values, which
    is displayed in the Model Selection panel described in Section 3.2.2 (User Interface
    — Screen 3b: Automated Graph Output).
    """
    def __init__(self, title: str, x_axis_name: str, y_axis_name: str, equation: Optional[str] = None):
        super().__init__(title, x_axis_name, y_axis_name, equation)
        self.best_fit_model = None   # name of the highest-R² model (e.g., "quadratic")
        self.r2_values: Dict[str, float] = {}  # stores R² for every tested model

    def calculate_coeffs(self):
        """Placeholder; automated model fitting is implemented in AutomatedGraphDisplay.py."""
        pass


class ScientificEquation:
    """
    Represents a scientific equation and its linearised form.

    Defined in Section 3.3 Development (Stage 1) and described in Section 3.2.2
    (Structure of the Solution). Stores both the original equation and the y = mx + c
    linearised form, including the physical meanings of m and c. Used by the
    'Scientific Equation Selection' and 'Linearise to y = mx + c' sub-components
    of Section 3.2.1 (Branch 3). The linearise() stub corresponds to Algorithm 2
    from Section 3.2.2.
    """
    def __init__(self, original_equation: str):
        self.original_equation = original_equation  # e.g., "F = kx" as entered or selected
        # All fields below are populated after linearise() is called
        self.linearised_equation = None  # SymPy Eq object in y = mx + c form
        self.y = self.x = self.m = self.c = None  # symbolic axis and coefficient variables
        self.m_meaning = self.c_meaning = None    # physical meanings, e.g., "spring constant k"

    def linearise(self):
        """
        Transform the original equation into y = mx + c form.

        Implements Algorithm 2 from Section 3.2.2: applies symbolic transformation
        (SymPy) to non-linear equations. Full implementation is in Equations.py and
        DataTransform.py. Discussed extensively in Section 3.3 (Linearising Equations
        and its failures/improvements).
        """
        pass


class LinearGraph(Graph):
    """
    Represents a graph analysed via the scientific equation (linear) pathway.

    Supports the 'Linear' sub-component of Section 3.2.1 (Branch 3). Stores
    best-fit and worst-fit gradient values (Algorithms 4 and 5 from Section 3.2.2),
    y-intercept, and gradient uncertainty. These attributes correspond directly to
    the key variables m_best, c_best, m_steep, m_shallow, and gradient_uncertainty
    defined in the Key Variables table (Section 3.2.2).
    """
    def __init__(self, title: str, x_axis_name: str, y_axis_name: str, equation: Optional[str] = None):
        super().__init__(title, x_axis_name, y_axis_name, equation)
        self.scientific_equation: Optional[ScientificEquation] = None  # linked equation object
        self.best_fit_gradient: Optional[float] = None          # gradient m from linear regression
        self.y_intercept: Optional[float] = None                # intercept c from linear regression
        self.worst_fit_gradient_max: Optional[float] = None     # steepest line through error bars
        self.worst_fit_gradient_min: Optional[float] = None     # shallowest line through error bars
        self.uncertainty: Optional[float] = None                # (m_steep - m_shallow) / 2

    def calculate_coeffs(self):
        """
        Calculate best-fit gradient and y-intercept via linear regression.

        Implements Algorithm 1 computation from Section 3.2.2 (gradient and intercept
        calculation). Full implementation is in LinearGraphDisplay.py. Validates that
        results are finite before storing, as required by the key variables table.
        """
        pass

    def calculate_worst_fit_grad(self):
        """
        Calculate the steepest and shallowest lines through error bars.

        Implements Algorithm 5 from Section 3.2.2: determines worst-fit gradients
        that can reasonably pass through the data given measurement uncertainties.
        Required by the OCR A-Level Physics specification for uncertainty analysis
        in graphical work, as noted in Section 3.2.2.
        """
        pass

    def calculate_uncertainty(self):
        """
        Compute gradient uncertainty as (m_steep - m_shallow) / 2.

        Finalises Algorithm 5 output from Section 3.2.2. The result is stored as
        gradient_uncertainty and displayed on Screen 4 (Gradient Analysis & Results)
        described in Section 3.2.2 (User Interface).
        """
        pass