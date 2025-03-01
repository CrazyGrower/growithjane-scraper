"""
Main script for the GrowLog Scraper.
"""
import os
import uvicorn
from src.web_interface import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8888))  # Render fournit le port via une variable d'env
    uvicorn.run(app, host="127.0.0.1", port=port)
