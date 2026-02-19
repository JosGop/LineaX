"""
Equations.py

Defines the equation library and supporting data structures for LineaX.
Corresponds to Section 3.2.1 (Sub-component: Scientific Equation Selection) and
Section 3.2.2 (Structure of the Solution — Equation Handling module). The
EquationLibrary implements the searchable equation dropdown described in the UI
design (Screen 2: Analysis Method, Section 3.2.2). Physical constants are drawn
from the OCR Physics A Data, Formulae and Relationships Booklet, as referenced
throughout Section 3.1.3 and the proposed solution (Section 3.1.4).
"""

from dataclasses import dataclass
from typing import Dict, List, Set, Optional, Tuple
import sympy as sp

"""
Physical constants from the OCR Physics A Data, Formulae and Relationships Booklet.

Listed here to satisfy the requirement in Section 3.1.3 (Research — Equation Handling
and Interpretation) that the solution must support pre-populated scientific constants,
eliminating the manual entry errors identified as a limitation of Excel and Prism.
All values are in SI units.
"""

CONSTANTS: Dict[str, float] = {
    "g": 9.81,           # acceleration due to gravity (m s^-2)
    "e": 1.60e-19,       # elementary charge (C)
    "c": 3.00e8,         # speed of light in vacuum (m s^-1)
    "h": 6.63e-34,       # Planck constant (J s)
    "N": 6.02e23,        # Avogadro constant (mol^-1)
    "R": 8.31,           # molar gas constant (J mol^-1 K^-1)
    "k": 1.38e-23,       # Boltzmann constant (J K^-1)
    "G": 6.67e-11,       # gravitational constant (N m^2 kg^-2)
    "epsilon_0": 8.85e-12,  # permittivity of free space (F m^-1)
    "m_e": 9.11e-31,     # electron rest mass (kg)
    "m_p": 1.673e-27,    # proton rest mass (kg)
    "m_n": 1.675e-27,    # neutron rest mass (kg)
    "m_alpha": 6.646e-27,  # alpha particle rest mass (kg)
    "sigma": 5.67e-8     # Stefan constant (W m^-2 K^-4)
}

"""
Equation data structure.

Stores the metadata required to display, search, and apply an equation.
The transform_info dict captures the axis transformations and gradient/intercept
meanings needed by Algorithm 2 (linearisation, Section 3.2.2) and Algorithm 5
(gradient interpretation, Section 3.2.2). The linearisation_type field drives
the correct branch selection in DataTransform.py.
"""


@dataclass(frozen=True)
class Equation:
    """
    Immutable record describing a single scientific equation in the library.

    Each Equation instance encodes all information needed to: present the equation
    to the user (name, expression, variables), select the correct linearisation
    path (linearisation_type), and interpret gradient/intercept physically
    (transform_info). Used by EquationLibrary and AnalysisMethod.py. Defined as
    frozen to prevent accidental mutation after construction.
    """
    name: str             # human-readable label shown in the equation dropdown
    expression: str       # equation as a parseable string, e.g. "v = u + a*t"
    variables: Dict[str, str]  # maps each symbol to its physical meaning
    linearisation_type: Optional[str] = None   # e.g. "linear", "exponential", "power"
    transform_info: Optional[Dict[str, str]] = None  # axis transforms and gradient meanings

    def __post_init__(self):
        # Ensure transform_info is never None to allow safe dict access downstream
        if self.transform_info is None:
            object.__setattr__(self, 'transform_info', {})


class ScientificEquation:
    """
    Represents a scientific equation and its linearised y = mx + c form.

    Implements the 'Linearise to the form y = mx + c' sub-component described in
    Section 3.2.1 (Branch 3 — Linear) and Algorithm 2 from Section 3.2.2. After
    set_linearisation() is called, all axis and coefficient metadata is available
    for the graph display and gradient analysis screens (Sections 3.2.2 UI design,
    Screens 3a and 4). Note: a separate ScientificEquation class also exists in
    LineaX_Classes.py as a stub; this version in Equations.py is the full implementation.
    """

    def __init__(self, original_equation: str):
        self.original_equation = original_equation   # user-entered or library equation string
        self.linearised_equation: Optional[sp.Eq] = None  # SymPy Eq in y = mx + c form
        # Axis symbols and their meanings, set after linearisation
        self.y_symbol = self.x_symbol = self.y_meaning = self.x_meaning = None
        # Linear constants and their physical meanings, e.g., gradient = "spring constant k"
        self.m = self.c = self.m_meaning = self.c_meaning = None
        self.linearised_str: Optional[str] = None  # human-readable linearised form for display

    def set_linearisation(
            self,
            linearised_eq: sp.Eq,
            y_symbol: str, x_symbol: str,
            y_meaning: str, x_meaning: str,
            m_meaning: str, c_meaning: str
    ):
        """
        Set all linearisation information at once.

        Called after Algorithm 2 (Section 3.2.2) completes transformation. Stores the
        SymPy equation alongside the physical meanings of each term, which are then
        retrieved by GradientAnalysis.py to populate the 'Gradient Analysis & Results'
        screen (Section 3.2.2, Screen 4).
        """
        self.linearised_equation = linearised_eq
        self.y_symbol, self.x_symbol = y_symbol, x_symbol
        self.y_meaning, self.x_meaning = y_meaning, x_meaning
        self.m_meaning, self.c_meaning = m_meaning, c_meaning
        self.linearised_str = str(linearised_eq)  # store string form for annotation display

    def get_plot_labels(self) -> Tuple[str, str]:
        """
        Return (x_axis_label, y_axis_label) for the graph.

        Labels reflect any transformation applied (e.g., "ln(Force)"), satisfying the
        requirement in Section 3.2.1 (Sub-sub-component: Assign apt. x and y values)
        that axis labels update automatically after linearisation.
        """
        return self.x_symbol or "x", self.y_symbol or "y"

    def get_gradient_meaning(self) -> str:
        """Return the physical interpretation of the gradient for Screen 4 display."""
        return self.m_meaning or "gradient"

    def get_intercept_meaning(self) -> str:
        """Return the physical interpretation of the y-intercept for Screen 4 display."""
        return self.c_meaning or "y-intercept"


