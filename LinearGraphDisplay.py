"""
GraphResults.py - Linear Model Analysis Screen with Chart Customization

This screen displays the linearised graph with best fit and worst fit lines,
along with statistical analysis results and Excel-style chart customization.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from LineaX_Classes import InputData, LinearGraph
from GraphSettings import ChartElementsPopup
from GradientAnalysis import GradientAnalysisScreen
from typing import Optional, Tuple, Dict


class GraphResultsScreen(tk.Frame):
    def __init__(self, parent, manager):
        super().__init__(parent, bg="#f5f6f8")
        self.manager = manager
        self.parent = parent
        
        # Data and analysis results
        self.input_data: Optional[InputData] = None
        self.linear_graph: Optional[LinearGraph] = None
        
        # Equation information
        self.equation_name: Optional[str] = None
        self.gradient_variable: Optional[str] = None
        self.gradient_units: Optional[str] = None
        self.intercept_variable: Optional[str] = None
        self.intercept_units: Optional[str] = None
        
        # Fit results
        self.best_fit_gradient: Optional[float] = None
        self.best_fit_intercept: Optional[float] = None
        self.gradient_uncertainty: Optional[float] = None
        self.intercept_uncertainty: Optional[float] = None
        self.r_squared: Optional[float] = None
        
        # Worst fit results
        self.worst_fit_max_gradient: Optional[float] = None
        self.worst_fit_min_gradient: Optional[float] = None
        self.max_percentage_diff: Optional[float] = None
        self.min_percentage_diff: Optional[float] = None
        
        # Matplotlib figure
        self.figure = None
        self.canvas = None
        
        # Chart customization
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
            'worst_fit': True,
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
        """Load transformed data from manager and perform linear regression."""
        self.input_data = self.manager.get_data()

        print(f"DEBUG: input_data = {self.input_data}")  # Debug

        if self.input_data is None:
            print("DEBUG: input_data is None")  # Debug
            messagebox.showerror(
                "No Data",
                "No data found. Please go back and input your data."
            )
            return False

        # Check if input_data has valid values
        print(f"DEBUG: x_values = {getattr(self.input_data, 'x_values', 'NO ATTR')}")  # Debug
        print(f"DEBUG: y_values = {getattr(self.input_data, 'y_values', 'NO ATTR')}")  # Debug

        if (not hasattr(self.input_data, 'x_values') or not hasattr(self.input_data, 'y_values') or
            self.input_data.x_values is None or self.input_data.y_values is None or
            len(self.input_data.x_values) == 0 or len(self.input_data.y_values) == 0):
            print("DEBUG: Data validation failed")  # Debug
            messagebox.showerror(
                "Invalid Data",
                "The data does not contain valid x and y values. Please go back and check your data."
            )
            return False

        print(f"DEBUG: Data looks valid, proceeding with analysis")  # Debug

        # Try to get equation information from manager
        equation_info = self.manager.get_equation_info() if hasattr(self.manager, 'get_equation_info') else None
        if equation_info:
            self.equation_name = equation_info.get('name', 'Linear Equation')
            self.gradient_variable = equation_info.get('gradient_variable', 'm')
            self.gradient_units = equation_info.get('gradient_units', '')
            self.intercept_variable = equation_info.get('intercept_variable', 'c')
            self.intercept_units = equation_info.get('intercept_units', '')
        else:
            self.equation_name = 'Linear Equation'
            self.gradient_variable = 'm'
            self.gradient_units = ''
            self.intercept_variable = 'c'
            self.intercept_units = ''

        # Perform linear regression analysis
        try:
            print("DEBUG: Starting linear regression")  # Debug
            self._perform_linear_regression()
            print("DEBUG: Starting worst fit calculation")  # Debug
            self._calculate_worst_fit_lines()
            print("DEBUG: Analysis complete")  # Debug
            return True
        except Exception as e:
            print(f"DEBUG: Analysis failed with exception: {e}")  # Debug
            import traceback
            traceback.print_exc()
            messagebox.showerror(
                "Analysis Error",
                f"Could not perform linear regression analysis:\n{str(e)}\n\nPlease check your data."
            )
            return False

    def _perform_linear_regression(self):
        """Perform linear regression on the data to get best fit line."""
        x = self.input_data.x_values
        y = self.input_data.y_values
        x_err = self.input_data.x_error
        y_err = self.input_data.y_error

        # Weighted least squares if errors are available
        if y_err is not None and np.any(y_err > 0):
            weights = 1.0 / (y_err ** 2)
            coeffs, cov = np.polyfit(x, y, 1, w=weights, cov=True)
        else:
            coeffs, cov = np.polyfit(x, y, 1, cov=True)

        self.best_fit_gradient = coeffs[0]
        self.best_fit_intercept = coeffs[1]

        # Extract uncertainties from covariance matrix
        self.gradient_uncertainty = np.sqrt(cov[0, 0])
        self.intercept_uncertainty = np.sqrt(cov[1, 1])

        # Calculate R² value
        y_pred = self.best_fit_gradient * x + self.best_fit_intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        self.r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

    def _calculate_worst_fit_lines(self):
        """Calculate worst fit lines using first and last error bars."""
        x = self.input_data.x_values
        y = self.input_data.y_values
        y_err = self.input_data.y_error

        if y_err is None or len(y_err) == 0:
            y_err = np.full_like(y, 0.01 * np.max(y))

        # Worst fit line 1: max gradient
        y_worst1 = [y[0] + y_err[0], y[-1] - y_err[-1]]
        x_worst = [x[0], x[-1]]
        self.worst_fit_max_gradient = (y_worst1[1] - y_worst1[0]) / (x_worst[1] - x_worst[0])

        # Worst fit line 2: min gradient
        y_worst2 = [y[0] - y_err[0], y[-1] + y_err[-1]]
        self.worst_fit_min_gradient = (y_worst2[1] - y_worst2[0]) / (x_worst[1] - x_worst[0])

        # Calculate percentage differences
        if self.best_fit_gradient != 0:
            self.max_percentage_diff = abs(
                (self.worst_fit_max_gradient - self.best_fit_gradient) /
                self.best_fit_gradient * 100
            )
            self.min_percentage_diff = abs(
                (self.worst_fit_min_gradient - self.best_fit_gradient) /
                self.best_fit_gradient * 100
            )
        else:
            self.max_percentage_diff = 0
            self.min_percentage_diff = 0

    def create_layout(self):
        """Create the main UI layout."""
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
            text="Graph Results - Linear Model",
            font=("Segoe UI", 16, "bold"),
            bg="white",
            fg="#0f172a"
        ).pack(anchor="w")

        subtitle_text = f"Selected Equation: {self.equation_name}" if self.equation_name else "Linear regression analysis"
        tk.Label(
            title_container,
            text=subtitle_text,
            font=("Segoe UI", 9),
            bg="white",
            fg="#64748b"
        ).pack(anchor="w")

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
        results_container.columnconfigure(2, weight=1)

        self.create_results_panels(results_container)

        # Analyze Gradient button
        tk.Button(
            content_frame,
            text="Analyse Gradient →",
            font=("Segoe UI", 12, "bold"),
            bg="#0f172a",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=30,
            pady=15,
            command=self.analyze_gradient
        ).pack(fill="x", padx=20, pady=(0, 20))

    def create_graph(self):
        """Create the matplotlib graph with customization options."""
        if self.input_data is None:
            placeholder = tk.Label(
                self.graph_frame,
                text="📈\n\n[Graph Display Area]\n\nData points with best fit line and worst fit lines",
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

        # Plot best fit line
        if states['best_fit']:
            x_line = np.linspace(x[0], x[-1], 100)
            y_best = self.best_fit_gradient * x_line + self.best_fit_intercept
            ax.plot(
                x_line, y_best,
                color='#10b981',
                linewidth=2,
                label='Best fit' if states['legend'] else '',
                zorder=2
            )

        # Plot worst fit lines
        if states['worst_fit'] and self.input_data.y_error is not None:
            self.plot_worst_fit_lines(ax, x, y, self.input_data.y_error, states['legend'])

        # Chart title
        if states['chart_title']:
            ax.set_title(
                "Linear Regression Analysis",
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

    def plot_worst_fit_lines(self, ax, x, y, y_err, show_in_legend):
        """Plot worst fit lines using first and last error bars."""
        y_worst1 = [y[0] + y_err[0], y[-1] - y_err[-1]]
        y_worst2 = [y[0] - y_err[0], y[-1] + y_err[-1]]
        x_worst = [x[0], x[-1]]

        ax.plot(
            x_worst, y_worst1,
            color='#ef4444',
            linestyle='--',
            linewidth=1.5,
            label='Worst fit (max)' if show_in_legend else '',
            zorder=1
        )
        ax.plot(
            x_worst, y_worst2,
            color='#f97316',
            linestyle='--',
            linewidth=1.5,
            label='Worst fit (min)' if show_in_legend else '',
            zorder=1
        )

    def create_results_panels(self, parent):
        """Create the three results panels showing fit statistics."""

        # Best Fit Panel (Green)
        best_fit_frame = tk.LabelFrame(
            parent,
            text="  Best Fit Line  ",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#059669",
            relief="solid",
            bd=2
        )
        best_fit_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        inner_best = tk.Frame(best_fit_frame, bg="white")
        inner_best.pack(fill="both", expand=True, padx=15, pady=10)

        self.create_stat_label(
            inner_best,
            "Gradient:",
            f"{self.best_fit_gradient:.4e} ± {self.gradient_uncertainty:.4e}"
        )
        self.create_stat_label(
            inner_best,
            "Y-intercept:",
            f"{self.best_fit_intercept:.4e} ± {self.intercept_uncertainty:.4e}"
        )
        self.create_stat_label(
            inner_best,
            "R² value:",
            f"{self.r_squared:.6f}"
        )

        # Worst Fit Max Panel (Red)
        worst_max_frame = tk.LabelFrame(
            parent,
            text="  Worst Fit (Max)  ",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#dc2626",
            relief="solid",
            bd=2
        )
        worst_max_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        inner_max = tk.Frame(worst_max_frame, bg="white")
        inner_max.pack(fill="both", expand=True, padx=15, pady=10)

        self.create_stat_label(
            inner_max,
            "Gradient:",
            f"{self.worst_fit_max_gradient:.4e}"
        )
        self.create_stat_label(
            inner_max,
            "% Difference:",
            f"{self.max_percentage_diff:.2f}%"
        )
        tk.Label(
            inner_max,
            text="Max gradient through error bars",
            font=("Segoe UI", 8, "italic"),
            bg="white",
            fg="#64748b"
        ).pack(anchor="w", pady=(5, 0))

        # Worst Fit Min Panel (Orange)
        worst_min_frame = tk.LabelFrame(
            parent,
            text="  Worst Fit (Min)  ",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#ea580c",
            relief="solid",
            bd=2
        )
        worst_min_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")

        inner_min = tk.Frame(worst_min_frame, bg="white")
        inner_min.pack(fill="both", expand=True, padx=15, pady=10)

        self.create_stat_label(
            inner_min,
            "Gradient:",
            f"{self.worst_fit_min_gradient:.4e}"
        )
        self.create_stat_label(
            inner_min,
            "% Difference:",
            f"{self.min_percentage_diff:.2f}%"
        )
        tk.Label(
            inner_min,
            text="Min gradient through error bars",
            font=("Segoe UI", 8, "italic"),
            bg="white",
            fg="#64748b"
        ).pack(anchor="w", pady=(5, 0))

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

    def open_chart_elements(self):
        """Open the Chart Elements customization popup."""
        if self.chart_elements_popup is not None:
            self.chart_elements_popup.lift()
            return

        self.chart_elements_popup = ChartElementsPopup(
            self.parent,
            self.update_chart_elements
        )

        # Set initial states
        for key, value in self.chart_element_states.items():
            if key in self.chart_elements_popup.element_states:
                self.chart_elements_popup.element_states[key].set(value)

        # Clear reference when closed
        def on_popup_close():
            self.chart_elements_popup = None

        self.chart_elements_popup.protocol("WM_DELETE_WINDOW", on_popup_close)

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

    def analyze_gradient(self):
        """Navigate to gradient analysis screen with results."""
        # Get equation info from manager
        equation_info = self.manager.get_equation_info() if hasattr(self.manager, 'get_equation_info') else {}

        # Store analysis results for next screen
        analysis_data = {
            'equation_name': self.equation_name,
            'gradient': self.best_fit_gradient,
            'gradient_uncertainty': self.gradient_uncertainty,
            'gradient_variable': self.gradient_variable,
            'gradient_units': self.gradient_units,
            'intercept': self.best_fit_intercept,
            'intercept_uncertainty': self.intercept_uncertainty,
            'intercept_variable': self.intercept_variable,
            'intercept_units': self.intercept_units,
            # Add new fields for solving
            'find_variable': equation_info.get('find_variable'),  # Variable user wants to find
            'constants': equation_info.get('constants', {}),  # Known constant values
            'measurement_units': equation_info.get('measurement_units', {}),  # NEW: User-entered units
            'gradient_meaning': equation_info.get('gradient_meaning', self.gradient_variable),  # Full gradient expression
            'intercept_meaning': equation_info.get('intercept_meaning', self.intercept_variable)  # Full intercept expression
        }

        # Store in manager
        if hasattr(self.manager, 'set_analysis_results'):
            self.manager.set_analysis_results(analysis_data)

        # Navigate to gradient analysis screen
        self.manager.show(GradientAnalysisScreen)

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
            text="There was an error loading or analyzing the data.\nPlease go back and check your data and equation settings.",
            font=("Segoe UI", 12),
            bg="white",
            fg="#64748b",
            justify="center"
        ).pack(pady=(0, 20))