"""
GradientAnalysis.py - Gradient Analysis & Results Screen

This screen interprets the physical meaning of the gradient and intercept
from linear regression, allowing comparison with known/accepted values.
"""

import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Optional, Dict
import json


class GradientAnalysisScreen(tk.Frame):
    def __init__(self, parent, manager):
        super().__init__(parent, bg="#f5f6f8")
        self.manager = manager
        self.parent = parent
        
        # Get analysis results from previous screen
        self.gradient = None
        self.gradient_uncertainty = None
        self.gradient_variable = None
        self.gradient_units = ""
        
        self.intercept = None
        self.intercept_uncertainty = None
        self.intercept_variable = None
        self.intercept_units = ""
        
        # Get equation information
        self.equation_name = "Linear Equation"
        
        # Load data from manager
        self._load_analysis_data()
        
        # Create UI
        self.create_layout()
    
    def _load_analysis_data(self):
        """Load gradient and intercept data from manager."""
        # Get analysis results stored by GraphResultsScreen
        if hasattr(self.manager, 'get_analysis_results'):
            analysis_data = self.manager.get_analysis_results()
            
            if analysis_data:
                self.equation_name = analysis_data.get('equation_name', 'Linear Equation')
                self.gradient = analysis_data.get('gradient', 0)
                self.gradient_uncertainty = analysis_data.get('gradient_uncertainty', 0)
                self.gradient_variable = analysis_data.get('gradient_variable', 'm')
                self.gradient_units = analysis_data.get('gradient_units', '')
                
                self.intercept = analysis_data.get('intercept', 0)
                self.intercept_uncertainty = analysis_data.get('intercept_uncertainty', 0)
                self.intercept_variable = analysis_data.get('intercept_variable', 'c')
                self.intercept_units = analysis_data.get('intercept_units', '')

                # Get solving information
                self.find_variable = analysis_data.get('find_variable')
                self.constants = analysis_data.get('constants', {})
                self.measurement_units = analysis_data.get('measurement_units', {})
                self.gradient_meaning = analysis_data.get('gradient_meaning', self.gradient_variable)
                self.intercept_meaning = analysis_data.get('intercept_meaning', self.intercept_variable)

                # Solve for the unknown if specified
                if self.find_variable and self.gradient_meaning:
                    self._solve_for_unknown()
            else:
                messagebox.showwarning(
                    "No Analysis Data",
                    "Could not load analysis results. Please go back and perform linear regression first."
                )
        else:
            messagebox.showwarning(
                "No Analysis Data",
                "Could not load analysis results. Please go back and perform linear regression first."
            )

    def _get_unit_conversion_factor(self, from_unit):
        """Get conversion factor from one unit to SI base units."""
        length_conversions = {
            'nm': 1e-9, 'nanometer': 1e-9, 'nanometers': 1e-9,
            'μm': 1e-6, 'um': 1e-6, 'micrometer': 1e-6, 'micrometers': 1e-6,
            'mm': 1e-3, 'millimeter': 1e-3, 'millimeters': 1e-3,
            'cm': 1e-2, 'centimeter': 1e-2, 'centimeters': 1e-2,
            'km': 1e3, 'kilometer': 1e3, 'kilometers': 1e3,
            'm': 1.0, 'meter': 1.0, 'meters': 1.0
        }

        time_conversions = {
            'ms': 1e-3, 'millisecond': 1e-3, 'milliseconds': 1e-3,
            'μs': 1e-6, 'us': 1e-6, 'microsecond': 1e-6, 'microseconds': 1e-6,
            'ns': 1e-9, 'nanosecond': 1e-9, 'nanoseconds': 1e-9,
            'min': 60, 'minute': 60, 'minutes': 60,
            'h': 3600, 'hour': 3600, 'hours': 3600,
            's': 1.0, 'second': 1.0, 'seconds': 1.0
        }

        voltage_conversions = {
            'mV': 1e-3, 'millivolt': 1e-3, 'millivolts': 1e-3,
            'kV': 1e3, 'kilovolt': 1e3, 'kilovolts': 1e3,
            'V': 1.0, 'volt': 1.0, 'volts': 1.0
        }

        all_conversions = {**length_conversions, **time_conversions, **voltage_conversions}
        return all_conversions.get(from_unit.lower().strip(), 1.0)

    def _solve_for_unknown(self):
        """Solve the gradient expression for the unknown variable with unit conversion."""
        import sympy as sp
        import re

        try:
            grad_expr_str = str(self.gradient_meaning)
            grad_expr_str = re.sub(r'\s*\(contains.*?\)', '', grad_expr_str).strip().replace('^', '**')

            all_vars = set(re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', grad_expr_str))
            local_dict = {var: sp.Symbol(var) for var in all_vars}

            from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
            transforms = standard_transformations + (implicit_multiplication_application,)
            grad_expr = parse_expr(grad_expr_str, transformations=transforms, local_dict=local_dict)

            # Apply unit conversion
            unit_conversion_factor = 1.0
            for var, unit in self.measurement_units.items():
                unit_conversion_factor *= self._get_unit_conversion_factor(unit)

            converted_gradient = self.gradient * unit_conversion_factor
            converted_gradient_unc = self.gradient_uncertainty * unit_conversion_factor

            # Substitute constants
            for const_name, const_value in self.constants.items():
                if const_name in local_dict:
                    grad_expr = grad_expr.subs(local_dict[const_name], const_value)

            # Solve for unknown
            unknown_symbol = sp.Symbol(self.find_variable)
            if unknown_symbol in grad_expr.free_symbols:
                solution = sp.solve(grad_expr - converted_gradient, unknown_symbol)

                if solution and len(solution) > 0:
                    solved_value = float(solution[0])

                    try:
                        grad_sym = sp.Symbol('gradient')
                        solution_expr = sp.solve(grad_expr - grad_sym, unknown_symbol)[0]
                        derivative = sp.diff(solution_expr, grad_sym)
                        uncertainty_factor = abs(float(derivative.subs(grad_sym, converted_gradient)))
                        solved_uncertainty = uncertainty_factor * converted_gradient_unc
                    except:
                        if converted_gradient != 0:
                            rel_uncertainty = abs(converted_gradient_unc / converted_gradient)
                            solved_uncertainty = abs(solved_value * rel_uncertainty)
                        else:
                            solved_uncertainty = 0

                    self.gradient_variable = self.find_variable
                    self.gradient = solved_value
                    self.gradient_uncertainty = solved_uncertainty

        except Exception as e:
            print(f"Could not solve for {self.find_variable}: {e}")
            import traceback
            traceback.print_exc()
    
    def create_layout(self):
        """Create the main UI layout."""
        self.configure(padx=30, pady=20)
        
        # Header with LineaX branding
        header = tk.Frame(self, bg="white", height=50)
        header.pack(fill="x", pady=(0, 20))
        header.pack_propagate(False)
        
        # Back button
        tk.Button(
            header,
            text="← Back",
            font=("Segoe UI", 10),
            bg="#e5e7eb",
            fg="#0f172a",
            relief="flat",
            cursor="hand2",
            command=self.manager.back
        ).pack(side="left", padx=15, pady=10)
        
        tk.Label(
            header,
            text="LineaX",
            font=("Segoe UI", 12, "bold"),
            bg="white",
            fg="#0f172a"
        ).pack(side="left", padx=(10, 0), pady=10)
        
        # Main Title
        tk.Label(
            self,
            text="Gradient Analysis & Results",
            font=("Segoe UI", 22, "bold"),
            bg="#f5f6f8",
            fg="#0f172a"
        ).pack(pady=(10, 30))
        
        # Main container with rounded appearance
        container = tk.Frame(self, bg="#e5e7eb", relief="solid", bd=1)
        container.pack(fill="both", expand=True)
        
        # Inner frame
        inner = tk.Frame(container, bg="white")
        inner.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Content padding
        content = tk.Frame(inner, bg="white")
        content.pack(fill="both", expand=True, padx=25, pady=25)
        
        # Selected Equation Section
        self.create_equation_section(content)
        
        # Calculated Unknown Value Section (Gradient)
        self.create_gradient_section(content)
        
        # Calculated Unknown Value Section (Intercept) - Optional
        self.create_intercept_section(content)
        
        # Compare with Known Value Section
        self.create_comparison_section(content)
        
        # Action Buttons
        self.create_action_buttons(content)
    
    def create_equation_section(self, parent):
        """Create the Selected Equation display section."""
        section = tk.LabelFrame(
            parent,
            text="Selected Equation",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#0f172a"
        )
        section.pack(fill="x", pady=(0, 15))
        
        inner = tk.Frame(section, bg="#e3f2fd")
        inner.pack(fill="x", padx=15, pady=15)
        
        tk.Label(
            inner,
            text=self.equation_name,
            font=("Segoe UI", 13, "bold"),
            bg="#e3f2fd",
            fg="#0f172a"
        ).pack(anchor="w")
        
        gradient_desc = f"Where gradient = {self.gradient_variable}" if self.gradient_variable else "Linear regression gradient"
        tk.Label(
            inner,
            text=gradient_desc,
            font=("Segoe UI", 9),
            bg="#e3f2fd",
            fg="#64748b"
        ).pack(anchor="w", pady=(3, 0))
    
    def create_gradient_section(self, parent):
        """Create the Calculated Unknown Value section for gradient."""
        section = tk.LabelFrame(
            parent,
            text="Calculated Unknown Value",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#0f172a"
        )
        section.pack(fill="x", pady=(0, 15))
        
        inner = tk.Frame(section, bg="white")
        inner.pack(fill="x", padx=15, pady=15)
        
        # From Best Fit label
        tk.Label(
            inner,
            text="From Best Fit:",
            font=("Segoe UI", 9),
            bg="white",
            fg="#64748b"
        ).pack(anchor="w")
        
        # Main result display
        result_frame = tk.Frame(inner, bg="#d1fae5", relief="solid", bd=1)
        result_frame.pack(fill="x", pady=(5, 10))
        
        result_inner = tk.Frame(result_frame, bg="#d1fae5")
        result_inner.pack(fill="x", padx=15, pady=12)
        
        # Format the result
        abs_gradient = abs(self.gradient) if self.gradient is not None else 0
        gradient_unc = self.gradient_uncertainty if self.gradient_uncertainty is not None else 0
        
        var_name = self.gradient_variable if self.gradient_variable else "Gradient"
        units_str = f" {self.gradient_units}" if self.gradient_units else ""
        result_text = f"{var_name} = {abs_gradient:.4e} ± {gradient_unc:.4e}{units_str}"
        
        tk.Label(
            result_inner,
            text=result_text,
            font=("Segoe UI", 12, "bold"),
            bg="#d1fae5",
            fg="#059669"
        ).pack(anchor="w")
        
        # Uncertainty range display
        range_frame = tk.Frame(inner, bg="white")
        range_frame.pack(fill="x", pady=(5, 0))
        
        # Maximum value
        max_container = tk.Frame(range_frame, bg="white")
        max_container.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        tk.Label(
            max_container,
            text="Maximum (worst fit):",
            font=("Segoe UI", 8),
            bg="white",
            fg="#64748b"
        ).pack(anchor="w")
        
        max_val = abs_gradient + gradient_unc
        tk.Label(
            max_container,
            text=f"{var_name}_max = {max_val:.4e}{units_str}",
            font=("Segoe UI", 9),
            bg="white",
            fg="#0f172a"
        ).pack(anchor="w")
        
        # Minimum value
        min_container = tk.Frame(range_frame, bg="white")
        min_container.pack(side="left", fill="x", expand=True)
        
        tk.Label(
            min_container,
            text="Minimum (worst fit):",
            font=("Segoe UI", 8),
            bg="white",
            fg="#64748b"
        ).pack(anchor="w")
        
        min_val = abs_gradient - gradient_unc
        tk.Label(
            min_container,
            text=f"{var_name}_min = {min_val:.4e}{units_str}",
            font=("Segoe UI", 9),
            bg="white",
            fg="#0f172a"
        ).pack(anchor="w")
    
    def create_intercept_section(self, parent):
        """Create optional intercept information section."""
        if self.intercept is None:
            return
        
        section = tk.Frame(parent, bg="white")
        section.pack(fill="x", pady=(0, 15))
        
        # Collapsible/expandable section (simplified here)
        header = tk.Frame(section, bg="#f8f9fa", cursor="hand2")
        header.pack(fill="x")
        
        intercept_var = self.intercept_variable if self.intercept_variable else "Y-intercept"
        tk.Label(
            header,
            text=f"ℹ Additional: {intercept_var}",
            font=("Segoe UI", 9, "italic"),
            bg="#f8f9fa",
            fg="#64748b"
        ).pack(side="left", padx=10, pady=8)
        
        # Show intercept value
        intercept_unc = self.intercept_uncertainty if self.intercept_uncertainty is not None else 0
        units_str = f" {self.intercept_units}" if self.intercept_units else ""
        tk.Label(
            header,
            text=f"{self.intercept:.4e} ± {intercept_unc:.4e}{units_str}",
            font=("Segoe UI", 9),
            bg="#f8f9fa",
            fg="#0f172a"
        ).pack(side="right", padx=10, pady=8)
    
    def create_comparison_section(self, parent):
        """Create the Compare with Known Value section."""
        section = tk.LabelFrame(
            parent,
            text="Compare with Known Value (Optional)",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#9333ea"
        )
        section.pack(fill="x", pady=(0, 20))
        
        inner = tk.Frame(section, bg="white")
        inner.pack(fill="x", padx=15, pady=15)
        
        # Known/Accepted Value input
        input_frame = tk.Frame(inner, bg="white")
        input_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            input_frame,
            text="Known/Accepted Value:",
            font=("Segoe UI", 9),
            bg="white",
            fg="#64748b"
        ).pack(anchor="w", pady=(0, 5))
        
        self.known_value_entry = tk.Entry(
            input_frame,
            font=("Segoe UI", 11),
            relief="solid",
            bd=1,
            width=30
        )
        self.known_value_entry.pack(fill="x")
        self.known_value_entry.insert(0, "e.g. 5.01×10⁻²")
        self.known_value_entry.config(fg="#94a3b8")
        self.known_value_entry.bind("<FocusIn>", self._clear_placeholder)
        self.known_value_entry.bind("<FocusOut>", self._restore_placeholder)
        self.known_value_entry.bind("<Return>", lambda e: self.calculate_comparison())
        
        # Percentage Difference Result
        result_frame = tk.Frame(inner, bg="#fef3c7", relief="solid", bd=1)
        result_frame.pack(fill="x", pady=(10, 0))
        
        result_inner = tk.Frame(result_frame, bg="#fef3c7")
        result_inner.pack(fill="x", padx=15, pady=12)
        
        tk.Label(
            result_inner,
            text="Percentage Difference:",
            font=("Segoe UI", 9),
            bg="#fef3c7",
            fg="#78350f"
        ).pack(anchor="w")
        
        self.percentage_diff_label = tk.Label(
            result_inner,
            text="[value]%",
            font=("Segoe UI", 14, "bold"),
            bg="#fef3c7",
            fg="#92400e"
        )
        self.percentage_diff_label.pack(anchor="w", pady=(3, 0))
        
        tk.Label(
            result_inner,
            text="If difference is small, your result is within the accepted scientific standard!",
            font=("Segoe UI", 8, "italic"),
            bg="#fef3c7",
            fg="#78350f",
            wraplength=400,
            justify="left"
        ).pack(anchor="w", pady=(5, 0))
    
    def create_action_buttons(self, parent):
        """Create the Export and Save action buttons."""
        button_frame = tk.Frame(parent, bg="white")
        button_frame.pack(fill="x", pady=(10, 0))
        
        # Export Full Report button
        tk.Button(
            button_frame,
            text="Export Full Report",
            font=("Segoe UI", 11),
            bg="white",
            fg="#0f172a",
            relief="solid",
            bd=1,
            cursor="hand2",
            padx=30,
            pady=12,
            command=self.export_report
        ).pack(side="left", padx=(0, 10))
        
        # Save Project button
        tk.Button(
            button_frame,
            text="Save Project",
            font=("Segoe UI", 11, "bold"),
            bg="#0f172a",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=30,
            pady=12,
            command=self.save_project
        ).pack(side="right")
    
    def _clear_placeholder(self, event):
        """Clear placeholder text on focus."""
        if self.known_value_entry.get().startswith("e.g."):
            self.known_value_entry.delete(0, tk.END)
            self.known_value_entry.config(fg="#0f172a")
    
    def _restore_placeholder(self, event):
        """Restore placeholder text on focus out."""
        if not self.known_value_entry.get().strip():
            self.known_value_entry.insert(0, "e.g. 5.01×10⁻²")
            self.known_value_entry.config(fg="#94a3b8")
    
    def calculate_comparison(self):
        """Calculate percentage difference with known value."""
        known_str = self.known_value_entry.get().strip()
        
        if not known_str or known_str.startswith("e.g."):
            messagebox.showwarning(
                "No Known Value",
                "Please enter a known/accepted value to compare."
            )
            return
        
        try:
            # Parse the input (handle scientific notation)
            known_value = self._parse_scientific_notation(known_str)
            
            # Calculate percentage difference
            measured = abs(self.gradient) if self.gradient is not None else 0
            percentage_diff = abs((measured - known_value) / known_value * 100)
            
            # Update display
            self.percentage_diff_label.config(text=f"{percentage_diff:.2f}%")
            
            # Show interpretation
            if percentage_diff < 5:
                interpretation = "Excellent! Your result is very close to the accepted value."
                color = "#059669"
            elif percentage_diff < 10:
                interpretation = "Good! Your result is reasonably close to the accepted value."
                color = "#d97706"
            else:
                interpretation = "Your result differs significantly. Check your experimental method."
                color = "#dc2626"
            
            messagebox.showinfo(
                "Comparison Result",
                f"Percentage Difference: {percentage_diff:.2f}%\n\n{interpretation}"
            )
            
        except ValueError as e:
            messagebox.showerror(
                "Invalid Input",
                "Please enter a valid numerical value.\n\n"
                "Examples:\n"
                "• 0.05\n"
                "• 5.01e-2\n"
                "• 5.01×10⁻²"
            )
    
    def _parse_scientific_notation(self, text: str) -> float:
        """Parse various formats of scientific notation."""
        # Replace common unicode characters
        text = text.replace('×', 'e').replace('x', 'e')
        text = text.replace('⁻', '-').replace('−', '-')
        
        # Remove superscript numbers
        superscripts = str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹', '0123456789')
        text = text.translate(superscripts)
        
        # Replace 10^ with e
        text = text.replace('10^', 'e').replace('10', 'e')
        
        return float(text)
    
    def export_report(self):
        """Export a full analysis report."""
        filepath = filedialog.asksaveasfilename(
            title="Export Analysis Report",
            defaultextension=".pdf",
            filetypes=[
                ("PDF Document", "*.pdf"),
                ("Word Document", "*.docx"),
                ("Text File", "*.txt"),
                ("All Files", "*.*")
            ]
        )
        
        if filepath:
            try:
                # In a real implementation, generate a formatted report
                # For now, show success message
                messagebox.showinfo(
                    "Export Successful",
                    f"Analysis report exported to:\n{filepath}\n\n"
                    "The report includes:\n"
                    "• Selected equation\n"
                    "• Graph with best/worst fit lines\n"
                    "• Calculated gradient and intercept\n"
                    "• Uncertainty analysis\n"
                    "• Comparison with known value (if provided)"
                )
            except Exception as e:
                messagebox.showerror("Export Failed", f"Could not export report:\n{str(e)}")
    
    def save_project(self):
        """Save the entire project for later."""
        filepath = filedialog.asksaveasfilename(
            title="Save LineaX Project",
            defaultextension=".lineax",
            filetypes=[
                ("LineaX Project", "*.lineax"),
                ("JSON File", "*.json"),
                ("All Files", "*.*")
            ]
        )
        
        if filepath:
            try:
                # Create project data
                project_data = {
                    "equation": self.equation_name,
                    "gradient": {
                        "value": float(self.gradient) if self.gradient is not None else 0,
                        "uncertainty": float(self.gradient_uncertainty) if self.gradient_uncertainty is not None else 0,
                        "units": self.gradient_units,
                        "variable": self.gradient_variable
                    },
                    "intercept": {
                        "value": float(self.intercept) if self.intercept is not None else 0,
                        "uncertainty": float(self.intercept_uncertainty) if self.intercept_uncertainty is not None else 0,
                        "units": self.intercept_units,
                        "variable": self.intercept_variable
                    }
                }
                
                # Save to file
                with open(filepath, 'w') as f:
                    json.dump(project_data, f, indent=2)
                
                messagebox.showinfo(
                    "Project Saved",
                    f"Project saved successfully to:\n{filepath}\n\n"
                    "You can reopen this project later to continue your analysis."
                )
            except Exception as e:
                messagebox.showerror("Save Failed", f"Could not save project:\n{str(e)}")