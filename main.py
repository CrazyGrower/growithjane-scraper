"""
Main script for the GrowLog Scraper.
"""
from src.web_interface import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)  # reload=True pour le développement