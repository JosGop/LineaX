"""AnalysisMethod.py — Screen 2 (Analysis Method) for LineaX."""

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

TRANSFORMS = standard_transformations + (implicit_multiplication_application,)

_GREEK_REPLACEMENTS = {
    "lambda": "lambda_", "Lambda": "lambda_",
    "mu": "mu", "sigma": "sigma", "theta": "theta", "phi": "phi", "rho": "rho",
    "λ": "lambda_", "μ": "mu", "σ": "sigma", "ρ": "rho",
    "θ": "theta", "φ": "phi", "π": "pi", "Δ": "Delta",
}

_GREEK_DISPLAY_DESCRIPTIONS = {
    "λ": "wavelength or decay constant", "lam": "wavelength or decay constant",
    "lamb": "wavelength or decay constant", "μ": "coefficient",
    "σ": "cross-section or Stefan constant", "ρ": "density or resistivity",
    "θ": "angle", "φ": "angle or work function",
    "f": "frequency", "v": "velocity", "c": "speed of light or constant",
    "h": "height or Planck constant",
}


def _apply_greek_replacements(text: str) -> str:
    """Replace Greek letter representations with SymPy-safe ASCII forms."""
    for original, replacement in _GREEK_REPLACEMENTS.items():
        text = text.replace(original, replacement)
    return text


