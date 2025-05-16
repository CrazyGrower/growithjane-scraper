from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import asyncio
from src.utils import load_config
from src.grow_with_jane_scraper import GrowWithJaneScraper
from src.pdf_generator import generate_pdf
from src.video_generator import generate_video
import os
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('web_interface')

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")

app = FastAPI()

# Obtenir le chemin absolu du dossier racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Configuration des templates et fichiers statiques avec les chemins absolus
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html", 
        {"request": request}
    )

@app.post("/generate_video")
async def generate_video_endpoint(request: Request):
    form_data = await request.form()
    pdf_filename = form_data.get("pdf_filename")
    if not pdf_filename:
        return {"error": "PDF filename not provided"}
    pdf_path = os.path.join(OUTPUT_DIR, pdf_filename)
    if not os.path.exists(pdf_path):
        return {"error": "PDF file not found"}
    video_output = pdf_filename.replace('.pdf', '.mp4')
    video_file = generate_video(pdf_path, video_output, verbose=True)
    video_name = os.path.basename(video_file)
    return FileResponse(
        path=os.path.join(OUTPUT_DIR, video_name),
        filename=video_name,
        media_type="video/mp4",
        headers={"Content-Disposition": f"attachment; filename={video_name}"}
    )

@app.post("/generate")
async def generate(request: Request):
    try:
        form_data = await request.form()
        url = form_data.get("url")
        if not url:
            return {"error": "URL non fournie"}

        verbose_mode = str(form_data.get("verbose", "false")).lower() in ("true", "1", "yes", "on")

        if verbose_mode:
            logger.info(f"Starting scraping with verbose mode for URL: {url}")

        # Utiliser notre nouveau scraper
        scraper = GrowWithJaneScraper(verbose=verbose_mode)
        growlog_data = await scraper.get_growlog_data(url)

        if not growlog_data:
            if verbose_mode:
                logger.error("No data retrieved from the growlog")
            return {"error": "Impossible de récupérer les données du growlog"}

        # Préparer les données pour le template
        title = growlog_data.get("title", "Growlog")
        if not title or not title.strip():
            title = "Growlog"
        
        if verbose_mode:
            logger.info(f"Processing data for growlog: {title}")
            logger.info(f"Found {len(growlog_data.get('timeline', []))} timeline entries")
            logger.info(f"Found {len(growlog_data.get('photos', []))} photos")
        
        # Convertir les données du scraper au format attendu par le template
        def parse_date(date_str):
            for suffix in ['st', 'nd', 'rd', 'th']:
                date_str = date_str.replace(suffix, '')
            try:
                return datetime.strptime(date_str.strip(), "%b %d %y")
            except Exception:
                return None
        stage_changes = []
        for sc in growlog_data.get("stage_changes", []):
            d = parse_date(sc.get("date", ""))
            if d and sc.get("plant_state"):
                stage_changes.append({"date": d, "plant_state": sc.get("plant_state")})
        stage_changes.sort(key=lambda x: x["date"])
        entries = []
        for event in growlog_data.get("timeline", []):
            event_date = parse_date(event.get("date", ""))
            plant_state = None
            for sc in reversed(stage_changes):
                if event_date and sc["date"] <= event_date:
                    plant_state = sc["plant_state"]
                    break
            entry = {
                "full_date": event.get("date", ""),
                "day_count": event.get("day_count", ""),
                "plant_state": plant_state,
                "stage_change": event.get("stage_change", ""),
                "actions": event.get("actions", []),
                "images": event.get("photos", []),
                "tree_logs": event.get("tree_logs", {})
            }
            entries.append(entry)

        # Préparer le metadata avec les stages, strain et environment enrichis
        metadata = {
            "strain": {
                "brand": "Unknown",  # Peut être enrichi si tu as la marque
                "name": growlog_data.get("strain", "Unknown strain")
            },
            "environment": growlog_data.get("environment", {}),
            "stages": growlog_data.get("stages", [])
        }

        if verbose_mode:
            logger.info("Generating PDF...")

        # Générer le PDF
        pdf_file = generate_pdf(title, entries, metadata, verbose=verbose_mode)
        pdf_name = os.path.basename(pdf_file)

        if verbose_mode:
            logger.info(f"PDF generated: {pdf_name}")

        if not os.path.exists(os.path.join(OUTPUT_DIR, pdf_name)):
            logger.error(f"PDF file not found: {os.path.join(OUTPUT_DIR, pdf_name)}")
            return {"error": "PDF file not found"}

        logger.info(f"Retour du PDF (POST): {os.path.abspath(os.path.join(OUTPUT_DIR, pdf_name))}")
        logger.info(f"Fichier existe: {os.path.exists(os.path.abspath(os.path.join(OUTPUT_DIR, pdf_name)))}")

        # Retourner le PDF pour téléchargement
        try:
            return FileResponse(
                path=os.path.abspath(os.path.join(OUTPUT_DIR, pdf_name)),
                filename=pdf_name,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={pdf_name}"}
            )
        except Exception as e:
            logger.error(f"Erreur lors du retour du PDF: {e}")
            return {"error": str(e)}
    except Exception as e:
        import traceback
        if 'verbose_mode' in locals() and verbose_mode:
            logger.error("Debug - Traceback complet:")
            logger.error(traceback.format_exc())
        return {"error": str(e)}

@app.get("/test_download")
async def test_download():
    test_path = os.path.abspath(os.path.join(OUTPUT_DIR, "Growlog.pdf"))
    if not os.path.exists(test_path):
        return {"error": "not found"}
    return FileResponse(
        path=test_path,
        filename="Growlog.pdf",
        media_type="application/pdf"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)