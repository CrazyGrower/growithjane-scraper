"""GrowWithJane scraper module (version mise à jour)."""
from playwright.async_api import Page
import re
import logging
import json

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('scraper')

def clean_plant_state(state_text):
    """Remove any CSS class names from the plant state."""
    if not state_text:
        return "Unknown"
    
    # Remove any CSS class references (like text-2xl)
    cleaned_state = re.sub(r'\btext-[a-z0-9]+\b', '', state_text)
    return cleaned_state.strip()

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

    # Attendre que les éléments de la timeline se chargent
    await page.wait_for_selector("div[data-testid='growlog-page-timeline-card']")
    timeline_cards = await page.query_selector_all("div[data-testid='growlog-page-timeline-card']")
    logger.info(f"Found {len(timeline_cards)} timeline cards")
    return timeline_cards

async def extract_logs(page: Page, verbose=True):
    logger.info("Starting extraction of grow logs...")

    metadata = await extract_metadata(page)
    
    # Extraire tous les changements de stade d'abord
    stage_changes = await page.query_selector_all("div[data-testid='growlog-page-timeline-stage-change']")
    stage_change_entries = []
    stage_change_dates = []
    
    for i, stage_change in enumerate(stage_changes):
        try:
            logger.debug(f"Processing stage change {i+1}/{len(stage_changes)}")
            entry_data = await extract_stage_change(stage_change, page, verbose)
            if entry_data:
                stage_change_entries.append(entry_data)
                stage_change_dates.append(entry_data['full_date'])
                logger.info(f"Extracted stage change for date: {entry_data['full_date']}")
                logger.debug(f"Stage change details: {entry_data}")
        except Exception as e:
            logger.error(f"Failed to extract stage change: {e}", exc_info=True)
    
    # Extraire les entrées de journal normales
    timeline_cards = await page.query_selector_all("div[data-testid='growlog-page-timeline-card']")
    logger.info(f"Found {len(timeline_cards)} timeline cards")

    entries = []
    current_stage = None
    
    for i, card in enumerate(timeline_cards):
        try:
            logger.debug(f"Processing timeline card {i+1}/{len(timeline_cards)}")
            entry_data = await extract_entry_data(card, page, verbose)
            
            # Ne pas ajouter l'état de la plante à chaque entrée
            # sauf si c'est un changement de stade
            if entry_data['full_date'] not in stage_change_dates:
                entry_data.pop('plant_state', None)
                
            entries.append(entry_data)
            logger.info(f"Extracted log for date: {entry_data['full_date']}")
            logger.debug(f"Entry details: {entry_data}")
        except Exception as e:
            logger.error(f"Failed to extract log entry: {e}", exc_info=True)

    # Fusionner les entrées régulières et les changements de stade
    all_entries = stage_change_entries + entries
    
    # Trier par date (du plus récent au plus ancien)
    all_entries.sort(key=lambda x: x['full_date'], reverse=True)
    
    logger.info(f"Extraction completed. Total entries: {len(all_entries)}")
    return all_entries, metadata

async def extract_entry_data(card, page, verbose=True):
    logger.debug("Extracting entry data from timeline card...")

    # Récupérer la date et le nombre de jours
    date_section = await card.query_selector("div[data-testid='growlog-page-timeline-card-date']")
    date_element = await date_section.query_selector("div:has(svg)")
    date_text = await date_element.evaluate("el => el.textContent") if date_element else ""
    
    day_count_element = await date_section.query_selector("span")
    day_count = await day_count_element.evaluate("el => el.textContent") if day_count_element else ""
    
    logger.debug(f"Date: {date_text}, Day count: {day_count}")

    # Déterminer l'état de la plante (à partir des infos générales, pas directement dans la timeline)
    plant_state = await extract_plant_state(page)
    logger.debug(f"Plant state: {plant_state}")

    # Extraire les actions (reminders) et les images
    actions = await extract_actions(card, verbose)
    images = await extract_images(card, verbose)
    tree_logs = await extract_tree_logs(card, verbose)
    logger.debug(f"Found {len(actions)} actions")

    return {
        "full_date": date_text.strip(),
        "day_count": day_count.strip(),
        "plant_state": plant_state,
        "actions": actions,
        "images": images,
        "tree_logs": tree_logs
    }

