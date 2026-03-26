import html
import re
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from backend.database import get_connection
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.units import inch
from docx import Document

router = APIRouter()


# ── Shared helpers ────────────────────────────────────────

def render_rich_text_pdf(text: str) -> str:
    """Convert **bold** and __underline__ to ReportLab HTML tags."""
    # Escape HTML first
    text = html.escape(text)
    # Then apply bold and underline
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.*?)__',     r'<u>\1</u>', text)
    return text


def clean_text_basic(text: str) -> str:
    """Strip all markdown — used only for tables."""
    text = re.sub(r'#{1,6}\s*', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__',     r'\1', text)
    text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}(.*?)_{1,3}',   r'\1', text)
    text = re.sub(r'`{1,3}(.*?)`{1,3}',   r'\1', text)
    return text.strip()


def is_table_row(line: str) -> bool:
    line = line.strip()
    return line.startswith('|') and line.endswith('|')


def is_separator_row(line: str) -> bool:
    return bool(re.match(r'\|[-:\s|]+\|', line.strip()))


def parse_table_rows(lines: list) -> list:
    rows = []
    for line in lines:
        if is_separator_row(line):
            continue
        if is_table_row(line):
            cells = [clean_text_basic(c.strip()) for c in line.strip('|').split('|')]
            cells = [c for c in cells if c != '']
            if cells:
                rows.append(cells)
    return rows


# ══════════════════════════════════════════════════════════
# PDF DOWNLOAD
# ══════════════════════════════════════════════════════════

