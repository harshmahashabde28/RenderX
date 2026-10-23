"""Measure idle, orbiting, and largest-mesh draws over paced intervals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=60.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[2]
    runner = Path(__file__).with_name("headless_runner.py")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    frames = max(1, round(args.seconds * 60))
    results = {}
    for scenario in ("idle", "orbit", "largest"):
        run_dir = output / scenario
        command = [sys.executable, "-W", "error::DeprecationWarning", str(runner),
                   "--scenario", scenario, "--frames", str(frames),
                   "--capture", "", "--pace", "--audit-memory",
                   "--output", str(run_dir)]
        completed = subprocess.run(command, cwd=repo, check=False)
        summary_path = run_dir / "summary.json"
        if not summary_path.exists():
            results[scenario] = {"status": "error", "error": "Runner produced no summary"}
        else:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            results[scenario] = {
                "status": summary.get("status"),
                "error": summary.get("error"),
                "requested_seconds": args.seconds,
                "simulated_seconds": summary.get("simulated_seconds"),
                "wall_seconds": summary.get("wall_seconds"),
                "measured_frames": summary.get("measured_frames"),
                "frame_ms_avg": summary.get("frame_ms_avg"),
                "frame_ms_p95": summary.get("frame_ms_p95"),
                "frame_ms_p99": summary.get("frame_ms_p99"),
                "memory_audit": summary.get("memory_audit"),
                "draw_ms_avg": summary.get("draw_ms_avg"),
                "draw_ms_p95": summary.get("draw_ms_p95"),
                "draw_ms_p99": summary.get("draw_ms_p99"),
                "draw_calls": summary.get("draw_calls"),
            }
        print(json.dumps({scenario: results[scenario]}, sort_keys=True), flush=True)
        if completed.returncode or results[scenario]["status"] != "passed":
            break

    report = {
        "requested_seconds_per_scenario": args.seconds,
        "timing_scope": "App loop from clock tick return through display flip; separate Dashboard.draw timings are also reported",
        "results": results,
        "all_passed": len(results) == 3 and all(
            result.get("status") == "passed" for result in results.values()),
    }
    (output / "performance-summary.json").write_text(json.dumps(report, indent=2),
                                                       encoding="utf-8")
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
