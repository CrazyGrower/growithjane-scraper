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

    # Utiliser le chemin absolu pour le dossier de sortie
    output_dir = os.path.join('/app', 'output')
    os.makedirs(output_dir, exist_ok=True)

    # Utiliser le nom de la plante si disponible, sinon le titre, sinon 'growlog'
    plant_name = metadata.get('strain', {}).get('name')
    safe_title = (plant_name or title or "growlog").strip() or "growlog"
    filename = f"{safe_title.replace(' ', '_')}.pdf"
    output_path = os.path.join(output_dir, filename)
    
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

    # S'assurer que les chemins d'images sont corrects
    for entry in entries:
        if 'images' in entry:
            for img in entry['images']:
                if 'local_path' in img:
                    # Convertir le chemin en chemin relatif par rapport à /app
                    img['local_path'] = os.path.relpath(img['local_path'], '/app')

    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template(template_path)

    html_content = template.render(title=title, entries=entries, metadata=metadata)
    
    # Créer le PDF avec WeasyPrint en spécifiant le répertoire de base
    HTML(string=html_content, base_url='/app').write_pdf(output_path)

    if verbose:
        logger.info(f"PDF generated successfully: {output_path}")

    return output_path