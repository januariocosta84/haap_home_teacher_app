from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.lib.pagesizes import A4

def generate_parents_pdf(parents):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    data = [["Name", "WhatsApp", "Municipality"]]
    for p in parents:
        data.append([p.first_name, p.whatsapp_number, str(p.municipality)])

    table = Table(data)
    doc.build([table])
    buffer.seek(0)
    return buffer
