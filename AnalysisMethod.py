"""
AnalysisMethod.py

Screen 2 of the LineaX application — presents the user with the two analysis
pathways described in Section 3.2.1 (Branch 3):

    Left panel  — Linear Graph Analysis: the user searches the EquationLibrary
                  (or enters a custom equation), selects the two measured variables
                  by clicking them, optionally specifies a variable to find, then
                  triggers linearisation.  The screen calls DataTransformer and
                  stores the result in ScreenManager before handing off to
                  LinearGraphResultsScreen.

    Right panel — Automated Model Selection: displays nine model cards; selecting
                  any one navigates directly to AutomatedGraphResultsScreen without
                  equation configuration.

Implements Algorithm 2 (Section 3.2.2 — Linearise to the form y = mx + c) through
the _linearise_equation / _attempt_linearisation pipeline, and the 'Assign apt. x
and y values' sub-component by scoring two candidate variable orderings and choosing
the one that better satisfies standard physics conventions.
"""

import re
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Tuple

import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
)

from DataTransform import DataTransformer, identify_required_transformations
from Equations import *
from LineaX_Classes import ScientificEquation, InputData
from LinearGraphDisplay import LinearGraphResultsScreen
from AutomatedGraphDisplay import AutomatedGraphResultsScreen
from ManagingScreens import ScreenManager, make_scrollable

# SymPy parser transformations — enables implicit multiplication (e.g. "2x" → "2*x")
# as described in Section 3.3 (Linearising Equations).
TRANSFORMS = standard_transformations + (implicit_multiplication_application,)

# Maps common text representations and Unicode Greek letters to their canonical
# SymPy-compatible forms.  Defined at module level so both _enter_custom_equation
# and _linearise_equation can share the same single source of truth.
_GREEK_REPLACEMENTS = {
    "lambda": "lambda_",
    "Lambda": "lambda_",
    "mu":     "mu",
    "sigma":  "sigma",
    "theta":  "theta",
    "phi":    "phi",
    "rho":    "rho",
    "λ":      "lambda_",
    "μ":      "mu",
    "σ":      "sigma",
    "ρ":      "rho",
    "θ":      "theta",
    "φ":      "phi",
    "π":      "pi",
    "Δ":      "Delta",
}

# Maps the same Greek identifiers to their display Unicode characters, used when
# populating variable description labels in _enter_custom_equation.
_GREEK_DISPLAY_DESCRIPTIONS = {
    "λ":  "wavelength or decay constant",
    "lam":  "wavelength or decay constant",
    "lamb": "wavelength or decay constant",
    "μ":  "coefficient",
    "σ":  "cross-section or Stefan constant",
    "ρ":  "density or resistivity",
    "θ":  "angle",
    "φ":  "angle or work function",
    "f":  "frequency",
    "v":  "velocity",
    "c":  "speed of light or constant",
    "h":  "height or Planck constant",
}


def _apply_greek_replacements(text: str) -> str:
    """
    Replace all Greek letter representations in text with SymPy-safe ASCII forms.

    Centralises the substitution logic previously duplicated across
    _enter_custom_equation and _linearise_equation.  The replacement order
    follows longest-match-first to prevent partial substitutions (e.g. 'lambda'
    must be replaced before a hypothetical single-char sweep).

    Args:
        text: Raw equation string that may contain 'lambda', 'μ', 'θ', etc.

    Returns:
        String with all recognised Greek forms converted for SymPy parsing.
    """
    for original, replacement in _GREEK_REPLACEMENTS.items():
        text = text.replace(original, replacement)
    return text


