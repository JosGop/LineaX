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

        self.equation_display = tk.Label(panel, text="", bg="#f8fafc", height=3, relief="solid")
        self.equation_display.pack(fill="x", pady=10)

        tk.Label(panel, text="X Variable", bg="white").pack(anchor="w")
        self.x_var = ttk.Combobox(panel, state="readonly")
        self.x_var.pack(fill="x", pady=(0, 10))

        tk.Label(panel, text="Y Variable", bg="white").pack(anchor="w")
        self.y_var = ttk.Combobox(panel, state="readonly")
        self.y_var.pack(fill="x")

        tk.Button(panel, text="Generate Linear Graph", bg="#0f172a", fg="white").pack(side="bottom", fill="x", pady=(25, 0))

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
        name = self.results_box.get(index)
        for eq in self.library.search(name):
            self.selected_equation = eq
            break
        self.equation_display.config(text=self.selected_equation.expression)
        vars_list = list(self.selected_equation.variables.keys())
        self.x_var.config(values=vars_list)
        self.y_var.config(values=vars_list)

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
