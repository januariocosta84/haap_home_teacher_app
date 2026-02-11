from django.http import HttpResponse
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
from core.models import User, Municipality

def export_parents_pdf(request):
    municipality_id = request.GET.get("municipality")
    parents = User.objects.filter(role="parent").order_by('-date_joined')

    if municipality_id:
        parents = parents.filter(municipality_id=municipality_id)
        municipality_name = Municipality.objects.get(id=municipality_id).name
    else:
        municipality_name = "All Municipalities"

    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=(8.27*inch, 11.69*inch))  # A4

    story = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                 fontSize=16, textColor=colors.HexColor('#1f4788'),
                                 alignment=1, spaceAfter=12)
    story.append(Paragraph(f"Lista Parentes - {municipality_name}", title_style))
    story.append(Spacer(1, 0.2*inch))

    metadata_style = ParagraphStyle('Metadata', parent=styles['Normal'], fontSize=10, textColor=colors.grey)
    story.append(Paragraph(f"<i>Gerada iha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</i>", metadata_style))
    story.append(Spacer(1, 0.3*inch))

    total_parents = parents.count()
    story.append(Paragraph(f"Total Parentes: <b>{total_parents}</b>", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    table_data = [['Naran', 'WhatsApp', 'Email', 'Munisipiu']]
    for parent in parents:
        table_data.append([
            f"{parent.first_name} {parent.last_name}",
            parent.whatsapp_number or "-",
            parent.email or "-",
            str(parent.municipality) if parent.municipality else "-"
        ])

    if len(table_data) > 1:
        table = Table(table_data, colWidths=[2*inch, 1.5*inch, 2*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.lightgrey]),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("Walha dados no filtru ne'e.", styles['Normal']))

    doc.build(story)
    pdf_buffer.seek(0)

    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="parents_list_{municipality_name.replace(" ", "_")}_{datetime.now().strftime("%d%m%Y")}.pdf"'
    return response
