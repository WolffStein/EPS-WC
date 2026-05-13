from __future__ import annotations

import os
from io import BytesIO
from html import escape
from datetime import datetime

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, Image

from .models import Operation


def _safe_paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(str(text) if text else "-").replace("\n", "<br/>"), style)

def get_month_name(month: int) -> str:
    months = [
        "janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
    ]
    return months[month - 1]

def build_operation_pdf(operation: Operation) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    stylesheet = getSampleStyleSheet()
    
    # Custom Styles based on DOCX
    styles = {
        "Header1": ParagraphStyle(
            "Header1",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=13,
            alignment=TA_CENTER,
            spaceAfter=2,
        ),
        "Header2": ParagraphStyle(
            "Header2",
            fontName="Helvetica",
            fontSize=11,
            leading=13,
            alignment=TA_CENTER,
            spaceAfter=2,
        ),
        "Header3": ParagraphStyle(
            "Header3",
            fontName="Helvetica",
            fontSize=10,
            leading=12,
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "Title": ParagraphStyle(
            "Title",
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            alignment=TA_CENTER,
            spaceAfter=16,
        ),
        "BodyJustify": ParagraphStyle(
            "BodyJustify",
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            alignment=TA_JUSTIFY,
            firstLineIndent=1.5 * cm,
            spaceAfter=8,
        ),
        "BodyBold": ParagraphStyle(
            "BodyBold",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=16,
            alignment=TA_LEFT,
        ),
        "Body": ParagraphStyle(
            "Body",
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            alignment=TA_LEFT,
            spaceAfter=6,
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            fontName="Helvetica",
            fontSize=10,
            leading=12,
            alignment=TA_LEFT,
        ),
        "TableHead": ParagraphStyle(
            "TableHead",
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            alignment=TA_CENTER,
        ),
        "Checkbox": ParagraphStyle(
            "Checkbox",
            fontName="Helvetica",
            fontSize=11,
            leading=14,
            alignment=TA_LEFT,
        ),
        "Signature": ParagraphStyle(
            "Signature",
            fontName="Helvetica",
            fontSize=10,
            leading=12,
            alignment=TA_CENTER,
        ),
    }

    story = []

    # 1. Header with Logo
    logo_path = os.path.join(settings.BASE_DIR, "static", "images", "pcdf_logo.png")
    if os.path.exists(logo_path):
        img = Image(logo_path, width=3*cm, height=3*cm)
        img.hAlign = 'CENTER'
        story.append(img)
    
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("POLÍCIA CIVIL DO DISTRITO FEDERAL", styles["Header1"]))
    story.append(Paragraph("DEPARTAMENTO DE COMBATE A CORRUPÇÃO E AO CRIME ORGANIZADO - DECOR", styles["Header2"]))
    story.append(Paragraph("DIVISÃO DE REPRESSÃO À CORRUPÇÃO - DICOR", styles["Header3"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("AUTO CIRCUNSTANCIADO DE BUSCA E APREENSÃO", styles["Title"]))

    # 2. Process Info Table
    process_data = [
        [
            Paragraph(f"<b>Processo nº:</b> {operation.processo_numero or '-'}", styles["TableCell"]),
            Paragraph(f"<b>Protocolo:</b> {operation.protocolo or '-'}", styles["TableCell"]),
            Paragraph(f"<b>Vara:</b> {operation.vara_criminal or '-'}", styles["TableCell"])
        ]
    ]
    process_table = Table(process_data, colWidths=[6*cm, 5*cm, 6*cm])
    process_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(process_table)
    story.append(Spacer(1, 0.5 * cm))

    # 3. Introduction Paragraph
    op_date = operation.data_operacao or datetime.now().date()
    day = op_date.day
    month = get_month_name(op_date.month)
    year = op_date.year
    
    team_members = [m.nome for m in operation.team_members.all()]
    team_str = ", ".join(team_members) if team_members else "equipe não informada"
    
    intro_text = (
        f"Aos {day} dia do mês de {month} do ano de {year}, "
        f"os Policiais Civis abaixo assinados: {team_str}, "
        f"dirigiram-se ao local: {operation.local_apreensao}, "
        f"Cidade: {operation.cidade_uf or '-'} a fim de dar cumprimento a Mandado de Busca e Apreensão, "
        f"tendo como alvo: {operation.suspeito_nome or '-'}. Onde procederam a referida busca "
        f"de acordo com as seguintes circunstâncias:"
    )
    story.append(Paragraph(intro_text, styles["BodyJustify"]))
    story.append(Spacer(1, 0.2 * cm))

    # Checkboxes (Circunstâncias)
    def checkbox_str(checked: bool) -> str:
        return "[ X ]" if checked else "[   ]"

    cb_data = [
        [
            Paragraph(f"{checkbox_str(operation.houve_arrombamento)} Com Arrombamento<br/>{checkbox_str(not operation.houve_arrombamento)} Sem Arrombamento", styles["Checkbox"]),
            Paragraph(f"{checkbox_str(operation.houve_recalcitrancia)} Com recalcitrância<br/>{checkbox_str(not operation.houve_recalcitrancia)} Sem recalcitrância", styles["Checkbox"]),
            Paragraph(f"{checkbox_str(operation.morador_ausente)} Sem a presença de morador<br/>{checkbox_str(not operation.morador_ausente)} Com a presença de morador", styles["Checkbox"]),
        ]
    ]
    cb_table = Table(cb_data, colWidths=[5.6*cm, 5.6*cm, 5.8*cm])
    cb_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(cb_table)
    
    if operation.obs_arrombamento_desobediencia:
        story.append(Paragraph(f"<b>Obs (Arrombamento/Desobediência):</b> {operation.obs_arrombamento_desobediencia}", styles["Body"]))
    
    story.append(Spacer(1, 0.5 * cm))

    # Witnesses
    witnesses = operation.witnesses.all()
    if witnesses:
        story.append(Paragraph("TESTEMUNHAS:", styles["BodyBold"]))
        for i, w in enumerate(witnesses, 1):
            w_text = (
                f"{i}. <b>Nome:</b> {w.nome or '-'} "
                f"<b>RG:</b> {w.rg or '-'} "
                f"<b>CPF:</b> {w.cpf or '-'}<br/>"
                f"<b>Filiação:</b> {w.filiacao or '-'}<br/>"
                f"<b>Endereço:</b> {w.endereco or '-'} "
                f"<b>Cidade/UF:</b> {w.cidade_uf or '-'}<br/>"
                f"<b>Telefone:</b> {w.telefone or '-'}"
            )
            if w.observacoes:
                w_text += f"<br/><b>Obs:</b> {w.observacoes}"
            story.append(Paragraph(w_text, styles["Body"]))
            story.append(Spacer(1, 0.2 * cm))
    else:
        story.append(Paragraph("Nenhuma testemunha registrada.", styles["Body"]))

    story.append(Spacer(1, 0.5 * cm))

    # 4. ITENS ARRECADADOS Table
    story.append(Paragraph("ITENS ARRECADADOS:", styles["BodyBold"]))
    story.append(Spacer(1, 0.2 * cm))

    all_items = operation.items.select_related('category').prefetch_related('extra_field_items')
    info_items = []
    other_items = []

    for item in all_items:
        # PCDF standard dual table: Informatics vs Others
        # If category name contains 'informática', 'celular', 'mídia', 'computador', etc.
        cat_name = item.category.nome.lower()
        is_info = any(kw in cat_name for kw in ['informática', 'celular', 'mídia', 'computador', 'notebook', 'tablet', 'eletrônico'])
        
        if is_info:
            info_items.append(item)
        else:
            other_items.append(item)

    def _build_item_table(title: str, items_list) -> None:
        story.append(Paragraph(title, styles["TableHead"]))
        
        t_data = [
            [Paragraph("Item", styles["TableHead"]), Paragraph("Descrição", styles["TableHead"])]
        ]
        
        if items_list:
            for idx, it in enumerate(items_list, 1):
                desc_parts = []
                if it.descricao:
                    desc_parts.append(it.descricao)
                for field in it.extra_field_items:
                    desc_parts.append(f"{field['label']}: {field['value']}")
                if it.local_encontrado:
                    desc_parts.append(f"Local Encontrado: {it.local_encontrado}")
                    
                desc_text = "<br/>".join(desc_parts) if desc_parts else "-"
                
                t_data.append([
                    Paragraph(str(idx), styles["TableCell"]),
                    Paragraph(desc_text, styles["TableCell"])
                ])
        else:
             t_data.append([
                 Paragraph("-", styles["TableCell"]),
                 Paragraph("Nenhum item registrado nesta categoria.", styles["TableCell"])
             ])
             
        t_table = Table(t_data, colWidths=[2*cm, 15*cm])
        t_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ]))
        story.append(t_table)
        story.append(Spacer(1, 0.5 * cm))

    _build_item_table("MATERIAIS DE INFORMÁTICA, APARELHOS CELULARES E MÍDIAS", info_items)
    _build_item_table("OUTROS MATERIAIS, OBJETOS E DOCUMENTOS", other_items)

    if operation.observacoes_complementares:
        story.append(Paragraph(f"<b>Observações Complementares:</b><br/>{operation.observacoes_complementares}", styles["Body"]))
        story.append(Spacer(1, 0.5 * cm))

    # 5. Footer Text
    footer_text = (
        "E por nada mais haver a consignar, foi lavrado o presente Auto de Busca "
        "e Apreensão, que depois de lido e achado conforme, vai devidamente assinado."
    )
    story.append(Paragraph(footer_text, styles["BodyJustify"]))
    story.append(Spacer(1, 1.5 * cm))

    # 6. Signatures
    sig_line = "______________________________________________________"
    
    # Morador/Responsável signature
    story.append(Paragraph(sig_line, styles["Signature"]))
    story.append(Paragraph("ASSINATURA MORADOR/ RESPONSÁVEL", styles["Signature"]))
    story.append(Spacer(1, 1.5 * cm))
    
    # Team members signatures (2 in a row if possible)
    team = list(operation.team_members.all())
    
    for i in range(0, len(team), 2):
        row_data = []
        # First sig in row
        m1 = team[i]
        p1 = Paragraph(f"{sig_line}<br/>{m1.nome}<br/>{m1.cargo} - Mat. {m1.matricula or '-'}", styles["Signature"])
        row_data.append(p1)
        
        # Second sig in row (if exists)
        if i + 1 < len(team):
            m2 = team[i+1]
            p2 = Paragraph(f"{sig_line}<br/>{m2.nome}<br/>{m2.cargo} - Mat. {m2.matricula or '-'}", styles["Signature"])
            row_data.append(p2)
        else:
            row_data.append(Paragraph("", styles["Signature"]))
            
        sig_table = Table([row_data], colWidths=[8.5*cm, 8.5*cm])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 30),
        ]))
        story.append(sig_table)

    doc.build(story)
    return buffer.getvalue()
