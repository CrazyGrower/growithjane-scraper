from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import asyncio
from src.utils import load_config
from src.scraper import load_page, extract_logs
from src.pdf_generator import generate_pdf
from src.video_generator import generate_video
from playwright.async_api import async_playwright
import os
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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

@app.post("/generate")
async def generate(request: Request):
    try:
        form_data = await request.form()
        url = form_data.get("url")
        if not url:
            return {"error": "URL non fournie"}

        need_video = str(form_data.get("generate_video", "false")).lower() in ("true", "1", "yes", "on")
        verbose_mode = str(form_data.get("verbose", "false")).lower() in ("true", "1", "yes", "on")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            await load_page(page, url, verbose_mode)
            await page.wait_for_load_state('networkidle')
            
            title = await page.title()
            entries = await extract_logs(page, verbose_mode)

            await context.close()
            await browser.close()

            # Générer le PDF
            pdf_file = generate_pdf(title, entries, verbose=verbose_mode)
            pdf_name = os.path.basename(pdf_file)

            if need_video:
                video_output = f"{title.replace(' ', '_')}.mp4"
                video_file = generate_video(pdf_file, video_output, verbose=verbose_mode)
                video_name = os.path.basename(video_file)

                # Retourner la vidéo pour téléchargement
                return FileResponse(
                    path=os.path.join(OUTPUT_DIR, video_name),
                    filename=video_name,
                    media_type="video/mp4"
                )

            # Retourner le PDF pour téléchargement
            return FileResponse(
                path=os.path.join(OUTPUT_DIR, pdf_name),
                filename=pdf_name,
                media_type="application/pdf"
            )

    except Exception as e:
        import traceback
        print("Debug - Traceback complet:")
        print(traceback.format_exc())
        return {"error": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)