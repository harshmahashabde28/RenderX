from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, Image, NextPageTemplate, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle, XPreformatted,
)
from reportlab.platypus.tableofcontents import TableOfContents


ROOT = Path(__file__).resolve().parents[2]
MATERIALS = ROOT / "output" / "milestone_04" / "raw_materials"
PHOTOS = MATERIALS / "photos"
OUT = ROOT / "output" / "pdf" / "RenderX_Milestone_04_Testing_and_Validation.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)

INK = colors.HexColor("#16252A")
MUTED = colors.HexColor("#58696D")
TEAL = colors.HexColor("#198E7B")
MINT = colors.HexColor("#67CDB5")
PALE = colors.HexColor("#EAF7F3")
PAPER = colors.HexColor("#F8FBFA")
LINE = colors.HexColor("#D5E3DF")
WHITE = colors.white
PAGE_W, PAGE_H = A4
LEFT = RIGHT = 17 * mm
TOP = 20 * mm
BOTTOM = 17 * mm
BODY_W = PAGE_W - LEFT - RIGHT

FONT_DIR = ROOT / "assets" / "fonts"
pdfmetrics.registerFont(TTFont("Inter", str(FONT_DIR / "Inter-Variable.ttf")))
pdfmetrics.registerFont(TTFont("PlexMono", str(FONT_DIR / "IBM-Plex-Mono-Regular.ttf")))

base_styles = getSampleStyleSheet()
styles = {
    "h1": ParagraphStyle("RXH1", fontName="Inter", fontSize=17, leading=21,
                         textColor=INK, spaceBefore=8, spaceAfter=11, keepWithNext=True),
    "h2": ParagraphStyle("RXH2", fontName="Inter", fontSize=12.2, leading=16,
                         textColor=TEAL, spaceBefore=10, spaceAfter=6, keepWithNext=True),
    "h3": ParagraphStyle("RXH3", fontName="Inter", fontSize=9.4, leading=12,
                         textColor=INK, spaceBefore=7, spaceAfter=3, keepWithNext=True),
    "body": ParagraphStyle("RXBody", fontName="Inter", fontSize=8.6, leading=12.2,
                           textColor=INK, spaceAfter=5, alignment=TA_LEFT,
                           allowWidows=0, allowOrphans=0),
    "bullet": ParagraphStyle("RXBullet", fontName="Inter", fontSize=8.4, leading=11.5,
                             textColor=INK, leftIndent=12, firstLineIndent=-8,
                             bulletIndent=0, spaceAfter=3),
    "quote": ParagraphStyle("RXQuote", fontName="Inter", fontSize=8.2, leading=11.5,
                            textColor=MUTED, leftIndent=12, rightIndent=12,
                            borderColor=MINT, borderWidth=2, borderPadding=7,
                            backColor=PALE, spaceBefore=4, spaceAfter=8),
    "small": ParagraphStyle("RXSmall", fontName="Inter", fontSize=7.1, leading=9.4,
                            textColor=MUTED, spaceAfter=3),
    "table_caption": ParagraphStyle("RXTableCaption", fontName="Inter", fontSize=7.1,
                                    leading=9.4, textColor=MUTED, spaceAfter=3,
                                    keepWithNext=True),
    "source_caption": ParagraphStyle("RXSourceCaption", fontName="Inter", fontSize=7.1,
                                     leading=9.4, textColor=TEAL, spaceAfter=4,
                                     keepWithNext=True),
    "table": ParagraphStyle("RXTable", fontName="Inter", fontSize=6.5, leading=8.5,
                            textColor=INK, spaceAfter=0),
    "table_head": ParagraphStyle("RXTableHead", fontName="Inter", fontSize=6.7,
                                 leading=8.5, textColor=WHITE, spaceAfter=0),
    "code": ParagraphStyle("RXCode", fontName="PlexMono", fontSize=6.1, leading=8,
                           textColor=INK, leftIndent=4, rightIndent=4, spaceAfter=0),
}