@router.get("/download/pdf/{document_id}")
def download_pdf(document_id: str):
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT dt.name FROM documents d
        JOIN document_templates dt ON d.template_id = dt.id
        WHERE d.id=%s
        """,
        (document_id,)
    )
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    title = result[0]

    cursor.execute(
        """
        SELECT DISTINCT ON (section_order)
            section_title, section_content, section_order
        FROM document_sections
        WHERE document_id=%s
        ORDER BY section_order, id DESC
        """,
        (document_id,)
    )
    sections = cursor.fetchall()
    if not sections:
        raise HTTPException(status_code=404, detail="No content found")

    cursor.close()
    conn.close()

    file_name = title.lower().replace(" ", "_") + ".pdf"
    file_path = f"/tmp/{file_name}"

    doc    = SimpleDocTemplate(
        file_path,
        rightMargin=60, leftMargin=60,
        topMargin=60,   bottomMargin=60
    )
    styles = getSampleStyleSheet()
    story  = []

    # ── Custom styles ─────────────────────────────────────
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=22,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1a1a3a'),
        alignment=TA_CENTER,
        spaceAfter=6
    )
    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=14,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#7F77DD'),
        spaceBefore=16,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica',
        textColor=colors.HexColor('#2a2a4a'),
        leading=18,
        spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica',
        textColor=colors.HexColor('#2a2a4a'),
        leading=18,
        spaceAfter=4,
        leftIndent=16,
        firstLineIndent=0
    )
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold',
        textColor=colors.white
    )
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica',
        textColor=colors.HexColor('#2a2a4a')
    )

    # ── Build PDF table ───────────────────────────────────
    def build_pdf_table(rows):
        if not rows:
            return None
        pdf_rows = []
        for i, row in enumerate(rows):
            pdf_row = []
            for cell in row:
                style = table_header_style if i == 0 else table_cell_style
                pdf_row.append(Paragraph(html.escape(str(cell)), style))
            pdf_rows.append(pdf_row)

        col_count = max(len(r) for r in pdf_rows)
        col_width  = doc.width / col_count

        t = Table(pdf_rows, colWidths=[col_width] * col_count)
        t.setStyle(TableStyle([
            ('BACKGROUND',     (0, 0), (-1, 0),  colors.HexColor('#7F77DD')),
            ('TEXTCOLOR',      (0, 0), (-1, 0),  colors.white),
            ('FONTNAME',       (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',       (0, 0), (-1, 0),  10),
            ('BACKGROUND',     (0, 1), (-1, -1), colors.HexColor('#f5f5ff')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.HexColor('#f5f5ff'), colors.white]),
            ('GRID',           (0, 0), (-1, -1), 0.5, colors.HexColor('#c0c0d8')),
            ('LINEBELOW',      (0, 0), (-1, 0),  1.5, colors.HexColor('#534AB7')),
            ('TOPPADDING',     (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING',  (0, 0), (-1, -1), 8),
            ('LEFTPADDING',    (0, 0), (-1, -1), 10),
            ('RIGHTPADDING',   (0, 0), (-1, -1), 10),
            ('VALIGN',         (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        return t

    # ── Document title ────────────────────────────────────
    story.append(Spacer(1, 20))
    story.append(Paragraph(html.escape(title), title_style))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(
        width="100%", thickness=2,
        color=colors.HexColor('#7F77DD')
    ))
    story.append(Spacer(1, 16))

    # ── Process sections ──────────────────────────────────
    for row in sections:
        sec_title   = row[0] or "Untitled Section"
        sec_content = row[1] or "No content available"

        story.append(Paragraph(html.escape(sec_title), section_style))
        story.append(HRFlowable(
            width="100%", thickness=0.5,
            color=colors.HexColor('#e0e0f0')
        ))
        story.append(Spacer(1, 8))

        lines     = sec_content.split('\n')
        i         = 0
        table_buf = []

        while i < len(lines):
            line = lines[i]

            # ── Table block ───────────────────────────────
            if is_table_row(line):
                table_buf.append(line)
                i += 1
                while i < len(lines) and (
                    is_table_row(lines[i]) or is_separator_row(lines[i])
                ):
                    table_buf.append(lines[i])
                    i += 1
                table_rows = parse_table_rows(table_buf)
                if table_rows:
                    pdf_table = build_pdf_table(table_rows)
                    if pdf_table:
                        story.append(Spacer(1, 8))
                        story.append(pdf_table)
                        story.append(Spacer(1, 12))
                table_buf = []
                continue

            clean_line = line.strip()

            # Skip empty lines
            if not clean_line:
                story.append(Spacer(1, 4))
                i += 1
                continue

            # Remove ## headings only
            clean_line = re.sub(r'#{1,6}\s*', '', clean_line)

           # ── Bullet point ──────────────────────────────
            if clean_line.startswith('•') or (clean_line.startswith('*') and not clean_line.startswith('**')):
                bullet_text = re.sub(r'^[•*]\s*', '', clean_line)
                # Auto bold label before colon e.g. "Primary Target Audience: ..."
                bullet_text = re.sub(
                    r'^([A-Za-z][^:]{2,50}):\s',
                    r'**\1:** ',
                    bullet_text
                )
                rich = render_rich_text_pdf(bullet_text)
                story.append(Paragraph(f"• {rich}", bullet_style))

            # ── Regular text ──────────────────────────────
            else:
                rich = render_rich_text_pdf(clean_line)
                story.append(Paragraph(rich, body_style))

            i += 1

        story.append(Spacer(1, 12))

    doc.build(story)

    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type="application/pdf"
    )


# ══════════════════════════════════════════════════════════
# DOCX DOWNLOAD
# ══════════════════════════════════════════════════════════

@router.get("/download/docx/{document_id}")
def download_docx(document_id: str):
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT dt.name FROM documents d
        JOIN document_templates dt ON d.template_id = dt.id
        WHERE d.id=%s
        """,
        (document_id,)
    )
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    title = result[0]

    cursor.execute(
        """
        SELECT DISTINCT ON (section_order)
            section_title, section_content, section_order
        FROM document_sections
        WHERE document_id=%s
        ORDER BY section_order, id DESC
        """,
        (document_id,)
    )
    sections = cursor.fetchall()
    cursor.close()
    conn.close()

    if not sections:
        raise HTTPException(status_code=404, detail="No content found")

    doc = Document()

    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    # ── Title ─────────────────────────────────────────────
    title_para           = doc.add_heading(title, level=0)
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in title_para.runs:
        run.font.color.rgb = RGBColor(0x1a, 0x1a, 0x3a)
        run.font.size      = Pt(22)
        run.font.bold      = True

    doc.add_paragraph("")

    # ── Rich text line to DOCX ────────────────────────────
    def add_rich_line_docx(para, text: str):
        """Add text with **bold** and __underline__ to an existing paragraph."""
        parts = re.split(r'(\*\*.*?\*\*|__.*?__)', text)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                run      = para.add_run(part[2:-2])
                run.bold = True
                run.font.size      = Pt(11)
                run.font.color.rgb = RGBColor(0x2a, 0x2a, 0x4a)
            elif part.startswith('__') and part.endswith('__'):
                run           = para.add_run(part[2:-2])
                run.underline = True
                run.font.size      = Pt(11)
                run.font.color.rgb = RGBColor(0x2a, 0x2a, 0x4a)
            else:
                if part:
                    run = para.add_run(part)
                    run.font.size      = Pt(11)
                    run.font.color.rgb = RGBColor(0x2a, 0x2a, 0x4a)

    # ── Add table to DOCX ─────────────────────────────────
    def add_table_to_doc(doc, rows):
        if not rows:
            return
        col_count  = max(len(r) for r in rows)
        normalized = []
        for row in rows:
            while len(row) < col_count:
                row.append('')
            normalized.append(row[:col_count])

        table       = doc.add_table(rows=len(normalized), cols=col_count)
        table.style = 'Table Grid'

        for i, row_data in enumerate(normalized):
            row = table.rows[i]
            for j, cell_text in enumerate(row_data):
                cell      = row.cells[j]
                cell.text = cell_text

                if i == 0:
                    for para in cell.paragraphs:
                        for run in para.runs:
                            run.font.bold      = True
                            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                            run.font.size      = Pt(10)
                    tc   = cell._tc
                    tcPr = tc.get_or_add_tcPr()
                    shd  = OxmlElement('w:shd')
                    shd.set(qn('w:val'),   'clear')
                    shd.set(qn('w:color'), 'auto')
                    shd.set(qn('w:fill'),  '7F77DD')
                    tcPr.append(shd)
                else:
                    for para in cell.paragraphs:
                        for run in para.runs:
                            run.font.size      = Pt(10)
                            run.font.color.rgb = RGBColor(0x2a, 0x2a, 0x4a)
                    if i % 2 == 0:
                        tc   = cell._tc
                        tcPr = tc.get_or_add_tcPr()
                        shd  = OxmlElement('w:shd')
                        shd.set(qn('w:val'),   'clear')
                        shd.set(qn('w:color'), 'auto')
                        shd.set(qn('w:fill'),  'F5F5FF')
                        tcPr.append(shd)

        doc.add_paragraph("")

    # ── Process sections ──────────────────────────────────
    for row in sections:
        sec_title   = row[0] or "Untitled Section"
        sec_content = row[1] or "No content available"

        heading = doc.add_heading(sec_title, level=1)
        for run in heading.runs:
            run.font.color.rgb = RGBColor(0x7F, 0x77, 0xDD)
            run.font.size      = Pt(14)

        lines     = sec_content.split('\n')
        i         = 0
        table_buf = []

        while i < len(lines):
            line = lines[i]

            # ── Table block ───────────────────────────────
            if is_table_row(line):
                table_buf.append(line)
                i += 1
                while i < len(lines) and (
                    is_table_row(lines[i]) or is_separator_row(lines[i])
                ):
                    table_buf.append(lines[i])
                    i += 1
                table_rows = parse_table_rows(table_buf)
                if table_rows:
                    add_table_to_doc(doc, table_rows)
                table_buf = []
                continue

            clean_line = line.strip()

            # Skip empty lines
            if not clean_line:
                doc.add_paragraph("")
                i += 1
                continue

            # Remove ## headings only
            clean_line = re.sub(r'#{1,6}\s*', '', clean_line).strip()

            # ── Bullet point ──────────────────────────────
            if clean_line.startswith('•') or (
                clean_line.startswith('*') and not clean_line.startswith('**')
            ):
                bullet_text = re.sub(r'^[•*]\s*', '', clean_line)
                # Auto bold label before colon
                bullet_text = re.sub(
                    r'^([A-Za-z][^:]{2,50}):\s',
                    r'**\1:** ',
                    bullet_text
                )
                para        = doc.add_paragraph(style='Normal')
                para.paragraph_format.left_indent = Pt(16)
                run_bullet           = para.add_run('• ')
                run_bullet.font.size = Pt(11)
                add_rich_line_docx(para, bullet_text)

            # ── Regular text ──────────────────────────────
            else:
                para = doc.add_paragraph(style='Normal')
                add_rich_line_docx(para, clean_line)

            i += 1

        doc.add_paragraph("")

    file_name = title.lower().replace(" ", "_") + ".docx"
    file_path = f"/tmp/{file_name}"
    doc.save(file_path)

    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )