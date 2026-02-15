from abc import ABC, abstractmethod
import csv
from decimal import Decimal
import numpy as np
from typing import List, Optional, Dict
import pandas as pd
from typing import List, Optional


def resolution(num):
    d = Decimal(str(num))
    return Decimal(f'1e{d.as_tuple().exponent}')


def find_error(inputs: list, axis_err=None):
    axis = np.array(inputs)
    if axis_err is not None:
        error = np.array(axis_err)
    else:
        res = []
        for i in axis:
            res.append(resolution(i))
        error = np.full_like(axis, min(res), dtype='float')
    return error


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
        self.x_values = x_values or []
        self.y_values = y_values or []
        self.x_error = x_error
        self.y_error = y_error
        self.x_title = x_title
        self.y_title = y_title


    def read_excel(self, filepath, x: int, y: int, x_err_col: None, y_err_col: None):
        # read the Excel file into a DataFrame
        df = pd.read_excel(filepath)

        # extract values from the chosen x column (1-based index)
        # convert each value to int if it is already an int, otherwise to float
        x_data = [int(val) if isinstance(val, int) else float(val) for val in df.iloc[:, x - 1]]

        # extract values from the chosen y column (1-based index)
        # same conversion logic as for x values
        y_data = [int(val) if isinstance(val, int) else float(val) for val in df.iloc[:, y - 1]]

        # get the column titles (names of x and y columns)
        x_title, y_title = df.columns

        self.x_values = x_data
        self.y_values = y_data
        self.x_error = find_error(x_data, x_err_col)
        self.y_error = find_error(y_data, y_err_col)
        self.x_title = x_title
        self.y_title = y_title

    def read_csv_file(self, filepath, x_col: int, y_col: int, x_err_col: None, y_err_col: None):
        # create empty lists to store x and y values
        x_data = []
        y_data = []

        # open the CSV file in read mode
        # newline='' prevents issues with line breaks across operating systems
        with open(filepath, newline='') as file:
            reader = csv.reader(file)  # turn the file into a CSV reader object

            # read header row to get column titles
            header = next(reader, None)
            x_title = header[x_col - 1]  # title of x column
            y_title = header[y_col - 1]  # title of y column

            # go through each row in the file
            for row in reader:
                # take the value from the chosen x column, convert to float, add to list
                x_data.append(float(row[x_col - 1]))
                # take the value from the chosen y column, convert to float, add to list
                y_data.append(float(row[y_col - 1]))

            self.x_values = x_data
            self.y_values = y_data
            self.x_error = find_error(x_data, x_err_col)
            self.y_error = find_error(y_data, y_err_col)
            self.x_title = x_title
            self.y_title = y_title

    def get_manual_data(
            self,
            x_vals,
            y_vals,
            x_err_vals=None,
            y_err_vals=None,
            x_title=None,
            y_title=None
    ):
        """
        Populate InputData from manual spreadsheet-style entry.
        Values are converted to floats and stored as numpy arrays.
        Error values are generated from resolution if not provided.
        """

        x_data = [float(v) for v in x_vals]
        y_data = [float(v) for v in y_vals]

        self.x_values = np.array(x_data, dtype=float)
        self.y_values = np.array(y_data, dtype=float)

        self.x_error = find_error(x_data, x_err_vals)
        self.y_error = find_error(y_data, y_err_vals)

        self.x_title = x_title or "X"
        self.y_title = y_title or "Y"


# Abstract base class for all graphs
class Graph(ABC):
    def __init__(self, title: str, x_axis_name: str, y_axis_name: str, equation: Optional[str] = None):
        self.title = title
        self.x_axis_name = x_axis_name
        self.y_axis_name = y_axis_name
        self.equation = equation

    @abstractmethod
    def calculate_coeffs(self):
        pass

# Non-linear graph inherits from abstract Graph
class NonLinearGraph(Graph):
    def __init__(self, title: str, x_axis_name: str, y_axis_name: str, equation: Optional[str] = None):
        super().__init__(title, x_axis_name, y_axis_name, equation)
        self.best_fit_model = None
        self.r2_values: Dict[str, float] = {}

    def calculate_coeffs(self):
        pass



class ScientificEquation(object):
    def __init__(self, original_equation: str):
        self.original_equation = original_equation

        # Filled after linearisation
        self.linearised_equation = None

        # Axis symbols
        self.y = None
        self.x = None

        # Linear constants
        self.m = None
        self.c = None

        # Optional explanations
        self.m_meaning = None
        self.c_meaning = None


    def linearise(self):
        pass

# Linear graph inherits from abstract Graph
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