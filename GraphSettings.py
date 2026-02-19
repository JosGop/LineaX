"""
GraphSettings.py - Excel-style Chart Elements Panel.

Provides a popup interface for toggling chart elements such as axes, axis titles,
chart title, data labels, error bars, gridlines, legend, and trendlines.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict

# Default states shared by ChartElementsPopup and ChartCustomizationMixin
_DEFAULT_ELEMENT_STATES: Dict[str, bool] = {
    'axes': True, 'axis_titles': True, 'chart_title': True,
    'data_labels': False, 'error_bars': True, 'gridlines': True,
    'legend': True, 'best_fit': True, 'worst_fit': True,
}

_ELEMENT_LABELS = [
    ('axes', 'Axes'), ('axis_titles', 'Axis Titles'), ('chart_title', 'Chart Title'),
    ('data_labels', 'Data Labels'), ('error_bars', 'Error Bars'), ('gridlines', 'Gridlines'),
    ('legend', 'Legend'), ('best_fit', 'Best Fit Line'), ('worst_fit', 'Worst Fit Lines'),
]


class ChartElementsPopup(tk.Toplevel):
    """
    Excel-style chart customisation popup with checkboxes.

    Allows users to toggle chart elements on/off with immediate visual feedback.
    """

    def __init__(self, parent, update_callback: Callable):
        """
        Initialise the Chart Elements popup.

        Args:
            parent: Parent tkinter window.
            update_callback: Called with a dict of element states whenever a toggle changes.
        """
        super().__init__(parent)
        self.update_callback = update_callback

        self.title("Chart Elements")
        self.geometry("250x400")
        self.resizable(False, False)
        self.configure(bg="#f0f0f0")
        self.transient(parent)
        self.attributes('-topmost', True)

        self._position_window(parent)

        # Initialise BooleanVars from shared defaults
        self.element_states = {k: tk.BooleanVar(value=v) for k, v in _DEFAULT_ELEMENT_STATES.items()}

        self.create_ui()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _position_window(self, parent):
        """Position the popup near the top-right of the parent window."""
        self.update_idletasks()
        x = parent.winfo_x() + parent.winfo_width() - 270
        y = parent.winfo_y() + 100
        self.geometry(f"+{x}+{y}")

    def create_ui(self):
        """Build the checkbox interface."""
        header = tk.Frame(self, bg="#0078d4", height=35)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="⚙ Chart Elements", font=("Segoe UI", 11, "bold"),
                 bg="#0078d4", fg="white").pack(side="left", padx=10, pady=8)

        content = tk.Frame(self, bg="white", padx=5, pady=10)
        content.pack(fill="both", expand=True)

        for key, label in _ELEMENT_LABELS:
            self.create_checkbox_item(content, key, label)

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
        """Create a single checkbox row with hover highlight."""
        item_frame = tk.Frame(parent, bg="white", height=32)
        item_frame.pack(fill="x", pady=1)
        item_frame.pack_propagate(False)

        checkbox = tk.Checkbutton(item_frame, text=label, variable=self.element_states[key],
                                  font=("Segoe UI", 10), bg="white", activebackground="#e5f3ff",
                                  selectcolor="white", relief="flat", cursor="hand2",
                                  command=lambda: self.on_element_toggle(key))
        checkbox.pack(side="left", padx=10, pady=5, fill="both", expand=True)

        def on_enter(e):
            item_frame.config(bg="#e5f3ff")
            checkbox.config(bg="#e5f3ff")

        def on_leave(e):
            item_frame.config(bg="white")
            checkbox.config(bg="white")

        for widget in (item_frame, checkbox):
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

    def on_element_toggle(self, key: str):
        """Notify callback when any checkbox is toggled."""
        if self.update_callback:
            self.update_callback(self.get_element_states())

    def get_element_states(self) -> Dict[str, bool]:
        """Return the current state of all elements as a plain dict."""
        return {key: var.get() for key, var in self.element_states.items()}

    def reset_to_default(self):
        """Reset all checkboxes to their defaults and notify the callback."""
        for key, value in _DEFAULT_ELEMENT_STATES.items():
            self.element_states[key].set(value)
        if self.update_callback:
            self.update_callback(self.get_element_states())

    def apply_changes(self):
        """Apply current state and close the popup."""
        if self.update_callback:
            self.update_callback(self.get_element_states())
        self.destroy()


class ChartCustomizationMixin:
    """
    Mixin that adds Chart Elements popup functionality to a graph results screen.

    Add this to your GraphResultsScreen class to enable chart customisation.
    """

    def init_chart_customization(self):
        """Initialise chart customisation state."""
        self.chart_elements_popup = None
        self.chart_element_states = dict(_DEFAULT_ELEMENT_STATES)

    def open_chart_elements(self):
        """Open the Chart Elements popup, or bring it to front if already open."""
        if self.chart_elements_popup is not None:
            self.chart_elements_popup.lift()
            return

        self.chart_elements_popup = ChartElementsPopup(self.parent, self.update_chart_elements)
        for key, value in self.chart_element_states.items():
            if key in self.chart_elements_popup.element_states:
                self.chart_elements_popup.element_states[key].set(value)
        self.chart_elements_popup.protocol("WM_DELETE_WINDOW",
                                           lambda: setattr(self, 'chart_elements_popup', None))

    def update_chart_elements(self, states: Dict[str, bool]):
        """Store updated element states and redraw the graph."""
        self.chart_element_states = states
        self.refresh_graph()

    def refresh_graph(self):
        """Destroy existing canvas and figure, then recreate the graph."""
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.get_tk_widget().destroy()
        if hasattr(self, 'figure') and self.figure:
            import matplotlib.pyplot as plt
            plt.close(self.figure)
        self.create_graph()

    def create_graph_with_customization(self):
        """
        Modified create_graph that respects chart element states.

        Should replace or be called by the existing create_graph method.
        """
        import matplotlib.pyplot as plt
        import numpy as np
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        if self.input_data is None:
            return

        states = self.chart_element_states
        self.figure = plt.Figure(figsize=(8, 5), dpi=100, facecolor='white')
        ax = self.figure.add_subplot(111)

        x, y = self.input_data.x_values, self.input_data.y_values
        x_err = self.input_data.x_error if states['error_bars'] else None
        y_err = self.input_data.y_error if states['error_bars'] else None

        ax.errorbar(x, y, xerr=x_err, yerr=y_err, fmt='o', color='#3b82f6', ecolor='#94a3b8',
                    capsize=4, markersize=6, label='Data points' if states['legend'] else '', zorder=3)

        if states['data_labels']:
            for xi, yi in zip(x, y):
                ax.annotate(f'{yi:.2f}', (xi, yi), textcoords="offset points",
                            xytext=(0, 8), ha='center', fontsize=8, color='#333')

        if states['best_fit']:
            x_line = np.linspace(x[0], x[-1], 100)
            ax.plot(x_line, self.best_fit_gradient * x_line + self.best_fit_intercept,
                    color='#10b981', linewidth=2, label='Best fit' if states['legend'] else '', zorder=2)

        if states['worst_fit'] and y_err is not None:
            x_pts = [x[0], x[-1]]
            ax.plot(x_pts, [y[0] + y_err[0], y[-1] - y_err[-1]], color='#ef4444', linestyle='--',
                    linewidth=1.5, label='Worst fit (max)' if states['legend'] else '', zorder=1)
            ax.plot(x_pts, [y[0] - y_err[0], y[-1] + y_err[-1]], color='#f97316', linestyle='--',
                    linewidth=1.5, label='Worst fit (min)' if states['legend'] else '', zorder=1)

        if states['axis_titles']:
            ax.set_xlabel(self.input_data.x_title or "X", fontsize=11, fontweight='bold')
            ax.set_ylabel(self.input_data.y_title or "Y", fontsize=11, fontweight='bold')
        if states['chart_title']:
            ax.set_title("Linear Regression Analysis", fontsize=13, fontweight='bold', pad=15)
        if states['gridlines']:
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        if states['legend']:
            ax.legend(loc='best', framealpha=0.9, fontsize=9)
        if not states['axes']:
            ax.set_frame_on(False)
            ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

        self.figure.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)


if __name__ == "__main__":
    import numpy as np

    class DemoWindow:
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
                    popup.element_states[key].set(value)

        def on_elements_changed(self, states):
            self.chart_states = states
            self.update_state_display()

        def update_state_display(self):
            self.state_text.delete(1.0, tk.END)
            self.state_text.insert(1.0, "Current Chart Element States:\n\n")
            for key, value in self.chart_states.items():
                self.state_text.insert(tk.END, f"{'✓ ON ' if value else '✗ OFF'}  {key.replace('_', ' ').title()}\n")

    root = tk.Tk()
    app = DemoWindow(root)
    root.mainloop()