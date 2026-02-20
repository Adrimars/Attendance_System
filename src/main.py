"""
main.py — Application entry point.

Initialises the database, verifies the admin PIN, and launches the full-screen
CustomTkinter window.

Usage:
    python src/main.py          (from project root)
    python main.py              (from src/ directory)
"""

import sys
import os

# Ensure the project src directory is on sys.path when running as a script
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_SRC_DIR)
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

import customtkinter as ctk

from utils.logger import log_info, log_error
from models.database import initialise_database
from views.app import App


def main() -> None:
    """Initialise the database, show PIN guard, then launch the main window."""
    log_info("Application starting up.")

    try:
        initialise_database()
        log_info("Database initialised successfully.")
    except Exception as exc:
        log_error(f"Fatal: database initialisation failed — {exc}")
        # Show a plain-tkinter error before the CTk window exists
        import tkinter as tk
        from tkinter import messagebox
        _root = tk.Tk()
        _root.withdraw()
        messagebox.showerror(
            "Startup Error",
            f"Failed to initialise the database:\n\n{exc}\n\nThe application cannot start.",
        )
        _root.destroy()
        sys.exit(1)

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = App()
    app.mainloop()

    log_info("Application shut down cleanly.")


if __name__ == "__main__":
    main()
