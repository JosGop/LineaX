"""AutomatedGraphDisplay.py — Screen 3b (Automated Curve Fitting) from Section 3.2.2."""

import tkinter as tk
from tkinter import messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score
from LineaX_Classes import InputData
from GraphSettings import ChartElementsPopup, _DEFAULT_ELEMENT_STATES, _DEFAULT_LABEL_TEXTS, _fmt_coord
from NumberFormatting import format_number
from ManagingScreens import make_scrollable
from typing import Optional, Dict


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


_MODEL_P0 = {
    "Linear": [1, 1], "Quadratic": [1, 1, 1], "Exponential Increase": [1, 1, 1],
    "Exponential Decrease": [1, 1, 1], "Logarithmic": [1, 1, 1],
    "Cubic": [1, 1, 1, 1], "Sine": [1, 1, 1, 1],
}

_EQ_TEMPLATES = {
    "Linear":               lambda p, f: f"y = {f(p[0])}x + {f(p[1])}",
    "Quadratic":            lambda p, f: f"y = {f(p[0])}x^2 + {f(p[1])}x + {f(p[2])}",
    "Cubic":                lambda p, f: f"y = {f(p[0])}x^3 + {f(p[1])}x^2 + {f(p[2])}x + {f(p[3])}",
    "Exponential Increase": lambda p, f: f"y = {f(p[0])}e^({f(p[1])}x) + {f(p[2])}",
    "Exponential Decrease": lambda p, f: f"y = {f(p[0])}e^(-{f(p[1])}x) + {f(p[2])}",
    "Logarithmic":          lambda p, f: f"y = {f(p[0])}ln({f(p[1])}x) + {f(p[2])}",
    "Logistic":             lambda p, f: f"y = {f(p[2])} / (1 + e^(-(x-{f(p[1])})/{f(p[0])}))",
    "Gaussian":             lambda p, f: f"y = {f(p[0])}e^(-((x-{f(p[1])})^2/(2*{f(p[2])}^2)))",
    "Sine":                 lambda p, f: f"y = {f(p[0])}sin({f(p[1])}(x-{f(p[2])})) + {f(p[3])}",
}


