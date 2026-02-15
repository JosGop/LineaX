import tkinter as tk

def make_scrollable(parent, row, column, padx=(0, 0), pady=0, bg="white", panel_kwargs=None):
    """Create and grid a scrollable panel and return (container, panel, canvas, scrollbar)."""
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

    def _update_scroll_region(_event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _resize_panel(event):
        canvas.itemconfig(canvas_frame, width=event.width)

    panel.bind("<Configure>", _update_scroll_region)
    canvas.bind("<Configure>", _resize_panel)

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

        # Shared application data
        self.input_data = None

    def set_data(self, input_data):
        """
        Stores InputData instance for access across screens.
        """
        self.input_data = input_data

    def get_data(self):
        """
        Returns the stored InputData instance.
        """
        return self.input_data

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


