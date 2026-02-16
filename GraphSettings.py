"""
ChartCustomization.py - Excel-style Chart Elements Panel

Provides a popup interface for toggling chart elements like:
- Axes, Axis Titles, Chart Title, Data Labels, Error Bars,
- Gridlines, Legend, Trendline (best/worst fit lines)
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict


class ChartElementsPopup(tk.Toplevel):
    """
    Excel-style chart customization popup with checkboxes.

    Allows users to toggle various chart elements on/off with immediate
    visual feedback on the graph.
    """

    def __init__(self, parent, update_callback: Callable):
        """
        Initialize the Chart Elements popup.

        Args:
            parent: Parent tkinter window
            update_callback: Function to call when any element is toggled
                           Should accept a dict of element states
        """
        super().__init__(parent)

        self.update_callback = update_callback

        # Window configuration
        self.title("Chart Elements")
        self.geometry("250x400")
        self.resizable(False, False)
        self.configure(bg="#f0f0f0")

        # Make it stay on top but not modal
        self.transient(parent)
        self.attributes('-topmost', True)

        # Position near the parent window
        self._position_window(parent)

        # Chart element states (default values)
        self.element_states = {
            'axes': tk.BooleanVar(value=True),
            'axis_titles': tk.BooleanVar(value=True),
            'chart_title': tk.BooleanVar(value=True),
            'data_labels': tk.BooleanVar(value=False),
            'error_bars': tk.BooleanVar(value=True),
            'gridlines': tk.BooleanVar(value=True),
            'legend': tk.BooleanVar(value=True),
            'best_fit': tk.BooleanVar(value=True),
            'worst_fit': tk.BooleanVar(value=True),
        }

        # Create UI
        self.create_ui()

        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _position_window(self, parent):
        """Position the popup near the parent window."""
        # Wait for window to be created
        self.update_idletasks()

        # Get parent position
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()

        # Position to the right of parent, slightly below top
        x = parent_x + parent_width - 270
        y = parent_y + 100

        self.geometry(f"+{x}+{y}")

    def create_ui(self):
        """Create the checkbox interface."""
        # Header
        header = tk.Frame(self, bg="#0078d4", height=35)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="⚙ Chart Elements",
            font=("Segoe UI", 11, "bold"),
            bg="#0078d4",
            fg="white"
        ).pack(side="left", padx=10, pady=8)

        # Main content area
        content = tk.Frame(self, bg="white", padx=5, pady=10)
        content.pack(fill="both", expand=True)

        # Chart elements list
        elements = [
            ('axes', 'Axes'),
            ('axis_titles', 'Axis Titles'),
            ('chart_title', 'Chart Title'),
            ('data_labels', 'Data Labels'),
            ('error_bars', 'Error Bars'),
            ('gridlines', 'Gridlines'),
            ('legend', 'Legend'),
            ('best_fit', 'Best Fit Line'),
            ('worst_fit', 'Worst Fit Lines'),
        ]

        for key, label in elements:
            self.create_checkbox_item(content, key, label)

        # Separator
        ttk.Separator(content, orient="horizontal").pack(fill="x", pady=10)

        # Action buttons
        button_frame = tk.Frame(content, bg="white")
        button_frame.pack(fill="x", pady=5)

        tk.Button(
            button_frame,
            text="Reset to Default",
            font=("Segoe UI", 9),
            bg="#f0f0f0",
            fg="#333",
            relief="solid",
            bd=1,
            cursor="hand2",
            command=self.reset_to_default
        ).pack(side="left", padx=5)

        tk.Button(
            button_frame,
            text="Apply",
            font=("Segoe UI", 9, "bold"),
            bg="#0078d4",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=15,
            command=self.apply_changes
        ).pack(side="right", padx=5)

    def create_checkbox_item(self, parent, key: str, label: str):
        """
        Create a single checkbox item with hover effect.

        Args:
            parent: Parent frame
            key: Dictionary key for this element
            label: Display label
        """
        # Container frame for hover effect
        item_frame = tk.Frame(parent, bg="white", height=32)
        item_frame.pack(fill="x", pady=1)
        item_frame.pack_propagate(False)

        # Checkbox
        checkbox = tk.Checkbutton(
            item_frame,
            text=label,
            variable=self.element_states[key],
            font=("Segoe UI", 10),
            bg="white",
            activebackground="#e5f3ff",
            selectcolor="white",
            relief="flat",
            cursor="hand2",
            command=lambda: self.on_element_toggle(key)
        )
        checkbox.pack(side="left", padx=10, pady=5, fill="both", expand=True)

        # Hover effects
        def on_enter(e):
            item_frame.config(bg="#e5f3ff")
            checkbox.config(bg="#e5f3ff")

        def on_leave(e):
            item_frame.config(bg="white")
            checkbox.config(bg="white")

        item_frame.bind("<Enter>", on_enter)
        item_frame.bind("<Leave>", on_leave)
        checkbox.bind("<Enter>", on_enter)
        checkbox.bind("<Leave>", on_leave)

    def on_element_toggle(self, key: str):
        """
        Called when a checkbox is toggled.

        Args:
            key: The element that was toggled
        """
        # Get current states
        states = self.get_element_states()

        # Call the update callback to refresh the graph
        if self.update_callback:
            self.update_callback(states)

    def get_element_states(self) -> Dict[str, bool]:
        """
        Get the current state of all elements.

        Returns:
            Dictionary mapping element names to their boolean states
        """
        return {key: var.get() for key, var in self.element_states.items()}

    def reset_to_default(self):
        """Reset all elements to their default states."""
        defaults = {
            'axes': True,
            'axis_titles': True,
            'chart_title': True,
            'data_labels': False,
            'error_bars': True,
            'gridlines': True,
            'legend': True,
            'best_fit': True,
            'worst_fit': True,
        }

        for key, value in defaults.items():
            self.element_states[key].set(value)

        # Update the graph
        if self.update_callback:
            self.update_callback(self.get_element_states())

    def apply_changes(self):
        """Apply changes and close the window."""
        if self.update_callback:
            self.update_callback(self.get_element_states())
        self.destroy()

    def on_close(self):
        """Handle window close event."""
        self.destroy()


class ChartCustomizationMixin:
    """
    Mixin class to add chart customization functionality to GraphResultsScreen.

    Add this to your GraphResultsScreen class to enable the Chart Elements popup.
    """

    def init_chart_customization(self):
        """Initialize chart customization features."""
        self.chart_elements_popup = None
        self.chart_element_states = {
            'axes': True,
            'axis_titles': True,
            'chart_title': True,
            'data_labels': False,
            'error_bars': True,
            'gridlines': True,
            'legend': True,
            'best_fit': True,
            'worst_fit': True,
        }

    def open_chart_elements(self):
        """Open the Chart Elements customization popup."""
        if self.chart_elements_popup is not None:
            # Popup already open, bring to front
            self.chart_elements_popup.lift()
            return

        # Create new popup
        self.chart_elements_popup = ChartElementsPopup(
            self.parent,
            self.update_chart_elements
        )

        # Set initial states from current configuration
        for key, value in self.chart_element_states.items():
            if key in self.chart_elements_popup.element_states:
                self.chart_elements_popup.element_states[key].set(value)

        # Clear reference when closed
        def on_popup_close():
            self.chart_elements_popup = None

        self.chart_elements_popup.protocol("WM_DELETE_WINDOW", on_popup_close)

    def update_chart_elements(self, states: Dict[str, bool]):
        """
        Update the chart based on new element states.

        Args:
            states: Dictionary of element states from the popup
        """
        # Store new states
        self.chart_element_states = states

        # Recreate the graph with new settings
        self.refresh_graph()

    def refresh_graph(self):
        """Refresh the graph with current element states."""
        # Clear existing graph
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.get_tk_widget().destroy()

        if hasattr(self, 'figure') and self.figure:
            import matplotlib.pyplot as plt
            plt.close(self.figure)

        # Recreate graph with current settings
        self.create_graph()

    def create_graph_with_customization(self):
        """
        Modified version of create_graph that respects element states.

        This should replace or be called by your existing create_graph method.
        """
        import matplotlib.pyplot as plt
        import numpy as np

        if self.input_data is None:
            return

        states = self.chart_element_states

        # Create figure
        self.figure = plt.Figure(figsize=(8, 5), dpi=100, facecolor='white')
        ax = self.figure.add_subplot(111)

        x = self.input_data.x_values
        y = self.input_data.y_values
        x_err = self.input_data.x_error if states['error_bars'] else None
        y_err = self.input_data.y_error if states['error_bars'] else None

        # Plot data points
        ax.errorbar(
            x, y,
            xerr=x_err,
            yerr=y_err,
            fmt='o',
            color='#3b82f6',
            ecolor='#94a3b8',
            capsize=4,
            markersize=6,
            label='Data points' if states['legend'] else '',
            zorder=3
        )

        # Add data labels if enabled
        if states['data_labels']:
            for i, (xi, yi) in enumerate(zip(x, y)):
                ax.annotate(
                    f'{yi:.2f}',
                    (xi, yi),
                    textcoords="offset points",
                    xytext=(0, 8),
                    ha='center',
                    fontsize=8,
                    color='#333'
                )

        # Plot best fit line
        if states['best_fit']:
            x_line = np.linspace(x[0], x[-1], 100)
            y_best = self.best_fit_gradient * x_line + self.best_fit_intercept
            ax.plot(
                x_line, y_best,
                color='#10b981',
                linewidth=2,
                label='Best fit' if states['legend'] else '',
                zorder=2
            )

        # Plot worst fit lines
        if states['worst_fit'] and y_err is not None:
            y_worst1 = [y[0] + y_err[0], y[-1] - y_err[-1]]
            y_worst2 = [y[0] - y_err[0], y[-1] + y_err[-1]]
            x_worst = [x[0], x[-1]]

            ax.plot(
                x_worst, y_worst1,
                color='#ef4444',
                linestyle='--',
                linewidth=1.5,
                label='Worst fit (max)' if states['legend'] else '',
                zorder=1
            )
            ax.plot(
                x_worst, y_worst2,
                color='#f97316',
                linestyle='--',
                linewidth=1.5,
                label='Worst fit (min)' if states['legend'] else '',
                zorder=1
            )

        # Axis labels
        if states['axis_titles']:
            ax.set_xlabel(
                self.input_data.x_title or "X",
                fontsize=11,
                fontweight='bold'
            )
            ax.set_ylabel(
                self.input_data.y_title or "Y",
                fontsize=11,
                fontweight='bold'
            )

        # Chart title
        if states['chart_title']:
            ax.set_title(
                "Linear Regression Analysis",
                fontsize=13,
                fontweight='bold',
                pad=15
            )

        # Grid
        if states['gridlines']:
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

        # Legend
        if states['legend']:
            ax.legend(loc='best', framealpha=0.9, fontsize=9)

        # Axes
        if not states['axes']:
            ax.set_frame_on(False)
            ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)

        self.figure.tight_layout()

        # Embed in tkinter
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)


# Standalone demo
if __name__ == "__main__":
    import numpy as np

    class DemoWindow:
        def __init__(self, root):
            self.root = root
            self.root.title("Chart Elements Demo")
            self.root.geometry("600x400")

            # Simulated chart state
            self.chart_states = {
                'axes': True,
                'axis_titles': True,
                'chart_title': True,
                'data_labels': False,
                'error_bars': True,
                'gridlines': True,
                'legend': True,
                'best_fit': True,
                'worst_fit': True,
            }

            # Info label
            self.info_label = tk.Label(
                root,
                text="Click 'Open Chart Elements' to customize",
                font=("Segoe UI", 14),
                pady=20
            )
            self.info_label.pack()

            # State display
            self.state_text = tk.Text(root, height=15, width=50, font=("Courier", 10))
            self.state_text.pack(pady=10)
            self.update_state_display()

            # Open button
            tk.Button(
                root,
                text="Open Chart Elements",
                font=("Segoe UI", 12, "bold"),
                bg="#0078d4",
                fg="white",
                padx=30,
                pady=10,
                command=self.open_popup
            ).pack(pady=10)

        def open_popup(self):
            popup = ChartElementsPopup(self.root, self.on_elements_changed)

            # Set current states
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
                status = "✓ ON " if value else "✗ OFF"
                self.state_text.insert(tk.END, f"{status}  {key.replace('_', ' ').title()}\n")

    root = tk.Tk()
    app = DemoWindow(root)
    root.mainloop()