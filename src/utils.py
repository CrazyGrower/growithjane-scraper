"""
Utility functions for the GrowLog Scraper.
"""

def load_config(verbose=False):
    """Load configuration."""
    if verbose:
        print("[LOG] Configuration loaded successfully")
        
    return {}  # Plus besoin de configuration depuis .env

def log_message(message, verbose=False):
    """Print a log message if verbose mode is enabled."""
    if verbose:
        print(f"[LOG] {message}")
        