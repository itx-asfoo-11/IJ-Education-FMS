import io
from reportlab.lib.pagesizes import A5
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import cm

def generate_payment_receipt(payment):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A5, rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=12,
        alignment=1, # Center
        textColor=colors.HexColor("#4f46e5")
    )
    elements.append(Paragraph("PAYMENT RECEIPT", title_style))
    elements.append(Paragraph("FMS PRO - Student Fees Management", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))

    # Payment Info Table
    data = [
        ["Receipt No:", f"REC-{payment.id:06d}"],
        ["Date:", payment.date.strftime("%Y-%m-%d")],
        ["Student Name:", payment.student.name],
        ["Roll No:", payment.student.roll_no],
        ["Class:", payment.student.student_class],
        ["Payment Mode:", payment.payment_mode],
        ["Amount Paid:", f"${payment.amount:,.2f}"],
    ]

    table = Table(data, colWidths=[4*cm, 8*cm])
    table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 1*cm))

    # Total Section
    total_data = [
        ["", "TOTAL PAID", f"${payment.amount:,.2f}"]
    ]
    total_table = Table(total_data, colWidths=[4*cm, 4*cm, 4*cm])
    total_table.setStyle(TableStyle([
        ('BACKGROUND', (1, 0), (2, 0), colors.HexColor("#4f46e5")),
        ('TEXTCOLOR', (1, 0), (2, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (2, 0), 'CENTER'),
        ('FONTNAME', (1, 0), (2, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 0), (2, 0), 12),
        ('TOPPADDING', (1, 0), (2, 0), 10),
        ('BOTTOMPADDING', (1, 0), (2, 0), 10),
    ]))
    elements.append(total_table)
    elements.append(Spacer(1, 2*cm))

    # Signature
    elements.append(Paragraph("________________________", styles['Normal']))
    elements.append(Paragraph("Authorized Signature", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer
