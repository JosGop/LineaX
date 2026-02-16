import tkinter as tk
from ManagingScreen import ScreenManager
from DataInput import DataInputScreen
from AnalysisMethod import AnalysisMethodScreen
from LinearGraphDisplay import GraphResultsScreen
from GradientAnalysis import GradientAnalysisScreen

root = tk.Tk()
root.geometry("1000x600")
root.title("LineaX")

# Set minimum window size
root.minsize(800, 600)

# Center window on screen
root.update_idletasks()
width = root.winfo_width()
height = root.winfo_height()
x = (root.winfo_screenwidth() // 2) - (width // 2)
y = (root.winfo_screenheight() // 2) - (height // 2)
root.geometry(f'{width}x{height}+{x}+{y}')

manager = ScreenManager(root)
manager.show(DataInputScreen)

root.mainloop()