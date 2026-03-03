"""
Viajera Digital — Export Generation (PDF, TXT, JSON)
Vintage Cuban Literary Pamphlet Style

PDF STYLE: 1950s Cuban literary pamphlet.
  Colors: Cream background, dark brown text, golden-brown accents.
  Fonts: Times-Roman, Times-Bold, Times-Italic (built into reportlab).
  Everything in Spanish.
"""

import os
import json
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import Color
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
)

# ── Colors ───────────────────────────────────────────────
CREAM = Color(245 / 255, 235 / 255, 220 / 255)
DARK_BROWN = Color(60 / 255, 40 / 255, 20 / 255)
GOLDEN_BROWN = Color(180 / 255, 130 / 255, 60 / 255)

W, H = letter  # 612 x 792 points

# ── Unicode decorations ─────────────────────────────────
ORNAMENT = "\u2500\u2500\u2500 \u2726 \u2500\u2500\u2500"
THICK_ORNAMENT = "\u2550\u2550\u2550\u2550\u2550\u2550\u2550 \u2726 \u2550\u2550\u2550\u2550\u2550\u2550\u2550"
THIN_LINE = "\u2500" * 35


# ═══════════════════════════════════════════════════════════
# REPORTLAB STYLES
# ═══════════════════════════════════════════════════════════

def _make_styles():
    return {
        "cover_brand": ParagraphStyle(
            "CoverBrand", fontName="Times-Bold", fontSize=14,
            textColor=GOLDEN_BROWN, alignment=1, spaceAfter=4, leading=18,
        ),
        "cover_title": ParagraphStyle(
            "CoverTitle", fontName="Times-Bold", fontSize=28,
            textColor=DARK_BROWN, alignment=1, spaceAfter=6, leading=34,
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle", fontName="Times-Italic", fontSize=16,
            textColor=DARK_BROWN, alignment=1, spaceAfter=6, leading=20,
        ),
        "cover_poets": ParagraphStyle(
            "CoverPoets", fontName="Times-Roman", fontSize=18,
            textColor=DARK_BROWN, alignment=1, spaceAfter=4, leading=22,
        ),
        "cover_stats": ParagraphStyle(
            "CoverStats", fontName="Times-Roman", fontSize=11,
            textColor=GOLDEN_BROWN, alignment=1, spaceAfter=4, leading=14,
        ),
        "cover_footer": ParagraphStyle(
            "CoverFooter", fontName="Times-Italic", fontSize=9,
            textColor=GOLDEN_BROWN, alignment=1, spaceAfter=3, leading=12,
        ),
        "ornament": ParagraphStyle(
            "Ornament", fontName="Times-Roman", fontSize=12,
            textColor=GOLDEN_BROWN, alignment=1, spaceBefore=10, spaceAfter=10,
        ),
        "epigraph": ParagraphStyle(
            "Epigraph", fontName="Times-Italic", fontSize=13,
            textColor=DARK_BROWN, alignment=1, leading=18, spaceAfter=12,
        ),
        "decima_header": ParagraphStyle(
            "DecimaHeader", fontName="Times-Bold", fontSize=12,
            textColor=DARK_BROWN, alignment=0, spaceBefore=8, spaceAfter=4,
        ),
        "verse": ParagraphStyle(
            "Verse", fontName="Times-Roman", fontSize=11,
            textColor=DARK_BROWN, alignment=0, leading=15,
            leftIndent=0.5 * inch, spaceAfter=1,
        ),
        "separator": ParagraphStyle(
            "Separator", fontName="Times-Roman", fontSize=9,
            textColor=GOLDEN_BROWN, alignment=1, spaceBefore=8, spaceAfter=8,
        ),
        "thick_separator": ParagraphStyle(
            "ThickSep", fontName="Times-Roman", fontSize=10,
            textColor=GOLDEN_BROWN, alignment=1, spaceBefore=12, spaceAfter=12,
        ),
        "section_title": ParagraphStyle(
            "SectionTitle", fontName="Times-Bold", fontSize=16,
            textColor=DARK_BROWN, alignment=1, spaceBefore=16, spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "Body", fontName="Times-Roman", fontSize=11,
            textColor=DARK_BROWN, alignment=0, leading=15, spaceAfter=6,
        ),
        "highlight_header": ParagraphStyle(
            "HighlightHeader", fontName="Times-Bold", fontSize=12,
            textColor=GOLDEN_BROWN, alignment=0, spaceBefore=10, spaceAfter=4,
        ),
        "analysis": ParagraphStyle(
            "Analysis", fontName="Times-Italic", fontSize=10,
            textColor=DARK_BROWN, alignment=0, leading=13,
            leftIndent=0.3 * inch, spaceBefore=4, spaceAfter=8,
        ),
        "colophon": ParagraphStyle(
            "Colophon", fontName="Times-Italic", fontSize=10,
            textColor=GOLDEN_BROWN, alignment=1, leading=14, spaceAfter=4,
        ),
    }


