"""LineaX_Classes.py — Core data structures and abstract base classes for LineaX.

Defines the data model used throughout the application:
  InputData       — holds experimental x/y values and their uncertainties
  Graph hierarchy — abstract Graph, LinearGraph (Screen 3a path), NonLinearGraph (Screen 3b path)
  ScientificEquation — stores a linearised equation and its physical interpretation

Algorithm 3 (resolution, Section 3.2.2) and Algorithm 4 (error derivation, Section 3.2.2)
are implemented as module-level functions and called by InputData._populate.
"""

# ABC and abstractmethod from the standard library enforce the interface contract:
# any concrete Graph subclass must implement calculate_coeffs().
from abc import ABC, abstractmethod

# csv is the standard library CSV reader used by InputData.read_csv_file.
import csv

# Decimal provides arbitrary-precision decimal arithmetic; used in Algorithm 3
# to inspect the number of decimal places in a float without floating-point rounding errors.
from decimal import Decimal

# numpy is the numerical computing library used for array operations, polynomial
# fitting and error propagation throughout LineaX.
import numpy as np

# Optional, List, Dict provide type hints for IDE support and code clarity.
from typing import List, Optional, Dict

# pandas is the data analysis library used to read Excel and CSV files into
# DataFrame objects before extraction into InputData.
import pandas as pd


def resolution(num) -> Decimal:
    """Return the measurement resolution of a number (Algorithm 3, Section 3.2.2).

    Converts num to a Decimal string to avoid floating-point representation errors,
    then reads the exponent from the Decimal tuple. For example, 0.01 returns
    Decimal('1e-2'), giving the smallest increment the instrument can resolve.

    Decimal.as_tuple() returns a DecimalTuple(sign, digits, exponent); the exponent
    field is a negative integer for fractional values (e.g. -2 for hundredths).
    """
    d = Decimal(str(num))
    return Decimal(f'1e{d.as_tuple().exponent}')


def find_error(inputs: list, axis_err=None) -> np.ndarray:
    """Return uncertainties for an axis, either from supplied values or from minimum resolution.

    Implements Algorithm 4 (Section 3.2.2): if no explicit error column is provided,
    the uncertainty for every data point is set to the smallest resolution found across
    all values in the column (i.e. the least precise measurement dictates the error).

    np.array converts a plain list to a numpy array for vectorised downstream arithmetic.
    np.full creates an array of a given length filled with a constant value.
    """
    if axis_err is not None:
        return np.array(axis_err)

    # min() over a generator applies resolution() to every value and returns the smallest.
    min_res = float(min(resolution(v) for v in inputs))
    return np.full(len(inputs), min_res)


