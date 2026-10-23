# RenderX Milestone 04 evidence source

This folder contains the files used to capture the report evidence and build the two PDFs.

## Files

- `capture_screenshots.py` runs the real RenderX headless app scenarios and saves their raw screenshots.
- `screenshots/` contains current app captures and a small number of clearly labeled historical reference captures.
- `screenshot_manifest.json` records the source and purpose of each image.
- `runs/` contains the event schedules and runner outputs used during capture.
- `fixtures/oversized.obj` is a generated malformed-size input used to show the safe rejection message.
- `build_report.py` creates the charts, the report PDF, and the viva sheet from repository source and this evidence.
- `chart-*.png` are the generated charts.
- `rendered_pdf/` contains page images rendered from the final PDFs for visual inspection.

## Rebuild

Run from the repository root in PowerShell. The project virtual environment supplies Pygame and pytest. Report generation requires ReportLab and Pillow; use the bundled workspace Python runtime if it is available.

```powershell
$env:LOCALAPPDATA = Join-Path $env:TEMP 'renderx-m04-test-local'
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tools\qa\engine_edges.py
.\.venv\Scripts\python.exe tools\qa\resize_matrix.py <temporary-output-folder>
.\.venv\Scripts\python.exe tools\qa\performance_runs.py --seconds 5
.\.venv\Scripts\python.exe output\milestone_04\source\capture_screenshots.py
python output\milestone_04\source\build_report.py
```

The report's measured results are from the captured 23 October 2026 run. The screenshots from historic dates are not newly reproduced and are marked as historical in the manifest and report. The current screenshot runner uses SDL's dummy video driver, so it cannot confirm native Windows cursor appearance, the native file chooser, or live OpenGL Breakpoint gameplay.
