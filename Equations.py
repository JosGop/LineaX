from dataclasses import dataclass
from typing import Dict, List, Set
import sympy as sp


"""

Physical constants:


Values taken from the OCR Physics A Data, Formulae and Relationships Booklet.
All values are given in SI units.
"""

CONSTANTS: Dict[str, float] = {
    "g": 9.81,                     # acceleration due to gravity (m s^-2)
    "e": 1.60e-19,                 # elementary charge (C)
    "c": 3.00e8,                   # speed of light in vacuum (m s^-1)
    "h": 6.63e-34,                 # Planck constant (J s)
    "N": 6.02e23,                  # Avogadro constant (mol^-1)
    "R": 8.31,                     # molar gas constant (J mol^-1 K^-1)
    "k": 1.38e-23,                 # Boltzmann constant (J K^-1)
    "G": 6.67e-11,                 # gravitational constant (N m^2 kg^-2)
    "epsilon_0": 8.85e-12,         # permittivity of free space (F m^-1)
    "m_e": 9.11e-31,                # electron rest mass (kg)
    "m_p": 1.673e-27,               # proton rest mass (kg)
    "m_n": 1.675e-27,               # neutron rest mass (kg)
    "m_alpha": 6.646e-27,          # alpha particle rest mass (kg)
    "sigma": 5.67e-8               # Stefan constant (W m^-2 K^-4)
}


"""

Equation data structure:


Each equation stores:
- a readable name
- the equation as a string
- a dictionary mapping symbols to meanings
"""

@dataclass(frozen=True)
class Equation:
    name: str
    expression: str
    variables: Dict[str, str]


"""

Equation library:

Stores all syllabus equations from Module 3 onwards.
Provides keyword-based searching for use in LineaX.
"""

