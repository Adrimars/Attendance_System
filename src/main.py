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
import traceback

# Ensure the project src directory is on sys.path when running as a script
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_SRC_DIR)
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

import customtkinter as ctk

from utils.logger import log_info, log_error, log_startup, log_shutdown
from models.database import initialise_database
from views.app import App


def _global_exception_handler(exc_type: type, exc_value: BaseException, exc_tb: object) -> None:
    """
    Last-resort handler for any uncaught exception.

    Logs the full traceback and shows a user-friendly error dialog before
    the application exits, so the user never sees a raw Python traceback.
    """
    import types
    tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb if isinstance(exc_tb, types.TracebackType) else None))
    log_error(f"Unhandled exception:\n{tb_text}")

    import tkinter as tk
    from tkinter import messagebox
    try:
        _root = tk.Tk()
        _root.withdraw()
        messagebox.showerror(
            "Unexpected Error",
            f"An unexpected error occurred and the application must close.\n\n"
            f"{exc_type.__name__}: {exc_value}\n\n"
            "Details have been written to the log file.",
        )
        _root.destroy()
    except Exception:
        pass  # If even the dialog fails, we can't do much more


def main() -> None:
    """Initialise the database, show PIN guard, then launch the main window."""
    # Install global handler so no raw tracebacks reach the user
    sys.excepthook = _global_exception_handler

    log_startup()
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

    log_shutdown()
    log_info("Application shut down cleanly.")


if __name__ == "__main__":
    main()
