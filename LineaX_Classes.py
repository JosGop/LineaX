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

    def validate_input(self) -> bool:
        pass

    def read_csv_file(self, filepath, x_col: int, y_col: int, x_err_col: None, y_err_col: None):
        pass

    def read_excel(self, filepath, x: int, y: int, x_err_col: None, y_err_col: None):
        pass

    # def load_from_dataframe(
    #     self,
    #     df,
    #     x_col: str,
    #     y_col: str,
    #     x_err_col: Optional[str] = None,
    #     y_err_col: Optional[str] = None
    # ):
    #     self.x_values = df[x_col].astype(float).tolist()
    #     self.y_values = df[y_col].astype(float).tolist()
    #
    #     self.x_error = (
    #         df[x_err_col].astype(float).tolist()
    #         if x_err_col and x_err_col != "None"
    #         else None
    #     )
    #
    #     self.y_error = (
    #         df[y_err_col].astype(float).tolist()
    #         if y_err_col and y_err_col != "None"
    #         else None
    #     )
    #
    #     return self.validate_input()


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