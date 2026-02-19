import tkinter as tk
from ManagingScreens import ScreenManager
from DataInput import DataInputScreen


def main():
    """Launch the LineaX application."""
    root = tk.Tk()
    root.title("LineaX – Linear Analysis Tool")
    root.geometry("1100x700")
    root.configure(bg="#f5f6f8")

    # Centre the window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() - 1100) // 2
    y = (root.winfo_screenheight() - 700) // 2
    root.geometry(f"1100x700+{x}+{y}")

    manager = ScreenManager(root)
    manager.show(DataInputScreen)
    root.mainloop()


if __name__ == "__main__":
    main()