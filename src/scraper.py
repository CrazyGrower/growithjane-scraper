"""GrowWithJane scraper module."""
from playwright.async_api import Page

async def load_page(page: Page, url: str, verbose=False):
    """Load the page and scroll to load all content."""
    if verbose:
        print(f"[LOG] Loading page: {url}")
    
    await page.goto(url)
    await page.wait_for_timeout(5000)

    if verbose:
        print("[LOG] Scrolling the page dynamically...")
    
    last_height = await page.evaluate("document.body.scrollHeight")
    while True:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        await page.wait_for_timeout(2000)
        new_height = await page.evaluate("document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    await page.wait_for_selector("div.date-container")
    return await page.query_selector_all("div.date-container")

async def extract_logs(page: Page, verbose=False):
    """Extract grow logs from the loaded page."""
    if verbose:
        print("[LOG] Extracting logs...")
    
    log_containers = await page.query_selector_all("div.date-container")
    if verbose:
        print(f"[LOG] Found {len(log_containers)} logs.")

    entries = []
    for log_entry in log_containers:
        try:
            entry_data = await extract_entry_data(log_entry, page)
            entries.append(entry_data)
            if verbose:
                print(f"[LOG] Extracted log: {entry_data['full_date']}")
        except Exception as e:
            if verbose:
                print(f"[ERROR] Failed to extract log entry: {e}")

    return entries

async def extract_entry_data(log_entry, page):
    """Extract data from a single log entry."""
    date_elem = await log_entry.query_selector("span.date-left")
    day_elem = await log_entry.query_selector("span.date-right, div.date-right")
    
    full_date = await date_elem.text_content() if date_elem else ""
    day_count = await day_elem.text_content() if day_elem else ""
    plant_state = await extract_plant_state(log_entry)
    actions, images = await extract_actions_and_images(log_entry, page)

    return {
        "full_date": full_date.strip(),
        "day_count": day_count.strip(),
        "plant_state": plant_state,
        "actions": actions,
        "images": images
    }

async def extract_plant_state(log_entry):
    """Extract the plant's state from a log entry."""
    try:
        icon_element = await log_entry.query_selector(".icon-rounded i")
        if icon_element:
            class_attr = await icon_element.get_attribute("class")
            return class_attr.split("icon-")[-1].strip()
    except:
        return "Unknown"
    return "Unknown"

async def extract_actions_and_images(log_entry, page):
    """Extract actions and images from a log entry."""
    actions, images = [], []
    
    # Trouver tous les éléments suivants jusqu'au prochain date-container
    sibling = await log_entry.evaluate_handle("el => el.nextElementSibling")
    while sibling:
        try:
            has_date_class = await sibling.evaluate("el => el.classList.contains('date-container')")
            if has_date_class:
                break
                
            # Photos
            photos_list = await sibling.query_selector("li:has-text('PHOTOS')")
            if photos_list:
                img_elements = await sibling.query_selector_all("img.timeline__image-grid__item__img")
                for img in img_elements:
                    src = await img.get_attribute("src")
                    if src:
                        images.append(src)
            
            # Actions
            actions_div = await sibling.query_selector("div:has-text('ACTIONS')")
            if actions_div:
                action_items = await sibling.query_selector_all("li.MuiListItem-root")
                for action in action_items:
                    title = await action.query_selector(".MuiTypography-body1")
                    desc = await action.query_selector(".MuiTypography-body2")
                    if title and desc:
                        title_text = await title.text_content()
                        desc_text = await desc.text_content()
                        actions.append(f"{title_text.strip()}: {desc_text.strip()}")
            
            sibling = await sibling.evaluate_handle("el => el.nextElementSibling")
        except:
            break
    
    return actions, images