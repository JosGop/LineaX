"""
ManagingScreens.py

Manages screen navigation and shared application state across all LineaX screens.
Implements the multi-screen architecture described in Section 3.2.2 (Structure of the Solution) and the linear navigation
flow shown in the Data Flow diagram (Section 3.2.1 — Data Flow Through the System): Screen 1 (Data Input) → Screen 2
(Analysis Method) → Screen 3a/3b (Graph Output) → Screen 4 (Gradient Analysis).
The ScreenManager acts as a central state store so that InputData, equation metadata, and analysis results can be passed
between screens without global variables, consistent with the modular OOP design.
"""

import tkinter as tk


def make_scrollable(parent, row, column, padx=(0, 0), pady=0, bg="white", panel_kwargs=None):
    """
    Create and grid a scrollable panel; return (container, panel, canvas, scrollbar).

    Used by data-heavy screens (Data Input, Analysis Method) to accommodate variable-length content without fixed window
    resizing. The mousewheel bindings handle cross-platform scroll events (Windows: event.delta, Linux: Button-4/5),
    satisfying the usability requirement in Section 3.1.4 that the interface must be accessible on common operating
    systems. Panel resizes with the canvas via the <Configure> binding, implementing the dynamic graph scaling usability
    eature mentioned in Section 3.2.2 (Usability Features).
    """
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

    # Resize scroll region when panel contents change (e.g., adding rows to data grid)
    panel.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
    # Resize inner frame to match canvas width when window is resized
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_frame, width=e.width))

    def _on_mousewheel(event):
        """Handle scroll events for Windows (event.delta) and Linux (Button-4/5)."""
        if event.delta:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return
        if getattr(event, "num", None) == 4:
            canvas.yview_scroll(-1, "units")
        elif getattr(event, "num", None) == 5:
            canvas.yview_scroll(1, "units")

    def _bind_mousewheel(_event):
        """Bind scroll events when the mouse enters the panel."""
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)

    def _unbind_mousewheel(_event):
        """Unbind scroll events when the mouse leaves to avoid intercepting other panels."""
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

    panel.bind("<Enter>", _bind_mousewheel)
    panel.bind("<Leave>", _unbind_mousewheel)

    return panel_container, panel, canvas, scrollbar


