"""
Viajera Digital — Export Generation (PDF, TXT, JSON)
Vintage Cuban Literary Style
"""

import os
import json
import random
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Flowable,
)

from models import ProcessResult

W, H = letter

# ─── Color Palette ───
PARCHMENT_BASE  = HexColor("#F5E6C8")
PARCHMENT_EDGE  = HexColor("#D4B896")
PARCHMENT_STAIN = HexColor("#C8A878")
DARK_SEPIA      = HexColor("#3C2415")   # Deep brown for text/borders
MID_SEPIA       = HexColor("#6B4226")   # Medium brown for headers
GOLDEN_ACCENT   = HexColor("#8B6914")   # Golden brown for ornaments
LIGHT_ACCENT    = HexColor("#A0845C")   # Light brown for subtle elements
BANNER_BG       = HexColor("#2C1810")   # Very dark brown for banner
BANNER_TEXT     = HexColor("#F0DDB8")   # Cream for text on dark banner
BORDER_COLOR    = HexColor("#5C3A1E")   # Border lines

# ─── Ornamental Characters ───
ORNAMENT_DIAMOND = "◆"
ORNAMENT_FLEUR   = "❧"
ORNAMENT_STAR    = "✦"


# --- Helpers ---

def _esc(text):
    """Escape XML special characters for reportlab Paragraphs."""
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def get_vintage_styles():
    s = {}
    s["banner_sub"] = ParagraphStyle(
        "BannerSub", fontName="Times-Italic", fontSize=13,
        textColor=MID_SEPIA, alignment=1, spaceAfter=10,
    )
    s["cover_poet"] = ParagraphStyle(
        "CoverPoet", fontName="Times-Bold", fontSize=16,
        textColor=DARK_SEPIA, alignment=1, spaceAfter=4,
    )
    s["cover_stats"] = ParagraphStyle(
        "CoverStats", fontName="Times-Roman", fontSize=11,
        textColor=GOLDEN_ACCENT, alignment=1, spaceBefore=8,
    )
    s["cover_footer"] = ParagraphStyle(
        "CoverFooter", fontName="Times-Italic", fontSize=9,
        textColor=LIGHT_ACCENT, alignment=1, leading=13,
    )
    s["ornament"] = ParagraphStyle(
        "Ornament", fontName="Times-Roman", fontSize=11,
        textColor=GOLDEN_ACCENT, alignment=1, spaceBefore=4, spaceAfter=4,
    )
    s["epigraph"] = ParagraphStyle(
        "Epigraph", fontName="Times-Italic", fontSize=13,
        textColor=MID_SEPIA, alignment=1, leading=19,
    )
    s["section_title"] = ParagraphStyle(
        "SectionTitle", fontName="Times-Bold", fontSize=15,
        textColor=DARK_SEPIA, alignment=1, spaceBefore=18, spaceAfter=12,
    )
    s["decima_header"] = ParagraphStyle(
        "DecimaHeader", fontName="Times-Bold", fontSize=12,
        textColor=MID_SEPIA, alignment=0, spaceBefore=14, spaceAfter=2,
    )
    s["verse"] = ParagraphStyle(
        "Verse", fontName="Times-Roman", fontSize=11,
        textColor=DARK_SEPIA, alignment=0, leading=15.5,
        leftIndent=0.6*inch,
    )
    s["separator"] = ParagraphStyle(
        "Separator", fontName="Times-Roman", fontSize=8,
        textColor=GOLDEN_ACCENT, alignment=1, spaceBefore=4, spaceAfter=4,
    )
    s["body"] = ParagraphStyle(
        "Body", fontName="Times-Roman", fontSize=11,
        textColor=DARK_SEPIA, leading=14, spaceAfter=5,
    )
    s["analysis"] = ParagraphStyle(
        "Analysis", fontName="Times-Italic", fontSize=10,
        textColor=MID_SEPIA, leftIndent=0.3*inch, rightIndent=0.3*inch,
        spaceBefore=4, leading=13,
    )
    s["colophon"] = ParagraphStyle(
        "Colophon", fontName="Times-Italic", fontSize=10,
        textColor=GOLDEN_ACCENT, alignment=1, leading=14,
    )
    return s


# ═══════════════════════════════════════════
#  CANVAS DRAWING FUNCTIONS
# ═══════════════════════════════════════════

