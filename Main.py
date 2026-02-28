"""Main.py — Application entry point for LineaX.

Initialises the Tkinter root window, centres it on screen and launches Screen 1
(DataInputScreen) via ScreenManager. Satisfies success criterion 1.1.1.
"""

# tkinter is Python's standard GUI library; tk.Tk() creates the root application window.
import tkinter as tk

# ScreenManager handles screen-to-screen navigation and shared application state.
from ManagingScreens import ScreenManager

# DataInputScreen is Screen 1 (Section 3.2.1, Branch 1 and 2).
from DataInput import DataInputScreen


def main():
    """Launch the LineaX application at 1100x700, centred on screen.

    winfo_screenwidth / winfo_screenheight query the display resolution so the
    window can be positioned at (screen_width - window_width) // 2 on each axis.
    root.mainloop() starts the Tkinter event loop, which processes user input and
    widget redraws until the window is closed.
    """
    root = tk.Tk()
    root.title("LineaX – Linear Analysis Tool")
    root.geometry("1100x700")
    root.configure(bg="#f5f6f8")

    # update_idletasks() forces Tk to process pending geometry calculations before
    # querying screen dimensions, ensuring accurate centring on all monitors.
    root.update_idletasks()
    x = (root.winfo_screenwidth() - 1100) // 2
    y = (root.winfo_screenheight() - 700) // 2
    root.geometry(f"1100x700+{x}+{y}")

    manager = ScreenManager(root)
    manager.show(DataInputScreen)

    # mainloop() blocks here, processing events until the window is closed.
    root.mainloop()


if __name__ == "__main__":
    main()

