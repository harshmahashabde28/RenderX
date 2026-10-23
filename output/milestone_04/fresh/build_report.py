from __future__ import annotations

import ast
import html
import subprocess
from pathlib import Path

from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, PageBreak, PageTemplate, Paragraph, Spacer,
    Table, TableStyle, XPreformatted,
)


ROOT = Path(__file__).resolve().parents[3]
MILESTONE = ROOT / "output" / "milestone_04"
PHOTOS = MILESTONE / "raw_materials" / "photos"
EVIDENCE = MILESTONE / "fresh" / "evidence"
CHARTS = MILESTONE / "fresh" / "charts"
OUTPUT = ROOT / "output" / "pdf" / "RenderX_Milestone_04_Testing_and_Validation.pdf"
CHARTS.mkdir(parents=True, exist_ok=True)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

PAGE_W, PAGE_H = A4
LEFT = RIGHT = 17 * mm
TOP = 20 * mm
BOTTOM = 16 * mm
BODY_W = PAGE_W - LEFT - RIGHT

NAVY = colors.HexColor("#21364B")
TEAL = colors.HexColor("#008C9B")
MINT = colors.HexColor("#63C9B3")
PALE = colors.HexColor("#EDF6F7")
PAPER = colors.HexColor("#F8FBFC")
LINE = colors.HexColor("#CBD9DF")
BODY = colors.HexColor("#243847")
MUTED = colors.HexColor("#657681")
WHITE = colors.white

FONT_DIR = ROOT / "assets" / "fonts"
pdfmetrics.registerFont(TTFont("Inter", str(FONT_DIR / "Inter-Variable.ttf")))
pdfmetrics.registerFont(TTFont("PlexMono", str(FONT_DIR / "IBM-Plex-Mono-Regular.ttf")))

styles = {
    "title": ParagraphStyle("Title", fontName="Inter", fontSize=22, leading=27,
                             textColor=NAVY, spaceAfter=3),
    "subtitle": ParagraphStyle("Subtitle", fontName="Inter", fontSize=10.2, leading=14,
                                textColor=MUTED, spaceAfter=13),
    "h1": ParagraphStyle("Section", fontName="Inter", fontSize=15, leading=19,
                          textColor=TEAL, spaceBefore=3, spaceAfter=8,
                          keepWithNext=True),
    "h2": ParagraphStyle("Subsection", fontName="Inter", fontSize=10.5, leading=13,
                          textColor=NAVY, spaceBefore=7, spaceAfter=4,
                          keepWithNext=True),
    "body": ParagraphStyle("Body", fontName="Inter", fontSize=9.2, leading=13,
                            textColor=BODY, spaceAfter=6, allowWidows=0,
                            allowOrphans=0),
    "small": ParagraphStyle("Small", fontName="Inter", fontSize=7.8, leading=10.2,
                             textColor=MUTED, spaceAfter=4),
    "caption": ParagraphStyle("Caption", fontName="Inter", fontSize=7.3, leading=9.2,
                               textColor=MUTED, spaceBefore=3, spaceAfter=5),
    "cell": ParagraphStyle("Cell", fontName="Inter", fontSize=7.4, leading=9.4,
                            textColor=BODY, spaceAfter=0),
    "cellhead": ParagraphStyle("CellHead", fontName="Inter", fontSize=7.4, leading=9.4,
                                textColor=NAVY, spaceAfter=0),
    "code": ParagraphStyle("Code", fontName="PlexMono", fontSize=6.4, leading=8.2,
                            textColor=BODY, leftIndent=3, rightIndent=3,
                            spaceAfter=0),
}


def P(text: str, style: str = "body") -> Paragraph:
    return Paragraph(text, styles[style])


def cell(value, heading: bool = False, font_size: float = 7.4) -> Paragraph:
    if isinstance(value, Paragraph):
        return value
    base = styles["cellhead" if heading else "cell"]
    style = base if font_size == 7.4 else ParagraphStyle(
        f"Cell_{'head' if heading else 'body'}_{font_size}", parent=base,
        fontSize=font_size, leading=font_size + 2.0)
    return Paragraph(html.escape(str(value)), style)


def make_table(rows, widths=None, header=True, font_size=7.4, padding=4):
    data = []
    for row_index, row in enumerate(rows):
        data.append([cell(value, header and row_index == 0, font_size) for value in row])
    if widths is None:
        widths = [BODY_W / len(rows[0])] * len(rows[0])
    table = Table(data, colWidths=widths, repeatRows=1 if header else 0,
                  hAlign="LEFT")
    commands = [
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), padding),
        ("RIGHTPADDING", (0, 0), (-1, -1), padding),
        ("TOPPADDING", (0, 0), (-1, -1), padding),
        ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
    ]
    if header:
        commands.append(("BACKGROUND", (0, 0), (-1, 0), PALE))
    for row_index in range(2 if header else 1, len(rows), 2):
        commands.append(("BACKGROUND", (0, row_index), (-1, row_index), PAPER))
    table.setStyle(TableStyle(commands))
    return table


def section(story, number: int, title: str):
    story.append(P(f"{number}. {html.escape(title)}", "h1"))


def caption(story, number: int, text: str):
    story.append(P(f"Table {number}. {html.escape(text)}", "caption"))


def listing(story, number: int, title: str, source: str, code: str, note: str = ""):
    story.append(P(f"Listing {number}. {html.escape(title)}", "h2"))
    story.append(P(html.escape(source), "small"))
    panel = Table([[XPreformatted(code.rstrip(), styles["code"])]],
                  colWidths=[BODY_W], hAlign="LEFT")
    panel.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("LINEBEFORE", (0, 0), (0, 0), 2, MINT),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([panel, Spacer(1, 4)])
    if note:
        story.append(P(html.escape(note), "small"))