def draw_aged_paper(c):
    """Draw multi-layered aged parchment background."""
    c.setFillColor(PARCHMENT_BASE)
    c.rect(0, 0, W, H, fill=True, stroke=False)

    edge_w = 1.2 * inch
    c.setFillColor(Color(0.83, 0.72, 0.59, alpha=0.35))
    c.rect(0, 0, edge_w, H, fill=True, stroke=False)
    c.rect(W - edge_w, 0, edge_w, H, fill=True, stroke=False)
    c.rect(0, H - edge_w * 0.7, W, edge_w * 0.7, fill=True, stroke=False)
    c.rect(0, 0, W, edge_w * 0.7, fill=True, stroke=False)

    corner_r = 2.0 * inch
    c.setFillColor(Color(0.75, 0.63, 0.48, alpha=0.2))
    for cx, cy in [(0, 0), (W, 0), (0, H), (W, H)]:
        c.circle(cx, cy, corner_r, fill=True, stroke=False)

    random.seed(42)
    c.setFillColor(Color(0.78, 0.66, 0.47, alpha=0.12))
    for _ in range(8):
        sx = random.uniform(1*inch, W - 1*inch)
        sy = random.uniform(1*inch, H - 1*inch)
        sr = random.uniform(0.3*inch, 0.8*inch)
        c.circle(sx, sy, sr, fill=True, stroke=False)

def draw_ornate_border(c, margin=0.55*inch):
    """Draw ornate double-line border with corner flourishes."""
    x0, y0 = margin, margin
    x1, y1 = W - margin, H - margin

    c.setStrokeColor(BORDER_COLOR)
    c.setLineWidth(2.5)
    c.rect(x0, y0, x1 - x0, y1 - y0, fill=False, stroke=True)

    inset = 6
    c.setLineWidth(0.8)
    c.rect(x0 + inset, y0 + inset, x1 - x0 - 2*inset, y1 - y0 - 2*inset, fill=False, stroke=True)

    flourish_len = 0.4 * inch
    c.setLineWidth(1.8)
    c.setStrokeColor(BORDER_COLOR)

    corners = [
        (x0, y0, 1, 1),     (x1, y0, -1, 1),
        (x0, y1, 1, -1),    (x1, y1, -1, -1),
    ]
    for cx, cy, dx, dy in corners:
        ox, oy = cx - dx * 4, cy - dy * 4
        p = c.beginPath()
        p.moveTo(ox, oy + dy * flourish_len)
        p.lineTo(ox, oy)
        p.lineTo(ox + dx * flourish_len, oy)
        c.drawPath(p, stroke=True, fill=False)

        c.setFillColor(BORDER_COLOR)
        diamond_size = 3
        dp = c.beginPath()
        dp.moveTo(ox, oy + diamond_size)
        dp.lineTo(ox + diamond_size, oy)
        dp.lineTo(ox, oy - diamond_size)
        dp.lineTo(ox - diamond_size, oy)
        dp.close()
        c.drawPath(dp, stroke=False, fill=True)

def draw_guitar_icon(c, x, y, scale=1.0):
    c.saveState()
    c.translate(x, y)
    c.scale(scale, scale)
    c.setFillColor(BORDER_COLOR)
    c.circle(0, 0, 8, fill=True, stroke=False)
    c.circle(0, 12, 6, fill=True, stroke=False)
    c.setFillColor(PARCHMENT_BASE)
    c.circle(-7, 6, 4, fill=True, stroke=False)
    c.circle(7, 6, 4, fill=True, stroke=False)
    c.setFillColor(BORDER_COLOR)
    c.rect(-1.5, 18, 3, 16, fill=True, stroke=False)
    c.rect(-3, 34, 6, 4, fill=True, stroke=False)
    c.setFillColor(PARCHMENT_EDGE)
    c.circle(0, 0, 3, fill=True, stroke=False)
    c.restoreState()

def draw_palm_tree(c, x, y, scale=1.0):
    c.saveState()
    c.translate(x, y)
    c.scale(scale, scale)
    c.setFillColor(Color(0.36, 0.23, 0.12, alpha=0.25))
    p = c.beginPath()
    p.moveTo(-2, 0)
    p.lineTo(-1, 40)
    p.lineTo(1, 40)
    p.lineTo(2, 0)
    p.close()
    c.drawPath(p, stroke=False, fill=True)
    fronds = [
        (-20, 50, 0, 42),   (20, 50, 0, 42),
        (-15, 55, 0, 44),   (15, 55, 0, 44),
        (-5, 58, 0, 43),    (5, 58, 0, 43),
    ]
    for fx, fy, bx, by in fronds:
        fp = c.beginPath()
        fp.moveTo(bx, by)
        fp.curveTo(fx*0.3, (by+fy)/2, fx*0.7, fy-3, fx, fy)
        fp.lineTo(bx, by + 2)
        fp.close()
        c.drawPath(fp, stroke=False, fill=True)
    c.restoreState()


# ═══════════════════════════════════════════
#  PAGE TEMPLATES
# ═══════════════════════════════════════════

def draw_cover_page(canvas, doc):
    canvas.saveState()
    draw_aged_paper(canvas)
    draw_ornate_border(canvas)
    draw_palm_tree(canvas, 1.1*inch, 1.0*inch, scale=0.9)
    draw_palm_tree(canvas, W - 1.1*inch, 1.0*inch, scale=0.9)
    draw_guitar_icon(canvas, 1.2*inch, H/2 + 0.5*inch, scale=0.7)
    draw_guitar_icon(canvas, W - 1.2*inch, H/2 + 0.5*inch, scale=0.7)
    canvas.restoreState()

def draw_interior_page(canvas, doc):
    canvas.saveState()
    draw_aged_paper(canvas)
    draw_ornate_border(canvas)
    draw_guitar_icon(canvas, W/2 - 0.6*inch, 0.75*inch, scale=0.45)
    draw_guitar_icon(canvas, W/2 + 0.6*inch, 0.75*inch, scale=0.45)
    canvas.setFont("Times-Roman", 9)
    canvas.setFillColor(MID_SEPIA)
    canvas.drawCentredString(W/2, 0.45*inch, f"— {doc.page} —")
    canvas.restoreState()


# ═══════════════════════════════════════════
#  FLOWABLES
# ═══════════════════════════════════════════

class BannerFlowable(Flowable):
    def __init__(self, title, subtitle=None, height=60):
        Flowable.__init__(self)
        self.title = title
        self.subtitle = subtitle
        self.height = height
        self.width = W - 2.0*inch

    def draw(self):
        c = self.canv
        bw = self.width
        bh = 38
        bx = 0
        by = self.height - bh - 5

        # Banner background
        c.setFillColor(BANNER_BG)
        c.roundRect(bx, by, bw, bh, 3, fill=True, stroke=False)

        # Gold border on banner
        c.setStrokeColor(GOLDEN_ACCENT)
        c.setLineWidth(0.5)
        c.roundRect(bx + 2, by + 2, bw - 4, bh - 4, 2, fill=False, stroke=True)

        # Title
        c.setFillColor(BANNER_TEXT)
        c.setFont("Times-Bold", 18)
        c.drawCentredString(bw / 2, by + 12, self.title)

        # Subtitle below
        if self.subtitle:
            c.setFillColor(MID_SEPIA)
            c.setFont("Times-Italic", 12)
            c.drawCentredString(bw / 2, by - 16, self.subtitle)


class DecorativeRuleFlowable(Flowable):
    def __init__(self, width_ratio=0.6, height=12):
        Flowable.__init__(self)
        self.width = W - 2.0*inch
        self.height = height
        self.rule_width = self.width * width_ratio

    def draw(self):
        c = self.canv
        cx = self.width / 2
        rw = self.rule_width
        x0 = cx - rw/2
        x1 = cx + rw/2
        y = self.height / 2

        c.setStrokeColor(GOLDEN_ACCENT)
        c.setLineWidth(0.8)
        c.line(x0, y, x1, y)

        c.setFillColor(GOLDEN_ACCENT)
        s = 3
        dp = c.beginPath()
        dp.moveTo(cx, y + s)
        dp.lineTo(cx + s, y)
        dp.lineTo(cx, y - s)
        dp.lineTo(cx - s, y)
        dp.close()
        c.drawPath(dp, stroke=False, fill=True)

        c.circle(x0, y, 1.5, fill=True, stroke=False)
        c.circle(x1, y, 1.5, fill=True, stroke=False)


class SectionHeaderFlowable(Flowable):
    def __init__(self, text, height=30):
        Flowable.__init__(self)
        self.text = text
        self.width = W - 2.0*inch
        self.height = height

    def draw(self):
        c = self.canv
        cx = self.width / 2
        c.setFillColor(DARK_SEPIA)
        c.setFont("Times-Bold", 14)
        c.drawCentredString(cx, 14, self.text)

        rw = 3 * inch
        x0 = cx - rw/2
        x1 = cx + rw/2
        y = 8
        c.setStrokeColor(GOLDEN_ACCENT)
        c.setLineWidth(0.8)
        c.line(x0, y, x1, y)

        c.setFillColor(GOLDEN_ACCENT)
        s = 2.5
        dp = c.beginPath()
        dp.moveTo(cx, y + s)
        dp.lineTo(cx + s, y)
        dp.lineTo(cx, y - s)
        dp.lineTo(cx - s, y)
        dp.close()
        c.drawPath(dp, stroke=False, fill=True)


# ═══════════════════════════════════════════
#  MAIN PDF GENERATION
# ═══════════════════════════════════════════

def generate_pdf(job_id: str, data: ProcessResult, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, "viajera_archivo.pdf")
    styles = get_vintage_styles()

    content_frame = Frame(
        1.0*inch, 0.9*inch,
        W - 2.0*inch, H - 1.8*inch,
        id="content_frame"
    )

    doc = BaseDocTemplate(pdf_path, pagesize=letter)
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[content_frame], onPage=draw_cover_page),
        PageTemplate(id="interior", frames=[content_frame], onPage=draw_interior_page),
    ])

    elements = []
    
    # --- COVER ---
    elements.append(Spacer(1, 0.6*inch))
    elements.append(Paragraph(f'<font color="#F0DDB8" size="1">.</font>', styles["ornament"]))
    
    elements.append(BannerFlowable(
        "Viajera Canturía Final",
        "Poesía Guajira y Décimas Cubanas"
    ))
    elements.append(Spacer(1, 0.6*inch))
    elements.append(DecorativeRuleFlowable(width_ratio=0.5))
    elements.append(Spacer(1, 0.15*inch))
    
    event_title = f"Controversia entre {_esc(data.poets[0].name)} y {_esc(data.poets[1].name)}"
    elements.append(Paragraph(event_title, styles["section_title"]))
    elements.append(DecorativeRuleFlowable(width_ratio=0.4))
    elements.append(Spacer(1, 0.3*inch))
    
    elements.append(Paragraph(_esc(data.poets[0].name), styles["cover_poet"]))
    elements.append(Paragraph("vs.", styles["cover_stats"]))
    elements.append(Paragraph(_esc(data.poets[1].name), styles["cover_poet"]))
    
    elements.append(Spacer(1, 0.2*inch))
    elements.append(DecorativeRuleFlowable(width_ratio=0.3))
    
    elements.append(Paragraph(
        f"{data.total_decimas} décimas · {data.duration_minutes} minutos",
        styles["cover_stats"],
    ))
    
    elements.append(Spacer(1, 0.8*inch))
    elements.append(Paragraph("Transcripción y análisis automatizado", styles["cover_footer"]))
    elements.append(Paragraph("Viajera Digital · viajera-digital-alpha.vercel.app", styles["cover_footer"]))
    elements.append(Paragraph("En honor a Calixto González, El Guajiro de Hialeah", styles["cover_footer"]))

    elements.append(PageBreak())
    elements.append(NextPageTemplate("interior"))

    # --- EPIGRAPH ---
    elements.append(Spacer(1, 2.2*inch))
    elements.append(Paragraph(
        "“La décima es el alma del pueblo cubano,<br/>"
        "diez versos que caben en la palma de la mano.”",
        styles["epigraph"],
    ))
    elements.append(Spacer(1, 0.15*inch))
    elements.append(DecorativeRuleFlowable(width_ratio=0.35))
    elements.append(PageBreak())

    # --- DÉCIMAS ---
    elements.append(SectionHeaderFlowable("DÉCIMAS DE LA TRADICIÓN"))
    elements.append(Spacer(1, 0.15*inch))

    for d in data.decimas:
        elements.append(Paragraph(f"{d.number}. {_esc(d.poet_name)}", styles["decima_header"]))
        elements.append(Spacer(1, 4))
        for line in d.lines:
            elements.append(Paragraph(_esc(line), styles["verse"]))
        elements.append(Spacer(1, 2))
        elements.append(DecorativeRuleFlowable(width_ratio=0.45, height=10))
        elements.append(Spacer(1, 4))

    elements.append(PageBreak())

    # --- RESUMEN FINAL ---
    elements.append(SectionHeaderFlowable("RESUMEN FINAL"))
    elements.append(Spacer(1, 0.15*inch))

    elements.append(Paragraph(f"<b>Total de décimas:</b> {data.total_decimas}", styles["body"]))
    elements.append(Paragraph(f"<b>Duración:</b> {data.duration_minutes} min", styles["body"]))
    elements.append(Paragraph(f"<b>Narrativa:</b> {_esc(data.event_summary)}", styles["body"]))
    if data.technical_winner:
        elements.append(Paragraph(f"<b>Ganador Técnico:</b> {_esc(data.technical_winner)}", styles["body"]))

    elements.append(Spacer(1, 0.2*inch))
    elements.append(SectionHeaderFlowable("DESTACADAS"))
    elements.append(Spacer(1, 0.1*inch))

    for t in getattr(data, 'top_4', getattr(data, 'top_decimas', [])):
        elements.append(Paragraph(
            f"DESTACADA — {_esc(t.poet_name)} (Décima #{t.decima_number})",
            styles["decima_header"],
        ))
        for line in t.lines:
            elements.append(Paragraph(_esc(line), styles["verse"]))
        out_analysis = getattr(t, 'analysis', "Análisis literario y emocional...")
        elements.append(Paragraph(f"ANÁLISIS: {_esc(out_analysis)}", styles["analysis"]))
        elements.append(Spacer(1, 2))
        elements.append(DecorativeRuleFlowable(width_ratio=0.5, height=10))
        elements.append(Spacer(1, 4))

    # --- COLOPHON ---
    elements.append(PageBreak())
    elements.append(Spacer(1, 3*inch))
    elements.append(DecorativeRuleFlowable(width_ratio=0.35))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph("Generado por Viajera Digital", styles["colophon"]))
    elements.append(Paragraph("Preservando el repentismo cubano", styles["colophon"]))
    elements.append(Paragraph("© Emilio José Novo", styles["colophon"]))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(DecorativeRuleFlowable(width_ratio=0.35))

    doc.build(elements)
    return pdf_path


# --- TXT Generation ---
def generate_txt(job_id: str, data: ProcessResult, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    txt_path = os.path.join(output_dir, "viajera_archivo.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("VIAJERA DIGITAL - ARCHIVO DE REPENTISMO\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Resumen: {data.event_summary}\n\n")
        for d in data.decimas:
            f.write(f"{d.number}. {d.poet_name}\n")
            for line in d.lines:
                f.write(f"    {line}\n")
            f.write("-" * 20 + "\n")
        f.write("\nTOP 4 DESTACADAS\n")
        f.write("=" * 40 + "\n")
        for t in getattr(data, 'top_4', getattr(data, 'top_decimas', [])):
            f.write(f"Décima #{t.decima_number} - {t.poet_name}\n")
            for line in t.lines:
                f.write(f"    {line}\n")
            out_analysis = getattr(t, 'analysis', "")
            if out_analysis:
                f.write(f"Análisis: {out_analysis}\n")
            f.write("-" * 20 + "\n")
    return txt_path


# --- JSON Generation ---
def generate_json(job_id: str, data: ProcessResult, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "viajera_archivo.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data.model_dump(), f, indent=2, ensure_ascii=False)
    return json_path


# --- Public API (called by pipeline.py) ---
def generate_all_exports(job_id: str, result: ProcessResult, export_dir: str):
    """Generate PDF, TXT, JSON exports. Returns dict of paths."""
    os.makedirs(export_dir, exist_ok=True)
    pdf_path = generate_pdf(job_id, result, export_dir)
    txt_path = generate_txt(job_id, result, export_dir)
    json_path = generate_json(job_id, result, export_dir)
    return {
        "pdf": pdf_path,
        "txt": txt_path,
        "json": json_path,
    }