def inline_markup(text: str) -> str:
    text = text.translate(str.maketrans({"–": "-", "—": "-", "‑": "-", "−": "-", "×": "x", "·": "/", "�": "-"}))
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<font name='PlexMono' color='#246F65'>\1</font>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"<link href='\2' color='#198E7B'>\1</link>", text)
    return text


class PipelineDiagram(Flowable):
    def __init__(self, width=BODY_W, height=94):
        super().__init__()
        self.width = width
        self.height = height

    def draw(self):
        c = self.canv
        c.setFillColor(PAPER)
        c.setStrokeColor(LINE)
        c.roundRect(0, 0, self.width, self.height, 8, fill=1, stroke=1)
        labels = [
            ("UI & input", "Pygame"),
            ("Mesh + scene", "Transforms"),
            ("Camera", "Clip + project"),
            ("Software renderer", "Explore / Maze"),
        ]
        gap = 12
        box_w = (self.width - 32 - gap * 3) / 4
        x = 16
        y = 36
        for i, (title, sub) in enumerate(labels):
            c.setFillColor(WHITE)
            c.setStrokeColor(LINE)
            c.roundRect(x, y, box_w, 38, 5, fill=1, stroke=1)
            c.setFillColor(INK)
            c.setFont("Inter", 7.4)
            c.drawCentredString(x + box_w / 2, y + 23, title)
            c.setFillColor(MUTED)
            c.setFont("Inter", 6.5)
            c.drawCentredString(x + box_w / 2, y + 10, sub)
            if i < len(labels) - 1:
                c.setStrokeColor(TEAL)
                c.setLineWidth(1.1)
                ax = x + box_w + 2
                c.line(ax, y + 19, ax + gap - 4, y + 19)
                c.line(ax + gap - 7, y + 22, ax + gap - 4, y + 19)
                c.line(ax + gap - 7, y + 16, ax + gap - 4, y + 19)
            x += box_w + gap
        c.setFillColor(TEAL)
        c.setFont("Inter", 7)
        c.drawCentredString(self.width / 2, 13,
                            "Breakpoint uses a separate OpenGL 3.3 game renderer")


class RXDocTemplate(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(filename, pagesize=A4, leftMargin=LEFT, rightMargin=RIGHT,
                         topMargin=TOP, bottomMargin=BOTTOM,
                         title="RenderX - Milestone 04: Testing and Validation",
                         author="RenderX project")
        cover_frame = Frame(LEFT, 15 * mm, BODY_W, PAGE_H - 30 * mm,
                            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
                            id="cover")
        body_frame = Frame(LEFT, BOTTOM, BODY_W, PAGE_H - TOP - BOTTOM,
                           leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
                           id="body")
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[cover_frame], onPage=self.cover_page),
            PageTemplate(id="body", frames=[body_frame], onPage=self.body_page),
        ])

    def cover_page(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#102027"))
        canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        canvas.setFillColor(TEAL)
        canvas.rect(0, PAGE_H - 7 * mm, PAGE_W, 7 * mm, fill=1, stroke=0)
        canvas.setStrokeColor(colors.HexColor("#25444A"))
        canvas.setLineWidth(0.6)
        for i in range(5):
            canvas.circle(PAGE_W - 12 * mm - i * 13 * mm, PAGE_H - 19 * mm,
                          (i + 1) * 3 * mm, stroke=1, fill=0)
        canvas.restoreState()

    def body_page(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(WHITE)
        canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.5)
        canvas.line(LEFT, PAGE_H - 12 * mm, PAGE_W - RIGHT, PAGE_H - 12 * mm)
        canvas.setFillColor(TEAL)
        canvas.setFont("Inter", 7.2)
        canvas.drawString(LEFT, PAGE_H - 9.6 * mm, "RENDERX  /  MILESTONE 04")
        canvas.setFillColor(MUTED)
        canvas.setFont("Inter", 7)
        canvas.drawRightString(PAGE_W - RIGHT, PAGE_H - 9.6 * mm,
                               "TESTING & VALIDATION")
        canvas.setStrokeColor(LINE)
        canvas.line(LEFT, 11 * mm, PAGE_W - RIGHT, 11 * mm)
        canvas.setFillColor(MUTED)
        canvas.setFont("PlexMono", 6.5)
        canvas.drawString(LEFT, 7.2 * mm, "RENDERX  /  PYTHON / PYGAME")
        canvas.drawRightString(PAGE_W - RIGHT, 7.2 * mm, f"{doc.page:02d}")
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return
        style = flowable.style.name
        if style not in ("RXH1", "RXH2"):
            return
        text = flowable.getPlainText()
        level = 0 if style == "RXH1" else 1
        key = f"sec-{self.page}-{len(text)}-{abs(hash(text)) % 1000000}"
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text, key, level=level, closed=False)
        self.notify("TOCEntry", (level, text, self.page, key))