# ═══════════════════════════════════════════════════════════
# PAGE CALLBACKS
# ═══════════════════════════════════════════════════════════

def _draw_cream_bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(CREAM)
    canvas.rect(0, 0, W, H, fill=True, stroke=False)
    canvas.restoreState()


def _draw_cover(canvas, doc):
    _draw_cream_bg(canvas, doc)


def _draw_epigraph(canvas, doc):
    _draw_cream_bg(canvas, doc)


class _InteriorCallback:
    def __init__(self, poet_a, poet_b):
        self.header_text = f"Viajera Digital \u2014 {poet_a} vs. {poet_b}"

    def __call__(self, canvas, doc):
        _draw_cream_bg(canvas, doc)
        canvas.saveState()
        canvas.setFont("Times-Italic", 8)
        canvas.setFillColor(GOLDEN_BROWN)
        canvas.drawRightString(W - 72, H - 40, self.header_text)
        canvas.setFont("Times-Roman", 9)
        canvas.setFillColor(GOLDEN_BROWN)
        canvas.drawCentredString(W / 2, 35, f"\u2014 {doc.page} \u2014")
        canvas.restoreState()


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def _esc(text):
    """Escape XML special characters for reportlab Paragraphs."""
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _get_poet_names(data):
    poets = data.get("poets", [])
    poet_a = poets[0]["name"] if len(poets) > 0 else "Poeta A"
    poet_b = poets[1]["name"] if len(poets) > 1 else "Poeta B"
    return poet_a, poet_b


# ═══════════════════════════════════════════════════════════
# PDF GENERATION
# ═══════════════════════════════════════════════════════════

