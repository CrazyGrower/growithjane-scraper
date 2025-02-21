"""
PDF Generator module.
Handles the generation of PDF reports using WeasyPrint.
"""
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import os

def generate_pdf(title, entries, template_path="templates/template.html", verbose=False):
    """Generate a styled PDF using an HTML template and WeasyPrint."""
    if verbose:
        print("[LOG] Generating PDF...")

    # Créer le dossier output s'il n'existe pas
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)

    # PDF file name avec le chemin complet
    pdf_filename = os.path.join(output_dir, f"{title.replace(' ', '_')}.pdf")

    # Load the template
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template(template_path)

    # Render HTML with extracted data
    html_content = template.render(title=title, entries=entries)

    # Convert to PDF
    HTML(string=html_content).write_pdf(pdf_filename)

    if verbose:
        print(f"[LOG] PDF generated successfully: {pdf_filename}")
        
    return pdf_filename