def function_source(path: Path, name: str, max_lines: int = 25) -> tuple[str, int, int]:
    text = path.read_text(encoding="utf-8").splitlines()
    tree = ast.parse("\n".join(text))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            first, last = node.lineno, node.end_lineno or node.lineno
            body = text[first - 1:last]
            if len(body) > max_lines:
                body = body[:max_lines - 1] + ["    # ... remaining lines omitted ..."]
            return "\n".join(body), first, first + len(body) - 1
    raise ValueError(f"Function {name!r} not found in {path}")


def source_range(path: Path, first: int, last: int) -> str:
    return "\n".join(path.read_text(encoding="utf-8").splitlines()[first - 1:last])


def old_icon_source() -> str:
    text = subprocess.check_output(
        ["git", "show", "98354b3:renderx/ui/components/button.py"],
        cwd=ROOT, text=True, encoding="utf-8")
    lines = text.splitlines()
    start = next(index for index, line in enumerate(lines) if "content = rect.inflate" in line)
    return "\n".join(lines[start:start + 9])


def get_font(path, size):
    try:
        return ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def make_bar_chart(path: Path, title: str, items, suffix="", maximum=None):
    width, height = 1100, 460
    image = PILImage.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = get_font(path, 27)
    label_font = get_font(path, 21)
    value_font = get_font(path, 19)
    draw.text((38, 22), title, fill="#21364B", font=title_font)
    maximum = maximum or max(item[1] for item in items)
    left, usable, bar_h, gap = 300, 620, 44, 36
    y = 100
    for label, value, note in items:
        draw.text((36, y + 6), label, fill="#243847", font=label_font)
        bar_w = max(2, int(usable * value / maximum))
        draw.rounded_rectangle((left, y, left + bar_w, y + bar_h), radius=9,
                               fill="#63C9B3")
        draw.text((left + bar_w + 14, y + 5), f"{value:g}{suffix}",
                  fill="#21364B", font=value_font)
        draw.text((left, y + bar_h + 3), note, fill="#657681", font=get_font(path, 15))
        y += bar_h + gap + 22
    image.save(path)


def create_charts():
    make_bar_chart(CHARTS / "tests-by-level.png", "Automated tests: all passed",
                   [("Unit-focused", 49, "49 passed, 0 failed"),
                    ("Integration-focused", 86, "86 passed, 0 failed")],
                   suffix=" tests", maximum=90)
    make_bar_chart(CHARTS / "defects-by-area.png", "Recorded defect entries by area",
                   [("UI", 8, "Fixed and rechecked in recorded paths"),
                    ("Core projection", 2, "Fixed and rechecked"),
                    ("Test isolation", 1, "Fixed; full suite rerun")],
                   suffix="", maximum=8)
    fps = [("Explore idle", 152.3, "6.565 ms mean frame time"),
           ("Explore orbit", 153.6, "6.511 ms mean frame time"),
           ("Largest built-in mesh", 94.0, "10.642 ms mean frame time")]
    make_bar_chart(CHARTS / "performance.png", "Reciprocal of mean headless frame time",
                   fps, suffix=" fps", maximum=165)


