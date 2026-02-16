import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from LineaX_Classes import *
from AnalysisMethod import *
from ManagingScreen import *


class DataInputScreen(tk.Frame):
    def __init__(self, parent, manager):
        super().__init__(parent, bg="#f5f6f8")
        self.manager = manager
        self.parent = parent
        self.df = None
        self.input_data = None
        self.configure(padx=20, pady=15)
        self.create_layout()

    def create_layout(self):
        # Header with LineaX branding
        header = tk.Frame(self, bg="white", height=50)
        header.pack(fill="x", pady=(0, 15))
        header.pack_propagate(False)

        tk.Label(
            header,
            text="LineaX",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg="#0f172a"
        ).pack(side="left", padx=15, pady=10)

        # Main Title
        tk.Label(
            self,
            text="Import Your Data",
            font=("Segoe UI", 26, "bold"),
            bg="#f5f6f8",
            fg="#0f172a"
        ).pack(pady=(10, 25))

        # Main container with rounded appearance
        container = tk.Frame(self, bg="#d1d5db")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # Inner frame for content
        inner = tk.Frame(container, bg="#d1d5db", padx=15, pady=15)
        inner.pack(fill="both", expand=True)

        # Configure grid layout for two equal columns
        inner.grid_rowconfigure(0, weight=1)
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(1, weight=1)

        # Left and right panels
        self.create_import_panel(inner)
        self.create_manual_panel(inner)

        # Next button at bottom
        bottom_frame = tk.Frame(self, bg="#f5f6f8")
        bottom_frame.pack(fill="x", pady=(15, 0))

        self.next_btn = tk.Button(
            bottom_frame,
            text="Next →",
            font=("Segoe UI", 11, "bold"),
            bg="#0f172a",
            fg="white",
            padx=30,
            pady=10,
            relief="flat",
            cursor="hand2",
            command=self.proceed_to_next
        )
        self.next_btn.pack(side="right", padx=10)

        tk.Button(
            bottom_frame,
            text="↺ Clear All",
            font=("Segoe UI", 10, "bold"),
            bg="#e5e7eb",
            fg="#334155",
            padx=20,
            pady=10,
            relief="flat",
            cursor="hand2",
            command=self.clear_all
        ).pack(side="right", padx=10)

    def create_import_panel(self, parent):
        """Create left panel for CSV/Excel import"""
        self.import_panel_container, self.import_panel, _, _ = make_scrollable(
            parent,
            row=0,
            column=0,
            padx=(0, 10),
            bg="white",
            panel_kwargs={"padx": 20, "pady": 20},
        )
        left_panel = self.import_panel

        # Title
        tk.Label(
            left_panel,
            text="Import Excel/CSV Files",
            font=("Segoe UI", 13, "bold"),
            bg="white",
            fg="#0f172a"
        ).pack(anchor="w", pady=(0, 15))

        # Progress bar frame (hidden initially)
        self.progress_frame = tk.Frame(left_panel, bg="white")

        self.progress_var = tk.DoubleVar(value=0)

        self.progress = ttk.Progressbar(
            self.progress_frame,
            mode="determinate",
            length=320,
            maximum=100,
            variable=self.progress_var
        )

        self.progress_label = tk.Label(
            self.progress_frame,
            text="0%",
            font=("Segoe UI", 9),
            bg="white",
            fg="#475569"
        )

        self.progress.pack()
        self.progress_label.pack(pady=(2, 0))

        # Drop zone with dashed border
        drop_frame = tk.Frame(left_panel, bg="white")
        drop_frame.pack(pady=15)

        self.drop_zone = tk.Frame(
            drop_frame,
            bg="#f8fafc",
            relief="solid",
            bd=2,
            highlightbackground="#cbd5e1",
            highlightthickness=2
        )
        self.drop_zone.pack()

        # Drop zone content
        drop_content = tk.Frame(self.drop_zone, bg="#f8fafc", padx=40, pady=40)
        drop_content.pack()

        # Upload icon (using emoji as placeholder)
        tk.Label(
            drop_content,
            text="📁",
            font=("Segoe UI", 32),
            bg="#f8fafc"
        ).pack()

        self.drop_label = tk.Label(
            drop_content,
            text="Drop file or click to browse",
            font=("Segoe UI", 10),
            bg="#f8fafc",
            fg="#64748b"
        )
        self.drop_label.pack(pady=(10, 0))

        self.remove_file_btn = tk.Button(
            drop_content,
            text="✕",
            font=("Segoe UI", 10, "bold"),
            fg="#ef4444",
            bg="#f8fafc",
            relief="flat",
            cursor="hand2",
            command=self.remove_imported_file
        )
        self.remove_file_btn.pack(pady=(5, 0))
        self.remove_file_btn.pack_forget()  # hidden initially

        # Make drop zone clickable
        for widget in [self.drop_zone, drop_content, self.drop_label]:
            widget.bind("<Button-1>", lambda e: self.select_file())

        # Select File button
        tk.Button(
            left_panel,
            text="Select File",
            font=("Segoe UI", 10, "bold"),
            bg="#0f172a",
            fg="white",
            padx=20,
            pady=8,
            relief="flat",
            cursor="hand2",
            command=self.select_file
        ).pack(pady=10)

        # Column mapping section
        map_frame = tk.LabelFrame(
            left_panel,
            text=" 📋 Map Your Columns:",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#475569",
            padx=15,
            pady=15
        )
        map_frame.pack(fill="x", pady=15)

        # Dropdown style
        style = ttk.Style()
        style.configure("TCombobox", padding=5)

        # Column selectors
        self.x_col = ttk.Combobox(map_frame, state="readonly", width=25)
        self.y_col = ttk.Combobox(map_frame, state="readonly", width=25)
        self.x_err_col = ttk.Combobox(map_frame, state="readonly", values=["None"], width=25)
        self.y_err_col = ttk.Combobox(map_frame, state="readonly", values=["None"], width=25)

        # Set default values
        self.x_err_col.set("None")
        self.y_err_col.set("None")

        mappings = [
            ("X Values:", self.x_col),
            ("Y Values:", self.y_col),
            ("X Uncertainty:", self.x_err_col),
            ("Y Uncertainty:", self.y_err_col)
        ]

        for label_text, combo in mappings:
            label_frame = tk.Frame(map_frame, bg="white")
            label_frame.pack(fill="x", pady=5)

            tk.Label(
                label_frame,
                text=label_text,
                font=("Segoe UI", 9),
                bg="white",
                fg="#334155"
            ).pack(anchor="w")

            combo.pack(fill="x", pady=(2, 0))

        # Optional note
        tk.Label(
            map_frame,
            text="* Uncertainties are optional",
            font=("Segoe UI", 8, "italic"),
            fg="#94a3b8",
            bg="white"
        ).pack(anchor="w", pady=(8, 0))

    def select_file(self):
        path = filedialog.askopenfilename(
            title="Select Data File",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*")
            ]
        )

        if not path:
            return

        self.filepath = path
        self.progress_var.set(0)
        self.progress_label.config(text="0%")
        self.progress_frame.pack(pady=5, before=self.drop_zone.master)
        self.parent.update()

        try:
            self.progress_var.set(30)
            self.progress_label.config(text="30%")
            self.parent.update()

            if path.endswith(".csv"):
                self.df = pd.read_csv(path)
            else:
                self.df = pd.read_excel(path)

            self.progress_var.set(70)
            self.progress_label.config(text="70%")
            self.parent.update()

            filename = path.split("/")[-1]
            self.drop_label.config(
                text=f"✓ {filename}",
                fg="#10b981",
                font=("Segoe UI", 10, "bold")
            )

            self.populate_columns()

            self.progress_var.set(100)
            self.progress_label.config(text="100%")
            self.parent.update()

            self.set_panel_state(self.manual_panel, enabled=False)
            self.remove_file_btn.place(relx=1, rely=0, anchor="ne")

        except Exception as e:
            self.df = None
            self.filepath = None
            messagebox.showerror("File Error", str(e))

        finally:
            self.parent.after(300, self.progress_frame.pack_forget)

    def populate_columns(self):
        """Populate column dropdowns after file load"""
        if self.df is None:
            return

        cols = list(self.df.columns)

        # Update all comboboxes
        self.x_col["values"] = cols
        self.y_col["values"] = cols
        self.x_err_col["values"] = ["None"] + cols
        self.y_err_col["values"] = ["None"] + cols

        # Auto-select first two columns if available
        if len(cols) >= 1:
            self.x_col.set(cols[0])
        if len(cols) >= 2:
            self.y_col.set(cols[1])

        messagebox.showinfo(
            "Success",
            f"File loaded successfully!\n\n"
            f"Rows: {len(self.df)}\n"
            f"Columns: {len(cols)}\n\n"
            f"Please verify column mappings below."
        )

    def collect_file_data(self):
        """Collect data from imported CSV/Excel file."""
        if self.df is None:
            raise ValueError("No file has been imported.")

        x_col_name = self.x_col.get()
        y_col_name = self.y_col.get()
        x_err_name = self.x_err_col.get()
        y_err_name = self.y_err_col.get()

        if not x_col_name or not y_col_name:
            raise ValueError("Please select both X and Y columns.")

        # Get column indices (1-based)
        x_idx = list(self.df.columns).index(x_col_name) + 1
        y_idx = list(self.df.columns).index(y_col_name) + 1

        # Get error column indices if specified
        x_err_idx = None
        y_err_idx = None
        if x_err_name != "None":
            x_err_idx = list(self.df.columns).index(x_err_name) + 1
        if y_err_name != "None":
            y_err_idx = list(self.df.columns).index(y_err_name) + 1

        # Create InputData instance
        self.input_data = InputData()

        # Determine file type and read accordingly
        if hasattr(self, 'filepath'):
            if self.filepath.endswith('.csv'):
                self.input_data.read_csv_file(
                    self.filepath,
                    x_idx,
                    y_idx,
                    x_err_idx,
                    y_err_idx
                )
            else:  # Excel file
                self.input_data.read_excel(
                    self.filepath,
                    x_idx,
                    y_idx,
                    x_err_idx,
                    y_err_idx
                )

    def collect_manual_data(self):
        """Collect data from manual entry fields."""
        manual_data = self.get_manual_data()

        if manual_data is None:
            raise ValueError("Please enter valid numeric data in at least one row.")

        # Remove None values
        x_vals = [v for v in manual_data["X"] if v is not None]
        y_vals = [v for v in manual_data["Y"] if v is not None]
        x_err_vals = [v for v in manual_data["X_err"] if v is not None]
        y_err_vals = [v for v in manual_data["Y_err"] if v is not None]

        if len(x_vals) != len(y_vals):
            raise ValueError("X and Y must have the same number of values.")

        if len(x_vals) < 3:
            raise ValueError("At least 3 data points are required.")

        # Get titles from header entries
        x_title = self.header_entries[0].get().strip()
        y_title = self.header_entries[2].get().strip()

        # Use defaults if empty
        if not x_title or x_title == "X Val":
            x_title = "X"
        if not y_title or y_title == "Y Val":
            y_title = "Y"

        # Create InputData instance
        self.input_data = InputData()
        self.input_data.get_manual_data(
            x_vals,
            y_vals,
            x_err_vals if x_err_vals else None,
            y_err_vals if y_err_vals else None,
            x_title,
            y_title
        )

    def create_manual_panel(self, parent):
        """Create right panel for manual data entry"""
        self.manual_panel_container, self.manual_panel, _, _ = make_scrollable(
            parent,
            row=0,
            column=1,
            padx=(10, 0),
            bg="white",
            panel_kwargs={"padx": 20, "pady": 20},
        )
        right_panel = self.manual_panel

        # Title
        tk.Label(
            right_panel,
            text="Manual Spreadsheet Entry",
            font=("Segoe UI", 13, "bold"),
            bg="white",
            fg="#0f172a"
        ).pack(anchor="w", pady=(0, 15))

        # Spreadsheet table with colored headers
        table_frame = tk.Frame(right_panel, bg="white")
        table_frame.pack(pady=10)

        placeholders = ["X Val", "X Err", "Y Val", "Y Err"]
        self.header_entries = []

        for col, text in enumerate(placeholders):
            e = tk.Entry(
                table_frame,
                font=("Segoe UI", 9, "bold"),
                fg="#94a3b8",
                justify="center",
                width=12,
                relief="solid",
                bd=1
            )
            e.insert(0, text)
            e.grid(row=0, column=col, padx=1, pady=1, sticky="ew")

            e.bind("<FocusIn>", lambda ev, t=text: self.clear_placeholder(ev, t))
            e.bind("<FocusOut>", lambda ev, t=text: self.restore_placeholder(ev, t))

            self.header_entries.append(e)


        # Create data entry rows
        self.entries = []
        for row in range(1, 8):  # 7 rows for data entry
            row_entries = []
            for col in range(4):
                entry = tk.Entry(
                    table_frame,
                    font=("Segoe UI", 9),
                    width=12,
                    justify="center",
                    relief="solid",
                    bd=1
                )
                entry.grid(row=row, column=col, padx=1, pady=1, sticky="ew")

                # Add validation for numeric input
                entry.bind("<KeyRelease>", lambda e, r=row, c=col: self.validate_entry(e.widget))

                row_entries.append(entry)
            self.entries.append(row_entries)

        # Warning/info box
        info_frame = tk.Frame(right_panel, bg="#fef3c7", relief="solid", bd=1)
        info_frame.pack(fill="x", pady=15, padx=5)

        info_content = tk.Frame(info_frame, bg="#fef3c7", padx=10, pady=8)
        info_content.pack(fill="x")

        tk.Label(
            info_content,
            text="⚠",
            font=("Segoe UI", 12),
            bg="#fef3c7",
            fg="#92400e"
        ).pack(side="left", padx=(0, 8))

        tk.Label(
            info_content,
            text="Uncertainty Columns: Optional - can be left blank",
            font=("Segoe UI", 9),
            bg="#fef3c7",
            fg="#92400e"
        ).pack(side="left")

        # Add/Delete row buttons
        btn_frame = tk.Frame(right_panel, bg="white")
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="➕ Add Row",
            font=("Segoe UI", 9),
            bg="#f1f5f9",
            fg="#334155",
            padx=15,
            pady=5,
            relief="flat",
            cursor="hand2",
            command=self.add_row
        ).pack(side="left", padx=5)

        tk.Button(
            btn_frame,
            text="➖ Delete Row",
            font=("Segoe UI", 9),
            bg="#f1f5f9",
            fg="#334155",
            padx=15,
            pady=5,
            relief="flat",
            cursor="hand2",
            command=self.delete_row
        ).pack(side="left", padx=5)

    def validate_entry(self, entry_widget):
        """Provide visual feedback for entry validation"""
        if self.df is None and entry_widget.get().strip():
            self.set_panel_state(self.import_panel, enabled=False)



        if self.df is not None:
            entry_widget.delete(0, tk.END)
            return

        value = entry_widget.get().strip()

        if not value:  # Empty is OK
            entry_widget.config(bg="white")
            return

        try:
            float(value)
            entry_widget.config(bg="#f0fdf4")  # Light green
        except ValueError:
            entry_widget.config(bg="#fee2e2")  # Light red

    def add_row(self):
        """Add a new row to the manual entry table"""
        # Find the table frame dynamically
        table_frame = self.entries[0][0].master

        current_rows = len(self.entries)
        new_row_index = current_rows + 1  # +1 because header is row 0

        row_entries = []

        for col in range(4):
            entry = tk.Entry(
                table_frame,
                font=("Segoe UI", 9),
                width=12,
                justify="center",
                relief="solid",
                bd=1
            )
            entry.grid(row=new_row_index, column=col, padx=1, pady=1, sticky="ew")

            # Keep numeric validation
            entry.bind(
                "<KeyRelease>",
                lambda e: self.validate_entry(e.widget)
            )

            row_entries.append(entry)

        self.entries.append(row_entries)

    def delete_row(self):
        """Delete the last row from manual entry"""
        if len(self.entries) <= 3:
            messagebox.showwarning("Minimum Rows", "At least three rows must remain.")
            return

        for entry in self.entries[-1]:
            entry.destroy()

        self.entries.pop()

    def get_manual_data(self):
        """Extract data from manual entry fields"""
        data = {"X": [], "Y": [], "X_err": [], "Y_err": []}

        if self.df is not None:
            return None

        for row_entries in self.entries:
            x_val = row_entries[0].get().strip()
            x_err = row_entries[1].get().strip()
            y_val = row_entries[2].get().strip()
            y_err = row_entries[3].get().strip()

            # Skip completely empty rows
            if not any([x_val, x_err, y_val, y_err]):
                continue

            try:
                data["X"].append(float(x_val) if x_val else None)
                data["Y"].append(float(y_val) if y_val else None)
                data["X_err"].append(float(x_err) if x_err else None)
                data["Y_err"].append(float(y_err) if y_err else None)
            except ValueError:
                return None  # Invalid data

        return data if data["X"] else None

    def proceed_to_next(self):
        """
        Decides which input path was used and passes InputData forward.
        """

        try:
            if self.df is not None:
                self.collect_file_data()
            else:
                self.collect_manual_data()

            self.manager.set_data(self.input_data)

            messagebox.showinfo(
                "Data Validated",
                "Data validated successfully. Proceeding to analysis."
            )

            self.manager.show(AnalysisMethodScreen)

        except Exception as e:
            messagebox.showerror("Data Error", str(e))

    def clear_placeholder(self, event, text):
        if event.widget.get() == text:
            event.widget.delete(0, tk.END)
            event.widget.config(fg="#0f172a")

    def restore_placeholder(self, event, text):
        if not event.widget.get().strip():
            event.widget.insert(0, text)
            event.widget.config(fg="#94a3b8")

    def clear_all(self):
        # Reset imported file
        self.df = None
        self.drop_label.config(
            text="Drop file or click to browse",
            fg="#64748b",
            font=("Segoe UI", 10)
        )

        # Reset column mappings
        for combo in [self.x_col, self.y_col, self.x_err_col, self.y_err_col]:
            combo.set("")
            combo["values"] = []

        self.x_err_col.set("None")
        self.y_err_col.set("None")

        # Hide progress bar
        if hasattr(self, "progress_frame"):
            self.progress_frame.pack_forget()

        # Clear manual entries + re-enable
        for row in self.entries:
            for entry in row:
                entry.config(state="normal")
                entry.delete(0, tk.END)
                entry.config(bg="white")

        # Reset manual header placeholders
        placeholders = ["X Val", "X Err", "Y Val", "Y Err"]
        for entry, text in zip(self.header_entries, placeholders):
            entry.config(state="normal", fg="#94a3b8")
            entry.delete(0, tk.END)
            entry.insert(0, text)

        messagebox.showinfo("Reset Complete", "All inputs have been cleared.")
        self.set_panel_state(self.import_panel, enabled=True)
        self.df = None

    def remove_imported_file(self):
        self.df = None

        self.drop_label.config(
            text="Drop file or click to browse",
            fg="#64748b",
            font=("Segoe UI", 10)
        )

        self.remove_file_btn.pack_forget()

        # Reset column selectors
        for combo in [self.x_col, self.y_col, self.x_err_col, self.y_err_col]:
            combo.set("")
            combo["values"] = []

        self.x_err_col.set("None")
        self.y_err_col.set("None")

        # Re-enable manual entry
        for row in self.entries:
            for entry in row:
                entry.config(state="normal")

        messagebox.showinfo("File Removed", "Imported file has been removed.")
        self.set_panel_state(self.manual_panel, enabled=True)
        self.df = None

    def set_panel_state(self, panel, enabled: bool):
        bg_colour = "white" if enabled else "#e5e7eb"
        text_colour = "#0f172a" if enabled else "#9ca3af"

        panel.config(bg=bg_colour)

        for widget in panel.winfo_children():
            self._update_widget_state(widget, enabled, bg_colour, text_colour)

    def _update_widget_state(self, widget, enabled, bg, fg):
        try:
            widget.config(
                state="normal" if enabled else "disabled",
                bg=bg,
                fg=fg
            )
        except tk.TclError:
            pass

        for child in widget.winfo_children():
            self._update_widget_state(child, enabled, bg, fg)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("LineaX - Data Analysis Tool")
    root.geometry("1100x700")
    root.configure(bg="#f5f6f8")

    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (1100 // 2)
    y = (root.winfo_screenheight() // 2) - (700 // 2)
    root.geometry(f"1100x700+{x}+{y}")

    # app = DataInputScreen(root)
    # app.pack(fill="both", expand=True)

    manager = ScreenManager(root)
    manager.show(DataInputScreen)

    root.mainloop()