"""
PDF Generator module.
Handles the generation of PDF reports using WeasyPrint.
"""
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

def generate_pdf(title, entries, template_path="templates/template.html", verbose=False):
    """Generate a styled PDF using an HTML template and WeasyPrint."""
    # Convertir verbose en booléen si c'est une string
    if isinstance(verbose, str):
        verbose = verbose.lower() == "true"
    
    if verbose:
        print("[LOG] Generating PDF...")

    # Load the template
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template(template_path)

    # Render HTML with extracted data
    html_content = template.render(title=title, entries=entries)

    # PDF file name
    pdf_filename = f"{title.replace(' ', '_')}.pdf"

    # Convert to PDF
    HTML(string=html_content).write_pdf(pdf_filename)

    if verbose:
        print(f"[LOG] PDF generated successfully: {pdf_filename}")
        
    return pdf_filename