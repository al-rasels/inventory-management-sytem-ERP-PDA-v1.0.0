from src.utils.pdf_gen import InvoiceGenerator, ReportGenerator

class PDFService:
    """Unified service for all PDF generation needs."""
    
    def __init__(self, invoice_dir="invoices", report_dir="reports"):
        self.invoice_gen = InvoiceGenerator(invoice_dir)
        self.report_gen = ReportGenerator(report_dir)

    def generate_invoice(self, invoice_data):
        return self.invoice_gen.generate(invoice_data)

    def generate_report(self, title, headers, data, filename_prefix="Report"):
        return self.report_gen.generate(title, headers, data, filename_prefix)
