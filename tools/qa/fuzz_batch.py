"""Run long, reproducible event-fuzz sessions in fresh RenderX processes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", default="0,1,2,3,4,5,6,7,8,9")
    parser.add_argument("--minutes", type=float, default=3.0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pace", action="store_true",
                        help="run each seed for the requested wall-clock duration")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[2]
    runner = Path(__file__).with_name("headless_runner.py")
    frames = max(1, round(args.minutes * 60 * 60))
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for seed in (int(value.strip()) for value in args.seeds.split(",") if value.strip()):
        run_dir = output / f"seed-{seed}"
        command = [sys.executable, "-W", "error::DeprecationWarning", str(runner),
                   "--frames", str(frames), "--fuzz-seed", str(seed),
                   "--capture", "", "--audit-memory", "--output", str(run_dir)]
        if args.pace:
            command.append("--pace")
        completed = subprocess.run(command, cwd=repo, check=False)
        summary_path = run_dir / "summary.json"
        summary = (json.loads(summary_path.read_text(encoding="utf-8"))
                   if summary_path.exists() else
                   {"status": "error", "error": "Runner produced no summary"})
        summary["seed"] = seed
        results.append(summary)
        print(json.dumps(summary, sort_keys=True), flush=True)
        if completed.returncode or summary.get("status") != "passed":
            break
    report = {
        "requested_seeds": [int(value.strip()) for value in args.seeds.split(",")
                            if value.strip()],
        "minutes_per_seed": args.minutes,
        "wall_clock_paced": args.pace,
        "results": results,
        "all_passed": len(results) == len([value for value in args.seeds.split(",")
                                           if value.strip()]) and all(
            result.get("status") == "passed" for result in results),
    }
    (output / "batch-summary.json").write_text(json.dumps(report, indent=2),
                                                encoding="utf-8")
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
