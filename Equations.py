from dataclasses import dataclass
from typing import Dict, List, Set
import sympy as sp


@dataclass(frozen=True)
class Equation:
    name: str
    expression: str
    variables: Dict[str, str]


class EquationLibrary:
    def __init__(self):
        self._equations: List[Equation] = []
        self._index: Dict[str, Set[int]] = {}
        self._load_equations()
        self._build_index()

    def _load_equations(self):
        self._equations = [
            Equation(
                name="Ohm's Law",
                expression="V = I R",
                variables={"V": "Potential difference", "I": "Current", "R": "Resistance"}
            ),
            Equation(
                name="Hooke's Law",
                expression="F = k x",
                variables={"F": "Force", "k": "Spring constant", "x": "Extension"}
            ),
            Equation(
                name="Kinetic Energy",
                expression="E = 1/2 m v^2",
                variables={"E": "Energy", "m": "Mass", "v": "Velocity"}
            ),
            Equation(
                name="Ideal Gas Law",
                expression="P V = n R T",
                variables={"P": "Pressure", "V": "Volume", "n": "Amount of substance", "R": "Gas constant", "T": "Temperature"}
            ),
            Equation(
                name="Density",
                expression="ρ = m / V",
                variables={"ρ": "Density", "m": "Mass", "V": "Volume"}
            ),
            Equation(
                name="Wave Speed",
                expression="v = f λ",
                variables={"v": "Wave speed", "f": "Frequency", "λ": "Wavelength"}
            ),
            Equation(
                name= "Magnetic Field",
                expression= "F = B Q v",
                variables= {"F": "Force","B": "Magnetic flux density", "Q": "Charge", "v": "Velocity"}
            ),
        ]

    def _build_index(self):
        for idx, eq in enumerate(self._equations):
            tokens = set()
            tokens.update(eq.name.lower().split())
            tokens.update(eq.expression.replace("=", " ").split())
            for symbol, meaning in eq.variables.items():
                tokens.add(symbol.lower())
                tokens.update(meaning.lower().split())
            for token in tokens:
                self._index.setdefault(token, set()).add(idx)

    def search(self, query: str) -> List[Equation]:
        if not query:
            return []
        query_tokens = query.lower().split()
        matched: Set[int] = set()
        for token in query_tokens:
            if token in self._index:
                matched = self._index[token] if not matched else matched & self._index[token]
        return [self._equations[i] for i in matched]

    x, y = sp.symbols('x y')

    def linearise(equation):

        """
        Linearise common non-linear functions for straight-line graphs.

        Supported transformations:
        - Exponential: y = a*exp(b*x) + c -> ln(y - c) = ln(a) + b*x
        - Reciprocal: y = a/x + c -> remains y = a/x + c (already linear in 1/x)
        - Power/Polynomial: y = a*x^n + c -> remains unchanged (linear in x^n)

        Accepts equations in the form of SymPy Eq objects or expressions (assumes = 0).
        Handles cases where y is not isolated, such as:
        - 2*y = x^2 + 3
        - y^2 = x + c
        - a*y^n = b*x^m + c

        All other forms are kept unchanged as they're already
        linear in the transformed variables.
        """

        # Convert to equation if just an expression is passed
        if not isinstance(equation, sp.Eq):
            expr = equation
            # Try to determine if it's meant to be y = expr or expr = 0
            if y in expr.free_symbols:
                # Check if it's already solved for y
                if expr.is_Add or expr.is_Mul or expr.is_Pow:
                    equation = sp.Eq(y, expr)
                else:
                    equation = sp.Eq(expr, 0)
            else:
                # No y in expression, treat as y = expr
                equation = sp.Eq(y, expr)

        lhs = equation.lhs
        rhs = equation.rhs

        # Determine which side contains y and which contains the main expression
        if y in lhs.free_symbols and y not in rhs.free_symbols:
            y_side = lhs
            expr_side = rhs
        elif y in rhs.free_symbols and y not in lhs.free_symbols:
            # Swap to keep y on left
            y_side = rhs
            expr_side = lhs
        else:
            # Both sides have y or neither side has y, return unchanged
            return equation

        # Check if the expression side (without y) has exponential
        if expr_side.has(sp.exp):
            c, rest = expr_side.as_coeff_Add()
            if rest.has(sp.exp):
                coeff, exp_term = rest.as_coeff_Mul()
                if isinstance(exp_term, sp.exp):
                    b = exp_term.args[0]
                else:
                    b = 1
                # Apply transformation: ln(y_side - c) = ln(coeff) + b
                return sp.Eq(sp.log(y_side - c), sp.log(coeff) + b)
            else:
                return sp.Eq(y_side, expr_side)

        # Check for reciprocal in expression side
        if expr_side.has(1 / x):
            return sp.Eq(y_side, expr_side)

        # All other cases (power, polynomial, linear, or y^n forms) -> keep unchanged
        # This includes: y = x^n, 2*y = x^2, y^2 = x + c, etc.
        return sp.Eq(y_side, expr_side)

