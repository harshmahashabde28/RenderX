"""Exercise renderer, projection, and OBJ boundary cases under SDL dummy."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import sys
import tempfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
repository_root = Path(__file__).resolve().parents[2]
if str(repository_root) not in sys.path:
    sys.path.insert(0, str(repository_root))

import pygame

from renderx.app import load_sample
from renderx.camera import Camera
from renderx.core.mesh import Mesh
from renderx.core.projection import project_orthographic, project_point
from renderx.engine.renderer import draw_wireframe
from renderx.engine.styles import RenderStyle
from renderx.models import make_cube
from renderx.obj_loader import load_obj
from renderx.scene import Scene


def main():
    pygame.init()
    pygame.display.set_mode((820, 740))
    surface = pygame.Surface((820, 740))
    camera = Camera()
    scene = Scene(angles=(0.0, 0.0, 0.0), position=(0.0, 0.0, 0.0))
    results = []

    def check(label, passed):
        if not passed:
            raise AssertionError(label)
        results.append(label)

    check("zero and negative depths are rejected",
        project_point((1.0, 1.0, 0.0), near_depth=0.0) is None and
        project_point((1.0, 1.0, -0.5), near_depth=-1.0) is None and
        project_orthographic((1.0, 1.0, 0.0), near_depth=0.0) is None)
    check("positive near-plane boundary remains projectable after clipping",
          project_point((1.0, 1.0, 0.1), near_depth=0.1) is not None)
    check("non-finite and overflowing projections are rejected",
        project_point((math.nan, 0.0, 1.0)) is None and
        project_point((1e308, 0.0, 0.1)) is None and
        project_orthographic((1e308, 0.0, 1.0)) is None and
        project_point((1.0, 1.0, 1.0), focal_length=math.inf) is None)

    crossing = Mesh([(0.0, 0.0, 0.0), (0.5, 0.5, 1.0)], [(0, 1)])
    drawn = draw_wireframe(surface, crossing, scene, camera, clear=True,
                           show_vertices=False, viewport=pygame.Rect(0, 0, 820, 740))
    check("edge crossing near plane is retained", drawn == 1)

    point_mesh = Mesh([(0.0, 0.0, 5.0)], [])
    point_count = draw_wireframe(surface, point_mesh, scene, camera,
                                 show_vertices=False)
    check("single-vertex mesh renders without edges", point_count == 0)
    check("empty mesh is rejected with a clear validation error",
          _expect_value_error(lambda: Mesh([], [])))

    duplicate = Mesh([(0.0, 0.0, 5.0), (1.0, 0.0, 5.0),
                       (1.0, 0.0, 5.0)], [(0, 1), (1, 2)])
    draw_wireframe(surface, duplicate, scene, camera, show_vertices=False)
    check("duplicate-position vertices remain renderable", True)

    flat = Mesh([(-1.0, 0.0, 5.0), (0.0, 0.0, 5.0),
                 (1.0, 0.0, 5.0)], [(0, 1), (1, 2), (2, 0)],
                faces=[[0, 1, 2]])
    draw_wireframe(surface, flat, scene, camera, show_vertices=False,
                   render_style=RenderStyle.SOLID)
    check("zero-area face stays stable in solid rendering", True)

    extreme = Mesh([(1e308, 0.0, 5.0), (1e308, 1.0, 6.0)], [(0, 1)])
    draw_wireframe(surface, extreme, scene, camera, show_vertices=False)
    check("huge finite model coordinates do not escape the viewport", True)

    with tempfile.TemporaryDirectory(prefix="renderx-obj-qa-") as temporary:
        root = Path(temporary)
        invalid = root / "invalid.obj"
        for contents in ("", "v 0 0 0\n", "v nan 0 0\nf 1 1 1\n",
                         "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 99\n"):
            invalid.write_text(contents, encoding="utf-8")
            _expect_value_error(lambda: load_obj(invalid))
        check("empty, invalid, and out-of-range OBJ files report errors", True)

        oversized = root / "oversized.obj"
        oversized.write_text("#" + "x" * (2_000_001), encoding="utf-8")
        _expect_value_error(lambda: load_obj(oversized))
        check("oversized OBJ is rejected", True)

        models = {"Cube": make_cube()}
        active_scene = Scene()
        message = load_sample(active_scene, models, invalid)
        check("failed OBJ import keeps the active model and reports a message",
              message.startswith("OBJ load failed:") and
              active_scene.shape == "Cube" and set(models) == {"Cube"})

    print(json.dumps({"status": "passed", "checks": results}, indent=2))
    pygame.quit()


def _expect_value_error(function):
    try:
        function()
    except ValueError:
        return True
    raise AssertionError("expected a clear ValueError")


if __name__ == "__main__":
    main()
