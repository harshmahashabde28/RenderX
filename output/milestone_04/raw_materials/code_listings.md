# Appendix E - Code listings and source excerpts

The excerpts below are copied from the stated source locations. `...` means lines were intentionally omitted. Verify line numbers again if the source changes.

## Listing 1 — OBJ polygon parsing test

`tests/test_extensions.py`, lines 78–85

```python
    def test_polygon_closure_unique_edges_and_normalization(self):
        text = "v 10 20 0\nv 14 20 0\nv 14 24 0\nv 10 24 0\n"
        mesh = self.load_text(text + "f 1 2 3 4\nf 4 3 2 1\n")
        self.assertEqual(mesh.edges, [(0, 1), (0, 3), (1, 2), (2, 3)])
        for actual, expected in [(mesh.vertices[0], (-1, -1, 0)),
                                 (mesh.vertices[2], (1, 1, 0))]:
            for value, target in zip(actual, expected):
                self.assertAlmostEqual(value, target)
```

This test checks that a quad becomes four unique boundary edges and its coordinates are normalized.

## Listing 2 — icon drawing stays inside its button

`tests/test_launch_flow.py`, lines 176–194

```python
    def test_every_svg_and_mesh_icon_is_safe_at_small_and_large_sizes(self):
        icon_names = [path.stem for path in icons._ASSET_DIRECTORY.glob("*.svg")]
        icon_names.extend(f"shape:{name}" for name in make_library())
        icon_names.append("brand")
        for name in icon_names:
            for side in (12, 16, 20, 24, 32):
                target = pygame.Surface((side + 32, side + 32), pygame.SRCALPHA)
                rect = pygame.Rect(16, 16, side, side)
                icons.draw_icon(target, name, rect, (245, 245, 245))
                pixels = target.get_bounding_rect(min_alpha=1)
                self.assertFalse(pixels.colliderect(pygame.Rect(0, 0, 16, 16)))
                self.assertGreaterEqual(pixels.left - rect.left, 1, (name, side))
                self.assertGreaterEqual(pixels.top - rect.top, 1, (name, side))
                self.assertGreaterEqual(rect.right - pixels.right, 1, (name, side))
                self.assertGreaterEqual(rect.bottom - pixels.bottom, 1, (name, side))
                self.assertLessEqual(abs(pixels.centerx - rect.centerx), 1,
                                     (name, side, pixels, rect))
                self.assertLessEqual(abs(pixels.centery - rect.centery), 1,
                                     (name, side, pixels, rect))
```

## Listing 3 — OBJ loader size and error handling

`renderx/core/obj_loader.py`, lines 42–47 and 84–89

```python
    with Path(path).open("r", encoding="utf-8-sig") as source:
        text = source.read(MAX_FILE_BYTES + 1)
    if len(text.encode("utf-8")) > MAX_FILE_BYTES:
        raise ValueError("OBJ exceeds the 2 MB educational loader limit.")
    vertices, faces = [], []
    ignored = set()
    for line_number, line in enumerate(text.splitlines(), 1):
        fields = line.split("#", 1)[0].split()
        if not fields:
            continue
        ...
        except ValueError as error:
            raise ValueError(f"OBJ line {line_number}: {error}") from error
    if not vertices or not faces:
        raise ValueError("OBJ needs vertices and at least one polygon face.")
```

## Listing 4 — current shared icon placement

`renderx/ui/components/button.py`, lines 8–30

```python
def icon_button_rect(rect, label, icon, *, align="center"):
    """Return the shared safe icon placement for a real button rectangle.

    Center-aligned icon buttons use a centered mark when the label cannot fit.
    Wider buttons center the icon and label as one group; left-aligned buttons
    retain a consistent leading inset.
    """
    rect = pygame.Rect(rect)
    size = min(theme.METRICS["icon_medium"] if icon.startswith("shape:")
               else theme.METRICS["icon_small"], max(1, rect.height - 8))
    size = max(1, size)
    padding = theme.SPACE["md"]
    gap = theme.SPACE["sm"]
    label_width = fonts.font("control").size(str(label))[0]
    group_width = size + gap + label_width
    can_fit_group = group_width <= rect.width - padding * 2
    if align == "center" and can_fit_group:
        left = rect.centerx - group_width // 2
    elif align == "center" or not can_fit_group:
        left = rect.centerx - size // 2
    else:
        left = rect.x + padding
    return pygame.Rect(left, rect.centery - size // 2, size, size)
```

## Listing 5 — earlier icon placement from local history

`renderx/ui/components/button.py`, commit `98354b3`, lines 29–37 (approximate)

```python
    content = rect.inflate(-theme.SPACE["md"] * 2, 0)
    if icon:
        size = min(theme.METRICS["icon_small"], content.height)
        icon_rect = pygame.Rect(content.x, content.centery - size // 2, size, size)
        icons.draw_icon(surface, icon, icon_rect, label_color)
        content.x += size + theme.SPACE["sm"]
    if shortcut:
        hint_width = fonts.font("micro").size(shortcut)[0]
        ...
```

This historical code placed the icon at the content's leading edge and always reserved label room. The later shared helper adds fit-aware centering and safe inset behavior. This excerpt is from local history, not the public GitHub baseline.

## Listing 6 — opening an OBJ updates scene, model library, and recent list

`tests/test_file_open.py`, lines 20–31

```python
    def test_open_obj_adds_selects_and_remembers_mesh(self):
        scene, models = Scene(), make_library()
        with tempfile.TemporaryDirectory() as temporary:
            settings = Path(temporary) / "settings.json"
            with patch("renderx.theme._SETTING", settings), \
                    patch("renderx.theme._recent_files", []):
                result = load_obj_file(SAMPLE_OBJ, scene, models)
                self.assertEqual(result, "Opened house.obj")
                self.assertEqual(scene.shape, "house")
                self.assertIn("house", models)
                self.assertEqual(json.loads(settings.read_text())["recent_files"],
                                 [str(SAMPLE_OBJ.resolve())])
```

## Listing 7 — test commands

Current project evidence instructions, run from the repository root in PowerShell:

```powershell
$env:LOCALAPPDATA = Join-Path $env:TEMP 'renderx-m04-test-local'
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tools\qa\engine_edges.py
.\.venv\Scripts\python.exe tools\qa\resize_matrix.py <temporary-output-folder>
.\.venv\Scripts\python.exe tools\qa\performance_runs.py --seconds 5 --output <temporary-output-folder>
.\.venv\Scripts\python.exe output\milestone_04\source\capture_screenshots.py
```
