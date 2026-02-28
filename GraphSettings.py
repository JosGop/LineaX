"""GraphSettings.py — Chart Elements popup for toggling and customising graph visual components."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List, Optional

_DEFAULT_ELEMENT_STATES: Dict[str, bool] = {
    'axes': True, 'axis_titles': True, 'chart_title': True,
    'data_labels': False, 'error_bars': True, 'major_gridlines': True,
    'minor_gridlines': False, 'legend': True, 'best_fit': True, 'worst_fit': True,
}

_DEFAULT_LABEL_TEXTS: Dict[str, str] = {
    'chart_title': '', 'x_title': '', 'y_title': '',
}

_ELEMENT_LABELS = [
    ('axes', 'Axes'), ('axis_titles', 'Axis Titles'), ('chart_title', 'Chart Title'),
    ('data_labels', 'Data Labels'), ('error_bars', 'Error Bars'),
    ('major_gridlines', 'Major Gridlines'), ('minor_gridlines', 'Minor Gridlines'),
    ('legend', 'Legend'), ('best_fit', 'Best Fit Line'), ('worst_fit', 'Worst Fit Lines'),
]

_KEYS_WITH_ENTRIES = {'axis_titles', 'chart_title'}


def _fmt_coord(v: float) -> str:
    """Format a float to at most 5 decimal places, stripping trailing zeros."""
    return f"{v:.5f}".rstrip('0').rstrip('.')


class ChartElementsPopup(tk.Toplevel):
    """Excel-style chart customisation popup with checkboxes and inline label editors."""

    def __init__(
        self,
        parent,
        update_callback: Callable,
        show_worst_fit: bool = True,
        initial_labels: Optional[Dict[str, str]] = None,
    ):
        super().__init__(parent)
        self.update_callback = update_callback
        self.show_worst_fit = show_worst_fit
        self.title("Chart Elements")
        self.resizable(False, True)
        self.minsize(320, 460)
        self.geometry(f"320x{660 if show_worst_fit else 630}")
        self.configure(bg="#f0f0f0")
        self.transient(parent)
        self.attributes('-topmost', True)
        self._position_window(parent)

        self.element_states: Dict[str, tk.BooleanVar] = {
            k: tk.BooleanVar(value=v) for k, v in _DEFAULT_ELEMENT_STATES.items()
        }
        init = initial_labels or {}
        self.label_texts: Dict[str, tk.StringVar] = {
            'chart_title': tk.StringVar(value=init.get('chart_title', '')),
            'x_title':     tk.StringVar(value=init.get('x_title', '')),
            'y_title':     tk.StringVar(value=init.get('y_title', '')),
        }
        self._entry_widgets: Dict[str, List[tk.Entry]] = {}
        self.create_ui()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _position_window(self, parent):
        self.update_idletasks()
        x = parent.winfo_x() + parent.winfo_width() - 340
        y = parent.winfo_y() + 80
        self.geometry(f"+{x}+{y}")

    def create_ui(self):
        """Build the header, element rows and action buttons."""
        header = tk.Frame(self, bg="#0078d4", height=35)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="Chart Elements", font=("Segoe UI", 11, "bold"),
                 bg="#0078d4", fg="white").pack(side="left", padx=10, pady=8)

        content = tk.Frame(self, bg="white", padx=5, pady=8)
        content.pack(fill="both", expand=True)

        for key, label in _ELEMENT_LABELS:
            if key == 'worst_fit' and not self.show_worst_fit:
                continue
            if key == 'axis_titles':
                self._create_axis_titles_item(content, key, label)
            elif key == 'chart_title':
                self._create_chart_title_item(content, key, label)
            else:
                self.create_checkbox_item(content, key, label)

        ttk.Separator(content, orient="horizontal").pack(fill="x", pady=8)
        btn_frame = tk.Frame(content, bg="white")
        btn_frame.pack(fill="x", pady=4)
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        tk.Button(btn_frame, text="Reset to Default", font=("Segoe UI", 9),
                  bg="#f0f0f0", fg="#333", relief="solid", bd=1, cursor="hand2",
                  command=self.reset_to_default).grid(row=0, column=0, sticky="ew", padx=(5, 3), pady=2)
        tk.Button(btn_frame, text="Apply", font=("Segoe UI", 9, "bold"),
                  bg="#0078d4", fg="white", relief="flat", cursor="hand2",
                  command=self.apply_changes).grid(row=0, column=1, sticky="ew", padx=(3, 5), pady=2)

    def _hover(self, item_frame, checkbox):
        """Bind hover highlight events to a row frame and its checkbox."""
        item_frame.bind("<Enter>", lambda e: [item_frame.config(bg="#e5f3ff"), checkbox.config(bg="#e5f3ff")])
        item_frame.bind("<Leave>", lambda e: [item_frame.config(bg="white"), checkbox.config(bg="white")])
        checkbox.bind("<Enter>", lambda e: [item_frame.config(bg="#e5f3ff"), checkbox.config(bg="#e5f3ff")])
        checkbox.bind("<Leave>", lambda e: [item_frame.config(bg="white"), checkbox.config(bg="white")])

    def create_checkbox_item(self, parent, key: str, label: str):
        """Standard toggle row with hover highlight."""
        item_frame = tk.Frame(parent, bg="white", height=32)
        item_frame.pack(fill="x", pady=1)
        item_frame.pack_propagate(False)
        checkbox = tk.Checkbutton(
            item_frame, text=label, variable=self.element_states[key],
            font=("Segoe UI", 10), bg="white", activebackground="#e5f3ff",
            selectcolor="white", relief="flat", cursor="hand2",
            command=lambda k=key: self._on_toggle(k),
        )
        checkbox.pack(side="left", padx=10, pady=5, fill="both", expand=True)
        self._hover(item_frame, checkbox)

    def _entry_row(self, parent, key: str, enabled: bool):
        """Return a configured Entry widget, registering it in _entry_widgets."""
        entry = tk.Entry(parent, font=("Segoe UI", 9), relief="solid", bd=1)
        entry.config(state='normal' if enabled else 'disabled',
                     bg='white' if enabled else '#f0f0f0')
        entry.bind("<FocusOut>", lambda e: self._fire_callback())
        entry.bind("<Return>", lambda e: self._fire_callback())
        self._entry_widgets.setdefault(key, []).append(entry)
        return entry

    def _create_chart_title_item(self, parent, key: str, label: str):
        """Checkbox row with a single Entry for renaming the chart title."""
        outer = tk.Frame(parent, bg="white")
        outer.pack(fill="x", pady=1)
        cb_row = tk.Frame(outer, bg="white", height=32)
        cb_row.pack(fill="x")
        cb_row.pack_propagate(False)
        checkbox = tk.Checkbutton(
            cb_row, text=label, variable=self.element_states[key],
            font=("Segoe UI", 10), bg="white", activebackground="#e5f3ff",
            selectcolor="white", relief="flat", cursor="hand2",
            command=lambda k=key: self._on_toggle(k),
        )
        checkbox.pack(side="left", padx=10, pady=5, fill="both", expand=True)
        self._hover(cb_row, checkbox)

        entry_row = tk.Frame(outer, bg="white")
        entry_row.pack(fill="x", padx=(30, 8), pady=(0, 5))
        tk.Label(entry_row, text="Title:", font=("Segoe UI", 8), bg="white", fg="#64748b").pack(side="left", padx=(0, 4))
        entry = self._entry_row(entry_row, key, self.element_states[key].get())
        entry.config(textvariable=self.label_texts['chart_title'])
        entry.pack(side="left", fill="x", expand=True)

    def _create_axis_titles_item(self, parent, key: str, label: str):
        """Checkbox row with two Entries for renaming X and Y axis titles."""
        outer = tk.Frame(parent, bg="white")
        outer.pack(fill="x", pady=1)
        cb_row = tk.Frame(outer, bg="white", height=32)
        cb_row.pack(fill="x")
        cb_row.pack_propagate(False)
        checkbox = tk.Checkbutton(
            cb_row, text=label, variable=self.element_states[key],
            font=("Segoe UI", 10), bg="white", activebackground="#e5f3ff",
            selectcolor="white", relief="flat", cursor="hand2",
            command=lambda k=key: self._on_toggle(k),
        )
        checkbox.pack(side="left", padx=10, pady=5, fill="both", expand=True)
        self._hover(cb_row, checkbox)

        grid = tk.Frame(outer, bg="white")
        grid.pack(fill="x", padx=(30, 8), pady=(0, 5))
        grid.columnconfigure(1, weight=1)
        enabled = self.element_states[key].get()
        for row_idx, (var_key, lbl_text) in enumerate([('x_title', 'X:'), ('y_title', 'Y:')]):
            tk.Label(grid, text=lbl_text, font=("Segoe UI", 8), bg="white",
                     fg="#64748b", width=2).grid(row=row_idx, column=0, sticky="w", pady=2)
            ent = self._entry_row(grid, key, enabled)
            ent.config(textvariable=self.label_texts[var_key])
            ent.grid(row=row_idx, column=1, sticky="ew", padx=(4, 0), pady=2)

    def _on_toggle(self, key: str):
        """Sync Entry enable state with checkbox, then fire the update callback."""
        enabled = self.element_states[key].get()
        for w in self._entry_widgets.get(key, []):
            w.config(state='normal' if enabled else 'disabled',
                     bg='white' if enabled else '#f0f0f0')
        self._fire_callback()

    def _fire_callback(self):
        if self.update_callback:
            self.update_callback(self.get_element_states(), self.get_label_texts())

    def on_element_toggle(self, key: str):
        """Public alias for _on_toggle."""
        self._on_toggle(key)

    def get_element_states(self) -> Dict[str, bool]:
        return {k: v.get() for k, v in self.element_states.items()}

    def get_label_texts(self) -> Dict[str, str]:
        return {k: v.get() for k, v in self.label_texts.items()}

    def reset_to_default(self):
        """Reset all toggles to defaults, clear rename fields and redraw."""
        for key, value in _DEFAULT_ELEMENT_STATES.items():
            self.element_states[key].set(value)
        for sv in self.label_texts.values():
            sv.set('')
        for key in _KEYS_WITH_ENTRIES:
            enabled = self.element_states[key].get()
            for w in self._entry_widgets.get(key, []):
                w.config(state='normal' if enabled else 'disabled',
                         bg='white' if enabled else '#f0f0f0')
        self._fire_callback()

    def apply_changes(self):
        self._fire_callback()
        self.destroy()


class ChartCustomisationMixin:
    """Mixin that adds Chart Elements popup management to a graph results screen."""

    def init_chart_customisation(self):
        self.chart_elements_popup = None
        self.chart_element_states = dict(_DEFAULT_ELEMENT_STATES)
        self.chart_label_texts = dict(_DEFAULT_LABEL_TEXTS)

    def open_chart_elements(self):
        if self.chart_elements_popup is not None:
            self.chart_elements_popup.lift()
            return
        input_data = getattr(self, 'input_data', None)
        initial_labels = {
            'chart_title': self.chart_label_texts.get('chart_title', ''),
            'x_title': self.chart_label_texts.get('x_title', '') or (input_data.x_title if input_data else ''),
            'y_title': self.chart_label_texts.get('y_title', '') or (input_data.y_title if input_data else ''),
        }
        self.chart_elements_popup = ChartElementsPopup(self.parent, self.update_chart_elements,
                                                       initial_labels=initial_labels)
        for k, v in self.chart_element_states.items():
            if k in self.chart_elements_popup.element_states:
                self.chart_elements_popup.element_states[k].set(v)

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
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.get_tk_widget().destroy()
        if hasattr(self, 'figure') and self.figure:
            import matplotlib.pyplot as plt
            plt.close(self.figure)
        self.create_graph()

    def apply_chart_customisation(self, ax, x, y, states: Dict[str, bool], default_chart_title: str = ""):
        """Apply all chart customisation to an existing Matplotlib Axes object."""
        if states.get('data_labels'):
            for xi, yi in zip(x, y):
                ax.annotate(
                    f'({_fmt_coord(xi)}, {_fmt_coord(yi)})',
                    (xi, yi), textcoords="offset points", xytext=(0, 10),
                    ha='center', fontsize=7, color='#334155',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.75, edgecolor='none'),
                )
        if states.get('major_gridlines'):
            ax.grid(True, which='major', alpha=0.35, linestyle='--', linewidth=0.6)
        if states.get('minor_gridlines'):
            ax.minorticks_on()
            ax.grid(True, which='minor', alpha=0.18, linestyle=':', linewidth=0.4)
        if states.get('chart_title'):
            ax.set_title(self.chart_label_texts.get('chart_title') or default_chart_title,
                         fontsize=13, fontweight='bold', pad=15)
        if states.get('axis_titles'):
            input_data = getattr(self, 'input_data', None)
            x_label = self.chart_label_texts.get('x_title') or (input_data.x_title if input_data else '') or "X"
            y_label = self.chart_label_texts.get('y_title') or (input_data.y_title if input_data else '') or "Y"
            ax.set_xlabel(x_label, fontsize=11, fontweight='bold')
            ax.set_ylabel(y_label, fontsize=11, fontweight='bold')
        if states.get('legend'):
            ax.legend(loc='best', framealpha=0.9, fontsize=9)
        if not states.get('axes'):
            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)


if __name__ == "__main__":
    class DemoWindow:
        def __init__(self, root):
            self.root = root
            self.root.title("Chart Elements Demo")
            self.root.geometry("600x420")
            self.chart_states = dict(_DEFAULT_ELEMENT_STATES)
            self.chart_labels = dict(_DEFAULT_LABEL_TEXTS)
            tk.Label(root, text="Click 'Open Chart Elements' to customise",
                     font=("Segoe UI", 14), pady=20).pack()
            self.state_text = tk.Text(root, height=16, width=55, font=("Courier", 9))
            self.state_text.pack(pady=10)
            self._refresh_display()
            tk.Button(root, text="Open Chart Elements", font=("Segoe UI", 12, "bold"),
                      bg="#0078d4", fg="white", padx=30, pady=10, command=self.open_popup).pack(pady=10)

        def open_popup(self):
            popup = ChartElementsPopup(self.root, self.on_changed, initial_labels=self.chart_labels)
            for key, value in self.chart_states.items():
                if key in popup.element_states:
                    popup.element_states[key].set(value)

        def on_changed(self, states, label_texts):
            self.chart_states = states
            self.chart_labels = label_texts
            self._refresh_display()

        def _refresh_display(self):
            self.state_text.delete(1.0, tk.END)
            self.state_text.insert(tk.END, "Toggles:\n")
            for k, v in self.chart_states.items():
                self.state_text.insert(tk.END, f"  {'on ' if v else 'off'}  {k}\n")
            self.state_text.insert(tk.END, "\nLabel overrides:\n")
            for k, v in self.chart_labels.items():
                self.state_text.insert(tk.END, f"  {k}: {repr(v)}\n")

    root = tk.Tk()
    DemoWindow(root)
    root.mainloop()