class MilestoneDoc(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(filename, pagesize=A4, leftMargin=LEFT, rightMargin=RIGHT,
                         topMargin=TOP, bottomMargin=BOTTOM,
                         title="RenderX | Milestone 04: Testing and Validation",
                         author="RenderX")
        frame = Frame(LEFT, BOTTOM, BODY_W, PAGE_H - TOP - BOTTOM,
                      leftPadding=0, rightPadding=0, topPadding=0,
                      bottomPadding=0, id="body")
        self.addPageTemplates([PageTemplate(id="main", frames=[frame],
                                            onPage=self.draw_page)] )

    @staticmethod
    def draw_page(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(MUTED)
        canvas.setFont("Inter", 8.2)
        canvas.drawString(LEFT, PAGE_H - 11 * mm, "RenderX | Milestone 04")
        canvas.drawRightString(PAGE_W - RIGHT, 9 * mm, str(doc.page))
        canvas.restoreState()


def image_cell(filename: str, number: int, caption_text: str):
    path = PHOTOS / filename
    if not path.exists():
        raise FileNotFoundError(path)
    image = Image(str(path), width=(BODY_W - 8 * mm) / 2, height=54 * mm,
                  kind="proportional", hAlign="CENTER")
    image.hAlign = "CENTER"
    return [image, P(f"Figure {number}. {html.escape(caption_text)}", "caption")]


def gallery_page(story, title: str, images):
    story.append(P(title, "h1"))
    cells = []
    for i in range(0, len(images), 2):
        row = []
        for number, filename, text in images[i:i + 2]:
            row.append(image_cell(filename, number, text))
        if len(row) == 1:
            row.append(P("", "small"))
        cells.append(row)
    grid = Table(cells, colWidths=[BODY_W / 2] * 2, hAlign="LEFT")
    grid.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(grid)


def build_story():
    create_charts()
    story = []

    # Page 1: milestone scope and version change, matching Milestone 02's opening sequence.
    story.extend([Spacer(1, 1 * mm), P("Testing &amp; Validation", "title"),
                  P("Milestone 04 | Checking the current RenderX application", "subtitle")])
    story.append(P("This report follows the project sequence: Milestone 01 set the requirements, Milestone 02 recorded the design and plan, Milestone 03 implemented the Learning Laboratory, and Milestone 04 checks the resulting application. It also explains how the current RenderX grew from the published Learning Laboratory.", "small"))
    section(story, 1, "What RenderX now does")
    story.append(P("RenderX began as a Python and Pygame Learning Laboratory for 3D wireframe graphics. The current version keeps the custom transform, camera, clipping and projection path, then adds a workspace, practical challenges, a three-stage maze and Breakpoint, a separate shooter. This milestone checks the current behavior and records what remains unverified."))
    rows = [
        ["Area", "GitHub Learning Laboratory", "Current RenderX"],
        ["Main use", "Explore and learn renderer steps through lessons, comparisons and a guided demo.", "Explore meshes and complete three challenges, a wireframe maze campaign or Breakpoint."],
        ["Renderer", "Custom Python wireframe transform and projection pipeline.", "Retains the custom pipeline; adds hidden-line, solid and depth-oriented software modes."],
        ["Models and files", "Procedural teaching shapes and sample models.", "Adds bounded OBJ import, recent files, readable errors and showcase models."],
        ["Validation", "Published README reports 86 tests; this is a claim in the old README, not a rerun here.", "Current automated suite: 135 tests passed. Focused edge, resize, scenario and performance checks are also recorded below."],
    ]
    story.append(make_table(rows, [24 * mm, 72 * mm, BODY_W - 96 * mm]))
    caption(story, 1, "Summary of the change from the published Learning Laboratory to the current application.")
    story.append(P("The comparison uses GitHub main at 972266d (25 Sep 2026) and the current application snapshot at d34e273 (23 Oct 2026). Their Git histories are unrelated, so this is a source and feature comparison, not a single commit chain.", "small"))
    story.append(P("The tree comparison counted 423 changed paths, including source, archived files, assets, screenshots and evidence. That is not a count of 423 user features.", "small"))
    story.append(PageBreak())

    # Page 2: architecture.
    section(story, 2, "System architecture")
    story.append(P("The Explore, Challenges and Maze screens share the Python renderer. For a frame, the app reads input, updates the scene, transforms mesh points, clips edges near the camera, projects visible points and draws them with Pygame. Breakpoint runs in a separate OpenGL 3.3 window."))
    arch_rows = [
        ["Input and pages", "Scene and model", "3D pipeline", "Display"],
        ["Pygame events; Explore, Challenges, Maze", "Vertices, edges, transforms, selected OBJ", "Transform, camera, clip, project", "Software wireframe and raster styles"],
    ]
    arch = make_table(arch_rows, [BODY_W * .23, BODY_W * .23, BODY_W * .27, BODY_W * .27], padding=8)
    story.extend([arch, Spacer(1, 5), P("Figure 1. RenderX software rendering path", "caption")])
    story.append(P("Breakpoint uses its own OpenGL models, shaders and HUD. Its real graphics window cannot be created by the SDL dummy display used for the automated app screenshots.", "small"))
    rows = [
        ["Part", "Responsibility", "Example source"],
        ["Main UI", "Landing, navigation, panels, preferences and file actions.", "renderx/dashboard.py; renderx/ui/"],
        ["Geometry and renderer", "Mesh data, transforms, camera, clipping, projection and drawing.", "renderx/core/; renderx/engine/"],
        ["OBJ loader", "Reads a bounded subset of vertices and polygon faces.", "renderx/core/obj_loader.py"],
        ["Maze and challenges", "Campaign state and renderer-based exercises.", "renderx/maze.py; renderx/quest.py"],
        ["Breakpoint", "Separate OpenGL shooter and game state.", "renderx/shooter/"],
    ]
    story.append(make_table(rows, [33 * mm, 83 * mm, BODY_W - 116 * mm]))
    caption(story, 2, "Main application parts included in the validation scope.")
    # Page 3: technology and actual measurement environment.
    section(story, 3, "Technology stack and test environment")
    story.append(P("The test run used the project virtual environment and SDL's dummy video driver for automated window checks. This lets the app loop run without a visible desktop window; it does not reproduce a GPU display or native Windows dialogs."))
    rows = [
        ["Item", "Observed or required value"],
        ["Operating system", "Windows 11, build 10.0.26300"],
        ["Python", "3.13.15 (project supports Python 3.10 and later)"],
        ["Pygame", "2.6.1"],
        ["Test runner", "Python unittest discovery; 135 test methods in the full run"],
        ["Window sizes", "800x500, 1024x640, 1280x720, 1366x768, 1920x1080, 2560x1440, 1024x1600 and 2200x720"],
        ["Shooter requirement", "A graphics device with OpenGL 3.3 support for interactive Breakpoint gameplay"],
        ["Not recorded", "The fresh automated run did not record the GPU model or a native desktop frame rate."],
    ]
    story.append(make_table(rows, [43 * mm, BODY_W - 43 * mm]))
    caption(story, 3, "Software and conditions for the recorded validation run.")
    story.append(P("The system version and Python/Pygame versions were read from the machine used for this report. The window-size values are the sizes requested by the QA runner, not display resolutions supported by every monitor.", "small"))
    story.append(P("The application keeps preferences and best scores in local files. It does not need a database or an account server.", "small"))
    story.append(PageBreak())

    # Page 4: strategy.
    section(story, 4, "Test plan and execution")
    story.append(P("A unit test checks one small function or class. An integration test checks connected parts. A system check drives several parts through a user-like flow. A regression test repeats a check after a fix to make sure the old problem stays fixed."))
    rows = [
        ["Level", "What it checks in RenderX", "How it was run"],
        ["Unit-focused", "Projection, clipping, mesh and OBJ rules, font layout, icon bounds and settings.", "135-test suite, grouped by the test modules' main purpose."],
        ["Integration-focused", "Navigation, file open, saved settings, game state and UI actions.", "Same full test suite; module grouping is described in Appendix A."],
        ["System / headless", "Launch, destinations, file feedback, shortcuts and window resizing.", "Real app loop with scripted input and screenshots."],
        ["Boundary checks", "Zero/negative depth, non-finite values, broken OBJ and oversized OBJ.", "12 focused engine and input checks."],
        ["Performance", "Average frame time and process working set for three Explore scenes.", "Three paced 5-second dummy-display runs."],
    ]
    story.append(make_table(rows, [30 * mm, 81 * mm, BODY_W - 111 * mm]))
    caption(story, 4, "Test levels used for this milestone.")
    story.append(P("The full suite ran with SDL_VIDEODRIVER=dummy and the app settings redirected to a temporary folder. The run finished with 135 tests and no failures. Separate QA results are reported in Sections 6 and 8.", "small"))
    story.append(P("The unit/integration split is a report grouping by test module: six focused modules account for 49 unit-focused tests; the remaining application-flow modules account for 86 integration-focused tests. The full suite was run together.", "small"))
    # Page 5: unit tests.
    section(story, 5, "Unit and integration testing")
    story.append(P("The test suite checks the renderer's math as well as the code that joins the renderer to the desktop interface. The table shows representative checks, not all 135 test methods."))
    rows = [
        ["ID", "Area", "Input or action", "Expected and recorded result"],
        ["UT-01", "Mesh data", "Build built-in shapes and inspect edge indices.", "Valid meshes and expected counts; passed."],
        ["UT-02", "Transform math", "Rotate known points around X, Y and Z.", "Known results and unchanged source geometry; passed."],
        ["UT-03", "Projection", "Compare perspective and orthographic points at two depths.", "Perspective size changes; orthographic size does not; passed."],
        ["UT-04", "Clipping", "Place an edge across the near plane.", "Visible segment remains; behind-camera points are rejected; passed."],
        ["UT-05", "OBJ parser", "Read triangle, quad, face variants and comments.", "Boundary edges are unique and vertices normalize; passed."],
        ["UT-06", "Invalid values", "Try empty, non-finite and out-of-range OBJ data.", "Controlled ValueError; no partial scene change; passed."],
        ["UT-07", "Icon layout", "Draw SVG and mesh icons from 12 to 32 pixels.", "Pixels stay inside the target and remain centered; passed."],
        ["UT-08", "Small text", "Use minimum supported controls and shortcut overlay.", "No clipped binding or unsupported ellipsis; passed."],
    ]
    story.append(make_table(rows, [12 * mm, 25 * mm, 61 * mm, BODY_W - 98 * mm], padding=3))
    caption(story, 5, "Representative unit-focused checks.")
    quad_code, start, end = function_source(ROOT / "tests" / "test_extensions.py",
                                            "test_polygon_closure_unique_edges_and_normalization", 20)
    listing(story, 1, "Quad face becomes four unique edges", "tests/test_extensions.py, lines %d-%d" % (start, end), quad_code,
            "The test also checks that the imported vertices are normalized.")
    story.append(PageBreak())
    # Page 6: integration tests.
    story.append(P("5.1 Integration checks", "h1"))
    story.append(P("Integration testing checks that an action reaches the right part of the app and leaves the rest of the state consistent."))
    rows = [
        ["ID", "Action", "Expected result", "Recorded result"],
        ["IT-01", "Open bundled house.obj.", "Scene selection, model list and recent file update together.", "Passed: tests/test_file_open.py."],
        ["IT-02", "Open a missing or invalid OBJ.", "Readable error; old model and selection remain.", "Passed: tests/test_file_open.py and edge runner."],
        ["IT-03", "Click destination tabs and cycle with Tab.", "Explore, Challenges, Maze and Shooter state follows the active page.", "Passed: dashboard and launch-flow tests."],
        ["IT-04", "Change volume and mute music.", "Preference state persists without overlapping compact controls.", "Passed: audio and dashboard tests; physical playback not covered."],
        ["IT-05", "Collect keys and reach a Maze exit.", "Locked exit opens when objectives are complete.", "Passed: maze movement/state tests."],
        ["IT-06", "Exercise Shooter state and launch failure.", "Rules stay bounded; failed GL launch returns to RenderX.", "Passed in tests; live GPU combat not covered."],
    ]
    story.append(make_table(rows, [12 * mm, 43 * mm, 67 * mm, BODY_W - 122 * mm], padding=3))
    caption(story, 6, "Representative integration checks.")
    file_code, start, end = function_source(ROOT / "tests" / "test_file_open.py",
                                            "test_open_obj_adds_selects_and_remembers_mesh", 20)
    listing(story, 2, "Opening an OBJ updates the scene and recent list",
            f"tests/test_file_open.py, lines {start}-{end}", file_code)
    # Page 7: system and responsive testing.
    section(story, 6, "System testing and regression checks")
    story.append(P("System testing follows the app from launch through its main destinations. The screenshot harness launched the current app, injected scripted events where needed, checked the final state and saved the Pygame display surface."))
    rows = [
        ["Step", "User-like action", "Evidence"],
        ["1", "Launch RenderX.", "Landing screen opens; launch-flow tests check the default route."],
        ["2", "Enter Explore and inspect the built-in model.", "Cube, inspector, scene list and status capture."],
        ["3", "Open a sample OBJ and an oversized OBJ.", "House appears; oversize input shows controlled feedback."],
        ["4", "Open menu, shortcuts, preferences and context actions.", "Captured screens and input-flow tests pass."],
        ["5", "Visit Challenges and Maze; inspect Shooter destination.", "All three page shells are captured; Breakpoint gameplay is not."],
        ["6", "Resize the app and close/return through launch routes.", "Eight sizes and 50 rapid resize events passed."],
    ]
    story.append(make_table(rows, [13 * mm, 73 * mm, BODY_W - 86 * mm], padding=3))
    caption(story, 7, "System-level flow exercised by the app harness.")
    rows = [
        ["800 x 500", "1024 x 640", "1280 x 720", "1366 x 768"],
        ["Pass", "Pass", "Pass", "Pass"],
        ["1920 x 1080", "2560 x 1440", "1024 x 1600", "2200 x 720"],
        ["Pass", "Pass", "Pass", "Pass"],
    ]
    story.append(make_table(rows, [BODY_W / 4] * 4, padding=5))
    caption(story, 8, "Eight requested window sizes; the run also injected 50 rapid resizes.")
    story.append(P("Regression checks repeated navigation, focus-loss handling, file-open errors, icon bounds, tab width, current model status and launch defaults after the relevant fixes. FEATURES.md was used as the current feature checklist.", "small"))
    story.append(PageBreak())

    # Page 8: first part of defect register.
    section(story, 7, "Defects found and fixed")
    story.append(P("BUGLOG.md contains 11 recorded findings. Severity labels below are report-level impact estimates: high means a possible crash or invalid projection; medium means a blocked interaction; low means a visual or test-reliability issue."))
    rows = [
        ["ID / impact", "Reproduction and observed result", "Root cause", "Fix, check and status"],
        ["RX-UI-001\nLow / UI", "Open Explore's object list. Each row showed the same generic box instead of a distinct mesh preview.", "ScenePanel reused one fixed mesh icon, and the top bar used the generic box as the brand.", "Added the RX mark and mesh previews. Headless screens show them. Fixed (checked)."],
        ["RX-UI-002\nLow / window", "Inspect the app window identity. The default runtime icon remained visible.", "The app set window captions but did not set a project icon.", "Added a shared identity helper. RenderX was checked; Breakpoint's OpenGL window is unavailable in dummy mode. Fixed (RenderX checked; Breakpoint icon unverified)."],
        ["RX-CORE-001\nHigh / projection", "Project a point at depth zero with a zero near plane. It raised ZeroDivisionError instead of rejecting the point.", "The guard compared depth only to the supplied near plane, so zero passed when that plane was zero.", "Reject non-positive depth before division. Edge checks passed for zero, negative and clipped positive depth. Fixed (checked)."],
        ["RX-CORE-002\nHigh / projection", "Project extreme but finite coordinates. The result contained an infinite screen coordinate.", "Input values were checked, but projected output was not checked after scaling.", "Reject non-finite output coordinates. Engine-edge checks passed. Fixed (checked)."],
        ["RX-UI-003\nMedium / input", "Open keyboard help and click a destination beneath it. The destination changed while help stayed open.", "The overlay did not capture mouse input or consume the outside click.", "Help now captures and consumes the click. Replayed event sequences passed. Fixed (checked)."],
        ["RX-UI-004\nLow / focus", "Hover or press a control, then leave the window or lose focus. Its transient style stayed active.", "Leave and focus-loss handlers did not clear hover and pressed state.", "Clear transient state on leave and focus loss. Replayed event sequences passed. Fixed (checked)."],
    ]
    story.append(make_table(rows, [23 * mm, 48 * mm, 48 * mm, BODY_W - 119 * mm], padding=4, font_size=7.8))
    caption(story, 9, "Recorded defect register, part 1.")
    story.append(P("The projection fixes protect two different points in the pipeline. One stops unsafe depth before division; the other catches overflow after projection. The engine edge runner rechecked both.", "small"))
    story.append(PageBreak())

    # Page 9: rest of defect register and explanation.
    story.append(P("7.1 Defect register, continued", "h1"))
    rows = [
        ["ID / impact", "Reproduction and observed result", "Root cause", "Fix, check and status"],
        ["RX-UI-005\nLow / pointer", "Move over a button or field. The pointer remained an arrow instead of showing the control type.", "Dashboard hit testing had no cursor mapping.", "Added cursor requests. Event checks saw hand then arrow; native cursor appearance was not available in dummy mode. Fixed (requests checked; desktop appearance unverified)."],
        ["RX-UI-006\nLow / layout", "At 1024x640, inspect a narrow icon-led control. The ellipsis could overlap its icon.", "Text truncation always drew an ellipsis even when it could not fit.", "Omit the label when the mark cannot fit. Typography audit passed at the compact size. Fixed (checked)."],
        ["RX-UI-007\nLow / pointer", "Press and hold a button, then leave the window before releasing it. The pressed state remained.", "The leave handler cleared hover but not the pressed action.", "Clear the pressed state on leave. Replayed event schedule passed. Fixed (checked)."],
        ["RX-UI-008\nMedium / text", "Draw a long label that truncates. The bundled font raised an error on the ellipsis glyph.", "The font did not contain the Unicode ellipsis character.", "Use three ASCII periods. Focused font checks and the full suite passed. Fixed (checked)."],
        ["RX-TEST-001\nLow / tests", "Open files before running the recent-file test. The test inherited old paths and could fail its one-item check.", "The test redirected the settings file but did not reset the in-memory recent list.", "Reset the in-memory list inside the test. The fresh full suite passed. Fixed (checked)."],
    ]
    story.append(make_table(rows, [23 * mm, 48 * mm, 48 * mm, BODY_W - 119 * mm], padding=4, font_size=7.8))
    caption(story, 10, "Recorded defect register, part 2.")
    story.append(P("A useful example came from the test-isolation defect. OBJ opening worked, but the test could fail after the app had already stored recent files. The fix resets that in-memory list for the test, then the whole suite was run again with settings redirected to a temporary folder.", "body"))
    story.append(P("No issue is marked open in BUGLOG.md. Two native-only details remain outside this check: the cursor's visible shape on a real desktop and Breakpoint's own OpenGL window icon.", "small"))
    story.append(P("What we learned", "h2"))
    rows = [
        ["Cause group", "Example from this review", "Lesson"],
        ["Hard-coded sizes", "Icon spacing and narrow Challenge labels could conflict with controls.", "Measure text and available control space before drawing."],
        ["Old data not refreshed", "Torus was visible while the status bar showed Cube counts.", "Build status from the currently selected model."],
        ["Missing input checks", "Zero depth, extreme projection values and malformed OBJ data.", "Validate values before division, drawing or changing the scene."],
    ]
    story.append(make_table(rows, [35 * mm, 63 * mm, BODY_W - 98 * mm], padding=4))
    caption(story, 11, "Lessons grouped by the cause patterns found during review.")
    story.append(PageBreak())

    # Page 10: earlier UI feedback and genuine before/after evidence.
    story.append(P("7.2 Checks raised by earlier interface feedback", "h1"))
    story.append(P("These checks are included because they were raised during project review. They are separate from the 11 BUGLOG.md entries; the report does not add an undocumented root cause."))
    rows = [
        ["Earlier observation", "Current evidence", "Status"],
        ["Icon looked clipped or off-center.", "Current pixel-bound test checks every SVG and mesh icon at five sizes; current toolbar capture is included.", "Current layout passes. No matching before image was available."],
        ["Challenge tab shortened to 'Chall...'.", "Launch-flow test checks actual tab labels and page shortcuts.", "Current tab text fits. No matching before image was available."],
        ["Status bar showed Cube counts while Torus was visible.", "Historical screen paired with current Torus capture; a test compares status to the active shape.", "Current status check passes."],
        ["App opened in Shooter by default.", "Landing screen capture and launch-flow tests check the initial destination.", "Current app opens on Landing; Enter opens Explore."],
        ["Left and right panels seemed to repeat headings.", "Current Explore capture shows SCENE and INSPECTOR as separate panel headings.", "Not reproduced in the current screen; no earlier panel capture found."],
    ]
    story.append(make_table(rows, [48 * mm, 79 * mm, BODY_W - 127 * mm], padding=3))
    caption(story, 12, "Earlier UI observations checked against current evidence.")
    # Two genuine before/after pairs from the supplied project evidence.
    pair_data = []
    for old_name, new_name, left_caption, right_caption in [
        ("historical-status-bug-before.png", "explore-torus-status.png",
         "Figure 2. Earlier capture: Torus shown with stale Cube status.",
         "Figure 3. Current capture: Torus mesh with matching status."),
        ("landing-checkbox-before.png", "landing-current.png",
         "Figure 4. Earlier landing screen with the misaligned option.",
         "Figure 5. Current landing screen after the option was removed."),
    ]:
        old_img = Image(str(PHOTOS / old_name), width=76 * mm, height=42 * mm,
                        kind="proportional", hAlign="CENTER")
        new_img = Image(str(PHOTOS / new_name), width=76 * mm, height=42 * mm,
                        kind="proportional", hAlign="CENTER")
        pair_data.append([[old_img, P(left_caption, "caption")],
                          [new_img, P(right_caption, "caption")]])
    pair_table = Table(pair_data, colWidths=[BODY_W / 2] * 2, hAlign="LEFT")
    pair_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.4, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(pair_table)
    story.append(PageBreak())

    # Page 11: official M1 acceptance IDs and later additions.
    section(story, 8, "Validation and results")
    story.append(P("F01-F10 are the feature IDs from the supplied Milestone 01 PRD. The table checks those original aims against current tests. The later v4 features are listed separately because they were added after that requirements sheet."))
    rows = [
        ["ID", "Milestone 01 acceptance area", "Current check", "Status"],
        ["F01", "Launch, use and close the app.", "Landing and exit routes; launch-flow tests.", "Pass in tested routes"],
        ["F02", "Valid built-in mesh data.", "Shape and mesh validation tests.", "Pass"],
        ["F03", "Perspective projection and safe depth.", "Projection, clipping and engine-edge checks.", "Pass for listed cases"],
        ["F04", "Three-axis rotation from input.", "Known rotations and interaction tests.", "Pass"],
        ["F05", "Move a model without mutating source points.", "Translation and original-vertex tests.", "Pass"],
        ["F06", "Uniform scale with positive bounds.", "Scale interaction and bounds tests.", "Pass"],
        ["F07", "Choose either built-in shape.", "Dashboard selection and model tests.", "Pass"],
        ["F08", "Reset selected model transforms.", "Scene reset and UI action tests.", "Pass"],
        ["F09", "Readable controls and current status.", "Dashboard tests and visible status capture.", "Pass in tested paths"],
        ["F10", "Input remains usable after focus changes.", "Focus, leave-window and release-event tests.", "Pass"],
    ]
    story.append(make_table(rows, [13 * mm, 62 * mm, 65 * mm, BODY_W - 140 * mm], padding=2.8))
    caption(story, 13, "Validation against the original feature IDs.")
    story.append(P("The acceptance table shows the requirements that still matter in the current app. It does not claim a full manual acceptance run on every feature of the later shooter.", "small"))

    # Page 12: v4 additions validation and performance.
    story.append(P("8.1 Later features added after the original requirements", "h1"))
    rows = [
        ["Current feature", "Evidence", "Status"],
        ["OBJ import and safe errors", "Parser and file-open tests; over-limit screenshot.", "Pass for bounded supported subset; native picker not checked."],
        ["Challenges and Maze", "Quest and Maze tests; destination captures.", "Pass in tested code paths."],
        ["Breakpoint shooter", "Game-rule tests and launch-failure recovery.", "Partly checked; live OpenGL run remains unverified."],
        ["Audio settings", "Preference and audio state tests.", "State passes; physical device playback not checked."],
        ["Responsive desktop layout", "Eight sizes and 50 rapid resize events.", "Pass for the tested size matrix."],
    ]
    story.append(make_table(rows, [42 * mm, 72 * mm, BODY_W - 114 * mm], padding=3))
    caption(story, 14, "Validation of later additions without assigning them old requirement IDs.")
    story.append(P("Performance testing", "h2"))
    story.append(P("The performance runner used three paced 5-second SDL dummy-display runs, with 300 target frames per run. The FPS column is 1,000 divided by average frame time; it is a headless comparison value, not a graphics-card benchmark."))
    rows = [
        ["Scene", "Mean frame time", "p95", "p99", "Reciprocal FPS", "Peak working set"],
        ["Explore idle", "6.565 ms", "8.211 ms", "8.903 ms", "152.3", "65.11 MB"],
        ["Explore orbit", "6.511 ms", "7.703 ms", "8.618 ms", "153.6", "65.12 MB"],
        ["Signal wave mesh", "10.642 ms", "11.930 ms", "12.605 ms", "94.0", "65.37 MB"],
    ]
    story.append(make_table(rows, [29 * mm, 28 * mm, 23 * mm, 23 * mm, 28 * mm, BODY_W - 131 * mm], padding=3))
    caption(story, 15, "Fresh 5-second headless measurements, 23 October 2026.")
    story.append(P("Peak resident memory rose by about 9.8-10.0 MB over the run baseline. The tests did not record minimum instantaneous FPS, native GPU FPS, or the parse time for a successful large external OBJ.", "small"))
    story.append(PageBreak())

    # Page 13: security/input.
    story.append(P("8.2 Input safety and basic security", "h1"))
    story.append(P("RenderX is an offline desktop app. It has no account service, server API or network-based user data. The relevant input boundary in this milestone is a local OBJ file, plus saved preference and score files."))
    rows = [
        ["Check", "Current protection", "Evidence / limit"],
        ["File size", "OBJ reader reads at most 2,000,001 bytes before rejecting over 2,000,000 bytes.", "Oversized fixture and visible error scenario passed."],
        ["Geometry size", "Limits of 20,000 vertices and 50,000 unique edges.", "Loader and edge tests cover limits."],
        ["Numeric values", "Reject non-finite vertex values and unsafe projected results.", "Core and engine-edge checks passed."],
        ["Face references", "Reject empty, malformed and out-of-range face data.", "OBJ parser and failure-preservation tests passed."],
        ["File execution", "OBJ records are parsed as text; they are not evaluated as Python code.", "Source review of the current loader; no penetration audit."],
        ["Network threats", "No login or network endpoint exists in this desktop app.", "Not applicable to the current architecture."],
    ]
    story.append(make_table(rows, [31 * mm, 84 * mm, BODY_W - 115 * mm], padding=3))
    caption(story, 16, "Basic input checks carried out for the current offline app.")
    story.append(P("A corrupt or oversized file should produce an error while leaving the current scene available. This is checked by the parser tests, the engine-edge runner and the oversized-input screenshot scenario.", "body"))
    story.append(P("This is basic local-file robustness testing, not a formal security review. Authentication, network attacks, deployment, malware scanning and third-party penetration testing were not performed.", "small"))
    story.append(PageBreak())

    # Page 14: result, charts and known limits.
    story.append(P("8.3 Summary, limits and next work", "h1"))
    story.append(P("The fresh full suite completed with 135 tests passing in 11.507 seconds. No test failed. The edge runner passed 12 checks; the resize matrix passed 8 sizes and 50 rapid events. The screenshot harness captured 15 current app scenarios. The performance runner completed all three scenarios."))
    story.append(Image(str(CHARTS / "tests-by-level.png"), width=BODY_W * .58,
                       height=65 * mm, kind="proportional", hAlign="CENTER"))
    story.append(P("Figure 6. Automated tests grouped by module purpose; the combined run passed all 135.", "caption"))
    story.append(Image(str(CHARTS / "defects-by-area.png"), width=BODY_W * .58,
                       height=63 * mm, kind="proportional", hAlign="CENTER"))
    story.append(P("Figure 7. Eleven documented defects: eight UI, two projection and one test-isolation.", "caption"))
    story.append(Image(str(CHARTS / "performance.png"), width=BODY_W * .72,
                       height=52 * mm, kind="proportional", hAlign="CENTER"))
    story.append(P("Figure 8. Reciprocal of mean frame time in the headless runs; this is not a native GPU benchmark.", "caption"))
    story.append(P("Not measured or not confirmed", "h2"))
    story.append(P("A live Windows acceptance session, Breakpoint gameplay on a real OpenGL display, the native file chooser, physical audio output, visible system cursor, fullscreen across monitors, minimum instantaneous FPS and a successful parse of the student's large model.obj were not confirmed. The user previously reported that model exceeded 2 MB, but the file was not present during this run. The loader's documented limit is 2 MB.", "small"))
    story.append(P("Next work", "h2"))
    story.append(P("Before the demonstration, run the app once on the target laptop: open a normal OBJ, try the native file dialog, play a short Breakpoint run, confirm music and effects, resize the window and close it. Simplify or split any external OBJ above the documented limit.", "small"))
    story.append(PageBreak())

    # Page 15: references and test-file map.
    story.append(P("References and test file map", "h1"))
    story.append(P("Project sources", "h2"))
    sources = [
        "RenderX public GitHub repository, baseline commit 972266d8ff9582fbb9f2f81fd65e855cfb635b0a, 25 September 2026.",
        "Current RenderX code snapshot d34e273b5d9699c915589e5429f0bf27e84401da, 23 October 2026.",
        "Project README.md, FEATURES.md, BUGLOG.md and docs/TESTING.md.",
        "Milestone 01 PRD, feature IDs F01-F10, supplied as read-only project source.",
    ]
    for item in sources:
        story.append(P("- " + html.escape(item), "body"))
    story.append(P("Testing tool", "h2"))
    story.append(P("- Python unittest: standard library test framework used for the fresh run.", "body"))
    story.append(P("Test modules", "h2"))
    rows = [
        ["Main purpose", "Test files"],
        ["Geometry and renderer", "test_core.py, test_engine.py, test_comparison.py, test_extensions.py"],
        ["UI, input and launch", "test_dashboard.py, test_input_map.py, test_interaction.py, test_launch_flow.py, test_ui_fonts.py, test_window.py"],
        ["File and settings", "test_file_open.py, test_settings_path.py"],
        ["Challenges and games", "test_quest.py, test_maze.py, test_shooter.py, test_audio.py"],
    ]
    story.append(make_table(rows, [44 * mm, BODY_W - 44 * mm]))
    caption(story, 17, "Current test modules included by unittest discovery.")
    story.append(P("No database was introduced. The application uses local preference and score files, as documented in the current project.", "small"))
    story.append(PageBreak())

    # Page 16: exact rerun commands.
    story.append(P("Appendix A | Re-running the checks", "h1"))
    story.append(P("Run these commands from the repository root in PowerShell. The temporary settings path keeps the test run separate from normal RenderX preferences.", "body"))
    commands = """$env:LOCALAPPDATA = Join-Path $env:TEMP 'renderx-m04-fresh-validation'
$env:SDL_VIDEODRIVER = 'dummy'
.\\.venv\\Scripts\\python.exe -m unittest discover -s tests -v
.\\.venv\\Scripts\\python.exe tools\\qa\\engine_edges.py
.\\.venv\\Scripts\\python.exe tools\\qa\\resize_matrix.py <output-folder>
.\\.venv\\Scripts\\python.exe tools\\qa\\performance_runs.py --seconds 5 --output <output-folder>
.\\.venv\\Scripts\\python.exe output\\milestone_04\\source\\capture_screenshots.py"""
    listing(story, 3, "Commands used for the current report", "PowerShell, from the repository root", commands)
    story.append(P("Recorded fresh outputs", "h2"))
    rows = [
        ["Run", "Result"],
        ["unittest discovery", "Ran 135 tests in 11.507 seconds; OK."],
        ["engine_edges.py", "12 named geometry and OBJ checks passed."],
        ["resize_matrix.py", "8 size snapshots passed; 50 rapid resize events; no runner error."],
        ["performance_runs.py", "Idle, orbit and largest-mesh scenarios passed; 300 target frames each."],
        ["capture_screenshots.py", "15 current application scenarios captured with passed runner status."],
    ]
    story.append(make_table(rows, [51 * mm, BODY_W - 51 * mm]))
    caption(story, 18, "Fresh recorded checks for this version of the report.")
    story.append(P("A screenshot of the Shooter destination is only a headless app-shell capture. It is not evidence that live Breakpoint combat ran on a GPU.", "small"))
    story.append(PageBreak())

    # Page 17: code listings, current tests and parser guard.
    story.append(P("Appendix B | Code listings", "h1"))
    icon_test, start, end = function_source(ROOT / "tests" / "test_launch_flow.py",
                                            "test_every_svg_and_mesh_icon_is_safe_at_small_and_large_sizes", 22)
    listing(story, 4, "Icon pixels stay inside the button rectangle",
            f"tests/test_launch_flow.py, lines {start}-{end}", icon_test,
            "This checks five icon sizes and the four pixel margins around the rendered mark.")
    loader = ROOT / "renderx" / "core" / "obj_loader.py"
    loader_excerpt = source_range(loader, 36, 52)
    listing(story, 5, "OBJ size and numeric input guards",
            "renderx/core/obj_loader.py, lines 36-52", loader_excerpt,
            "The excerpt comes from the current loader; later lines check face references and edge limits.")
    story.append(PageBreak())

    # Page 18: file-open and fixed/old icon placement.
    story.append(P("Appendix B | Code listings, continued", "h1"))
    open_test, start, end = function_source(ROOT / "tests" / "test_file_open.py",
                                            "test_open_obj_adds_selects_and_remembers_mesh", 20)
    listing(story, 6, "Opening an OBJ updates the model and recent list",
            f"tests/test_file_open.py, lines {start}-{end}", open_test)
    button = ROOT / "renderx" / "ui" / "components" / "button.py"
    current_icon, start, end = function_source(button, "icon_button_rect", 25)
    listing(story, 7, "Current fit-aware icon placement",
            f"renderx/ui/components/button.py, lines {start}-{end}", current_icon)
    previous_icon = old_icon_source()
    listing(story, 8, "Earlier fixed leading placement from local history",
            "renderx/ui/components/button.py at commit 98354b3, lines 29-37", previous_icon,
            "The earlier snippet has no centering decision. The current helper and pixel-bound test are shown above.")
    story.append(PageBreak())

    # Three screenshot pages with current and clearly labelled historical captures.
    story.extend([P("Appendix C | Screenshot evidence", "h1"),
                  P("Current app captures below were made on 23 October 2026; the historical reference is labelled. The current Shooter capture shows the destination shell only, not live OpenGL gameplay.", "small")])
    gallery_page(story, "Explore and file workflows", [
        (9, "explore-cube.png", "Explore with the built-in cube, scene list, inspector and status strip."),
        (10, "explore-house-loaded.png", "Bundled house OBJ loaded in the renderer."),
        (11, "explore-file-menu.png", "File menu and the available open actions."),
        (12, "explore-oversized-obj-error.png", "Readable feedback for an oversized OBJ."),
        (13, "explore-shortcuts.png", "Keyboard shortcut overlay."),
    ])
    story.append(PageBreak())
    gallery_page(story, "Destinations and workspace controls", [
        (14, "challenges.png", "Challenges destination."),
        (15, "maze.png", "First-person wireframe Maze destination."),
        (16, "shooter.png", "Shooter destination shell; not live OpenGL gameplay."),
        (17, "preferences.png", "Preferences and audio controls."),
        (18, "viewport-context-menu.png", "Viewport context menu in Explore."),
    ])
    story.append(PageBreak())
    gallery_page(story, "Display sizes and an earlier project capture", [
        (19, "historical-shooter-first.png", "Earlier Breakpoint destination capture; historical reference, not from this validation run."),
        (20, "explore-light-theme.png", "Explore in the alternate light theme."),
        (21, "explore-small-1024x640.png", "Compact Explore layout at 1024 by 640."),
        (22, "explore-large-1920x1080.png", "Explore layout at 1920 by 1080."),
        (23, "explore-toolbar-zoom.png", "Enlarged crop from the real Explore toolbar capture."),
    ])

    return story


def main():
    doc = MilestoneDoc(str(OUTPUT))
    doc.build(build_story())
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
