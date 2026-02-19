from abc import ABC, abstractmethod
import csv
from decimal import Decimal
import numpy as np
from typing import List, Optional, Dict
import pandas as pd


def resolution(num) -> Decimal:
    """Return the resolution (smallest unit) of a number from its decimal representation."""
    d = Decimal(str(num))
    return Decimal(f'1e{d.as_tuple().exponent}')


def find_error(inputs: list, axis_err=None) -> np.ndarray:
    """Return axis_err as an array, or derive uniform error from the minimum resolution of inputs."""
    if axis_err is not None:
        return np.array(axis_err)
    min_res = float(min(resolution(v) for v in inputs))
    return np.full(len(inputs), min_res)


class InputData:
    def __init__(
        self,
        x_values: Optional[List[float]] = None,
        y_values: Optional[List[float]] = None,
        x_error: Optional[List[float]] = None,
        y_error: Optional[List[float]] = None,
        x_title: Optional[str] = None,
        y_title: Optional[str] = None,
    ):
        self.x_values = np.array(x_values, dtype=float) if x_values is not None else np.array([], dtype=float)
        self.y_values = np.array(y_values, dtype=float) if y_values is not None else np.array([], dtype=float)
        self.x_error = np.array(x_error, dtype=float) if x_error is not None else None
        self.y_error = np.array(y_error, dtype=float) if y_error is not None else None
        self.x_title = x_title
        self.y_title = y_title

    def _populate(self, x_data, y_data, x_title, y_title, x_err=None, y_err=None):
        """Shared helper: convert list data to numpy arrays and compute errors."""
        self.x_values = np.array(x_data, dtype=float)
        self.y_values = np.array(y_data, dtype=float)
        self.x_error = find_error(x_data, x_err)
        self.y_error = find_error(y_data, y_err)
        self.x_title = x_title
        self.y_title = y_title

    def read_excel(self, filepath, x: int, y: int, x_err_col=None, y_err_col=None):
        df = pd.read_excel(filepath)
        # Preserve int if already int, otherwise convert to float
        to_num = lambda col: [int(v) if isinstance(v, int) else float(v) for v in df.iloc[:, col - 1]]
        self._populate(to_num(x), to_num(y), df.columns[x - 1], df.columns[y - 1], x_err_col, y_err_col)

    def read_csv_file(self, filepath, x_col: int, y_col: int, x_err_col=None, y_err_col=None):
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
        """
        Populate InputData from manual spreadsheet-style entry.
        Values are converted to floats and stored as numpy arrays.
        Errors are generated from resolution if not provided.
        """
        self._populate(
            [float(v) for v in x_vals], [float(v) for v in y_vals],
            x_title or "X", y_title or "Y", x_err_vals, y_err_vals
        )


class Graph(ABC):
    """Abstract base class for all graph types."""
    def __init__(self, title: str, x_axis_name: str, y_axis_name: str, equation: Optional[str] = None):
        self.title = title
        self.x_axis_name = x_axis_name
        self.y_axis_name = y_axis_name
        self.equation = equation

    @abstractmethod
    def calculate_coeffs(self):
        pass


class NonLinearGraph(Graph):
    def __init__(self, title: str, x_axis_name: str, y_axis_name: str, equation: Optional[str] = None):
        super().__init__(title, x_axis_name, y_axis_name, equation)
        self.best_fit_model = None
        self.r2_values: Dict[str, float] = {}

    def calculate_coeffs(self):
        pass


class ScientificEquation:
    def __init__(self, original_equation: str):
        self.original_equation = original_equation
        # Filled after linearisation
        self.linearised_equation = None
        self.y = self.x = self.m = self.c = None
        self.m_meaning = self.c_meaning = None

    def linearise(self):
        pass


class LinearGraph(Graph):
    def __init__(self, title: str, x_axis_name: str, y_axis_name: str, equation: Optional[str] = None):
        super().__init__(title, x_axis_name, y_axis_name, equation)
        self.scientific_equation: Optional[ScientificEquation] = None
        self.best_fit_gradient: Optional[float] = None
        self.y_intercept: Optional[float] = None
        self.worst_fit_gradient_max: Optional[float] = None
        self.worst_fit_gradient_min: Optional[float] = None
        self.uncertainty: Optional[float] = None

    def calculate_coeffs(self):
        pass

    def calculate_worst_fit_grad(self):
        pass

    def calculate_uncertainty(self):
        pass