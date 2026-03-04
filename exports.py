"""
Viajera Digital — Export Generation (PDF, TXT, JSON)
Vintage Cuban Literary Style
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

from models import ProcessResult

# --- Constants & Colors ---
CREAM = Color(245/255, 235/255, 220/255)
DARK_BROWN = Color(60/255, 40/255, 20/255)
GOLDEN_BROWN = Color(180/255, 130/255, 60/255)

ORNAMENT = "\u2500\u2500\u2500 \u2726 \u2500\u2500\u2500"
THICK_ORNAMENT = "\u2550\u2550\u2550\u2550 \u2726 \u2550\u2550\u2550\u2550"
THIN_LINE = "\u2500" * 35

W, H = letter


# --- Styles ---

def _esc(text):
    """Escape XML special characters for reportlab Paragraphs."""
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def get_vintage_styles():
    styles = {}
    styles["brand"] = ParagraphStyle(
        "Brand", fontName="Times-Bold", fontSize=14,
        textColor=GOLDEN_BROWN, alignment=1,
    )
    styles["cover_title"] = ParagraphStyle(
        "CoverTitle", fontName="Times-Bold", fontSize=28,
        textColor=DARK_BROWN, alignment=1, spaceBefore=20, spaceAfter=20,
    )
    styles["cover_subtitle"] = ParagraphStyle(
        "CoverSubtitle", fontName="Times-Italic", fontSize=16,
        textColor=DARK_BROWN, alignment=1, spaceAfter=20,
    )
    styles["cover_poets"] = ParagraphStyle(
        "CoverPoets", fontName="Times-Roman", fontSize=18,
        textColor=DARK_BROWN, alignment=1, spaceAfter=5,
    )
    styles["cover_stats"] = ParagraphStyle(
        "CoverStats", fontName="Times-Roman", fontSize=11,
        textColor=GOLDEN_BROWN, alignment=1, spaceBefore=10,
    )
    styles["cover_footer"] = ParagraphStyle(
        "CoverFooter", fontName="Times-Italic", fontSize=9,
        textColor=GOLDEN_BROWN, alignment=1, leading=12,
    )
    styles["ornament"] = ParagraphStyle(
        "Ornament", fontName="Times-Roman", fontSize=12,
        textColor=GOLDEN_BROWN, alignment=1, spaceBefore=4, spaceAfter=4,
    )
    styles["epigraph"] = ParagraphStyle(
        "Epigraph", fontName="Times-Italic", fontSize=13,
        textColor=DARK_BROWN, alignment=1, leading=18,
    )
    styles["decima_header"] = ParagraphStyle(
        "DecimaHeader", fontName="Times-Bold", fontSize=12,
        textColor=DARK_BROWN, alignment=0, spaceBefore=10,
    )
    styles["verse"] = ParagraphStyle(
        "Verse", fontName="Times-Roman", fontSize=11,
        textColor=DARK_BROWN, alignment=0, leading=15, leftIndent=0.5*inch,
    )
    styles["separator"] = ParagraphStyle(
        "Separator", fontName="Times-Roman", fontSize=8,
        textColor=GOLDEN_BROWN, alignment=1, spaceBefore=6, spaceAfter=6,
    )
    styles["section_title"] = ParagraphStyle(
        "SectionTitle", fontName="Times-Bold", fontSize=16,
        textColor=DARK_BROWN, alignment=1, spaceBefore=20, spaceAfter=10,
    )
    styles["body"] = ParagraphStyle(
        "Body", fontName="Times-Roman", fontSize=11,
        textColor=DARK_BROWN, spaceAfter=6,
    )
    styles["analysis"] = ParagraphStyle(
        "Analysis", fontName="Times-Italic", fontSize=10,
        textColor=DARK_BROWN, leftIndent=0.2*inch, spaceBefore=4,
    )
    styles["colophon"] = ParagraphStyle(
        "Colophon", fontName="Times-Italic", fontSize=10,
        textColor=GOLDEN_BROWN, alignment=1, leading=14,
    )
    return styles


# --- Background Drawing ---

def draw_vintage_bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(CREAM)
    canvas.rect(0, 0, W, H, fill=True, stroke=False)

    # Generic interior footer
    if doc.pageTemplate.id == "interior":
        canvas.setFont("Times-Roman", 9)
        canvas.setFillColor(GOLDEN_BROWN)
        canvas.drawCentredString(W/2, 35, f"\u2014 {doc.page} \u2014")
    canvas.restoreState()


# --- PDF Generation ---

def generate_pdf(job_id: str, data: ProcessResult, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, "viajera_archivo.pdf")
    styles = get_vintage_styles()

    interior_frame = Frame(1.2*inch, 1*inch, W-2.4*inch, H-2*inch, id="interior_frame")

    doc = BaseDocTemplate(pdf_path, pagesize=letter)
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[interior_frame], onPage=draw_vintage_bg),
        PageTemplate(id="interior", frames=[interior_frame], onPage=draw_vintage_bg),
    ])

    elements = []

    # --- COVER ---
    elements.append(Spacer(1, 1*inch))
    elements.append(Paragraph(ORNAMENT, styles["ornament"]))
    elements.append(Paragraph("VIAJERA DIGITAL", styles["brand"]))
    elements.append(Paragraph(ORNAMENT, styles["ornament"]))
    elements.append(Spacer(1, 0.4*inch))
    elements.append(Paragraph("CANTUR\u00cdA", styles["cover_title"]))

    event_title = f"Controversia entre {_esc(data.poets[0].name)} y {_esc(data.poets[1].name)}"
    elements.append(Paragraph(event_title, styles["cover_subtitle"]))

    elements.append(Paragraph(ORNAMENT, styles["ornament"]))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph(_esc(data.poets[0].name), styles["cover_poets"]))
    elements.append(Paragraph("vs.", styles["cover_stats"]))
    elements.append(Paragraph(_esc(data.poets[1].name), styles["cover_poets"]))
    elements.append(Paragraph(ORNAMENT, styles["ornament"]))

    elements.append(Paragraph(
        f"{data.total_decimas} d\u00e9cimas \u00b7 {data.duration_minutes} minutos",
        styles["cover_stats"],
    ))

    elements.append(Spacer(1, 1*inch))
    elements.append(Paragraph("Transcripci\u00f3n y an\u00e1lisis automatizado", styles["cover_footer"]))
    elements.append(Paragraph("Viajera Digital \u00b7 viajera-digital-alpha.vercel.app", styles["cover_footer"]))
    elements.append(Paragraph("En honor a Calixto Gonz\u00e1lez, El Guajiro de Hialeah", styles["cover_footer"]))

    elements.append(PageBreak())
    elements.append(NextPageTemplate("interior"))

    # --- EPIGRAPH ---
    elements.append(Spacer(1, 2*inch))
    elements.append(Paragraph(
        "\u201cLa d\u00e9cima es el alma del pueblo cubano,<br/>"
        "diez versos que caben en la palma de la mano.\u201d",
        styles["epigraph"],
    ))
    elements.append(Paragraph(ORNAMENT, styles["ornament"]))
    elements.append(PageBreak())

    # --- DÉCIMAS ---
    for d in data.decimas:
        elements.append(Paragraph(f"{d.number}. {_esc(d.poet_name)}", styles["decima_header"]))
        elements.append(Spacer(1, 4))
        for line in d.lines:
            elements.append(Paragraph(_esc(line), styles["verse"]))
        elements.append(Paragraph(THIN_LINE, styles["separator"]))
        elements.append(Spacer(1, 10))

    elements.append(PageBreak())

    # --- SUMMARY ---
    elements.append(Paragraph(THICK_ORNAMENT, styles["ornament"]))
    elements.append(Paragraph("RESUMEN FINAL", styles["section_title"]))
    elements.append(Paragraph(THICK_ORNAMENT, styles["ornament"]))

    elements.append(Paragraph(f"<b>Total de d\u00e9cimas:</b> {data.total_decimas}", styles["body"]))
    elements.append(Paragraph(f"<b>Duraci\u00f3n:</b> {data.duration_minutes} min", styles["body"]))
    elements.append(Paragraph(f"<b>Narrativa:</b> {_esc(data.event_summary)}", styles["body"]))
    if data.technical_winner:
        elements.append(Paragraph(f"<b>Ganador T\u00e9cnico:</b> {_esc(data.technical_winner)}", styles["body"]))

    elements.append(Spacer(1, 20))
    elements.append(Paragraph(THICK_ORNAMENT, styles["ornament"]))
    elements.append(Paragraph("TOP 4 DESTACADAS", styles["section_title"]))
    elements.append(Paragraph(THICK_ORNAMENT, styles["ornament"]))

    for t in data.top_4:
        elements.append(Paragraph(
            f"DESTACADA - {_esc(t.poet_name)} (D\u00e9cima #{t.decima_number})",
            styles["decima_header"],
        ))
        for line in t.lines:
            elements.append(Paragraph(_esc(line), styles["verse"]))
        elements.append(Paragraph(f"AN\u00c1LISIS: {_esc(t.analysis)}", styles["analysis"]))
        elements.append(Paragraph(THIN_LINE, styles["separator"]))

    # --- COLOPHON ---
    elements.append(PageBreak())
    elements.append(Spacer(1, 3*inch))
    elements.append(Paragraph(ORNAMENT, styles["ornament"]))
    elements.append(Paragraph("Generado por Viajera Digital", styles["colophon"]))
    elements.append(Paragraph("Preservando el repentismo cubano", styles["colophon"]))
    elements.append(Paragraph("\u00a9 Emilio Jos\u00e9 Novo", styles["colophon"]))
    elements.append(Paragraph(ORNAMENT, styles["ornament"]))

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
        for t in data.top_4:
            f.write(f"D\u00e9cima #{t.decima_number} - {t.poet_name}\n")
            for line in t.lines:
                f.write(f"    {line}\n")
            f.write(f"An\u00e1lisis: {t.analysis}\n")
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