async def extract_stage_change(stage_change, page, verbose=True):
    logger.debug("Extracting stage change data...")
    try:
        # Récupérer la date et le nombre de jours
        date_section = await stage_change.query_selector("div[data-testid='growlog-page-timeline-stage-change-date']")
        date_element = await date_section.query_selector("div:has(svg)")
        date_text = await date_element.evaluate("el => el.textContent") if date_element else ""
        day_count_element = await date_section.query_selector("span")
        day_count = await day_count_element.evaluate("el => el.textContent") if day_count_element else ""
        logger.info(f"Stage change date: '{date_text}', day_count: '{day_count}'")
        # Extraire l'étape de croissance
        stage_section = await stage_change.query_selector("div[data-testid='growlog-page-timeline-stage-change-stage']")
        stage_text_element = await stage_section.query_selector("div > div > span")
        stage_text = await stage_text_element.evaluate("el => el.textContent") if stage_text_element else ""
        logger.info(f"Stage change text: '{stage_text}'")
        # Récupérer l'icône pour déterminer le state
        icon_element = await stage_section.query_selector("i")
        if icon_element:
            icon_class = await icon_element.get_attribute("class")
            logger.info(f"Stage change icon class: '{icon_class}'")
            plant_state = clean_plant_state(icon_class.replace("icon-", "")) if "icon-" in icon_class else "Unknown"
        else:
            plant_state = "Unknown"
        logger.info(f"Stage change plant_state: '{plant_state}'")
        result = {
            "full_date": date_text.strip(),
            "day_count": day_count.strip(),
            "plant_state": plant_state,
            "stage_change": stage_text.strip(),
            "actions": [],
            "images": [],
            "tree_logs": {}
        }
        logger.info(f"Extracted stage change entry: {result}")
        return result
    except Exception as e:
        logger.error(f"Error extracting stage change: {e}", exc_info=True)
        return None

async def extract_plant_state(page):
    logger.debug("Extracting plant state...")
    try:
        # Dans la nouvelle interface, l'état courant de la plante est affiché dans la colonne de gauche
        stage_element = await page.query_selector("div[data-testid='growlog-page-details-stage'] span.capitalize")
        if stage_element:
            stage_name = await stage_element.text_content()
            logger.debug(f"Found current stage: {stage_name}")
            return clean_plant_state(stage_name.strip().lower())
            
        # Essayer une autre méthode si la première échoue
        tree_stages = await page.query_selector("div[data-testid='growlog-page-tree-stages']")
        if tree_stages:
            active_stage = await tree_stages.query_selector("span[data-testid='growlog-page-tree-stages-item-name-value'].text-primary")
            if active_stage:
                stage_name = await active_stage.text_content()
                logger.debug(f"Found active stage from tree stages: {stage_name}")
                return clean_plant_state(stage_name.strip().lower())
    except Exception as e:
        logger.error(f"Error extracting plant state: {e}", exc_info=True)

    logger.debug("No state found, defaulting to 'Unknown'")
    return "Unknown"

