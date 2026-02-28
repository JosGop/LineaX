"""GradientAnalysis.py — Screen 4 (Gradient Analysis & Results) from Section 3.2.2."""

import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Optional, Dict
import json
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from NumberFormatting import format_number, format_number_with_uncertainty
from ManagingScreens import make_scrollable

# Unit-to-SI conversion factors (multiply measurement by factor to obtain SI value).
_UNIT_CONVERSIONS: Dict[str, float] = {
    'nm': 1e-9, 'nanometer': 1e-9, 'nanometers': 1e-9,
    'um': 1e-6, 'micrometer': 1e-6, 'micrometers': 1e-6,
    'mm': 1e-3, 'millimeter': 1e-3, 'millimeters': 1e-3,
    'cm': 1e-2, 'centimeter': 1e-2, 'centimeters': 1e-2,
    'km': 1e3,  'kilometer': 1e3,  'kilometers': 1e3,
    'm': 1.0,   'meter': 1.0,      'meters': 1.0,
    'ms': 1e-3, 'millisecond': 1e-3, 'milliseconds': 1e-3,
    'us': 1e-6, 'microsecond': 1e-6, 'microseconds': 1e-6,
    'ns': 1e-9, 'nanosecond': 1e-9, 'nanoseconds': 1e-9,
    'min': 60,  'minute': 60,   'minutes': 60,
    'h': 3600,  'hour': 3600,   'hours': 3600,
    's': 1.0,   'second': 1.0,  'seconds': 1.0,
    'mV': 1e-3, 'millivolt': 1e-3, 'millivolts': 1e-3,
    'kV': 1e3,  'kilovolt': 1e3,   'kilovolts': 1e3,
    'V': 1.0,   'volt': 1.0,       'volts': 1.0,
}

_FROM_SUPERSCRIPT = str.maketrans('0123456789+-', '0123456789+-')


