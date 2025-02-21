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
        
        # Validation de l'URL
        if not url:
            return {"success": False, "error": "URL non fournie"}
        if not url.startswith("https://growithjane.com/growlog/"):
            return {"success": False, "error": "URL invalide - Doit être une URL GrowWithJane valide"}
            
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

            pdf_file = generate_pdf(title, entries, verbose=verbose_mode)
            
            if need_video:
                video_output = f"{title.replace(' ', '_')}.mp4"
                generate_video(pdf_file, video_output, verbose=verbose_mode)
                return {"success": True, "pdf_file": pdf_file, "video_file": video_output}
            
            return {"success": True, "pdf_file": pdf_file}
            
    except Exception as e:
        import traceback
        print("Debug - Traceback complet:")
        print(traceback.format_exc())
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)