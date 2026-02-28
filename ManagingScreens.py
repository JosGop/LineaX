"""ManagingScreens.py — Screen navigation and shared application state for LineaX.

ScreenManager acts as a central data bus between screens, holding InputData,
the graph figure, equation metadata and regression results so each screen can
retrieve what the previous screen computed (Section 3.2.1, Data Flow).

make_scrollable is a utility used by Screens 1, 2, 3a and 4 to wrap any panel
in a scrollable canvas, satisfying the usability requirement in Section 3.1.4
that all content must be accessible regardless of window height.
"""

# tkinter is Python's built-in GUI toolkit used throughout LineaX for all UI widgets.
import tkinter as tk


def make_scrollable(parent, row, column, padx=(0, 0), pady=0, bg="white", panel_kwargs=None):
    """Create a scrollable panel and return (container, panel, canvas, scrollbar).

    tk.Canvas serves as the viewport for the scrollable area; a tk.Frame (panel)
    is embedded inside the canvas via create_window so that its contents can
    extend beyond the visible area.

    tk.Scrollbar linked to the canvas via yscrollcommand/yview keeps the scrollbar
    thumb position in sync with the canvas scroll position.

    The <Configure> binding on the inner panel calls canvas.configure(scrollregion)
    whenever widgets are added or resized, updating the scrollable region automatically.
    The <Configure> binding on the canvas calls canvas.itemconfig to keep the inner
    frame width equal to the visible canvas width, preventing horizontal overflow.

    Mouse wheel scrolling is bound only while the cursor is over the panel (<Enter> /
    <Leave>) to avoid interfering with other scrollable widgets on the same screen.
    event.delta is used on Windows/macOS; Button-4/5 handle Linux scroll events.
    """
    panel_kwargs = panel_kwargs or {}

    # Outer container placed in the parent's grid layout.
    panel_container = tk.Frame(parent, bg=bg)
    panel_container.grid(row=row, column=column, sticky="nsew", padx=padx, pady=pady)

    # Canvas is the scrollable viewport; highlightthickness=0 removes the focus border.
    canvas = tk.Canvas(panel_container, bg=bg, highlightthickness=0)

    # Scrollbar positioned to the right; command=canvas.yview links it to the canvas.
    scrollbar = tk.Scrollbar(panel_container, orient="vertical", command=canvas.yview)

    # The panel Frame is the actual content area embedded inside the canvas.
    panel = tk.Frame(canvas, bg=bg, **panel_kwargs)

    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    # create_window embeds the panel Frame at (0,0) inside the canvas viewport.
    canvas_frame = canvas.create_window((0, 0), window=panel, anchor="nw")

    # Recalculate the scrollable region whenever panel contents change size.
    panel.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))

    # Keep inner frame width equal to canvas width to prevent horizontal overflow.
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_frame, width=e.width))

    def _on_mousewheel(event):
        """Scroll canvas on mouse wheel; normalises across platforms."""
        if event.delta:
            # Windows and macOS: event.delta is ±120 per notch.
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return
        # Linux: Button-4 scrolls up, Button-5 scrolls down.
        if getattr(event, "num", None) == 4:
            canvas.yview_scroll(-1, "units")
        elif getattr(event, "num", None) == 5:
            canvas.yview_scroll(1, "units")

    def _bind_scroll(_event):
        """Activate mouse wheel scrolling when cursor enters the panel."""
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)

    def _unbind_scroll(_event):
        """Deactivate mouse wheel scrolling when cursor leaves the panel."""
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

    panel.bind("<Enter>", _bind_scroll)
    panel.bind("<Leave>", _unbind_scroll)

    return panel_container, panel, canvas, scrollbar


class ScreenManager:
    """Central controller for screen navigation and shared application state.

    Implements a simple navigation stack: show() pushes the current screen and
    displays the new one; back() pops and restores the previous screen.
    This satisfies success criterion 1.2.1 (the user can navigate backwards
    through the analysis pipeline without losing previously entered data).

    Shared state fields:
      input_data       — validated InputData from Screen 1 (Section 3.2.1, Branch 1/2)
      raw_data         — original untransformed InputData, preserved for 'Fit Other Models'
      graph_figure     — Matplotlib Figure from Screen 3a, passed to Screen 4 for PDF export
      equation_info    — dict of gradient/intercept metadata from Screen 2
      analysis_results — regression results dict from Screen 3a, consumed by Screen 4
    """

    def __init__(self, root):
        # root is the Tk main window; all screens are packed into it.
        self.root = root

        # stack holds previously displayed screen widgets for back() navigation.
        self.stack = []
        self.current_screen = None

        # Shared data fields initialised to None; populated by each screen in sequence.
        self.input_data = None
        self.raw_data = None
        self.graph_figure = None
        self.equation_info = None
        self.analysis_results = None

    def set_data(self, input_data):
        """Store an InputData instance for retrieval by the next screen."""
        self.input_data = input_data

    def get_data(self):
        """Return the currently stored InputData instance."""
        return self.input_data

    def set_raw_data(self, raw_data):
        """Store the original untransformed dataset for revert operations."""
        self.raw_data = raw_data

    def get_raw_data(self):
        """Return the original untransformed InputData."""
        return self.raw_data

    def set_graph_figure(self, figure):
        """Store the Matplotlib Figure generated by Screen 3a."""
        self.graph_figure = figure

    def get_graph_figure(self):
        """Return the stored Matplotlib Figure."""
        return self.graph_figure

    def set_equation_info(self, equation_info):
        """Store the equation metadata dict produced by Screen 2."""
        self.equation_info = equation_info

    def get_equation_info(self):
        """Return the equation metadata dict."""
        return self.equation_info

    def set_analysis_results(self, analysis_results):
        """Store the regression results dict produced by Screen 3a."""
        self.analysis_results = analysis_results

    def get_analysis_results(self):
        """Return the regression results dict."""
        return self.analysis_results

    def show(self, screen_class):
        """Display a new screen, pushing the current one onto the back-navigation stack.

        screen_class is instantiated here with (root, self) so each screen receives a
        reference to ScreenManager and can call set_data / get_data / show / back.
        pack(fill='both', expand=True) makes the screen fill the entire root window.
        """
        if self.current_screen is not None:
            self.stack.append(self.current_screen)
            self.current_screen.pack_forget()   # hide without destroying
        self.current_screen = screen_class(self.root, self)
        self.current_screen.pack(fill="both", expand=True)

    def back(self):
        """Restore the previous screen from the navigation stack.

        pack_forget() hides the current screen; the previous screen is re-shown
        via pack without being re-instantiated, so all widget state is preserved.
        Satisfies success criterion 1.2.1.
        """
        if not self.stack:
            return
        self.current_screen.pack_forget()
        self.current_screen = self.stack.pop()
        self.current_screen.pack(fill="both", expand=True)