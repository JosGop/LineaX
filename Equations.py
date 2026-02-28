"""Equations.py — Equation library and data structures for LineaX.

Provides:
  CONSTANTS        — SI values for physical constants from the OCR Physics A booklet
  Equation         — immutable record for one equation in the library
  ScientificEquation — mutable container for a linearised equation and its interpretation
  EquationLibrary  — searchable catalogue of OCR Physics A equations (Modules 3–6)

The EquationLibrary satisfies success criterion 2.1.1 (the application must provide
a searchable physics equation library for OCR A-Level Physics A).
"""

# dataclass generates __init__, __repr__ and __eq__ automatically; frozen=True makes
# the instance immutable (hashable) so Equation objects can safely be stored in sets.
from dataclasses import dataclass

# Dict, List, Set, Optional, Tuple are standard type hint aliases from typing.
from typing import Dict, List, Set, Optional, Tuple

# sympy is the symbolic mathematics library; used in ScientificEquation to store
# linearised SymPy Eq objects and in EquationLibrary for type hints.
import sympy as sp


# Physical constants from the OCR Physics A Data, Formulae and Relationships Booklet (SI units).
# These are pre-filled into constant entry fields on Screen 2 by _default_constant() in
# AnalysisMethodScreen, satisfying success criterion 2.1.2.
CONSTANTS: Dict[str, float] = {
    "g": 9.81,          # gravitational field strength near Earth's surface (m s⁻²)
    "e": 1.60e-19,      # elementary charge (C)
    "c": 3.00e8,        # speed of light in vacuo (m s⁻¹)
    "h": 6.63e-34,      # Planck constant (J s)
    "N": 6.02e23,       # Avogadro constant (mol⁻¹)
    "R": 8.31,          # molar gas constant (J mol⁻¹ K⁻¹)
    "k": 1.38e-23,      # Boltzmann constant (J K⁻¹)
    "G": 6.67e-11,      # gravitational constant (N m² kg⁻²)
    "epsilon_0": 8.85e-12,  # permittivity of free space (F m⁻¹)
    "m_e": 9.11e-31,    # electron rest mass (kg)
    "m_p": 1.673e-27,   # proton rest mass (kg)
    "m_n": 1.675e-27,   # neutron rest mass (kg)
    "m_alpha": 6.646e-27,   # alpha particle mass (kg)
    "sigma": 5.67e-8,   # Stefan-Boltzmann constant (W m⁻² K⁻⁴)
}


@dataclass(frozen=True)
class Equation:
    """Immutable record describing a single scientific equation in the library.

    frozen=True means all fields are set once in __init__ and cannot be changed;
    the dataclass decorator generates __init__ automatically from the field declarations.

    Fields:
      name                — human-readable name used in search results and Screen 4
      expression          — string form of the equation (e.g. 'v = u + a*t')
      variables           — dict mapping symbol to physical meaning (e.g. 'v': 'final velocity')
      linearisation_type  — hint for the linearisation algorithm: 'linear', 'exponential',
                            'reciprocal', 'quadratic' or 'power'
      transform_info      — pre-computed gradient/intercept meanings for exponential equations,
                            used by _identify_meanings in AnalysisMethodScreen
    """
    name: str
    expression: str
    variables: Dict[str, str]
    linearisation_type: Optional[str] = None
    transform_info: Optional[Dict[str, str]] = None

    def __post_init__(self):
        # object.__setattr__ is required here because frozen=True normally forbids attribute
        # assignment; this sets the default for transform_info after dataclass __init__ runs.
        if self.transform_info is None:
            object.__setattr__(self, 'transform_info', {})


