"""
LinMain.py

Application entry point for LineaX.
Implements the launch logic described in Section 3.3 Development (Stage 2 — Data Input Screen, "Main Code Launch for the
Data Input Screen"). Initialises the root Tkinter window, centres it on the user's display, and opens the first screen
(DataInputScreen) via ScreenManager.show(). The conditional __main__ guard (also described in Section 3.3) allows
DataInputScreen and other modules to be imported independently during unit testing (Section 3.2.3, Stage 1) without
executing the full application.
"""

import tkinter as tk
from ManagingScreens import ScreenManager
from DataInput import DataInputScreen


def main():
    """
    Launch the LineaX application.

    Creates the root window, sets a fixed 1100×700 resolution as described in Section 3.3 (Stage 2: "presented at a fixed
    resolution to ensure consistent layout behaviour during early development"), centres the window on screen for usability
    (Section 3.1.4, Usability Features), and delegates screen management to ScreenManager.
    The fixed geometry ensures the UI mockups from Section 3.2.2 render as designed across different monitor sizes.
    """
    root = tk.Tk()
    root.title("LineaX – Linear Analysis Tool")
    root.geometry("1100x700")
    root.configure(bg="#f5f6f8")  # neutral background matches UI mockup colour scheme

    # Centre the window on the screen — described explicitly in Section 3.3 (Stage 2)
    root.update_idletasks()
    x = (root.winfo_screenwidth() - 1100) // 2
    y = (root.winfo_screenheight() - 700) // 2
    root.geometry(f"1100x700+{x}+{y}")

    # Initialise ScreenManager as the central state and navigation controller
    manager = ScreenManager(root)
    manager.show(DataInputScreen)  # launch at Screen 1 (Data Input) per the navigation flow
    root.mainloop()


if __name__ == "__main__":
    """
    Conditional entry point guard.

    Encapsulating the launch logic in this conditional block allows the screen to be imported into other modules later 
    without executing the application automatically, supporting modular development and testing.Enables white-box unit tests 
    (Section 3.2.3, Stage 1) to import individual screen classes without triggering the Tkinter event loop.
    """
    main()