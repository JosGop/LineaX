import tkinter as tk
from ManagingScreen import ScreenManager
from AnalysisMethod import AnalysisMethodScreen
from DataInput import DataInputScreen

root = tk.Tk()
root.geometry("1000x600")
root.title("LineaX")

manager = ScreenManager(root)
manager.show(DataInputScreen)

root.mainloop()
