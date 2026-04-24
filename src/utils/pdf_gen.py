from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import os

class InvoiceGenerator:
    def __init__(self, output_dir="invoices"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def generate(self, invoice_data):
        """
        invoice_data = {
            "invoice_id": "SL-00001",
            "date": "2026-04-24",
            "customer": "Walk-in Customer",
            "items": [
                {"name": "Sun Atta 1 kg", "qty": 2, "price": 100, "total": 200},
                ...
            ],
            "subtotal": 500,
            "discount": 10,
            "grand_total": 490
        }
        """
        filename = f"Invoice_{invoice_data['invoice_id']}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()

            # Header
            elements.append(Paragraph(f"<b>SunERP Professional</b>", styles['Title']))
            elements.append(Paragraph("123 Business Street, Warehouse Zone", styles['Normal']))
            elements.append(Spacer(1, 12))

            # Invoice Info
            elements.append(Paragraph(f"<b>Invoice:</b> {invoice_data['invoice_id']}", styles['Normal']))
            elements.append(Paragraph(f"<b>Date:</b> {invoice_data['date']}", styles['Normal']))
            elements.append(Paragraph(f"<b>Customer:</b> {invoice_data['customer']}", styles['Normal']))
            elements.append(Spacer(1, 12))

            # Table Header
            data = [["Product", "Qty", "Price", "Total"]]
            for item in invoice_data['items']:
                data.append([item['name'], item['qty'], f"{item['price']:,.2f}", f"{item['total']:,.2f}"])
            
            data.append(["", "", "Subtotal:", f"{invoice_data['subtotal']:,.2f}"])
            data.append(["", "", "Discount:", f"{invoice_data['discount']:,.2f}"])
            data.append(["", "", "Grand Total:", f"{invoice_data['grand_total']:,.2f}"])

            table = Table(data, colWidths=[250, 50, 80, 80])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#3B82F6")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -4), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -4), 0.5, colors.grey),
                ('ALIGN', (2, -3), (3, -1), 'RIGHT'),
                ('FONTNAME', (2, -1), (3, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (2, -1), (3, -1), colors.HexColor("#3B82F6")),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 24))
            elements.append(Paragraph("Thank you for your business!", styles['Italic']))

            doc.build(elements)
            return filepath
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return None
