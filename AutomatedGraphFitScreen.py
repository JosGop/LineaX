"""
AutomatedGraphFitScreen.py - Automated Curve Fitting Screen

This screen displays automated curve fitting for non-linear models with Excel-style
chart customization. Matches the layout and functionality of LinearGraphDisplay.py.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score
from LineaX_Classes import InputData
from GraphSettings import ChartElementsPopup
from NumberFormatting import format_number
from typing import Optional, Dict


# Model functions
def linear(x, a, b):
    return a * x + b


def quadratic(x, a, b, c):
    return a * x**2 + b * x + c


def cubic(x, a, b, c, d):
    return a * x**3 + b * x**2 + c * x + d


def exponential_increase(x, a, b, c):
    return a * np.exp(b * x) + c


def exponential_decrease(x, a, b, c):
    return a * np.exp(-b * x) + c


def logarithmic(x, a, b, c):
    x = np.array(x)
    with np.errstate(divide='ignore', invalid='ignore'):
        result = a * np.log(b * x) + c
        result[np.isnan(result) | np.isinf(result) | (b * x <= 0)] = c
    return result


def logistic(x, a, b, c):
    return c / (1 + np.exp(-(x - b) / a))


def gaussian(x, a, b, c):
    return a * np.exp(-((x - b)**2) / (2 * c**2))


def sine(x, a, b, c, d):
    return a * np.sin(b * (x - c)) + d


class AutomatedGraphFitScreen(tk.Frame):
    def __init__(self, parent, manager):
        super().__init__(parent, bg="#f5f6f8")
        self.manager = manager
        self.parent = parent

        # Data
        self.input_data: Optional[InputData] = None

        # Model functions dictionary
        self.models = {
            "Linear": linear,
            "Quadratic": quadratic,
            "Cubic": cubic,
            "Exponential Increase": exponential_increase,
            "Exponential Decrease": exponential_decrease,
            "Logarithmic": logarithmic,
            "Logistic": logistic,
            "Gaussian": gaussian,
            "Sine": sine
        }

        # Store results
        self.results = {}
        self.best_model_name = None
        self.best_model_params = None
        self.selected_model = None

        # Matplotlib figure
        self.figure = None
        self.canvas = None

        # Chart customization (Note: no worst_fit for automated)
        self.chart_elements_popup = None
        self.chart_element_states = {
            'axes': True,
            'axis_titles': True,
            'chart_title': True,
            'data_labels': False,
            'error_bars': True,
            'gridlines': True,
            'legend': True,
            'best_fit': True,
            # Note: worst_fit not included for automated fitting
        }

        # Load data and perform analysis
        data_loaded = self._load_data_and_analyze()

        # Only create UI if data was loaded successfully
        if data_loaded:
            self.create_layout()
        else:
            # Show error screen with back button
            self._create_error_layout()

    def _load_data_and_analyze(self):
        """Load data from manager and perform curve fitting."""
        self.input_data = self.manager.get_data()

        if self.input_data is None:
            messagebox.showerror(
                "No Data",
                "No data found. Please go back and input your data."
            )
            return False

        # Check if input_data has valid values
        if (not hasattr(self.input_data, 'x_values') or not hasattr(self.input_data, 'y_values') or
            self.input_data.x_values is None or self.input_data.y_values is None or
            len(self.input_data.x_values) == 0 or len(self.input_data.y_values) == 0):
            messagebox.showerror(
                "Invalid Data",
                "The data does not contain valid x and y values. Please go back and check your data."
            )
            return False

        # Perform automated curve fitting
        try:
            self.fit_models()
            return True
        except Exception as e:
            messagebox.showerror(
                "Analysis Error",
                f"Could not perform curve fitting:\n{str(e)}\n\nPlease check your data."
            )
            return False

    def create_layout(self):
        """Create the main UI layout matching LinearGraphDisplay."""
        # Configure main frame padding
        self.configure(padx=20, pady=20)

        # Header
        header_frame = tk.Frame(self, bg="white", height=60)
        header_frame.pack(fill="x", pady=(0, 15))
        header_frame.pack_propagate(False)

        # Back button
        tk.Button(
            header_frame,
            text="← Back",
            font=("Segoe UI", 10),
            bg="#e5e7eb",
            fg="#0f172a",
            relief="flat",
            cursor="hand2",
            command=self.manager.back
        ).pack(side="left", padx=15, pady=10)

        # Title section
        title_container = tk.Frame(header_frame, bg="white")
        title_container.pack(side="left", padx=(20, 0), pady=10)

        tk.Label(
            title_container,
            text="Graph Results - Automated Fit",
            font=("Segoe UI", 16, "bold"),
            bg="white",
            fg="#0f172a"
        ).pack(anchor="w")

        best_model_text = f"Best model: {self.best_model_name}" if self.best_model_name else "Analyzing models..."
        self.subtitle_label = tk.Label(
            title_container,
            text=best_model_text,
            font=("Segoe UI", 9),
            bg="white",
            fg="#64748b"
        )
        self.subtitle_label.pack(anchor="w")

        # Export and Settings buttons
        button_frame = tk.Frame(header_frame, bg="white")
        button_frame.pack(side="right", padx=15, pady=10)

        tk.Button(
            button_frame,
            text="Export",
            font=("Segoe UI", 10),
            bg="white",
            fg="#0f172a",
            relief="solid",
            bd=1,
            padx=20,
            pady=5,
            cursor="hand2",
            command=self.export_results
        ).pack(side="left", padx=5)

        tk.Button(
            button_frame,
            text="⚙ Chart Elements",
            font=("Segoe UI", 10),
            bg="white",
            fg="#0f172a",
            relief="solid",
            bd=1,
            padx=20,
            pady=5,
            cursor="hand2",
            command=self.open_chart_elements
        ).pack(side="left", padx=5)

        # Main content container
        content_frame = tk.Frame(self, bg="white", relief="solid", bd=1)
        content_frame.pack(fill="both", expand=True)
        content_frame.pack_configure(padx=10, pady=10)

        # Graph display area
        self.graph_frame = tk.Frame(content_frame, bg="white")
        self.graph_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Create and display the graph
        self.create_graph()

        # Results panels
        results_container = tk.Frame(content_frame, bg="white")
        results_container.pack(fill="x", padx=20, pady=(0, 20))

        # Configure grid
        results_container.columnconfigure(0, weight=1)
        results_container.columnconfigure(1, weight=1)

        self.create_results_panels(results_container)

        # Note about automated fitting
        note_frame = tk.Frame(content_frame, bg="#fef3c7", relief="solid", bd=1)
        note_frame.pack(fill="x", padx=20, pady=(0, 10))

        note_container = tk.Frame(note_frame, bg="#fef3c7")
        note_container.pack(fill="x", padx=10, pady=8)

        tk.Label(
            note_container,
            text="ℹ️",
            font=("Segoe UI", 10),
            bg="#fef3c7",
            fg="#92400e"
        ).pack(side="left", padx=(0, 5))

        tk.Label(
            note_container,
            text="Note: Worst fit lines and gradient analysis are only available for linear models. "
                 "Automated fits show the single best-fitting curve for each model type.",
            font=("Segoe UI", 9),
            bg="#fef3c7",
            fg="#92400e",
            wraplength=800,
            justify="left"
        ).pack(side="left")

        # Save Results button
        tk.Button(
            content_frame,
            text="Save Results →",
            font=("Segoe UI", 12, "bold"),
            bg="#0f172a",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=30,
            pady=15,
            command=self.save_results
        ).pack(fill="x", padx=20, pady=(0, 20))

    def fit_models(self):
        """Fit all models to the data and identify the best one."""
        x_data = self.input_data.x_values
        y_data = self.input_data.y_values

        best_r2 = -np.inf
        self.best_model_name = None
        self.best_model_params = None

        for model_name, model_func in self.models.items():
            try:
                # Initial parameter guess
                if model_name == "Linear":
                    p0 = [1, 1]
                elif model_name in ["Quadratic", "Exponential Increase",
                                   "Exponential Decrease", "Logarithmic"]:
                    p0 = [1, 1, 1]
                elif model_name in ["Cubic", "Sine"]:
                    p0 = [1, 1, 1, 1]
                else:
                    p0 = None

                # Fit the model
                params, _ = curve_fit(
                    model_func, x_data, y_data,
                    p0=p0,
                    maxfev=10000
                )

                # Calculate R² score
                y_pred = model_func(x_data, *params)
                r2 = r2_score(y_data, y_pred)

                # Store results
                self.results[model_name] = (r2, params)

                # Track best model
                if r2 > best_r2:
                    best_r2 = r2
                    self.best_model_name = model_name
                    self.best_model_params = params

            except Exception as e:
                # If fitting fails, store None
                self.results[model_name] = (None, None)

        # Set selected model to best model initially
        self.selected_model = self.best_model_name

    def create_graph(self):
        """Create the matplotlib graph with customization options."""
        if self.input_data is None:
            placeholder = tk.Label(
                self.graph_frame,
                text="📈\n\n[Graph Display Area]\n\nData points with fitted curve",
                font=("Segoe UI", 12),
                fg="#94a3b8",
                bg="white",
                justify="center"
            )
            placeholder.pack(expand=True)
            return

        # Get current element states
        states = self.chart_element_states

        # Create figure
        self.figure = plt.Figure(figsize=(8, 5), dpi=100, facecolor='white')
        ax = self.figure.add_subplot(111)

        x = self.input_data.x_values
        y = self.input_data.y_values
        x_err = self.input_data.x_error if states['error_bars'] else None
        y_err = self.input_data.y_error if states['error_bars'] else None

        # Plot data points with error bars
        ax.errorbar(
            x, y,
            xerr=x_err,
            yerr=y_err,
            fmt='o',
            color='#3b82f6',
            ecolor='#94a3b8',
            capsize=4,
            markersize=6,
            label='Data points' if states['legend'] else '',
            zorder=3
        )

        # Add data labels if enabled
        if states['data_labels']:
            for i, (xi, yi) in enumerate(zip(x, y)):
                ax.annotate(
                    f'{yi:.2f}',
                    (xi, yi),
                    textcoords="offset points",
                    xytext=(0, 8),
                    ha='center',
                    fontsize=8,
                    color='#333'
                )

        # Plot fitted curve
        current_model = self.selected_model or self.best_model_name
        if current_model and current_model in self.results and states['best_fit']:
            result = self.results[current_model]
            if result[0] is not None:
                params = result[1]
                model_func = self.models[current_model]

                # Create smooth curve
                x_smooth = np.linspace(x.min(), x.max(), 200)
                y_smooth = model_func(x_smooth, *params)

                ax.plot(
                    x_smooth, y_smooth,
                    color='#10b981',
                    linewidth=2,
                    label=f'{current_model} fit' if states['legend'] else '',
                    zorder=2
                )

        # Chart title
        if states['chart_title']:
            ax.set_title(
                "Automated Curve Fitting",
                fontsize=13,
                fontweight='bold',
                pad=15
            )

        # Axis labels
        if states['axis_titles']:
            ax.set_xlabel(
                self.input_data.x_title or "X",
                fontsize=11,
                fontweight='bold'
            )
            ax.set_ylabel(
                self.input_data.y_title or "Y",
                fontsize=11,
                fontweight='bold'
            )

        # Grid
        if states['gridlines']:
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

        # Legend
        if states['legend']:
            ax.legend(loc='best', framealpha=0.9, fontsize=9)

        # Axes visibility
        if not states['axes']:
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.tick_params(left=False, bottom=False)

        # Tight layout
        self.figure.tight_layout()

        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def create_results_panels(self, parent):
        """Create the two results panels showing fit statistics and model selection."""

        # Fit Statistics Panel (Left)
        stats_frame = tk.LabelFrame(
            parent,
            text="  Fit Statistics  ",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#059669",
            relief="solid",
            bd=2
        )
        stats_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.stats_content = tk.Frame(stats_frame, bg="white")
        self.stats_content.pack(fill="both", expand=True, padx=15, pady=10)

        self.update_statistics_display()

        # Model Selection Panel (Right)
        model_frame = tk.LabelFrame(
            parent,
            text="  Model Selection  ",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#2563eb",
            relief="solid",
            bd=2
        )
        model_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        self.model_content = tk.Frame(model_frame, bg="white")
        self.model_content.pack(fill="both", expand=True, padx=15, pady=10)

        self.update_model_selection_display()

    def update_statistics_display(self):
        """Update the statistics panel with current model's data."""
        # Clear existing widgets
        for widget in self.stats_content.winfo_children():
            widget.destroy()

        current_model = self.selected_model or self.best_model_name

        if current_model and current_model in self.results:
            r2_value = self.results[current_model][0]
            rmse_value = self.calculate_rmse()
            equation_text = self.get_equation_text()

            self.create_stat_label(
                self.stats_content,
                "Model:",
                current_model
            )
            self.create_stat_label(
                self.stats_content,
                "R² value:",
                format_number(r2_value, 6) if r2_value is not None else "N/A"
            )
            self.create_stat_label(
                self.stats_content,
                "RMSE:",
                format_number(rmse_value) if rmse_value is not None else "N/A"
            )

            # Equation label (may wrap)
            tk.Label(
                self.stats_content,
                text="Equation:",
                font=("Segoe UI", 9),
                bg="white",
                fg="#475569",
                anchor="w"
            ).pack(anchor="w", pady=(10, 2))

            tk.Label(
                self.stats_content,
                text=equation_text,
                font=("Segoe UI", 9, "bold"),
                bg="white",
                fg="#0f172a",
                wraplength=250,
                justify="left"
            ).pack(anchor="w")

    def create_stat_label(self, parent, label_text, value_text):
        """Create a formatted statistic label."""
        container = tk.Frame(parent, bg="white")
        container.pack(fill="x", pady=2)

        tk.Label(
            container,
            text=label_text,
            font=("Segoe UI", 9),
            bg="white",
            fg="#475569",
            anchor="w"
        ).pack(side="left")

        tk.Label(
            container,
            text=value_text,
            font=("Segoe UI", 9, "bold"),
            bg="white",
            fg="#0f172a",
            anchor="e"
        ).pack(side="right")

    def calculate_rmse(self):
        """Calculate RMSE for current model."""
        current_model = self.selected_model or self.best_model_name
        if current_model not in self.results or self.results[current_model][0] is None:
            return None

        params = self.results[current_model][1]
        model_func = self.models[current_model]

        x_data = self.input_data.x_values
        y_data = self.input_data.y_values
        y_pred = model_func(x_data, *params)

        rmse = np.sqrt(np.mean((y_data - y_pred) ** 2))
        return rmse

    def get_equation_text(self):
        """Generate equation text based on selected model and parameters."""
        current_model = self.selected_model or self.best_model_name
        if current_model not in self.results or self.results[current_model][0] is None:
            return "N/A"

        params = self.results[current_model][1]

        if current_model == "Linear":
            return f"y = {format_number(params[0], 3)}x + {format_number(params[1], 3)}"
        elif current_model == "Quadratic":
            return f"y = {format_number(params[0], 3)}x² + {format_number(params[1], 3)}x + {format_number(params[2], 3)}"
        elif current_model == "Cubic":
            return f"y = {format_number(params[0], 3)}x³ + {format_number(params[1], 3)}x² + {format_number(params[2], 3)}x + {format_number(params[3], 3)}"
        elif current_model == "Exponential Increase":
            return f"y = {format_number(params[0], 3)}e^({format_number(params[1], 3)}x) + {format_number(params[2], 3)}"
        elif current_model == "Exponential Decrease":
            return f"y = {format_number(params[0], 3)}e^(-{format_number(params[1], 3)}x) + {format_number(params[2], 3)}"
        elif current_model == "Logarithmic":
            return f"y = {format_number(params[0], 3)}ln({format_number(params[1], 3)}x) + {format_number(params[2], 3)}"
        elif current_model == "Logistic":
            return f"y = {format_number(params[2], 3)} / (1 + e^(-(x-{format_number(params[1], 3)})/{format_number(params[0], 3)}))"
        elif current_model == "Gaussian":
            return f"y = {format_number(params[0], 3)}e^(-((x-{format_number(params[1], 3)})²/(2·{format_number(params[2], 3)}²)))"
        elif current_model == "Sine":
            return f"y = {format_number(params[0], 3)}sin({format_number(params[1], 3)}(x-{format_number(params[2], 3)})) + {format_number(params[3], 3)}"
        else:
            return "Complex equation"

    def update_model_selection_display(self):
        """Update the model selection panel with radio buttons."""
        for widget in self.model_content.winfo_children():
            widget.destroy()

        self.model_var = tk.StringVar(value=self.best_model_name)

        for model_name in self.models.keys():
            result = self.results.get(model_name)

            model_row = tk.Frame(self.model_content, bg="white")
            model_row.pack(fill="x", pady=2)

            if result and result[0] is not None:
                r2_value = result[0]

                rb = tk.Radiobutton(
                    model_row,
                    text=f"{model_name}:",
                    variable=self.model_var,
                    value=model_name,
                    font=("Segoe UI", 9),
                    bg="white",
                    activebackground="white",
                    command=self.on_model_selected
                )
                rb.pack(side="left", anchor="w")

                r2_label = tk.Label(
                    model_row,
                    text=f"R² = {format_number(r2_value, 4)}",
                    font=("Segoe UI", 9, "bold"),
                    bg="white",
                    fg="#2563eb"
                )
                r2_label.pack(side="right", anchor="e")

                if model_name == self.best_model_name:
                    check_label = tk.Label(
                        model_row,
                        text="✓",
                        font=("Segoe UI", 10, "bold"),
                        bg="white",
                        fg="#059669"
                    )
                    check_label.pack(side="right", padx=(0, 5))
            else:
                tk.Label(
                    model_row,
                    text=f"{model_name}: Error",
                    font=("Segoe UI", 9),
                    bg="white",
                    fg="#94a3b8"
                ).pack(side="left", anchor="w")

    def on_model_selected(self):
        """Handle model selection change."""
        self.selected_model = self.model_var.get()
        self.subtitle_label.config(text=f"Selected model: {self.selected_model}")
        self.update_statistics_display()
        self.refresh_graph()

    def open_chart_elements(self):
        """Open the Chart Elements customization popup."""
        if self.chart_elements_popup is not None:
            self.chart_elements_popup.lift()
            return

        # Create custom popup without worst_fit option
        self.chart_elements_popup = self._create_custom_chart_elements_popup()

        # Set initial states
        for key, value in self.chart_element_states.items():
            if key in self.chart_elements_popup.element_states:
                self.chart_elements_popup.element_states[key].set(value)

        # Clear reference when closed
        def on_popup_close():
            self.chart_elements_popup = None

        self.chart_elements_popup.protocol("WM_DELETE_WINDOW", on_popup_close)

    def _create_custom_chart_elements_popup(self):
        """Create a custom chart elements popup without worst_fit option."""
        popup = tk.Toplevel(self.parent)
        popup.title("Chart Elements")
        popup.geometry("250x350")
        popup.resizable(False, False)
        popup.configure(bg="#f0f0f0")
        popup.transient(self.parent)
        popup.attributes('-topmost', True)

        # Position near the parent window
        self._position_popup(popup)

        # Chart element states (no worst_fit for automated)
        popup.element_states = {
            'axes': tk.BooleanVar(value=True),
            'axis_titles': tk.BooleanVar(value=True),
            'chart_title': tk.BooleanVar(value=True),
            'data_labels': tk.BooleanVar(value=False),
            'error_bars': tk.BooleanVar(value=True),
            'gridlines': tk.BooleanVar(value=True),
            'legend': tk.BooleanVar(value=True),
            'best_fit': tk.BooleanVar(value=True),
        }

        # Create UI
        self._create_popup_ui(popup)

        return popup

    def _position_popup(self, popup):
        """Position the popup near the parent window."""
        popup.update_idletasks()
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        x = parent_x + parent_width - 270
        y = parent_y + 100
        popup.geometry(f"+{x}+{y}")

    def _create_popup_ui(self, popup):
        """Create the checkbox interface for the popup."""
        # Header
        header = tk.Frame(popup, bg="#0078d4", height=35)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="⚙ Chart Elements",
            font=("Segoe UI", 11, "bold"),
            bg="#0078d4",
            fg="white"
        ).pack(side="left", padx=10, pady=8)

        # Main content area
        content = tk.Frame(popup, bg="white", padx=5, pady=10)
        content.pack(fill="both", expand=True)

        # Chart elements list (no worst_fit)
        elements = [
            ('axes', 'Axes'),
            ('axis_titles', 'Axis Titles'),
            ('chart_title', 'Chart Title'),
            ('data_labels', 'Data Labels'),
            ('error_bars', 'Error Bars'),
            ('gridlines', 'Gridlines'),
            ('legend', 'Legend'),
            ('best_fit', 'Best Fit Line'),
        ]

        for key, label in elements:
            self._create_popup_checkbox(popup, content, key, label)

        # Separator
        tk.Frame(content, bg="#d1d5db", height=1).pack(fill="x", pady=10)

        # Action buttons
        button_frame = tk.Frame(content, bg="white")
        button_frame.pack(fill="x", pady=5)

        tk.Button(
            button_frame,
            text="Reset to Default",
            font=("Segoe UI", 9),
            bg="#f0f0f0",
            fg="#333",
            relief="solid",
            bd=1,
            cursor="hand2",
            command=lambda: self._reset_popup_defaults(popup)
        ).pack(side="left", padx=5)

        tk.Button(
            button_frame,
            text="Apply",
            font=("Segoe UI", 9, "bold"),
            bg="#0078d4",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=15,
            command=lambda: self._apply_popup_changes(popup)
        ).pack(side="right", padx=5)

    def _create_popup_checkbox(self, popup, parent, key, label):
        """Create a single checkbox item with hover effect."""
        item_frame = tk.Frame(parent, bg="white", height=32)
        item_frame.pack(fill="x", pady=1)
        item_frame.pack_propagate(False)

        checkbox = tk.Checkbutton(
            item_frame,
            text=label,
            variable=popup.element_states[key],
            font=("Segoe UI", 10),
            bg="white",
            activebackground="#e5f3ff",
            selectcolor="white",
            relief="flat",
            cursor="hand2",
            command=lambda: self._on_popup_element_toggle(popup)
        )
        checkbox.pack(side="left", padx=10, pady=5, fill="both", expand=True)

        # Hover effects
        def on_enter(e):
            item_frame.config(bg="#e5f3ff")
            checkbox.config(bg="#e5f3ff")

        def on_leave(e):
            item_frame.config(bg="white")
            checkbox.config(bg="white")

        item_frame.bind("<Enter>", on_enter)
        item_frame.bind("<Leave>", on_leave)
        checkbox.bind("<Enter>", on_enter)
        checkbox.bind("<Leave>", on_leave)

    def _on_popup_element_toggle(self, popup):
        """Called when a checkbox is toggled."""
        states = {key: var.get() for key, var in popup.element_states.items()}
        self.update_chart_elements(states)

    def _reset_popup_defaults(self, popup):
        """Reset all elements to their default states."""
        defaults = {
            'axes': True,
            'axis_titles': True,
            'chart_title': True,
            'data_labels': False,
            'error_bars': True,
            'gridlines': True,
            'legend': True,
            'best_fit': True,
        }

        for key, value in defaults.items():
            popup.element_states[key].set(value)

        self.update_chart_elements(defaults)

    def _apply_popup_changes(self, popup):
        """Apply changes and close the window."""
        states = {key: var.get() for key, var in popup.element_states.items()}
        self.update_chart_elements(states)
        popup.destroy()

    def update_chart_elements(self, states: Dict[str, bool]):
        """Update the chart based on new element states."""
        self.chart_element_states = states
        self.refresh_graph()

    def refresh_graph(self):
        """Refresh the graph with current element states."""
        # Clear existing graph
        if self.canvas:
            self.canvas.get_tk_widget().destroy()

        if self.figure:
            plt.close(self.figure)

        # Recreate graph
        self.create_graph()

    def export_results(self):
        """Export graph and results to file."""
        if self.figure is None:
            messagebox.showwarning("No Graph", "No graph available to export.")
            return

        filepath = filedialog.asksaveasfilename(
            title="Export Graph",
            defaultextension=".png",
            filetypes=[
                ("PNG Image", "*.png"),
                ("PDF Document", "*.pdf"),
                ("SVG Vector", "*.svg"),
                ("All Files", "*.*")
            ]
        )

        if filepath:
            try:
                self.figure.savefig(filepath, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Export Successful", f"Graph exported to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Could not export graph:\n{str(e)}")

    def save_results(self):
        """Save results and show confirmation."""
        current_model = self.selected_model or self.best_model_name

        if current_model and current_model in self.results:
            r2 = self.results[current_model][0]

            if r2 is not None:
                messagebox.showinfo(
                    "Results Saved",
                    f"Results saved for {current_model} model\n\n"
                    f"R² value: {r2:.6f}\n"
                    f"RMSE: {self.calculate_rmse():.4f}\n\n"
                    f"Note: Linear models can be analyzed further through "
                    f"the Linear Analysis workflow for gradient analysis."
                )
            else:
                messagebox.showwarning(
                    "Model Error",
                    f"The {current_model} model failed to fit the data."
                )
        else:
            messagebox.showwarning(
                "No Model Selected",
                "Please select a model to save results."
            )

    def _create_error_layout(self):
        """Create a simple error screen with back button when data loading fails."""
        # Configure main frame padding
        self.configure(padx=20, pady=20)

        # Header
        header_frame = tk.Frame(self, bg="white", height=60)
        header_frame.pack(fill="x", pady=(0, 15))
        header_frame.pack_propagate(False)

        # Back button
        tk.Button(
            header_frame,
            text="← Back",
            font=("Segoe UI", 10),
            bg="#e5e7eb",
            fg="#0f172a",
            relief="flat",
            cursor="hand2",
            command=self.manager.back
        ).pack(side="left", padx=15, pady=10)

        # Error message
        error_container = tk.Frame(self, bg="white")
        error_container.pack(fill="both", expand=True)

        tk.Label(
            error_container,
            text="⚠️",
            font=("Segoe UI", 48),
            bg="white",
            fg="#dc2626"
        ).pack(pady=(100, 20))

        tk.Label(
            error_container,
            text="Cannot Display Graph",
            font=("Segoe UI", 20, "bold"),
            bg="white",
            fg="#0f172a"
        ).pack(pady=(0, 10))

        tk.Label(
            error_container,
            text="There was an error loading or analyzing the data.\n"
                 "Please go back and check your data.",
            font=("Segoe UI", 12),
            bg="white",
            fg="#64748b",
            justify="center"
        ).pack(pady=(0, 20))