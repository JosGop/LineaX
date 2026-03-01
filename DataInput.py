"""DataInput.py — Screen 1 (Data Input Screen) for LineaX.

Implements the two data import pathways described in Section 3.2.1:
  Branch 1 — Import CSV or Excel file, map columns, extract InputData.
  Branch 2 — Manual spreadsheet entry, validate cell values, build InputData.

The screen satisfies success criteria 1.1.2 (file import), 1.1.3 (manual entry)
and 1.1.4 (input validation with visual feedback).

Once the user clicks 'Next', valid data is stored in ScreenManager and the
application navigates to AnalysisMethodScreen (Screen 2).
"""

# tkinter is Python's built-in GUI toolkit used for all widgets on Screen 1.
import tkinter as tk

# ttk provides themed Tk widgets; Combobox (dropdown) and Progressbar are used here.
# filedialog opens the OS file chooser for CSV/Excel selection.
# messagebox displays modal info/warning/error dialogs to the user.
from tkinter import ttk, filedialog, messagebox

# pandas is the data analysis library used to read CSV and Excel files into
# DataFrames before the user maps columns to x, y and error axes.
import pandas as pd

# InputData is the core data container populated here and passed to all downstream screens.
from LineaX_Classes import InputData

# AnalysisMethodScreen is Screen 2; the navigation target after successful data validation.
from AnalysisMethod import AnalysisMethodScreen

# ScreenManager manages screen transitions; make_scrollable wraps panels in a scrollable canvas.
from ManagingScreens import make_scrollable, ScreenManager

# Column header labels for the manual entry grid (Section 3.2.1, Branch 2).
_MANUAL_HEADERS = ["X / Independent", "X Error", "Y / Dependent", "Y Error"]


def _btn(parent, text, command, bg="#0f172a", fg="white", font_size=10, bold=True, **kwargs) -> tk.Button:
    """Factory for consistently styled flat buttons used throughout Screen 1.

    Centralises visual styling (relief='flat', cursor='hand2') so all action
    buttons on the screen share a uniform appearance, satisfying the visual
    consistency requirement in Section 3.1.4.
    """
    weight = "bold" if bold else "normal"
    return tk.Button(parent, text=text, font=("Segoe UI", font_size, weight),
                     bg=bg, fg=fg, relief="flat", cursor="hand2", command=command, **kwargs)


