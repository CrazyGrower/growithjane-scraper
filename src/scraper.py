"""GrowWithJane scraper module.
Handles all web scraping functionality using Selenium."""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def configure_driver(chromedriver_path, verbose=False):
    """Configure and return the Selenium WebDriver."""
    if verbose:
        print("[LOG] Configuring WebDriver...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver

def load_page(driver, url, verbose=False):
    """Load the page and scroll to load all content."""
    if verbose:
        print(f"[LOG] Loading page: {url}")
    
    driver.get(url)
    time.sleep(5)

    if verbose:
        print("[LOG] Scrolling the page dynamically...")
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    return WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.date-container"))
    )

def extract_logs(driver, verbose=False):
    """Extract grow logs from the loaded page."""
    if verbose:
        print("[LOG] Extracting logs...")
    
    entries = []
    log_containers = driver.find_elements(By.CSS_SELECTOR, "div.date-container")
    
    if verbose:
        print(f"[LOG] Found {len(log_containers)} logs.")

    for log_entry in log_containers:
        try:
            entry_data = extract_entry_data(log_entry)
            entries.append(entry_data)
            
            if verbose:
                print(f"[LOG] Extracted log: {entry_data['full_date']} "
                      f"({entry_data['day_count']}) - {entry_data['plant_state']}, "
                      f"{len(entry_data['actions'])} actions, "
                      f"{len(entry_data['images'])} images.")
        
        except Exception as e:
            if verbose:
                print(f"[ERROR] Failed to extract log entry: {e}")

    return entries

def extract_entry_data(log_entry):
    """Extract data from a single log entry."""
    full_date = log_entry.find_element(By.CSS_SELECTOR, "span.date-left").text.strip()
    day_count = log_entry.find_element(By.CSS_SELECTOR, "span.date-right, div.date-right").text.strip()
    plant_state = extract_plant_state(log_entry)
    actions, images = extract_actions_and_images(log_entry)

    return {
        "full_date": full_date,
        "day_count": day_count,
        "plant_state": plant_state,
        "actions": actions,
        "images": images
    }

def extract_plant_state(log_entry):
    """Extract the plant's state from a log entry."""
    try:
        icon_element = log_entry.find_element(
            By.XPATH, 
            ".//div[contains(@class, 'icon-rounded')]/i"
        )
        return icon_element.get_attribute("class").split("icon-")[-1].strip()
    except:
        return "Unknown"

def extract_actions_and_images(log_entry):
    """Extract actions and images from a log entry."""
    actions, images = [], []
    
    for elem in log_entry.find_elements(By.XPATH, "following-sibling::*"):
        if "date-container" in elem.get_attribute("class"):
            break
            
        if elem.find_elements(By.XPATH, ".//li[contains(text(), 'PHOTOS')]"):
            images = [
                img.get_attribute("src") 
                for img in elem.find_elements(
                    By.XPATH, 
                    ".//img[contains(@class, 'timeline__image-grid__item__img')]"
                )
            ]
            
        if elem.find_elements(By.XPATH, ".//div[contains(text(), 'ACTIONS')]"):
            actions = [
                f"{action.find_element(By.XPATH, './/span[contains(@class, \"MuiTypography-body1\")]').text.strip()}: "
                f"{action.find_element(By.XPATH, './/p[contains(@class, \"MuiTypography-body2\")]').text.strip()}"
                for action in elem.find_elements(By.XPATH, ".//li[contains(@class, 'MuiListItem-root')]")
            ]
            
    return actions, images