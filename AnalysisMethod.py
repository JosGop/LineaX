import tkinter as tk
from tkinter import ttk
from Equations import *


class AnalysisMethodScreen(tk.Frame):
    def __init__(self, parent, manager):
        super().__init__(parent, bg="#f5f6f8", padx=20, pady=20)
        self.manager = manager
        self.library = EquationLibrary()
        self.selected_equation: Equation | None = None
        self.create_layout()

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
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(1, weight=1)

        self.create_linear_panel(inner)
        self.create_automated_panel(inner)

    def create_linear_panel(self, parent):
        panel = tk.Frame(parent, bg="white", padx=20, pady=20)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        tk.Label(panel, text="Linear Graph Analysis", font=("Segoe UI", 14, "bold"), bg="white").pack(anchor="w", pady=(0, 15))

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

        self.equation_display = tk.Label(
            panel,
            text="",
            bg="#f8fafc",
            height=3,
            relief="solid"
        )
        self.equation_display.pack(fill="x", pady=10)

        tk.Label(panel, text="Select Variables", bg="white", font=("Segoe UI", 11, "bold")).pack(anchor="w",
                                                                                                 pady=(10, 5))

        tk.Label(panel, text="X Variable", bg="white").pack(anchor="w")
        self.x_var = ttk.Combobox(panel, state="readonly")
        self.x_var.pack(fill="x", pady=(0, 8))

        tk.Label(panel, text="Y Variable", bg="white").pack(anchor="w")
        self.y_var = ttk.Combobox(panel, state="readonly")
        self.y_var.pack(fill="x", pady=(0, 8))

        tk.Label(panel, text="Value to Find (optional)", bg="white").pack(anchor="w")
        self.find_var = ttk.Combobox(panel, state="readonly")
        self.find_var.pack(fill="x", pady=(0, 12))


        tk.Button(panel, text="Generate Linear Graph", bg="#0f172a", fg="white").pack(side="bottom", fill="x", pady=(25, 0))

        self.constants_frame = tk.LabelFrame(
            panel,
            text="Constant Values",
            bg="white",
            padx=10,
            pady=10
        )
        self.constants_frame.pack(fill="x", pady=10)

        self.constant_entries = {}

    def create_automated_panel(self, parent):
        panel = tk.Frame(parent, bg="white", padx=20, pady=20)
        panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        tk.Label(panel, text="Automated Model Selection", font=("Segoe UI", 14, "bold"), bg="white").pack(anchor="w", pady=(0, 15))

        models = ["Linear", "Quadratic", "Cubic", "Exponential", "Logarithmic", "Gaussian", "Logistic", "Sinusoidal"]
        for model in models:
            tk.Label(panel, text=model, bg="white").pack(anchor="w", pady=2)

        tk.Button(panel, text="Generate Graph", bg="#0f172a", fg="white").pack(side="bottom", fill="x", pady=(25, 0))

    def _on_search(self, event):
        query = self.search_entry.get()
        if query == self.search_placeholder:
            return
        results = self.library.search(query)
        self.results_box.delete(0, tk.END)
        for eq in results:
            self.results_box.insert(tk.END, f"{eq.name}             {eq.expression}")



    def _select_equation(self, event):
        if not self.results_box.curselection():
            return

        index = self.results_box.curselection()[0]
        display_text = self.results_box.get(index)
        name = display_text.split()[0]

        for eq in self.library.search(name):
            self.selected_equation = eq
            break

        self.equation_display.config(text=self.selected_equation.expression)

        vars_list = list(self.selected_equation.variables.keys())

        self.x_var.config(values=vars_list)
        self.y_var.config(values=vars_list)
        self.find_var.config(values=["None"] + vars_list)
        self.find_var.set("None")

        self.x_var.bind("<<ComboboxSelected>>", self._on_variable_change)
        self.y_var.bind("<<ComboboxSelected>>", self._on_variable_change)
        self.find_var.bind("<<ComboboxSelected>>", self._on_variable_change)

        self.find_var.set("None")
        self._enforce_variable_rules()
        self._update_constants()


    def _update_constants(self, event=None):
        for widget in self.constants_frame.winfo_children():
            widget.destroy()

        if not self.selected_equation:
            return

        x = self.x_var.get()
        y = self.y_var.get()
        f = self.find_var.get()

        chosen = {x, y}
        if f and f != "None":
            chosen.add(f)

        remaining = [
            v for v in self.selected_equation.variables.keys()
            if v not in chosen
        ]

        self.constant_entries.clear()

        for var in remaining:
            row = tk.Frame(self.constants_frame, bg="white")
            row.pack(fill="x", pady=3)

            tk.Label(
                row,
                text=f"{var} =",
                width=6,
                anchor="w",
                bg="white"
            ).pack(side="left")

            entry = tk.Entry(row)
            entry.pack(side="left", fill="x", expand=True)

            default = self._default_constant(var)
            if default is not None:
                entry.insert(0, str(default))

            self.constant_entries[var] = entry

    def _default_constant(self, symbol):
        constants = {
            "h": 6.626e-34,
            "c": 3.0e8,
            "R": 8.314,
            "g": 9.81,
            "n": 1
        }
        return constants.get(symbol)

    def _on_variable_change(self, event=None):
        self._enforce_variable_rules()
        self._update_constants()

    def _enforce_variable_rules(self):
        if not self.selected_equation:
            return

        all_vars = list(self.selected_equation.variables.keys())

        x = self.x_var.get()
        y = self.y_var.get()
        f = self.find_var.get()

        # X and Y must be different
        if x and x == y:
            self.y_var.set("")

        # Rebuild Y options excluding X
        y_options = [v for v in all_vars if v != x]
        self.y_var.config(values=y_options)

        # Rebuild X options excluding Y
        x_options = [v for v in all_vars if v != y]
        self.x_var.config(values=x_options)

        # Find cannot clash with X or Y
        find_options = ["None"] + [
            v for v in all_vars
            if v != x and v != y
        ]
        self.find_var.config(values=find_options)

        if f in (x, y):
            self.find_var.set("None")

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
    # AnalysisMethodScreen(root).pack(fill="both", expand=True)
    class DummyManager:
        def show(self, *_): pass
        def back(self): pass
    AnalysisMethodScreen(root, DummyManager()).pack(fill="both", expand=True)
    root.mainloop()
