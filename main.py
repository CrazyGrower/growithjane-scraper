import argparse
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import requests
import time

# Load environment variables
load_dotenv()
URL = os.getenv("GROWLOG_URL")

# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
args = parser.parse_args()

def log(message):
    if args.verbose:
        print(message)

def configure_driver():
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
    log(f"[LOG] Loading page: {url}")
    driver.get(url)
    time.sleep(10)
    log("[LOG] Performing page scroll to load logs...")
    body = driver.find_element(By.TAG_NAME, "body")
    for _ in range(20):
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(1)
    log("[LOG] Page loaded and scrolled.")
    return WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.date-container")))

def extract_logs(driver):
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
    try:
        icon_element = log_entry.find_element(By.XPATH, ".//div[contains(@class, 'icon-rounded')]/i")
        return icon_element.get_attribute("class").split("icon-")[-1].strip()
    except:
        return "Unknown"

def extract_actions_and_images(log_entry):
    actions, images = [], []
    for elem in log_entry.find_elements(By.XPATH, "following-sibling::*"):
        if "date-container" in elem.get_attribute("class"):
            break
        if elem.find_elements(By.XPATH, ".//li[contains(text(), 'PHOTOS')]"):
            images = [img.get_attribute("src") for img in elem.find_elements(By.XPATH, ".//img[contains(@class, 'timeline__image-grid__item__img')]")]
        if elem.find_elements(By.XPATH, ".//div[contains(text(), 'ACTIONS')]"):
            actions = [f"{action.find_element(By.XPATH, './/span[contains(@class, "MuiTypography-body1")]').text.strip()}: {action.find_element(By.XPATH, './/p[contains(@class, "MuiTypography-body2")]').text.strip()}" for action in elem.find_elements(By.XPATH, ".//li[contains(@class, 'MuiListItem-root')]")]
    return actions, images

def generate_pdf(title, entries):
    log("[LOG] Generating PDF...")
    pdf_filename = f"{title.replace(' ', '_')}.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 50, f"Grow Log: {title}")
    y_position = height - 100

    for i, entry in enumerate(entries):
        if y_position < 150:
            c.showPage()
            y_position = height - 50
            c.setFont("Helvetica-Bold", 12)

        state_text = f" - {entry['plant_state'].capitalize()}" if entry["plant_state"] != "Unknown" else ""
        c.setFont("Helvetica-Bold", 12)
        c.drawString(100, y_position, f"{entry['full_date']} ({entry['day_count']}){state_text}")
        y_position -= 20
        c.setFont("Helvetica", 10)

        for action in entry["actions"]:
            c.drawString(120, y_position, f"- {action}")
            y_position -= 15

        for img_url in entry["images"]:
            if y_position < 200:
                c.showPage()
                y_position = height - 50
                c.setFont("Helvetica-Bold", 12)

            img_path = f"temp_img_{i}.jpg"
            response = requests.get(img_url, stream=True)
            if response.status_code == 200:
                with open(img_path, "wb") as img_file:
                    img_file.write(response.content)
                if os.path.getsize(img_path) > 0:
                    c.drawImage(ImageReader(img_path), 100, y_position - 150, width=200, height=150)
                    y_position -= 180
                os.remove(img_path)
        y_position -= 20
    c.save()
    log(f"[LOG] PDF generated successfully: {pdf_filename}")
    return pdf_filename

driver = configure_driver()
log_containers = load_page(driver, URL)
title = driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
log(f"[LOG] Extracted Title: {title}")
entries = extract_logs(driver)
driver.quit()
pdf_file = generate_pdf(title, entries)
