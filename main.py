"""Start RenderX with: python main.py."""
import sys


def main():
    try:
        import pygame
    except ModuleNotFoundError as error:
        if error.name != "pygame":
            raise
        print("Pygame is missing. Run: python -m pip install -r requirements.txt",
              file=sys.stderr)
        return 1

    from renderx.app import run

    try:
        run()
    except pygame.error as error:
        print(f"RenderX could not start or use the display: {error}",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