class AnalysisMethodScreen(tk.Frame):
    """Screen 2: equation selection and linearisation (linear path) or model card selection (automated path)."""

    def __init__(self, parent, manager: ScreenManager):
        super().__init__(parent, bg="#f5f6f8", padx=20, pady=20)
        self.manager = manager
        self.library = EquationLibrary()
        self.selected_equation: Optional[Equation] = None
        self.scientific_equation: Optional[ScientificEquation] = None
        self.selected_vars: set = set()
        self.raw_data: Optional[InputData] = None
        self.transformed_data: Optional[InputData] = None
        self.data_transformer: Optional[DataTransformer] = None
        self._load_data_from_manager()
        self.create_layout()

    def _load_data_from_manager(self):
        self.raw_data = self.manager.get_data()
        self.manager.set_raw_data(self.raw_data)
        if self.raw_data is None:
            messagebox.showwarning("No Data", "No data was found. Please go back and input your data.")
        else:
            self.data_transformer = DataTransformer(self.raw_data)

    def create_layout(self):
        nav_bar = tk.Frame(self, bg="#f5f6f8")
        nav_bar.pack(fill="x", pady=(0, 10))
        tk.Button(nav_bar, text="← Back", font=("Segoe UI", 10), bg="#e5e7eb",
                  relief="flat", cursor="hand2", command=self.manager.back).pack(anchor="w")
        tk.Label(self, text="Choose Your Analysis Method", font=("Segoe UI", 26, "bold"),
                 bg="#f5f6f8", fg="#0f172a").pack(pady=(10, 25))

        container = tk.Frame(self, bg="#d1d5db")
        container.pack(fill="both", expand=True)
        inner = tk.Frame(container, bg="#d1d5db", padx=15, pady=15)
        inner.pack(fill="both", expand=True)
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(1, weight=1)
        inner.grid_rowconfigure(0, weight=1)
        self.create_linear_panel(inner)
        self.create_automated_panel(inner)

    def create_linear_panel(self, parent):
        """Build the scrollable Linear Graph Analysis panel."""
        _, panel, _, _ = make_scrollable(parent, row=0, column=0, padx=(0, 10),
                                         bg="white", panel_kwargs={"padx": 20, "pady": 20})

        tk.Label(panel, text="Linear Graph Analysis", font=("Segoe UI", 14, "bold"), bg="white").pack(anchor="w", pady=(0, 15))

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

        self.results_box = tk.Listbox(panel, height=4)
        self.results_box.pack(fill="x", pady=(5, 10))
        self.results_box.bind("<<ListboxSelect>>", self._select_equation)

        tk.Button(panel, text="+ Enter Custom Equation", bg="#f3f4f6", fg="#0f172a", relief="flat",
                  cursor="hand2", font=("Segoe UI", 9), command=self._enter_custom_equation).pack(fill="x", pady=(0, 10))

        tk.Label(panel, text="Selected Equation:", bg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 5))
        self.equation_display_frame = tk.Frame(panel, bg="#f8fafc", relief="solid", borderwidth=1)
        self.equation_display_frame.pack(fill="x", pady=(0, 10))
        self.equation_canvas = tk.Canvas(self.equation_display_frame, bg="#f8fafc", height=60, highlightthickness=0)
        self.equation_canvas.pack(fill="x", padx=10, pady=10)

        tk.Label(panel, text="Variables Measured:", bg="white", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(10, 5))
        self.selected_vars_display = tk.Label(
            panel,
            text="Click on variables in the equation above that you have measured in your experiment",
            bg="#fffbeb", fg="#92400e", relief="solid", borderwidth=1,
            padx=10, pady=8, justify="left", anchor="w"
        )
        self.selected_vars_display.pack(fill="x", pady=(0, 10))

        tk.Label(panel, text="Value to Find (optional):", bg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 5))
        self.find_var = ttk.Combobox(panel, state="readonly")
        self.find_var.pack(fill="x", pady=(0, 12))

        tk.Button(panel, text="Linearise Equation", bg="#0f172a", fg="white", font=("Segoe UI", 11, "bold"),
                  command=self._linearise_equation, cursor="hand2").pack(fill="x", pady=(15, 8))

        self.linearised_display_frame = tk.LabelFrame(panel, text="Linearised Form", bg="white", fg="#0f172a",
                                                      font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        self.linearised_equation_label = tk.Label(self.linearised_display_frame, text="", bg="white", fg="#0f172a",
                                                  font=("Courier", 11), justify="left", anchor="w")
        self.linearised_equation_label.pack(fill="x", pady=(0, 10))
        self.linearised_info_label = tk.Label(self.linearised_display_frame, text="", bg="#f0f9ff", fg="#1e40af",
                                              justify="left", anchor="nw", padx=8, pady=8, relief="solid", borderwidth=1)
        self.linearised_info_label.pack(fill="both", expand=True)

        self.constants_frame = tk.LabelFrame(panel, text="Required Constants", bg="white", fg="#0f172a",
                                             font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        self.constant_entries: dict = {}
        self.units_frame = tk.LabelFrame(panel, text="Measurement Units", bg="white", fg="#0f172a",
                                         font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        self.unit_entries: dict = {}
        self.generate_graph_button = tk.Button(panel, text="Generate Linear Graph", bg="#059669", fg="white",
                                               font=("Segoe UI", 11, "bold"), cursor="hand2", command=self.generate_graph)

    def create_automated_panel(self, parent):
        """Build the scrollable Automated Model Selection panel."""
        _, panel, _, _ = make_scrollable(parent, row=0, column=1, padx=(10, 0),
                                         bg="white", panel_kwargs={"padx": 20, "pady": 20})
        tk.Label(panel, text="Automated Model Selection", font=("Segoe UI", 14, "bold"),
                 bg="white", fg="#0f172a").pack(anchor="w", pady=(0, 15))
        tk.Label(panel, text="Select a model to automatically fit your data", font=("Segoe UI", 9),
                 bg="white", fg="#6b7280").pack(anchor="w", pady=(0, 20))

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
        tk.Frame(panel, bg="white", height=20).pack()
        tk.Button(panel, text="Generate Graph", font=("Segoe UI", 11, "bold"), bg="#0f172a", fg="white",
                  padx=30, pady=12, relief="flat", cursor="hand2",
                  command=self._generate_automated_graph).pack(fill="x", pady=(15, 0))

    def _create_model_card(self, parent, model: dict):
        """Render a single model card."""
        card = tk.Frame(parent, bg="#f8fafc", relief="solid", bd=1,
                        highlightbackground="#e2e8f0", highlightthickness=1)
        card.pack(fill="x", pady=8)
        inner = tk.Frame(card, bg="#f8fafc", padx=15, pady=12)
        inner.pack(fill="both", expand=True)

        top_row = tk.Frame(inner, bg="#f8fafc")
        top_row.pack(fill="x", pady=(0, 8))
        color_bar = tk.Frame(top_row, bg=model["color"], width=4, height=20)
        color_bar.pack(side="left", padx=(0, 10))
        color_bar.pack_propagate(False)
        tk.Label(top_row, text=model["name"], font=("Segoe UI", 12, "bold"),
                 bg="#f8fafc", fg="#0f172a").pack(side="left")

        eq_frame = tk.Frame(inner, bg="white", relief="flat", bd=1)
        eq_frame.pack(fill="x", pady=(0, 8))
        tk.Label(eq_frame, text=model["equation"], font=("Courier New", 11),
                 bg="white", fg="#1e293b", padx=12, pady=8).pack(anchor="w")
        tk.Label(inner, text=model["description"], font=("Segoe UI", 9),
                 bg="#f8fafc", fg="#64748b", justify="left").pack(anchor="w")

    def _generate_automated_graph(self):
        if self.raw_data is None:
            messagebox.showwarning("No Data", "Please go back and input your data first.")
            return
        self.manager.show(AutomatedGraphResultsScreen)

    def _on_search(self, event):
        query = self.search_entry.get()
        if query == self.search_placeholder:
            return
        results = self.library.search(query)
        self.results_box.delete(0, tk.END)
        for eq in results:
            self.results_box.insert(tk.END, f"{eq.name}             {eq.expression}")

    def _enter_custom_equation(self):
        """Open a dialog for entering a custom equation."""
        dialog = tk.Toplevel(self)
        dialog.title("Enter Custom Equation")
        dialog.geometry("500x350")
        dialog.configure(bg="white")
        tk.Label(dialog, text="Enter Custom Equation", font=("Segoe UI", 14, "bold"), bg="white").pack(pady=(20, 10))
        tk.Label(dialog,
                 text="Format: variable = expression\nExample: F = m*a  or  E = 0.5*m*v**2\n"
                      "Use 'lambda' or 'λ' for lambda, 'mu' or 'μ' for mu",
                 font=("Segoe UI", 9), bg="white", fg="#6b7280", justify="left").pack(pady=(0, 20))
        equation_entry = tk.Entry(dialog, font=("Segoe UI", 11))
        equation_entry.pack(fill="x", padx=40, pady=(0, 20))

        def submit():
            equation_str = equation_entry.get().strip()
            if not equation_str or "=" not in equation_str:
                messagebox.showwarning("Invalid Equation", "Please enter a valid equation with '='")
                return
            equation_str = (equation_str.replace("lambda", "λ").replace("Lambda", "λ")
                            .replace("mu", "μ").replace("sigma", "σ")
                            .replace("theta", "θ").replace("phi", "φ").replace("rho", "ρ"))
            try:
                lhs_str, rhs_str = equation_str.split("=")
                all_vars: set = set()
                for part in [lhs_str, rhs_str]:
                    all_vars.update(re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', part))
                    all_vars.update(re.findall(r'[α-ωΑ-Ω]', part))
                function_names = {'exp', 'log', 'ln', 'sin', 'cos', 'tan', 'sqrt',
                                  'abs', 'asin', 'acos', 'atan', 'sinh', 'cosh', 'tanh'}
                all_vars -= function_names
                if len(all_vars) < 2:
                    messagebox.showwarning("Invalid Equation",
                                           "Equation must have at least 2 variables.\nFound: " + ", ".join(all_vars))
                    return
                variables = {var: _GREEK_DISPLAY_DESCRIPTIONS.get(var, var) for var in all_vars}
                self.selected_equation = Equation("Custom Equation", equation_str, variables, linearisation_type="custom")
                self.selected_vars.clear()
                self.scientific_equation = ScientificEquation(equation_str)
                self.linearised_display_frame.pack_forget()
                self.constants_frame.pack_forget()
                self.units_frame.pack_forget()
                self.generate_graph_button.pack_forget()
                self._display_clickable_equation()
                self._update_selected_vars_display()
                self._update_find_var_options()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Parse Error",
                                     f"Could not parse equation:\n{e}\n\nPlease check your equation format.")

        tk.Button(dialog, text="Add Equation", bg="#0f172a", fg="white", font=("Segoe UI", 11, "bold"),
                  cursor="hand2", command=submit).pack(fill="x", padx=40, pady=20)

    def _select_equation(self, event):
        if not self.results_box.curselection():
            return
        index = self.results_box.curselection()[0]
        display_text = self.results_box.get(index)
        name = display_text.split("   ")[0].strip()
        for eq in self.library.search(name):
            if eq.name == name:
                self.selected_equation = eq
                break
        self.selected_vars.clear()
        self.scientific_equation = ScientificEquation(self.selected_equation.expression)
        self.linearised_display_frame.pack_forget()
        self.constants_frame.pack_forget()
        self._display_clickable_equation()
        self._update_selected_vars_display()
        self._update_find_var_options()

    def _display_clickable_equation(self):
        """Render the selected equation with variable tokens as clickable buttons."""
        self.equation_canvas.delete("all")
        if not self.selected_equation:
            return
        expr = self.selected_equation.expression
        x_pos, y_pos = 10, 30
        pattern = r'([\s=+\-*/()^]+|[0-9.]+|[a-zA-Z_][a-zA-Z0-9_]*|[α-ωΑ-Ω]+)'
        tokens = re.findall(pattern, expr)
        for token in tokens:
            token_stripped = token.strip()
            if not token_stripped:
                continue
            if token_stripped in self.selected_equation.variables:
                is_selected = token_stripped in self.selected_vars
                color    = "#3b82f6" if is_selected else "#6b7280"
                bg_color = "#dbeafe" if is_selected else "#f3f4f6"
                btn = tk.Button(self.equation_canvas, text=token_stripped, font=("Segoe UI", 11, "bold"),
                                fg=color, bg=bg_color, relief="raised", borderwidth=2, cursor="hand2",
                                command=lambda v=token_stripped: self._toggle_variable(v))
                btn_window = self.equation_canvas.create_window(x_pos, y_pos, anchor="w", window=btn)
                self.equation_canvas.update()
                bbox = self.equation_canvas.bbox(btn_window)
                x_pos = bbox[2] + 5
            else:
                if token == ' ':
                    x_pos += 3
                    continue
                text_id = self.equation_canvas.create_text(x_pos, y_pos, text=token_stripped,
                                                           font=("Segoe UI", 12), fill="#0f172a", anchor="w")
                bbox = self.equation_canvas.bbox(text_id)
                if bbox:
                    x_pos = bbox[2] + 3

    def _toggle_variable(self, var: str):
        if var in self.selected_vars:
            self.selected_vars.remove(var)
        else:
            if len(self.selected_vars) >= 2:
                messagebox.showwarning("Selection Limit",
                                       "You can only select 2 variables to measure.\nDeselect one first.")
                return
            self.selected_vars.add(var)
        self._display_clickable_equation()
        self._update_selected_vars_display()
        self._update_find_var_options()

    def _update_selected_vars_display(self):
        """Refresh the colour-coded label summarising current variable selection."""
        if len(self.selected_vars) == 0:
            text = "Click on variables in the equation above that you have measured in your experiment"
            bg, fg = "#fffbeb", "#92400e"
        elif len(self.selected_vars) == 1:
            var = next(iter(self.selected_vars))
            meaning = self.selected_equation.variables[var]
            text = f"Selected: {var} ({meaning})\n\nSelect one more variable"
            bg, fg = "#fef3c7", "#92400e"
        else:
            lines = [f"  * {var} ({self.selected_equation.variables[var]})" for var in sorted(self.selected_vars)]
            text = "Selected variables:\n" + "\n".join(lines)
            bg, fg = "#d1fae5", "#065f46"
        self.selected_vars_display.config(text=text, bg=bg, fg=fg)

    def _update_constants_post_linearisation(self):
        """Rebuild the constants input section after linearisation."""
        for widget in self.constants_frame.winfo_children():
            widget.destroy()
        if not self.selected_equation:
            return
        find_var = self.find_var.get()
        findable_from_graph: set = set()
        if self.selected_equation.linearisation_type == "exponential":
            findable_from_graph = {v for v in self.selected_equation.variables if v not in self.selected_vars}
        excluded = self.selected_vars.copy()
        if find_var and find_var != "None":
            excluded.add(find_var)
        excluded.update(findable_from_graph)
        remaining = [v for v in self.selected_equation.variables if v not in excluded]
        self.constant_entries.clear()

        if not remaining:
            tk.Label(self.constants_frame,
                     text="✓ No additional constants needed\n\nAll unknowns can be determined from the graph!",
                     fg="#065f46", bg="#d1fae5", font=("Segoe UI", 9), justify="left",
                     padx=10, pady=10, relief="solid", borderwidth=1).pack(fill="x")
            return

        tk.Label(self.constants_frame, text="Enter values for these constants:", fg="#0f172a", bg="white",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 5))
        for var in remaining:
            row = tk.Frame(self.constants_frame, bg="white")
            row.pack(fill="x", pady=3)
            meaning = self.selected_equation.variables[var]
            tk.Label(row, text=f"{var}:", width=4, anchor="w", bg="white", font=("Segoe UI", 10, "bold")).pack(side="left")
            entry = tk.Entry(row, width=15)
            entry.pack(side="left", padx=(0, 10))
            tk.Label(row, text=meaning, fg="#6b7280", bg="white", font=("Segoe UI", 9)).pack(side="left", fill="x", expand=True)
            default = self._default_constant(var)
            if default is not None:
                entry.insert(0, str(default))
            self.constant_entries[var] = entry

    def _update_units_input(self, x_var: str, y_var: str):
        """Rebuild the measurement units input section after linearisation."""
        for widget in self.units_frame.winfo_children():
            widget.destroy()
        if not self.selected_equation:
            return
        tk.Label(self.units_frame, text="Enter the units you measured your variables in:",
                 fg="#0f172a", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 10))
        self.unit_entries.clear()
        for var in [x_var, y_var]:
            row = tk.Frame(self.units_frame, bg="white")
            row.pack(fill="x", pady=5)
            meaning = self.selected_equation.variables.get(var, var)
            tk.Label(row, text=f"{var}:", width=6, anchor="w", bg="white", font=("Segoe UI", 10, "bold")).pack(side="left")
            entry = tk.Entry(row, width=20)
            entry.pack(side="left", padx=(0, 10))
            entry.insert(0, "Units")
            tk.Label(row, text=f"({meaning})", fg="#6b7280", bg="white",
                     font=("Segoe UI", 9)).pack(side="left", fill="x", expand=True)
            self.unit_entries[var] = entry
        tk.Label(self.units_frame,
                 text="If your units don't match SI units, the system will help convert them.\n"
                      "Example: If you measured in cm, enter 'cm' and we'll convert to m.",
                 fg="#059669", bg="#f0fdf4", font=("Segoe UI", 8), justify="left",
                 padx=8, pady=6, relief="solid", borderwidth=1).pack(fill="x", pady=(10, 0))

    def _update_find_var_options(self):
        if not self.selected_equation:
            return
        available = [v for v in self.selected_equation.variables if v not in self.selected_vars]
        self.find_var.config(values=["None"] + available)
        self.find_var.set("None")

    def _default_constant(self, symbol: str) -> Optional[float]:
        return CONSTANTS.get(symbol)

    def _linearise_equation(self):
        """Linearise the selected equation and update the UI with the result."""
        if not self.selected_equation:
            messagebox.showwarning("No Equation", "Please select an equation first.")
            return
        if len(self.selected_vars) != 2:
            messagebox.showwarning("Invalid Selection",
                                   "Please select exactly 2 variables to measure by clicking on them in the equation.")
            return

        var1, var2 = list(self.selected_vars)
        find_sym = self.find_var.get()
        if find_sym == "None":
            find_sym = None

        try:
            expr_str = self.selected_equation.expression
            expr_str = expr_str.replace("^", "**").replace("₀", "0")
            expr_str = _apply_greek_replacements(expr_str)
            expr_str = re.sub(r'([A-Za-z])([₀₁₂₃₄₅₆₇₈₉])', r'\1', expr_str)
            lhs_str, rhs_str = expr_str.split("=")
            local_dict = {
                'e': sp.E, 'pi': sp.pi, 'exp': sp.exp, 'log': sp.log,
                'ln': sp.log, 'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan, 'sqrt': sp.sqrt,
            }
            for var in self.selected_equation.variables:
                clean_var = var.replace("₀", "0").replace("₁", "1")
                local_dict[clean_var] = sp.Symbol(var)
            local_dict.update({
                'mu': sp.Symbol('μ'), 'lambda_': sp.Symbol('λ'),
                'sigma': sp.Symbol('σ'), 'rho': sp.Symbol('ρ'),
                'theta': sp.Symbol('θ'), 'phi': sp.Symbol('φ'),
            })
            lhs = parse_expr(lhs_str.strip(), transformations=TRANSFORMS, local_dict=local_dict)
            rhs = parse_expr(rhs_str.strip(), transformations=TRANSFORMS, local_dict=local_dict)
            equation = sp.Eq(lhs, rhs)
        except Exception as e:
            messagebox.showerror("Parse Error",
                                 f"Could not parse equation.\n\nTechnical details: {str(e)}\n\n"
                                 "Please try a different equation or contact support.")
            return

        result1 = self._attempt_linearisation(equation, var1, var2, find_sym)
        result2 = self._attempt_linearisation(equation, var2, var1, find_sym)

        def score_result(result) -> float:
            if not result:
                return float('inf')
            _, x_var, y_var, x_transform, y_transform, _, _ = result
            x_is_transformed = x_transform != x_var
            y_is_transformed = y_transform != y_var
            score = 0
            if x_is_transformed and y_is_transformed:
                score += 10
            elif not x_is_transformed and not y_is_transformed:
                score += 0
            else:
                score += 2
            if y_is_transformed:
                score -= 1
            if x_is_transformed:
                score += 2
            independent_vars = {'t', 'x', 's', 'r', 'd', 'f', 'λ', 'θ', 'φ', 'ω', 'I', 'h', 'L', 'A'}
            dependent_vars   = {'v', 'V', 'F', 'E', 'p', 'A', 'N', 'Q', 'P', 'T', 'W', 'R'}
            if x_var in independent_vars: score -= 2
            if y_var in dependent_vars:   score -= 2
            if x_var in dependent_vars:   score += 3
            if y_var in independent_vars: score += 3
            return score

        result = result1 if score_result(result1) <= score_result(result2) else result2
        if not result:
            messagebox.showinfo("Linearisation Result",
                                "This equation is already in linear form or doesn't require transformation.")
            self._display_linear_result(equation, var1, var2, find_sym)
            return

        linearised_eq, x_var, y_var, x_transform, y_transform, grad_meaning, int_meaning = result

        if self.data_transformer is not None:
            try:
                self.transformed_data = self.data_transformer.transform_for_linearisation(
                    x_transform=x_transform, y_transform=y_transform, x_var=x_var, y_var=y_var
                )
                self.manager.set_data(self.transformed_data)
            except ValueError as e:
                messagebox.showerror("Transformation Error",
                                     f"Could not transform data: {str(e)}\n\n"
                                     "Please check your data values are suitable for this transformation.")
                return

        self.scientific_equation.linearised_equation = str(linearised_eq)
        self.scientific_equation.x = x_transform
        self.scientific_equation.y = y_transform
        self.scientific_equation.m_meaning = grad_meaning
        self.scientific_equation.c_meaning = int_meaning

        self._display_linear_result(linearised_eq, x_var, y_var, find_sym,
                                    x_transform, y_transform, grad_meaning, int_meaning)
        self.constants_frame.pack(fill="x", pady=(10, 10))
        self._update_constants_post_linearisation()
        self.units_frame.pack(fill="x", pady=(10, 10))
        self._update_units_input(x_var, y_var)
        self.generate_graph_button.pack(fill="x", pady=(15, 0))

    def generate_graph(self):
        """Build equation_info dict and navigate to LinearGraphResultsScreen."""
        if self.transformed_data is None:
            messagebox.showwarning("No Linearised Data", "Please linearise an equation first before generating the graph.")
            return
        if self.selected_equation:
            gradient_var, gradient_units   = self._extract_coefficient_info("gradient")
            intercept_var, intercept_units = self._extract_coefficient_info("intercept")
            find_var = self.find_var.get() if self.find_var.get() != "None" else None
            constants: dict = {}
            for var, entry in self.constant_entries.items():
                value_str = entry.get().strip()
                if value_str:
                    try:
                        constants[var] = float(value_str)
                    except ValueError:
                        pass
            measurement_units: dict = {
                var: entry.get().strip()
                for var, entry in self.unit_entries.items()
                if entry.get().strip() and entry.get().strip() != "Units"
            }
            equation_info = {
                'name': self.selected_equation.name,
                'equation_expression': self.selected_equation.expression if self.selected_equation else '',
                'gradient_variable': gradient_var,
                'gradient_units': gradient_units,
                'intercept_variable': intercept_var,
                'intercept_units': intercept_units,
                'find_variable': find_var,
                'constants': constants,
                'measurement_units': measurement_units,
                'gradient_meaning': self.scientific_equation.m_meaning if self.scientific_equation else gradient_var,
                'intercept_meaning': self.scientific_equation.c_meaning if self.scientific_equation else intercept_var,
            }
        else:
            equation_info = {
                'name': 'Custom Linear Equation', 'equation_expression': '',
                'gradient_variable': 'm', 'gradient_units': '',
                'intercept_variable': 'c', 'intercept_units': '',
                'find_variable': None, 'constants': {}, 'measurement_units': {},
                'gradient_meaning': 'm', 'intercept_meaning': 'c',
            }
        self.manager.set_equation_info(equation_info)
        self.manager.show(LinearGraphResultsScreen)

    def _extract_coefficient_info(self, role: str) -> Tuple[str, str]:
        """Return the variable name and unit string for either the gradient or intercept."""
        if not self.selected_equation:
            return ('m', '') if role == "gradient" else ('c', '')
        if role == "gradient":
            var = (self.scientific_equation.m_meaning
                   if self.scientific_equation and self.scientific_equation.m_meaning else 'gradient')
            units = ''
            if 'decay' in self.selected_equation.name.lower() or 'λ' in var:
                units = 's⁻¹'
            elif 'attenuation' in self.selected_equation.name.lower() or 'μ' in var:
                units = 'm⁻¹'
            return var, units
        var = (self.scientific_equation.c_meaning
               if self.scientific_equation and self.scientific_equation.c_meaning else 'intercept')
        return var, ''

    def _identify_xy_vars(self) -> Tuple[str, str]:
        vars_list = list(self.selected_vars)
        if len(vars_list) < 2:
            raise ValueError("Need at least 2 variables selected")
        return vars_list[0], vars_list[1]

    def get_current_data(self) -> InputData:
        return self.transformed_data if self.transformed_data is not None else self.raw_data

    def revert_to_raw_data(self):
        if self.data_transformer is not None:
            self.transformed_data = None
            self.manager.set_data(self.raw_data)
            messagebox.showinfo("Data Reverted", "Data has been reverted to original raw measurements.")

    def _attempt_linearisation(self, equation: sp.Eq, x_var: str, y_var: str,
                                find_var: Optional[str]) -> Optional[tuple]:
        """Attempt linearisation with the given x/y variable assignment."""
        x_temp, y_temp = sp.symbols("__linx__ __liny__")
        symbol_map = {sp.Symbol(x_var): x_temp, sp.Symbol(y_var): y_temp}
        try:
            mapped_eq = equation.subs(symbol_map)
        except Exception:
            return None
        try:
            linearised = self.linearise(mapped_eq)
        except Exception:
            return None
        reverse_map = {x_temp: sp.Symbol(x_var), y_temp: sp.Symbol(y_var)}
        linearised_with_original_symbols = linearised.subs(reverse_map)
        x_transform, y_transform = self._identify_transforms(linearised, x_var, y_var)
        grad_meaning, int_meaning = self._identify_meanings(linearised, self.selected_equation, x_var, y_var, find_var)
        return (linearised_with_original_symbols, x_var, y_var, x_transform, y_transform, grad_meaning, int_meaning)

    def _identify_transforms(self, linearised_eq: sp.Eq, x_var: str, y_var: str) -> Tuple[str, str]:
        """Inspect a linearised equation to determine axis transformation labels."""
        x_temp, y_temp = sp.symbols("__linx__ __liny__")
        x_transform, y_transform = x_var, y_var
        lhs, rhs = linearised_eq.lhs, linearised_eq.rhs

        if lhs.has(sp.log):
            if lhs == sp.log(y_temp) or lhs.func == sp.log:
                y_transform = f"ln({y_var})"
        elif lhs != y_temp and lhs.has(y_temp) and not lhs.has(y_temp ** 2):
            try:
                y_transform = str(lhs.subs(y_temp, sp.Symbol(y_var)))
            except Exception:
                y_transform = y_var

        if lhs == y_temp ** 2 or lhs.has(y_temp ** 2):
            y_transform = f"{y_var}**2"
        elif lhs == y_temp ** 3 or lhs.has(y_temp ** 3):
            y_transform = f"{y_var}**3"

        if rhs.has(sp.log):
            for arg in sp.preorder_traversal(rhs):
                if isinstance(arg, sp.log) and arg.has(x_temp):
                    x_transform = f"ln({x_var})"
                    break
        if rhs.has(x_temp ** 2) and not rhs.has(1 / x_temp):
            x_transform = f"{x_var}²"
        elif rhs.has(x_temp ** 3):
            x_transform = f"{x_var}³"
        elif rhs.has(x_temp ** 4):
            x_transform = f"{x_var}⁴"
        if rhs.has(1 / x_temp):
            x_transform = f"1/{x_var}"
        return x_transform, y_transform

    def _identify_meanings(self, linearised_eq: sp.Eq, original_eq, x_var: str,
                           y_var: str, find_var: Optional[str]) -> Tuple[str, str]:
        """Extract physical meanings of the gradient and intercept from a linearised equation."""
        x_temp, y_temp = sp.symbols("__linx__ __liny__")
        rhs = linearised_eq.rhs
        rhs_expanded = sp.expand(rhs)
        try:
            if rhs.has(1 / x_temp):
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
                const_term = sp.Integer(0)
            else:
                grad_coeff = rhs_expanded.coeff(x_temp, 1) or sp.Integer(0)
                const_term = rhs_expanded.coeff(x_temp, 0) or sp.Integer(0)

            reverse_map = {x_temp: sp.Symbol(x_var), y_temp: sp.Symbol(y_var)}
            grad_coeff_original = grad_coeff.subs(reverse_map) if grad_coeff != 0 else grad_coeff
            const_term_original = const_term.subs(reverse_map) if const_term != 0 else const_term

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
                grad_meaning = " ".join(grad_meaning.replace('**', '^').split())
            else:
                grad_meaning = "0"

            int_meaning = " ".join(str(sp.simplify(const_term_original)).replace('**', '^').split()) if const_term_original != 0 else "0"

            if original_eq.linearisation_type == "exponential" and original_eq.transform_info:
                grad_meaning = original_eq.transform_info.get("gradient_meaning", grad_meaning)
                int_meaning  = original_eq.transform_info.get("intercept_meaning", int_meaning)

            if find_var:
                if find_var in str(grad_coeff_original):
                    grad_meaning += f" (contains {find_var})"
                if find_var in str(const_term_original):
                    int_meaning  += f" (contains {find_var})"
            return grad_meaning, int_meaning
        except Exception as e:
            print(f"Error in _identify_meanings: {e}")
            grad_meaning = "gradient"
            int_meaning  = "y-intercept"
            if original_eq.linearisation_type == "exponential" and original_eq.transform_info:
                grad_meaning = original_eq.transform_info.get("gradient_meaning", "gradient")
                int_meaning  = original_eq.transform_info.get("intercept_meaning", "y-intercept")
            if find_var:
                int_meaning += f" (can be used to find {find_var})"
            return grad_meaning, int_meaning

    def _display_linear_result(self, linearised_eq, x_var, y_var, find_var=None,
                               x_transform=None, y_transform=None,
                               grad_meaning=None, int_meaning=None):
        """Reveal the linearised result panel and populate it with equation and instructions."""
        self.linearised_display_frame.pack(fill="both", expand=True, pady=(10, 15))
        self.linearised_equation_label.config(text=sp.pretty(linearised_eq, use_unicode=True))

        x_transform  = x_transform  or x_var
        y_transform  = y_transform  or y_var
        grad_meaning = grad_meaning or "gradient"
        int_meaning  = int_meaning  or "y-intercept"
        x_meaning = self.selected_equation.variables.get(x_var, x_var)
        y_meaning = self.selected_equation.variables.get(y_var, y_var)

        def _pretty_transform(t: str) -> str:
            _sups = {'2': '²', '3': '³', '4': '⁴', '5': '⁵'}
            return re.sub(r'(\w+)\*\*(\d)', lambda m: m.group(1) + _sups.get(m.group(2), f'^{m.group(2)}'), t)

        info_lines = [
            "Plotting Instructions:\n",
            f"X-axis: {_pretty_transform(x_transform)}", f"   ({x_meaning})\n",
            f"Y-axis: {_pretty_transform(y_transform)}", f"   ({y_meaning})\n",
            f"Gradient represents: {grad_meaning}\n",
            f"Y-intercept represents: {int_meaning}",
        ]
        if find_var:
            info_lines.append(f"\n\nYou can find {find_var} from the graph")
        self.linearised_info_label.config(text="\n".join(info_lines))

    @staticmethod
    def linearise(equation: sp.Eq) -> sp.Eq:
        """Transform a SymPy equation into y = mx + c linear form (Algorithm 2)."""
        x, y = sp.symbols("__linx__ __liny__")
        if not isinstance(equation, sp.Eq):
            expr = equation
            if y in expr.free_symbols:
                equation = sp.Eq(y, expr) if (expr.is_Add or expr.is_Mul or expr.is_Pow) else sp.Eq(expr, 0)
            else:
                equation = sp.Eq(y, expr)

        lhs, rhs = equation.lhs, equation.rhs
        if y in lhs.free_symbols and y not in rhs.free_symbols:
            y_side, expr_side = lhs, rhs
        elif y in rhs.free_symbols and y not in lhs.free_symbols:
            y_side, expr_side = rhs, lhs
        else:
            return equation

        # Pre-check: y**n = linear_in_x pattern (must run before the already-linear branch)
        for _pw in (2, 3, 4):
            _y_power = y ** _pw
            if equation.has(_y_power):
                _y_sub = sp.Symbol('_ysub_tmp_')
                _eq_sub = equation.subs(_y_power, _y_sub)
                if y not in _eq_sub.free_symbols:
                    try:
                        _sols = sp.solve(_eq_sub, _y_sub)
                        if _sols:
                            _cand = sp.expand(_sols[0])
                            if _cand.is_polynomial(x) and sp.degree(_cand, x) <= 1:
                                return sp.Eq(_y_power, _cand)
                    except Exception:
                        pass

        if expr_side.is_polynomial(x) and sp.degree(expr_side, x) <= 1:
            if y_side == y:
                return equation
            try:
                solved = sp.solve(equation, y)
                if solved:
                    return sp.Eq(y, solved[0])
            except Exception:
                pass
            return sp.Eq(y_side, expr_side)

        if y_side != y:
            try:
                solved = sp.solve(equation, y)
                if solved:
                    expr_side = solved[0]
                    y_side = y
            except Exception:
                pass

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

        return sp.Eq(y_side, expr_side)

    def _clear_placeholder(self, event):
        if self.search_entry.get() == self.search_placeholder:
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg="#0f172a")

    def _restore_placeholder(self, event):
        if not self.search_entry.get().strip():
            self.search_entry.insert(0, self.search_placeholder)
            self.search_entry.config(fg="#9ca3af")


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x600")
    root.title("LineaX - Analysis Method")
    manager = ScreenManager(root)
    manager.show(AnalysisMethodScreen)
    root.mainloop()