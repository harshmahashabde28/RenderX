"""OpenGL survival shooter integrated into RenderX."""

def run_shooter(audio=None):
    """Load the OpenGL runtime only when the user launches Breakpoint."""
    from .app import run_shooter as run
    return run(audio=audio)


__all__ = ["run_shooter"]