class EquationLibrary:
    def __init__(self):
        self._equations: List[Equation] = []
        self._index: Dict[str, Set[int]] = {}
        self._load_equations()
        self._build_index()

    """
    Load all equations from Modules 3 to 6 of the OCR Physics A syllabus.
    """

    def _load_equations(self):
        self._equations = [

            # Module 3: Forces and motion

            Equation(
                "SUVAT (velocity)",
                "v = u + a*t",
                {"v": "final velocity", "u": "initial velocity", "a": "acceleration", "t": "time"}
            ),

            Equation(
                "SUVAT (displacement)",
                "s = (u + v)*t/2",
                {"s": "displacement", "u": "initial velocity", "v": "final velocity", "t": "time"}
            ),

            Equation(
                "SUVAT (displacement 2)",
                "s = u*t + 0.5*a*t^2",
                {"s": "displacement", "u": "initial velocity", "a": "acceleration", "t": "time"}
            ),

            Equation(
                "SUVAT (velocity squared)",
                "v^2 = u^2 + 2*a*s",
                {"v": "final velocity", "u": "initial velocity", "a": "acceleration", "s": "displacement"}
            ),

            Equation(
                "Momentum",
                "p = m*v",
                {"p": "momentum", "m": "mass", "v": "velocity"}
            ),

            Equation(
                "Force from momentum",
                "F = Δp/Δt",
                {"F": "force", "p": "momentum", "t": "time"}
            ),

            Equation(
                "Density",
                "ρ = m/V",
                {"ρ": "density", "m": "mass", "V": "volume"}
            ),

            Equation(
                "Pressure",
                "p = F/A",
                {"p": "pressure", "F": "force", "A": "area"}
            ),

            Equation(
                "Pressure in fluids",
                "p = ρ*g*h",
                {"p": "pressure", "ρ": "density", "g": "gravitational field strength", "h": "height"}
            ),

            Equation(
                "Work done",
                "W = F*s*cos(θ)",
                {"W": "work", "F": "force", "s": "displacement", "θ": "angle"}
            ),

            Equation(
                "Power",
                "P = W/t",
                {"P": "power", "W": "work", "t": "time"}
            ),

            Equation(
                "Power (mechanical)",
                "P = F*v",
                {"P": "power", "F": "force", "v": "velocity"}
            ),

            Equation(
                "Hooke's law",
                "F = k*x",
                {"F": "force", "k": "spring constant", "x": "extension"}
            ),

            Equation(
                "Elastic potential energy",
                "E = 0.5*k*x^2",
                {"E": "energy", "k": "spring constant", "x": "extension"}
            ),

            # Module 4: Waves and electricity

            Equation(
                "Charge",
                "Q = I*t",
                {"Q": "charge", "I": "current", "t": "time"}
            ),

            Equation(
                "Resistance",
                "R = ρ*L/A",
                {"R": "resistance", "ρ": "resistivity", "L": "length", "A": "area"}
            ),

            Equation(
                "Electrical power",
                "P = V*I",
                {"P": "power", "V": "potential difference", "I": "current"}
            ),

            Equation(
                "Wave speed",
                "v = f*λ",
                {"v": "wave speed", "f": "frequency", "λ": "wavelength"}
            ),

            Equation(
                "Photon energy",
                "E = h*f",
                {"E": "energy", "h": "Planck constant", "f": "frequency"}
            ),

            Equation(
                "Photoelectric equation",
                "h*f = φ + KE",
                {"h": "Planck constant", "f": "frequency", "φ": "work function", "KE": "maximum kinetic energy"}
            ),

            # Module 5: Newtonian world

            Equation(
                "Ideal gas law",
                "p*V = n*R*T",
                {"p": "pressure", "V": "volume", "n": "amount of substance", "R": "gas constant", "T": "temperature"}
            ),

            Equation(
                "Centripetal force",
                "F = m*v^2/r",
                {"F": "force", "m": "mass", "v": "velocity", "r": "radius"}
            ),

            Equation(
                "Gravitational force",
                "F = G*M*m/r^2",
                {"F": "force", "G": "gravitational constant", "M": "mass", "m": "mass", "r": "distance"}
            ),

            Equation(
                "Stefan–Boltzmann law",
                "L = 4*π*r^2*σ*T^4",
                {"L": "luminosity", "r": "radius", "σ": "Stefan constant", "T": "temperature"}
            ),

            # Module 6: Fields and particles

            Equation(
                "Capacitance",
                "C = Q/V",
                {"C": "capacitance", "Q": "charge", "V": "potential difference"}
            ),

            Equation(
                "Energy in capacitor",
                "E = 0.5*C*V^2",
                {"E": "energy", "C": "capacitance", "V": "potential difference"}
            ),

            Equation(
                "Electric field strength",
                "E = F/Q",
                {"E": "electric field strength", "F": "force", "Q": "charge"}
            ),

            Equation(
                "Magnetic force",
                "F = B*Q*v",
                {"F": "force", "B": "magnetic flux density", "Q": "charge", "v": "velocity"}
            ),

            Equation(
                "Mass–energy equivalence",
                "E = m*c^2",
                {"E": "energy", "m": "mass", "c": "speed of light"}
            ),

            # Exponential equations

            Equation(
                "Radioactive activity",
                "A = A0*e^(-λ*t)",
                {"A": "activity", "A0": "initial activity", "λ": "decay constant", "t": "time"}
            ),

            Equation(
                "Number of undecayed nuclei",
                "N = N0*e^(-λ*t)",
                {"N": "number of nuclei", "N0": "initial number", "λ": "decay constant", "t": "time"}
            ),

            Equation(
                "Half-life relation",
                "λ*t_1/2 = ln(2)",
                {"λ": "decay constant", "t_1/2": "half-life"}
            ),

            Equation(
                "X-ray attenuation",
                "I = I0*e^(-μ*x)",
                {"I": "intensity", "I0": "initial intensity", "μ": "attenuation coefficient", "x": "thickness"}
            ),

            Equation(
                "Capacitor charging",
                "V = V0*(1 - e^(-t/(C*R)))",
                {"V": "potential difference", "V0": "final potential difference", "t": "time", "C": "capacitance", "R": "resistance"}
            ),

            Equation(
                "Capacitor discharging",
                "x = x0*e^(-t/(C*R))",
                {"x": "charge or potential differnence", "x0": "initial value", "t": "time", "C": "capacitance", "R": "resistance"}
            ),
        ]


    """
    Build a keyword index to allow fast searching by name, symbol or description.
    """
    def _build_index(self):
        for idx, eq in enumerate(self._equations):
            tokens = set(eq.name.lower().split())
            tokens.update(eq.expression.replace("=", " ").replace("*", " ").split())
            for symbol, meaning in eq.variables.items():
                tokens.add(symbol.lower())
                tokens.update(meaning.lower().split())
            for token in tokens:
                self._index.setdefault(token, set()).add(idx)

    """
    Search the equation library using keyword matching.
    """
    def search(self, query: str) -> List[Equation]:
        if not query:
            return []
        query_tokens = query.lower().split()
        matched: Set[int] = set()
        for token in query_tokens:
            if token in self._index:
                matched = self._index[token] if not matched else matched & self._index[token]
        return [self._equations[i] for i in matched]


    # Global SymPy symbols for later algebra and graphing
    x, y = sp.symbols("x y")

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

