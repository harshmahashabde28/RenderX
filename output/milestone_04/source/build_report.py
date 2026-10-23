"""Build the RenderX Milestone 04 report and viva PDF from repository evidence."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, SimpleDocTemplate, Frame, PageTemplate, Paragraph,
                                Spacer, PageBreak, Table, TableStyle, Image as RLImage,
                                KeepTogether, Preformatted, HRFlowable)

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent
OUT = ROOT / "output" / "pdf"
SHOTS = SOURCE / "screenshots"
MANIFEST = json.loads((SOURCE / "screenshot_manifest.json").read_text(encoding="utf-8"))
OUT.mkdir(parents=True, exist_ok=True)
MINT = colors.HexColor("#62CDB4")
INK = colors.HexColor("#172126")
MUTED = colors.HexColor("#53636A")
PALE = colors.HexColor("#EFF8F6")
LINE = colors.HexColor("#D5E2DF")
PAGE_W, PAGE_H = A4

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="BodyX", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=8.7, leading=12.1, textColor=INK, spaceAfter=5))
styles.add(ParagraphStyle(name="SmallX", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=7.4, leading=9.6, textColor=MUTED, spaceAfter=3))
styles.add(ParagraphStyle(name="TitleX", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=26, leading=31, textColor=INK, alignment=TA_CENTER, spaceAfter=8))
styles.add(ParagraphStyle(name="SubX", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=13, leading=18, textColor=MUTED, alignment=TA_CENTER, spaceAfter=10))
styles.add(ParagraphStyle(name="H1X", parent=styles["Heading1"], fontName="Helvetica-Bold",
    fontSize=16, leading=19, textColor=INK, spaceAfter=8, keepWithNext=True))
styles.add(ParagraphStyle(name="H2X", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=10.2, leading=13, textColor=colors.HexColor("#168B78"), spaceBefore=5,
    spaceAfter=4, keepWithNext=True))
styles.add(ParagraphStyle(name="CaptionX", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=7.4, leading=9.2, textColor=MUTED, alignment=TA_CENTER, spaceBefore=3,
    spaceAfter=4))
styles.add(ParagraphStyle(name="CodeCapX", parent=styles["BodyText"], fontName="Helvetica-Bold",
    fontSize=7.6, leading=9, textColor=INK, spaceBefore=3, spaceAfter=2))
styles.add(ParagraphStyle(name="CellX", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=7.05, leading=8.9, textColor=INK, spaceAfter=0))
styles.add(ParagraphStyle(name="CellHeadX", parent=styles["BodyText"], fontName="Helvetica-Bold",
    fontSize=7.2, leading=9, textColor=colors.white, spaceAfter=0))
styles.add(ParagraphStyle(name="DetailX", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=6.35, leading=7.65, textColor=INK, spaceAfter=0))
styles.add(ParagraphStyle(name="CenterX", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=8, leading=11, textColor=INK, alignment=TA_CENTER))
CODE = ParagraphStyle("CodeX", fontName="Courier", fontSize=6.4, leading=8.1,
                      textColor=INK, backColor=colors.HexColor("#F5F8F8"), borderColor=LINE,
                      borderWidth=.5, borderPadding=6, leftIndent=0, rightIndent=0,
                      spaceBefore=1, spaceAfter=5)

def P(text, style="BodyX"):
    return Paragraph(text, styles[style])

def table(rows, widths, header=True, fontsize=None):
    cooked = [[P(str(cell), "CellHeadX" if header and ri == 0 else "CellX") for cell in row]
              for ri, row in enumerate(rows)]
    t = Table(cooked, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), .35, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    if header:
        commands += [("BACKGROUND", (0, 0), (-1, 0), INK)]
    for ri in range(1 if header else 0, len(rows)):
        if (ri - (1 if header else 0)) % 2 == 1:
            commands.append(("BACKGROUND", (0, ri), (-1, ri), colors.HexColor("#F7FAF9")))
    t.setStyle(TableStyle(commands))
    return t

def code(path, start, end, title, lines=None):
    content = (ROOT / path).read_text(encoding="utf-8").splitlines()
    snippet = "\n".join(f"{i:>4}  {content[i-1]}" for i in range(start, end + 1))
    return [P(title, "CodeCapX"), Preformatted(snippet, CODE)]

def code_segments(path, segments, title):
    content = (ROOT / path).read_text(encoding="utf-8").splitlines()
    parts = []
    for si, (start, end) in enumerate(segments):
        if si:
            parts.append("...")
        parts.extend(f"{i:>4}  {content[i-1]}" for i in range(start, end + 1))
    return [P(title, "CodeCapX"), Preformatted("\n".join(parts), CODE)]

def old_code():
    result = subprocess.run(["git", "show", "98354b3:renderx/ui/components/button.py"],
                            cwd=ROOT, check=True, capture_output=True, text=True)
    lines = result.stdout.splitlines()
    snippet = "\n".join(f"{i:>4}  {lines[i-1]}" for i in range(29, 38))
    return [P("Listing 4.5: Earlier left-anchored icon placement — git 98354b3, lines 29–37", "CodeCapX"),
            Preformatted(snippet, CODE)]

def img(filename, width, height=None):
    p = Path(filename)
    if not p.is_absolute():
        p = SHOTS / p
    im = Image.open(p)
    w, h = im.size
    target_h = height if height else width * h / w
    return RLImage(str(p), width=width, height=target_h, kind="proportional")

def on_page(canvas, doc):
    if doc.page == 1:
        return
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(.5)
    canvas.line(18*mm, PAGE_H-15*mm, PAGE_W-18*mm, PAGE_H-15*mm)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(INK)
    canvas.drawString(18*mm, PAGE_H-11*mm, "RenderX  |  Milestone 04")
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(PAGE_W-18*mm, PAGE_H-11*mm, "Testing & Validation")
    canvas.line(18*mm, 14*mm, PAGE_W-18*mm, 14*mm)
    canvas.drawString(18*mm, 9*mm, "B.Tech CSE · 2nd Year · 2026")
    canvas.drawRightString(PAGE_W-18*mm, 9*mm, f"Page {doc.page}")
    canvas.restoreState()

class ReportDoc(BaseDocTemplate):
    def __init__(self, path):
        super().__init__(str(path), pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
                         topMargin=22*mm, bottomMargin=20*mm, title="RenderX Milestone 04 — Testing & Validation",
                         author="RenderX project team")
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height,
                      id="normal", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates(PageTemplate(id="main", frames=[frame], onPage=on_page))

def make_charts():
    try:
        font = ImageFont.truetype("arial.ttf", 20)
        small = ImageFont.truetype("arial.ttf", 14)
    except OSError:
        font = ImageFont.load_default(); small = font
    def bar_chart(filename, title, items, suffix=""):
        w, h = 1200, 570
        im = Image.new("RGB", (w, h), "white")
        d = ImageDraw.Draw(im)
        d.text((40, 25), title, font=font, fill="#172126")
        maxv = max(v for _, v, _ in items) or 1
        left, top, plotw = 270, 90, 650
        for i, (label, val, detail) in enumerate(items):
            y = top + i*105
            d.text((35, y+14), label, font=small, fill="#172126")
            bw = int(plotw * val / maxv)
            d.rounded_rectangle((left, y, left+bw, y+46), radius=10, fill="#62CDB4")
            label = f"{val:g}{suffix}" if str(detail) == str(val) else f"{val:g}{suffix}  {detail}"
            d.text((left+bw+12, y+13), label, font=small, fill="#172126")
        im.save(SOURCE / filename)
    bar_chart("chart-defects.png", "Recorded defect entries by area",
              [("User interface", 8, "8"), ("Core geometry", 2, "2"), ("Test isolation", 1, "1")])
    bar_chart("chart-tests.png", "Automated test functions passed; no failures",
              [("Unit-focused", 58, "0 failed"), ("Integration-focused", 77, "0 failed"),
               ("System QA runs", 20, "0 errors")])
    means = [("Explore · idle", 8.673), ("Explore · orbit input", 8.803),
             ("Signal wave · complex scene", 23.729)]
    bar_chart("chart-fps.png", "Calculated reciprocal of mean headless frame time",
              [(name, round(1000/ms, 1), f"{ms:.3f} ms mean") for name, ms in means], " fps")

def gallery_page(story, title, names):
    story.extend([P(title, "H1X"), P("Captured from the current application through the headless Pygame loop. Captions state the check each image supports.", "SmallX")])
    cells = []
    cell_w = (PAGE_W-36*mm-12)/2
    for index, (filename, caption) in enumerate(names):
        content = [img(filename, cell_w-8, height=126), P(caption, "CaptionX")]
        cells.append(content)
    rows = []
    for i in range(0, len(cells), 2):
        row = []
        for j in range(i, min(i+2, len(cells))):
            row.append(cells[j])
        if len(row) == 1:
            row.append(Spacer(1, 1))
        rows.append(row)
    t = Table(rows, colWidths=[cell_w, cell_w], hAlign="LEFT")
    t.setStyle(TableStyle([("VALIGN", (0,0),(-1,-1),"TOP"), ("BOX", (0,0),(-1,-1),.4,LINE),
        ("INNERGRID", (0,0),(-1,-1),.4,LINE), ("LEFTPADDING",(0,0),(-1,-1),4),
        ("RIGHTPADDING",(0,0),(-1,-1),4), ("TOPPADDING",(0,0),(-1,-1),5),
        ("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story.append(t)

def build_main():
    make_charts()
    out = OUT / "RenderX_Milestone_04_Testing_and_Validation.pdf"
    story = []
    # 1 cover
    story += [Spacer(1, 25*mm), RLImage(str(ROOT/"assets/logo/renderx-logo.png"), width=155*mm, height=38*mm),
              Spacer(1, 16*mm), P("RenderX", "TitleX"), P("Milestone 04: Testing &amp; Validation", "SubX"),
              HRFlowable(width="70%", thickness=2, color=MINT, hAlign="CENTER"), Spacer(1, 13*mm),
              P("A test report for a Python and Pygame 3D wireframe renderer", "CenterX"), Spacer(1, 12*mm),
              table([["Student detail", "Fill in before submission"], ["Name", "[Your name]"],
                     ["Roll number", "[Roll number]"], ["Section / branch", "[Section] / CSE"],
                     ["Year", "2nd year"], ["Faculty / guide", "[Faculty name]"],
                     ["College", "[College name]"], ["Submission date", "[Date]"]],
                    [55*mm, 105*mm]), Spacer(1, 8*mm),
              P("Evidence captured from the repository and test runs on 23 October 2026.", "CaptionX"), PageBreak()]
    # 2 declaration
    story += [P("Declaration and acknowledgement", "H1X"),
              P("I declare that this report describes testing carried out on the RenderX project files available for this milestone. The results and screenshots are based on the project’s current source, test suite, and QA runs. Any requirement IDs copied from earlier milestones must be checked by me before submission."),
              P("Student: [Your name]  |  Signature: ____________________  |  Date: [Date]", "SmallX"),
              P("Acknowledgement", "H2X"), P("I thank [faculty / guide name] for guidance and feedback. I also acknowledge the open-source Python, Pygame, and pytest communities and the contributors whose tools made the project possible."),
              Spacer(1, 8*mm), P("Report note", "H2X"),
              P("The earlier Milestone 01/02 requirement documents were not present with the available project materials. Requirements R1–R8 in this report are therefore provisional statements derived from the current FEATURES.md and verified behavior. Replace their IDs or wording if your earlier documents use a different set."), PageBreak()]
    # 3 abstract
    story += [P("Abstract", "H1X"), P("RenderX is a desktop 3D wireframe application built with Python and Pygame. It provides an Explore workspace for viewing built-in and imported OBJ models, plus Challenges, Maze, and Shooter destinations. This milestone checks the renderer and geometry helpers, OBJ input handling, interface controls, and navigation. Automated tests were run with pytest in an isolated settings directory. The final run passed 135 test functions and 36 subtests, with one PyGLM deprecation warning. Separate QA scripts completed 12 engine edge checks, eight window-size cases, 50 rapid resize events, 15 current interface screenshot runs, and three short performance scenarios. One test-isolation defect was found and fixed during the report work. Timing figures come from a headless environment and are not a promise of on-screen frame rate. The report records what was not measured, including OBJ load time and a live OpenGL Breakpoint gameplay run."),
              P("Contents", "H2X"), table([["Section", "Page"], ["1. Introduction and project timeline", "4"],
                ["2. System overview and environment", "5"], ["3. Requirements and test plan", "6–7"],
                ["4. Unit tests and code listings", "8–9"], ["5. Integration and system testing", "10–11"],
                ["6. Screenshot evidence", "12–16"], ["7. Defects and regression", "17–18"],
                ["8. Performance, security, validation, conclusion", "19–21"],
                ["Appendices", "22"]], [118*mm, 35*mm]),
              P("Lists: Figures 4.1–4.19 (pages 12–16); Tables 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 9.1, 12.1, B.1; Listings 4.1–4.5, 6.1–6.2 and A.1.", "SmallX"), PageBreak()]
    # 4 intro/timeline
    story += [P("1. Introduction", "H1X"),
              P("RenderX demonstrates the basic 3D viewing pipeline in a desktop application. A user can choose a built-in shape or open an OBJ file, adjust the view, and explore additional destinations. This milestone focuses on checking reliability after recent interface and feature changes."),
              P("Objectives", "H2X"), P("Check the main parser, geometry, icon layout, settings, and navigation behavior; run the automated suite; exercise application screens and resize cases; review the recorded defects; and report limits honestly."),
              P("Scope", "H2X"), P("Included: Python tests, headless Pygame interface captures, parser and geometry edge checks, resize QA, and short headless timing runs. Excluded or unverified: live desktop cursor appearance, native Windows file chooser behavior, real GPU frame rate, large-OBJ load time, and current OpenGL Shooter gameplay on a visible display."),
              P("Project timeline", "H2X"), table([["Verified sequence", "Repository evidence"],
                ["Core renderer and math foundation", "68c89c9, 637a69e"],
                ["UI shell and responsive workspace", "0198192, 98354b3, 6ab93a8"],
                ["Breakpoint recovery and audio/game additions", "9c67c2c, b96df4a, 696aa3b"],
                ["Desktop conventions, landing flow, OBJ showcases", "67df2c6, d0e5beb, 989e63c, baa03cf"],
                ["QA and screenshot capture", "tools/qa/* and this milestone evidence"]], [75*mm, 78*mm]),
              P("The sequence above is based on git history. A few older overview documents describe an earlier launch flow; this report follows current code and recent commits.", "SmallX"), PageBreak()]
    # 5 overview
    story += [P("2. System overview", "H1X"),
      P("The app uses a Pygame interface around a software wireframe renderer. The OBJ loader reads a limited subset of Wavefront OBJ, turns polygon boundaries into mesh edges, and normalizes the model. Dashboard pages manage Explore, Challenges, Maze, and Shooter. Breakpoint is a separate OpenGL path and needs a real display for end-to-end gameplay confirmation."),
      table([["Layer", "Purpose"], ["Interface", "Landing, navigation, panels, settings, shortcuts, status and file actions."],
        ["Geometry / renderer", "Mesh, transform, camera projection, clipping, and line drawing."],
        ["OBJ loader", "Read bounded vertex and face data, validate it, and create a mesh."],
        ["Destinations", "Explore, Challenges, Maze, and Shooter pages."],
        ["Breakpoint", "Separate OpenGL shooter runtime; not covered by the current headless gameplay run."]], [42*mm, 111*mm]),
      Spacer(1, 6), P("Table 2.1: Application areas included in this report", "CaptionX"),
      P("Technology and measured environment", "H2X"),
      table([["Item", "Observed value"], ["OS", "Windows 11 Home Single Language, build 10.0.26300"],
        ["Python", "3.13.15"], ["Pygame", "2.6.1"], ["pytest", "9.1.1"],
        ["System memory", "16,873,545,728 bytes (about 15.7 GiB reported by the host)"],
        ["Computer", "Lenovo model 83DV; GPU and native display details were not reported by the headless QA host"],
        ["QA window sizes", "800×500 through 2560×1440; also 1024×1600 and 2200×720"]], [50*mm, 103*mm]), PageBreak()]
    # 6 requirements
    reqs = [["ID*", "Requirement used for this report", "Check"],
      ["R1", "Open built-in and supported OBJ meshes in Explore.", "OBJ and file-open tests"],
      ["R2", "Reject malformed, empty, oversized, and invalid-index OBJ input safely.", "Parser tests / engine edges"],
      ["R3", "Show mesh identity and counts for the current visible model.", "Status tests / screenshot"],
      ["R4", "Render and transform 3D wireframe models with projection controls.", "Core and dashboard tests"],
      ["R5", "Keep interface controls and icons within their hit areas.", "Icon layout tests"],
      ["R6", "Switch among Explore, Challenges, Maze, and Shooter destinations.", "Navigation tests / screenshots"],
      ["R7", "Keep primary workspace usable at tested window sizes.", "Resize matrix"],
      ["R8", "Show clear feedback for unsupported or failed model loads.", "File-open test / screenshot"]]
    story += [P("3. Requirements", "H1X"), P("*Provisional IDs: the earlier milestone requirement sheets were unavailable in the provided project materials. Match these rows to the official IDs before submission.", "SmallX"),
      table(reqs, [13*mm, 91*mm, 49*mm]), P("Table 3.1: Provisional requirement statements", "CaptionX"), Spacer(1, 8),
      P("Validation status is summarized again in Table 8.2. These statements describe the tested scope, not a claim that every product behavior has been formally specified.", "BodyX"), PageBreak()]
    # 7 plan
    story += [P("4. Test plan and environment", "H1X"),
      P("Unit testing checks a small part in isolation. Integration testing checks that connected parts work together. System testing exercises the application as a user would. Regression testing repeats checks after a change to catch old problems returning."),
      table([["Level / tool", "How it was used", "Observed outcome"],
        ["Unit-focused · pytest", "OBJ parsing, projection, mesh rules, icon drawing, input and settings helpers.", "58 categorized test functions passed."],
        ["Integration-focused · pytest", "File-open state, page routing, recent files, audio controls and application flow.", "77 categorized test functions passed."],
        ["System QA · headless runner", "Drive app pages, take screenshots, check different sizes and engine edge inputs.", "20 QA invocations completed without reported errors."],
        ["Performance runner", "Three 5-second simulated headless runs.", "Mean frame time and process working set recorded."]], [37*mm, 77*mm, 39*mm]),
      P("Table 4.1: Test levels and tools", "CaptionX"),
      P("Re-run commands", "H2X"),
      P("The commands listed in Appendix A were run from the project root. Test settings were redirected to a temporary LOCALAPPDATA folder so previously saved recent files could not affect the result.", "BodyX"),
      P("The automated tests use unittest-style test cases executed by pytest. The 58/77 split is a report grouping by test module purpose; individual modules can include more than one testing level.", "SmallX"), PageBreak()]
    # 8 unit tests
    story += [P("5. Unit testing", "H1X"),
      table([["Test group", "Examples covered", "Result"],
        ["OBJ parser", "Triangle and polygon faces; face variants; comments; empty/broken files; non-finite values; invalid indices.", "Pass"],
        ["Geometry", "Projection modes, clipping boundaries, transforms, mesh validity, and safe numeric extremes.", "Pass"],
        ["Interface icons", "Every SVG and mesh mark at five sizes; real button placement on four destinations.", "Pass"],
        ["Controls / state", "Input changes, launch flow, settings paths and state preservation after failed load.", "Pass"]], [35*mm, 95*mm, 23*mm]),
      P("Table 5.1: Unit-focused test coverage", "CaptionX"),
      P("Selected parser unit test", "H2X"), *code("tests/test_extensions.py", 78, 85, "Listing 4.1: Polygon closure, unique edges and normalization · tests/test_extensions.py, lines 78–85"),
      P("The parser intentionally supports only positive OBJ vertex indices. Relative negative face indices are rejected; they are not silently treated as supported.", "SmallX"), PageBreak()]
    # 9 code listings
    story += [P("5.1 Code examples from the repository", "H1X"),
      *code("tests/test_launch_flow.py", 176, 194, "Listing 4.2: Icon drawing stays within the icon rectangle · tests/test_launch_flow.py, lines 176–194"),
      *code_segments("renderx/core/obj_loader.py", [(42, 45), (86, 89)], "Listing 4.3: File-size and contextual parser errors · renderx/core/obj_loader.py, lines 42–45 and 86–89"),
      *code("renderx/ui/components/button.py", 8, 26, "Listing 4.4: Shared icon placement helper · renderx/ui/components/button.py, lines 8–26"),
      *old_code(),
      P("The older code is copied from commit 98354b3. It placed the icon at the left edge of the padded content area. Current code calculates a shared rectangle with padding and centering.", "SmallX"), PageBreak()]
    # 10 integration
    story += [P("6. Integration testing", "H1X"),
      P("Integration testing checks whether components agree on shared state. For example, opening an OBJ should add the mesh, select it, and update the saved recent-file list; switching destinations should update the active page and status model."),
      table([["ID", "Connected behavior", "Expected", "Observed"],
        ["IT-01", "OBJ loader → scene/model library → settings", "Successful load selects model and records its path.", "Pass"],
        ["IT-02", "Invalid load → app feedback → existing scene", "Show a readable failure and retain old scene.", "Pass"],
        ["IT-03", "Navigation → destination page state", "Switch page and preserve isolated panel state.", "Pass"],
        ["IT-04", "Visible model → status values", "Status shows current model and its mesh counts.", "Pass"],
        ["IT-05", "Drag/drop or file action → loader", "Supported file path is sent to loader.", "Automated behavior covered; native chooser not verified."]], [14*mm, 47*mm, 50*mm, 42*mm]),
      P("Table 6.1: Integration test cases", "CaptionX"),
      P("Listing 6.1: Integration test for opening an OBJ", "H2X"),
      *code("tests/test_file_open.py", 18, 30, "tests/test_file_open.py, lines 18–30"),
      P("Listing 6.2: Page navigation and status data", "H2X"),
      *code("tests/test_dashboard.py", 56, 67, "tests/test_dashboard.py, lines 56–67"),
      P("The exact checked-in test source is shown above; the surrounding test module uses temporary settings paths for isolation.", "SmallX"), PageBreak()]
    # 11 system
    story += [P("7. System testing", "H1X"),
      P("System testing exercises the application flow with its main pieces connected. The headless runner launched the current app, rendered the destination, injected mouse or keyboard events where needed, and saved the resulting Pygame surface."),
      table([["Step", "User-like action", "Evidence / result"],
        ["1", "Open app and view landing page.", "Current landing screenshot; no welcome skip checkbox."],
        ["2", "Enter Explore and view the built-in cube.", "Cube view, toolbar, panels, and status shown."],
        ["3", "Open a built-in showcase model and file menu.", "House and file menu captures."],
        ["4", "Try an invalid oversized OBJ.", "Readable error feedback captured; scene remains available."],
        ["5", "Open help, preferences, or viewport menu.", "Shortcuts, preferences and context menu captures."],
        ["6", "Visit Challenges, Maze and Shooter pages.", "Current page shell captures; Breakpoint gameplay not included."],
        ["7", "Resize workspace from small to large.", "Eight sizes and 50 rapid resize events passed."],
        ["8", "Close / relaunch flow.", "Launch-flow tests cover app entry and destinations."]], [12*mm, 67*mm, 74*mm]),
      P("Table 7.1: System flow and evidence", "CaptionX"),
      P("The headless test surface is useful for checking layout and app logic. It does not reproduce every Windows desktop behavior, GPU driver, or native operating-system dialog.", "SmallX"), PageBreak()]
    # 12-14 screenshot galleries
    gallery_page(story, "8. Screenshot evidence · application and Explore", [
      ("landing-current.png", "Figure 4.1: Current landing screen. Shows the simplified welcome flow."),
      ("explore-cube.png", "Figure 4.2: Explore with built-in cube, inspector and status area."),
      ("explore-house-loaded.png", "Figure 4.3: Loaded house model in Explore."),
      ("explore-torus-status.png", "Figure 4.4: Current torus view and model-status region.")]); story.append(PageBreak())
    gallery_page(story, "8.1 Screenshot evidence · controls and feedback", [
      ("explore-file-menu.png", "Figure 4.5: File menu and available model actions."),
      ("explore-shortcuts.png", "Figure 4.6: Keyboard shortcuts overlay."),
      ("explore-oversized-obj-error.png", "Figure 4.7: Oversized OBJ rejected with visible feedback."),
      ("preferences.png", "Figure 4.8: Preferences panel from the running interface.")]); story.append(PageBreak())
    gallery_page(story, "8.2 Screenshot evidence · destinations and layout", [
      ("challenges.png", "Figure 4.9: Challenges destination shell."),
      ("maze.png", "Figure 4.10: Maze destination shell."),
      ("shooter.png", "Figure 4.11: Shooter destination shell; this is not live Breakpoint gameplay."),
      ("viewport-context-menu.png", "Figure 4.12: Viewport context menu in Explore.")]); story.append(PageBreak())
    gallery_page(story, "8.3 Screenshot evidence · theme and window sizes", [
      ("explore-light-theme.png", "Figure 4.13: Light theme in Explore."),
      ("explore-small-1024x640.png", "Figure 4.14: Explore at 1024×640."),
      ("explore-large-1920x1080.png", "Figure 4.15: Explore at 1920×1080."),
      ("explore-toolbar-zoom.png", "Figure 4.16: Enlarged crop of real toolbar rendering.")]); story.append(PageBreak())
    # 16 before/after pairs
    evidence = Table([[P("Before / historical evidence", "CellHeadX"), P("Current evidence", "CellHeadX"), P("What it supports", "CellHeadX")],
        [Table([[img("landing-checkbox-before.png", 59*mm, 38*mm)], [P("Figure 4.17: Earlier welcome screen with the checkbox.", "CaptionX")]], [61*mm]),
         Table([[img("landing-current.png", 59*mm, 38*mm)], [P("Current landing page without it.", "CaptionX")]], [61*mm]),
         P("The unwanted 'Don't show this again' option was removed after user feedback.", "CellX")],
        [Table([[img("historical-status-bug-before.png", 59*mm, 38*mm)], [P("Figure 4.18: Historical torus view with stale Cube status.", "CaptionX")]], [61*mm]),
         Table([[img("explore-torus-status.png", 59*mm, 38*mm)], [P("Current torus view and status area.", "CaptionX")]], [61*mm]),
         P("This old image is a genuine repository capture. The current test checks status values against the active torus.", "CellX")],
        [P("No archived before screenshot. Earlier placement code is shown in Listing 4.5 (git 98354b3, lines 29–37).", "SmallX"),
         Table([[img("explore-toolbar-zoom.png", 59*mm, 38*mm)], [P("Figure 4.19: Current toolbar rendering.", "CaptionX")]], [61*mm]),
         P("Current toolbar capture shows the present icon appearance. Pixel-bound tests check that icons retain a margin.", "CellX")]], colWidths=[62*mm, 62*mm, 63*mm])
    evidence.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"), ("GRID",(0,0),(-1,-1),.35,LINE),
        ("BACKGROUND",(0,0),(-1,0),INK), ("BACKGROUND",(0,2),(-1,2),colors.HexColor("#F7FAF9")),
        ("LEFTPADDING",(0,0),(-1,-1),4), ("RIGHTPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",(0,0),(-1,-1),4), ("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story += [P("8.4 Before-and-after evidence", "H1X"),
      P("Only a few historical image captures were available. These pairs use those genuine older screenshots and the matching current capture. For defects without an archived image, the report gives code/test evidence and does not invent a before image."),
      evidence,
      P("Historical status image is an actual repository capture from 21 October 2026; it is not presented as a newly reproduced bug. Current screenshot layout is evidence of current rendering only. Automated tests are the direct check for icon bounds and status values.", "SmallX"),
      P("The icon issue came from a fixed leading offset. Shared placement now adds margin and centers an icon when its label does not fit; pixel-bound tests cover each mark and real button. The status defect used stale model data; the current test compares the status values with the visible torus. The new test-isolation issue came from old in-memory recent paths; the test now starts with an empty list and temporary storage.", "SmallX"), PageBreak()]
    # 17 defects
    story += [P("9. Defects found and regression checks", "H1X"),
      P("A regression check repeats earlier behavior after a change. BUGLOG.md contains the UI and core entries summarized here; RX-TEST-001 was found during this milestone when the full test run used prior application settings."),
      table([["ID / area", "Problem and cause", "Fix and current check"],
        ["RX-UI-001 · Low · UI", "Repeated generic model mark.", "Distinct model/logo drawing; visual captures and UI tests."],
        ["RX-UI-002 · Low · window", "RenderX window icon was missing or wrong.", "Set app icon; app-side check. Breakpoint icon not verified on dummy driver."],
        ["RX-CORE-001 · Medium · projection", "Zero near depth could divide by zero.", "Guard invalid depth; engine edge check."],
        ["RX-CORE-002 · Medium · projection", "Finite extreme coordinates could overflow screen values.", "Clamp/validate projected output; engine edge check."],
        ["RX-UI-003 · Medium · modal", "Help overlay allowed clicks to reach controls behind it.", "Modal event handling; scheduled event check."],
        ["RX-UI-004/007 · Medium · input", "Hover/pressed state could persist after leave or focus loss.", "Clear pointer states; event-schedule checks."],
        ["RX-UI-005 · Low · cursor", "Cursor did not follow hovered control.", "Request cursor state from hover; logic checked, native cursor appearance unverified."],
        ["RX-UI-006 · Low · icons", "Icon touched/overlapped button edge from fixed offsets.", "Shared placement with padding; all-size and real-button tests."],
        ["RX-UI-008 · Low · text", "Unsupported ellipsis glyph raised a font error.", "Use ASCII dots; font tests."],
        ["RX-TEST-001 · Low · test setup", "Recent-file test inherited prior in-memory paths.", "Patch list to empty in test; isolated full suite now passes."]], [35*mm, 64*mm, 88*mm]),
      P("Table 9.1: Recorded defect summary. Severity is assigned for this report based on effect on use; BUGLOG.md itself records fix details.", "CaptionX"), PageBreak()]
    detail_rows = [["ID · severity · area", "How found / reproduction; expected vs actual", "Root cause; fix; current check"]]
    defects = [
      ("RX-UI-001 · Low · object list", "Found in Explore review. Open the object catalog: rows repeated one generic mark instead of showing distinct models.", "ScenePanel used one fixed mesh icon. Mesh previews and a separate RX brand mark were added; current page captures confirm the change."),
      ("RX-UI-002 · Low · window", "Found during window identity review. Start RenderX: expected the RX icon; the runtime default icon remained.", "The display had no shared set_icon call. A shared identity helper was added; headless app run checks RenderX icon call. Breakpoint display is unavailable in dummy mode."),
      ("RX-CORE-001 · Medium · projection", "Engine edge case: project a point at depth 0 with near plane 0. It should be rejected, but previously raised ZeroDivisionError.", "Depth guard allowed zero through when near was zero. Reject nonpositive depth; engine_edges.py now checks zero/negative values and valid clipped points."),
      ("RX-CORE-002 · Medium · projection", "Engine edge case: project finite coordinates near 1e308. Expected a rejected point; old code returned infinite screen coordinates.", "Output finiteness was not checked after scaling. Validate projected values; engine_edges.py checks extreme perspective and orthographic inputs."),
      ("RX-UI-003 · Medium · help overlay", "Open help and click a destination behind it. Expected the overlay to consume the click; previously the page changed underneath it.", "Only keyboard input was modal. Mouse/wheel/text input is captured and outside click dismisses; replayed event schedules confirm first click is consumed."),
      ("RX-UI-004 · Medium · pointer state", "Hover a button, then send WINDOWLEAVE or lose focus while pressed. Expected hover and press to clear; old state remained recorded.", "Leave/focus handlers did not reset pointer state. Clear hover and press; interaction schedules check empty state."),
      ("RX-UI-005 · Low · cursor", "Move over button, numeric field, slider, and splitter. Expected matching pointer shapes; the system arrow stayed active.", "No cursor mapping followed hit testing. Added cursor requests; headless checks see hand then arrow, but native appearance needs desktop verification."),
      ("RX-UI-006 · Low · compact button", "At 1024×640 inspect narrow icon buttons. Expected no label when it cannot fit; ellipsis could overlap the icon.", "Text truncation drew ellipsis even when too wide. Omit it when it cannot fit; typography audit and minimum-size layout check pass."),
      ("RX-UI-007 · Medium · pressed state", "Press and hold a control, then move pointer outside the window. Expected the pressed visual to clear; it previously remained.", "Window-leave cleared hover but not pressed action. Clear both while allowing drag release; scheduled hold/leave test confirms state clears."),
      ("RX-UI-008 · Low · text rendering", "Draw a compact long label whose available width only fits truncation. Expected safe text; unsupported Unicode ellipsis raised a Pygame glyph error.", "Bundled font lacks that glyph. Use ASCII dots; focused typography tests and final pytest run pass."),
      ("RX-TEST-001 · Low · test isolation", "After OBJ paths were saved in memory, run file-open test. Expected the sample path only; test inherited prior paths and failed.", "The test patched file path but not in-memory list. Patch list empty and use temp settings; focused and isolated full suite now pass.")]
    for bug_id, reproduction, fix in defects:
        detail_rows.append([bug_id, "Found / reproduce: " + reproduction,
                           "Cause / fix / check: " + fix])
    detailed = Table([[P(str(c), "CellHeadX" if r == 0 else "DetailX") for c in row]
                      for r, row in enumerate(detail_rows)], colWidths=[32*mm, 70*mm, 65*mm], repeatRows=1)
    detailed.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"), ("GRID",(0,0),(-1,-1),.35,LINE),
        ("BACKGROUND",(0,0),(-1,0),INK), ("LEFTPADDING",(0,0),(-1,-1),3),
        ("RIGHTPADDING",(0,0),(-1,-1),3), ("TOPPADDING",(0,0),(-1,-1),3),
        ("BOTTOMPADDING",(0,0),(-1,-1),3)]))
    story += [P("9.1 Defect details", "H1X"), P("Each entry records the reproduction or discovery, expected and actual behavior, cause, fix, and check. Severity is assigned for this report.", "SmallX"), detailed, PageBreak()]
    # 19 performance security
    story += [P("10. Performance and basic security", "H1X"),
      P("Performance method", "H2X"), P("The QA runner simulated three 5-second scenarios under SDL's dummy video driver. It ran 300 frames for each scenario. Mean frame time is reported. Reciprocal FPS is calculated as 1,000 divided by mean milliseconds; it is not an in-game FPS measurement."),
      img(str(SOURCE / "chart-fps.png"), 150*mm, 71*mm),
      table([["Scenario", "Mean", "p95 / p99", "Reciprocal", "Peak process WS"],
        ["Idle Explore", "8.673 ms", "15.084 / 16.656 ms", "115.3 fps", "62.0 MiB"],
        ["Orbit input", "8.803 ms", "14.735 / 16.421 ms", "113.6 fps", "62.2 MiB"],
        ["Signal wave", "23.729 ms", "30.725 / 34.341 ms", "42.1 fps", "62.3 MiB"]], [33*mm, 25*mm, 43*mm, 35*mm, 31*mm]),
      P("Peak process working set includes Python and its libraries, not only RenderX. Minimum FPS and OBJ import duration were not measured. The external large model's load speed was not measured.", "SmallX"),
      P("Table 10.1: Short headless timing and process-memory results", "CaptionX"),
      P("Basic security review", "H2X"), P("RenderX is an offline desktop app. The OBJ loader enforces a 2 MB file limit, 20,000 vertex limit, and 50,000 unique-edge limit. It rejects non-finite coordinates, unsupported negative indices, malformed faces, and out-of-range references with a ValueError. The file data is parsed as text; the parser does not evaluate it as Python code. Login and network attack checks do not apply to this offline app scope. No penetration test or automated security scan was performed.", "BodyX"), PageBreak()]
    # 20 charts and validation
    story += [P("11. Results and validation", "H1X"),
      P("The final isolated run completed 135 pytest test functions, 36 unittest subtests, and one warning. A warning remains because the shooter imports PyGLM as `glm`; it is marked pending deprecation. The engine edge runner passed 12 checks, resize QA passed eight sizes plus 50 rapid changes, current UI capture runner completed 15 app scenarios, and three performance scenarios completed. Ten application defects (eight UI, two core) and one test-isolation issue are fixed and checked in current code; the Breakpoint window icon and native cursor appearance still need a visible desktop check."),
      img(str(SOURCE / "chart-tests.png"), 150*mm, 71*mm),
      img(str(SOURCE / "chart-defects.png"), 150*mm, 71*mm),
      table([["Req.", "Status", "Evidence / limit"], ["R1", "Met in tested paths", "Built-in samples and fixture load tested."],
        ["R2", "Met within loader scope", "Bounds and malformed input checks passed; negative indices are unsupported."],
        ["R3", "Met in covered cases", "Status test verifies current torus counts."],
        ["R4", "Partly met", "Core and Explore behavior tested; no broad GPU renderer timing claim."],
        ["R5", "Met in automated layout tests", "Icon bounds tested; native display appearance not confirmed."],
        ["R6", "Met for destination shells", "Page tests and captures; Shooter game loop excluded."],
        ["R7", "Met for tested window matrix", "Eight sizes plus rapid resizing; does not cover every monitor/DPI."],
        ["R8", "Met for parser failure path", "Oversize error and state-preservation checks passed."]], [15*mm, 39*mm, 113*mm]),
      P("Table 12.1: Provisional requirement validation", "CaptionX"), PageBreak()]
    # 21 conclusion
    story += [P("12. Conclusion and future scope", "H1X"),
      P("The tested RenderX code passed the isolated automated suite. The tests cover geometry, a safe subset of OBJ parsing, screen layout, navigation and file-open state. QA scripts also exercised several screen sizes and captured the current interface. During this work, a test that depended on old recent-file state was fixed and the full suite passed again."),
      P("The results support the tested behaviors, but they do not prove every desktop environment or GPU path works. The Shooter destination shell was captured, but live OpenGL Breakpoint gameplay was not verified on a real display. File-load speed for large models was not measured. The headless frame timings should not be compared directly with a visible game FPS counter."),
      P("Future work", "H2X"), table([["Area", "Possible next step"], ["Input format", "Support relative negative OBJ indices and additional OBJ data carefully."],
        ["Performance", "Measure on a visible display and time several file sizes on named hardware."],
        ["Desktop QA", "Check actual Windows cursor, native file chooser, DPI scaling and GPU paths."],
        ["Testing", "Add automated checks for more user workflows and structured security review."]], [43*mm, 124*mm]),
      P("What we learned", "H2X"), table([["Cause", "Lesson"], ["Hard-coded sizes", "Measure and center interface content against its real rectangle."],
        ["Stale displayed data", "Use the active page's model when building status values."],
        ["Missing input checks", "Treat external geometry files as untrusted input and cap work."],
        ["Shared test state", "Reset settings and in-memory state so tests do not depend on run order."]], [48*mm, 119*mm]),
      P("References", "H2X"), P("[1] Python Software Foundation. Python 3 documentation. https://docs.python.org/3/", "SmallX"),
      P("[2] Pygame community. Pygame documentation. https://www.pygame.org/docs/", "SmallX"),
      P("[3] pytest development team. pytest documentation. https://docs.pytest.org/en/stable/", "SmallX"),
      P("[4] RenderX repository source, test modules, FEATURES.md, BUGLOG.md, and tools/qa scripts; commit history inspected during this report.", "SmallX"), PageBreak()]
    # 22 appendix
    story += [P("Appendix A–C: Re-run details and limitations", "H1X"),
      P("Appendix A · Commands", "H2X"),
      P("Listing A.1: Commands used to reproduce the main checks", "CodeCapX"),
      Preformatted("$env:LOCALAPPDATA = Join-Path $env:TEMP 'renderx-m04-test-local'\n.\\.venv\\Scripts\\python.exe -m pytest -q\n.\\.venv\\Scripts\\python.exe tools\\qa\\engine_edges.py\n.\\.venv\\Scripts\\python.exe tools\\qa\\resize_matrix.py <temporary-output-folder>\n.\\.venv\\Scripts\\python.exe tools\\qa\\performance_runs.py --seconds 5\n.\\.venv\\Scripts\\python.exe output\\milestone_04\\source\\capture_screenshots.py\n.\\.venv\\Scripts\\python.exe output\\milestone_04\\source\\build_report.py", CODE),
      P("Appendix B · Test modules", "H2X"),
      table([["Files", "Focus"], ["test_core, test_engine, test_extensions", "Core geometry, renderer, parser and extension rules."],
        ["test_dashboard, test_launch_flow, test_interaction", "Navigation, UI layout, startup and interaction."],
        ["test_file_open, test_settings_path, test_window", "File workflow, persistent paths and window behavior."],
        ["test_maze, test_quest, test_shooter, test_audio", "Destination/game state and audio behavior."],
        ["test_comparison, test_input_map, test_ui_fonts", "Comparison, input mapping and font/UI checks."]], [60*mm, 107*mm]),
      P("Table B.1: Test modules grouped by focus", "CaptionX"),
      P("Appendix C · Not measured or not confirmed", "H2X"),
      P("Native screen size and GPU model; actual hardware-rendered FPS and minimum FPS; OBJ load time; live Breakpoint gameplay; Windows file chooser appearance; native cursor visibility; every monitor scale; security penetration testing. Explore has a default Cube rather than an empty state; empty-file rejection was tested in the OBJ parser. The user's external model file is larger than the educational OBJ loader's 2 MB limit and was not imported during this report run."),
      P("Appendix D · Fill before submission", "H2X"),
      P("Add your name, roll number, section, faculty name, college, and submission date. Compare R1–R8 with the official requirements in earlier milestones and replace provisional IDs where needed. Review the declaration and acknowledgement names.")]
    ReportDoc(out).build(story)
    print(out)

def build_viva():
    out = OUT / "RenderX_Milestone_04_Viva_Cheat_Sheet.pdf"
    qas = [
      ("1. What is unit testing?", "Testing one small part by itself, such as the OBJ parser or a geometry helper."),
      ("2. What is integration testing?", "Checking connected parts, such as an OBJ load updating the model list and recent-file settings."),
      ("3. What is system testing?", "Exercising the app flow through its pages and controls."),
      ("4. What does regression testing check?", "It repeats earlier checks after changes so a fixed behavior does not break again."),
      ("5. What did the final test run report?", "135 pytest test functions passed, 36 subtests passed, and one PyGLM pending-deprecation warning remained."),
      ("6. Why is an OBJ file risky input?", "It comes from outside the program and can contain malformed values or huge geometry."),
      ("7. What limits does this OBJ loader use?", "2 MB per file, 20,000 vertices and 50,000 unique edges."),
      ("8. Does it support negative OBJ indices?", "No. The current parser accepts positive vertex indices and rejects negative relative indices."),
      ("9. What was the icon bug?", "Icons could sit against button edges because their positions used fixed offsets. Shared placement and bounds tests now check margins."),
      ("10. What was the status bar bug?", "It could show stale model details. A current test checks that status counts match the visible torus."),
      ("11. What is the performance result?", "Headless mean frame time ranged from 8.673 to 23.729 ms. Reciprocal FPS is calculated from those means, not measured in a live game."),
      ("12. Was large OBJ import speed measured?", "No. OBJ load time was not measured."),
      ("13. Was the OpenGL Shooter gameplay tested?", "The page shell was captured, but live Breakpoint gameplay was not verified on a visible display."),
      ("14. What new test issue was fixed?", "The recent-file test inherited old in-memory settings. It now starts with an empty list and the isolated suite passes."),
      ("15. What should be improved next?", "Measure visible-display performance, test native Windows behavior, and broaden safe OBJ support.")]
    story = [P("RenderX", "TitleX"), P("Milestone 04 · Viva cheat sheet", "SubX"),
             P("Short answers based on the current report evidence", "CaptionX"), Spacer(1, 4)]
    for q, a in qas:
        story += [P(q, "H2X"), P(a, "SmallX")]
    story += [Spacer(1, 3), HRFlowable(width="100%", thickness=1, color=MINT),
              P("Remember: distinguish what was tested from what was not measured. The report’s requirement IDs are provisional until matched to earlier milestones.", "SmallX")]
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=19*mm, rightMargin=19*mm,
                            topMargin=14*mm, bottomMargin=14*mm, title="RenderX Viva Cheat Sheet")
    doc.build(story)
    print(out)

if __name__ == "__main__":
    build_main()
    build_viva()
