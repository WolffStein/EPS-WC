from __future__ import annotations

from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import Operation


def _build_page_number(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#425466"))
    canvas.drawRightString(A4[0] - 1.5 * cm, 1 * cm, f"Página {doc.page}")
    canvas.restoreState()


def _safe_paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(text or "-").replace("\n", "<br/>"), style)


def _metadata_table(operation: Operation, styles) -> Table:
    rows = [
        [
            _safe_paragraph("Código", styles["Label"]),
            _safe_paragraph(operation.codigo, styles["Value"]),
            _safe_paragraph("Data", styles["Label"]),
            _safe_paragraph(operation.data_operacao.strftime("%d/%m/%Y"), styles["Value"]),
        ],
        [
            _safe_paragraph("Operação", styles["Label"]),
            _safe_paragraph(operation.nome, styles["Value"]),
            _safe_paragraph("Status", styles["Label"]),
            _safe_paragraph(operation.get_status_display(), styles["Value"]),
        ],
        [
            _safe_paragraph("Departamento", styles["Label"]),
            _safe_paragraph(operation.departamento, styles["Value"]),
            _safe_paragraph("Responsável", styles["Label"]),
            _safe_paragraph(operation.responsavel, styles["Value"]),
        ],
        [
            _safe_paragraph("Local", styles["Label"]),
            _safe_paragraph(operation.local_apreensao, styles["Value"]),
            _safe_paragraph("Cidade / UF", styles["Label"]),
            _safe_paragraph(operation.cidade_uf or "-", styles["Value"]),
        ],
        [
            _safe_paragraph("Suspeito / alvo", styles["Label"]),
            _safe_paragraph(operation.suspeito_nome, styles["Value"]),
            _safe_paragraph("Documento", styles["Label"]),
            _safe_paragraph(operation.suspeito_documento or "-", styles["Value"]),
        ],
        [
            _safe_paragraph("Endereço do suspeito", styles["Label"]),
            _safe_paragraph(operation.suspeito_endereco or "-", styles["Value"]),
            _safe_paragraph("Encerrada em", styles["Label"]),
            _safe_paragraph(
                operation.encerrada_em.strftime("%d/%m/%Y %H:%M")
                if operation.encerrada_em
                else "-",
                styles["Value"],
            ),
        ],
    ]

    table = Table(rows, colWidths=[3.2 * cm, 6.1 * cm, 3.2 * cm, 5.4 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#0f172a")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#94a3b8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _team_table(operation: Operation, styles) -> Table:
    rows = [[
        _safe_paragraph("Nome", styles["TableHead"]),
        _safe_paragraph("Cargo", styles["TableHead"]),
        _safe_paragraph("Matrícula", styles["TableHead"]),
        _safe_paragraph("Contato", styles["TableHead"]),
    ]]

    if operation.team_members.exists():
        for member in operation.team_members.all():
            rows.append(
                [
                    _safe_paragraph(member.nome, styles["Cell"]),
                    _safe_paragraph(member.cargo, styles["Cell"]),
                    _safe_paragraph(member.matricula or "-", styles["Cell"]),
                    _safe_paragraph(member.contato or "-", styles["Cell"]),
                ]
            )
    else:
        rows.append(
            [
                _safe_paragraph("Equipe não cadastrada.", styles["Cell"]),
                _safe_paragraph("-", styles["Cell"]),
                _safe_paragraph("-", styles["Cell"]),
                _safe_paragraph("-", styles["Cell"]),
            ]
        )

    table = Table(rows, colWidths=[6 * cm, 4.2 * cm, 3.2 * cm, 3.2 * cm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#0f172a")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _items_table(operation: Operation, styles) -> Table:
    rows = [[
        _safe_paragraph("#", styles["TableHead"]),
        _safe_paragraph("Item", styles["TableHead"]),
        _safe_paragraph("Categoria", styles["TableHead"]),
        _safe_paragraph("Qtd.", styles["TableHead"]),
        _safe_paragraph("Detalhes", styles["TableHead"]),
    ]]

    if operation.items.exists():
        for index, item in enumerate(operation.items.all(), start=1):
            details = []
            if item.local_encontrado:
                details.append(f"Local encontrado: {item.local_encontrado}")
            if item.estado:
                details.append(f"Estado: {item.estado}")
            if item.descricao:
                details.append(f"Descrição: {item.descricao}")
            details.extend(f"{field['label']}: {field['value']}" for field in item.extra_field_items)

            rows.append(
                [
                    _safe_paragraph(str(index), styles["Cell"]),
                    _safe_paragraph(item.titulo, styles["Cell"]),
                    _safe_paragraph(item.category.nome, styles["Cell"]),
                    _safe_paragraph(str(item.quantidade), styles["Cell"]),
                    _safe_paragraph("\n".join(details) or "-", styles["Cell"]),
                ]
            )
    else:
        rows.append(
            [
                _safe_paragraph("-", styles["Cell"]),
                _safe_paragraph("Nenhum item apreendido cadastrado.", styles["Cell"]),
                _safe_paragraph("-", styles["Cell"]),
                _safe_paragraph("-", styles["Cell"]),
                _safe_paragraph("-", styles["Cell"]),
            ]
        )

    table = Table(
        rows,
        colWidths=[1 * cm, 4.3 * cm, 3.1 * cm, 1.2 * cm, 8 * cm],
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#0f172a")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def build_operation_pdf(operation: Operation) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.4 * cm,
        rightMargin=1.4 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    stylesheet = getSampleStyleSheet()
    styles = {
        "Title": ParagraphStyle(
            "Title",
            parent=stylesheet["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=8,
        ),
        "Subtitle": ParagraphStyle(
            "Subtitle",
            parent=stylesheet["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#475569"),
            spaceAfter=14,
        ),
        "Section": ParagraphStyle(
            "Section",
            parent=stylesheet["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#0f766e"),
            spaceBefore=8,
            spaceAfter=8,
        ),
        "Label": ParagraphStyle(
            "Label",
            parent=stylesheet["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#0f172a"),
        ),
        "Value": ParagraphStyle(
            "Value",
            parent=stylesheet["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#0f172a"),
        ),
        "TableHead": ParagraphStyle(
            "TableHead",
            parent=stylesheet["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.white,
        ),
        "Cell": ParagraphStyle(
            "Cell",
            parent=stylesheet["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#0f172a"),
        ),
        "Note": ParagraphStyle(
            "Note",
            parent=stylesheet["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#475569"),
        ),
    }

    story = [
        Paragraph("Auto de Apreensão", styles["Title"]),
        Paragraph(
            "Documento gerado pelo MVP de inventário de apreensões da operação.",
            styles["Subtitle"],
        ),
        _metadata_table(operation, styles),
        Spacer(1, 0.35 * cm),
        Paragraph("Equipe da Operação", styles["Section"]),
        _team_table(operation, styles),
        Spacer(1, 0.35 * cm),
        Paragraph("Itens Apreendidos", styles["Section"]),
        _items_table(operation, styles),
    ]

    if operation.observacoes:
        story.extend(
            [
                Spacer(1, 0.35 * cm),
                Paragraph("Observações", styles["Section"]),
                _safe_paragraph(operation.observacoes, styles["Value"]),
            ]
        )

    story.extend(
        [
            Spacer(1, 0.45 * cm),
            Paragraph(
                "O layout final pode ser ajustado para espelhar o formulário oficial assim que o PDF base for disponibilizado pela PCDF.",
                styles["Note"],
            ),
        ]
    )

    doc.build(story, onFirstPage=_build_page_number, onLaterPages=_build_page_number)
    return buffer.getvalue()