def generate_pdf(data, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, "viajera_archivo.pdf")
    styles = _make_styles()

    poet_a, poet_b = _get_poet_names(data)
    interior_cb = _InteriorCallback(poet_a, poet_b)

    cover_frame = Frame(1.5 * inch, 1 * inch, W - 3 * inch, H - 2 * inch, id="cover")
    epigraph_frame = Frame(1.5 * inch, 2.5 * inch, W - 3 * inch, H - 5 * inch, id="epigraph")
    interior_frame = Frame(1.2 * inch, 1 * inch, W - 2.4 * inch, H - 2 * inch, id="interior")

    templates = [
        PageTemplate(id="cover", frames=[cover_frame], onPage=_draw_cover),
        PageTemplate(id="epigraph", frames=[epigraph_frame], onPage=_draw_epigraph),
        PageTemplate(id="interior", frames=[interior_frame], onPage=interior_cb),
    ]

    doc = BaseDocTemplate(pdf_path, pagesize=letter, pageTemplates=templates)
    elements = []

    # ── COVER PAGE ───────────────────────────────────────
    elements.append(Spacer(1, 1.2 * inch))
    elements.append(Paragraph(ORNAMENT, styles["ornament"]))
    elements.append(Paragraph("VIAJERA DIGITAL", styles["cover_brand"]))
    elements.append(Paragraph(ORNAMENT, styles["ornament"]))
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph("CANTUR\u00cdA", styles["cover_title"]))

    subtitle = f"Controversia entre {poet_a} y {poet_b}"
    elements.append(Paragraph(_esc(subtitle), styles["cover_subtitle"]))

    elements.append(Paragraph(ORNAMENT, styles["ornament"]))
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph(_esc(poet_a), styles["cover_poets"]))
    elements.append(Paragraph("vs.", styles["cover_stats"]))
    elements.append(Paragraph(_esc(poet_b), styles["cover_poets"]))
    elements.append(Paragraph(ORNAMENT, styles["ornament"]))

    dur = data.get("duration_minutes", "\u2014")
    total = data.get("total_decimas", 0)
    elements.append(Paragraph(
        f"{total} d\u00e9cimas \u00b7 {dur} minutos",
        styles["cover_stats"],
    ))

    elements.append(Spacer(1, 0.8 * inch))
    elements.append(Paragraph("Transcripci\u00f3n y an\u00e1lisis automatizado", styles["cover_footer"]))
    elements.append(Paragraph("Viajera Digital \u00b7 viajera-digital-alpha.vercel.app", styles["cover_footer"]))
    elements.append(Paragraph("En honor a Calixto Gonz\u00e1lez, El Guajiro de Hialeah", styles["cover_footer"]))

    # ── EPIGRAPH PAGE ────────────────────────────────────
    elements.append(NextPageTemplate("epigraph"))
    elements.append(PageBreak())
    elements.append(Spacer(1, 1 * inch))
    elements.append(Paragraph(
        "\u201cLa d\u00e9cima es el alma del pueblo cubano,<br/>"
        "diez versos que caben en la palma de la mano.\u201d",
        styles["epigraph"],
    ))
    elements.append(Paragraph(ORNAMENT, styles["ornament"]))

    # ── DECIMA PAGES ─────────────────────────────────────
    elements.append(NextPageTemplate("interior"))
    elements.append(PageBreak())

    decimas = data.get("decimas", [])
    prev_poet = None

    for decima in decimas:
        poet_id = decima.get("poet_id", "")
        poet_name = decima.get("poet_name", "")
        number = decima.get("number", 0)
        lines = decima.get("lines", [])

        if prev_poet is not None and poet_id != prev_poet:
            elements.append(Paragraph(THICK_ORNAMENT, styles["thick_separator"]))
        elif prev_poet is not None:
            elements.append(Paragraph(THIN_LINE, styles["separator"]))

        gb_hex = GOLDEN_BROWN.hexval()[2:]
        num_str = f'<font color="#{gb_hex}">{number}.</font>'
        elements.append(Paragraph(f"{num_str} {_esc(poet_name)}", styles["decima_header"]))
        elements.append(Spacer(1, 4))

        for line in lines:
            elements.append(Paragraph(_esc(line), styles["verse"]))

        elements.append(Spacer(1, 12))
        prev_poet = poet_id

    # ── RESUMEN FINAL + TOP 4 ────────────────────────────
    elements.append(PageBreak())
    elements.append(Paragraph(ORNAMENT, styles["ornament"]))
    elements.append(Paragraph("RESUMEN FINAL", styles["section_title"]))
    elements.append(Paragraph(ORNAMENT, styles["ornament"]))
    elements.append(Spacer(1, 8))

    poets = data.get("poets", [])
    poet_a_count = poets[0].get("decima_count", 0) if len(poets) > 0 else 0
    poet_b_count = poets[1].get("decima_count", 0) if len(poets) > 1 else 0

    stats = [
        f"<b>Total de d\u00e9cimas:</b> {total}",
        f"<b>Duraci\u00f3n del evento:</b> {dur} minutos",
        f"<b>Poetas:</b> {_esc(poet_a)} ({poet_a_count}) vs. {_esc(poet_b)} ({poet_b_count})",
    ]
    summary = data.get("event_summary", "")
    winner = data.get("technical_winner", "")
    if summary:
        stats.append(f"<b>Tema principal:</b> {_esc(summary)}")
    if winner:
        stats.append(f"<b>Ganador t\u00e9cnico:</b> {_esc(winner)}")

    for s in stats:
        elements.append(Paragraph(s, styles["body"]))

    elements.append(Spacer(1, 16))
    elements.append(Paragraph(ORNAMENT, styles["ornament"]))
    elements.append(Paragraph("TOP 4 D\u00c9CIMAS DESTACADAS", styles["section_title"]))
    elements.append(Paragraph(ORNAMENT, styles["ornament"]))

    top_4 = data.get("top_4", [])
    for entry in top_4:
        rank = entry.get("rank", 0)
        e_poet = entry.get("poet_name", "")
        e_num = entry.get("decima_number", 0)
        e_lines = entry.get("lines", [])
        e_analysis = entry.get("analysis", "")

        elements.append(Paragraph(THIN_LINE, styles["separator"]))
        elements.append(Paragraph(f"DESTACADA #{rank}", styles["highlight_header"]))
        elements.append(Paragraph(
            f"Poeta: {_esc(e_poet)} \u00b7 D\u00e9cima Original: #{e_num}",
            styles["highlight_header"],
        ))
        elements.append(Paragraph(THIN_LINE, styles["separator"]))

        for line in e_lines:
            elements.append(Paragraph(_esc(line), styles["verse"]))

        elements.append(Spacer(1, 6))
        elements.append(Paragraph(
            f"<b>AN\u00c1LISIS:</b><br/>{_esc(e_analysis)}",
            styles["analysis"],
        ))

    # ── COLOPHON ─────────────────────────────────────────
    elements.append(PageBreak())
    elements.append(Spacer(1, 2.5 * inch))
    elements.append(Paragraph(ORNAMENT, styles["colophon"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Este archivo fue generado por Viajera Digital", styles["colophon"]))
    elements.append(Paragraph("Preservando el repentismo cubano, una d\u00e9cima a la vez.", styles["colophon"]))
    elements.append(Paragraph("viajera-digital-alpha.vercel.app", styles["colophon"]))
    elements.append(Paragraph("\u00a9 Emilio Jos\u00e9 Novo", styles["colophon"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(ORNAMENT, styles["colophon"]))

    doc.build(elements)
    return pdf_path


# ═══════════════════════════════════════════════════════════
# TXT GENERATION
# ═══════════════════════════════════════════════════════════

def generate_txt(data, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    txt_path = os.path.join(output_dir, "viajera_archivo.txt")

    poet_a, poet_b = _get_poet_names(data)
    total = data.get("total_decimas", 0)
    dur = data.get("duration_minutes", "\u2014")

    lines = []
    lines.append("VIAJERA DIGITAL")
    lines.append("Archivo de Repentismo Cubano")
    lines.append("=" * 50)
    lines.append("")
    lines.append(f"Poetas: {poet_a} vs. {poet_b}")
    lines.append(f"Total de decimas: {total}")
    lines.append(f"Duracion: {dur} minutos")
    lines.append("")

    summary = data.get("event_summary", "")
    if summary:
        lines.append(summary)
        lines.append("")

    lines.append("=" * 50)
    lines.append("")

    prev_poet = None
    for decima in data.get("decimas", []):
        pid = decima.get("poet_id", "")
        if prev_poet is not None and pid != prev_poet:
            lines.append("\u2550\u2550\u2550\u2550\u2550\u2550\u2550 \u2726 \u2550\u2550\u2550\u2550\u2550\u2550\u2550")
            lines.append("")
        elif prev_poet is not None:
            lines.append("\u2500" * 35)
            lines.append("")

        lines.append(f"{decima.get('number', 0)}. {decima.get('poet_name', '')}")
        lines.append("")
        for verse in decima.get("lines", []):
            lines.append(f"    {verse}")
        lines.append("")
        prev_poet = pid

    lines.append("=" * 50)
    lines.append("RESUMEN FINAL")
    lines.append("=" * 50)
    lines.append("")
    lines.append(f"Total de decimas: {total}")
    lines.append(f"Duracion: {dur} minutos")

    poets = data.get("poets", [])
    pa_c = poets[0].get("decima_count", 0) if len(poets) > 0 else 0
    pb_c = poets[1].get("decima_count", 0) if len(poets) > 1 else 0
    lines.append(f"Poetas: {poet_a} ({pa_c}) vs. {poet_b} ({pb_c})")

    if summary:
        lines.append(f"Tema: {summary}")
    winner = data.get("technical_winner", "")
    if winner:
        lines.append(f"Ganador tecnico: {winner}")
    lines.append("")

    lines.append("TOP 4 DECIMAS DESTACADAS")
    lines.append("\u2500" * 35)
    lines.append("")

    for entry in data.get("top_4", []):
        lines.append(f"Destacada #{entry.get('rank', 0)} \u2014 {entry.get('poet_name', '')} (Decima #{entry.get('decima_number', 0)})")
        lines.append("")
        for verse in entry.get("lines", []):
            lines.append(f"    {verse}")
        lines.append("")
        lines.append(f"Analisis: {entry.get('analysis', '')}")
        lines.append("")
        lines.append("\u2500" * 35)
        lines.append("")

    lines.append("\u2500\u2500\u2500 \u2726 \u2500\u2500\u2500")
    lines.append("Generado por Viajera Digital")
    lines.append("viajera-digital-alpha.vercel.app")
    lines.append("\u00a9 Emilio Jose Novo")

    content = "\n".join(lines)
    Path(txt_path).write_text(content, encoding="utf-8")
    return txt_path


# ═══════════════════════════════════════════════════════════
# JSON GENERATION
# ═══════════════════════════════════════════════════════════

def generate_json(data, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "viajera_archivo.json")
    Path(json_path).write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return json_path


# ═══════════════════════════════════════════════════════════
# PUBLIC API — called by pipeline.py
# ═══════════════════════════════════════════════════════════

def generate_all_exports(result, export_dir):
    """Generate PDF, TXT, JSON exports. Returns dict of paths."""
    os.makedirs(export_dir, exist_ok=True)
    pdf_path = generate_pdf(result, export_dir)
    txt_path = generate_txt(result, export_dir)
    json_path = generate_json(result, export_dir)
    return {
        "pdf": pdf_path,
        "txt": txt_path,
        "json": json_path,
    }