class InputData:
    """Container for experimental values: x/y data, errors and axis titles.

    All numeric fields are stored as numpy float64 arrays so that vectorised
    operations (e.g. error propagation in DataTransform.py) can be applied
    without explicit loops. Satisfies success criterion 1.3.1 (the application
    must store and propagate measurement uncertainties from input to output).
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
        # np.array with dtype=float converts None or empty lists to zero-length float arrays.
        self.x_values = np.array(x_values, dtype=float) if x_values is not None else np.array([], dtype=float)
        self.y_values = np.array(y_values, dtype=float) if y_values is not None else np.array([], dtype=float)
        self.x_error  = np.array(x_error,  dtype=float) if x_error  is not None else None
        self.y_error  = np.array(y_error,  dtype=float) if y_error  is not None else None
        self.x_title  = x_title
        self.y_title  = y_title

    def _populate(self, x_data, y_data, x_title, y_title, x_err=None, y_err=None):
        """Convert list data to numpy arrays and compute errors via Algorithm 4.

        Called by read_excel, read_csv_file and get_manual_data after data is extracted.
        find_error (Algorithm 4) is called with the raw list so that resolution() can
        inspect the original decimal precision before floating-point conversion.
        """
        self.x_values = np.array(x_data, dtype=float)
        self.y_values = np.array(y_data, dtype=float)
        self.x_error  = find_error(x_data, x_err)
        self.y_error  = find_error(y_data, y_err)
        self.x_title  = x_title
        self.y_title  = y_title

    def read_excel(self, filepath, x: int, y: int, x_err_col=None, y_err_col=None):
        """Populate InputData from an Excel file using 1-based column indices.

        pd.read_excel uses the openpyxl library to parse .xlsx/.xls files into a
        DataFrame. df.iloc[:, col - 1] selects a column by zero-based integer position.
        Column headers become x_title and y_title for graph axis labelling.
        Satisfies success criterion 1.1.2 (the application must accept Excel input).
        """
        df = pd.read_excel(filepath)
        # Lambda converts each cell to int if it is already an integer, otherwise float,
        # preserving the original precision for Algorithm 3.
        to_num = lambda col: [int(v) if isinstance(v, int) else float(v) for v in df.iloc[:, col - 1]]
        self._populate(to_num(x), to_num(y), df.columns[x - 1], df.columns[y - 1], x_err_col, y_err_col)

    def read_csv_file(self, filepath, x_col: int, y_col: int, x_err_col=None, y_err_col=None):
        """Populate InputData from a CSV file using 1-based column indices.

        csv.reader from the standard library parses comma-separated text; next(reader)
        reads the header row to extract axis titles. Each subsequent row is parsed
        to float for x and y values. Satisfies success criterion 1.1.2.
        """
        x_data, y_data = [], []
        with open(filepath, newline='') as file:
            reader = csv.reader(file)
            header = next(reader, None)
            x_title, y_title = header[x_col - 1], header[y_col - 1]
            for row in reader:
                x_data.append(float(row[x_col - 1]))
                y_data.append(float(row[y_col - 1]))
        self._populate(x_data, y_data, x_title, y_title, x_err_col, y_err_col)

    def get_manual_data(self, x_vals, y_vals, x_err_vals=None, y_err_vals=None, x_title=None, y_title=None):
        """Populate InputData from values entered manually in Screen 1 (Branch 2).

        Converts string entries from the Tkinter Entry widgets to float before calling
        _populate. Satisfies success criterion 1.1.3 (the application must accept
        manually entered data as well as file imports).
        """
        self._populate(
            [float(v) for v in x_vals], [float(v) for v in y_vals],
            x_title or "X", y_title or "Y", x_err_vals, y_err_vals
        )


class Graph(ABC):
    """Abstract base class for all graph types in LineaX.

    ABC (Abstract Base Class) from the abc module prevents direct instantiation;
    any subclass that does not implement calculate_coeffs() will raise TypeError.
    This enforces a common interface for both analysis pathways (Section 3.2.1).
    """

    def __init__(self, title: str, x_axis_name: str, y_axis_name: str, equation: Optional[str] = None):
        self.title = title
        self.x_axis_name = x_axis_name
        self.y_axis_name = y_axis_name
        self.equation = equation

    @abstractmethod
    def calculate_coeffs(self):
        """Subclasses must implement coefficient calculation for their model type."""
        pass


class NonLinearGraph(Graph):
    """Graph fitted by the automated model selection pathway (Algorithm 8, Section 3.2.2).

    best_fit_model holds the name of the model with the highest R² after curve_fit
    has been applied to all nine candidate models in AutomatedGraphDisplay.py.
    r2_values maps each model name to its R² score for the comparison table.
    """

    def __init__(self, title: str, x_axis_name: str, y_axis_name: str, equation: Optional[str] = None):
        super().__init__(title, x_axis_name, y_axis_name, equation)
        self.best_fit_model = None
        self.r2_values: Dict[str, float] = {}

    def calculate_coeffs(self):
        # Fitting is performed directly by AutomatedGraphResultsScreen; this stub
        # satisfies the ABC contract.
        pass


class ScientificEquation:
    """Represents a scientific equation and its linearised y = mx + c form.

    Populated by AnalysisMethodScreen._linearise_equation (Algorithm 2, Section 3.2.2)
    and passed to GradientAnalysisScreen via ScreenManager.equation_info so that
    Screen 4 can display the physical meaning of the gradient and intercept.
    """

    def __init__(self, original_equation: str):
        self.original_equation = original_equation
        self.linearised_equation = None
        # x and y store the axis transform labels (e.g. 'ln(I)', '1/λ') set by
        # _identify_transforms after linearisation.
        self.y = self.x = self.m = self.c = None
        # m_meaning and c_meaning are human-readable strings such as '-μ' or 'ln(I₀)'
        # derived by _identify_meanings and forwarded to GradientAnalysisScreen.
        self.m_meaning = self.c_meaning = None

    def linearise(self):
        """Transform the original equation into y = mx + c form (Algorithm 2, Section 3.2.2).

        The actual implementation lives in AnalysisMethodScreen.linearise(); this stub
        maintains the class interface.
        """
        pass


class LinearGraph(Graph):
    """Graph analysed via the scientific equation (linear) pathway (Section 3.2.1, Branch 3).

    Stores gradient, intercept and worst-fit data produced by LinearGraphResultsScreen.
    Algorithm 1 (linear regression, Section 3.2.2) populates best_fit_gradient and
    y_intercept; Algorithm 5 (worst-fit lines, Section 3.2.2) populates the gradient bounds.
    """

    def __init__(self, title: str, x_axis_name: str, y_axis_name: str, equation: Optional[str] = None):
        super().__init__(title, x_axis_name, y_axis_name, equation)
        self.scientific_equation: Optional[ScientificEquation] = None
        self.best_fit_gradient: Optional[float] = None
        self.y_intercept: Optional[float] = None
        # worst_fit_gradient_max and _min are the upper/lower gradient bounds
        # calculated by Algorithm 5 using the first and last error bar extremes.
        self.worst_fit_gradient_max: Optional[float] = None
        self.worst_fit_gradient_min: Optional[float] = None
        self.uncertainty: Optional[float] = None

    def calculate_coeffs(self):
        # Regression is performed directly by LinearGraphResultsScreen; stub satisfies ABC.
        pass

    def calculate_worst_fit_grad(self):
        # Worst-fit calculation is performed by LinearGraphResultsScreen (Algorithm 5).
        pass

    def calculate_uncertainty(self):
        # Uncertainty is derived from the np.polyfit covariance matrix in LinearGraphResultsScreen.
        pass