class ScientificEquation:
    """Represents a scientific equation and its linearised y = mx + c form.

    Populated by AnalysisMethodScreen._linearise_equation (Algorithm 2, Section 3.2.2)
    and carried through ScreenManager.equation_info to GradientAnalysisScreen so that
    Screen 4 can display the physical meaning of the regression gradient and intercept.
    """

    def __init__(self, original_equation: str):
        self.original_equation = original_equation
        # linearised_equation is a SymPy Eq object produced by Algorithm 2.
        self.linearised_equation: Optional[sp.Eq] = None
        self.y_symbol = self.x_symbol = self.y_meaning = self.x_meaning = None
        self.m = self.c = self.m_meaning = self.c_meaning = None
        self.linearised_str: Optional[str] = None

    def set_linearisation(self, linearised_eq, y_symbol, x_symbol, y_meaning, x_meaning, m_meaning, c_meaning):
        """Store all linearisation metadata at once after Algorithm 2 completes."""
        self.linearised_equation = linearised_eq
        self.y_symbol, self.x_symbol = y_symbol, x_symbol
        self.y_meaning, self.x_meaning = y_meaning, x_meaning
        self.m_meaning, self.c_meaning = m_meaning, c_meaning
        # str(linearised_eq) produces a human-readable string of the SymPy Eq.
        self.linearised_str = str(linearised_eq)

    def get_plot_labels(self) -> Tuple[str, str]:
        """Return (x_axis_label, y_axis_label) for the graph axes."""
        return self.x_symbol or "x", self.y_symbol or "y"

    def get_gradient_meaning(self) -> str:
        """Return the physical interpretation of the gradient (e.g. '-μ')."""
        return self.m_meaning or "gradient"

    def get_intercept_meaning(self) -> str:
        """Return the physical interpretation of the y-intercept (e.g. 'ln(I₀)')."""
        return self.c_meaning or "y-intercept"


