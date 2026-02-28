"""LinearGraphDisplay.py — Screen 3a (Linear Graph Results) from Section 3.2.2."""

import tkinter as tk
from tkinter import messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from LineaX_Classes import InputData, LinearGraph
from ManagingScreens import make_scrollable, ScreenManager
from GraphSettings import ChartElementsPopup, _DEFAULT_ELEMENT_STATES, _DEFAULT_LABEL_TEXTS, _fmt_coord
from GradientAnalysis import GradientAnalysisScreen
from NumberFormatting import format_number, format_number_with_uncertainty
from typing import Optional, Dict


class LinearGraphResultsScreen(tk.Frame):
    """Screen 3a: linear regression results with best-fit and worst-fit lines."""

    def __init__(self, parent, manager):
        super().__init__(parent, bg="#f5f6f8")
        self.manager = manager
        self.parent = parent
        self.input_data: Optional[InputData] = None
        self.linear_graph: Optional[LinearGraph] = None
        self.equation_name = self.gradient_variable = self.gradient_units = None
        self.intercept_variable = self.intercept_units = None
        self.best_fit_gradient = self.best_fit_intercept = None
        self.gradient_uncertainty = self.intercept_uncertainty = self.r_squared = None
        self.worst_fit_max_gradient = self.worst_fit_min_gradient = None
        self.max_percentage_diff = self.min_percentage_diff = None
        self.figure = self.canvas = None
        self.chart_elements_popup = None
        self.chart_element_states = dict(_DEFAULT_ELEMENT_STATES)
        self.chart_label_texts = dict(_DEFAULT_LABEL_TEXTS)

        if self._load_data_and_analyze():
            self.create_layout()
        else:
            self._create_error_layout()

    def _load_data_and_analyze(self) -> bool:
        self.input_data = self.manager.get_data()
        if self.input_data is None or len(getattr(self.input_data, 'x_values', [])) == 0:
            messagebox.showerror("No Data", "No valid data found. Please go back and check your inputs.")
            return False
        eq = (self.manager.get_equation_info() if hasattr(self.manager, 'get_equation_info') else {}) or {}
        self.equation_name = eq.get('name', 'Linear Equation')
        self.gradient_variable = eq.get('gradient_variable', 'm')
        self.gradient_units = eq.get('gradient_units', '')
        self.intercept_variable = eq.get('intercept_variable', 'c')
        self.intercept_units = eq.get('intercept_units', '')
        try:
            self._perform_linear_regression()
            self._calculate_worst_fit_lines()
            return True
        except Exception as e:
            messagebox.showerror("Analysis Error", f"Could not perform linear regression:\n{e}")
            return False

    def _perform_linear_regression(self):
        """Fit a weighted or unweighted least-squares line and compute R²."""
        x, y = self.input_data.x_values, self.input_data.y_values
        y_err = self.input_data.y_error
        if y_err is not None and np.any(y_err > 0):
            coeffs, cov = np.polyfit(x, y, 1, w=1.0 / (y_err ** 2), cov=True)
        else:
            coeffs, cov = np.polyfit(x, y, 1, cov=True)
        self.best_fit_gradient, self.best_fit_intercept = coeffs
        self.gradient_uncertainty = np.sqrt(cov[0, 0])
        self.intercept_uncertainty = np.sqrt(cov[1, 1])
        y_pred = self.best_fit_gradient * x + self.best_fit_intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        self.r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

    def _calculate_worst_fit_lines(self):
        """Estimate worst-case gradient bounds using first and last error bar extremes (Algorithm 5)."""
        x, y = self.input_data.x_values, self.input_data.y_values
        y_err = self.input_data.y_error
        if y_err is None or len(y_err) == 0:
            y_err = np.full_like(y, 0.01 * np.max(y))
        dx = x[-1] - x[0]
        self.worst_fit_max_gradient = ((y[-1] - y_err[-1]) - (y[0] + y_err[0])) / dx
        self.worst_fit_min_gradient = ((y[-1] + y_err[-1]) - (y[0] - y_err[0])) / dx
        if self.best_fit_gradient != 0:
            self.max_percentage_diff = abs((self.worst_fit_max_gradient - self.best_fit_gradient) / self.best_fit_gradient * 100)
            self.min_percentage_diff = abs((self.worst_fit_min_gradient - self.best_fit_gradient) / self.best_fit_gradient * 100)
        else:
            self.max_percentage_diff = self.min_percentage_diff = 0

    def create_layout(self):
        self.configure(padx=20, pady=20)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = tk.Frame(self, bg="white", height=80)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        header.pack_propagate(False)
        tk.Button(header, text="Back", font=("Segoe UI", 10), bg="#e5e7eb", fg="#0f172a",
                  relief="flat", cursor="hand2", command=self.manager.back).pack(side="left", padx=15, pady=10)

        title_box = tk.Frame(header, bg="white")
        title_box.pack(side="left", padx=(20, 0), pady=10)
        tk.Label(title_box, text="Graph Results - Linear Model", font=("Segoe UI", 16, "bold"),
                 bg="white", fg="#0f172a").pack(anchor="w")
        subtitle = f"Selected Equation: {self.equation_name}" if self.equation_name else "Linear regression analysis"
        tk.Label(title_box, text=subtitle, font=("Segoe UI", 9), bg="white", fg="#64748b").pack(anchor="w")

        btn_frame = tk.Frame(header, bg="white")
        btn_frame.pack(side="right", padx=15, pady=10)
        for text, cmd in [("Export", self.export_results), ("Chart Elements", self.open_chart_elements)]:
            tk.Button(btn_frame, text=text, font=("Segoe UI", 10), bg="white", fg="#0f172a",
                      relief="solid", bd=1, padx=20, pady=5, cursor="hand2", command=cmd).pack(side="left", padx=5)

        _, content, _, _ = make_scrollable(self, row=1, column=0, bg="white", padx=(10, 10), pady=(10, 10))
        self.graph_frame = tk.Frame(content, bg="white")
        self.graph_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.create_graph()

        results_cont = tk.Frame(content, bg="white")
        results_cont.pack(fill="x", padx=20, pady=(0, 20))
        for i in range(3):
            results_cont.columnconfigure(i, weight=1)
        self.create_results_panels(results_cont)

        tk.Button(content, text="Analyse Gradient ->", font=("Segoe UI", 12, "bold"), bg="#0f172a", fg="white",
                  relief="flat", cursor="hand2", padx=30, pady=15, command=self.analyze_gradient).pack(
            fill="x", padx=20, pady=(0, 20))

    def create_graph(self):
        """Draw data points, error bars, best-fit line and worst-fit lines."""
        if self.input_data is None:
            tk.Label(self.graph_frame, text="[Graph Display Area]",
                     font=("Segoe UI", 12), fg="#94a3b8", bg="white", justify="center").pack(expand=True)
            return

        states = self.chart_element_states
        self.figure = plt.Figure(figsize=(8, 5), dpi=100, facecolor='white')
        ax = self.figure.add_subplot(111)
        self.manager.set_graph_figure(self.figure)

        x, y = self.input_data.x_values, self.input_data.y_values
        ax.errorbar(x, y,
                    xerr=self.input_data.x_error if states['error_bars'] else None,
                    yerr=self.input_data.y_error if states['error_bars'] else None,
                    fmt='o', color='#3b82f6', ecolor='#94a3b8', capsize=4, markersize=6,
                    label='Data points' if states['legend'] else '', zorder=3)

        if states.get('data_labels'):
            for xi, yi in zip(x, y):
                ax.annotate(f'({_fmt_coord(xi)}, {_fmt_coord(yi)})', (xi, yi),
                            textcoords="offset points", xytext=(0, 10), ha='center', fontsize=7,
                            color='#334155', bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                                                       alpha=0.75, edgecolor='none'))

        if states['best_fit']:
            x_line = np.linspace(x[0], x[-1], 100)
            ax.plot(x_line, self.best_fit_gradient * x_line + self.best_fit_intercept,
                    color='#10b981', linewidth=2, label='Best fit' if states['legend'] else '', zorder=2)

        if states['worst_fit'] and self.input_data.y_error is not None:
            self._plot_worst_fit(ax, x, y, self.input_data.y_error, states['legend'])

        if states.get('chart_title'):
            ax.set_title(self.chart_label_texts.get('chart_title') or "Linear Regression Analysis",
                         fontsize=13, fontweight='bold', pad=15)
        if states.get('axis_titles'):
            ax.set_xlabel(self.chart_label_texts.get('x_title') or self.input_data.x_title or "X",
                          fontsize=11, fontweight='bold')
            ax.set_ylabel(self.chart_label_texts.get('y_title') or self.input_data.y_title or "Y",
                          fontsize=11, fontweight='bold')
        if states.get('major_gridlines'):
            ax.grid(True, which='major', alpha=0.35, linestyle='--', linewidth=0.6)
        if states.get('minor_gridlines'):
            ax.minorticks_on()
            ax.grid(True, which='minor', alpha=0.18, linestyle=':', linewidth=0.4)
        if states['legend']:
            ax.legend(loc='best', framealpha=0.9, fontsize=9)
        if not states['axes']:
            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.tick_params(left=False, bottom=False)

        self.figure.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _plot_worst_fit(self, ax, x, y, y_err, show_legend: bool):
        """Overlay worst-case max and min gradient lines (Algorithm 5 visual output)."""
        x_pts = [x[0], x[-1]]
        ax.plot(x_pts, [y[0] + y_err[0], y[-1] - y_err[-1]], color='#ef4444', linestyle='--',
                linewidth=1.5, label='Worst fit (max)' if show_legend else '', zorder=1)
        ax.plot(x_pts, [y[0] - y_err[0], y[-1] + y_err[-1]], color='#f97316', linestyle='--',
                linewidth=1.5, label='Worst fit (min)' if show_legend else '', zorder=1)

    def _make_panel(self, parent, title: str, fg: str, col: int) -> tk.Frame:
        frame = tk.LabelFrame(parent, text=f"  {title}  ", font=("Segoe UI", 10, "bold"),
                              bg="white", fg=fg, relief="solid", bd=2)
        frame.grid(row=0, column=col, padx=5, pady=5, sticky="nsew")
        inner = tk.Frame(frame, bg="white")
        inner.pack(fill="both", expand=True, padx=15, pady=10)
        return inner

    def _stat_row(self, parent, label: str, value: str):
        row = tk.Frame(parent, bg="white")
        row.pack(fill="x", pady=2)
        tk.Label(row, text=label, font=("Segoe UI", 9), bg="white", fg="#475569", anchor="w").pack(side="left")
        tk.Label(row, text=value, font=("Segoe UI", 9, "bold"), bg="white", fg="#0f172a", anchor="e").pack(side="right")

    def create_results_panels(self, parent):
        """Create best-fit, worst-fit max and worst-fit min panels."""
        best = self._make_panel(parent, "Best Fit Line", "#059669", 0)
        self._stat_row(best, "Gradient:", format_number_with_uncertainty(self.best_fit_gradient, self.gradient_uncertainty))
        self._stat_row(best, "Y-intercept:", format_number_with_uncertainty(self.best_fit_intercept, self.intercept_uncertainty))
        self._stat_row(best, "R value:", format_number(self.r_squared, 6))

        wmax = self._make_panel(parent, "Worst Fit (Max)", "#dc2626", 1)
        self._stat_row(wmax, "Gradient:", format_number(self.worst_fit_max_gradient))
        self._stat_row(wmax, "% Difference:", f"{self.max_percentage_diff:.2f}%")
        tk.Label(wmax, text="Max gradient through error bars", font=("Segoe UI", 8, "italic"),
                 bg="white", fg="#64748b").pack(anchor="w", pady=(5, 0))

        wmin = self._make_panel(parent, "Worst Fit (Min)", "#ea580c", 2)
        self._stat_row(wmin, "Gradient:", format_number(self.worst_fit_min_gradient))
        self._stat_row(wmin, "% Difference:", f"{self.min_percentage_diff:.2f}%")
        tk.Label(wmin, text="Min gradient through error bars", font=("Segoe UI", 8, "italic"),
                 bg="white", fg="#64748b").pack(anchor="w", pady=(5, 0))

    def create_stat_label(self, parent, label_text: str, value_text: str):
        """Alias for _stat_row to maintain external compatibility."""
        self._stat_row(parent, label_text, value_text)

    def open_chart_elements(self):
        if self.chart_elements_popup is not None:
            self.chart_elements_popup.lift()
            return
        initial_labels = {
            'chart_title': self.chart_label_texts.get('chart_title', ''),
            'x_title': self.chart_label_texts.get('x_title', '') or (self.input_data.x_title if self.input_data else ''),
            'y_title': self.chart_label_texts.get('y_title', '') or (self.input_data.y_title if self.input_data else ''),
        }
        self.chart_elements_popup = ChartElementsPopup(self.parent, self.update_chart_elements,
                                                       initial_labels=initial_labels)
        for k, v in self.chart_element_states.items():
            if k in self.chart_elements_popup.element_states:
                self.chart_elements_popup.element_states[k].set(v)

        def _on_close():
            self.chart_elements_popup.destroy()
            self.chart_elements_popup = None

        self.chart_elements_popup.protocol("WM_DELETE_WINDOW", _on_close)

    def update_chart_elements(self, states: Dict[str, bool], label_texts: Optional[Dict[str, str]] = None):
        self.chart_element_states = states
        if label_texts is not None:
            self.chart_label_texts = label_texts
        self.refresh_graph()

    def refresh_graph(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        if self.figure:
            plt.close(self.figure)
        self.create_graph()

    def export_results(self):
        if self.figure is None:
            messagebox.showwarning("No Graph", "No graph available to export.")
            return
        path = filedialog.asksaveasfilename(
            title="Export Graph", defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("PDF Document", "*.pdf"),
                       ("SVG Vector", "*.svg"), ("All Files", "*.*")]
        )
        if path:
            try:
                self.figure.savefig(path, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Export Successful", f"Graph exported to:\n{path}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Could not export graph:\n{e}")

    def analyze_gradient(self):
        """Package regression results and navigate to GradientAnalysisScreen."""
        eq = (self.manager.get_equation_info() if hasattr(self.manager, 'get_equation_info') else {}) or {}
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
            'find_variable': eq.get('find_variable'),
            'constants': eq.get('constants', {}),
            'measurement_units': eq.get('measurement_units', {}),
            'gradient_meaning': eq.get('gradient_meaning', self.gradient_variable),
            'intercept_meaning': eq.get('intercept_meaning', self.intercept_variable),
        }
        if hasattr(self.manager, 'set_analysis_results'):
            self.manager.set_analysis_results(analysis_data)
        self.manager.show(GradientAnalysisScreen)

    def _create_error_layout(self):
        self.configure(padx=20, pady=20)
        header = tk.Frame(self, bg="white", height=60)
        header.pack(fill="x", pady=(0, 15))
        header.pack_propagate(False)
        tk.Button(header, text="Back", font=("Segoe UI", 10), bg="#e5e7eb", fg="#0f172a",
                  relief="flat", cursor="hand2", command=self.manager.back).pack(side="left", padx=15, pady=10)
        err = tk.Frame(self, bg="white")
        err.pack(fill="both", expand=True)
        tk.Label(err, text="Error", font=("Segoe UI", 48), bg="white", fg="#dc2626").pack(pady=(100, 20))
        tk.Label(err, text="Cannot Display Graph", font=("Segoe UI", 20, "bold"),
                 bg="white", fg="#0f172a").pack(pady=(0, 10))
        tk.Label(err, text="There was an error loading or analysing the data.\nPlease go back and check your data.",
                 font=("Segoe UI", 12), bg="white", fg="#64748b", justify="center").pack(pady=(0, 20))