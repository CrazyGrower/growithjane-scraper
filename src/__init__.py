"""
GrowLog Scraper package initialization.
"""
from .scraper import configure_driver, load_page, extract_logs
from .pdf_generator import generate_pdf
from .utils import load_config, log_message

__version__ = '1.0.0'
__author__ = 'Tistech'