class DataInputScreen(tk.Frame):
    """Screen 1: data import (Branch 1) and manual entry (Branch 2).

    Inherits from tk.Frame so it can be packed into the root window by ScreenManager.
    The two panels are placed side-by-side in a grid layout; grid_columnconfigure
    with weight=1 on both columns gives each panel equal horizontal space.
    """

    def __init__(self, parent, manager):
        super().__init__(parent, bg="#f5f6f8", padx=20, pady=15)
        self.manager = manager
        self.parent = parent
        self.df = None        # pandas DataFrame loaded from the selected file
        self.filepath = None  # path of the loaded file, used to choose read_csv vs read_excel
        self.input_data = None
        self.create_layout()

    def create_layout(self):
        """Build the top-level layout: header bar, title, two-column panel, bottom buttons.

        grid_rowconfigure / grid_columnconfigure on inner set weight=1 so both
        panels expand equally when the window is resized (Section 3.1.4, usability).
        """
        header = tk.Frame(self, bg="white", height=50)
        header.pack(fill="x", pady=(0, 15))
        header.pack_propagate(False)
        tk.Label(header, text="LineaX", font=("Segoe UI", 14, "bold"),
                 bg="white", fg="#0f172a").pack(side="left", padx=15, pady=10)
        tk.Label(self, text="Import Your Data", font=("Segoe UI", 26, "bold"),
                 bg="#f5f6f8", fg="#0f172a").pack(pady=(10, 25))

        container = tk.Frame(self, bg="#d1d5db")
        container.pack(fill="both", expand=True, padx=10, pady=10)
        inner = tk.Frame(container, bg="#d1d5db", padx=15, pady=15)
        inner.pack(fill="both", expand=True)
        inner.grid_rowconfigure(0, weight=1)
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(1, weight=1)

        self.create_import_panel(inner)
        self.create_manual_panel(inner)

        bottom = tk.Frame(self, bg="#f5f6f8")
        bottom.pack(fill="x", pady=(15, 0))
        _btn(bottom, "Next ->", self.proceed_to_next, padx=30, pady=10).pack(side="right", padx=10)
        _btn(bottom, "Clear All", self.clear_all, bg="#e5e7eb", fg="#334155",
             bold=True, padx=20, pady=10).pack(side="right", padx=10)

    def create_import_panel(self, parent):
        """Build the left panel for Branch 1 (Import CSV/Excel).

        make_scrollable wraps the panel in a tk.Canvas so content remains accessible
        if the window is too short. ttk.Progressbar provides visual feedback during
        file loading (Section 3.1.4, usability). ttk.Combobox dropdowns let the user
        map file columns to x, y and optional error axes (success criterion 1.1.2).
        """
        self.import_panel_container, self.import_panel, _, _ = make_scrollable(
            parent, row=0, column=0, padx=(0, 10), bg="white", panel_kwargs={"padx": 20, "pady": 20}
        )
        panel = self.import_panel
        tk.Label(panel, text="Import Excel/CSV Files", font=("Segoe UI", 13, "bold"),
                 bg="white", fg="#0f172a").pack(anchor="w", pady=(0, 15))

        # Progress bar: shown during file loading, hidden after 300 ms via parent.after().
        self.progress_frame = tk.Frame(panel, bg="white")
        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(self.progress_frame, mode="determinate",
                                        length=320, maximum=100, variable=self.progress_var)
        self.progress_label = tk.Label(self.progress_frame, text="0%",
                                       font=("Segoe UI", 9), bg="white", fg="#475569")
        self.progress.pack()
        self.progress_label.pack(pady=(2, 0))

        # Drop zone frame: clicking anywhere within it triggers select_file().
        drop_frame = tk.Frame(panel, bg="white")
        drop_frame.pack(pady=15)
        self.drop_zone = tk.Frame(drop_frame, bg="#f8fafc", relief="solid", bd=2,
                                  highlightbackground="#cbd5e1", highlightthickness=2)
        self.drop_zone.pack()
        drop_content = tk.Frame(self.drop_zone, bg="#f8fafc", padx=40, pady=40)
        drop_content.pack()
        tk.Label(drop_content, text="📂", font=("Segoe UI", 32), bg="#f8fafc").pack()
        self.drop_label = tk.Label(drop_content, text="Drop file or click to browse",
                                   font=("Segoe UI", 10), bg="#f8fafc", fg="#64748b")
        self.drop_label.pack(pady=(10, 0))
        self.remove_file_btn = tk.Button(drop_content, text="X", font=("Segoe UI", 10, "bold"),
                                         fg="#ef4444", bg="#f8fafc", relief="flat",
                                         cursor="hand2", command=self.remove_imported_file)
        self.remove_file_btn.pack(pady=(5, 0))
        self.remove_file_btn.pack_forget()   # hidden until a file is loaded

        # Bind click events on all three sub-widgets of the drop zone to select_file().
        for widget in (self.drop_zone, drop_content, self.drop_label):
            widget.bind("<Button-1>", lambda e: self.select_file())
        _btn(panel, "Select File", self.select_file, padx=20, pady=8).pack(pady=10)

        # Column mapping section: four ttk.Combobox widgets (state='readonly' prevents
        # free-text entry; the user can only pick from the loaded file's column names).
        map_frame = tk.LabelFrame(panel, text=" Map Your Columns:", font=("Segoe UI", 10, "bold"),
                                  bg="white", fg="#475569", padx=15, pady=15)
        map_frame.pack(fill="x", pady=15)
        ttk.Style().configure("TCombobox", padding=5)
        self.x_col     = ttk.Combobox(map_frame, state="readonly", width=25)
        self.y_col     = ttk.Combobox(map_frame, state="readonly", width=25)
        self.x_err_col = ttk.Combobox(map_frame, state="readonly", values=["None"], width=25)
        self.y_err_col = ttk.Combobox(map_frame, state="readonly", values=["None"], width=25)
        self.x_err_col.set("None")
        self.y_err_col.set("None")
        for label_text, combo in [("X Values:", self.x_col), ("Y Values:", self.y_col),
                                   ("X Uncertainty:", self.x_err_col), ("Y Uncertainty:", self.y_err_col)]:
            row = tk.Frame(map_frame, bg="white")
            row.pack(fill="x", pady=5)
            tk.Label(row, text=label_text, font=("Segoe UI", 9), bg="white", fg="#334155").pack(anchor="w")
            combo.pack(fill="x", pady=(2, 0))
        tk.Label(map_frame, text="* Uncertainties are optional", font=("Segoe UI", 8, "italic"),
                 fg="#94a3b8", bg="white").pack(anchor="w", pady=(8, 0))

    def select_file(self):
        """Open the OS file chooser and load the selected CSV or Excel file.

        filedialog.askopenfilename opens the native OS file picker, filtered to
        CSV and Excel types, returning the chosen path or empty string if cancelled.
        pd.read_csv / pd.read_excel (pandas) parse the file into a DataFrame; the
        column names are then used to populate the four Combobox dropdowns.
        parent.after(300, ...) schedules the progress bar to be hidden 300 ms after
        loading completes, giving the user brief visual feedback of completion.
        Satisfies success criterion 1.1.2.
        """
        path = filedialog.askopenfilename(
            title="Select Data File",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if not path:
            return
        self.filepath = path
        self._set_progress(0)
        self.progress_frame.pack(pady=5, before=self.drop_zone.master)
        self.parent.update()
        try:
            self._set_progress(30)
            # pandas automatically detects the file format from the extension.
            self.df = pd.read_csv(path) if path.endswith(".csv") else pd.read_excel(path)
            self._set_progress(70)
            self.drop_label.config(text=f"✓ {path.split('/')[-1]}", fg="#10b981", font=("Segoe UI", 10, "bold"))
            self.populate_columns()
            self._set_progress(100)
            # Disable manual entry panel while a file is loaded to prevent conflicting input.
            self.set_panel_state(self.manual_panel, enabled=False)
            self.remove_file_btn.place(relx=1, rely=0, anchor="ne")
        except Exception as e:
            self.df = None
            self.filepath = None
            messagebox.showerror("File Error", str(e))
        finally:
            # Hide progress bar after a short delay regardless of success or failure.
            self.parent.after(300, self.progress_frame.pack_forget)

    def _set_progress(self, value: int):
        """Update the progress bar value and label text.

        self.parent.update() forces an immediate Tkinter redraw so the progress
        bar appears to animate during sequential calls within select_file().
        """
        self.progress_var.set(value)
        self.progress_label.config(text=f"{value}%")
        self.parent.update()

    def populate_columns(self):
        """Populate the four Combobox dropdowns after a file is loaded.

        Sets the first two file columns as the default x and y selections,
        matching the most common layout of a two-column data file.
        Displays the row and column count to confirm the import was successful.
        """
        if self.df is None:
            return
        cols = list(self.df.columns)
        self.x_col["values"] = cols
        self.y_col["values"] = cols
        self.x_err_col["values"] = ["None"] + cols
        self.y_err_col["values"] = ["None"] + cols
        if cols:
            self.x_col.set(cols[0])
        if len(cols) >= 2:
            self.y_col.set(cols[1])
        messagebox.showinfo("Success",
                            f"File loaded successfully!\n\nRows: {len(self.df)}\n"
                            f"Columns: {len(cols)}\n\nPlease verify column mappings below.")

    def collect_file_data(self):
        """Collect data from the imported file into self.input_data.

        Converts the user's Combobox selections to 1-based column indices (as required
        by InputData.read_csv_file / read_excel) and calls the appropriate reader.
        Raises ValueError with a descriptive message if the DataFrame is absent or
        columns are unselected, satisfying success criterion 1.1.4 (input validation).
        """
        if self.df is None:
            raise ValueError("No file has been imported.")
        x_col_name = self.x_col.get()
        y_col_name = self.y_col.get()
        if not x_col_name or not y_col_name:
            raise ValueError("Please select both X and Y columns.")
        cols = list(self.df.columns)
        x_idx = cols.index(x_col_name) + 1
        y_idx = cols.index(y_col_name) + 1
        x_err_name = self.x_err_col.get()
        y_err_name = self.y_err_col.get()
        x_err_idx = cols.index(x_err_name) + 1 if x_err_name != "None" else None
        y_err_idx = cols.index(y_err_name) + 1 if y_err_name != "None" else None
        self.input_data = InputData()
        if self.filepath.endswith('.csv'):
            self.input_data.read_csv_file(self.filepath, x_idx, y_idx, x_err_idx, y_err_idx)
        else:
            self.input_data.read_excel(self.filepath, x_idx, y_idx, x_err_idx, y_err_idx)

    def collect_manual_data(self):
        """Collect data from manual entry fields into self.input_data.

        Calls get_manual_data() to extract numeric values from the entry grid, then
        validates that x and y have equal counts and at least three data points
        (the minimum required for meaningful regression, Section 3.2.2, Algorithm 1).
        x_title and y_title are read from the editable header entries; defaults
        apply if the user left them as placeholder text.
        Satisfies success criterion 1.1.3 and 1.1.4.
        """
        manual_data = self.get_manual_data()
        if manual_data is None:
            raise ValueError("Please enter valid numeric data in at least one row.")
        x_vals = [v for v in manual_data["X"] if v is not None]
        y_vals = [v for v in manual_data["Y"] if v is not None]
        x_err_vals = [v for v in manual_data["X_err"] if v is not None] or None
        y_err_vals = [v for v in manual_data["Y_err"] if v is not None] or None
        if len(x_vals) != len(y_vals):
            raise ValueError("X and Y must have the same number of values.")
        if len(x_vals) < 3:
            raise ValueError("At least 3 data points are required.")
        x_title = self.header_entries[0].get().strip()
        y_title = self.header_entries[2].get().strip()
        x_title = "X" if not x_title or x_title == "X Val" else x_title
        y_title = "Y" if not y_title or y_title == "Y Val" else y_title
        self.input_data = InputData()
        self.input_data.get_manual_data(x_vals, y_vals, x_err_vals, y_err_vals, x_title, y_title)

    def create_manual_panel(self, parent):
        """Build the right panel for Branch 2 (Manual Spreadsheet Entry).

        The panel contains a grid of tk.Entry widgets (7 rows × 4 columns) that the
        user fills with numeric data. validate_entry is bound to <KeyRelease> on each
        cell to provide immediate green/red visual feedback (success criterion 1.1.4).
        """
        self.manual_panel_container, self.manual_panel, _, _ = make_scrollable(
            parent, row=0, column=1, padx=(10, 0), bg="white", panel_kwargs={"padx": 20, "pady": 20}
        )
        panel = self.manual_panel
        tk.Label(panel, text="Manual Spreadsheet Entry", font=("Segoe UI", 13, "bold"),
                 bg="white", fg="#0f172a").pack(anchor="w", pady=(0, 15))

        table_frame = tk.Frame(panel, bg="white")
        table_frame.pack(pady=10)

        # Header row: editable Entry widgets initialised with placeholder text.
        self.header_entries = []
        for col, text in enumerate(_MANUAL_HEADERS):
            e = tk.Entry(table_frame, font=("Segoe UI", 9, "bold"), fg="#94a3b8",
                         justify="center", width=12, relief="solid", bd=1)
            e.insert(0, text)
            e.grid(row=0, column=col, padx=1, pady=1, sticky="ew")
            # FocusIn/FocusOut bindings implement placeholder text behaviour.
            e.bind("<FocusIn>",  lambda ev, t=text: self.clear_placeholder(ev, t))
            e.bind("<FocusOut>", lambda ev, t=text: self.restore_placeholder(ev, t))
            self.header_entries.append(e)

        # Data rows: 7 initial rows, expandable via Add Row button.
        self.entries = [self._make_entry_row(table_frame, row) for row in range(1, 8)]

        # Warning banner indicating that error columns are optional.
        info_frame = tk.Frame(panel, bg="#fef3c7", relief="solid", bd=1)
        info_frame.pack(fill="x", pady=15, padx=5)
        info_content = tk.Frame(info_frame, bg="#fef3c7", padx=10, pady=8)
        info_content.pack(fill="x")
        tk.Label(info_content, text="Warning", bg="#fef3c7", fg="#92400e").pack(side="left", padx=(0, 8))
        tk.Label(info_content, text="Uncertainty Columns: Optional - can be left blank",
                 font=("Segoe UI", 9), bg="#fef3c7", fg="#92400e").pack(side="left")

        btn_frame = tk.Frame(panel, bg="white")
        btn_frame.pack(pady=10)
        _btn(btn_frame, "Add Row", self.add_row, bg="#f1f5f9", fg="#334155",
             font_size=9, bold=False, padx=15, pady=5).pack(side="left", padx=5)
        _btn(btn_frame, "Delete Row", self.delete_row, bg="#f1f5f9", fg="#334155",
             font_size=9, bold=False, padx=15, pady=5).pack(side="left", padx=5)

    def _make_entry_row(self, table_frame: tk.Frame, row: int) -> list:
        """Create and grid four tk.Entry widgets for a data row.

        Each entry has a <KeyRelease> binding to validate_entry so the cell background
        updates to green (#f0fdf4) for valid numbers or red (#fee2e2) for invalid input
        on every keystroke (success criterion 1.1.4).
        """
        row_entries = []
        for col in range(4):
            entry = tk.Entry(table_frame, font=("Segoe UI", 9), width=12,
                             justify="center", relief="solid", bd=1)
            entry.grid(row=row, column=col, padx=1, pady=1, sticky="ew")
            entry.bind("<KeyRelease>", lambda e: self.validate_entry(e.widget))
            row_entries.append(entry)
        return row_entries

    def validate_entry(self, entry_widget):
        """Colour-code entry cells on each keystroke: green for valid float, red for invalid.

        float() is used to test whether the cell content is numeric; a ValueError
        indicates invalid input and triggers the red background.
        If a file has been loaded, manual entry is blocked by immediately clearing
        any typed character (mutually exclusive input paths, Section 3.2.1).
        """
        if self.df is None and entry_widget.get().strip():
            # Disable the import panel once manual typing starts.
            self.set_panel_state(self.import_panel, enabled=False)
        if self.df is not None:
            entry_widget.delete(0, tk.END)
            return
        value = entry_widget.get().strip()
        if not value:
            entry_widget.config(bg="white")
            return
        try:
            float(value)
            entry_widget.config(bg="#f0fdf4")   # green: valid number
        except ValueError:
            entry_widget.config(bg="#fee2e2")   # red: non-numeric input

    def add_row(self):
        """Append a new data row to the manual entry grid."""
        table_frame = self.entries[0][0].master
        self.entries.append(self._make_entry_row(table_frame, len(self.entries) + 1))

    def delete_row(self):
        """Remove the last row from the manual entry grid.

        A minimum of three rows is enforced because Algorithm 1 (linear regression,
        Section 3.2.2) requires at least three data points for a meaningful fit.
        widget.destroy() removes the Entry widget from both the grid and memory.
        """
        if len(self.entries) <= 3:
            messagebox.showwarning("Minimum Rows", "At least three rows must remain.")
            return
        for entry in self.entries.pop():
            entry.destroy()

    def get_manual_data(self):
        """Extract numeric values from the manual entry grid into a dict of lists.

        Iterates over all rows; any row that is entirely blank is skipped. A single
        non-numeric cell in a non-blank row causes None to be returned, signalling
        invalid input to collect_manual_data().
        Returns None if no file has been loaded but df is not None (defensive guard).
        """
        if self.df is not None:
            return None
        data = {"X": [], "Y": [], "X_err": [], "Y_err": []}
        for row_entries in self.entries:
            x_val, x_err, y_val, y_err = (e.get().strip() for e in row_entries)
            if not any((x_val, x_err, y_val, y_err)):
                continue    # skip fully blank rows
            try:
                data["X"].append(float(x_val) if x_val else None)
                data["Y"].append(float(y_val) if y_val else None)
                data["X_err"].append(float(x_err) if x_err else None)
                data["Y_err"].append(float(y_err) if y_err else None)
            except ValueError:
                return None
        return data if data["X"] else None

    def proceed_to_next(self):
        """Validate input, store InputData in ScreenManager, and navigate to Screen 2.

        Calls collect_file_data or collect_manual_data depending on which pathway
        the user took; any validation error surfaces as a messagebox with a descriptive
        message, satisfying success criterion 1.1.4.
        manager.set_data stores the InputData so Screen 2 can retrieve it via get_data().
        manager.show(AnalysisMethodScreen) navigates to Screen 2 (Section 3.2.1).
        """
        try:
            if self.df is not None:
                self.collect_file_data()
            else:
                self.collect_manual_data()
            self.manager.set_data(self.input_data)
            messagebox.showinfo("Data Validated", "Data validated successfully. Proceeding to analysis.")
            self.manager.show(AnalysisMethodScreen)
        except Exception as e:
            messagebox.showerror("Data Error", str(e))

    def clear_placeholder(self, event, text: str):
        """Clear placeholder text when an entry gains focus."""
        if event.widget.get() == text:
            event.widget.delete(0, tk.END)
            event.widget.config(fg="#0f172a")

    def restore_placeholder(self, event, text: str):
        """Restore placeholder text when an entry loses focus while empty."""
        if not event.widget.get().strip():
            event.widget.insert(0, text)
            event.widget.config(fg="#94a3b8")

    def _reset_file_state(self):
        """Clear loaded file state and reset all four Combobox selectors to empty."""
        self.df = None
        self.filepath = None
        self.drop_label.config(text="Drop file or click to browse", fg="#64748b", font=("Segoe UI", 10))
        for combo in (self.x_col, self.y_col, self.x_err_col, self.y_err_col):
            combo.set("")
            combo["values"] = []
        self.x_err_col.set("None")
        self.y_err_col.set("None")

    def clear_all(self):
        """Reset all inputs on both panels to their initial state."""
        self._reset_file_state()
        if hasattr(self, "progress_frame"):
            self.progress_frame.pack_forget()
        for row in self.entries:
            for entry in row:
                entry.config(state="normal", bg="white")
                entry.delete(0, tk.END)
        for entry, text in zip(self.header_entries, _MANUAL_HEADERS):
            entry.config(state="normal", fg="#94a3b8")
            entry.delete(0, tk.END)
            entry.insert(0, text)
        messagebox.showinfo("Reset Complete", "All inputs have been cleared.")
        self.set_panel_state(self.import_panel, enabled=True)

    def remove_imported_file(self):
        """Remove the currently loaded file and re-enable the manual entry panel."""
        self._reset_file_state()
        self.remove_file_btn.pack_forget()
        for row in self.entries:
            for entry in row:
                entry.config(state="normal")
        messagebox.showinfo("File Removed", "Imported file has been removed.")
        self.set_panel_state(self.manual_panel, enabled=True)

    def set_panel_state(self, panel, enabled: bool):
        """Recursively enable or disable all widgets in a panel.

        Changing bg and fg gives a visual greyed-out appearance for disabled panels,
        clearly communicating to the user which pathway is currently active
        (success criterion 1.1.4).
        winfo_children() returns all direct children of a widget; the recursive
        _update_widget_state call propagates the state change to nested frames.
        """
        bg = "white" if enabled else "#e5e7eb"
        fg = "#0f172a" if enabled else "#9ca3af"
        panel.config(bg=bg)
        for widget in panel.winfo_children():
            self._update_widget_state(widget, enabled, bg, fg)

    def _update_widget_state(self, widget, enabled: bool, bg: str, fg: str):
        """Apply state, bg and fg to a single widget, ignoring unsupported options via TclError."""
        try:
            widget.config(state="normal" if enabled else "disabled", bg=bg, fg=fg)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._update_widget_state(child, enabled, bg, fg)


if __name__ == "__main__":
    # Standalone launch for layout testing without running the full application.
    root = tk.Tk()
    root.title("LineaX - Data Analysis Tool")
    root.geometry("1100x700")
    root.configure(bg="#f5f6f8")
    root.update_idletasks()
    x = (root.winfo_screenwidth() - 1100) // 2
    y = (root.winfo_screenheight() - 700) // 2
    root.geometry(f"1100x700+{x}+{y}")
    manager = ScreenManager(root)
    manager.show(DataInputScreen)
    root.mainloop()