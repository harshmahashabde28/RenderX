"""Run the requested viewport resize matrix through the real app loop."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame


def main():
    repo = Path(__file__).resolve().parents[2]
    qa = Path(__file__).parent
    output = (Path(sys.argv[1]) if len(sys.argv) > 1 else
              Path("tools/qa/output/resize-matrix")).resolve()
    output.mkdir(parents=True, exist_ok=True)
    sizes = [(800, 500), (1024, 640), (1280, 720), (1366, 768),
             (1920, 1080), (2560, 1440), (1024, 1600), (2200, 720)]
    schedule = [{"frame": 1 + index * 2,
                 "events": [{"type": "resize", "size": list(size)}]}
                for index, size in enumerate(sizes)]
    schedule.extend(
        {"frame": 20 + index,
         "events": [{"type": "resize", "size": list(
             (1024, 640) if index % 2 == 0 else (1920, 1080))}]}
        for index in range(50)
    )
    event_path = output / "events.json"
    event_path.write_text(json.dumps(schedule, indent=2), encoding="utf-8")
    capture_frames = [2, 4, 6, 8, 10, 12, 14, 16, 20, 30, 40, 50, 60, 70, 80]
    run_output = output / "run"
    command = [sys.executable, "-W", "error::DeprecationWarning",
               str(qa / "headless_runner.py"), "--frames", "90",
               "--capture", ",".join(map(str, capture_frames)),
               "--events", str(event_path), "--output", str(run_output),
               "--expect-display-size", "1920x1080", "--expect-window-icon"]
    completed = subprocess.run(command, cwd=repo, check=False)

    expected_sizes = {
        2: (1024, 640), 4: (1024, 640), 6: (1280, 720), 8: (1366, 768),
        10: (1920, 1080), 12: (2560, 1440), 14: (1024, 1600),
        16: (2200, 720),
    }
    observed = {}
    for frame, expected in expected_sizes.items():
        path = run_output / f"frame-{frame:06d}.png"
        actual = pygame.image.load(path).get_size()
        observed[frame] = {"actual": actual, "expected": expected,
                           "passed": actual == expected}
    summary = json.loads((run_output / "summary.json").read_text(encoding="utf-8"))
    report = {"runner_status": summary["status"], "resize_snapshots": observed,
              "rapid_resize_events": 50,
              "all_snapshots_passed": all(item["passed"] for item in observed.values())}
    (output / "matrix-summary.json").write_text(json.dumps(report, indent=2),
                                                 encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if completed.returncode == 0 and report["all_snapshots_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
