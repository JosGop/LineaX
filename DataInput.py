import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from LineaX_Classes import InputData
from AnalysisMethod import AnalysisMethodScreen
from ManagingScreens import make_scrollable, ScreenManager

# Column header labels for the manual entry table
_MANUAL_HEADERS = ["X Val", "X Err", "Y Val", "Y Err"]


def _btn(parent, text, command, bg="#0f172a", fg="white", font_size=10, bold=True, **kwargs) -> tk.Button:
    """Factory for consistently styled flat buttons."""
    weight = "bold" if bold else "normal"
    return tk.Button(parent, text=text, font=("Segoe UI", font_size, weight),
                     bg=bg, fg=fg, relief="flat", cursor="hand2", command=command, **kwargs)


class DataInputScreen(tk.Frame):
    def __init__(self, parent, manager):
        super().__init__(parent, bg="#f5f6f8", padx=20, pady=15)
        self.manager = manager
        self.parent = parent
        self.df = None
        self.filepath = None
        self.input_data = None
        self.create_layout()

    def create_layout(self):
        # Header with LineaX branding
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

        bottom_frame = tk.Frame(self, bg="#f5f6f8")
        bottom_frame.pack(fill="x", pady=(15, 0))
        _btn(bottom_frame, "Next →", self.proceed_to_next, padx=30, pady=10).pack(side="right", padx=10)
        _btn(bottom_frame, "↺ Clear All", self.clear_all,
             bg="#e5e7eb", fg="#334155", bold=True, padx=20, pady=10).pack(side="right", padx=10)

    def create_import_panel(self, parent):
        """Create left panel for CSV/Excel import."""
        self.import_panel_container, self.import_panel, _, _ = make_scrollable(
            parent, row=0, column=0, padx=(0, 10), bg="white", panel_kwargs={"padx": 20, "pady": 20}
        )
        panel = self.import_panel

        tk.Label(panel, text="Import Excel/CSV Files", font=("Segoe UI", 13, "bold"),
                 bg="white", fg="#0f172a").pack(anchor="w", pady=(0, 15))

        # Progress bar (hidden initially)
        self.progress_frame = tk.Frame(panel, bg="white")
        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(self.progress_frame, mode="determinate",
                                        length=320, maximum=100, variable=self.progress_var)
        self.progress_label = tk.Label(self.progress_frame, text="0%",
                                       font=("Segoe UI", 9), bg="white", fg="#475569")
        self.progress.pack()
        self.progress_label.pack(pady=(2, 0))

        # Drop zone
        drop_frame = tk.Frame(panel, bg="white")
        drop_frame.pack(pady=15)
        self.drop_zone = tk.Frame(drop_frame, bg="#f8fafc", relief="solid", bd=2,
                                  highlightbackground="#cbd5e1", highlightthickness=2)
        self.drop_zone.pack()

        drop_content = tk.Frame(self.drop_zone, bg="#f8fafc", padx=40, pady=40)
        drop_content.pack()
        tk.Label(drop_content, text="📁", font=("Segoe UI", 32), bg="#f8fafc").pack()
        self.drop_label = tk.Label(drop_content, text="Drop file or click to browse",
                                   font=("Segoe UI", 10), bg="#f8fafc", fg="#64748b")
        self.drop_label.pack(pady=(10, 0))

        self.remove_file_btn = tk.Button(drop_content, text="✕", font=("Segoe UI", 10, "bold"),
                                         fg="#ef4444", bg="#f8fafc", relief="flat",
                                         cursor="hand2", command=self.remove_imported_file)
        self.remove_file_btn.pack(pady=(5, 0))
        self.remove_file_btn.pack_forget()

        for widget in (self.drop_zone, drop_content, self.drop_label):
            widget.bind("<Button-1>", lambda e: self.select_file())

        _btn(panel, "Select File", self.select_file, padx=20, pady=8).pack(pady=10)

        # Column mapping section
        map_frame = tk.LabelFrame(panel, text=" 📋 Map Your Columns:", font=("Segoe UI", 10, "bold"),
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
            tk.Label(row, text=label_text, font=("Segoe UI", 9),
                     bg="white", fg="#334155").pack(anchor="w")
            combo.pack(fill="x", pady=(2, 0))

        tk.Label(map_frame, text="* Uncertainties are optional", font=("Segoe UI", 8, "italic"),
                 fg="#94a3b8", bg="white").pack(anchor="w", pady=(8, 0))

    def select_file(self):
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
            self.df = pd.read_csv(path) if path.endswith(".csv") else pd.read_excel(path)
            self._set_progress(70)

            self.drop_label.config(text=f"✓ {path.split('/')[-1]}", fg="#10b981",
                                   font=("Segoe UI", 10, "bold"))
            self.populate_columns()
            self._set_progress(100)
            self.set_panel_state(self.manual_panel, enabled=False)
            self.remove_file_btn.place(relx=1, rely=0, anchor="ne")

        except Exception as e:
            self.df = None
            self.filepath = None
            messagebox.showerror("File Error", str(e))
        finally:
            self.parent.after(300, self.progress_frame.pack_forget)

    def _set_progress(self, value: int):
        """Update progress bar and label, then refresh the UI."""
        self.progress_var.set(value)
        self.progress_label.config(text=f"{value}%")
        self.parent.update()

    def populate_columns(self):
        """Populate column dropdowns after file load."""
        if self.df is None:
            return
        cols = list(self.df.columns)
        self.x_col["values"] = cols
        self.y_col["values"] = cols
        self.x_err_col["values"] = ["None"] + cols
        self.y_err_col["values"] = ["None"] + cols

        # Auto-select the first two columns
        if cols:
            self.x_col.set(cols[0])
        if len(cols) >= 2:
            self.y_col.set(cols[1])

        messagebox.showinfo("Success",
                            f"File loaded successfully!\n\nRows: {len(self.df)}\n"
                            f"Columns: {len(cols)}\n\nPlease verify column mappings below.")

    def collect_file_data(self):
        """Collect data from the imported CSV/Excel file into self.input_data."""
        if self.df is None:
            raise ValueError("No file has been imported.")

        x_col_name = self.x_col.get()
        y_col_name = self.y_col.get()
        if not x_col_name or not y_col_name:
            raise ValueError("Please select both X and Y columns.")

        cols = list(self.df.columns)
        # Convert column names to 1-based indices
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
        """Collect data from manual entry fields into self.input_data."""
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
        """Create right panel for manual data entry."""
        self.manual_panel_container, self.manual_panel, _, _ = make_scrollable(
            parent, row=0, column=1, padx=(10, 0), bg="white", panel_kwargs={"padx": 20, "pady": 20}
        )
        panel = self.manual_panel

        tk.Label(panel, text="Manual Spreadsheet Entry", font=("Segoe UI", 13, "bold"),
                 bg="white", fg="#0f172a").pack(anchor="w", pady=(0, 15))

        table_frame = tk.Frame(panel, bg="white")
        table_frame.pack(pady=10)

        # Header row with editable placeholder titles
        self.header_entries = []
        for col, text in enumerate(_MANUAL_HEADERS):
            e = tk.Entry(table_frame, font=("Segoe UI", 9, "bold"), fg="#94a3b8",
                         justify="center", width=12, relief="solid", bd=1)
            e.insert(0, text)
            e.grid(row=0, column=col, padx=1, pady=1, sticky="ew")
            e.bind("<FocusIn>", lambda ev, t=text: self.clear_placeholder(ev, t))
            e.bind("<FocusOut>", lambda ev, t=text: self.restore_placeholder(ev, t))
            self.header_entries.append(e)

        # 7 blank data-entry rows
        self.entries = []
        for row in range(1, 8):
            self.entries.append(self._make_entry_row(table_frame, row))

        # Warning info box
        info_frame = tk.Frame(panel, bg="#fef3c7", relief="solid", bd=1)
        info_frame.pack(fill="x", pady=15, padx=5)
        info_content = tk.Frame(info_frame, bg="#fef3c7", padx=10, pady=8)
        info_content.pack(fill="x")
        tk.Label(info_content, text="⚠", font=("Segoe UI", 12),
                 bg="#fef3c7", fg="#92400e").pack(side="left", padx=(0, 8))
        tk.Label(info_content, text="Uncertainty Columns: Optional - can be left blank",
                 font=("Segoe UI", 9), bg="#fef3c7", fg="#92400e").pack(side="left")

        btn_frame = tk.Frame(panel, bg="white")
        btn_frame.pack(pady=10)
        _btn(btn_frame, "➕ Add Row", self.add_row, bg="#f1f5f9", fg="#334155",
             font_size=9, bold=False, padx=15, pady=5).pack(side="left", padx=5)
        _btn(btn_frame, "➖ Delete Row", self.delete_row, bg="#f1f5f9", fg="#334155",
             font_size=9, bold=False, padx=15, pady=5).pack(side="left", padx=5)

    def _make_entry_row(self, table_frame: tk.Frame, row: int) -> list:
        """Create and grid 4 entry widgets for a data row; return the list of entries."""
        row_entries = []
        for col in range(4):
            entry = tk.Entry(table_frame, font=("Segoe UI", 9), width=12,
                             justify="center", relief="solid", bd=1)
            entry.grid(row=row, column=col, padx=1, pady=1, sticky="ew")
            entry.bind("<KeyRelease>", lambda e: self.validate_entry(e.widget))
            row_entries.append(entry)
        return row_entries

    def validate_entry(self, entry_widget):
        """Provide visual feedback for entry validation; disable import panel when manual data is entered."""
        if self.df is None and entry_widget.get().strip():
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
            entry_widget.config(bg="#f0fdf4")  # valid: light green
        except ValueError:
            entry_widget.config(bg="#fee2e2")  # invalid: light red

    def add_row(self):
        """Append a new data-entry row to the manual table."""
        table_frame = self.entries[0][0].master
        self.entries.append(self._make_entry_row(table_frame, len(self.entries) + 1))

    def delete_row(self):
        """Remove the last row from the manual table (minimum 3 rows enforced)."""
        if len(self.entries) <= 3:
            messagebox.showwarning("Minimum Rows", "At least three rows must remain.")
            return
        for entry in self.entries.pop():
            entry.destroy()

    def get_manual_data(self):
        """Extract and return data from manual entry fields, or None on invalid/empty input."""
        if self.df is not None:
            return None

        data = {"X": [], "Y": [], "X_err": [], "Y_err": []}
        for row_entries in self.entries:
            x_val, x_err, y_val, y_err = (e.get().strip() for e in row_entries)
            if not any((x_val, x_err, y_val, y_err)):
                continue  # skip empty rows
            try:
                data["X"].append(float(x_val) if x_val else None)
                data["Y"].append(float(y_val) if y_val else None)
                data["X_err"].append(float(x_err) if x_err else None)
                data["Y_err"].append(float(y_err) if y_err else None)
            except ValueError:
                return None
        return data if data["X"] else None

    def proceed_to_next(self):
        """Validate input from whichever path was used and navigate to AnalysisMethodScreen."""
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
        if event.widget.get() == text:
            event.widget.delete(0, tk.END)
            event.widget.config(fg="#0f172a")

    def restore_placeholder(self, event, text: str):
        if not event.widget.get().strip():
            event.widget.insert(0, text)
            event.widget.config(fg="#94a3b8")

    def _reset_file_state(self):
        """Shared helper: clear loaded file state and reset column selectors."""
        self.df = None
        self.filepath = None
        self.drop_label.config(text="Drop file or click to browse", fg="#64748b",
                               font=("Segoe UI", 10))
        for combo in (self.x_col, self.y_col, self.x_err_col, self.y_err_col):
            combo.set("")
            combo["values"] = []
        self.x_err_col.set("None")
        self.y_err_col.set("None")

    def clear_all(self):
        """Reset all inputs on both panels."""
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
        """Recursively enable or disable all widgets in a panel."""
        bg = "white" if enabled else "#e5e7eb"
        fg = "#0f172a" if enabled else "#9ca3af"
        panel.config(bg=bg)
        for widget in panel.winfo_children():
            self._update_widget_state(widget, enabled, bg, fg)

    def _update_widget_state(self, widget, enabled: bool, bg: str, fg: str):
        """Recursively apply state, background, and foreground to a widget tree."""
        try:
            widget.config(state="normal" if enabled else "disabled", bg=bg, fg=fg)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._update_widget_state(child, enabled, bg, fg)


if __name__ == "__main__":
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