async def extract_actions(card, verbose=True):
    logger.debug("Extracting actions from timeline card...")
    actions = []
    
    try:
        # Vérifier s'il y a une section "Actions"
        reminders_section = await card.query_selector("div[data-testid='growlog-page-timeline-reminders']")
        if not reminders_section:
            logger.debug("No actions section found in this card")
            return actions
            
        # Trouver tous les éléments d'action
        reminder_items = await reminders_section.query_selector_all("div[data-testid='growlog-page-timeline-reminder-item']")
        logger.debug(f"Found {len(reminder_items)} reminder items")
        
        for item in reminder_items:
            try:
                # Extraire le nom de l'action
                name_element = await item.query_selector("span[data-testid='growlog-page-timeline-reminder-item-name']")
                action_name = await name_element.text_content() if name_element else ""
                
                # Extraire la valeur des données supplémentaires
                amount_element = await item.query_selector("span[data-testid='growlog-page-timeline-reminder-extra-data-amount-value']")
                amount_text = await amount_element.text_content() if amount_element else ""
                
                # Combiner le nom et la valeur
                if action_name and amount_text:
                    actions.append(f"{action_name.strip()}: {amount_text.strip()}")
                    logger.debug(f"Added action with value: '{action_name.strip()}: {amount_text.strip()}'")
                elif action_name:
                    actions.append(action_name.strip())
                    logger.debug(f"Added action: '{action_name.strip()}'")
                        
            except Exception as e:
                logger.error(f"Error processing action item: {e}", exc_info=True)
                
    except Exception as e:
        logger.error(f"Error extracting actions: {e}", exc_info=True)
    
    return actions

async def extract_images(card, verbose=True):
    logger.debug("Extracting images from timeline card...")
    images = []
    try:
        photos_section = await card.query_selector("div[data-testid='growlog-page-timeline-photos']")
        if not photos_section:
            logger.debug("No photos section found in this card")
            return images
        photo_items = await photos_section.query_selector_all("div[data-testid='growlog-page-timeline-photos-item']")
        for item in photo_items:
            try:
                img_element = await item.query_selector("img")
                if img_element:
                    src = await img_element.get_attribute("src")
                    if src:
                        src = src.replace("_thumb@480_", "_")
                        images.append(src)
            except Exception as e:
                logger.error(f"Error processing image item: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Error extracting images: {e}", exc_info=True)
    return images

async def extract_tree_logs(card, verbose=True):
    logger.debug("Extracting tree logs from timeline card...")
    tree_logs = {}
    try:
        tree_log_section = await card.query_selector("div[data-testid='growlog-page-timeline-tree-log']")
        if not tree_log_section:
            logger.debug("No tree log section found in this card")
            return tree_logs
        else:
            logger.info("Tree log section found!")

        log_items = await tree_log_section.query_selector_all("div[data-testid='growlog-page-timeline-log-item']")
        logger.info(f"Found {len(log_items)} tree log items")
        for item in log_items:
            label_el = await item.query_selector("div[data-testid='growlog-page-timeline-log-item-label']")
            value_el = await item.query_selector("div[data-testid='growlog-page-timeline-log-item-value']")
            label = await label_el.text_content() if label_el else ""
            value = await value_el.text_content() if value_el else ""
            logger.info(f"Tree log item: label='{label}', value='{value}'")
            if label and value:
                tree_logs[label.strip()] = value.strip()
    except Exception as e:
        logger.error(f"Error extracting tree logs: {e}", exc_info=True)
    logger.info(f"Extracted tree_logs: {tree_logs}")
    return tree_logs

