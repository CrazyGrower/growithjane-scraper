"""
Main script for the GrowLog Scraper.
"""
import argparse
import asyncio
from playwright.async_api import async_playwright
from src.utils import load_config, log_message
from src.scraper import load_page, extract_logs
from src.pdf_generator import generate_pdf
from src.video_generator import generate_video

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    try:
        config = load_config(args.verbose)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)  # Mode headless activé
            context = await browser.new_context()
            page = await context.new_page()
            
            await load_page(page, config['url'], args.verbose)
            await page.wait_for_load_state('networkidle')  # Attendre que la page soit complètement chargée
            
            title = await page.title()
            entries = await extract_logs(page, args.verbose)
            
            pdf_file = generate_pdf(title, entries, verbose=args.verbose)
            video_output = title + ".mp4"
            generate_video(pdf_file, video_output)
            
            await context.close()
            await browser.close()
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    asyncio.run(main())