"""OpenGL survival shooter integrated into RenderX."""

def run_shooter():
    """Load the OpenGL runtime only when the user launches Breakpoint."""
    from .app import run_shooter as run
    return run()


__all__ = ["run_shooter"]
