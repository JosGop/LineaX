import tkinter as tk


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