class AnalysisMethodScreen(tk.Frame):
    """
    Screen 2: Analysis Method selection and equation linearisation.

    Defined in Section 3.3 Development (Stage 3).  Implements the two analysis
    branches described in Section 3.2.1:

      * Branch 3 — Linear: EquationLibrary search → variable selection →
        linearisation via _linearise_equation → data transformation via
        DataTransformer → navigate to LinearGraphResultsScreen.

      * Branch 3 — Automated: model card selection → navigate directly to
        AutomatedGraphResultsScreen.

    The screen retrieves the validated InputData deposited in ScreenManager by
    DataInputScreen (Screen 1) and stores a DataTransformer instance so that
    transformed datasets can be accessed by generate_graph() without re-computation.
    """

    def __init__(self, parent, manager: ScreenManager):
        super().__init__(parent, bg="#f5f6f8", padx=20, pady=20)
        self.manager = manager

        # EquationLibrary provides the searchable catalogue of scientific equations
        # defined in Equations.py, corresponding to Section 3.2.1 (Scientific Equation
        # Selection sub-component).
        self.library = EquationLibrary()

        # Currently active Equation object from the library or custom entry
        self.selected_equation: Optional[Equation] = None

        # ScientificEquation stores the symbolic linearised form and its physical
        # interpretation (m_meaning, c_meaning) after _linearise_equation completes.
        self.scientific_equation: Optional[ScientificEquation] = None

        # Set of variable names the user has selected by clicking in the equation canvas
        self.selected_vars: set = set()

        # Raw InputData from Stage 1, preserved for revert_to_raw_data()
        self.raw_data: Optional[InputData] = None
        # Linearised / transformed dataset written to ScreenManager for Screen 3a
        self.transformed_data: Optional[InputData] = None
        # DataTransformer wrapping the raw data; applies transforms in _linearise_equation
        self.data_transformer: Optional[DataTransformer] = None

        self._load_data_from_manager()
        self.create_layout()

    def _load_data_from_manager(self):
        """
        Retrieve validated InputData from ScreenManager and initialise DataTransformer.

        Called once during __init__.  Mirrors the 'Retrieve raw data' step in the
        Data Flow diagram (Section 3.2.1).  Stores raw_data in ScreenManager via
        set_raw_data() so it can be recovered by revert_to_raw_data() or the
        'Fit other Models' workflow (Section 3.2.1, Branch 4) without re-importing.
        Warns the user and skips transformer initialisation if no data was passed.
        """
        self.raw_data = self.manager.get_data()
        self.manager.set_raw_data(self.raw_data)

        if self.raw_data is None:
            messagebox.showwarning(
                "No Data",
                "No data was found. Please go back and input your data."
            )
        else:
            self.data_transformer = DataTransformer(self.raw_data)

    def create_layout(self):
        """
        Build the top-level window layout: navigation bar, title, and two-column panel.

        The two columns correspond to the two analysis pathways in Section 3.2.1
        (Branch 3 — Linear and Automated).  Both columns are equally weighted via
        grid_columnconfigure so the panels share available horizontal space, consistent
        with the Screen 2 mockup in Section 3.2.2 (User Interface).
        """
        # Navigation bar with back button
        nav_bar = tk.Frame(self, bg="#f5f6f8")
        nav_bar.pack(fill="x", pady=(0, 10))

        tk.Button(
            nav_bar,
            text="← Back",
            font=("Segoe UI", 10),
            bg="#e5e7eb",
            relief="flat",
            cursor="hand2",
            command=self.manager.back
        ).pack(anchor="w")

        tk.Label(
            self,
            text="Choose Your Analysis Method",
            font=("Segoe UI", 26, "bold"),
            bg="#f5f6f8",
            fg="#0f172a"
        ).pack(pady=(10, 25))

        # Grey outer container and padded inner frame that hosts both panel columns
        container = tk.Frame(self, bg="#d1d5db")
        container.pack(fill="both", expand=True)

        inner = tk.Frame(container, bg="#d1d5db", padx=15, pady=15)
        inner.pack(fill="both", expand=True)

        # Both columns receive equal weight; row 0 expands to fill all remaining space
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(1, weight=1)
        inner.grid_rowconfigure(0, weight=1)

        self.create_linear_panel(inner)
        self.create_automated_panel(inner)

    def create_linear_panel(self, parent):
        """
        Build the scrollable Linear Graph Analysis panel (left column).

        Contains: equation search box, results listbox, custom equation entry,
        clickable variable canvas, selected variables indicator, 'Value to Find'
        combobox, 'Linearise Equation' button, linearised result display, constants
        frame, units frame, and 'Generate Linear Graph' button.

        The constants, units, and generate-graph widgets are created here but kept
        hidden (pack_forget) until _linearise_equation reveals them, implementing
        the progressive disclosure pattern described in Section 3.2.2 (User Interface
        — Screen 2).
        """
        _, panel, _, _ = make_scrollable(
            parent,
            row=0,
            column=0,
            padx=(0, 10),
            bg="white",
            panel_kwargs={"padx": 20, "pady": 20},
        )

        tk.Label(
            panel,
            text="Linear Graph Analysis",
            font=("Segoe UI", 14, "bold"),
            bg="white"
        ).pack(anchor="w", pady=(0, 15))

        # Search box with placeholder text behaviour (FocusIn / FocusOut bindings)
        search_frame = tk.Frame(panel, bg="white")
        search_frame.pack(fill="x")

        tk.Label(search_frame, text="🔍", bg="white", fg="#64748b").pack(side="left", padx=(0, 5))

        self.search_placeholder = "Search equations...."
        self.search_entry = tk.Entry(search_frame, fg="#9ca3af")
        self.search_entry.insert(0, self.search_placeholder)
        self.search_entry.pack(fill="x", expand=True)
        self.search_entry.bind("<FocusIn>",   self._clear_placeholder)
        self.search_entry.bind("<FocusOut>",  self._restore_placeholder)
        self.search_entry.bind("<KeyRelease>", self._on_search)

        # Results listbox — populated by _on_search as the user types
        self.results_box = tk.Listbox(panel, height=4)
        self.results_box.pack(fill="x", pady=(5, 10))
        self.results_box.bind("<<ListboxSelect>>", self._select_equation)

        tk.Button(
            panel,
            text="+ Enter Custom Equation",
            bg="#f3f4f6",
            fg="#0f172a",
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 9),
            command=self._enter_custom_equation
        ).pack(fill="x", pady=(0, 10))

        # Equation display — variables rendered as clickable canvas buttons
        tk.Label(
            panel,
            text="Selected Equation:",
            bg="white",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(10, 5))

        self.equation_display_frame = tk.Frame(
            panel, bg="#f8fafc", relief="solid", borderwidth=1
        )
        self.equation_display_frame.pack(fill="x", pady=(0, 10))

        self.equation_canvas = tk.Canvas(
            self.equation_display_frame, bg="#f8fafc", height=60, highlightthickness=0
        )
        self.equation_canvas.pack(fill="x", padx=10, pady=10)

        # Colour-coded display of which variables the user has clicked
        tk.Label(
            panel,
            text="Variables Measured:",
            bg="white",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(10, 5))

        self.selected_vars_display = tk.Label(
            panel,
            text="Click on variables in the equation above that you have measured in your experiment",
            bg="#fffbeb",
            fg="#92400e",
            relief="solid",
            borderwidth=1,
            padx=10,
            pady=8,
            justify="left",
            anchor="w"
        )
        self.selected_vars_display.pack(fill="x", pady=(0, 10))

        # Optional 'Value to Find' combobox — drives gradient/intercept labelling on Screen 4
        tk.Label(
            panel,
            text="Value to Find (optional):",
            bg="white",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(10, 5))

        self.find_var = ttk.Combobox(panel, state="readonly")
        self.find_var.pack(fill="x", pady=(0, 12))

        # Linearise button — triggers _linearise_equation (Algorithm 2, Section 3.2.2)
        tk.Button(
            panel,
            text="Linearise Equation",
            bg="#0f172a",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            command=self._linearise_equation,
            cursor="hand2"
        ).pack(fill="x", pady=(15, 8))

        # Linearised result panel — hidden until linearisation succeeds
        self.linearised_display_frame = tk.LabelFrame(
            panel,
            text="Linearised Form",
            bg="white",
            fg="#0f172a",
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=10
        )

        # Label that displays the pretty-printed SymPy equation string
        self.linearised_equation_label = tk.Label(
            self.linearised_display_frame,
            text="",
            bg="white",
            fg="#0f172a",
            font=("Courier", 11),
            justify="left",
            anchor="w"
        )
        self.linearised_equation_label.pack(fill="x", pady=(0, 10))

        # Plotting instructions text (axis assignments, gradient meaning, intercept meaning)
        self.linearised_info_label = tk.Label(
            self.linearised_display_frame,
            text="",
            bg="#f0f9ff",
            fg="#1e40af",
            justify="left",
            anchor="nw",
            padx=8,
            pady=8,
            relief="solid",
            borderwidth=1
        )
        self.linearised_info_label.pack(fill="both", expand=True)

        # Constants section — hidden until _linearise_equation reveals it;
        # populated by _update_constants_post_linearisation to show only the
        # constants that cannot be derived from the graph (Section 3.2.1,
        # Manipulate user values if required).
        self.constants_frame = tk.LabelFrame(
            panel,
            text="Required Constants",
            bg="white",
            fg="#0f172a",
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=10
        )
        self.constant_entries: dict = {}

        # Units section — hidden until linearisation; populated by _update_units_input
        self.units_frame = tk.LabelFrame(
            panel,
            text="Measurement Units",
            bg="white",
            fg="#0f172a",
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=10
        )
        self.unit_entries: dict = {}

        # Generate graph button — hidden until linearisation; triggers generate_graph()
        self.generate_graph_button = tk.Button(
            panel,
            text="Generate Linear Graph",
            bg="#059669",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            cursor="hand2",
            command=self.generate_graph
        )

    def create_automated_panel(self, parent):
        """
        Build the scrollable Automated Model Selection panel (right column).

        Renders a card for each of the nine supported regression models and a
        'Generate Graph' button that navigates to AutomatedGraphResultsScreen,
        implementing the 'Automated' sub-component of Section 3.2.1 (Branch 3)
        and Algorithm 8 (Section 3.2.2 — automated model comparison via R²).
        """
        _, panel, _, _ = make_scrollable(
            parent,
            row=0,
            column=1,
            padx=(10, 0),
            bg="white",
            panel_kwargs={"padx": 20, "pady": 20},
        )

        tk.Label(
            panel,
            text="Automated Model Selection",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg="#0f172a"
        ).pack(anchor="w", pady=(0, 15))

        tk.Label(
            panel,
            text="Select a model to automatically fit your data",
            font=("Segoe UI", 9),
            bg="white",
            fg="#6b7280"
        ).pack(anchor="w", pady=(0, 20))

        # Model definitions — each entry maps to a model card created by _create_model_card
        models = [
            {"name": "Linear",      "equation": "y = mx + c",                      "description": "Straight line relationship",   "color": "#3b82f6"},
            {"name": "Quadratic",   "equation": "y = ax² + bx + c",                "description": "Parabolic curve",              "color": "#8b5cf6"},
            {"name": "Cubic",       "equation": "y = ax³ + bx² + cx + d",          "description": "S-shaped or cubic curve",      "color": "#ec4899"},
            {"name": "Exponential", "equation": "y = a·eᵇˣ",                       "description": "Growth or decay",              "color": "#f59e0b"},
            {"name": "Logarithmic", "equation": "y = a·ln(x) + b",                 "description": "Logarithmic relationship",     "color": "#10b981"},
            {"name": "Power",       "equation": "y = a·xᵇ",                        "description": "Power law relationship",       "color": "#06b6d4"},
            {"name": "Gaussian",    "equation": "y = a·e^(-(x-b)²/(2c²))",         "description": "Bell-shaped curve",            "color": "#6366f1"},
            {"name": "Logistic",    "equation": "y = L/(1 + e^(-k(x-x₀)))",        "description": "S-shaped growth curve",        "color": "#84cc16"},
            {"name": "Sinusoidal",  "equation": "y = a·sin(bx + c) + d",           "description": "Periodic oscillation",         "color": "#f43f5e"},
        ]

        for model in models:
            self._create_model_card(panel, model)

        # Bottom spacer keeps the generate button from sitting flush against the last card
        tk.Frame(panel, bg="white", height=20).pack()

        tk.Button(
            panel,
            text="Generate Graph",
            font=("Segoe UI", 11, "bold"),
            bg="#0f172a",
            fg="white",
            padx=30,
            pady=12,
            relief="flat",
            cursor="hand2",
            command=self._generate_automated_graph
        ).pack(fill="x", pady=(15, 0))

    def _create_model_card(self, parent, model: dict):
        """
        Render a single model card showing the model name, equation, and description.

        Each card is a rounded-corner-style Frame with a coloured left border strip
        that visually distinguishes models, matching the Screen 2 mockup in Section
        3.2.2 (User Interface).  Cards are purely informational — selection is
        implicit; clicking 'Generate Graph' passes all models to AutomatedGraphResultsScreen
        which runs Algorithm 8 to select the best fit.

        Args:
            parent: Parent widget to pack the card into.
            model:  Dict with keys 'name', 'equation', 'description', 'color'.
        """
        card = tk.Frame(
            parent,
            bg="#f8fafc",
            relief="solid",
            bd=1,
            highlightbackground="#e2e8f0",
            highlightthickness=1
        )
        card.pack(fill="x", pady=8)

        inner = tk.Frame(card, bg="#f8fafc", padx=15, pady=12)
        inner.pack(fill="both", expand=True)

        # Top row: coloured accent bar + model name
        top_row = tk.Frame(inner, bg="#f8fafc")
        top_row.pack(fill="x", pady=(0, 8))

        color_bar = tk.Frame(top_row, bg=model["color"], width=4, height=20)
        color_bar.pack(side="left", padx=(0, 10))
        color_bar.pack_propagate(False)

        tk.Label(
            top_row,
            text=model["name"],
            font=("Segoe UI", 12, "bold"),
            bg="#f8fafc",
            fg="#0f172a"
        ).pack(side="left")

        # Equation string shown in monospace for mathematical clarity
        equation_frame = tk.Frame(inner, bg="white", relief="flat", bd=1)
        equation_frame.pack(fill="x", pady=(0, 8))

        tk.Label(
            equation_frame,
            text=model["equation"],
            font=("Courier New", 11),
            bg="white",
            fg="#1e293b",
            padx=12,
            pady=8
        ).pack(anchor="w")

        tk.Label(
            inner,
            text=model["description"],
            font=("Segoe UI", 9),
            bg="#f8fafc",
            fg="#64748b",
            justify="left"
        ).pack(anchor="w")

    def _generate_automated_graph(self):
        """
        Validate data availability and navigate to AutomatedGraphResultsScreen.

        Implements the navigation step for the Automated pathway in Section 3.2.1
        (Branch 3 — Automated).  The actual model fitting (Algorithm 8, Section 3.2.2)
        is performed by AutomatedGraphResultsScreen once it has access to the InputData
        stored in ScreenManager.
        """
        if self.raw_data is None:
            messagebox.showwarning(
                "No Data",
                "Please go back and input your data first."
            )
            return

        self.manager.show(AutomatedGraphResultsScreen)

    def _on_search(self, event):
        """
        Update the results_box with equations matching the current search text.

        Bound to <KeyRelease> on the search entry.  Delegates to EquationLibrary.search()
        which performs a case-insensitive substring match on equation names and expressions,
        as described in Section 3.2.1 (Scientific Equation Selection sub-component).
        Skips the query if the placeholder text is still present.
        """
        query = self.search_entry.get()
        if query == self.search_placeholder:
            return

        results = self.library.search(query)
        self.results_box.delete(0, tk.END)
        for eq in results:
            self.results_box.insert(tk.END, f"{eq.name}             {eq.expression}")

    def _enter_custom_equation(self):
        """
        Open a Toplevel dialog for the user to enter an equation not in the library.

        Implements the 'Custom Equation' sub-branch of Section 3.2.1 (Branch 2).
        Parses the submitted string using _apply_greek_replacements() and a regex
        variable extractor, then constructs an Equation object with linearisation_type
        'custom' so downstream components handle it appropriately.  On success the
        dialog closes and the clickable equation canvas is refreshed.
        """
        dialog = tk.Toplevel(self)
        dialog.title("Enter Custom Equation")
        dialog.geometry("500x350")
        dialog.configure(bg="white")

        tk.Label(
            dialog,
            text="Enter Custom Equation",
            font=("Segoe UI", 14, "bold"),
            bg="white"
        ).pack(pady=(20, 10))

        tk.Label(
            dialog,
            text=(
                "Format: variable = expression\n"
                "Example: F = m*a  or  E = 0.5*m*v**2\n"
                "Use 'lambda' or 'λ' for lambda, 'mu' or 'μ' for mu"
            ),
            font=("Segoe UI", 9),
            bg="white",
            fg="#6b7280",
            justify="left"
        ).pack(pady=(0, 20))

        equation_entry = tk.Entry(dialog, font=("Segoe UI", 11))
        equation_entry.pack(fill="x", padx=40, pady=(0, 20))

        def submit():
            """
            Validate and parse the user-supplied equation string.

            Replaces Greek text with safe identifiers, extracts variable names via
            regex, assigns descriptions from _GREEK_DISPLAY_DESCRIPTIONS where
            available, and constructs the Equation object.  Displays a warning for
            equations with fewer than two variables or a parse error for malformed
            strings, consistent with the input validation requirements in Section 3.1.4.
            """
            equation_str = equation_entry.get().strip()
            if not equation_str or "=" not in equation_str:
                messagebox.showwarning("Invalid Equation", "Please enter a valid equation with '='")
                return

            # Substitute text Greek representations with display Unicode for readability
            equation_str = equation_str.replace("lambda", "λ").replace("Lambda", "λ")
            equation_str = equation_str.replace("mu", "μ").replace("sigma", "σ")
            equation_str = equation_str.replace("theta", "θ").replace("phi", "φ")
            equation_str = equation_str.replace("rho", "ρ")

            try:
                lhs_str, rhs_str = equation_str.split("=")
                all_vars: set = set()

                # Extract standard variable identifiers and Unicode Greek characters
                for part in [lhs_str, rhs_str]:
                    all_vars.update(re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', part))
                    all_vars.update(re.findall(r'[α-ωΑ-Ω]', part))

                # Remove function names that are not physical variables
                function_names = {
                    'exp', 'log', 'ln', 'sin', 'cos', 'tan', 'sqrt',
                    'abs', 'asin', 'acos', 'atan', 'sinh', 'cosh', 'tanh'
                }
                all_vars -= function_names

                if len(all_vars) < 2:
                    messagebox.showwarning(
                        "Invalid Equation",
                        "Equation must have at least 2 variables.\nFound: " + ", ".join(all_vars)
                    )
                    return

                # Build variable description map using _GREEK_DISPLAY_DESCRIPTIONS
                variables = {
                    var: _GREEK_DISPLAY_DESCRIPTIONS.get(var, var)
                    for var in all_vars
                }

                self.selected_equation = Equation(
                    "Custom Equation",
                    equation_str,
                    variables,
                    linearisation_type="custom"
                )

                self.selected_vars.clear()
                self.scientific_equation = ScientificEquation(equation_str)

                # Reset progressive-disclosure widgets before re-displaying equation
                self.linearised_display_frame.pack_forget()
                self.constants_frame.pack_forget()
                self.units_frame.pack_forget()
                self.generate_graph_button.pack_forget()

                self._display_clickable_equation()
                self._update_selected_vars_display()
                self._update_find_var_options()
                dialog.destroy()

            except Exception as e:
                messagebox.showerror(
                    "Parse Error",
                    f"Could not parse equation:\n{e}\n\nPlease check your equation format."
                )

        tk.Button(
            dialog,
            text="Add Equation",
            bg="#0f172a",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            cursor="hand2",
            command=submit
        ).pack(fill="x", padx=40, pady=20)

    def _select_equation(self, event):
        """
        Handle a listbox selection event: load the chosen Equation and refresh the UI.

        Searches the EquationLibrary for an exact name match on the selected row,
        resets the variable selection state, and re-draws the clickable equation canvas.
        Corresponds to the 'Scientific Equation Selection' sub-component in Section 3.2.1.
        """
        if not self.results_box.curselection():
            return

        index = self.results_box.curselection()[0]
        display_text = self.results_box.get(index)
        name = display_text.split("   ")[0].strip()

        # Locate the exact Equation object in the library using the name key
        for eq in self.library.search(name):
            if eq.name == name:
                self.selected_equation = eq
                break

        self.selected_vars.clear()
        self.scientific_equation = ScientificEquation(self.selected_equation.expression)

        # Hide post-linearisation widgets so they don't persist across equation changes
        self.linearised_display_frame.pack_forget()
        self.constants_frame.pack_forget()

        self._display_clickable_equation()
        self._update_selected_vars_display()
        self._update_find_var_options()

    def _display_clickable_equation(self):
        """
        Render the selected equation onto the canvas with variable tokens as buttons.

        Implements the 'Assign apt. x and y values' UI interaction from Section 3.2.1:
        each recognised variable is drawn as a clickable tk.Button (highlighted when
        selected) so the user can indicate which two quantities they measured.  Non-variable
        tokens (operators, numbers) are drawn as canvas text items.  The canvas is cleared
        and fully redrawn on every call so selection state is always consistent.
        """
        self.equation_canvas.delete("all")

        if not self.selected_equation:
            return

        expr = self.selected_equation.expression
        x_pos = 10
        y_pos = 30

        # Tokenise the expression, preserving operators, numbers, and multi-char identifiers
        pattern = r'([\s=+\-*/()^]+|[0-9.]+|[a-zA-Z_][a-zA-Z0-9_]*|[α-ωΑ-Ω]+)'
        tokens = re.findall(pattern, expr)

        for token in tokens:
            token_stripped = token.strip()
            if not token_stripped:
                continue

            if token_stripped in self.selected_equation.variables:
                # Render measured variables as interactive toggle buttons
                is_selected = token_stripped in self.selected_vars
                color    = "#3b82f6" if is_selected else "#6b7280"
                bg_color = "#dbeafe" if is_selected else "#f3f4f6"

                btn = tk.Button(
                    self.equation_canvas,
                    text=token_stripped,
                    font=("Segoe UI", 11, "bold"),
                    fg=color,
                    bg=bg_color,
                    relief="raised",
                    borderwidth=2,
                    cursor="hand2",
                    command=lambda v=token_stripped: self._toggle_variable(v)
                )

                btn_window = self.equation_canvas.create_window(x_pos, y_pos, anchor="w", window=btn)
                self.equation_canvas.update()
                bbox = self.equation_canvas.bbox(btn_window)
                x_pos = bbox[2] + 5
            else:
                # Render operators, numbers, and non-variable identifiers as plain text
                if token == ' ':
                    x_pos += 3
                    continue

                text_id = self.equation_canvas.create_text(
                    x_pos, y_pos,
                    text=token_stripped,
                    font=("Segoe UI", 12),
                    fill="#0f172a",
                    anchor="w"
                )
                bbox = self.equation_canvas.bbox(text_id)
                if bbox:
                    x_pos = bbox[2] + 3

    def _toggle_variable(self, var: str):
        """
        Toggle selection state of a variable in the clickable equation canvas.

        Enforces a maximum of two selected variables (one for each axis), which is
        the minimum required to produce a two-variable linearised form as described
        in Section 3.2.1 (Assign apt. x and y values).  Warns the user before
        preventing a third selection.

        Args:
            var: Variable symbol string (e.g., 'I', 'λ') whose state is being toggled.
        """
        if var in self.selected_vars:
            self.selected_vars.remove(var)
        else:
            if len(self.selected_vars) >= 2:
                messagebox.showwarning(
                    "Selection Limit",
                    "You can only select 2 variables to measure.\nDeselect one first."
                )
                return
            self.selected_vars.add(var)

        # Redraw canvas and update dependent UI elements to reflect new selection state
        self._display_clickable_equation()
        self._update_selected_vars_display()
        self._update_find_var_options()

    def _update_selected_vars_display(self):
        """
        Refresh the colour-coded label that summarises the current variable selection.

        Uses a traffic-light colour scheme:
          - Amber (#fffbeb): no variables selected — prompts user to click.
          - Yellow (#fef3c7): one variable selected — prompts for second.
          - Green (#d1fae5):  two variables selected — ready to linearise.

        Displayed text lists each variable symbol and its physical meaning from
        self.selected_equation.variables, satisfying the usability requirement in
        Section 3.1.4 (the UI must clearly communicate analysis state).
        """
        if len(self.selected_vars) == 0:
            text = "Click on variables in the equation above that you have measured in your experiment"
            bg, fg = "#fffbeb", "#92400e"

        elif len(self.selected_vars) == 1:
            var = next(iter(self.selected_vars))
            meaning = self.selected_equation.variables[var]
            text = f"Selected: {var} ({meaning})\n\nSelect one more variable"
            bg, fg = "#fef3c7", "#92400e"

        else:
            lines = [f"  • {var} ({self.selected_equation.variables[var]})"
                     for var in sorted(self.selected_vars)]
            text = "Selected variables:\n" + "\n".join(lines)
            bg, fg = "#d1fae5", "#065f46"

        self.selected_vars_display.config(text=text, bg=bg, fg=fg)

    def _update_constants_post_linearisation(self):
        """
        Rebuild the constants input section after linearisation.

        Only asks for constants that cannot be determined from the graph itself —
        for example, in I = I₀·exp(−μx) both μ and I₀ can be read from the
        gradient and intercept respectively, so no constants are required.
        This mirrors the 'Manipulate user values if required' guard described in
        Section 3.2.1.

        For exponential equations all non-measured variables are treated as
        findable from the graph structure; for other equation types only the
        explicitly selected and find variables are excluded.
        """
        # Clear stale widgets from any previous linearisation
        for widget in self.constants_frame.winfo_children():
            widget.destroy()

        if not self.selected_equation:
            return

        find_var = self.find_var.get()

        # Variables derivable from the graph — no entry needed for these
        findable_from_graph: set = set()
        if self.selected_equation.linearisation_type == "exponential":
            findable_from_graph = {
                v for v in self.selected_equation.variables
                if v not in self.selected_vars
            }

        # Collect variables excluded from the constant-entry requirement
        excluded = self.selected_vars.copy()
        if find_var and find_var != "None":
            excluded.add(find_var)
        excluded.update(findable_from_graph)

        remaining = [
            v for v in self.selected_equation.variables
            if v not in excluded
        ]

        self.constant_entries.clear()

        if not remaining:
            # Confirmation banner — no constants needed
            tk.Label(
                self.constants_frame,
                text="✓ No additional constants needed\n\nAll unknowns can be determined from the graph!",
                fg="#065f46",
                bg="#d1fae5",
                font=("Segoe UI", 9),
                justify="left",
                padx=10,
                pady=10,
                relief="solid",
                borderwidth=1
            ).pack(fill="x")
            return

        tk.Label(
            self.constants_frame,
            text="Enter values for these constants:",
            fg="#0f172a",
            bg="white",
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", pady=(0, 5))

        for var in remaining:
            row = tk.Frame(self.constants_frame, bg="white")
            row.pack(fill="x", pady=3)

            meaning = self.selected_equation.variables[var]
            tk.Label(row, text=f"{var}:", width=4, anchor="w", bg="white",
                     font=("Segoe UI", 10, "bold")).pack(side="left")

            entry = tk.Entry(row, width=15)
            entry.pack(side="left", padx=(0, 10))

            tk.Label(row, text=meaning, fg="#6b7280", bg="white",
                     font=("Segoe UI", 9)).pack(side="left", fill="x", expand=True)

            # Pre-fill recognised physical constants (e.g. e, h, c) from CONSTANTS dict
            default = self._default_constant(var)
            if default is not None:
                entry.insert(0, str(default))

            self.constant_entries[var] = entry

    def _update_units_input(self, x_var: str, y_var: str):
        """
        Rebuild the measurement units input section after linearisation.

        Renders one row per measured axis variable with an Entry pre-filled with
        'SI units'.  The values entered here are stored in equation_info['measurement_units']
        and forwarded to GradientAnalysis.py for display and potential unit conversion
        on Screen 4 (Section 3.2.2, User Interface — Screen 4, Section 2: Calculated
        Unknown Value).

        Args:
            x_var: Symbol name of the variable assigned to the x-axis.
            y_var: Symbol name of the variable assigned to the y-axis.
        """
        for widget in self.units_frame.winfo_children():
            widget.destroy()

        if not self.selected_equation:
            return

        tk.Label(
            self.units_frame,
            text="Enter the units you measured your variables in:",
            fg="#0f172a",
            bg="white",
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", pady=(0, 10))

        self.unit_entries.clear()

        for var in [x_var, y_var]:
            row = tk.Frame(self.units_frame, bg="white")
            row.pack(fill="x", pady=5)

            meaning = self.selected_equation.variables.get(var, var)
            tk.Label(row, text=f"{var}:", width=6, anchor="w", bg="white",
                     font=("Segoe UI", 10, "bold")).pack(side="left")

            entry = tk.Entry(row, width=20)
            entry.pack(side="left", padx=(0, 10))
            entry.insert(0, "SI units")

            tk.Label(row, text=f"({meaning})", fg="#6b7280", bg="white",
                     font=("Segoe UI", 9)).pack(side="left", fill="x", expand=True)

            self.unit_entries[var] = entry

        # Instructional note about non-SI units
        tk.Label(
            self.units_frame,
            text=(
                "💡 If your units don't match SI units, the system will help convert them.\n"
                "Example: If you measured in cm, enter 'cm' and we'll convert to m."
            ),
            fg="#059669",
            bg="#f0fdf4",
            font=("Segoe UI", 8),
            justify="left",
            padx=8,
            pady=6,
            relief="solid",
            borderwidth=1
        ).pack(fill="x", pady=(10, 0))

    def _update_find_var_options(self):
        """
        Refresh the 'Value to Find' combobox with variables not currently being measured.

        Only unmeasured variables can be solved for from the gradient or intercept,
        consistent with the 'Value to Find' sub-component of Section 3.2.1 (Branch 3).
        Falls back gracefully if no equation is selected.
        """
        if not self.selected_equation:
            return

        available = [
            v for v in self.selected_equation.variables
            if v not in self.selected_vars
        ]
        self.find_var.config(values=["None"] + available)
        self.find_var.set("None")

    def _default_constant(self, symbol: str) -> Optional[float]:
        """
        Return the pre-defined value for a recognised physical constant symbol.

        Delegates to the CONSTANTS dict imported from Equations.py, which maps
        symbols such as 'e', 'h', 'c', 'k_B' to their SI values.  Returns None
        if the symbol is not a known constant, leaving the entry field blank for
        the user to fill in.

        Args:
            symbol: Variable symbol string from the selected equation.

        Returns:
            float value if symbol is a known constant, otherwise None.
        """
        return CONSTANTS.get(symbol)

    def _linearise_equation(self):
        """
        Linearise the selected equation and update the UI with the result.

        Main handler for the 'Linearise Equation' button.  Implements the full
        Algorithm 2 pipeline from Section 3.2.2:

          1. Validate that an equation and exactly two variables are selected.
          2. Parse the equation string into a SymPy Eq using _apply_greek_replacements.
          3. Attempt linearisation with both (var1, var2) and (var2, var1) orderings.
          4. Score each ordering via score_result() and select the better one.
          5. Apply axis transformations to the InputData via DataTransformer.
          6. Store the linearised ScientificEquation and transformed data.
          7. Display the result and reveal the constants, units, and generate buttons.

        Raises a user-facing error dialog if the equation cannot be parsed or if
        the data transformation fails (e.g., log of a negative value).
        """
        if not self.selected_equation:
            messagebox.showwarning("No Equation", "Please select an equation first.")
            return

        if len(self.selected_vars) != 2:
            messagebox.showwarning(
                "Invalid Selection",
                "Please select exactly 2 variables to measure by clicking on them in the equation."
            )
            return

        var1, var2 = list(self.selected_vars)

        find_sym = self.find_var.get()
        if find_sym == "None":
            find_sym = None

        # Parse the equation string into a SymPy Eq
        try:
            expr_str = self.selected_equation.expression

            # Normalise notation to SymPy-compatible forms before parsing
            expr_str = expr_str.replace("^", "**")    # caret → double-star power operator
            expr_str = expr_str.replace("₀", "0")     # Unicode subscript zero → ASCII
            expr_str = _apply_greek_replacements(expr_str)

            # Remove any remaining Unicode numeric subscripts (₁, ₂, …)
            expr_str = re.sub(r'([A-Za-z])([₀₁₂₃₄₅₆₇₈₉])', r'\1', expr_str)

            lhs_str, rhs_str = expr_str.split("=")

            # Populate local_dict with SymPy functions and all equation variables as Symbols
            local_dict = {
                'e': sp.E,   'pi': sp.pi,   'exp': sp.exp,  'log': sp.log,
                'ln': sp.log, 'sin': sp.sin, 'cos': sp.cos,  'tan': sp.tan,
                'sqrt': sp.sqrt,
            }

            for var in self.selected_equation.variables:
                clean_var = var.replace("₀", "0").replace("₁", "1")
                local_dict[clean_var] = sp.Symbol(var)

            # Ensure Greek aliases are available in the parser namespace
            local_dict.update({
                'mu': sp.Symbol('μ'),    'lambda_': sp.Symbol('λ'),
                'sigma': sp.Symbol('σ'), 'rho': sp.Symbol('ρ'),
                'theta': sp.Symbol('θ'), 'phi': sp.Symbol('φ'),
            })

            lhs = parse_expr(lhs_str.strip(), transformations=TRANSFORMS, local_dict=local_dict)
            rhs = parse_expr(rhs_str.strip(), transformations=TRANSFORMS, local_dict=local_dict)
            equation = sp.Eq(lhs, rhs)

        except Exception as e:
            messagebox.showerror(
                "Parse Error",
                f"Could not parse equation.\n\nTechnical details: {str(e)}\n\n"
                "Please try a different equation or contact support."
            )
            return

        # Try both variable orderings; pick the one with the lower heuristic score
        result1 = self._attempt_linearisation(equation, var1, var2, find_sym)
        result2 = self._attempt_linearisation(equation, var2, var1, find_sym)

        def score_result(result) -> float:
            """
            Heuristic scoring function: lower score indicates a more suitable linearisation.

            Penalises orderings where both axes are transformed (+10) or where the
            independent variable ends up on the Y-axis (+3), and rewards orderings
            where only the Y-axis is transformed (−1) and recognised independent
            variables are on the X-axis (−2 each), following standard physics
            convention as cited in Section 3.2.1 (Assign apt. x and y values).

            Args:
                result: Tuple from _attempt_linearisation or None.

            Returns:
                float score (inf if result is None).
            """
            if not result:
                return float('inf')

            _, x_var, y_var, x_transform, y_transform, _, _ = result

            x_is_transformed = x_transform != x_var
            y_is_transformed = y_transform != y_var

            score = 0
            if x_is_transformed and y_is_transformed:
                score += 10   # both axes transformed — least preferred
            elif not x_is_transformed and not y_is_transformed:
                score += 0    # no transformation — ideal for already-linear equations
            else:
                score += 2    # one axis transformed — acceptable for non-linear equations

            # Prefer Y-axis transformation over X-axis (e.g., ln(I) vs x is cleaner)
            if y_is_transformed:
                score -= 1
            if x_is_transformed:
                score += 2

            # Physics convention: independent variables belong on X, dependent on Y
            independent_vars = {'t', 'x', 's', 'r', 'd', 'f', 'λ', 'θ', 'φ', 'ω', 'I', 'h', 'L', 'A'}
            dependent_vars   = {'v', 'V', 'F', 'E', 'p', 'A', 'N', 'Q', 'P', 'T', 'W', 'R'}

            if x_var in independent_vars: score -= 2
            if y_var in dependent_vars:   score -= 2
            if x_var in dependent_vars:   score += 3
            if y_var in independent_vars: score += 3

            return score

        # Select the variable ordering that produces the better linearised form
        result = result1 if score_result(result1) <= score_result(result2) else result2

        if not result:
            messagebox.showinfo(
                "Linearisation Result",
                "This equation is already in linear form or doesn't require transformation."
            )
            self._display_linear_result(equation, var1, var2, find_sym)
            return

        linearised_eq, x_var, y_var, x_transform, y_transform, grad_meaning, int_meaning = result

        # Apply the derived transforms to the numerical data via DataTransformer
        if self.data_transformer is not None:
            try:
                self.transformed_data = self.data_transformer.transform_for_linearisation(
                    x_transform=x_transform,
                    y_transform=y_transform,
                    x_var=x_var,
                    y_var=y_var
                )
                # Deposit transformed data into ScreenManager for LinearGraphResultsScreen
                self.manager.set_data(self.transformed_data)

            except ValueError as e:
                messagebox.showerror(
                    "Transformation Error",
                    f"Could not transform data: {str(e)}\n\n"
                    "Please check your data values are suitable for this transformation."
                )
                return

        # Persist the symbolic linearisation result in the ScientificEquation object
        self.scientific_equation.linearised_equation = str(linearised_eq)
        self.scientific_equation.x = x_transform   # e.g., "x" or "ln(x)"
        self.scientific_equation.y = y_transform   # e.g., "ln(I)"
        self.scientific_equation.m_meaning = grad_meaning
        self.scientific_equation.c_meaning = int_meaning

        # Render the linearised equation and plotting instructions
        self._display_linear_result(
            linearised_eq, x_var, y_var, find_sym,
            x_transform, y_transform, grad_meaning, int_meaning
        )

        # Reveal the post-linearisation UI sections progressively
        self.constants_frame.pack(fill="x", pady=(10, 10))
        self._update_constants_post_linearisation()

        self.units_frame.pack(fill="x", pady=(10, 10))
        self._update_units_input(x_var, y_var)

        self.generate_graph_button.pack(fill="x", pady=(15, 0))

    def generate_graph(self):
        """
        Build the equation_info dict and navigate to LinearGraphResultsScreen.

        Called when the user clicks 'Generate Linear Graph'.  Collects gradient and
        intercept metadata, user-entered constants, and measurement units, then stores
        them in ScreenManager via set_equation_info() so Screen 3a and Screen 4 can
        display and interpret the regression output correctly (Section 3.2.2, User
        Interface — Screen 4, Section 1: Selected Equation).
        """
        if self.transformed_data is None:
            messagebox.showwarning(
                "No Linearised Data",
                "Please linearise an equation first before generating the graph."
            )
            return

        if self.selected_equation:
            gradient_var, gradient_units   = self._extract_coefficient_info("gradient")
            intercept_var, intercept_units = self._extract_coefficient_info("intercept")

            find_var = self.find_var.get() if self.find_var.get() != "None" else None

            # Collect user-entered constant values, skipping blank or invalid entries
            constants: dict = {}
            for var, entry in self.constant_entries.items():
                value_str = entry.get().strip()
                if value_str:
                    try:
                        constants[var] = float(value_str)
                    except ValueError:
                        pass  # invalid constant entries are silently skipped

            # Collect non-SI unit strings, ignoring the placeholder 'SI units' value
            measurement_units: dict = {
                var: entry.get().strip()
                for var, entry in self.unit_entries.items()
                if entry.get().strip() and entry.get().strip() != "SI units"
            }

            equation_info = {
                'name':               self.selected_equation.name,
                'equation_expression': self.selected_equation.expression if self.selected_equation else '',
                'gradient_variable':  gradient_var,
                'gradient_units':     gradient_units,
                'intercept_variable': intercept_var,
                'intercept_units':    intercept_units,
                'find_variable':      find_var,
                'constants':          constants,
                'measurement_units':  measurement_units,
                # Full symbolic expressions for gradient and intercept (e.g., "-μ")
                'gradient_meaning':   self.scientific_equation.m_meaning if self.scientific_equation else gradient_var,
                'intercept_meaning':  self.scientific_equation.c_meaning if self.scientific_equation else intercept_var,
            }
        else:
            # Fallback used when a custom equation has not been formally processed
            equation_info = {
                'name': 'Custom Linear Equation',
                'equation_expression': '',
                'gradient_variable':  'm',
                'gradient_units':     '',
                'intercept_variable': 'c',
                'intercept_units':    '',
                'find_variable':      None,
                'constants':          {},
                'measurement_units':  {},
                'gradient_meaning':   'm',
                'intercept_meaning':  'c',
            }

        self.manager.set_equation_info(equation_info)
        self.manager.show(LinearGraphResultsScreen)

    def _extract_coefficient_info(self, role: str) -> Tuple[str, str]:
        """
        Return the variable name and unit string for either the gradient or intercept.

        Consolidates the logic previously split across two near-identical methods
        (_extract_gradient_info, _extract_intercept_info).  Reads the symbolic
        meaning stored in ScientificEquation after linearisation, falls back to a
        generic label when no equation is selected, and applies heuristic unit
        inference for common equation types (decay → s⁻¹, attenuation → m⁻¹).

        Used by generate_graph() to populate the equation_info dict passed to Screen 4
        (Section 3.2.2, User Interface — Screen 4, Section 1: Selected Equation).

        Args:
            role: Either "gradient" or "intercept".

        Returns:
            Tuple of (variable_name, unit_string).
        """
        if not self.selected_equation:
            return ('m', '') if role == "gradient" else ('c', '')

        if role == "gradient":
            var = (self.scientific_equation.m_meaning
                   if self.scientific_equation and self.scientific_equation.m_meaning
                   else 'gradient')

            # Heuristic unit inference for common linear physics equations
            units = ''
            if 'decay' in self.selected_equation.name.lower() or 'λ' in var:
                units = 's⁻¹'
            elif 'attenuation' in self.selected_equation.name.lower() or 'μ' in var:
                units = 'm⁻¹'
            return var, units

        else:  # intercept
            var = (self.scientific_equation.c_meaning
                   if self.scientific_equation and self.scientific_equation.c_meaning
                   else 'intercept')
            return var, ''   # intercept units are typically dimensionless for log transforms

    def _identify_xy_vars(self) -> Tuple[str, str]:
        """
        Return the x and y variable names from the current selection.

        Simple helper that converts the selected_vars set (unordered) into a
        deterministic (x, y) tuple, used by _attempt_linearisation before the
        scoring step picks the preferred ordering.  Raises ValueError if fewer
        than two variables are selected, which should not occur in normal flow
        since _linearise_equation validates selection count first.

        Returns:
            Tuple of (x_variable_name, y_variable_name).
        """
        vars_list = list(self.selected_vars)
        if len(vars_list) < 2:
            raise ValueError("Need at least 2 variables selected")
        return vars_list[0], vars_list[1]

    def get_current_data(self) -> InputData:
        """
        Return the data currently in use for analysis.

        Returns transformed data if a linearisation has been applied, otherwise
        the original raw InputData.  Used by the 'Fit other Models' workflow
        (Section 3.2.1, Branch 4) to determine the starting dataset for re-analysis.
        """
        return self.transformed_data if self.transformed_data is not None else self.raw_data

    def revert_to_raw_data(self):
        """
        Discard transformed data and restore the raw InputData in ScreenManager.

        Supports the 'Fit other Models' sub-component in Section 3.2.1 (Branch 4)
        by resetting the transformation state so the user can re-run linearisation
        with a different equation without re-importing their data.  Notifies the
        user with an informational dialog on success.
        """
        if self.data_transformer is not None:
            self.transformed_data = None
            self.manager.set_data(self.raw_data)
            messagebox.showinfo(
                "Data Reverted",
                "Data has been reverted to original raw measurements."
            )

    def _attempt_linearisation(
            self,
            equation: sp.Eq,
            x_var: str,
            y_var: str,
            find_var: Optional[str]
    ) -> Optional[tuple]:
        """
        Attempt to linearise equation with the given x/y variable assignment.

        Substitutes the user-selected variables into generic SymPy symbols x and y,
        calls the static linearise() method (Algorithm 2), then reverses the
        substitution to restore original symbol names in the displayed result.
        Called twice by _linearise_equation with swapped variable orderings so
        score_result() can compare both candidates.

        Args:
            equation: SymPy Eq parsed from the selected equation expression.
            x_var:    Symbol name to treat as the independent (x) variable.
            y_var:    Symbol name to treat as the dependent (y) variable.
            find_var: Optional variable to solve for; passed to _identify_meanings.

        Returns:
            Tuple of (linearised_eq, x_var, y_var, x_transform, y_transform,
            grad_meaning, int_meaning), or None if linearisation fails.
        """
        x_temp, y_temp = sp.symbols("x y")

        symbol_map = {sp.Symbol(x_var): x_temp, sp.Symbol(y_var): y_temp}
        try:
            mapped_eq = equation.subs(symbol_map)
        except Exception:
            return None

        try:
            linearised = self.linearise(mapped_eq)
        except Exception:
            return None

        # Reverse substitution so original symbols appear in the displayed equation
        reverse_map = {x_temp: sp.Symbol(x_var), y_temp: sp.Symbol(y_var)}
        linearised_with_original_symbols = linearised.subs(reverse_map)

        x_transform, y_transform = self._identify_transforms(linearised, x_var, y_var)
        grad_meaning, int_meaning = self._identify_meanings(
            linearised, self.selected_equation, x_var, y_var, find_var
        )

        return (
            linearised_with_original_symbols,
            x_var, y_var,
            x_transform, y_transform,
            grad_meaning, int_meaning
        )

    def _identify_transforms(self, linearised_eq: sp.Eq, x_var: str, y_var: str) -> Tuple[str, str]:
        """
        Inspect a linearised SymPy equation to determine axis transformation labels.

        Analyses the LHS for y-axis transforms (log, power) and the RHS for x-axis
        transforms (log, reciprocal, power), returning strings such as "ln(I)" or
        "1/λ" that are used as axis labels in the graph output (x_label / y_label in
        the Key Variables table, Section 3.2.2) and passed to DataTransformer.

        Args:
            linearised_eq: SymPy Eq in the generic x/y symbol space.
            x_var:         Original x variable name for label construction.
            y_var:         Original y variable name for label construction.

        Returns:
            Tuple of (x_transform_label, y_transform_label).
        """
        x_temp, y_temp = sp.symbols("x y")

        x_transform = x_var  # default: no transformation applied
        y_transform = y_var

        lhs = linearised_eq.lhs
        rhs = linearised_eq.rhs

        # Detect y-axis log transform from LHS structure
        if lhs.has(sp.log):
            if lhs == sp.log(y_temp) or lhs.func == sp.log:
                y_transform = f"ln({y_var})"
        elif lhs != y_temp and lhs.has(y_temp) and not lhs.has(y_temp ** 2):
            # LHS has a coefficient multiplying y (e.g., e*y) — show full expression as axis label
            try:
                y_transform = str(lhs.subs(y_temp, sp.Symbol(y_var)))
            except Exception:
                y_transform = y_var

        # Detect power transforms on y from LHS (y², y³, etc.)
        if lhs == y_temp ** 2 or lhs.has(y_temp ** 2):
            y_transform = f"{y_var}²"
        elif lhs == y_temp ** 3 or lhs.has(y_temp ** 3):
            y_transform = f"{y_var}³"

        # Detect x-axis log transform from RHS
        if rhs.has(sp.log):
            for arg in sp.preorder_traversal(rhs):
                if isinstance(arg, sp.log) and arg.has(x_temp):
                    x_transform = f"ln({x_var})"
                    break

        # Detect x-axis power transforms (x², x³, x⁴) — but not reciprocal
        if rhs.has(x_temp ** 2) and not rhs.has(1 / x_temp):
            x_transform = f"{x_var}²"
        elif rhs.has(x_temp ** 3):
            x_transform = f"{x_var}³"
        elif rhs.has(x_temp ** 4):
            x_transform = f"{x_var}⁴"

        # Detect reciprocal transform (1/x) — checked last to take precedence over powers
        if rhs.has(1 / x_temp):
            x_transform = f"1/{x_var}"

        return x_transform, y_transform

    def _identify_meanings(
            self,
            linearised_eq: sp.Eq,
            original_eq,
            x_var: str,
            y_var: str,
            find_var: Optional[str]
    ) -> Tuple[str, str]:
        """
        Extract the physical meanings of the gradient and intercept from a linearised equation.

        Parses the RHS of the SymPy Eq to identify the coefficient of x (gradient) and
        the constant term (intercept), converting them back to original symbols for
        readability.  Handles reciprocal equations (V = hc/(eλ) → gradient = hc/e) by
        multiplying the RHS by x and simplifying.  Falls back to transform_info metadata
        for exponential equations where SymPy's polynomial extraction may not apply.

        The returned strings populate the 'Gradient represents' and 'Y-intercept
        represents' fields in the plotting instructions panel (Section 3.2.2, User
        Interface — Screen 2) and are stored in ScientificEquation.m_meaning /
        c_meaning for forwarding to Screen 4.

        Args:
            linearised_eq: SymPy Eq (in generic x/y symbols) from _attempt_linearisation.
            original_eq:   The selected Equation object for type and metadata access.
            x_var:         Original x variable name.
            y_var:         Original y variable name.
            find_var:      Optional variable the user wants to solve for.

        Returns:
            Tuple of (gradient_meaning_str, intercept_meaning_str).
        """
        x_temp, y_temp = sp.symbols("x y")

        rhs = linearised_eq.rhs
        rhs_expanded = sp.expand(rhs)

        try:
            if rhs.has(1 / x_temp):
                # Reciprocal form: gradient = everything that multiplies 1/x
                try:
                    grad_coeff = rhs.coeff(1 / x_temp, 1)
                    if not grad_coeff:
                        grad_coeff = sp.simplify(rhs * x_temp)
                except Exception:
                    try:
                        rhs_fraction = sp.together(rhs)
                        numer, denom = sp.fraction(rhs_fraction)
                        if x_temp in denom.free_symbols:
                            grad_coeff = sp.simplify(numer / (denom / x_temp))
                        else:
                            grad_coeff = sp.simplify(rhs * x_temp)
                    except Exception:
                        grad_coeff = sp.simplify(rhs * x_temp)

                const_term = sp.Integer(0)   # reciprocal equations carry no constant term
            else:
                # Standard linear form: extract coefficient of x and constant term
                grad_coeff  = rhs_expanded.coeff(x_temp, 1) or sp.Integer(0)
                const_term  = rhs_expanded.coeff(x_temp, 0) or sp.Integer(0)

            # Substitute generic symbols back to original variable names for display
            reverse_map = {x_temp: sp.Symbol(x_var), y_temp: sp.Symbol(y_var)}
            grad_coeff_original = grad_coeff.subs(reverse_map)  if grad_coeff  != 0 else grad_coeff
            const_term_original = const_term.subs(reverse_map)  if const_term  != 0 else const_term

            # Format gradient meaning as a fraction string where appropriate
            if grad_coeff_original != 0:
                grad_simplified = sp.simplify(grad_coeff_original)

                if isinstance(grad_simplified, sp.Mul):
                    numer_factors = []
                    denom_factors = []
                    for factor in sp.Mul.make_args(grad_simplified):
                        if isinstance(factor, sp.Pow) and factor.exp < 0:
                            denom_factors.append(factor.base)
                        else:
                            numer_factors.append(factor)

                    if denom_factors:
                        numer_str = '*'.join(str(f) for f in numer_factors) if numer_factors else '1'
                        denom_str = '*'.join(str(f) for f in denom_factors)
                        grad_meaning = f"{numer_str}/{denom_str}"
                    else:
                        grad_meaning = str(grad_simplified)
                else:
                    grad_meaning = str(grad_simplified)

                # Normalise formatting: caret notation and collapsed whitespace
                grad_meaning = grad_meaning.replace('**', '^')
                grad_meaning = " ".join(grad_meaning.split())
            else:
                grad_meaning = "0"

            if const_term_original != 0:
                int_meaning = str(sp.simplify(const_term_original)).replace('**', '^')
                int_meaning = " ".join(int_meaning.split())
            else:
                int_meaning = "0"

            # For exponential equations, prefer the pre-computed human-readable metadata
            if original_eq.linearisation_type == "exponential" and original_eq.transform_info:
                grad_meaning = original_eq.transform_info.get("gradient_meaning",  grad_meaning)
                int_meaning  = original_eq.transform_info.get("intercept_meaning", int_meaning)

            # Annotate if the find variable appears in gradient or intercept expression
            if find_var:
                if find_var in str(grad_coeff_original):
                    grad_meaning += f" (contains {find_var})"
                if find_var in str(const_term_original):
                    int_meaning  += f" (contains {find_var})"

            return grad_meaning, int_meaning

        except Exception as e:
            # Graceful fallback: return generic labels and log the exception for debugging
            print(f"Error in _identify_meanings: {e}")
            grad_meaning = "gradient"
            int_meaning  = "y-intercept"

            if original_eq.linearisation_type == "exponential" and original_eq.transform_info:
                grad_meaning = original_eq.transform_info.get("gradient_meaning", "gradient")
                int_meaning  = original_eq.transform_info.get("intercept_meaning", "y-intercept")

            if find_var:
                int_meaning += f" (can be used to find {find_var})"

            return grad_meaning, int_meaning

    def _display_linear_result(
            self,
            linearised_eq: sp.Eq,
            x_var: str,
            y_var: str,
            find_var: Optional[str] = None,
            x_transform: Optional[str] = None,
            y_transform: Optional[str] = None,
            grad_meaning: Optional[str] = None,
            int_meaning: Optional[str] = None
    ):
        """
        Reveal the linearised result panel and populate it with equation and instructions.

        Called by _linearise_equation after a successful linearisation.  Displays the
        pretty-printed SymPy equation string and a multi-line 'Plotting Instructions'
        block listing the axis assignments and physical meanings of the gradient and
        intercept, as required by Section 3.2.2 (User Interface — Screen 2, Linearised
        Form panel).

        Args:
            linearised_eq: SymPy Eq to display (pretty-printed via sp.pretty).
            x_var:         Original x variable symbol.
            y_var:         Original y variable symbol.
            find_var:      Optional variable being solved for; appended to instructions.
            x_transform:   Axis label for x (e.g., "ln(t)"); defaults to x_var.
            y_transform:   Axis label for y (e.g., "ln(I)"); defaults to y_var.
            grad_meaning:  Physical meaning of the gradient; defaults to "gradient".
            int_meaning:   Physical meaning of the intercept; defaults to "y-intercept".
        """
        self.linearised_display_frame.pack(fill="both", expand=True, pady=(10, 15))

        self.linearised_equation_label.config(text=sp.pretty(linearised_eq, use_unicode=True))

        # Apply defaults for any unspecified display strings
        x_transform  = x_transform  or x_var
        y_transform  = y_transform  or y_var
        grad_meaning = grad_meaning or "gradient"
        int_meaning  = int_meaning  or "y-intercept"

        x_meaning = self.selected_equation.variables.get(x_var, x_var)
        y_meaning = self.selected_equation.variables.get(y_var, y_var)

        info_lines = [
            "Plotting Instructions:\n",
            f"📊 X-axis: {x_transform}",
            f"   ({x_meaning})\n",
            f"📊 Y-axis: {y_transform}",
            f"   ({y_meaning})\n",
            f"📈 Gradient represents: {grad_meaning}\n",
            f"📍 Y-intercept represents: {int_meaning}",
        ]
        if find_var:
            info_lines.append(f"\n\n🎯 You can find {find_var} from the graph")

        self.linearised_info_label.config(text="\n".join(info_lines))

    @staticmethod
    def linearise(equation: sp.Eq) -> sp.Eq:
        """
        Transform a SymPy equation into y = mx + c (or ln(y) = mx + c) linear form.

        Implements Algorithm 2 from Section 3.2.2.  The method operates in the generic
        x/y symbol space so it can be reused for any variable assignment without
        needing to know the original physical symbol names.

        Handles four equation structures:
          1. Already linear (degree ≤ 1 in x) — returns as-is or solves for y.
          2. Exponential (contains sp.exp) — applies ln to both sides.
          3. Non-linear polynomial — isolates y by solving, then re-checks linearity.
          4. Unrecognised — returns the equation unchanged as a safe fallback.

        Args:
            equation: SymPy Eq (or expression) in the generic x/y symbol space.

        Returns:
            Linearised SymPy Eq, or the original equation if no transform applies.
        """
        x, y = sp.symbols("x y")

        # Accept bare expressions as well as Eq objects
        if not isinstance(equation, sp.Eq):
            expr = equation
            if y in expr.free_symbols:
                equation = sp.Eq(y, expr) if (expr.is_Add or expr.is_Mul or expr.is_Pow) else sp.Eq(expr, 0)
            else:
                equation = sp.Eq(y, expr)

        lhs, rhs = equation.lhs, equation.rhs

        # Identify which side contains y
        if y in lhs.free_symbols and y not in rhs.free_symbols:
            y_side, expr_side = lhs, rhs
        elif y in rhs.free_symbols and y not in lhs.free_symbols:
            y_side, expr_side = rhs, lhs
        else:
            return equation   # y on both sides or absent — cannot linearise

        # Already linear: degree ≤ 1 in x
        if expr_side.is_polynomial(x) and sp.degree(expr_side, x) <= 1:
            if y_side == y:
                return equation   # already in y = mx + c form
            try:
                solved = sp.solve(equation, y)
                if solved:
                    return sp.Eq(y, solved[0])
            except Exception:
                pass
            return sp.Eq(y_side, expr_side)

        # Non-linear with y not isolated — solve for y before attempting transforms
        if y_side != y:
            try:
                solved = sp.solve(equation, y)
                if solved:
                    expr_side = solved[0]
                    y_side    = y
            except Exception:
                pass

        # Exponential: apply ln to linearise y = A·exp(kx) → ln(y) = kx + ln(A)
        if expr_side.has(sp.exp):
            exp_terms = [t for t in sp.preorder_traversal(expr_side) if isinstance(t, sp.exp)]
            if exp_terms:
                exp_term = exp_terms[0]
                try:
                    coefficient = sp.simplify(expr_side / exp_term)
                    target = y_side if y_side == y else y_side
                    return sp.Eq(sp.log(target), sp.log(coefficient) + exp_term.args[0])
                except Exception:
                    pass

        return sp.Eq(y_side, expr_side)   # fallback: return equation unchanged

    def _clear_placeholder(self, event):
        """
        Clear the placeholder text when the search entry gains focus.

        Part of the placeholder text pattern used by the equation search box.
        Resets text colour to the active foreground to signal editable state.
        """
        if self.search_entry.get() == self.search_placeholder:
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg="#0f172a")

    def _restore_placeholder(self, event):
        """
        Restore the placeholder text when the search entry loses focus while empty.

        Paired with _clear_placeholder to maintain the greyed-out hint text that
        guides users before they type a query, satisfying the usability requirement
        in Section 3.1.4 (the interface must clearly indicate interactive elements).
        """
        if not self.search_entry.get().strip():
            self.search_entry.insert(0, self.search_placeholder)
            self.search_entry.config(fg="#9ca3af")


if __name__ == "__main__":
    """
    Standalone launch for isolated development and manual testing of Screen 2.

    Mirrors the __main__ pattern in LinMain.py (Section 3.3, Stage 2 — Main Code
    Launch) so this screen can be inspected independently without running the full
    application.  Requires data to be seeded into ScreenManager for full
    functionality; useful for layout verification without data-dependent behaviour.
    """
    root = tk.Tk()
    root.geometry("1000x600")
    root.title("LineaX – Analysis Method")
    manager = ScreenManager(root)
    manager.show(AnalysisMethodScreen)
    root.mainloop()