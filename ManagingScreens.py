import tkinter as tk


def make_scrollable(parent, row, column, padx=(0, 0), pady=0, bg="white", panel_kwargs=None):
    """Create and grid a scrollable panel; return (container, panel, canvas, scrollbar)."""
    panel_kwargs = panel_kwargs or {}

    panel_container = tk.Frame(parent, bg=bg)
    panel_container.grid(row=row, column=column, sticky="nsew", padx=padx, pady=pady)

    canvas = tk.Canvas(panel_container, bg=bg, highlightthickness=0)
    scrollbar = tk.Scrollbar(panel_container, orient="vertical", command=canvas.yview)
    panel = tk.Frame(canvas, bg=bg, **panel_kwargs)

    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    canvas_frame = canvas.create_window((0, 0), window=panel, anchor="nw")

    panel.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_frame, width=e.width))

    def _on_mousewheel(event):
        if event.delta:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return
        if getattr(event, "num", None) == 4:
            canvas.yview_scroll(-1, "units")
        elif getattr(event, "num", None) == 5:
            canvas.yview_scroll(1, "units")

    def _bind_mousewheel(_event):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)

    def _unbind_mousewheel(_event):
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

    panel.bind("<Enter>", _bind_mousewheel)
    panel.bind("<Leave>", _unbind_mousewheel)

    return panel_container, panel, canvas, scrollbar


class ScreenManager:
    def __init__(self, root):
        self.root = root
        self.stack = []
        self.current_screen = None

        # Shared application state
        self.input_data = None
        self.raw_data = None
        self.graph_figure = None
        self.equation_info = None
        self.analysis_results = None

    def set_data(self, input_data):
        """Store InputData instance for access across screens."""
        self.input_data = input_data

    def get_data(self):
        """Return the stored InputData instance."""
        return self.input_data

    def set_raw_data(self, raw_data):
        """Store the original untransformed InputData."""
        self.raw_data = raw_data

    def get_raw_data(self):
        """Return the original untransformed InputData."""
        return self.raw_data

    def set_graph_figure(self, figure):
        """Store the matplotlib figure from the graph screen."""
        self.graph_figure = figure

    def get_graph_figure(self):
        """Return the stored matplotlib figure."""
        return self.graph_figure

    def set_equation_info(self, equation_info):
        """
        Store equation metadata from the AnalysisMethod screen.

        Args:
            equation_info: Dict with keys: name, gradient_variable, gradient_units,
                           intercept_variable, intercept_units.
        """
        self.equation_info = equation_info

    def get_equation_info(self):
        """Return stored equation metadata."""
        return self.equation_info

    def set_analysis_results(self, analysis_results):
        """
        Store regression results from GraphResultsScreen.

        Args:
            analysis_results: Dict with keys: equation_name, gradient, gradient_uncertainty,
                              gradient_variable, gradient_units, intercept, intercept_uncertainty,
                              intercept_variable, intercept_units.
        """
        self.analysis_results = analysis_results

    def get_analysis_results(self):
        """Return stored regression results."""
        return self.analysis_results

    def show(self, screen_class):
        if self.current_screen is not None:
            self.stack.append(self.current_screen)
            self.current_screen.pack_forget()
        self.current_screen = screen_class(self.root, self)
        self.current_screen.pack(fill="both", expand=True)

    def back(self):
        if not self.stack:
            return
        self.current_screen.pack_forget()
        self.current_screen = self.stack.pop()
        self.current_screen.pack(fill="both", expand=True)