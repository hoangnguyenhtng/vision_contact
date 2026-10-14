import tkinter as tk

from app_actions import AppActions


def main():
    root = tk.Tk()
    AppActions(root)
    root.mainloop()


if __name__ == "__main__":
    main()