class GradientAnalysisScreen(tk.Frame):
    """Screen 4: gradient analysis, optional unknown solving and PDF export."""

    def __init__(self, parent, manager):
        super().__init__(parent, bg="#f5f6f8")
        self.manager = manager
        self.parent = parent
        self.gradient = self.gradient_uncertainty = self.gradient_variable = None
        self.gradient_units = ""
        self.intercept = self.intercept_uncertainty = self.intercept_variable = None
        self.intercept_units = ""
        self.equation_name = "Linear Equation"
        self._load_analysis_data()
        self.create_layout()

    def _load_analysis_data(self):
        """Load gradient and intercept data from ScreenManager."""
        if not hasattr(self.manager, 'get_analysis_results'):
            messagebox.showwarning("No Analysis Data",
                                   "Could not load analysis results. Please go back and perform linear regression first.")
            return
        data = self.manager.get_analysis_results()
        if not data:
            messagebox.showwarning("No Analysis Data",
                                   "Could not load analysis results. Please go back and perform linear regression first.")
            return
        self.equation_name = data.get('equation_name', 'Linear Equation')
        self.gradient = data.get('gradient', 0)
        self.gradient_uncertainty = data.get('gradient_uncertainty', 0)
        self.gradient_variable = data.get('gradient_variable', 'm')
        self.gradient_units = data.get('gradient_units', '')
        self.intercept = data.get('intercept', 0)
        self.intercept_uncertainty = data.get('intercept_uncertainty', 0)
        self.intercept_variable = data.get('intercept_variable', 'c')
        self.intercept_units = data.get('intercept_units', '')
        self.find_variable = data.get('find_variable')
        self.constants = data.get('constants', {})
        self.measurement_units = data.get('measurement_units', {})
        self.gradient_meaning = data.get('gradient_meaning', self.gradient_variable)
        self.intercept_meaning = data.get('intercept_meaning', self.intercept_variable)

        eq_info = self.manager.get_equation_info() if hasattr(self.manager, 'get_equation_info') else {}
        self.equation_expression = (eq_info or {}).get('equation_expression', '')

        if self.find_variable and self.gradient_meaning:
            self._solve_for_unknown()

        self.raw_data = self.manager.get_raw_data() if hasattr(self.manager, 'get_raw_data') else None
        self.transformed_data = self.manager.get_data()
        self.graph_figure = self.manager.get_graph_figure() if hasattr(self.manager, 'get_graph_figure') else None

    def _get_unit_conversion_factor(self, from_unit: str) -> float:
        return _UNIT_CONVERSIONS.get(from_unit.lower().strip(), 1.0)

    def _solve_for_unknown(self):
        """Solve the gradient expression for the unknown variable with unit conversion."""
        import sympy as sp
        from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
        try:
            grad_expr_str = re.sub(r'\s*\(contains.*?\)', '', str(self.gradient_meaning)).strip().replace('^', '**')
            all_vars = set(re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', grad_expr_str))
            local_dict = {var: sp.Symbol(var) for var in all_vars}
            transforms = standard_transformations + (implicit_multiplication_application,)
            grad_expr = parse_expr(grad_expr_str, transformations=transforms, local_dict=local_dict)

            unit_conversion_factor = 1.0
            for unit in self.measurement_units.values():
                unit_conversion_factor *= self._get_unit_conversion_factor(unit)
            converted_gradient = self.gradient * unit_conversion_factor
            converted_gradient_unc = self.gradient_uncertainty * unit_conversion_factor

            for const_name, const_value in self.constants.items():
                if const_name in local_dict:
                    grad_expr = grad_expr.subs(local_dict[const_name], const_value)

            unknown_symbol = sp.Symbol(self.find_variable)
            if unknown_symbol not in grad_expr.free_symbols:
                return
            solution = sp.solve(grad_expr - converted_gradient, unknown_symbol)
            if not solution:
                return
            solved_value = float(solution[0])

            try:
                grad_sym = sp.Symbol('gradient')
                solution_expr = sp.solve(grad_expr - grad_sym, unknown_symbol)[0]
                derivative = sp.diff(solution_expr, grad_sym)
                uncertainty_factor = abs(float(derivative.subs(grad_sym, converted_gradient)))
                solved_uncertainty = uncertainty_factor * converted_gradient_unc
            except Exception:
                solved_uncertainty = abs(solved_value * abs(converted_gradient_unc / converted_gradient)) if converted_gradient else 0

            self.gradient_variable = self.find_variable
            self.gradient = solved_value
            self.gradient_uncertainty = solved_uncertainty
        except Exception as e:
            print(f"Could not solve for {self.find_variable}: {e}")

    def create_layout(self):
        self.configure(padx=30, pady=20)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = tk.Frame(self, bg="white", height=50)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header.pack_propagate(False)
        tk.Button(header, text="Back", font=("Segoe UI", 10), bg="#e5e7eb", fg="#0f172a",
                  relief="flat", cursor="hand2", command=self.manager.back).pack(side="left", padx=15, pady=10)
        tk.Label(header, text="LineaX", font=("Segoe UI", 12, "bold"),
                 bg="white", fg="#0f172a").pack(side="left", padx=(10, 0), pady=10)

        tk.Label(self, text="Gradient Analysis & Results", font=("Segoe UI", 22, "bold"),
                 bg="#f5f6f8", fg="#0f172a").grid(row=1, column=0, pady=(10, 30))

        _, content, _, _ = make_scrollable(self, row=2, column=0, bg="white", panel_kwargs={"padx": 25, "pady": 25})
        self.create_equation_section(content)
        self.create_gradient_section(content)
        self.create_intercept_section(content)
        self.create_comparison_section(content)
        self.create_action_buttons(content)

    def create_equation_section(self, parent):
        """Display the selected equation name, expression and gradient description (Section 1)."""
        section = tk.LabelFrame(parent, text="Selected Equation", font=("Segoe UI", 10, "bold"),
                                bg="white", fg="#0f172a")
        section.pack(fill="x", pady=(0, 15))
        inner = tk.Frame(section, bg="#e3f2fd")
        inner.pack(fill="x", padx=15, pady=15)
        tk.Label(inner, text=self.equation_name, font=("Segoe UI", 13, "bold"),
                 bg="#e3f2fd", fg="#0f172a").pack(anchor="w")
        if self.equation_expression:
            tk.Label(inner, text=self.equation_expression, font=("Courier", 11),
                     bg="#e3f2fd", fg="#334155").pack(anchor="w", pady=(4, 2))
        gradient_desc = f"Where gradient = {self.gradient_variable}" if self.gradient_variable else "Linear regression gradient"
        tk.Label(inner, text=gradient_desc, font=("Segoe UI", 9), bg="#e3f2fd", fg="#64748b").pack(anchor="w", pady=(3, 0))

    def create_gradient_section(self, parent):
        """Display calculated gradient with uncertainty and worst-fit range (Section 2)."""
        section = tk.LabelFrame(parent, text="Calculated Unknown Value", font=("Segoe UI", 10, "bold"),
                                bg="white", fg="#0f172a")
        section.pack(fill="x", pady=(0, 15))
        inner = tk.Frame(section, bg="white")
        inner.pack(fill="x", padx=15, pady=15)
        tk.Label(inner, text="From Best Fit:", font=("Segoe UI", 9), bg="white", fg="#64748b").pack(anchor="w")

        abs_gradient = abs(self.gradient) if self.gradient is not None else 0
        gradient_unc = self.gradient_uncertainty if self.gradient_uncertainty is not None else 0
        var_name = self.gradient_variable or "Gradient"
        units_str = f" {self.gradient_units}" if self.gradient_units else ""

        result_frame = tk.Frame(inner, bg="#d1fae5", relief="solid", bd=1)
        result_frame.pack(fill="x", pady=(5, 10))
        result_inner = tk.Frame(result_frame, bg="#d1fae5")
        result_inner.pack(fill="x", padx=15, pady=12)
        tk.Label(result_inner,
                 text=f"{var_name} = {format_number_with_uncertainty(abs_gradient, gradient_unc)}{units_str}",
                 font=("Segoe UI", 12, "bold"), bg="#d1fae5", fg="#059669").pack(anchor="w")

        range_frame = tk.Frame(inner, bg="white")
        range_frame.pack(fill="x", pady=(5, 0))
        for side, label_text, val in [
            ("left",  "Maximum (worst fit):", abs_gradient + gradient_unc),
            ("right", "Minimum (worst fit):", abs_gradient - gradient_unc),
        ]:
            c = tk.Frame(range_frame, bg="white")
            c.pack(side=side, fill="x", expand=True, padx=(0, 10) if side == "left" else 0)
            tk.Label(c, text=label_text, font=("Segoe UI", 8), bg="white", fg="#64748b").pack(anchor="w")
            suffix = "max" if side == "left" else "min"
            tk.Label(c, text=f"{var_name}_{suffix} = {format_number(val)}{units_str}",
                     font=("Segoe UI", 9), bg="white", fg="#0f172a").pack(anchor="w")

    def create_intercept_section(self, parent):
        """Display the y-intercept value if available."""
        if self.intercept is None:
            return
        section = tk.Frame(parent, bg="white")
        section.pack(fill="x", pady=(0, 15))
        header = tk.Frame(section, bg="#f8f9fa", cursor="hand2")
        header.pack(fill="x")
        intercept_var = self.intercept_variable or "Y-intercept"
        tk.Label(header, text=f"Additional: {intercept_var}", font=("Segoe UI", 9, "italic"),
                 bg="#f8f9fa", fg="#64748b").pack(side="left", padx=10, pady=8)
        intercept_unc = self.intercept_uncertainty or 0
        units_str = f" {self.intercept_units}" if self.intercept_units else ""
        tk.Label(header,
                 text=f"{format_number_with_uncertainty(self.intercept, intercept_unc)}{units_str}",
                 font=("Segoe UI", 9), bg="#f8f9fa", fg="#0f172a").pack(side="right", padx=10, pady=8)

    def create_comparison_section(self, parent):
        """Optional percentage difference comparison against a known value (Section 3)."""
        section = tk.LabelFrame(parent, text="Compare with Known Value (Optional)",
                                font=("Segoe UI", 10, "bold"), bg="white", fg="#9333ea")
        section.pack(fill="x", pady=(0, 20))
        inner = tk.Frame(section, bg="white")
        inner.pack(fill="x", padx=15, pady=15)

        input_frame = tk.Frame(inner, bg="white")
        input_frame.pack(fill="x", pady=(0, 10))
        tk.Label(input_frame, text="Known/Accepted Value:", font=("Segoe UI", 9),
                 bg="white", fg="#64748b").pack(anchor="w", pady=(0, 5))
        self.known_value_entry = tk.Entry(input_frame, font=("Segoe UI", 11), relief="solid", bd=1, width=30)
        self.known_value_entry.pack(fill="x")
        self.known_value_entry.insert(0, "e.g. 5.01*10^-2")
        self.known_value_entry.config(fg="#94a3b8")
        self.known_value_entry.bind("<FocusIn>", self._clear_placeholder)
        self.known_value_entry.bind("<FocusOut>", self._restore_placeholder)
        self.known_value_entry.bind("<Return>", lambda e: self.calculate_comparison())

        result_frame = tk.Frame(inner, bg="#fef3c7", relief="solid", bd=1)
        result_frame.pack(fill="x", pady=(10, 0))
        result_inner = tk.Frame(result_frame, bg="#fef3c7")
        result_inner.pack(fill="x", padx=15, pady=12)
        tk.Label(result_inner, text="Percentage Difference:", font=("Segoe UI", 9),
                 bg="#fef3c7", fg="#78350f").pack(anchor="w")
        self.percentage_diff_label = tk.Label(result_inner, text="[value]%", font=("Segoe UI", 14, "bold"),
                                              bg="#fef3c7", fg="#92400e")
        self.percentage_diff_label.pack(anchor="w", pady=(3, 0))
        tk.Label(result_inner, text="If difference is small, your result is within the accepted scientific standard!",
                 font=("Segoe UI", 8, "italic"), bg="#fef3c7", fg="#78350f",
                 wraplength=400, justify="left").pack(anchor="w", pady=(5, 0))

    def create_action_buttons(self, parent):
        button_frame = tk.Frame(parent, bg="white")
        button_frame.pack(fill="x", pady=(10, 0))
        tk.Button(button_frame, text="Export Full Report", font=("Segoe UI", 11), bg="white", fg="#0f172a",
                  relief="solid", bd=1, cursor="hand2", padx=30, pady=12,
                  command=self.export_report).pack(side="left", padx=(0, 10))
        tk.Button(button_frame, text="Save Project", font=("Segoe UI", 11, "bold"), bg="#0f172a", fg="white",
                  relief="flat", cursor="hand2", padx=30, pady=12,
                  command=self.save_project).pack(side="right")

    def _clear_placeholder(self, event):
        if self.known_value_entry.get().startswith("e.g."):
            self.known_value_entry.delete(0, tk.END)
            self.known_value_entry.config(fg="#0f172a")

    def _restore_placeholder(self, event):
        if not self.known_value_entry.get().strip():
            self.known_value_entry.insert(0, "e.g. 5.01*10^-2")
            self.known_value_entry.config(fg="#94a3b8")

    def calculate_comparison(self):
        """Calculate and display the percentage difference against a known value."""
        known_str = self.known_value_entry.get().strip()
        if not known_str or known_str.startswith("e.g."):
            messagebox.showwarning("No Known Value", "Please enter a known/accepted value to compare.")
            return
        try:
            known_value = self._parse_scientific_notation(known_str)
            measured = abs(self.gradient) if self.gradient is not None else 0
            percentage_diff = abs((measured - known_value) / known_value * 100)
            self.percentage_diff_label.config(text=f"{percentage_diff:.2f}%")
            if percentage_diff < 5:
                interpretation = "Excellent! Your result is very close to the accepted value."
            elif percentage_diff < 10:
                interpretation = "Good! Your result is reasonably close to the accepted value."
            else:
                interpretation = "Your result differs significantly. Check your experimental method."
            messagebox.showinfo("Comparison Result", f"Percentage Difference: {percentage_diff:.2f}%\n\n{interpretation}")
        except ValueError:
            messagebox.showerror("Invalid Input",
                                 "Please enter a valid numerical value.\n\n"
                                 "Examples:\n-0.05\n+5.01e-2\n+5.01*10^-3\n5.01*10^-2\n510.79")

    def _parse_scientific_notation(self, text: str) -> float:
        """Parse various scientific notation formats into a float."""
        text = text.strip().replace(' ', '').lstrip('+')
        text = text.replace('*', '*').replace('-', '-').translate(_FROM_SUPERSCRIPT)
        text = re.sub(r'\*\s*10\s*\^\s*\(?\s*(-?\d+)\s*\)?', r'e\1', text)
        text = re.sub(r'\*\s*10\s*(-?\d+)', r'e\1', text)
        try:
            return float(text)
        except ValueError:
            if all(c in '0123456789.+-*/()eE' for c in text):
                return float(eval(text))
            raise ValueError(f"Cannot parse '{text}' as a number")

    def export_report(self):
        """Export a multi-page PDF report: graph, results table and data tables."""
        filepath = filedialog.asksaveasfilename(
            title="Export Analysis Report", defaultextension=".pdf",
            filetypes=[("PDF Document", "*.pdf"), ("All Files", "*.*")]
        )
        if not filepath:
            return
        try:
            with PdfPages(filepath) as pdf:
                # Page 1: graph
                if self.graph_figure is not None:
                    pdf.savefig(self.graph_figure, bbox_inches='tight')
                else:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    ax.text(0.5, 0.5, "Graph not available", ha='center', va='center', fontsize=14)
                    ax.axis('off')
                    pdf.savefig(fig, bbox_inches='tight')
                    plt.close(fig)

                # Page 2: results table
                abs_grad = abs(self.gradient) if self.gradient is not None else 0
                grad_unc = self.gradient_uncertainty or 0
                intercept_unc = self.intercept_uncertainty or 0
                var = self.gradient_variable or "Gradient"
                ivar = self.intercept_variable or "Intercept"
                units = f" {self.gradient_units}" if self.gradient_units else ""
                iunits = f" {self.intercept_units}" if self.intercept_units else ""
                lines = [
                    ("Gradient Analysis & Results", "", True), ("", "", False),
                    ("Equation:", self.equation_name, False), ("", "", False),
                    ("From Best Fit:", "", False),
                    (f"  {var} =", f"{format_number_with_uncertainty(abs_grad, grad_unc)}{units}", False),
                    (f"  {var}_max =", f"{format_number(abs_grad + grad_unc)}{units}", False),
                    (f"  {var}_min =", f"{format_number(abs(abs_grad - grad_unc))}{units}", False),
                    ("", "", False),
                    (f"Intercept ({ivar}) =", f"{format_number_with_uncertainty(self.intercept, intercept_unc)}{iunits}", False),
                ]
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.axis('off')
                y = 0.95
                for label, value, bold in lines:
                    ax.text(0.05, y, label, transform=ax.transAxes,
                            fontsize=14 if bold else 11, fontweight='bold' if bold else 'normal', va='top')
                    if value:
                        ax.text(0.45, y, value, transform=ax.transAxes, fontsize=11, va='top')
                    y -= 0.08
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)

                # Page 3: data tables
                datasets = []
                if self.raw_data is not None and len(getattr(self.raw_data, 'x_values', [])) > 0:
                    datasets.append(("Raw Data", self.raw_data))
                if (self.transformed_data is not None and self.transformed_data is not self.raw_data
                        and len(getattr(self.transformed_data, 'x_values', [])) > 0):
                    datasets.append(("Transformed Data", self.transformed_data))

                for title, data in datasets:
                    x_title = getattr(data, 'x_title', 'X') or 'X'
                    y_title = getattr(data, 'y_title', 'Y') or 'Y'
                    x_vals, y_vals = data.x_values, data.y_values
                    n = len(x_vals)
                    x_err = data.x_error if getattr(data, 'x_error', None) is not None else [None] * n
                    y_err = data.y_error if getattr(data, 'y_error', None) is not None else [None] * n
                    col_labels = [x_title, f"+/-{x_title}", y_title, f"+/-{y_title}"]
                    table_data = [
                        [format_number(x_vals[i]),
                         format_number(x_err[i]) if x_err[i] is not None else "-",
                         format_number(y_vals[i]),
                         format_number(y_err[i]) if y_err[i] is not None else "-"]
                        for i in range(n)
                    ]
                    fig, ax = plt.subplots(figsize=(10, max(4, n * 0.35 + 2)))
                    ax.axis('off')
                    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
                    tbl = ax.table(cellText=table_data, colLabels=col_labels, loc='center', cellLoc='center')
                    tbl.auto_set_font_size(False)
                    tbl.set_fontsize(9)
                    tbl.auto_set_column_width(col=list(range(len(col_labels))))
                    for (row, col), cell in tbl.get_celld().items():
                        if row == 0:
                            cell.set_facecolor('#0f172a')
                            cell.set_text_props(color='white', fontweight='bold')
                        elif row % 2 == 0:
                            cell.set_facecolor('#f1f5f9')
                    pdf.savefig(fig, bbox_inches='tight')
                    plt.close(fig)

            messagebox.showinfo("Export Successful", f"Report exported to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not export report:\n{e}")

    def save_project(self):
        """Save analysis results to a .lineax JSON file."""
        filepath = filedialog.asksaveasfilename(
            title="Save LineaX Project", defaultextension=".lineax",
            filetypes=[("LineaX Project", "*.lineax"), ("JSON File", "*.json"), ("All Files", "*.*")]
        )
        if not filepath:
            return
        try:
            project_data = {
                "equation": self.equation_name,
                "gradient": {
                    "value": float(self.gradient) if self.gradient is not None else 0,
                    "uncertainty": float(self.gradient_uncertainty) if self.gradient_uncertainty is not None else 0,
                    "units": self.gradient_units,
                    "variable": self.gradient_variable,
                },
                "intercept": {
                    "value": float(self.intercept) if self.intercept is not None else 0,
                    "uncertainty": float(self.intercept_uncertainty) if self.intercept_uncertainty is not None else 0,
                    "units": self.intercept_units,
                    "variable": self.intercept_variable,
                },
            }
            with open(filepath, 'w') as f:
                json.dump(project_data, f, indent=2)
            messagebox.showinfo("Project Saved",
                                f"Project saved successfully to:\n{filepath}\n\n"
                                "You can reopen this project later to continue your analysis.")
        except Exception as e:
            messagebox.showerror("Save Failed", f"Could not save project:\n{e}")

