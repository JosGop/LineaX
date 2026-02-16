import tkinter as tk
from tkinter import ttk, messagebox
from Equations import *
from LineaX_Classes import ScientificEquation, InputData
from ManagingScreen import *
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application
)
from DataTransform import DataTransformer, identify_required_transformations
from LinearGraphDisplay import GraphResultsScreen
from AutomatedGraphFitScreen import AutomatedGraphFitScreen

TRANSFORMS = standard_transformations + (
    implicit_multiplication_application,
)


class AnalysisMethodScreen(tk.Frame):
    def __init__(self, parent, manager):
        super().__init__(parent, bg="#f5f6f8", padx=20, pady=20)
        self.manager = manager
        self.library = EquationLibrary()
        self.selected_equation: Equation | None = None
        self.scientific_equation: ScientificEquation | None = None

        # Track selected variables
        self.selected_vars = set()

        # Data management
        self.raw_data: InputData | None = None
        self.transformed_data: InputData | None = None
        self.data_transformer: DataTransformer | None = None

        # Retrieve raw data from manager
        self._load_data_from_manager()

        self.create_layout()

    def _load_data_from_manager(self):
        """Load the raw InputData from the screen manager."""
        self.raw_data = self.manager.get_data()

        if self.raw_data is None:
            messagebox.showwarning(
                "No Data",
                "No data was found. Please go back and input your data."
            )
        else:
            # Initialize transformer with raw data
            self.data_transformer = DataTransformer(self.raw_data)

    def create_layout(self):
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

        container = tk.Frame(self, bg="#d1d5db")
        container.pack(fill="both", expand=True)

        inner = tk.Frame(container, bg="#d1d5db", padx=15, pady=15)
        inner.pack(fill="both", expand=True)

        # Configure grid to give row 0 all available space
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(1, weight=1)
        inner.grid_rowconfigure(0, weight=1)

        self.create_linear_panel(inner)
        self.create_automated_panel(inner)

    def create_linear_panel(self, parent):
        _, panel, _, _ = make_scrollable(
            parent,
            row=0,
            column=0,
            padx=(0, 10),
            bg="white",
            panel_kwargs={"padx": 20, "pady": 20},
        )

        tk.Label(panel, text="Linear Graph Analysis", font=("Segoe UI", 14, "bold"), bg="white").pack(anchor="w",
                                                                                                      pady=(0, 15))

        # Search section
        search_frame = tk.Frame(panel, bg="white")
        search_frame.pack(fill="x")

        tk.Label(search_frame, text="🔍", bg="white", fg="#64748b").pack(side="left", padx=(0, 5))

        self.search_placeholder = "Search equations...."
        self.search_entry = tk.Entry(search_frame, fg="#9ca3af")
        self.search_entry.insert(0, self.search_placeholder)
        self.search_entry.pack(fill="x", expand=True)
        self.search_entry.bind("<FocusIn>", self._clear_placeholder)
        self.search_entry.bind("<FocusOut>", self._restore_placeholder)
        self.search_entry.bind("<KeyRelease>", self._on_search)

        self.results_box = tk.Listbox(panel, height=4)
        self.results_box.pack(fill="x", pady=(5, 10))
        self.results_box.bind("<<ListboxSelect>>", self._select_equation)

        # Custom equation button
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

        # Equation display with clickable variables
        tk.Label(panel, text="Selected Equation:", bg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w",
                                                                                                   pady=(10, 5))

        self.equation_display_frame = tk.Frame(panel, bg="#f8fafc", relief="solid", borderwidth=1)
        self.equation_display_frame.pack(fill="x", pady=(0, 10))

        self.equation_canvas = tk.Canvas(self.equation_display_frame, bg="#f8fafc", height=60, highlightthickness=0)
        self.equation_canvas.pack(fill="x", padx=10, pady=10)

        # Selected variables display
        tk.Label(panel, text="Variables Measured:", bg="white", font=("Segoe UI", 11, "bold")).pack(anchor="w",
                                                                                                    pady=(10, 5))

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

        # Optional value to find
        tk.Label(panel, text="Value to Find (optional):", bg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w",
                                                                                                          pady=(10, 5))
        self.find_var = ttk.Combobox(panel, state="readonly")
        self.find_var.pack(fill="x", pady=(0, 12))

        # Linearise button
        tk.Button(
            panel,
            text="Linearise Equation",
            bg="#0f172a",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            command=self._linearise_equation,
            cursor="hand2"
        ).pack(fill="x", pady=(15, 8))

        # Linearised result display
        self.linearised_display_frame = tk.LabelFrame(
            panel,
            text="Linearised Form",
            bg="white",
            fg="#0f172a",
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=10
        )

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

        # Constants section - appears AFTER linearisation
        self.constants_frame = tk.LabelFrame(
            panel,
            text="Required Constants",
            bg="white",
            fg="#0f172a",
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=10
        )
        self.constant_entries = {}

        # Units section - appears AFTER linearisation
        self.units_frame = tk.LabelFrame(
            panel,
            text="Measurement Units",
            bg="white",
            fg="#0f172a",
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=10
        )
        self.unit_entries = {}

        # Generate graph button - appears AFTER linearisation
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
        """Create the automated model selection panel with model cards."""
        _, panel, _, _ = make_scrollable(
            parent,
            row=0,
            column=1,
            padx=(10, 0),
            bg="white",
            panel_kwargs={"padx": 20, "pady": 20},
        )

        # Panel title
        tk.Label(
            panel,
            text="Automated Model Selection",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg="#0f172a"
        ).pack(anchor="w", pady=(0, 15))

        # Subtitle
        tk.Label(
            panel,
            text="Select a model to automatically fit your data",
            font=("Segoe UI", 9),
            bg="white",
            fg="#6b7280"
        ).pack(anchor="w", pady=(0, 20))

        # Model definitions with equations and descriptions
        models = [
            {
                "name": "Linear",
                "equation": "y = mx + c",
                "description": "Straight line relationship",
                "color": "#3b82f6"
            },
            {
                "name": "Quadratic",
                "equation": "y = ax² + bx + c",
                "description": "Parabolic curve",
                "color": "#8b5cf6"
            },
            {
                "name": "Cubic",
                "equation": "y = ax³ + bx² + cx + d",
                "description": "S-shaped or cubic curve",
                "color": "#ec4899"
            },
            {
                "name": "Exponential",
                "equation": "y = a·eᵇˣ",
                "description": "Growth or decay",
                "color": "#f59e0b"
            },
            {
                "name": "Logarithmic",
                "equation": "y = a·ln(x) + b",
                "description": "Logarithmic relationship",
                "color": "#10b981"
            },
            {
                "name": "Power",
                "equation": "y = a·xᵇ",
                "description": "Power law relationship",
                "color": "#06b6d4"
            },
            {
                "name": "Gaussian",
                "equation": "y = a·e^(-(x-b)²/(2c²))",
                "description": "Bell-shaped curve",
                "color": "#6366f1"
            },
            {
                "name": "Logistic",
                "equation": "y = L/(1 + e^(-k(x-x₀)))",
                "description": "S-shaped growth curve",
                "color": "#84cc16"
            },
            {
                "name": "Sinusoidal",
                "equation": "y = a·sin(bx + c) + d",
                "description": "Periodic oscillation",
                "color": "#f43f5e"
            }
        ]

        # Create model cards
        for model in models:
            self._create_model_card(panel, model)

        # Bottom spacer
        tk.Frame(panel, bg="white", height=20).pack()

        # Generate Graph button
        generate_btn = tk.Button(
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
        )
        generate_btn.pack(fill="x", pady=(15, 0))

    def _create_model_card(self, parent, model):
        """Create an individual model card with equation display."""
        # Card container
        card = tk.Frame(
            parent,
            bg="#f8fafc",
            relief="solid",
            bd=1,
            highlightbackground="#e2e8f0",
            highlightthickness=1
        )
        card.pack(fill="x", pady=8)

        # Inner padding
        inner = tk.Frame(card, bg="#f8fafc", padx=15, pady=12)
        inner.pack(fill="both", expand=True)

        # Top row: model name with colored indicator
        top_row = tk.Frame(inner, bg="#f8fafc")
        top_row.pack(fill="x", pady=(0, 8))

        # Color indicator
        color_bar = tk.Frame(
            top_row,
            bg=model["color"],
            width=4,
            height=20
        )
        color_bar.pack(side="left", padx=(0, 10))
        color_bar.pack_propagate(False)

        # Model name
        tk.Label(
            top_row,
            text=model["name"],
            font=("Segoe UI", 12, "bold"),
            bg="#f8fafc",
            fg="#0f172a"
        ).pack(side="left")

        # Equation display
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

        # Description
        tk.Label(
            inner,
            text=model["description"],
            font=("Segoe UI", 9),
            bg="#f8fafc",
            fg="#64748b",
            justify="left"
        ).pack(anchor="w")

    def _generate_automated_graph(self):
        """Generate graph with automated model selection."""
        # Check if we have data
        if self.raw_data is None:
            messagebox.showwarning(
                "No Data",
                "Please go back and input your data first."
            )
            return

        # Navigate to AutomatedGraphFitScreen
        self.manager.show(AutomatedGraphFitScreen)

    def _on_search(self, event):
        query = self.search_entry.get()
        if query == self.search_placeholder:
            return
        results = self.library.search(query)
        self.results_box.delete(0, tk.END)
        for eq in results:
            self.results_box.insert(tk.END, f"{eq.name}             {eq.expression}")

    def _enter_custom_equation(self):
        """Allow user to enter a custom equation."""
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
            text="Format: variable = expression\nExample: F = m*a  or  E = 0.5*m*v**2\nUse 'lambda' or 'λ' for lambda, 'mu' or 'μ' for mu",
            font=("Segoe UI", 9),
            bg="white",
            fg="#6b7280",
            justify="left"
        ).pack(pady=(0, 20))

        equation_entry = tk.Entry(dialog, font=("Segoe UI", 11))
        equation_entry.pack(fill="x", padx=40, pady=(0, 20))

        def submit():
            equation_str = equation_entry.get().strip()
            if not equation_str or "=" not in equation_str:
                messagebox.showwarning("Invalid Equation", "Please enter a valid equation with '='")
                return

            # Replace common text representations with Greek letters
            equation_str = equation_str.replace('lambda', 'λ')
            equation_str = equation_str.replace('Lambda', 'λ')
            equation_str = equation_str.replace('mu', 'μ')
            equation_str = equation_str.replace('sigma', 'σ')
            equation_str = equation_str.replace('theta', 'θ')
            equation_str = equation_str.replace('phi', 'φ')
            equation_str = equation_str.replace('rho', 'ρ')

            # Parse to extract variables
            try:
                lhs_str, rhs_str = equation_str.split("=")
                all_vars = set()

                import re
                # Extract variable names (letters, Greek letters, possibly with numbers/subscripts)
                # Match: single letters, Greek letters, or identifiers with numbers
                for part in [lhs_str, rhs_str]:
                    # Match standard variables (v, v0, v_0, etc.)
                    vars_found = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', part)
                    all_vars.update(vars_found)

                    # Also match Greek letters
                    greek_letters = re.findall(r'[α-ωΑ-Ω]', part)
                    all_vars.update(greek_letters)

                # Remove function names
                function_names = {'exp', 'log', 'ln', 'sin', 'cos', 'tan', 'sqrt',
                                  'abs', 'asin', 'acos', 'atan', 'sinh', 'cosh', 'tanh'}
                all_vars = all_vars - function_names

                if len(all_vars) < 2:
                    messagebox.showwarning(
                        "Invalid Equation",
                        "Equation must have at least 2 variables.\nFound: " + ", ".join(all_vars)
                    )
                    return

                # Create a custom equation with proper variable descriptions
                variables = {}
                for var in all_vars:
                    # Try to give meaningful descriptions
                    if var in ['λ', 'lam', 'lamb']:
                        variables[var] = "wavelength or decay constant"
                    elif var in ['μ', 'mu']:
                        variables[var] = "coefficient"
                    elif var in ['σ', 'sigma']:
                        variables[var] = "cross-section or Stefan constant"
                    elif var in ['ρ', 'rho']:
                        variables[var] = "density or resistivity"
                    elif var in ['θ', 'theta']:
                        variables[var] = "angle"
                    elif var in ['φ', 'phi']:
                        variables[var] = "angle or work function"
                    elif var == 'f':
                        variables[var] = "frequency"
                    elif var == 'v':
                        variables[var] = "velocity"
                    elif var == 'c':
                        variables[var] = "speed of light or constant"
                    elif var == 'h':
                        variables[var] = "height or Planck constant"
                    else:
                        variables[var] = var  # Use variable name as description

                self.selected_equation = Equation(
                    "Custom Equation",
                    equation_str,
                    variables,
                    linearisation_type="custom"
                )

                self.selected_vars.clear()
                self.scientific_equation = ScientificEquation(equation_str)

                # Hide linearised display and constants
                self.linearised_display_frame.pack_forget()
                self.constants_frame.pack_forget()
                self.units_frame.pack_forget()
                self.generate_graph_button.pack_forget()

                # Display equation
                self._display_clickable_equation()
                self._update_selected_vars_display()
                self._update_find_var_options()

                dialog.destroy()

            except Exception as e:
                messagebox.showerror("Parse Error",
                                     f"Could not parse equation:\n{e}\n\nPlease check your equation format.")

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
        if not self.results_box.curselection():
            return

        index = self.results_box.curselection()[0]
        display_text = self.results_box.get(index)
        name = display_text.split("   ")[0].strip()

        for eq in self.library.search(name):
            if eq.name == name:
                self.selected_equation = eq
                break

        # Reset state
        self.selected_vars.clear()
        self.scientific_equation = ScientificEquation(self.selected_equation.expression)

        # Hide linearised display and constants
        self.linearised_display_frame.pack_forget()
        self.constants_frame.pack_forget()

        # Display equation with clickable variables
        self._display_clickable_equation()

        # Update UI
        self._update_selected_vars_display()
        self._update_find_var_options()

    def _display_clickable_equation(self):
        """Display equation with clickable variable buttons."""
        self.equation_canvas.delete("all")

        if not self.selected_equation:
            return

        # Parse equation into parts
        expr = self.selected_equation.expression
        x_pos = 10
        y_pos = 30

        # Simple parser - split by common operators, but preserve Greek letters
        import re
        # Split by operators but keep them
        # Match: operators, numbers, variables (including Greek)
        pattern = r'([\s=+\-*/()^]+|[0-9.]+|[a-zA-Z_][a-zA-Z0-9_]*|[α-ωΑ-Ω]+)'
        tokens = re.findall(pattern, expr)

        for token in tokens:
            token_stripped = token.strip()
            if not token_stripped:
                continue

            # Check if token is a variable (in our variables dict)
            if token_stripped in self.selected_equation.variables:
                # Create clickable button for variable
                is_selected = token_stripped in self.selected_vars
                color = "#3b82f6" if is_selected else "#6b7280"
                bg_color = "#dbeafe" if is_selected else "#f3f4f6"

                # Create button
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
                # Draw text for operators, numbers, and constants
                # Handle spaces
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

    def _toggle_variable(self, var):
        """Toggle variable selection."""
        if var in self.selected_vars:
            self.selected_vars.remove(var)
        else:
            # Limit to 2 measured variables
            if len(self.selected_vars) >= 2:
                messagebox.showwarning(
                    "Selection Limit",
                    "You can only select 2 variables to measure.\nDeselect one first."
                )
                return
            self.selected_vars.add(var)

        # Update displays
        self._display_clickable_equation()
        self._update_selected_vars_display()
        self._update_find_var_options()

    def _update_selected_vars_display(self):
        """Update the display showing selected variables."""
        if len(self.selected_vars) == 0:
            text = "Click on variables in the equation above that you have measured in your experiment"
            bg = "#fffbeb"
            fg = "#92400e"
        elif len(self.selected_vars) == 1:
            var = list(self.selected_vars)[0]
            meaning = self.selected_equation.variables[var]
            text = f"Selected: {var} ({meaning})\n\nSelect one more variable"
            bg = "#fef3c7"
            fg = "#92400e"
        else:
            text = "Selected variables:\n"
            for var in sorted(self.selected_vars):
                meaning = self.selected_equation.variables[var]
                text += f"  • {var} ({meaning})\n"
            bg = "#d1fae5"
            fg = "#065f46"

        self.selected_vars_display.config(text=text, bg=bg, fg=fg)

    def _update_constants_post_linearisation(self):
        """
        Update constants section AFTER linearisation.
        Only request constants that CANNOT be determined from the graph.

        For example, in I = I0*e^(-μ*x):
        - If finding μ: Don't need I0 (it's in the intercept)
        - If finding I0: Don't need it (it's in the intercept)
        - Other constants (if any) still needed
        """
        for widget in self.constants_frame.winfo_children():
            widget.destroy()

        if not self.selected_equation:
            return

        find_var = self.find_var.get()

        # Identify which variables are "findable" from the linearised form
        # These are variables that appear in the gradient or intercept
        findable_from_graph = set()

        # For exponential equations, the coefficient in the exponent (e.g., μ in e^(-μx))
        # and the initial value (e.g., I0) can both be found from the graph
        if self.selected_equation.linearisation_type == "exponential":
            # Find variables that aren't the measured ones
            for var in self.selected_equation.variables.keys():
                if var not in self.selected_vars:
                    findable_from_graph.add(var)

        # Variables that need constant values:
        # - Not measured (not in selected_vars)
        # - Not the find variable
        # - Not findable from the graph structure
        excluded = self.selected_vars.copy()
        if find_var and find_var != "None":
            excluded.add(find_var)
        excluded.update(findable_from_graph)

        remaining = [
            v for v in self.selected_equation.variables.keys()
            if v not in excluded
        ]

        self.constant_entries.clear()

        if not remaining:
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
            tk.Label(
                row,
                text=f"{var}:",
                width=4,
                anchor="w",
                bg="white",
                font=("Segoe UI", 10, "bold")
            ).pack(side="left")

            entry = tk.Entry(row, width=15)
            entry.pack(side="left", padx=(0, 10))

            tk.Label(
                row,
                text=meaning,
                fg="#6b7280",
                bg="white",
                font=("Segoe UI", 9)
            ).pack(side="left", fill="x", expand=True)

            default = self._default_constant(var)
            if default is not None:
                entry.insert(0, str(default))

            self.constant_entries[var] = entry

    def _update_units_input(self, x_var, y_var):
        """Ask user for measurement units."""
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

        # Add unit inputs for the two measured variables
        for var in [x_var, y_var]:
            row = tk.Frame(self.units_frame, bg="white")
            row.pack(fill="x", pady=5)

            meaning = self.selected_equation.variables.get(var, var)

            tk.Label(
                row,
                text=f"{var}:",
                width=6,
                anchor="w",
                bg="white",
                font=("Segoe UI", 10, "bold")
            ).pack(side="left")

            entry = tk.Entry(row, width=20)
            entry.pack(side="left", padx=(0, 10))
            entry.insert(0, "SI units")  # Placeholder

            tk.Label(
                row,
                text=f"({meaning})",
                fg="#6b7280",
                bg="white",
                font=("Segoe UI", 9)
            ).pack(side="left", fill="x", expand=True)

            self.unit_entries[var] = entry

        # Add helpful note
        note = tk.Label(
            self.units_frame,
            text="💡 If your units don't match SI units, the system will help convert them.\nExample: If you measured in cm, enter 'cm' and we'll convert to m.",
            fg="#059669",
            bg="#f0fdf4",
            font=("Segoe UI", 8),
            justify="left",
            padx=8,
            pady=6,
            relief="solid",
            borderwidth=1
        )
        note.pack(fill="x", pady=(10, 0))

    def _update_find_var_options(self):
        """Update the dropdown for optional variable to find."""
        if not self.selected_equation:
            return

        # Can only find variables that aren't being measured
        available = [
            v for v in self.selected_equation.variables.keys()
            if v not in self.selected_vars
        ]

        self.find_var.config(values=["None"] + available)
        self.find_var.set("None")

    def _default_constant(self, symbol):
        """Get default value for known physical constants."""
        return CONSTANTS.get(symbol)

    def _linearise_equation(self):
        """Linearise the selected equation based on user's variable choices."""
        if not self.selected_equation:
            messagebox.showwarning("No Equation", "Please select an equation first.")
            return

        if len(self.selected_vars) != 2:
            messagebox.showwarning(
                "Invalid Selection",
                "Please select exactly 2 variables to measure by clicking on them in the equation."
            )
            return

        # Get the two measured variables
        measured_vars = list(self.selected_vars)
        var1, var2 = measured_vars[0], measured_vars[1]

        # Get variable to find (if any)
        find_sym = self.find_var.get()
        if find_sym == "None":
            find_sym = None

        # Parse the equation (without substituting constants yet)
        try:
            # Clean the equation string for parsing
            expr_str = self.selected_equation.expression

            # Replace common notations
            expr_str = expr_str.replace("^", "**")  # Convert ^ to **
            expr_str = expr_str.replace("₀", "0")  # Replace subscript 0
            expr_str = expr_str.replace("λ", "lambda_")  # Replace lambda
            expr_str = expr_str.replace("μ", "mu")  # Replace mu
            expr_str = expr_str.replace("σ", "sigma")  # Replace sigma
            expr_str = expr_str.replace("ρ", "rho")  # Replace rho
            expr_str = expr_str.replace("θ", "theta")  # Replace theta
            expr_str = expr_str.replace("φ", "phi")  # Replace phi
            expr_str = expr_str.replace("π", "pi")  # Replace pi
            expr_str = expr_str.replace("Δ", "Delta")  # Replace Delta

            # Handle other subscripts (just remove them for parsing)
            import re
            expr_str = re.sub(r'([A-Za-z])([₀₁₂₃₄₅₆₇₈₉])', r'\1', expr_str)

            lhs_str, rhs_str = expr_str.split("=")

            # Create a local namespace with necessary symbols and functions
            local_dict = {
                'e': sp.E,
                'pi': sp.pi,
                'exp': sp.exp,
                'log': sp.log,
                'ln': sp.log,
                'sin': sp.sin,
                'cos': sp.cos,
                'tan': sp.tan,
                'sqrt': sp.sqrt,
            }

            # Add all variables as symbols
            for var in self.selected_equation.variables.keys():
                clean_var = var.replace("₀", "0").replace("₁", "1")
                local_dict[clean_var] = sp.Symbol(var)

            # Also add cleaned versions
            local_dict['mu'] = sp.Symbol('μ')
            local_dict['lambda_'] = sp.Symbol('λ')
            local_dict['sigma'] = sp.Symbol('σ')
            local_dict['rho'] = sp.Symbol('ρ')
            local_dict['theta'] = sp.Symbol('θ')
            local_dict['phi'] = sp.Symbol('φ')

            lhs = parse_expr(lhs_str.strip(), transformations=TRANSFORMS, local_dict=local_dict)
            rhs = parse_expr(rhs_str.strip(), transformations=TRANSFORMS, local_dict=local_dict)
            equation = sp.Eq(lhs, rhs)

        except Exception as e:
            messagebox.showerror(
                "Parse Error",
                f"Could not parse equation.\n\nTechnical details: {str(e)}\n\nPlease try a different equation or contact support."
            )
            return

            # Try both orderings and analyze which gives better linearisation
        result1 = self._attempt_linearisation(equation, var1, var2, find_sym)
        result2 = self._attempt_linearisation(equation, var2, var1, find_sym)

        # Pick the result that produces a simpler/better linear form
        # Prefer orderings where:
        # 1. One axis needs transformation (ln, ^2) and the other doesn't
        # 2. The physically sensible independent variable is on X-axis

        def score_result(result):
            """Score a result - lower is better."""
            if not result:
                return float('inf')

            _, x_var, y_var, x_transform, y_transform, _, _ = result
            score = 0

            # Prefer when only one axis is transformed
            x_is_transformed = x_transform != x_var
            y_is_transformed = y_transform != y_var

            if x_is_transformed and y_is_transformed:
                score += 10  # Both transformed - not ideal
            elif not x_is_transformed and not y_is_transformed:
                score += 0  # Neither transformed - BEST for already linear equations
            else:
                score += 2  # One transformed - okay for non-linear equations

            # Prefer Y-axis transformation over X-axis for non-linear equations
            # (e.g., ln(I) vs x is better than I vs ln(x))
            if y_is_transformed:
                score -= 1
            if x_is_transformed:
                score += 2

            # Additional heuristic: prefer common physics conventions
            # Independent variables (typically on X-axis): t, x, s, r, d, f, λ, θ, I
            # Dependent variables (typically on Y-axis): v, V, F, E, p, A, N, Q
            independent_vars = {'t', 'x', 's', 'r', 'd', 'f', 'λ', 'θ', 'φ', 'ω', 'I', 'h', 'L', 'A'}
            dependent_vars = {'v', 'V', 'F', 'E', 'p', 'A', 'N', 'Q', 'P', 'T', 'W', 'R'}

            # Bonus for correct convention
            if x_var in independent_vars:
                score -= 2  # Good - independent on X
            if y_var in dependent_vars:
                score -= 2  # Good - dependent on Y

            # Penalty for backwards convention
            if x_var in dependent_vars:
                score += 3  # Bad - dependent on X
            if y_var in independent_vars:
                score += 3  # Bad - independent on Y

            return score

        score1 = score_result(result1)
        score2 = score_result(result2)

        if score1 <= score2:
            result = result1
        else:
            result = result2

        if not result:
            messagebox.showinfo(
                "Linearisation Result",
                "This equation is already in linear form or doesn't require transformation."
            )
            # Show the equation as-is
            self._display_linear_result(equation, var1, var2, find_sym)
            return

        # Unpack result
        linearised_eq, x_var, y_var, x_transform, y_transform, grad_meaning, int_meaning = result

        linearised_eq, x_var, y_var, x_transform, y_transform, grad_meaning, int_meaning = result

        # Transform the data if transformer is available
        if self.data_transformer is not None:
            try:
                self.transformed_data = self.data_transformer.transform_for_linearisation(
                    x_transform=x_transform,
                    y_transform=y_transform,
                    x_var=x_var,
                    y_var=y_var
                )

                # Update manager with transformed data
                self.manager.set_data(self.transformed_data)

            except ValueError as e:
                messagebox.showerror(
                    "Transformation Error",
                    f"Could not transform data: {str(e)}\n\n"
                    f"Please check your data values are suitable for this transformation."
                )
                return

        # Store in scientific equation object using the simple structure
        self.scientific_equation.linearised_equation = str(linearised_eq)
        self.scientific_equation.x = x_transform  # e.g., "x" or "ln(x)"
        self.scientific_equation.y = y_transform  # e.g., "ln(I)"
        self.scientific_equation.m_meaning = grad_meaning
        self.scientific_equation.c_meaning = int_meaning

        # Display result
        self._display_linear_result(linearised_eq, x_var, y_var, find_sym,
                                    x_transform, y_transform, grad_meaning, int_meaning)

        # Now show constants frame and populate it
        self.constants_frame.pack(fill="x", pady=(10, 10))
        self._update_constants_post_linearisation()

        # Show units frame
        self.units_frame.pack(fill="x", pady=(10, 10))
        self._update_units_input(x_var, y_var)

        # Show generate graph button at the bottom
        self.generate_graph_button.pack(fill="x", pady=(15, 0))

    def generate_graph(self):
        """
        Generate the linear graph and navigate to GraphResults screen.
        Called when user clicks 'Generate Linear Graph' button.
        """
        # Check if we have linearised data
        if self.transformed_data is None:
            messagebox.showwarning(
                "No Linearised Data",
                "Please linearise an equation first before generating the graph."
            )
            return

        # Extract equation information for the next screen
        if self.selected_equation:
            # Determine what the gradient and intercept represent
            gradient_var, gradient_units = self._extract_gradient_info()
            intercept_var, intercept_units = self._extract_intercept_info()

            # Get the variable to find
            find_var = self.find_var.get() if self.find_var.get() != "None" else None

            # Get constant values entered by user
            constants = {}
            for var, entry in self.constant_entries.items():
                try:
                    value_str = entry.get().strip()
                    if value_str:
                        constants[var] = float(value_str)
                except ValueError:
                    pass  # Ignore invalid entries

            # Get measurement units entered by user
            measurement_units = {}
            for var, entry in self.unit_entries.items():
                unit_str = entry.get().strip()
                if unit_str and unit_str != "SI units":
                    measurement_units[var] = unit_str

            equation_info = {
                'name': self.selected_equation.name,
                'gradient_variable': gradient_var,
                'gradient_units': gradient_units,
                'intercept_variable': intercept_var,
                'intercept_units': intercept_units,
                'find_variable': find_var,  # Variable to solve for
                'constants': constants,  # Known constant values
                'measurement_units': measurement_units,  # NEW: User-entered units
                'gradient_meaning': self.scientific_equation.m_meaning if self.scientific_equation else gradient_var,
                # Full gradient expression
                'intercept_meaning': self.scientific_equation.c_meaning if self.scientific_equation else intercept_var
                # Full intercept expression
            }
        else:
            # Fallback for custom equations
            equation_info = {
                'name': 'Custom Linear Equation',
                'gradient_variable': 'm',
                'gradient_units': '',
                'intercept_variable': 'c',
                'intercept_units': '',
                'find_variable': None,
                'constants': {},
                'measurement_units': {},
                'gradient_meaning': 'm',
                'intercept_meaning': 'c'
            }

        # Store equation info in manager
        self.manager.set_equation_info(equation_info)

        # The transformed data is already stored in manager from _linearise_equation
        # Now navigate to GraphResults screen
        self.manager.show(GraphResultsScreen)

    def _extract_gradient_info(self):
        """Extract gradient variable name and units from selected equation."""
        if not self.selected_equation:
            return 'm', ''

        # Use the m_meaning from scientific_equation if available
        if self.scientific_equation and self.scientific_equation.m_meaning:
            gradient_var = self.scientific_equation.m_meaning
        else:
            gradient_var = 'gradient'

        # Try to infer units (this is simplified - you may want to expand)
        gradient_units = ''  # Default

        # For common equations, set appropriate units
        if 'decay' in self.selected_equation.name.lower() or 'λ' in gradient_var:
            gradient_units = 's⁻¹'
        elif 'attenuation' in self.selected_equation.name.lower() or 'μ' in gradient_var:
            gradient_units = 'm⁻¹'

        return gradient_var, gradient_units

    def _extract_intercept_info(self):
        """Extract intercept variable name and units from selected equation."""
        if not self.selected_equation:
            return 'c', ''

        # Use the c_meaning from scientific_equation if available
        if self.scientific_equation and self.scientific_equation.c_meaning:
            intercept_var = self.scientific_equation.c_meaning
        else:
            intercept_var = 'intercept'

        # Intercept units are often empty for log transformations
        intercept_units = ''

        return intercept_var, intercept_units

    def _identify_xy_vars(self) -> Tuple[str, str]:
        """
        Identify which selected variables should be x and y.

        Returns:
            Tuple of (x_variable_name, y_variable_name)
        """
        # Convert selected vars set to list for indexing
        vars_list = list(self.selected_vars)

        if len(vars_list) < 2:
            raise ValueError("Need at least 2 variables selected")

        # Simple heuristic: first selected is x, second is y
        # You could enhance this with user input or smart detection
        return vars_list[0], vars_list[1]

    def get_current_data(self) -> InputData:
        """
        Get the current data to use for analysis.

        Returns transformed data if transformation was applied,
        otherwise returns raw data.
        """
        if self.transformed_data is not None:
            return self.transformed_data
        return self.raw_data

    def revert_to_raw_data(self):
        """Revert to using raw untransformed data."""
        if self.data_transformer is not None:
            self.transformed_data = None
            self.manager.set_data(self.raw_data)
            messagebox.showinfo(
                "Data Reverted",
                "Data has been reverted to original raw measurements."
            )

    def _attempt_linearisation(self, equation, x_var, y_var, find_var):
        """
        Attempt to linearise equation with given x and y variable assignment.
        Returns tuple of (linearised_eq, x_var, y_var, x_transform, y_transform, grad_meaning, int_meaning)
        or None if linearisation fails.
        """
        x_temp, y_temp = sp.symbols("x y")

        # Create substitution map
        symbol_map = {
            sp.Symbol(x_var): x_temp,
            sp.Symbol(y_var): y_temp
        }

        # Apply mapping
        try:
            mapped_eq = equation.subs(symbol_map)
        except Exception:
            return None

        # Apply linearisation function
        try:
            linearised = self.linearise(mapped_eq)
        except Exception:
            return None

        # Now substitute back to original symbols for display
        reverse_map = {
            x_temp: sp.Symbol(x_var),
            y_temp: sp.Symbol(y_var)
        }
        linearised_with_original_symbols = linearised.subs(reverse_map)

        # Determine transformations by looking at the linearised equation
        x_transform, y_transform = self._identify_transforms(linearised, x_var, y_var)
        grad_meaning, int_meaning = self._identify_meanings(linearised, self.selected_equation,
                                                            x_var, y_var, find_var)

        return (linearised_with_original_symbols, x_var, y_var, x_transform, y_transform, grad_meaning, int_meaning)

    def _identify_transforms(self, linearised_eq, x_var, y_var):
        """Identify what transformations were applied to x and y."""
        x_temp, y_temp = sp.symbols("x y")

        # Default - no transformation
        x_transform = x_var
        y_transform = y_var

        lhs = linearised_eq.lhs
        rhs = linearised_eq.rhs

        # Check LHS for transformations of y
        if lhs.has(sp.log):
            # Check if it's log(y_temp)
            if lhs == sp.log(y_temp):
                y_transform = f"ln({y_var})"
            elif lhs.func == sp.log:
                y_transform = f"ln({y_var})"
        # Check if LHS has a coefficient (like e*y, not just y)
        elif lhs != y_temp and lhs.has(y_temp) and not lhs.has(y_temp ** 2):
            # Extract the full expression on LHS
            # For e*y, we want to show "e*V" as the Y-axis
            try:
                # Substitute back y_temp with the actual variable
                lhs_with_var = lhs.subs(y_temp, sp.Symbol(y_var))
                y_transform = str(lhs_with_var)
            except:
                y_transform = y_var

        # Check for powers of y (y², y³)
        if lhs == y_temp ** 2:
            y_transform = f"{y_var}²"
        elif lhs == y_temp ** 3:
            y_transform = f"{y_var}³"
        elif lhs.has(y_temp ** 2):
            y_transform = f"{y_var}²"
        elif lhs.has(y_temp ** 3):
            y_transform = f"{y_var}³"

        # Check RHS for transformations of x
        # Log transform
        if rhs.has(sp.log):
            for arg in sp.preorder_traversal(rhs):
                if isinstance(arg, sp.log) and arg.has(x_temp):
                    x_transform = f"ln({x_var})"
                    break

        # Power transforms (x², x³, etc.) - but not if it's a reciprocal
        if rhs.has(x_temp ** 2) and not rhs.has(1 / x_temp):
            x_transform = f"{x_var}²"
        elif rhs.has(x_temp ** 3):
            x_transform = f"{x_var}³"
        elif rhs.has(x_temp ** 4):
            x_transform = f"{x_var}⁴"

        # Reciprocal (1/x)
        if rhs.has(1 / x_temp):
            x_transform = f"1/{x_var}"

        return x_transform, y_transform

    def _identify_meanings(self, linearised_eq, original_eq, x_var, y_var, find_var):
        """Identify what the gradient and intercept represent."""
        x_temp, y_temp = sp.symbols("x y")

        # Get the linearised equation structure
        lhs = linearised_eq.lhs
        rhs = linearised_eq.rhs

        # Extract gradient and intercept from y = mx + c form
        try:
            # Expand and simplify the RHS
            rhs_expanded = sp.expand(rhs)

            # For reciprocal equations like V = hc/(e*λ), we have V = (hc/e)*(1/λ)
            # The RHS might be a fraction, so we need to handle that

            # Check if RHS has 1/x_temp term
            if rhs.has(1 / x_temp):
                # Extract the coefficient of 1/x_temp
                # The gradient is everything that multiplies 1/x

                # Method 1: Try to get coefficient directly
                try:
                    grad_coeff = rhs.coeff(1 / x_temp, 1)
                    if grad_coeff is None or grad_coeff == 0:
                        # Method 2: Multiply by x and simplify
                        grad_coeff = sp.simplify(rhs * x_temp)
                except:
                    # Method 3: Rewrite as numerator/denominator and extract
                    try:
                        # Convert to a single fraction
                        rhs_as_fraction = sp.together(rhs)
                        numer, denom = sp.fraction(rhs_as_fraction)

                        # The gradient is numer/denom when denom contains x
                        if x_temp in denom.free_symbols:
                            # Cancel out x from denominator to get coefficient
                            grad_coeff = sp.simplify(numer / (denom / x_temp))
                        else:
                            grad_coeff = sp.simplify(rhs * x_temp)
                    except:
                        grad_coeff = sp.simplify(rhs * x_temp)

                const_term = 0  # Reciprocal equations typically have no constant
            else:
                # Regular linear form: mx + c
                # Collect terms by x_temp
                grad_coeff = rhs_expanded.coeff(x_temp, 1)
                if grad_coeff is None:
                    grad_coeff = 0

                # Extract constant term (the intercept)
                const_term = rhs_expanded.coeff(x_temp, 0)
                if const_term is None:
                    const_term = 0

            # Convert back to original symbols for display
            reverse_map = {x_temp: sp.Symbol(x_var), y_temp: sp.Symbol(y_var)}
            grad_coeff_original = grad_coeff.subs(reverse_map) if grad_coeff != 0 else grad_coeff
            const_term_original = const_term.subs(reverse_map) if const_term != 0 else const_term

            # Create meaningful descriptions
            if grad_coeff_original != 0:
                # Simplify and format nicely
                grad_simplified = sp.simplify(grad_coeff_original)

                # Format as a fraction if it contains division
                if isinstance(grad_simplified, sp.Mul):
                    # Check if any factors are negative powers (division)
                    numer_factors = []
                    denom_factors = []
                    for factor in sp.Mul.make_args(grad_simplified):
                        if isinstance(factor, sp.Pow) and factor.exp < 0:
                            # This is in denominator
                            denom_factors.append(factor.base)
                        else:
                            numer_factors.append(factor)

                    if denom_factors:
                        # Format as fraction: numer/denom
                        numer_str = '*'.join(str(f) for f in numer_factors) if numer_factors else '1'
                        denom_str = '*'.join(str(f) for f in denom_factors)
                        grad_meaning = f"{numer_str}/{denom_str}"
                    else:
                        grad_meaning = str(grad_simplified)
                else:
                    grad_meaning = str(grad_simplified)

                # Clean up formatting
                grad_meaning = grad_meaning.replace('**', '^')
                grad_meaning = " ".join(grad_meaning.split())
            else:
                grad_meaning = "0"

            if const_term_original != 0:
                const_simplified = sp.simplify(const_term_original)
                int_meaning = str(const_simplified)
                int_meaning = int_meaning.replace('**', '^')
                int_meaning = " ".join(int_meaning.split())
            else:
                int_meaning = "0"

            # Add context based on equation type
            if original_eq.linearisation_type == "exponential":
                if original_eq.transform_info:
                    grad_meaning = original_eq.transform_info.get("gradient_meaning", grad_meaning)
                    int_meaning = original_eq.transform_info.get("intercept_meaning", int_meaning)

            # If find_var is specified, mention it
            if find_var:
                if find_var in str(grad_coeff_original):
                    grad_meaning += f" (contains {find_var})"
                if find_var in str(const_term_original):
                    int_meaning += f" (contains {find_var})"

            return grad_meaning, int_meaning

        except Exception as e:
            # Fallback to generic terms
            print(f"Error in _identify_meanings: {e}")  # Debug
            grad_meaning = "gradient"
            int_meaning = "y-intercept"

            if original_eq.linearisation_type == "exponential" and original_eq.transform_info:
                grad_meaning = original_eq.transform_info.get("gradient_meaning", "gradient")
                int_meaning = original_eq.transform_info.get("intercept_meaning", "y-intercept")

            if find_var:
                int_meaning += f" (can be used to find {find_var})"

            return grad_meaning, int_meaning

    def _display_linear_result(self, linearised_eq, x_var, y_var, find_var=None,
                               x_transform=None, y_transform=None,
                               grad_meaning=None, int_meaning=None):
        """Display the linearised equation and plotting instructions."""
        # Show the frame
        self.linearised_display_frame.pack(fill="both", expand=True, pady=(10, 15))

        # Display equation
        eq_str = sp.pretty(linearised_eq, use_unicode=True)
        self.linearised_equation_label.config(text=eq_str)

        # Display plotting information
        if x_transform is None:
            x_transform = x_var
        if y_transform is None:
            y_transform = y_var
        if grad_meaning is None:
            grad_meaning = "gradient"
        if int_meaning is None:
            int_meaning = "y-intercept"

        x_meaning = self.selected_equation.variables.get(x_var, x_var)
        y_meaning = self.selected_equation.variables.get(y_var, y_var)

        info_text = "Plotting Instructions:\n\n"
        info_text += f"📊 X-axis: {x_transform}\n"
        info_text += f"   ({x_meaning})\n\n"
        info_text += f"📊 Y-axis: {y_transform}\n"
        info_text += f"   ({y_meaning})\n\n"
        info_text += f"📈 Gradient represents: {grad_meaning}\n\n"
        info_text += f"📍 Y-intercept represents: {int_meaning}"

        if find_var:
            info_text += f"\n\n🎯 You can find {find_var} from the graph"

        self.linearised_info_label.config(text=info_text)

    @staticmethod
    def linearise(equation):
        """
        Linearise common non-linear functions for straight-line graphs.

        [Keep existing linearise implementation]
        """
        x, y = sp.symbols("x y")

        # Convert to equation if just an expression is passed
        if not isinstance(equation, sp.Eq):
            expr = equation
            if y in expr.free_symbols:
                if expr.is_Add or expr.is_Mul or expr.is_Pow:
                    equation = sp.Eq(y, expr)
                else:
                    equation = sp.Eq(expr, 0)
            else:
                equation = sp.Eq(y, expr)

        lhs = equation.lhs
        rhs = equation.rhs

        # Determine which side contains y
        if y in lhs.free_symbols and y not in rhs.free_symbols:
            y_side = lhs
            expr_side = rhs
        elif y in rhs.free_symbols and y not in lhs.free_symbols:
            y_side = rhs
            expr_side = lhs
        else:
            return equation

        # Check if equation is already linear (y = mx + c or y = mx form)
        # Linear means: expr_side is polynomial in x with degree <= 1
        if expr_side.is_polynomial(x):
            degree = sp.degree(expr_side, x)
            if degree <= 1:
                # Already linear - check if y is alone on the left side
                if y_side == y:
                    # Perfect - already in y = mx + c form
                    return equation
                else:
                    # y has a coefficient, solve for y to get y = ... form
                    try:
                        solved = sp.solve(equation, y)
                        if solved and len(solved) > 0:
                            return sp.Eq(y, solved[0])
                    except:
                        pass
                # If solving fails, return as-is
                return sp.Eq(y_side, expr_side)

        # If y is not alone and equation is non-linear, solve for y first
        if y_side != y:
            try:
                solved = sp.solve(equation, y)
                if solved and len(solved) > 0:
                    expr_side = solved[0]
                    y_side = y
            except:
                pass

        # Check for exponential
        if expr_side.has(sp.exp):
            exp_terms = [term for term in sp.preorder_traversal(expr_side) if isinstance(term, sp.exp)]

            if exp_terms:
                exp_term = exp_terms[0]
                exponent = exp_term.args[0]

                try:
                    coefficient = sp.simplify(expr_side / exp_term)

                    if y_side == y:
                        return sp.Eq(sp.log(y), sp.log(coefficient) + exponent)
                    else:
                        return sp.Eq(sp.log(y_side), sp.log(coefficient) + exponent)
                except:
                    pass

            return sp.Eq(y_side, expr_side)

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
    root.title("LineaX – Analysis Method")

    # class DummyManager:
    #     def show(self, *_): pass
    #
    #     def back(self): pass
    #
    #
    # AnalysisMethodScreen(root, DummyManager()).pack(fill="both", expand=True)
    manager = ScreenManager(root)
    manager.show(AnalysisMethodScreen)
    root.mainloop()