"""
GraphSettings.py

Provides an Excel-style Chart Elements popup for toggling and customising graph visual components. Implements the 'Options
to toggle/change aspects' sub-component fromSection 3.2.1 (Branch 4 — Graphs). Corresponds to the 'Settings Button' described
in Section 3.2.2 (User Interface, Screen 3a and Screen 3b).

Sepcific Requests from Stakeholder M:
  - Major/minor gridlines as independent toggles (finer control over axis readability)
  - Inline rename fields for Chart Title and Axis Titles (X and Y separately)
  - Data labels rendered as coordinate pairs (x, y) to at most 5 decimal places
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List, Optional



# Module-level defaults — imported by LinearGraphDisplay and AutomatedGraphDisplay

_DEFAULT_ELEMENT_STATES: Dict[str, bool] = {
    'axes':             True,
    'axis_titles':      True,
    'chart_title':      True,
    'data_labels':      False,
    'error_bars':       True,
    'major_gridlines':  True,
    'minor_gridlines':  False,
    'legend':           True,
    'best_fit':         True,
    'worst_fit':        True,
}

_DEFAULT_LABEL_TEXTS: Dict[str, str] = {
    'chart_title': '',   # empty string means use the screen's built-in default title
    'x_title':     '',   # empty string means use input_data.x_title
    'y_title':     '',   # empty string means use input_data.y_title
}

# Ordered checkbox rows; chart_title and axis_titles get inline Entry expansions
_ELEMENT_LABELS = [
    ('axes',            'Axes'),
    ('axis_titles',     'Axis Titles'),        # expands with X and Y rename entries
    ('chart_title',     'Chart Title'),        # expands with single title rename entry
    ('data_labels',     'Data Labels'),        # renders as (x, y) coordinates <= 5 dp
    ('error_bars',      'Error Bars'),
    ('major_gridlines', 'Major Gridlines'),
    ('minor_gridlines', 'Minor Gridlines'),
    ('legend',          'Legend'),
    ('best_fit',        'Best Fit Line'),
    ('worst_fit',       'Worst Fit Lines'),    # omitted on Screen 3b via show_worst_fit=False
]

# Keys whose checkbox rows also contain Entry widgets
_KEYS_WITH_ENTRIES = {'axis_titles', 'chart_title'}



# Helper
def _fmt_coord(v: float) -> str:
    """
    Format a float to at most 3 decimal places, stripping trailing zeros.

    e.g. 1.5000 -> '1.5',  2.0 -> '2',  0.123 -> '0.123'
    Used for data-label coordinate annotations to satisfy a 'max 5 dp' standard.
    """
    return f"{v:.5f}".rstrip('0').rstrip('.')


# ChartElementsPopup

class ChartElementsPopup(tk.Toplevel):
    """
    Excel-style chart customisation popup with checkboxes and inline label editors.

    New in this version:
      - Major and minor gridlines are separate independent toggles.
      - Chart Title and Axis Titles rows include rename Entry fields.
      - The update_callback receives (states, label_texts) so both visibility
        and text overrides flow to the graph on every change.
      - show_worst_fit=False omits the Worst Fit Lines row for Screen 3b.
    """

    def __init__(
        self,
        parent,
        update_callback: Callable,
        show_worst_fit: bool = True,
        initial_labels: Optional[Dict[str, str]] = None,
    ):
        """
        Args:
            parent:           Parent Tk window.
            update_callback:  Called as callback(states, label_texts) on any change.
            show_worst_fit:   Include the Worst Fit Lines toggle (Screen 3a only).
            initial_labels:   Pre-populate rename entries; keys: chart_title, x_title, y_title.
        """
        super().__init__(parent)
        self.update_callback = update_callback
        self.show_worst_fit  = show_worst_fit

        self.title("Chart Elements")
        self.resizable(False, True)
        self.minsize(320, 460)
        popup_height = 660 if show_worst_fit else 630
        self.geometry(f"320x{popup_height}")
        self.configure(bg="#f0f0f0")
        self.transient(parent)
        self.attributes('-topmost', True)

        self._position_window(parent)

        # Boolean toggle BooleanVars
        self.element_states: Dict[str, tk.BooleanVar] = {
            k: tk.BooleanVar(value=v) for k, v in _DEFAULT_ELEMENT_STATES.items()
        }

        # Editable title StringVars; pre-populated from initial_labels if provided
        init = initial_labels or {}
        self.label_texts: Dict[str, tk.StringVar] = {
            'chart_title': tk.StringVar(value=init.get('chart_title', '')),
            'x_title':     tk.StringVar(value=init.get('x_title',     '')),
            'y_title':     tk.StringVar(value=init.get('y_title',     '')),
        }

        # Entry widget references keyed by checkbox key, for enable/disable on toggle
        self._entry_widgets: Dict[str, List[tk.Entry]] = {}

        self.create_ui()
        self.protocol("WM_DELETE_WINDOW", self.destroy)


    # Positioning

    def _position_window(self, parent):
        """Place popup near the top-right corner of the parent window."""
        self.update_idletasks()
        x = parent.winfo_x() + parent.winfo_width() - 340
        y = parent.winfo_y() + 80
        self.geometry(f"+{x}+{y}")


    # UI construction

    def create_ui(self):
        """Build header, element rows (with expandable rename sections), separator, and buttons."""
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
                  command=self.reset_to_default).grid(row=0, column=0, sticky="ew",
                                                       padx=(5, 3), pady=2)
        tk.Button(btn_frame, text="Apply", font=("Segoe UI", 9, "bold"),
                  bg="#0078d4", fg="white", relief="flat", cursor="hand2",
                  command=self.apply_changes).grid(row=0, column=1, sticky="ew",
                                                    padx=(3, 5), pady=2)

    def create_checkbox_item(self, parent, key: str, label: str):
        """Standard toggle row with hover highlight for non-rename elements."""
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

        def on_enter(e):
            item_frame.config(bg="#e5f3ff")
            checkbox.config(bg="#e5f3ff")

        def on_leave(e):
            item_frame.config(bg="white")
            checkbox.config(bg="white")

        for w in (item_frame, checkbox):
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

    def _create_chart_title_item(self, parent, key: str, label: str):
        """
        Checkbox row + single Entry for renaming the chart title.
        Entry is enabled/disabled to match the checkbox state.
        """
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

        entry_row = tk.Frame(outer, bg="white")
        entry_row.pack(fill="x", padx=(30, 8), pady=(0, 5))
        tk.Label(entry_row, text="Title:", font=("Segoe UI", 8),
                 bg="white", fg="#64748b").pack(side="left", padx=(0, 4))
        entry = tk.Entry(entry_row, textvariable=self.label_texts['chart_title'],
                         font=("Segoe UI", 9), relief="solid", bd=1)
        entry.pack(side="left", fill="x", expand=True)

        enabled = self.element_states[key].get()
        entry.config(state='normal' if enabled else 'disabled',
                     bg='white'   if enabled else '#f0f0f0')

        self._entry_widgets[key] = [entry]
        entry.bind("<FocusOut>", lambda e: self._fire_callback())
        entry.bind("<Return>",   lambda e: self._fire_callback())

        def on_enter(e):
            cb_row.config(bg="#e5f3ff")
            checkbox.config(bg="#e5f3ff")

        def on_leave(e):
            cb_row.config(bg="white")
            checkbox.config(bg="white")

        for w in (cb_row, checkbox):
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

    def _create_axis_titles_item(self, parent, key: str, label: str):
        """
        Checkbox row + two Entry rows for renaming X and Y axis titles independently.
        Both entries are enabled/disabled together with the checkbox.
        """
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

        grid = tk.Frame(outer, bg="white")
        grid.pack(fill="x", padx=(30, 8), pady=(0, 5))
        grid.columnconfigure(1, weight=1)

        entries = []
        for row_idx, (var_key, lbl_text) in enumerate([('x_title', 'X:'), ('y_title', 'Y:')]):
            tk.Label(grid, text=lbl_text, font=("Segoe UI", 8), bg="white",
                     fg="#64748b", width=2).grid(row=row_idx, column=0, sticky="w", pady=2)
            ent = tk.Entry(grid, textvariable=self.label_texts[var_key],
                           font=("Segoe UI", 9), relief="solid", bd=1)
            ent.grid(row=row_idx, column=1, sticky="ew", padx=(4, 0), pady=2)
            enabled = self.element_states[key].get()
            ent.config(state='normal' if enabled else 'disabled',
                       bg='white'   if enabled else '#f0f0f0')
            ent.bind("<FocusOut>", lambda e: self._fire_callback())
            ent.bind("<Return>",   lambda e: self._fire_callback())
            entries.append(ent)

        self._entry_widgets[key] = entries

        def on_enter(e):
            cb_row.config(bg="#e5f3ff")
            checkbox.config(bg="#e5f3ff")

        def on_leave(e):
            cb_row.config(bg="white")
            checkbox.config(bg="white")

        for w in (cb_row, checkbox):
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)


    # Event handlers

    def _on_toggle(self, key: str):
        """
        Sync Entry enable state with checkbox, then fire the update callback.
        For keys without Entry widgets this is a straightforward callback trigger.
        """
        enabled = self.element_states[key].get()
        for w in self._entry_widgets.get(key, []):
            w.config(state='normal' if enabled else 'disabled',
                     bg='white'   if enabled else '#f0f0f0')
        self._fire_callback()

    def _fire_callback(self):
        """Dispatch current states and label texts to the update callback."""
        if self.update_callback:
            self.update_callback(self.get_element_states(), self.get_label_texts())

    def on_element_toggle(self, key: str):
        """Public alias for _on_toggle — retained for backwards compatibility."""
        self._on_toggle(key)


    # State accessors
    def get_element_states(self) -> Dict[str, bool]:
        """Return all boolean toggle states as a plain dict."""
        return {k: v.get() for k, v in self.element_states.items()}

    def get_label_texts(self) -> Dict[str, str]:
        """Return all label text overrides as a plain dict."""
        return {k: v.get() for k, v in self.label_texts.items()}


    # Button actions
    def reset_to_default(self):
        """
        Reset all toggles to defaults, clear rename fields, re-sync Entry states, and fire the callback to redraw the
        graph immediately.
        """
        for key, value in _DEFAULT_ELEMENT_STATES.items():
            self.element_states[key].set(value)
        for sv in self.label_texts.values():
            sv.set('')
        for key in _KEYS_WITH_ENTRIES:
            enabled = self.element_states[key].get()
            for w in self._entry_widgets.get(key, []):
                w.config(state='normal' if enabled else 'disabled',
                         bg='white'   if enabled else '#f0f0f0')
        self._fire_callback()

    def apply_changes(self):
        """Fire callback with current state then close the popup."""
        self._fire_callback()
        self.destroy()


# ChartCustomisationMixin


class ChartCustomisationMixin:
    """
    Mixin that adds Chart Elements popup management to a graph results screen.

    Stores both toggle states (chart_element_states) and text overrides (chart_label_texts) so any create_graph()
    implementation can consult both.
    """

    def init_chart_customisation(self):
        """Initialise mixin state. Must be called during the screen's __init__."""
        self.chart_elements_popup  = None
        self.chart_element_states  = dict(_DEFAULT_ELEMENT_STATES)
        self.chart_label_texts     = dict(_DEFAULT_LABEL_TEXTS)

    def open_chart_elements(self):
        """Open or lift the Chart Elements popup, passing current label overrides."""
        if self.chart_elements_popup is not None:
            self.chart_elements_popup.lift()
            return

        input_data = getattr(self, 'input_data', None)
        initial_labels = {
            'chart_title': self.chart_label_texts.get('chart_title', ''),
            'x_title':     self.chart_label_texts.get('x_title', '') or
                           (input_data.x_title if input_data else ''),
            'y_title':     self.chart_label_texts.get('y_title', '') or
                           (input_data.y_title if input_data else ''),
        }
        self.chart_elements_popup = ChartElementsPopup(
            self.parent, self.update_chart_elements,
            initial_labels=initial_labels,
        )
        for k, v in self.chart_element_states.items():
            if k in self.chart_elements_popup.element_states:
                self.chart_elements_popup.element_states[k].set(v)

        def _on_close():
            self.chart_elements_popup.destroy()
            self.chart_elements_popup = None

        self.chart_elements_popup.protocol("WM_DELETE_WINDOW", _on_close)

    def update_chart_elements(self, states: Dict[str, bool],
                               label_texts: Optional[Dict[str, str]] = None):
        """Store updated states and label texts, then redraw the graph."""
        self.chart_element_states = states
        if label_texts is not None:
            self.chart_label_texts = label_texts
        self.refresh_graph()

    def refresh_graph(self):
        """Destroy existing canvas/figure and call create_graph() to redraw."""
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.get_tk_widget().destroy()
        if hasattr(self, 'figure') and self.figure:
            import matplotlib.pyplot as plt
            plt.close(self.figure)
        self.create_graph()

    def apply_chart_customisation(self, ax, x, y, states: Dict[str, bool],
                                    default_chart_title: str = ""):
        """
        Apply all chart customisation to an existing Matplotlib Axes object.

        Called at the end of create_graph() in both display screens after all data series and fit curves have been added.

        Handles:
          - Data labels as '(x, y)' coordinate pairs, trailing zeros stripped, max 5 dp
          - Major gridlines (dashed, subtle) and minor gridlines (dotted, very faint)
          - Renamed Chart Title and Axis Titles from chart_label_texts
          - Legend and axis spine/tick toggling
        """
        if states.get('data_labels'):
            for xi, yi in zip(x, y):
                ax.annotate(
                    f'({_fmt_coord(xi)}, {_fmt_coord(yi)})',
                    (xi, yi), textcoords="offset points", xytext=(0, 10),
                    ha='center', fontsize=7, color='#334155',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                              alpha=0.75, edgecolor='none'),
                )

        if states.get('major_gridlines'):
            ax.grid(True, which='major', alpha=0.35, linestyle='--', linewidth=0.6)
        if states.get('minor_gridlines'):
            ax.minorticks_on()
            ax.grid(True, which='minor', alpha=0.18, linestyle=':', linewidth=0.4)

        if states.get('chart_title'):
            title_text = self.chart_label_texts.get('chart_title') or default_chart_title
            ax.set_title(title_text, fontsize=13, fontweight='bold', pad=15)

        if states.get('axis_titles'):
            input_data = getattr(self, 'input_data', None)
            x_label = (self.chart_label_texts.get('x_title')
                       or (input_data.x_title if input_data else '') or "X")
            y_label = (self.chart_label_texts.get('y_title')
                       or (input_data.y_title if input_data else '') or "Y")
            ax.set_xlabel(x_label, fontsize=11, fontweight='bold')
            ax.set_ylabel(y_label, fontsize=11, fontweight='bold')

        if states.get('legend'):
            ax.legend(loc='best', framealpha=0.9, fontsize=9)

        if not states.get('axes'):
            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)



# Standalone demo / white-box test runner


if __name__ == "__main__":
    class DemoWindow:
        """Standalone test harness for ChartElementsPopup."""
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
                      bg="#0078d4", fg="white", padx=30, pady=10,
                      command=self.open_popup).pack(pady=10)

        def open_popup(self):
            popup = ChartElementsPopup(self.root, self.on_changed,
                                       initial_labels=self.chart_labels)
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