def table_from_markdown(lines, table_no, section_name):
    data = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells):
            continue
        cells = [Paragraph(inline_markup(cell), styles["table_head"] if not data else styles["table"])
                 for cell in cells]
        data.append(cells)
    if not data:
        return []
    cap_text = re.sub(r"^\d+(?:\.\d+)*\.?\s*", "", section_name)
    cap = Paragraph(f"<b>Table {table_no}.</b> {inline_markup(cap_text)}", styles["table_caption"])
    col_widths = [BODY_W / len(data[0])] * len(data[0])
    tbl = Table(data, colWidths=col_widths, repeatRows=1, hAlign="LEFT", splitByRow=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PAPER]),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3.3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.3),
    ]))
    return [cap, tbl, Spacer(1, 6)]


def parse_report():
    text = (MATERIALS / "report_content.md").read_text(encoding="utf-8")
    lines = text.splitlines()
    story = []

    # Cover page: this document continues completed project milestones.
    story.append(Spacer(1, 24 * mm))
    logo = Image(str(PHOTOS / "renderx-logo.png"), width=145 * mm, height=33 * mm,
                 kind="proportional", hAlign="CENTER")
    story.extend([logo, Spacer(1, 20 * mm)])
    story.append(Paragraph("MILESTONE 04  /  CONTINUATION", ParagraphStyle(
        "CoverKicker", fontName="Inter", fontSize=10, leading=14,
        textColor=MINT, alignment=TA_CENTER, spaceAfter=8)))
    story.append(Paragraph("Testing &amp; Validation", ParagraphStyle(
        "CoverTitle", fontName="Inter", fontSize=29, leading=34,
        textColor=WHITE, alignment=TA_CENTER, spaceAfter=7)))
    story.append(Paragraph("From Learning Laboratory to the current RenderX application", ParagraphStyle(
        "CoverSub", fontName="Inter", fontSize=10.2, leading=15,
        textColor=colors.HexColor("#B8C7C9"), alignment=TA_CENTER)))
    story.append(Spacer(1, 13 * mm))
    story.append(Paragraph(
        "This milestone continues the three reports already submitted. It records what changed after the GitHub Learning Laboratory version and validates the current RenderX build.",
        ParagraphStyle("CoverFoot", fontName="Inter", fontSize=10, leading=16,
                       textColor=colors.HexColor("#B8C7C9"), alignment=TA_CENTER,
                       leftIndent=22 * mm, rightIndent=22 * mm)))
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph(
        "CHANGE SUMMARY   Learning Laboratory → current RenderX<br/>VALIDATION   Automated tests · responsive checks · defect retesting · performance evidence",
        ParagraphStyle("CoverScope", fontName="Inter", fontSize=8.2, leading=14,
                       textColor=MINT, alignment=TA_CENTER)))
    story.append(NextPageTemplate("body"))
    story.append(PageBreak())

    # Begin with a linked contents page; the prior project milestones are already submitted.
    story.append(Paragraph("Contents", styles["h1"]))
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle("TOC0", fontName="Inter", fontSize=8.1, leading=12,
                       textColor=INK, leftIndent=0, firstLineIndent=0, spaceBefore=2),
        ParagraphStyle("TOC1", fontName="Inter", fontSize=7.1, leading=10,
                       textColor=MUTED, leftIndent=14, firstLineIndent=0),
    ]
    story.append(toc)
    story.append(Paragraph("Figure and table lists", styles["h1"]))
    figure_names = [
        "1. Component overview", "2. Current landing screen", "3. Explore workspace",
        "4. Imported sample OBJ", "5. Challenges destination", "6. Maze destination",
        "7. Breakpoint destination (headless)", "8. Explore light theme", "9. Preferences",
        "10. File menu", "11. Shortcut overlay", "12. Viewport context menu",
        "13. Torus and status strip", "14. Compact layout, 1024 x 640",
        "15. Large layout, 1920 x 1080", "16. Over-limit OBJ feedback",
        "17. Enlarged toolbar crop", "18. Historical landing screen",
        "19. Automated test and system QA counts", "20. Headless performance results",
        "21. Defect entries by area",
    ]
    table_names = [
        "1. Compared versions", "2. Current feature changes", "3. Local milestones",
        "4. Environment", "5. Automated verification",
        "6. Performance measurements", "7. Defect summary",
        "8. Test cases and outcomes", "9. Detailed defect register",
        "10. Unmeasured items", "11. What we learned",
    ]
    def listing(items):
        return [Paragraph(inline_markup(item), styles["small"]) for item in items]
    list_table = Table([[listing(figure_names), listing(table_names)]],
                       colWidths=[BODY_W * 0.51, BODY_W * 0.49], hAlign="LEFT")
    list_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.4, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, LINE),
        ("BACKGROUND", (0, 0), (-1, -1), PAPER),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(list_table)
    story.append(PageBreak())

    # Convert the editable Markdown report to styled, searchable PDF content.
    # Personal fields/front matter above are rendered as custom components.
    start = next((i for i, line in enumerate(lines) if line.startswith("## 1. Milestone 04 scope")), None)
    if start is None:
        raise RuntimeError("Could not find the report body start")
    i = start
    current_section = "Project report"
    table_no = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.strip() == "---":
            i += 1
            continue
        if line.startswith("```"):
            language = line[3:].strip().lower()
            i += 1
            code = []
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            # Light, ruled listing panel with preserved exact source text.
            pre = XPreformatted(html.escape("\n".join(code)), styles["code"])
            panel = Table([[pre]], colWidths=[BODY_W])
            panel.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0F5F3")),
                ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                ("LINEBEFORE", (0, 0), (0, 0), 2, MINT),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.extend([panel, Spacer(1, 6)])
            continue
        if line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].startswith("|"):
                table_lines.append(lines[i])
                i += 1
            table_no += 1
            story.extend(table_from_markdown(table_lines, table_no, current_section))
            continue
        if line.startswith("# "):
            i += 1
            continue
        if line.startswith("## "):
            current_section = line[3:].strip()
            story.append(Paragraph(inline_markup(current_section), styles["h1"]))
            if current_section == "3. System overview":
                story.append(Paragraph("Figure 1. RenderX component overview", styles["small"]))
                story.append(PipelineDiagram())
                story.append(Spacer(1, 6))
            i += 1
            continue
        if line.startswith("### "):
            title = line[4:].strip()
            current_section = title
            story.append(Paragraph(inline_markup(title), styles["h2"]))
            i += 1
            continue
        if line.startswith("#### "):
            story.append(Paragraph(inline_markup(line[5:].strip()), styles["h3"]))
            i += 1
            continue
        if line.startswith("> "):
            story.append(Paragraph(inline_markup(line[2:].strip()), styles["quote"]))
            i += 1
            continue
        if re.match(r"^\s*[-*] ", line):
            item = re.sub(r"^\s*[-*] ", "", line)
            story.append(Paragraph("• " + inline_markup(item), styles["bullet"]))
            i += 1
            continue
        ordered = re.match(r"^(\d+)\. (.*)$", line)
        if ordered:
            story.append(Paragraph(f"<b>{ordered.group(1)}.</b> {inline_markup(ordered.group(2))}", styles["bullet"]))
            i += 1
            continue
        para = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "|", "```", "> ")) and not re.match(r"^\s*[-*] ", lines[i]) and not re.match(r"^\d+\. ", lines[i]):
            para.append(lines[i].strip())
            i += 1
        story.append(Paragraph(inline_markup(" ".join(para)), styles["body"]))

    # Screenshot gallery: each image is preserved as a loose source PNG and captioned.
    story.append(PageBreak())
    story.append(Paragraph("Appendix B - Screenshot evidence", styles["h1"]))
    story.append(Paragraph("Screenshots were taken from the real application through the recorded headless scenarios. The Breakpoint image shows its destination state, not live GPU gameplay. Historical captures are clearly marked.", styles["body"]))

    figures = [
        ("landing-current.png", "Figure 2. Current landing screen. Shows the application start page and main entry action."),
        ("explore-cube.png", "Figure 3. Explore workspace. Shows the default mesh, viewport, panels, and status strip."),
        ("explore-house-loaded.png", "Figure 4. Loaded sample OBJ. Shows the imported house mesh in the renderer."),
        ("challenges.png", "Figure 5. Challenges destination. Shows the current graphics exercise interface."),
        ("maze.png", "Figure 6. Maze destination. Shows the first-person wireframe campaign view."),
        ("shooter.png", "Figure 7. Breakpoint destination. This headless capture does not prove live OpenGL combat."),
        ("explore-light-theme.png", "Figure 8. Light theme. Shows the alternate interface palette."),
        ("preferences.png", "Figure 9. Preferences. Shows application settings and audio controls."),
        ("explore-file-menu.png", "Figure 10. File menu. Shows file and recent-file actions."),
        ("explore-shortcuts.png", "Figure 11. Shortcut overlay. Shows contextual keyboard help."),
        ("viewport-context-menu.png", "Figure 12. Viewport context menu. Shows secondary viewport actions."),
        ("explore-torus-status.png", "Figure 13. Alternate mesh and status. Shows the torus selection and live scene information."),
        ("explore-small-1024x640.png", "Figure 14. Compact layout at 1024 × 640."),
        ("explore-large-1920x1080.png", "Figure 15. Large layout at 1920 × 1080."),
        ("explore-oversized-obj-error.png", "Figure 16. Over-limit OBJ message. Shows controlled feedback for a file above the configured size cap."),
        ("explore-toolbar-zoom.png", "Figure 17. Enlarged toolbar crop from the current Explore screenshot."),
        ("landing-checkbox-before.png", "Figure 18. Historical landing screen before the unwanted checkbox was removed."),
    ]
    cells = []
    for idx in range(0, len(figures), 2):
        row = []
        for filename, caption in figures[idx:idx + 2]:
            img_path = PHOTOS / filename
            img = Image(str(img_path), width=BODY_W / 2 - 12, height=74 * mm,
                        kind="proportional", hAlign="CENTER")
            cap = Paragraph(inline_markup(caption), styles["small"])
            row.append([img, Spacer(1, 3), cap])
        if len(row) == 1:
            row.append(Paragraph("", styles["small"]))
        cells.append(row)
    for pair in cells:
        gallery = Table([[cell for cell in pair]], colWidths=[BODY_W / 2] * 2,
                        hAlign="LEFT")
        gallery.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        story.append(gallery)
        story.append(Spacer(1, 6))

    story.append(PageBreak())
    story.append(Paragraph("Appendix C - Charts", styles["h1"]))
    story.append(Paragraph("The performance chart shows the reciprocal of mean frame time from headless runs. It is not a native GPU frame-rate result.", styles["body"]))
    for filename, caption in [
        ("chart-tests.png", "Figure 19. Automated test and system QA run counts from the recorded evidence."),
        ("chart-fps.png", "Figure 20. Headless frame-time measurements shown as reciprocal average frame rate."),
        ("chart-defects.png", "Figure 21. Recorded defect entries grouped by area."),
    ]:
        chart = Image(str(PHOTOS / filename), width=BODY_W - 14 * mm,
                      height=67 * mm, kind="proportional", hAlign="CENTER")
        story.extend([Spacer(1, 5), chart, Paragraph(inline_markup(caption), styles["small"]), Spacer(1, 8)])

    # Copy-ready detailed test cases and defect records.
    story.append(PageBreak())
    append_markdown(story, MATERIALS / "test_and_defect_appendices.md", 8)

    # Exact code excerpts and rerun commands, including the earlier button version.
    story.append(PageBreak())
    append_markdown(story, MATERIALS / "code_listings.md", 20)
    return story


