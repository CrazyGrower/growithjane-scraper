import argparse
import os
import time
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

# Load environment variables
load_dotenv()
URL = os.getenv("GROWLOG_URL")

# Argument for verbose mode
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
args = parser.parse_args()

def log(message):
    if args.verbose:
        print(message)

def configure_driver():
    """Configure and return the Selenium WebDriver."""
    log("[LOG] Configuring WebDriver...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    service = Service('/opt/homebrew/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    log("[LOG] WebDriver configured successfully.")
    return driver

def load_page(driver, url):
    """Load the page and dynamically scroll until everything is loaded."""
    log(f"[LOG] Loading page: {url}")
    driver.get(url)
    time.sleep(5)  # Initial loading wait

    log("[LOG] Scrolling the page dynamically...")
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Pause to allow content loading

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break  # Stop if the page no longer extends

        last_height = new_height

    log("[LOG] Page fully loaded.")
    return WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.date-container")))

def extract_logs(driver):
    """Extract grow logs from the page."""
    log("[LOG] Extracting logs...")
    entries = []
    log_containers = driver.find_elements(By.CSS_SELECTOR, "div.date-container")
    log(f"[LOG] Found {len(log_containers)} logs.")

    for log_entry in log_containers:
        try:
            full_date = log_entry.find_element(By.CSS_SELECTOR, "span.date-left").text.strip()
            day_count = log_entry.find_element(By.CSS_SELECTOR, "span.date-right, div.date-right").text.strip()
            plant_state = extract_plant_state(log_entry)
            actions, images = extract_actions_and_images(log_entry)

            entries.append({
                "full_date": full_date,
                "day_count": day_count,
                "plant_state": plant_state,
                "actions": actions,
                "images": images
            })

            log(f"[LOG] Extracted log: {full_date} ({day_count}) - {plant_state}, {len(actions)} actions, {len(images)} images.")
        except Exception as e:
            log(f"[ERROR] Failed to extract log entry: {e}")

    log("[LOG] Logs extracted successfully.")
    return entries

def extract_plant_state(log_entry):
    """Extract the plant's state if available."""
    try:
        icon_element = log_entry.find_element(By.XPATH, ".//div[contains(@class, 'icon-rounded')]/i")
        return icon_element.get_attribute("class").split("icon-")[-1].strip()
    except:
        return "Unknown"

def extract_actions_and_images(log_entry):
    """Extract actions and images associated with each log."""
    actions, images = [], []
    for elem in log_entry.find_elements(By.XPATH, "following-sibling::*"):
        if "date-container" in elem.get_attribute("class"):
            break
        if elem.find_elements(By.XPATH, ".//li[contains(text(), 'PHOTOS')]"):
            images = [img.get_attribute("src") for img in elem.find_elements(By.XPATH, ".//img[contains(@class, 'timeline__image-grid__item__img')]")]
        if elem.find_elements(By.XPATH, ".//div[contains(text(), 'ACTIONS')]"):
            actions = [f"{action.find_element(By.XPATH, './/span[contains(@class, \"MuiTypography-body1\")]').text.strip()}: {action.find_element(By.XPATH, './/p[contains(@class, \"MuiTypography-body2\")]').text.strip()}" for action in elem.find_elements(By.XPATH, ".//li[contains(@class, 'MuiListItem-root')]")]
    return actions, images

def generate_pdf(title, entries):
    """Generate a styled PDF using an HTML template and WeasyPrint."""
    log("[LOG] Generating PDF...")

    # Load the template
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("template.html")

    # Render HTML with extracted data
    html_content = template.render(title=title, entries=entries)

    # PDF file name
    pdf_filename = f"{title.replace(' ', '_')}.pdf"

    # Convert to PDF
    HTML(string=html_content).write_pdf(pdf_filename)

    log(f"[LOG] PDF generated successfully: {pdf_filename}")
    return pdf_filename

# 🚀 Script execution

driver = configure_driver()
log_containers = load_page(driver, URL)
title = driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
log(f"[LOG] Extracted Title: {title}")
entries = extract_logs(driver)
driver.quit()

# Generate PDF
pdf_file = generate_pdf(title, entries)
