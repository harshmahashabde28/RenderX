"""Capture report evidence from RenderX's real headless application loop."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent
SCREENSHOTS = SOURCE / "screenshots"
RUNS = SOURCE / "runs"
FIXTURES = SOURCE / "fixtures"
RUNNER = ROOT / "tools" / "qa" / "headless_runner.py"


def main() -> None:
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    RUNS.mkdir(parents=True, exist_ok=True)
    FIXTURES.mkdir(parents=True, exist_ok=True)

    oversized = FIXTURES / "oversized.obj"
    oversized.write_bytes(b"#" * 2_000_100 + b"\n")
    house = ROOT / "assets" / "models" / "house.obj"
    manifest = []

    cases = [
        ("landing-current", "1360x900", None, [], 2),
        ("explore-cube", "1360x900", "explore", [], 2),
        ("explore-house-loaded", "1360x900", "explore", [
            {"frame": 1, "events": [{"type": "drop_file", "file": str(house)}]}], 1),
        ("explore-oversized-obj-error", "1360x900", "explore", [
            {"frame": 1, "events": [{"type": "drop_file", "file": str(oversized)}]}], 1),
        ("explore-file-menu", "1360x900", "explore", [
            {"frame": 1, "events": [{"type": "click_action",
                                      "action": ["toolbar_open_obj"]}]}], 1),
        ("explore-shortcuts", "1360x900", "explore", [
            {"frame": 1, "events": [{"type": "key_down", "key": "f1"}]}], 1),
        ("explore-torus-status", "1360x900", "explore", [
            {"frame": 1, "events": [{"type": "click_action",
                                      "action": ["shape", "Torus"]}]}], 2),
        ("explore-light-theme", "1360x900", "explore", [
            {"frame": 1, "events": [{"type": "click_action",
                                      "action": ["theme"]}]}], 2),
        ("preferences", "1360x900", "explore", [
            {"frame": 1, "events": [{"type": "click_action",
                                      "action": ["toolbar_open_obj"]}]},
            {"frame": 2, "events": [{"type": "click_action",
                                      "action": ["file_menu", "preferences"]}]}], 2),
        ("viewport-context-menu", "1360x900", "explore", [
            {"frame": 1, "events": [{"type": "mouse_down", "button": 3,
                                      "pos": [600, 400]}]},
            {"frame": 2, "events": [{"type": "mouse_up", "button": 3,
                                      "pos": [600, 400]}]}], 2),
        ("challenges", "1360x900", "challenge", [], 2),
        ("maze", "1360x900", "maze", [], 2),
        ("shooter", "1360x900", "shooter", [], 2),
        ("explore-small-1024x640", "1360x900", "explore", [
            {"frame": 1, "events": [{"type": "resize", "size": [1024, 640]}]}], 2),
        ("explore-large-1920x1080", "1360x900", "explore", [
            {"frame": 1, "events": [{"type": "resize", "size": [1920, 1080]}]}], 2),
    ]

    for name, size, mode, schedule, capture_frame in cases:
        run_dir = RUNS / name
        if run_dir.exists():
            shutil.rmtree(run_dir)
        settings_path = run_dir / "state" / "RenderX" / "settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps({"theme": "dark",
                                             "welcome_seen": True}),
                                 encoding="utf-8")
        command = [sys.executable, str(RUNNER), "--initial", size,
                   "--frames", str(capture_frame + 1), "--capture",
                   str(capture_frame), "--output", str(run_dir)]
        if mode:
            command.extend(("--mode", mode))
        if schedule:
            event_path = run_dir.with_suffix(".json")
            event_path.write_text(json.dumps(schedule, indent=2), encoding="utf-8")
            command.extend(("--events", str(event_path)))
        completed = subprocess.run(command, cwd=ROOT, check=False)
        summary_path = run_dir / "summary.json"
        if completed.returncode or not summary_path.exists():
            raise RuntimeError(f"RenderX capture failed: {name}")
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if summary.get("status") != "passed":
            raise RuntimeError(f"RenderX capture failed: {name}: {summary}")
        source_image = run_dir / "frame-000001.png"
        source_image = run_dir / f"frame-{capture_frame:06d}.png"
        target_image = SCREENSHOTS / f"{name}.png"
        shutil.copy2(source_image, target_image)
        import pygame
        pygame.init()
        image_size = pygame.image.load(str(target_image)).get_size()
        pygame.quit()
        manifest.append({"name": name, "image": target_image.name,
                         "mode": summary.get("destination"),
                         "size": list(image_size),
                         "status": summary.get("status"),
                         "source_run": str(run_dir)})

    # These are genuine supplied/project screenshots used only as history;
    # the copies keep the source package self-contained.
    historic = {
        "historical-status-bug-before.png": ROOT / "screenshots" /
        "renderx_2026-10-21_18-39-39.png",
        "historical-shooter-first.png": ROOT / "screenshots" /
        "renderx_2026-10-21_18-39-27.png",
        "landing-checkbox-before.png": Path(
            r"C:\Users\darkh\AppData\Local\Temp\codex-clipboard-75d317e2-4726-4393-b391-1a423b197fff.png"),
    }
    for target, source in historic.items():
        if source.is_file():
            shutil.copy2(source, SCREENSHOTS / target)
            manifest.append({"name": target, "image": target,
                             "mode": "historical reference",
                             "size": None, "status": "provided screenshot",
                             "source_run": str(source)})

    # A zoomed crop is taken from the actual current app capture.
    import pygame
    pygame.init()
    image = pygame.image.load(str(SCREENSHOTS / "explore-cube.png"))
    width = image.get_width()
    crop = image.subsurface(pygame.Rect(0, 0, width, min(100, image.get_height())))
    zoomed = pygame.transform.scale(crop, (width * 2, crop.get_height() * 2))
    pygame.image.save(zoomed, str(SCREENSHOTS / "explore-toolbar-zoom.png"))
    pygame.quit()
    manifest.append({"name": "explore-toolbar-zoom",
                     "image": "explore-toolbar-zoom.png",
                     "mode": "cropped and enlarged from explore-cube",
                     "size": [zoomed.get_width(), zoomed.get_height()],
                     "status": "derived from real app screenshot",
                     "source_run": "explore-cube.png"})

    (SOURCE / "screenshot_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
