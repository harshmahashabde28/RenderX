"""Pygame presentation layer; imports stay lazy for the pure-Python core."""

__all__ = ["Panel"]


def __getattr__(name):
    if name == "Panel":
        from .panel import Panel
        return Panel
    raise AttributeError(name)
