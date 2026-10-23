"""Native system file chooser for opening Wavefront OBJ meshes."""

from pathlib import Path

from renderx import theme


class FileDialogUnavailable(RuntimeError):
    """Raised when the platform cannot create its native chooser."""


def choose_obj_file():
    """Open the platform file chooser and return the selected path or None."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError as error:
        raise FileDialogUnavailable("The system file chooser is unavailable.") from error
    try:
        root = tk.Tk()
    except tk.TclError as error:
        raise FileDialogUnavailable("The system file chooser could not be opened.") from error
    try:
        root.withdraw()
        root.wm_attributes("-topmost", True)
        recent = theme.recent_files()
        recent_dir = Path(recent[0]).expanduser().parent if recent else None
        initial_dir = (recent_dir if recent_dir and recent_dir.is_dir()
                       else Path.cwd())
        try:
            selected = filedialog.askopenfilename(
                parent=root,
                title="Open Wavefront OBJ",
                initialdir=str(initial_dir),
                filetypes=(("Wavefront OBJ", "*.obj"), ("All files", "*.*")),
            )
        except tk.TclError as error:
            raise FileDialogUnavailable("The system file chooser closed unexpectedly.") from error
        return selected or None
    finally:
        try:
            root.destroy()
        except tk.TclError:
            pass