class AutomatedGraphResultsScreen(tk.Frame):
    """Screen 3b: automated curve fitting results with R² model comparison."""

    def __init__(self, parent, manager):
        super().__init__(parent, bg="#f5f6f8")
        self.manager = manager
        self.parent = parent
        self.input_data: Optional[InputData] = None
        self.models = {
            "Linear": linear, "Quadratic": quadratic, "Cubic": cubic,
            "Exponential Increase": exponential_increase, "Exponential Decrease": exponential_decrease,
            "Logarithmic": logarithmic, "Logistic": logistic, "Gaussian": gaussian, "Sine": sine,
        }
        self.results: Dict = {}
        self.best_model_name = self.best_model_params = self.selected_model = None
        self.figure = self.canvas = None
        self.chart_elements_popup = None
        self.chart_element_states = {k: v for k, v in _DEFAULT_ELEMENT_STATES.items() if k != 'worst_fit'}
        self.chart_label_texts = dict(_DEFAULT_LABEL_TEXTS)

        if self._load_data_and_analyze():
            self.create_layout()
        else:
            self._create_error_layout()

    def _load_data_and_analyze(self) -> bool:
        self.input_data = self.manager.get_data()
        if self.input_data is None:
            messagebox.showerror("No Data", "No data found. Please go back and input your data.")
            return False
        if not len(getattr(self.input_data, 'x_values', [])):
            messagebox.showerror("Invalid Data", "The data does not contain valid x and y values.")
            return False
        try:
            self.fit_models()
            return True
        except Exception as e:
            messagebox.showerror("Analysis Error", f"Could not perform curve fitting:\n{e}\n\nPlease check your data.")
            return False

    def create_layout(self):
        self.configure(padx=20, pady=20)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = tk.Frame(self, bg="white", height=80)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        header.pack_propagate(False)
        tk.Button(header, text="Back", font=("Segoe UI", 10), bg="#e5e7eb", fg="#0f172a",
                  relief="flat", cursor="hand2", command=self.manager.back).pack(side="left", padx=15, pady=10)

        title_container = tk.Frame(header, bg="white")
        title_container.pack(side="left", padx=(20, 0), pady=10)
        tk.Label(title_container, text="Graph Results - Automated Fit", font=("Segoe UI", 16, "bold"),
                 bg="white", fg="#0f172a").pack(anchor="w")
        best_model_text = f"Best model: {self.best_model_name}" if self.best_model_name else "Analysing models..."
        self.subtitle_label = tk.Label(title_container, text=best_model_text, font=("Segoe UI", 9),
                                       bg="white", fg="#64748b")
        self.subtitle_label.pack(anchor="w")

        button_frame = tk.Frame(header, bg="white")
        button_frame.pack(side="right", padx=15, pady=10)
        for text, cmd in [("Export", self.export_results), ("Chart Elements", self.open_chart_elements)]:
            tk.Button(button_frame, text=text, font=("Segoe UI", 10), bg="white", fg="#0f172a",
                      relief="solid", bd=1, padx=20, pady=5, cursor="hand2", command=cmd).pack(side="left", padx=5)

        _, content_frame, _, _ = make_scrollable(self, row=1, column=0, bg="white", padx=(10, 10), pady=(10, 10))
        self.graph_frame = tk.Frame(content_frame, bg="white")
        self.graph_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.create_graph()

        results_container = tk.Frame(content_frame, bg="white")
        results_container.pack(fill="x", padx=20, pady=(0, 20))
        results_container.columnconfigure(0, weight=1)
        results_container.columnconfigure(1, weight=1)
        self.create_results_panels(results_container)

        note_frame = tk.Frame(content_frame, bg="#fef3c7", relief="solid", bd=1)
        note_frame.pack(fill="x", padx=20, pady=(0, 10))
        note_inner = tk.Frame(note_frame, bg="#fef3c7")
        note_inner.pack(fill="x", padx=10, pady=8)
        tk.Label(note_inner, text="Note:", font=("Segoe UI", 10), bg="#fef3c7", fg="#92400e").pack(side="left", padx=(0, 5))
        tk.Label(note_inner,
                 text="Worst fit lines and gradient analysis are only available for linear models. "
                      "Automated fits show the single best-fitting curve for each model type.",
                 font=("Segoe UI", 9), bg="#fef3c7", fg="#92400e", wraplength=800, justify="left").pack(side="left")

        tk.Button(content_frame, text="Save Results ->", font=("Segoe UI", 12, "bold"), bg="#0f172a", fg="white",
                  relief="flat", cursor="hand2", padx=30, pady=15, command=self.save_results).pack(
            fill="x", padx=20, pady=(0, 20))

    def fit_models(self):
        """Fit all nine models and identify the best by R² score (Algorithms 7 and 8)."""
        x_data, y_data = self.input_data.x_values, self.input_data.y_values
        best_r2 = -np.inf
        for model_name, model_func in self.models.items():
            try:
                p0 = _MODEL_P0.get(model_name)
                params, _ = curve_fit(model_func, x_data, y_data, p0=p0, maxfev=10000)
                r2 = r2_score(y_data, model_func(x_data, *params))
                self.results[model_name] = (r2, params)
                if r2 > best_r2:
                    best_r2, self.best_model_name, self.best_model_params = r2, model_name, params
            except Exception:
                self.results[model_name] = (None, None)
        self.selected_model = self.best_model_name

    def create_graph(self):
        """Draw data points and the selected model's fitted curve."""
        if self.input_data is None:
            tk.Label(self.graph_frame, text="[Graph Display Area]",
                     font=("Segoe UI", 12), fg="#94a3b8", bg="white", justify="center").pack(expand=True)
            return

        states = self.chart_element_states
        self.figure = plt.Figure(figsize=(8, 5), dpi=100, facecolor='white')
        ax = self.figure.add_subplot(111)
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

        current_model = self.selected_model or self.best_model_name
        if current_model and current_model in self.results and states['best_fit']:
            r2, params = self.results[current_model]
            if r2 is not None:
                x_smooth = np.linspace(x.min(), x.max(), 200)
                ax.plot(x_smooth, self.models[current_model](x_smooth, *params), color='#10b981',
                        linewidth=2, label=f'{current_model} fit' if states['legend'] else '', zorder=2)

        if states.get('chart_title'):
            ax.set_title(self.chart_label_texts.get('chart_title') or "Automated Curve Fitting",
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

    def create_results_panels(self, parent):
        """Create Fit Statistics and Model Selection panels."""
        stats_frame = tk.LabelFrame(parent, text="  Fit Statistics  ", font=("Segoe UI", 10, "bold"),
                                    bg="white", fg="#059669", relief="solid", bd=2)
        stats_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.stats_content = tk.Frame(stats_frame, bg="white")
        self.stats_content.pack(fill="both", expand=True, padx=15, pady=10)
        self.update_statistics_display()

        model_frame = tk.LabelFrame(parent, text="  Model Selection  ", font=("Segoe UI", 10, "bold"),
                                    bg="white", fg="#2563eb", relief="solid", bd=2)
        model_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.model_content = tk.Frame(model_frame, bg="white")
        self.model_content.pack(fill="both", expand=True, padx=15, pady=10)
        self.update_model_selection_display()

    def update_statistics_display(self):
        """Refresh the Fit Statistics panel for the current model."""
        for widget in self.stats_content.winfo_children():
            widget.destroy()
        current_model = self.selected_model or self.best_model_name
        if not current_model or current_model not in self.results:
            return
        r2_value = self.results[current_model][0]
        rmse_value = self.calculate_rmse()
        self.create_stat_label(self.stats_content, "Model:", current_model)
        self.create_stat_label(self.stats_content, "R value:",
                               format_number(r2_value, 6) if r2_value is not None else "N/A")
        self.create_stat_label(self.stats_content, "RMSE:",
                               format_number(rmse_value) if rmse_value is not None else "N/A")
        tk.Label(self.stats_content, text="Equation:", font=("Segoe UI", 9), bg="white",
                 fg="#475569", anchor="w").pack(anchor="w", pady=(10, 2))
        tk.Label(self.stats_content, text=self.get_equation_text(), font=("Segoe UI", 9, "bold"),
                 bg="white", fg="#0f172a", wraplength=250, justify="left").pack(anchor="w")

    def create_stat_label(self, parent, label_text: str, value_text: str):
        row = tk.Frame(parent, bg="white")
        row.pack(fill="x", pady=2)
        tk.Label(row, text=label_text, font=("Segoe UI", 9), bg="white", fg="#475569", anchor="w").pack(side="left")
        tk.Label(row, text=value_text, font=("Segoe UI", 9, "bold"), bg="white", fg="#0f172a", anchor="e").pack(side="right")

    def calculate_rmse(self) -> Optional[float]:
        """Calculate RMSE for the currently selected model."""
        current_model = self.selected_model or self.best_model_name
        if current_model not in self.results or self.results[current_model][0] is None:
            return None
        params = self.results[current_model][1]
        y_pred = self.models[current_model](self.input_data.x_values, *params)
        return float(np.sqrt(np.mean((self.input_data.y_values - y_pred) ** 2)))

    def get_equation_text(self) -> str:
        """Return a formatted equation string for the current model and fitted parameters."""
        current_model = self.selected_model or self.best_model_name
        if current_model not in self.results or self.results[current_model][0] is None:
            return "N/A"
        params = self.results[current_model][1]
        template = _EQ_TEMPLATES.get(current_model)
        return template(params, lambda v: format_number(v, 3)) if template else "Complex equation"

    def update_model_selection_display(self):
        """Refresh the Model Selection panel with radio buttons and R² scores."""
        for widget in self.model_content.winfo_children():
            widget.destroy()
        self.model_var = tk.StringVar(value=self.best_model_name)
        for model_name in self.models:
            result = self.results.get(model_name)
            row = tk.Frame(self.model_content, bg="white")
            row.pack(fill="x", pady=2)
            if result and result[0] is not None:
                tk.Radiobutton(row, text=f"{model_name}:", variable=self.model_var, value=model_name,
                               font=("Segoe UI", 9), bg="white", activebackground="white",
                               command=self.on_model_selected).pack(side="left", anchor="w")
                if model_name == self.best_model_name:
                    tk.Label(row, text="Best", font=("Segoe UI", 10, "bold"), bg="white",
                             fg="#059669").pack(side="right", padx=(0, 5))
                tk.Label(row, text=f"R² = {format_number(result[0], 4)}", font=("Segoe UI", 9, "bold"),
                         bg="white", fg="#2563eb").pack(side="right", anchor="e")
            else:
                tk.Label(row, text=f"{model_name}: Error", font=("Segoe UI", 9),
                         bg="white", fg="#94a3b8").pack(side="left", anchor="w")

    def on_model_selected(self):
        self.selected_model = self.model_var.get()
        self.subtitle_label.config(text=f"Selected model: {self.selected_model}")
        self.update_statistics_display()
        self.refresh_graph()

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
                                                       show_worst_fit=False, initial_labels=initial_labels)
        for key, value in self.chart_element_states.items():
            if key in self.chart_elements_popup.element_states:
                self.chart_elements_popup.element_states[key].set(value)

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
        filepath = filedialog.asksaveasfilename(
            title="Export Graph", defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("PDF Document", "*.pdf"),
                       ("SVG Vector", "*.svg"), ("All Files", "*.*")]
        )
        if filepath:
            try:
                self.figure.savefig(filepath, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Export Successful", f"Graph exported to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Export Failed", f"Could not export graph:\n{e}")

    def save_results(self):
        """Display a summary of the current model's results."""
        current_model = self.selected_model or self.best_model_name
        if current_model and current_model in self.results:
            r2 = self.results[current_model][0]
            if r2 is not None:
                rmse = self.calculate_rmse()
                messagebox.showinfo("Results Saved",
                                    f"Results saved for {current_model} model\n\n"
                                    f"R² value: {r2:.6f}\n"
                                    f"RMSE: {rmse:.4f}\n\n"
                                    "Note: Linear models can be analysed further through "
                                    "the Linear Analysis workflow for gradient analysis.")
            else:
                messagebox.showwarning("Model Error", f"The {current_model} model failed to fit the data.")
        else:
            messagebox.showwarning("No Model Selected", "Please select a model to save results.")

    def _create_error_layout(self):
        self.configure(padx=20, pady=20)
        header = tk.Frame(self, bg="white", height=60)
        header.pack(fill="x", pady=(0, 15))
        header.pack_propagate(False)
        tk.Button(header, text="Back", font=("Segoe UI", 10), bg="#e5e7eb", fg="#0f172a",
                  relief="flat", cursor="hand2", command=self.manager.back).pack(side="left", padx=15, pady=10)
        error_container = tk.Frame(self, bg="white")
        error_container.pack(fill="both", expand=True)
        tk.Label(error_container, text="Error", font=("Segoe UI", 48), bg="white", fg="#dc2626").pack(pady=(100, 20))
        tk.Label(error_container, text="Cannot Display Graph", font=("Segoe UI", 20, "bold"),
                 bg="white", fg="#0f172a").pack(pady=(0, 10))
        tk.Label(error_container,
                 text="There was an error loading or analysing the data.\nPlease go back and check your data.",
                 font=("Segoe UI", 12), bg="white", fg="#64748b", justify="center").pack(pady=(0, 20))

