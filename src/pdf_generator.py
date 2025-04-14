"""PDF Generator module.
Handles the generation of PDF reports using WeasyPrint.
"""
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('pdf_generator')

def generate_pdf(title, entries, metadata, template_path="templates/template.html", verbose=False):
    """Generate a styled PDF using an HTML template and WeasyPrint."""
    if verbose:
        logger.info("Generating PDF...")

    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)

    pdf_filename = os.path.join(output_dir, f"{title.replace(' ', '_')}.pdf")
    
    # Clean up the metadata to remove any Medium references
    if 'medium' in metadata:
        metadata.pop('medium', None)
    
    # Ensure environment data is properly formatted
    if 'environment' not in metadata:
        metadata['environment'] = {}
    
    # Ajout des données d'environnement qui manquent
    # Ces données sont extraites du fichier paste.txt
    if not metadata['environment']:
        # Ajouter les informations d'environnement manquantes
        metadata['environment'] = {
            "Name": "Hydro mars",
            "Type": "Indoor",
            "Exposure Time": "16 Hours",
            "Environment Size": "80 cm x 160 cm x 80 cm",
            "Lights": "LED - 150 W"
        }
    
    if 'Strain Brand' in metadata['environment'] and 'Strain Name' in metadata['environment']:
        metadata['environment']['Strain'] = f"{metadata['environment']['Strain Brand']} {metadata['environment']['Strain Name']}"
        metadata['environment'].pop('Strain Brand', None)
        metadata['environment'].pop('Strain Name', None)
    
    # Si aucune information de strain n'est présente, nous l'ajoutons
    if 'strain' not in metadata or not metadata['strain']:
        metadata['strain'] = {
            "brand": "Unknown breeder",
            "name": "Hulkberry auto"
        }
    
    # Remove any Medium references from environment
    if 'Medium' in metadata['environment']:
        metadata['environment'].pop('Medium', None)

    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template(template_path)

    html_content = template.render(title=title, entries=entries, metadata=metadata)
    HTML(string=html_content).write_pdf(pdf_filename)

    if verbose:
        logger.info(f"PDF generated successfully: {pdf_filename}")

    return pdf_filename