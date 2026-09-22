"""Save the already-rendered window as a PNG without overwriting files."""
from datetime import datetime
from pathlib import Path
import pygame

SCREENSHOT_DIR = Path(__file__).resolve().parent.parent / "screenshots"


def save_screenshot(surface, directory=SCREENSHOT_DIR):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    stem = datetime.now().strftime("renderx_%Y-%m-%d_%H-%M-%S")
    counter = 0
    while True:
        suffix = f"_{counter:02d}" if counter else ""
        path = directory / f"{stem}{suffix}.png"
        try:
            output = path.open("xb")  # Exclusive creation: never overwrite.
            break
        except FileExistsError:
            counter += 1
    try:
        with output:
            pygame.image.save(surface, output, path.name)
    except (OSError, pygame.error):
        # This file was created by this call; discard only its partial output.
        path.unlink(missing_ok=True)
        raise
    return path
