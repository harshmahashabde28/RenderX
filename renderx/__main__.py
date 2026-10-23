"""Command-line entry point for ``python -m renderx``."""

import argparse
import sys


def _parser():
    parser = argparse.ArgumentParser(description="RenderX 3D wireframe renderer")
    parser.add_argument("--skip-landing", action="store_true",
                        help="open the Explore workspace directly")
    parser.add_argument("--mode", choices=("explore", "challenge", "maze", "shooter"),
                        help="open a destination directly for development or QA")
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    try:
        import pygame
    except ModuleNotFoundError:
        print("RenderX dependencies are missing. Install requirements.txt first.",
              file=sys.stderr)
        return 1

    try:
        from renderx.app import run
        run(skip_landing=args.skip_landing, mode=args.mode)
    except ModuleNotFoundError as error:
        if error.name not in {"numpy", "OpenGL", "glm", "trimesh"}:
            raise
        print(f"RenderX is missing {error.name}. Install: python -m pip install -r requirements.txt",
              file=sys.stderr)
        return 1
    except pygame.error as error:
        print(f"RenderX could not start or use the display: {error}",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
