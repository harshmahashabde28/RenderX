"""Headless benchmarking tool for RenderX software rendering engine.

Measures real vertex transformation throughput (pure Python vs NumPy)
and real frame render times on simulated scenes.
Run with: python tools/benchmark.py
"""
import os
import sys
from pathlib import Path
import time
import platform

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame
from renderx.core.camera import Camera
from renderx.core.scene import Scene
from renderx.core.models import make_cube
from renderx.core.shapes import sphere, torus
from renderx.core.mesh import Mesh
from renderx.engine.renderer import draw_wireframe, VIEWPORT
from renderx.engine.fast_math import (
    has_numpy,
    batch_transform_pure,
    batch_transform_numpy,
)
from renderx.engine.styles import RenderStyle


def benchmark_math(iterations: int = 1000):
    print("=" * 60)
    print("1. MATHEMATICAL TRANSFORMATION BENCHMARK")
    print("=" * 60)
    mesh = torus(radius=1.5, tube=0.5, segments=32, rings=16)
    vertices = mesh.vertices
    vertex_count = len(vertices)
    print(f"Test Mesh: Torus ({vertex_count} vertices, {len(mesh.edges)} edges)")
    print(f"Iterations: {iterations} full batch transformations")

    angles = (0.35, 0.72, 0.15)
    pos = (1.2, -0.8, 6.5)
    scale = 1.3

    # Pure Python
    t0 = time.perf_counter()
    for _ in range(iterations):
        batch_transform_pure(vertices, scale, angles, pos)
    pure_time = time.perf_counter() - t0
    pure_rate = (iterations * vertex_count) / pure_time

    print(f"Pure-Python Reference: {pure_time:.4f} s | {pure_rate:,.0f} vertices/sec")

    # NumPy (if available)
    if has_numpy():
        t0 = time.perf_counter()
        for _ in range(iterations):
            batch_transform_numpy(vertices, scale, angles, pos)
        numpy_time = time.perf_counter() - t0
        numpy_rate = (iterations * vertex_count) / numpy_time
        speedup = pure_time / numpy_time
        print(f"NumPy Vectorized Fast Path: {numpy_time:.4f} s | {numpy_rate:,.0f} vertices/sec")
        print(f"NumPy Speedup: {speedup:.2f}x faster")
    else:
        print("NumPy not available in environment.")


def benchmark_rendering(frames: int = 500):
    print("\n" + "=" * 60)
    print("2. SOFTWARE RENDERER BENCHMARK (HEADLESS)")
    print("=" * 60)
    pygame.init()
    surface = pygame.Surface((1360, 900))
    camera = Camera((0.0, 0.0, 0.0))
    scene = Scene(position=(0.0, 0.0, 6.0), scale=1.5)

    # Test 1: Single Complex Mesh (Sphere)
    mesh_sphere = sphere(radius=1.2, segments=24, rings=16)
    edge_count = len(mesh_sphere.edges)

    frame_times = []
    for _ in range(frames):
        scene.rotate(0.01, 0.015, 0.005)
        t0 = time.perf_counter()
        draw_wireframe(surface, mesh_sphere, scene, camera, clear=True)
        frame_times.append((time.perf_counter() - t0) * 1000.0)

    avg_ms = sum(frame_times) / len(frame_times)
    min_ms = min(frame_times)
    max_ms = max(frame_times)
    fps = 1000.0 / avg_ms if avg_ms > 0 else 999.0

    print(f"Scene: Rotating Sphere ({len(mesh_sphere.vertices)} vertices, {edge_count} edges)")
    print(f"Frames: {frames}")
    print(f"Average frame time: {avg_ms:.2f} ms ({fps:.1f} FPS)")
    print(f"Min: {min_ms:.2f} ms | Max: {max_ms:.2f} ms")

    # Test 2: Simulated Dungeon Scene (~3,000 edges)
    # Combine multiple meshes into a large composite mesh
    cube = make_cube()
    combined_vertices = []
    combined_edges = []
    v_offset = 0
    # Create 250 cubes distributed in space -> 250 * 12 = 3,000 edges
    for i in range(-5, 5):
        for j in range(-5, 5):
            ox, oz = i * 4.0, j * 4.0 + 15.0
            for vx, vy, vz in cube.vertices:
                combined_vertices.append((vx + ox, vy, vz + oz))
            for ea, eb in cube.edges:
                combined_edges.append((ea + v_offset, eb + v_offset))
            v_offset += len(cube.vertices)

    dungeon_mesh = Mesh(combined_vertices, combined_edges)
    total_edges = len(dungeon_mesh.edges)
    print(f"\nScene: Dungeon Corridor Grid ({len(dungeon_mesh.vertices)} vertices, {total_edges} edges)")

    dungeon_times = []
    for _ in range(frames):
        camera.position = (camera.position[0], camera.position[1], camera.position[2] + 0.05)
        t0 = time.perf_counter()
        drawn = draw_wireframe(
            surface,
            dungeon_mesh,
            scene,
            camera,
            clear=True,
            show_vertices=False,
            render_style=RenderStyle.DEPTH_FADE,
        )
        dungeon_times.append((time.perf_counter() - t0) * 1000.0)

    avg_ms = sum(dungeon_times) / len(dungeon_times)
    min_ms = min(dungeon_times)
    max_ms = max(dungeon_times)
    fps = 1000.0 / avg_ms if avg_ms > 0 else 999.0

    print(f"Frames: {frames}")
    print(f"Visible Edges Drawn: ~{drawn}")
    print(f"Average frame time: {avg_ms:.2f} ms ({fps:.1f} FPS)")
    print(f"Min: {min_ms:.2f} ms | Max: {max_ms:.2f} ms")
    print(f"Target FPS budget: >= 30 FPS -> RESULT: {'PASS' if fps >= 30 else 'FAIL'}")
    pygame.quit()


def main():
    print(f"RenderX Benchmark Tool | System: {platform.system()} {platform.machine()} | Python {platform.python_version()}")
    benchmark_math(1000)
    benchmark_rendering(300)


if __name__ == "__main__":
    main()