async def extract_metadata(page: Page):
    logger.info("Extracting grow metadata block...")
    metadata = {
        "strain": {},
        "stages": [],
        "environment": {}
    }

    try:
        # STRAIN - Extraire les informations sur la souche
        logger.debug("Extracting strain information...")
        strain_container = await page.query_selector("div[data-testid='growlog-page-strain-breeder']")
        if strain_container:
            strain_name_element = await strain_container.query_selector("span[data-testid='growlog-page-strain-breeder-strain-name']")
            strain_name = await strain_name_element.text_content() if strain_name_element else ""
            
            strain_value_element = await strain_container.query_selector("span.text-lg.font-bold")
            strain_value = await strain_value_element.text_content() if strain_value_element else ""
            
            metadata["strain"] = {
                "brand": "Unknown breeder",  # Valeur par défaut
                "name": strain_value.strip()
            }
            
            # Ajouter à l'environnement aussi
            metadata["environment"]["Strain"] = strain_value.strip()
            logger.debug(f"Found strain: {strain_value}")
        else:
            logger.debug("Strain container not found")
            # Valeurs par défaut si on ne trouve pas la souche
            metadata["strain"] = {
                "brand": "Unknown breeder",
                "name": "Unknown strain"
            }
        
        # TREE STAGES - Extraire les étapes de croissance
        logger.debug("Extracting stages information...")
        stage_container = await page.query_selector("div[data-testid='growlog-page-tree-stages']")
        if stage_container:
            stage_items = await stage_container.query_selector_all("div[data-testid='growlog-page-tree-stages-item']")
            for stage in stage_items:
                name_el = await stage.query_selector("span[data-testid='growlog-page-tree-stages-item-name-value']")
                date_el = await stage.query_selector("div[data-testid='growlog-page-tree-stages-item-name-date'] span")
                
                if name_el and date_el:
                    name = await name_el.text_content()
                    date = await date_el.text_content()
                    metadata["stages"].append({"name": name.strip(), "date": date.strip()})
                    logger.debug(f"Found stage: {name} - {date}")

        # ENVIRONMENT - Extraire les informations sur l'environnement
        logger.debug("Extracting environment information...")
        env_section = await page.query_selector("div[data-testid='growlog-page-environment-details']")
        
        if env_section:
            # Extraire le nom
            name_item = await env_section.query_selector("div[data-testid='growlog-page-environment-details-name']")
            if name_item:
                name_value = await name_item.query_selector("span[data-testid='growlog-page-environment-details-name']")
                if name_value:
                    env_name = await name_value.text_content()
                    metadata["environment"]["Name"] = env_name.strip()
            
            # Extraire le type (Indoor/Outdoor)
            type_item = await env_section.query_selector("div[data-testid='growlog-page-environment-details-type']")
            if type_item:
                type_value = await type_item.query_selector("span.text-lg")
                if type_value:
                    env_type = await type_value.text_content()
                    metadata["environment"]["Type"] = env_type.strip()
            
            # Extraire le temps d'exposition
            exposure_item = await env_section.query_selector("div[data-testid='growlog-page-environment-details-exposure-time']")
            if exposure_item:
                exposure_value = await exposure_item.query_selector("span.text-lg")
                if exposure_value:
                    exposure = await exposure_value.text_content()
                    metadata["environment"]["Exposure Time"] = exposure.strip()
            
            # Extraire la taille de l'environnement
            size_item = await env_section.query_selector("div[data-testid='growlog-page-environment-details-indoor-size']")
            if size_item:
                size_value = await size_item.query_selector("span.text-lg")
                if size_value:
                    size = await size_value.text_content()
                    metadata["environment"]["Environment Size"] = size.strip()
            
            # Extraire les informations sur les lumières
            lights_item = await env_section.query_selector("div[data-testid='growlog-page-environment-details-lights']")
            if lights_item:
                lights_value = await lights_item.query_selector("span[data-testid='growlog-page-environment-details-lights-value']")
                if lights_value:
                    light_items = await lights_value.query_selector_all("p")
                    lights = []
                    for light in light_items:
                        light_text = await light.text_content()
                        lights.append(light_text.strip())
                    
                    metadata["environment"]["Lights"] = " | ".join(lights)
        
        # Si aucune information d'environnement n'a été trouvée, utiliser des valeurs par défaut
        if not metadata["environment"]:
            metadata["environment"] = {
                "Name": "Hydro mars",
                "Type": "Indoor", 
                "Exposure Time": "16 Hours",
                "Environment Size": "80 cm x 160 cm x 80 cm",
                "Lights": "LED - 150 W"
            }

        logger.info(f"Metadata extracted: {metadata}")
    except Exception as e:
        logger.error(f"Failed to extract metadata: {e}", exc_info=True)

    return metadata