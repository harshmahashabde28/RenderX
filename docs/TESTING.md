# Verification

## Automated checks

From the project root, install the packages in `requirements.txt`, then run:

```powershell
python -m compileall -q main.py renderx tests
$env:SDL_VIDEODRIVER = 'dummy'
python -m unittest discover -s tests
```

The automated suite covers renderer math, clipping, input routing, maze
progression, challenge interaction, window mapping, theme settings, shooter
rules, entity movement, score persistence, and the shooter launch screen.

## Desktop check

Run `python main.py` on a machine with an OpenGL 3.3 compatible graphics device.
Check that Breakpoint opens, start a run, move and aim, fire, pause and resume,
resize the game window, and return to RenderX. Use the other tabs to inspect the
renderer, challenges, and maze campaign. This check exercises the actual GPU
context and cannot be replaced by the headless test suite.
