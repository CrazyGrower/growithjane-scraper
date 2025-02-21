"""
Utility functions for the GrowLog Scraper.
"""
import os
from dotenv import load_dotenv

def load_config(verbose=False):
    """Load and validate configuration from environment variables."""
    load_dotenv()
    
    config = {
        'url': os.getenv("GROWLOG_URL"),
        'chromedriver_path': None  # Playwright ne nécessite pas de chemin pour le driver
    }
    
    # Validate configuration
    if not config['url']:
        raise ValueError("GROWLOG_URL is not set in .env file")
    if not config['chromedriver_path']:
        print("Playwright will manage the browser driver automatically.")
        
    if verbose:
        print("[LOG] Configuration loaded successfully")
        
    return config

def log_message(message, verbose=False):
    """Print a log message if verbose mode is enabled."""
    if verbose:
        print(f"[LOG] {message}")