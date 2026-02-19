"""
GraphSettings.py

Provides an Excel-style Chart Elements popup for toggling graph visual components.
Implements the 'Options to toggle/change aspects' sub-component from Section 3.2.1
(Branch 4 — Graphs), specifically the Style/Theme, Edit Scale/Range, and Edit Labels
sub-sub-components. Also corresponds to the 'Settings Button' described in the User
Interface design for Screen 3a (Linear Graph Output) and Screen 3b (Automated Graph
Output) in Section 3.2.2. Addresses the usability requirement for dynamic graph
customisation identified in Section 3.1.4 (Solution Requirements).
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict

# Default states shared by ChartElementsPopup and ChartCustomizationMixin — mirrors
# the default graph elements listed in the Screen 3a UI description (Section 3.2.2)
_DEFAULT_ELEMENT_STATES: Dict[str, bool] = {
    'axes': True, 'axis_titles': True, 'chart_title': True,
    'data_labels': False, 'error_bars': True, 'gridlines': True,
    'legend': True, 'best_fit': True, 'worst_fit': True,
}

# Ordered list of (key, display_label) pairs for checkbox generation; order matches UI mockup
_ELEMENT_LABELS = [
    ('axes', 'Axes'), ('axis_titles', 'Axis Titles'), ('chart_title', 'Chart Title'),
    ('data_labels', 'Data Labels'), ('error_bars', 'Error Bars'), ('gridlines', 'Gridlines'),
    ('legend', 'Legend'), ('best_fit', 'Best Fit Line'), ('worst_fit', 'Worst Fit Lines'),
]


class ChartElementsPopup(tk.Toplevel):
    """
    Excel-style chart customisation popup with checkboxes.

    Implements the chart element toggle panel described in Section 3.2.1 (Branch 4 —
    Options to toggle/change aspects) and Section 3.2.2 (User Interface, Screen 3a).
    The 'always-on-top' behaviour and proximity to the parent window match the
    accessibility and usability requirements in Section 3.1.4 (Usability Features).
    Error bars and best/worst fit toggles directly control Algorithm 5 output
    visibility (Section 3.2.2).
    """

    def __init__(self, parent, update_callback: Callable):
        """
        Initialise the Chart Elements popup.

        Args:
            parent: Parent tkinter window.
            update_callback: Called with a dict of element states whenever a toggle changes.
        """
        super().__init__(parent)
        self.update_callback = update_callback  # triggers graph redraw in ChartCustomizationMixin

        self.title("Chart Elements")
        self.geometry("250x400")
        self.resizable(False, False)
        self.configure(bg="#f0f0f0")
        self.transient(parent)
        self.attributes('-topmost', True)  # keeps popup visible above the main window

        self._position_window(parent)

        # Initialise BooleanVars from shared defaults — False = hidden, True = shown
        self.element_states = {k: tk.BooleanVar(value=v) for k, v in _DEFAULT_ELEMENT_STATES.items()}

        self.create_ui()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _position_window(self, parent):
        """
        Position the popup near the top-right of the parent window.

        Ensures the panel does not obstruct the graph area, consistent with the
        Excel-style interaction pattern identified in Section 3.1.3 (Research —
        Microsoft Excel, Features That Can Be Adapted).
        """
        self.update_idletasks()
        x = parent.winfo_x() + parent.winfo_width() - 270
        y = parent.winfo_y() + 100
        self.geometry(f"+{x}+{y}")

    def create_ui(self):
        """
        Build the checkbox interface.

        Constructs the header bar, scrollable checkbox list, separator, and action
        buttons. The 'Reset to Default' and 'Apply' buttons satisfy the Error Recovery
        usability requirement from Section 3.2.2 (Usability Features), allowing users
        to undo visual changes without restarting the analysis.
        """
        header = tk.Frame(self, bg="#0078d4", height=35)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="⚙ Chart Elements", font=("Segoe UI", 11, "bold"),
                 bg="#0078d4", fg="white").pack(side="left", padx=10, pady=8)

        content = tk.Frame(self, bg="white", padx=5, pady=10)
        content.pack(fill="both", expand=True)

        for key, label in _ELEMENT_LABELS:
            self.create_checkbox_item(content, key, label)  # one row per toggleable element

        ttk.Separator(content, orient="horizontal").pack(fill="x", pady=10)

        button_frame = tk.Frame(content, bg="white")
        button_frame.pack(fill="x", pady=5)
        tk.Button(button_frame, text="Reset to Default", font=("Segoe UI", 9), bg="#f0f0f0",
                  fg="#333", relief="solid", bd=1, cursor="hand2",
                  command=self.reset_to_default).pack(side="left", padx=5)
        tk.Button(button_frame, text="Apply", font=("Segoe UI", 9, "bold"), bg="#0078d4",
                  fg="white", relief="flat", cursor="hand2", padx=15,
                  command=self.apply_changes).pack(side="right", padx=5)

    def create_checkbox_item(self, parent, key: str, label: str):
        """
        Create a single checkbox row with hover highlight.

        Each checkbox controls one graph element as listed in _ELEMENT_LABELS. Hover
        highlighting provides immediate visual feedback, addressing the usability goal
        in Section 3.1.4 that the interface must be intuitive and accessible for
        students (stakeholder M and DG interviews, Section 3.1.2).
        """
        item_frame = tk.Frame(parent, bg="white", height=32)
        item_frame.pack(fill="x", pady=1)
        item_frame.pack_propagate(False)

        checkbox = tk.Checkbutton(item_frame, text=label, variable=self.element_states[key],
                                  font=("Segoe UI", 10), bg="white", activebackground="#e5f3ff",
                                  selectcolor="white", relief="flat", cursor="hand2",
                                  command=lambda: self.on_element_toggle(key))
        checkbox.pack(side="left", padx=10, pady=5, fill="both", expand=True)

        def on_enter(e):
            item_frame.config(bg="#e5f3ff")  # blue tint on hover for visual affordance
            checkbox.config(bg="#e5f3ff")

        def on_leave(e):
            item_frame.config(bg="white")    # restore neutral background on mouse exit
            checkbox.config(bg="white")

        for widget in (item_frame, checkbox):
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

    def on_element_toggle(self, key: str):
        """
        Notify callback when any checkbox is toggled.

        Triggers ChartCustomizationMixin.update_chart_elements(), which stores the new
        state and calls refresh_graph() to redraw immediately — implementing the live
        preview behaviour described in the dynamic graph scaling usability feature
        (Section 3.2.2, Usability Features).
        """
        if self.update_callback:
            self.update_callback(self.get_element_states())

    def get_element_states(self) -> Dict[str, bool]:
        """
        Return the current state of all elements as a plain dict.

        Used by ChartCustomizationMixin.update_chart_elements() and by
        create_graph_with_customization() to determine which graph components
        to render, corresponding to the user_settings variable in the Key Variables
        table (Section 3.2.2).
        """
        return {key: var.get() for key, var in self.element_states.items()}

    def reset_to_default(self):
        """
        Reset all checkboxes to their defaults and notify the callback.

        Implements the Error Recovery usability feature from Section 3.2.2, allowing
        users to restore the default graph state without re-running analysis.
        """
        for key, value in _DEFAULT_ELEMENT_STATES.items():
            self.element_states[key].set(value)
        if self.update_callback:
            self.update_callback(self.get_element_states())  # redraw with defaults

    def apply_changes(self):
        """
        Apply current state and close the popup.

        Provides an explicit confirmation step before closing, consistent with the
        two-button pattern (Apply/Cancel) described in the Screen 4 UI design
        (Section 3.2.2, User Interface).
        """
        if self.update_callback:
            self.update_callback(self.get_element_states())
        self.destroy()


class ChartCustomizationMixin:
    """
    Mixin that adds Chart Elements popup functionality to a graph results screen.

    Implements the 'Options to toggle/change aspects' sub-component from Section 3.2.1
    (Branch 4 — Graphs) as a reusable mixin, following the modular OOP architecture
    described in Section 3.3 Development. Designed to be mixed into LinearGraphDisplay
    and AutomatedGraphDisplay without code duplication. Uses composition over inheritance
    to keep graph-specific logic separate from UI customisation logic.
    """

    def init_chart_customization(self):
        """
        Initialise chart customisation state.

        Called during screen construction to set up the popup reference and state dict.
        Must be invoked before open_chart_elements() is used, ensuring the mixin
        attributes exist regardless of the subclass constructor order.
        """
        self.chart_elements_popup = None            # reference to open popup (None if closed)
        self.chart_element_states = dict(_DEFAULT_ELEMENT_STATES)  # current toggle state

    def open_chart_elements(self):
        """
        Open the Chart Elements popup, or bring it to front if already open.

        Prevents duplicate popups from being created, which would cause conflicting state
        updates. This guard satisfies the usability requirement from Section 3.1.4 that
        the interface must not produce confusing or unexpected behaviour.
        """
        if self.chart_elements_popup is not None:
            self.chart_elements_popup.lift()  # raise existing popup rather than opening another
            return

        self.chart_elements_popup = ChartElementsPopup(self.parent, self.update_chart_elements)
        for key, value in self.chart_element_states.items():
            if key in self.chart_elements_popup.element_states:
                self.chart_elements_popup.element_states[key].set(value)  # restore current state
        self.chart_elements_popup.protocol("WM_DELETE_WINDOW",
                                           lambda: setattr(self, 'chart_elements_popup', None))

    def update_chart_elements(self, states: Dict[str, bool]):
        """
        Store updated element states and redraw the graph.

        Called by ChartElementsPopup.on_element_toggle() and apply_changes(). Stores
        the new state and triggers refresh_graph() to rebuild the Matplotlib figure,
        implementing the live dynamic graph update described in Section 3.2.1 (Branch 4
        — Display sub-component).
        """
        self.chart_element_states = states
        self.refresh_graph()  # destroy old canvas and redraw with new visibility settings

    def refresh_graph(self):
        """
        Destroy existing canvas and figure, then recreate the graph.

        Ensures stale Matplotlib figures are properly closed before a new one is drawn,
        preventing memory leaks from accumulating Figure objects. Corresponds to the
        performance testing requirement in Section 3.2.3 (Stage 1 — Large Dataset test).
        """
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.get_tk_widget().destroy()
        if hasattr(self, 'figure') and self.figure:
            import matplotlib.pyplot as plt
            plt.close(self.figure)  # release Matplotlib memory
        self.create_graph()

    def create_graph_with_customization(self):
        """
        Modified create_graph that respects chart element states.

        Full reference implementation of the graph rendering pipeline described in
        Section 3.2.1 (Branch 4 — Plotting sub-component) and Algorithm 8 from Section
        3.2.2. Renders: scatter data points (Algorithm 1 input), error bars (Algorithm 4
        output), best-fit line (Algorithm 1 gradient/intercept), worst-fit lines
        (Algorithm 5 output), axis titles, legend, and gridlines — all conditionally
        controlled by chart_element_states. Should replace or wrap create_graph() in
        LinearGraphDisplay.py and AutomatedGraphDisplay.py.
        """
        import matplotlib.pyplot as plt
        import numpy as np
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        if self.input_data is None:
            return

        states = self.chart_element_states
        self.figure = plt.Figure(figsize=(8, 5), dpi=100, facecolor='white')
        ax = self.figure.add_subplot(111)  # single axes object; referenced by all plot calls

        x, y = self.input_data.x_values, self.input_data.y_values
        # Error bars are suppressed when the toggle is off (Section 3.2.2, Key Variable: error_bars)
        x_err = self.input_data.x_error if states['error_bars'] else None
        y_err = self.input_data.y_error if states['error_bars'] else None

        # Plot data points with error bars — error bar display controlled by Algorithm 4 output
        ax.errorbar(x, y, xerr=x_err, yerr=y_err, fmt='o', color='#3b82f6', ecolor='#94a3b8',
                    capsize=4, markersize=6, label='Data points' if states['legend'] else '', zorder=3)

        if states['data_labels']:
            # Annotate each point with its y-value for educational clarity (Section 3.2.2, data_labels)
            for xi, yi in zip(x, y):
                ax.annotate(f'{yi:.2f}', (xi, yi), textcoords="offset points",
                            xytext=(0, 8), ha='center', fontsize=8, color='#333')

        if states['best_fit']:
            # Draw best-fit line using gradient and intercept from Algorithm 1 (Section 3.2.2)
            x_line = np.linspace(x[0], x[-1], 100)
            ax.plot(x_line, self.best_fit_gradient * x_line + self.best_fit_intercept,
                    color='#10b981', linewidth=2, label='Best fit' if states['legend'] else '', zorder=2)

        if states['worst_fit'] and y_err is not None:
            # Draw steepest and shallowest worst-fit lines from Algorithm 5 (Section 3.2.2)
            x_pts = [x[0], x[-1]]
            ax.plot(x_pts, [y[0] + y_err[0], y[-1] - y_err[-1]], color='#ef4444', linestyle='--',
                    linewidth=1.5, label='Worst fit (max)' if states['legend'] else '', zorder=1)
            ax.plot(x_pts, [y[0] - y_err[0], y[-1] + y_err[-1]], color='#f97316', linestyle='--',
                    linewidth=1.5, label='Worst fit (min)' if states['legend'] else '', zorder=1)

        if states['axis_titles']:
            # Use transformed axis titles (e.g., "ln(Intensity)") updated by DataTransform.py
            ax.set_xlabel(self.input_data.x_title or "X", fontsize=11, fontweight='bold')
            ax.set_ylabel(self.input_data.y_title or "Y", fontsize=11, fontweight='bold')
        if states['chart_title']:
            ax.set_title("Linear Regression Analysis", fontsize=13, fontweight='bold', pad=15)
        if states['gridlines']:
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)  # subtle gridlines per UI mockup
        if states['legend']:
            ax.legend(loc='best', framealpha=0.9, fontsize=9)
        if not states['axes']:
            # Hide all axis spines and ticks when axes toggle is off
            ax.set_frame_on(False)
            ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

        self.figure.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)


if __name__ == "__main__":
    import numpy as np

    class DemoWindow:
        """Standalone demonstration of ChartElementsPopup — used for development testing."""
        def __init__(self, root):
            self.root = root
            self.root.title("Chart Elements Demo")
            self.root.geometry("600x400")
            self.chart_states = dict(_DEFAULT_ELEMENT_STATES)

            self.info_label = tk.Label(root, text="Click 'Open Chart Elements' to customize",
                                       font=("Segoe UI", 14), pady=20)
            self.info_label.pack()

            self.state_text = tk.Text(root, height=15, width=50, font=("Courier", 10))
            self.state_text.pack(pady=10)
            self.update_state_display()

            tk.Button(root, text="Open Chart Elements", font=("Segoe UI", 12, "bold"),
                      bg="#0078d4", fg="white", padx=30, pady=10, command=self.open_popup).pack(pady=10)

        def open_popup(self):
            popup = ChartElementsPopup(self.root, self.on_elements_changed)
            for key, value in self.chart_states.items():
                if key in popup.element_states:
                    popup.element_states[key].set(value)  # restore current state on each open

        def on_elements_changed(self, states):
            self.chart_states = states
            self.update_state_display()

        def update_state_display(self):
            """Refresh the text widget to show current element states — white-box testing aid."""
            self.state_text.delete(1.0, tk.END)
            self.state_text.insert(1.0, "Current Chart Element States:\n\n")
            for key, value in self.chart_states.items():
                self.state_text.insert(tk.END, f"{'✔ ON ' if value else '✗ OFF'}  {key.replace('_', ' ').title()}\n")

    root = tk.Tk()
    app = DemoWindow(root)
    root.mainloop()