class EquationLibrary:
    """Searchable library of OCR Physics A equations from Modules 3–6.

    Uses an inverted keyword index (_build_index) for efficient multi-token search.
    search() intersects per-token hit sets so that a query like 'decay constant'
    returns only equations containing both tokens, satisfying success criterion 2.1.1.
    """

    def __init__(self):
        self._equations: List[Equation] = []
        # _index maps individual lowercase tokens to the set of equation indices
        # that contain that token in name, expression, or variable descriptions.
        self._index: Dict[str, Set[int]] = {}
        self._load_equations()
        self._build_index()

    def _load_equations(self):
        """Load all equations from OCR Physics A Modules 3–6.

        Each Equation entry includes a linearisation_type hint used by Algorithm 2
        and, for exponential equations, pre-computed transform_info providing
        human-readable gradient and intercept meanings.
        """
        self._equations = [
            # Module 3: Forces and motion
            Equation("SUVAT (velocity)", "v = u + a*t",
                     {"v": "final velocity", "u": "initial velocity", "a": "acceleration", "t": "time"},
                     linearisation_type="linear"),
            Equation("SUVAT (displacement)", "s = (u + v)*t/2",
                     {"s": "displacement", "u": "initial velocity", "v": "final velocity", "t": "time"},
                     linearisation_type="linear"),
            Equation("SUVAT (displacement 2)", "s = u*t + 0.5*a*t**2",
                     {"s": "displacement", "u": "initial velocity", "a": "acceleration", "t": "time"},
                     linearisation_type="quadratic"),
            Equation("SUVAT (velocity squared)", "v**2 = u**2 + 2*a*s",
                     {"v": "final velocity", "u": "initial velocity", "a": "acceleration", "s": "displacement"},
                     linearisation_type="linear"),
            Equation("Momentum", "p = m*v",
                     {"p": "momentum", "m": "mass", "v": "velocity"},
                     linearisation_type="linear"),
            Equation("Force from momentum", "F = Δp/Δt",
                     {"F": "force", "p": "momentum", "t": "time"},
                     linearisation_type="linear"),
            Equation("Density", "ρ = m/V",
                     {"ρ": "density", "m": "mass", "V": "volume"},
                     linearisation_type="reciprocal"),
            Equation("Pressure", "p = F/A",
                     {"p": "pressure", "F": "force", "A": "area"},
                     linearisation_type="reciprocal"),
            Equation("Pressure in fluids", "p = ρ*g*h",
                     {"p": "pressure", "ρ": "density", "g": "gravitational field strength", "h": "height"},
                     linearisation_type="linear"),
            Equation("Work done", "W = F*s*cos(θ)",
                     {"W": "work", "F": "force", "s": "displacement", "θ": "angle"},
                     linearisation_type="linear"),
            Equation("Power", "P = W/t",
                     {"P": "power", "W": "work", "t": "time"},
                     linearisation_type="linear"),
            Equation("Power (mechanical)", "P = F*v",
                     {"P": "power", "F": "force", "v": "velocity"},
                     linearisation_type="linear"),
            Equation("Hooke's law", "F = k*x",
                     {"F": "force", "k": "spring constant", "x": "extension"},
                     linearisation_type="linear"),
            Equation("Elastic potential energy", "E = 0.5*k*x**2",
                     {"E": "energy", "k": "spring constant", "x": "extension"},
                     linearisation_type="quadratic"),
            # Module 4: Waves and electricity
            Equation("Charge", "Q = I*t",
                     {"Q": "charge", "I": "current", "t": "time"},
                     linearisation_type="linear"),
            Equation("Resistance", "R = ρ*L/A",
                     {"R": "resistance", "ρ": "resistivity", "L": "length", "A": "area"},
                     linearisation_type="linear"),
            Equation("Electrical power", "P = V*I",
                     {"P": "power", "V": "potential difference", "I": "current"},
                     linearisation_type="linear"),
            Equation("Wave speed", "v = f*λ",
                     {"v": "wave speed", "f": "frequency", "λ": "wavelength"},
                     linearisation_type="linear"),
            Equation("Photon energy", "E = h*f",
                     {"E": "energy", "h": "Planck constant", "f": "frequency"},
                     linearisation_type="linear"),
            Equation("Photoelectric equation", "h*f = φ + KE",
                     {"h": "Planck constant", "f": "frequency", "φ": "work function", "KE": "maximum kinetic energy"},
                     linearisation_type="linear"),
            # Module 5: Newtonian world
            Equation("Ideal gas law", "p*V = n*R*T",
                     {"p": "pressure", "V": "volume", "n": "amount of substance", "R": "gas constant", "T": "temperature"},
                     linearisation_type="linear"),
            Equation("Centripetal force", "F = m*v**2/r",
                     {"F": "force", "m": "mass", "v": "velocity", "r": "radius"},
                     linearisation_type="quadratic"),
            Equation("Gravitational force", "F = G*M*m/r**2",
                     {"F": "force", "G": "gravitational constant", "M": "mass", "m": "mass", "r": "distance"},
                     linearisation_type="reciprocal"),
            Equation("Stefan-Boltzmann law", "L = 4*π*r**2*σ*T**4",
                     {"L": "luminosity", "r": "radius", "σ": "Stefan constant", "T": "temperature"},
                     linearisation_type="power"),
            # Module 6: Fields and particles
            Equation("Capacitance", "C = Q/V",
                     {"C": "capacitance", "Q": "charge", "V": "potential difference"},
                     linearisation_type="linear"),
            Equation("Energy in capacitor", "E = 0.5*C*V**2",
                     {"E": "energy", "C": "capacitance", "V": "potential difference"},
                     linearisation_type="quadratic"),
            Equation("Electric field strength", "E = F/Q",
                     {"E": "electric field strength", "F": "force", "Q": "charge"},
                     linearisation_type="linear"),
            Equation("Magnetic force", "F = B*Q*v",
                     {"F": "force", "B": "magnetic flux density", "Q": "charge", "v": "velocity"},
                     linearisation_type="linear"),
            Equation("Mass-energy equivalence", "E = m*c**2",
                     {"E": "energy", "m": "mass", "c": "speed of light"},
                     linearisation_type="linear"),
            # Exponential equations: logarithmic linearisation (Algorithm 2, Section 3.2.2).
            # transform_info provides pre-computed gradient/intercept meanings because
            # SymPy's polynomial coefficient extraction does not apply to log-linear forms.
            Equation("Radioactive activity", "A = A0*exp(-λ*t)",
                     {"A": "activity", "A0": "initial activity", "λ": "decay constant", "t": "time"},
                     linearisation_type="exponential",
                     transform_info={
                         "y_transform": "ln(A)", "x_transform": "t",
                         "gradient_meaning": "-λ (negative decay constant)",
                         "intercept_meaning": "ln(A0) (natural log of initial activity)",
                     }),
            Equation("Number of undecayed nuclei", "N = N0*exp(-λ*t)",
                     {"N": "number of nuclei", "N0": "initial number", "λ": "decay constant", "t": "time"},
                     linearisation_type="exponential",
                     transform_info={
                         "y_transform": "ln(N)", "x_transform": "t",
                         "gradient_meaning": "-λ (negative decay constant)",
                         "intercept_meaning": "ln(N0) (natural log of initial number)",
                     }),
            Equation("Half-life relation", "λ*t_1/2 = ln(2)",
                     {"λ": "decay constant", "t_1/2": "half-life"},
                     linearisation_type="linear"),
            Equation("X-ray attenuation", "I = I0*exp(-μ*x)",
                     {"I": "intensity", "I0": "initial intensity", "μ": "attenuation coefficient", "x": "thickness"},
                     linearisation_type="exponential",
                     transform_info={
                         "y_transform": "ln(I)", "x_transform": "x",
                         "gradient_meaning": "-μ (negative attenuation coefficient)",
                         "intercept_meaning": "ln(I0) (natural log of initial intensity)",
                     }),
            Equation("Capacitor charging", "V = V0*(1 - exp(-t/(C*R)))",
                     {"V": "potential difference", "V0": "final potential difference", "t": "time",
                      "C": "capacitance", "R": "resistance"},
                     linearisation_type="exponential"),
            Equation("Capacitor discharging", "x = x0*exp(-t/(C*R))",
                     {"x": "charge or potential difference", "x0": "initial value", "t": "time",
                      "C": "capacitance", "R": "resistance"},
                     linearisation_type="exponential",
                     transform_info={
                         "y_transform": "ln(x)", "x_transform": "t",
                         "gradient_meaning": "-1/(C*R) (negative reciprocal of time constant)",
                         "intercept_meaning": "ln(x0) (natural log of initial value)",
                     }),
        ]

    def _build_index(self):
        """Build an inverted keyword index for efficient multi-token search.

        For each equation, all tokens from the name, expression and variable descriptions
        are extracted and lowercased. setdefault initialises a new empty set for any
        token not yet in the index, then adds the equation's index position to that set.
        The resulting _index supports O(1) per-token lookup used in search().
        """
        for idx, eq in enumerate(self._equations):
            tokens = set(eq.name.lower().split())
            # Add tokens from the expression string, splitting on operators.
            tokens.update(eq.expression.replace("=", " ").replace("*", " ").split())
            for symbol, meaning in eq.variables.items():
                tokens.add(symbol.lower())
                tokens.update(meaning.lower().split())
            for token in tokens:
                self._index.setdefault(token, set()).add(idx)

    def search(self, query: str) -> List[Equation]:
        """Return equations matching all tokens in the query string.

        Splits the query into tokens and intersects their hit sets so that only
        equations matching every token are returned (AND search). If any token is
        not in the index, the empty list is returned immediately.
        Satisfies success criterion 2.1.1 (equation search must return relevant results).
        """
        if not query:
            return []
        matched: Set[int] = set()
        for token in query.lower().split():
            if token not in self._index:
                return []
            # On first token, initialise matched; on subsequent tokens, intersect.
            matched = self._index[token] if not matched else matched & self._index[token]
        return [self._equations[i] for i in matched]