class ScreenManager:
    """
    Central controller for screen navigation and shared application state.

    Implements the screen stack and state-passing architecture described in Section 3.2.2 (Structure of the Solution).
    The stack-based show()/back() pattern mirrors the linear navigation flow in the Data Flow diagram (Section 3.2.1) while
    also supporting the 'Cancel Mid-Analysis' black-box test scenario (Section 3.2.3, Stage 2). Shared state attributes
    (input_data, equation_info, analysis_results) replace global variables, keeping each screen module testable in isolation
    as required by the white-box testing approach in Section 3.2.3 (Stage 1).
    """

    def __init__(self, root):
        self.root = root
        self.stack = []             # history of previous screens for back() navigation
        self.current_screen = None  # the screen currently displayed in the root window

        # Shared application state — passed between screens via set/get methods
        self.input_data = None       # InputData instance from DataInput.py (Screen 1)
        self.raw_data = None         # original untransformed InputData, preserved for re-analysis
        self.graph_figure = None     # Matplotlib Figure from LinearGraphDisplay / AutomatedGraphDisplay
        self.equation_info = None    # equation metadata dict from AnalysisMethod.py (Screen 2)
        self.analysis_results = None # regression results dict from LinearGraphDisplay.py (Screen 3a)

    def set_data(self, input_data):
        """
        Store InputData instance for access across screens.

        Called by DataInputScreen after validation (Algorithm 1, Section 3.2.2) to make the cleaned InputData available
        to Screen 2 (Analysis Method) and beyond.
        Corresponds to the x_values, y_values, x_error, y_error variables in  Key Variables table (Section 3.2.2).
        """
        self.input_data = input_data

    def get_data(self):
        """
        Return the stored InputData instance.

        Retrieved by AnalysisMethod.py (Screen 2) and graph display screens (Screen 3a/3b) to access the validated experimental
        data produced by the Data Input Screen.
        """
        return self.input_data

    def set_raw_data(self, raw_data):
        """
        Store the original untransformed InputData.

        Called before DataTransformer.transform_for_linearisation() is applied, so the raw dataset can be retrieved for
        re-analysis via 'Fit other Models' (Section 3.2.1, Branch 4 — Fit other Models sub-sub-component) or for back-transforming
        values to validate consistency (Section 3.2.1, Ensure consistency with results sub-component).
        """
        self.raw_data = raw_data

    def get_raw_data(self):
        """
        Return the original untransformed InputData.

        Used by DataTransformer.revert_to_raw() and the 'Fit other Models' workflow, ensuring the original dataset is always
        available without re-importing the file.
        """
        return self.raw_data

    def set_graph_figure(self, figure):
        """
        Store the matplotlib figure from the graph screen.

        Enables the Export Full Report functionality described in Screen 4 (Section 3.2.2, User Interface) to include the
        generated graph in the PDF export without re-rendering.
        """
        self.graph_figure = figure

    def get_graph_figure(self):
        """Return the stored matplotlib figure for export or re-display."""
        return self.graph_figure

    def set_equation_info(self, equation_info):
        """
        Store equation metadata from the AnalysisMethod screen.

        Called by AnalysisMethod.py (Screen 2) after the user selects a scientific equation and defines variable roles.
        Passes physical interpretation metadata forward to Screen 3a and Screen 4 so that gradient and intercept can be
        labelled correctly (Section 3.2.2, User Interface — Screen 4, Section 1: Selected Equation).

        Args:
            equation_info: Dict with keys: name, gradient_variable, gradient_units,
                           intercept_variable, intercept_units.
        """
        self.equation_info = equation_info

    def get_equation_info(self):
        """
        Return stored equation metadata.

        Retrieved by GradientAnalysis.py to populate the 'Where: gradient = [Variable]' label on Screen 4 (Section 3.2.2,
        User Interface — Screen 4, Section 1).
        """
        return self.equation_info

    def set_analysis_results(self, analysis_results):
        """
        Store regression results from GraphResultsScreen.

        Called by LinearGraphDisplay.py after Algorithm 1 (gradient and intercept calculation, Section 3.2.2) and
        Algorithm 5 (worst-fit gradients, Section 3.2.2) have been computed. These results are displayed on Screen 4
        (Gradient Analysis & Results) and used to calculate the final physical constant.

        Args:
            analysis_results: Dict with keys: equation_name, gradient, gradient_uncertainty,
                              gradient_variable, gradient_units, intercept, intercept_uncertainty,
                              intercept_variable, intercept_units.
        """
        self.analysis_results = analysis_results

    def get_analysis_results(self):
        """
        Return stored regression results.

        Retrieved by GradientAnalysis.py to populate all three sections of Screen 4:
        Selected Equation, Calculated Unknown Value, and Compare with Known Value (Section 3.2.2, User Interface).
        """
        return self.analysis_results

    def show(self, screen_class):
        """
        Display a new screen, pushing the current one onto the back-navigation stack.

        Implements the forward navigation in the Data Flow (Section 3.2.1 — Data Flow Through the System). Hides rather
        than destroys the previous screen so it can be restored by back(), supporting the 'Cancel Mid-Analysis' test scenario
        (Section 3.2.3, Stage 2) and the Error Recovery usability feature (Section 3.2.2, Usability Features).
        """
        if self.current_screen is not None:
            self.stack.append(self.current_screen)  # save current screen for back()
            self.current_screen.pack_forget()        # hide without destroying
        self.current_screen = screen_class(self.root, self)
        self.current_screen.pack(fill="both", expand=True)

    def back(self):
        """
        Navigate to the previous screen by popping from the stack.

        Supports the backward navigation described in the Data Flow (Section 3.2.1) and tested in the 'Cancel Mid-Analysis'
        black-box test scenario (Section 3.2.3, Stage 2). Does nothing if the stack is empty, preventing underflow when
        the user is already on the first screen.
        """
        if not self.stack:
            return  # already at the first screen; no previous screen to restore
        self.current_screen.pack_forget()   # hide the current screen
        self.current_screen = self.stack.pop()
        self.current_screen.pack(fill="both", expand=True)  # restore the previous screen