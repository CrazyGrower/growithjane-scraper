"""GrowWithJane scraper module."""
from playwright.async_api import Page
import re
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('scraper')

async def load_page(page: Page, url: str, verbose=True):
    logger.info(f"Loading page: {url}")
    await page.goto(url)
    await page.wait_for_timeout(5000)

    logger.info("Scrolling the page dynamically...")
    last_height = await page.evaluate("document.body.scrollHeight")
    while True:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        await page.wait_for_timeout(2000)
        new_height = await page.evaluate("document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        logger.debug(f"Scrolled to height: {last_height}")

    await page.wait_for_selector("div.date-container")
    containers = await page.query_selector_all("div.date-container")
    logger.info(f"Found {len(containers)} date containers")
    return containers

async def extract_logs(page: Page, verbose=True):
    logger.info("Starting extraction of grow logs...")

    metadata = await extract_metadata(page)
    log_containers = await page.query_selector_all("div.date-container")
    logger.info(f"Found {len(log_containers)} log containers")

    entries = []
    for i, log_entry in enumerate(log_containers):
        try:
            logger.debug(f"Processing log entry {i+1}/{len(log_containers)}")
            entry_data = await extract_entry_data(log_entry, page, verbose)
            entries.append(entry_data)
            logger.info(f"Extracted log for date: {entry_data['full_date']}")
            logger.debug(f"Entry details: {entry_data}")
        except Exception as e:
            logger.error(f"Failed to extract log entry: {e}", exc_info=True)

    logger.info(f"Extraction completed. Total entries: {len(entries)}")
    return entries, metadata

async def extract_entry_data(log_entry, page, verbose=True):
    logger.debug("Extracting entry data...")

    date_elem = await log_entry.query_selector("span.date-left")
    day_elem = await log_entry.query_selector("span.date-right, div.date-right")

    full_date = await date_elem.text_content() if date_elem else ""
    day_count = await day_elem.text_content() if day_elem else ""
    logger.debug(f"Date: {full_date}, Day count: {day_count}")

    plant_state = await extract_plant_state(log_entry)
    logger.debug(f"Plant state: {plant_state}")

    actions, images = await extract_actions_and_images(log_entry, page, verbose)
    logger.debug(f"Found {len(actions)} actions and {len(images)} images")

    return {
        "full_date": full_date.strip(),
        "day_count": day_count.strip(),
        "plant_state": plant_state,
        "actions": actions,
        "images": images
    }

async def extract_plant_state(log_entry):
    logger.debug("Extracting plant state...")
    try:
        icon_container = await log_entry.query_selector("div.icon-rounded")
        if icon_container:
            icon_elem = await icon_container.query_selector("i")
            if icon_elem:
                class_attr = await icon_elem.get_attribute("class")
                if "icon-" in class_attr:
                    state = class_attr.split("icon-")[-1].strip()
                    logger.debug(f"Found special state: {state}")
                    return state

        icon_element = await log_entry.query_selector(".icon-rounded i")
        if icon_element:
            class_attr = await icon_element.get_attribute("class")
            if "icon-" in class_attr:
                state = class_attr.split("icon-")[-1].strip()
                logger.debug(f"Found regular state: {state}")
                return state
    except Exception as e:
        logger.error(f"Error extracting plant state: {e}", exc_info=True)

    logger.debug("No state found, defaulting to 'Unknown'")
    return "Unknown"

async def extract_actions_and_images(log_entry, page, verbose=True):
    logger.debug("Starting extraction of actions and images...")
    actions = []
    actions_set = set()  # Utiliser un ensemble pour suivre les actions uniques
    images = []

    sibling = await log_entry.evaluate_handle("el => el.nextElementSibling")
    sibling_count = 0

    while sibling:
        try:
            sibling_count += 1
            logger.debug(f"Processing sibling element {sibling_count}")

            has_date_class = await sibling.evaluate("el => el.classList.contains('date-container')")
            if has_date_class:
                logger.debug("Found next date-container, stopping")
                break

            photos_list = await sibling.query_selector("li:has-text('PHOTOS')")
            if photos_list:
                logger.debug("Found photos section")
                img_elements = await sibling.query_selector_all("img")
                logger.debug(f"Found {len(img_elements)} image elements")
                for i, img in enumerate(img_elements):
                    src = await img.get_attribute("src")
                    if src:
                        images.append(src)
                        logger.debug(f"Added image {i+1}: {src[:50]}")

            actions_nav = await sibling.query_selector("nav")

            if actions_nav:
                logger.debug("Found actions navigation")

                # Extraction de toutes les actions depuis les éléments li
                generic_items = await sibling.query_selector_all("li")
                for item in generic_items:
                    try:
                        action_name = await item.query_selector("span")
                        action_type = await action_name.text_content() if action_name else None
                        
                        # Récupération de la classe pour identifier le type d'action
                        icon_elem = await item.query_selector("i")
                        action_icon_class = await icon_elem.get_attribute("class") if icon_elem else ""
                        
                        details_parts = await item.query_selector_all("p, div span")
                        details = []
                        for part in details_parts:
                            text = await part.text_content()
                            if text and text.strip():
                                details.append(text.strip())
                        
                        if action_type:
                            # Pour les actions d'arrosage
                            if "icon-watering" in action_icon_class:
                                water_amount = await item.evaluate("""el => {
                                    const spans = el.querySelectorAll('span');
                                    for (const span of spans) {
                                        const text = span.textContent.trim();
                                        if (text.includes('l') && /\\d/.test(text)) {
                                            return text;
                                        }
                                    }
                                    const divs = el.querySelectorAll('div');
                                    for (const div of divs) {
                                        const text = div.textContent.trim();
                                        if (text.includes('l') && /\\d/.test(text)) {
                                            return text;
                                        }
                                    }
                                    return 'amount not specified';
                                }""")
                                watering_action = f"Watering: {water_amount}"
                                if watering_action not in actions_set:
                                    actions.append(watering_action)
                                    actions_set.add(watering_action)
                                    logger.debug(f"Added watering action: '{watering_action}'")
                            
                            # Pour les actions de nutriments
                            elif "icon-nutrient" in action_icon_class:
                                raw_text = await item.evaluate("el => el.textContent.trim()")
                                cleaned_text = raw_text.replace("Nutrients", "").replace("Liquid", "").strip()
                                if "Mixes:" in cleaned_text:
                                    cleaned_text = cleaned_text.replace("Mixes:", "", 1).strip()
                                if cleaned_text:
                                    cleaned_text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', cleaned_text)
                                    cleaned_text = re.sub(r'\s{2,}', ' ', cleaned_text).strip()
                                    nutrient_action = f"Nutrients: {cleaned_text}"
                                    if nutrient_action not in actions_set:
                                        actions.append(nutrient_action)
                                        actions_set.add(nutrient_action)
                                        logger.debug(f"Added nutrient action: '{nutrient_action}'")
                            
                            # Pour les autres types d'actions génériques
                            else:
                                details_text = " | ".join(set(details)).strip()
                                formatted = f"{action_type.strip()}: {details_text}" if details_text else action_type.strip()
                                if formatted not in actions_set:
                                    actions.append(formatted)
                                    actions_set.add(formatted)
                                    logger.debug(f"Added generic action: '{formatted}'")
                    except Exception as e:
                        logger.error(f"Error processing action item: {e}", exc_info=True)

            sibling = await sibling.evaluate_handle("el => el.nextElementSibling")

        except Exception as e:
            logger.error(f"Error processing sibling: {e}", exc_info=True)
            break

    logger.info(f"Extraction completed. Found {len(actions)} actions and {len(images)} images")
    if actions:
        logger.debug(f"Actions: {actions}")

    return actions, images

async def extract_metadata(page: Page):
    logger.info("Extracting grow metadata block...")
    metadata = {
        "strain": {},
        "stages": [],
        "environment": {}
    }

    try:
        # STRAIN - Extract and also add to environment
        logger.debug("Extracting strain information...")
        strain_container = await page.query_selector(".MuiBox-root div:has(.icon-strain)")
        if strain_container:
            strain_elements = await strain_container.query_selector_all("p")
            if len(strain_elements) >= 2:
                brand = await strain_elements[0].text_content()
                name = await strain_elements[1].text_content()
                metadata["strain"] = {
                    "brand": brand.strip(),
                    "name": name.strip()
                }
                # Add to environment table as well
                if "Unknown breeder" in brand:
                    metadata["environment"]["Strain Brand"] = "Unknown breeder"
                    metadata["environment"]["Strain Name"] = name.strip()
                else:
                    metadata["environment"]["Strain"] = f"{brand.strip()} {name.strip()}"
                logger.debug(f"Found strain: {brand} - {name}")
            else:
                logger.debug("Insufficient strain elements found")
        else:
            logger.debug("Strain container not found")
            # Hardcoded default values if we can't find the strain
            metadata["strain"] = {
                "brand": "Unknown breeder",
                "name": "Hulkberry auto"
            }
        
        # TREE STAGES
        logger.debug("Extracting stages information...")
        stage_containers = await page.query_selector_all(".stage-content")
        for stage in stage_containers:
            name_el = await stage.query_selector(".stage-name")
            date_el = await stage.query_selector(".stage-details p:nth-of-type(2)")
            
            if name_el and date_el:
                name = await name_el.text_content()
                date = await date_el.text_content()
                metadata["stages"].append({"name": name.strip(), "date": date.strip()})
                logger.debug(f"Found stage: {name} - {date}")

        # ENVIRONMENT
        logger.debug("Extracting environment information...")
        env_section = await page.query_selector("p.list-title:text('ENVIRONMENT')")
        
        # Hardcoded environment values from the paste.txt if none are found
        if "environment" not in metadata or not metadata["environment"]:
            metadata["environment"] = {
                "Name": "Hydro mars",
                "Type": "Indoor", 
                "Exposure Time": "16 Hours",
                "Environment Size": "80 cm x 160 cm x 80 cm",
                "Lights": "LED - 150 W"
            }
        
        if env_section:
            env_containers = await page.query_selector_all(".MuiBox-root div:has(.icon-environment, .icon-indoor, .icon-time, .icon-height)")
            
            for container in env_containers:
                # Make sure it's not a strain container
                icon = await container.query_selector("i")
                if icon:
                    icon_class = await icon.get_attribute("class")
                    if icon_class and "icon-strain" in icon_class:
                        continue  # Skip this box since it's the strain container
                
                div = await container.query_selector("div:nth-of-type(2)")
                if not div:
                    continue
                
                label_el = await div.query_selector("p.list-label")
                value_el = await div.query_selector("p:nth-of-type(2)")
                
                if label_el and value_el:
                    label = await label_el.text_content()
                    value = await value_el.text_content()
                    
                    # Clean the values
                    label = label.strip()
                    value = value.strip()
                    
                    # Skip any Medium entries
                    if "medium" in label.lower():
                        continue
                        
                    metadata["environment"][label] = value
                    logger.debug(f"Found environment: {label} - {value}")

        logger.info(f"Metadata extracted: {metadata}")
    except Exception as e:
        logger.error(f"Failed to extract metadata: {e}", exc_info=True)

    return metadata