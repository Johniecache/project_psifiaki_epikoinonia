from gui.main_window import MainWindow
from client import ClientController
import tkinter as tk

if __name__ == "__main__":
    client_controller = ClientController()
    app = MainWindow(client_controller)
    app.mainloop()