"""
Equation library storing OCR Physics A syllabus equations from Modules 3–6.

Implements the 'Scientific Equation Selection' sub-component from Section 3.2.1
(Branch 3 — Linear). The library satisfies the success criterion (Section 3.1.4)
requiring pre-stored equations with correct physical variable mappings. An inverted
keyword index is built at construction for O(k) average-case search, where k is
the number of query tokens, matching the efficiency requirement raised in Section
3.1.4 (Measurable Success Criteria).
"""


class EquationLibrary:
    """
    Searchable library of OCR Physics A equations from Modules 3–6.

    Addresses the limitation identified in Section 3.1.3 (Research) that Excel and
    Prism do not interpret gradients or intercepts in scientific context. Each stored
    Equation includes physical variable meanings and gradient/intercept interpretations
    so LineaX can contextualise results on Screen 4 (Section 3.2.2, User Interface).
    The inverted index supports the search bar in Screen 2 (Analysis Method).
    """
    def __init__(self):
        self._equations: List[Equation] = []       # ordered list of all stored equations
        self._index: Dict[str, Set[int]] = {}      # inverted keyword → equation index set
        self._load_equations()
        self._build_index()

    def _load_equations(self):
        """
        Load all equations from Modules 3–6 of the OCR Physics A syllabus.

        Equations are grouped by module and tagged with linearisation_type to drive
        Algorithm 2 (Section 3.2.2) and transform_info for gradient interpretation
        on Screen 4. Exponential equations include explicit transform metadata
        corresponding to the worked examples in Section 3.2.1 (Linearise sub-component).
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

            # Exponential equations — require Algorithm 2 logarithmic linearisation (Section 3.2.2)

            Equation("Radioactive activity", "A = A0*exp(-λ*t)",
                     {"A": "activity", "A0": "initial activity", "λ": "decay constant", "t": "time"},
                     linearisation_type="exponential",
                     transform_info={
                         "y_transform": "ln(A)", "x_transform": "t",
                         "gradient_meaning": "-λ (negative decay constant)",
                         "intercept_meaning": "ln(A0) (natural log of initial activity)"
                     }),
            Equation("Number of undecayed nuclei", "N = N0*exp(-λ*t)",
                     {"N": "number of nuclei", "N0": "initial number", "λ": "decay constant", "t": "time"},
                     linearisation_type="exponential",
                     transform_info={
                         "y_transform": "ln(N)", "x_transform": "t",
                         "gradient_meaning": "-λ (negative decay constant)",
                         "intercept_meaning": "ln(N0) (natural log of initial number)"
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
                         "intercept_meaning": "ln(I0) (natural log of initial intensity)"
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
                         "intercept_meaning": "ln(x0) (natural log of initial value)"
                     }),
        ]

    def _build_index(self):
        """
        Build an inverted keyword index for O(k) average search, where k = number of query tokens.

        Implements the efficient search described in Section 3.2.2 (Structure of the Solution)
        to support the equation search bar in Screen 2 (Analysis Method). Tokens are drawn
        from equation names, expression tokens, symbol names, and variable meanings, enabling
        multi-term search such as "radioactive decay" or "spring constant".
        """
        for idx, eq in enumerate(self._equations):
            tokens = set(eq.name.lower().split())
            tokens.update(eq.expression.replace("=", " ").replace("*", " ").split())
            for symbol, meaning in eq.variables.items():
                tokens.add(symbol.lower())
                tokens.update(meaning.lower().split())
            for token in tokens:
                self._index.setdefault(token, set()).add(idx)  # append index to each token's set

    def search(self, query: str) -> List[Equation]:
        """
        Search equations using keyword intersection; returns equations matching all query tokens.

        Implements the equation search bar functionality from Screen 2 (Section 3.2.2, User
        Interface). Uses set intersection so only equations matching every query token are
        returned, reducing false positives. Returns an empty list immediately if any token
        is not in the index, avoiding unnecessary iteration.
        """
        if not query:
            return []
        matched: Set[int] = set()
        for token in query.lower().split():
            if token not in self._index:
                return []  # early exit if any token has no matches
            matched = self._index[token] if not matched else matched & self._index[token]
        return [self._equations[i] for i in matched]