def append_markdown(story, path: Path, table_no: int):
    lines = path.read_text(encoding="utf-8").splitlines()
    current_section = path.stem.replace("_", " ").title()
    listing_heading = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.strip() == "---":
            i += 1
            continue
        if line.startswith("```"):
            i += 1
            code = []
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            pre = XPreformatted(html.escape("\n".join(code)), styles["code"])
            panel = Table([[pre]], colWidths=[BODY_W])
            panel.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0F5F3")),
                ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                ("LINEBEFORE", (0, 0), (0, 0), 2, MINT),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.extend([panel, Spacer(1, 6)])
            continue
        if line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].startswith("|"):
                table_lines.append(lines[i])
                i += 1
            table_no += 1
            story.extend(table_from_markdown(table_lines, table_no, current_section))
            continue
        if line.startswith("# "):
            story.append(Paragraph(inline_markup(line[2:].strip()), styles["h1"]))
            listing_heading = False
            i += 1
            continue
        if line.startswith("## "):
            current_section = line[3:].strip()
            story.append(Paragraph(inline_markup(current_section), styles["h1"]))
            listing_heading = current_section.startswith("Listing ")
            i += 1
            continue
        if line.startswith("### "):
            current_section = line[4:].strip()
            story.append(Paragraph(inline_markup(current_section), styles["h2"]))
            listing_heading = False
            i += 1
            continue
        if line.startswith("#### "):
            story.append(Paragraph(inline_markup(line[5:].strip()), styles["h3"]))
            listing_heading = False
            i += 1
            continue
        if line.startswith("> "):
            story.append(Paragraph(inline_markup(line[2:].strip()), styles["quote"]))
            i += 1
            continue
        if re.match(r"^\s*[-*] ", line):
            story.append(Paragraph("• " + inline_markup(re.sub(r"^\s*[-*] ", "", line)), styles["bullet"]))
            i += 1
            continue
        ordered = re.match(r"^(\d+)\. (.*)$", line)
        if ordered:
            story.append(Paragraph(f"<b>{ordered.group(1)}.</b> {inline_markup(ordered.group(2))}", styles["bullet"]))
            i += 1
            continue
        para = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "|", "```", "> ")) and not re.match(r"^\s*[-*] ", lines[i]) and not re.match(r"^\d+\. ", lines[i]):
            para.append(lines[i].strip())
            i += 1
        paragraph_style = styles["source_caption"] if listing_heading else styles["body"]
        story.append(Paragraph(inline_markup(" ".join(para)), paragraph_style))
        listing_heading = False


def main():
    doc = RXDocTemplate(str(OUT))
    doc.multiBuild(parse_report())
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
