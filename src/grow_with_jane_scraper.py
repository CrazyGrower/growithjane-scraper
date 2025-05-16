import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os
from typing import Dict, List, Optional
import logging
from playwright.async_api import async_playwright
import time
import asyncio
import aiohttp
import aiofiles
from urllib.parse import urlparse

class GrowWithJaneScraper:
    def __init__(self, verbose: bool = False):
        self.base_url = "https://growithjane.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.verbose = verbose
        self.logger = logging.getLogger('grow_with_jane_scraper')
        if verbose:
            self.logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Créer les dossiers pour les photos avec le chemin absolu
        self.photos_dir = os.path.join('/app', 'output', 'photos')
        os.makedirs(self.photos_dir, exist_ok=True)

    async def _download_photo(self, url: str, session: aiohttp.ClientSession) -> Optional[str]:
        """Télécharge une photo et retourne son chemin local"""
        try:
            # Générer un nom de fichier simple basé sur un timestamp
            timestamp = int(time.time() * 1000)
            filename = f"photo_{timestamp}.jpg"
            
            # Utiliser le chemin absolu pour le fichier local
            local_path = os.path.join(self.photos_dir, filename)
            
            # Vérifier si la photo existe déjà
            if os.path.exists(local_path):
                if self.verbose:
                    self.logger.info(f"Photo already exists: {filename}")
                return local_path
            
            # Télécharger la photo
            async with session.get(url) as response:
                if response.status == 200:
                    async with aiofiles.open(local_path, 'wb') as f:
                        await f.write(await response.read())
                    if self.verbose:
                        self.logger.info(f"Downloaded photo: {filename}")
                    return local_path
                else:
                    if self.verbose:
                        self.logger.error(f"Failed to download photo: {url} (Status: {response.status})")
                    return None
        except Exception as e:
            if self.verbose:
                self.logger.error(f"Error downloading photo {url}: {str(e)}")
            return None

    async def _download_photos(self, urls: List[str]) -> List[Dict[str, str]]:
        """Télécharge une liste de photos et retourne leurs chemins locaux"""
        downloaded_photos = []
        async with aiohttp.ClientSession() as session:
            for url in urls:
                local_path = await self._download_photo(url, session)
                if local_path:
                    downloaded_photos.append({
                        "url": url,
                        "local_path": local_path
                    })
        return downloaded_photos

    async def get_growlog_data(self, growlog_url: str) -> Dict:
        """
        Récupère les données d'un growlog spécifique
        """
        try:
            if self.verbose:
                self.logger.info(f"\n=== STARTING SCRAPING: {growlog_url} ===")

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                if self.verbose:
                    self.logger.info("Loading page...")
                await page.goto(growlog_url)
                await page.wait_for_load_state('networkidle')

                if self.verbose:
                    self.logger.info("Scrolling to load all content...")
                
                last_height = await page.evaluate('document.body.scrollHeight')
                scroll_count = 0
                while True:
                    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await asyncio.sleep(2)
                    
                    new_height = await page.evaluate('document.body.scrollHeight')
                    if new_height == last_height:
                        break
                    last_height = new_height
                    scroll_count += 1
                    
                    if self.verbose and scroll_count % 5 == 0:
                        self.logger.info(f"Scrolled {scroll_count} times...")

                if self.verbose:
                    self.logger.info("Content loaded, starting extraction...")
                
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')

                # --- Extraction de l'environnement, du medium et du strain ---
                environment = self._extract_environment(soup)
                medium = self._extract_medium(soup)
                if medium:
                    environment["Medium"] = medium
                strain = self._extract_strain(soup)

                growlog_data = {
                    "url": growlog_url,
                    "title": self._extract_title(soup),
                    "strain": strain,
                    "growing_stage": self._extract_growing_stage(soup),
                    "timeline": [],
                    "environment": environment,
                    "stages": self._extract_stages(soup)
                }

                # --- Extraction des changements de stage ---
                stage_changes = []
                sc_blocks = soup.find_all('div', attrs={'data-testid': 'growlog-page-timeline-stage-change'})
                for sc in sc_blocks:
                    date = self._extract_stage_change_date(sc)
                    day_count = self._extract_stage_change_day_count(sc)
                    stage_change_text = self._extract_stage_change_text(sc)
                    plant_state = self._extract_stage_change_state(sc)
                    if self.verbose:
                        self.logger.info(f"Stage change found: date='{date}', day_count='{day_count}', text='{stage_change_text}', state='{plant_state}'")
                    stage_changes.append({
                        "date": date,
                        "day_count": day_count,
                        "stage_change": stage_change_text,
                        "plant_state": plant_state
                    })

                # --- Extraction des cartes classiques de timeline ---
                timeline_elements = soup.find_all('div', attrs={'data-testid': 'growlog-page-timeline-card'})
                for element in timeline_elements:
                    date = self._extract_date(element)
                    actions = self._extract_actions(element)
                    photo_urls = self._extract_event_photos(element)
                    downloaded_photos = await self._download_photos(photo_urls)
                    tree_logs = self._extract_tree_logs(element)
                    if self.verbose:
                        self.logger.info(f"Timeline card: date='{date}', actions={actions}, tree_logs={tree_logs}")
                    event = {
                        "date": date,
                        "actions": actions,
                        "photos": downloaded_photos,
                        "tree_logs": tree_logs,
                        "plant_state": None
                    }
                    growlog_data["timeline"].append(event)

                growlog_data["stage_changes"] = stage_changes
                
                # Télécharger les photos principales
                main_photo_urls = self._extract_photos(soup)
                growlog_data["photos"] = await self._download_photos(main_photo_urls)
                
                if self.verbose:
                    self.logger.info("\n=== EXTRACTION SUMMARY ===")
                    self.logger.info(f"Title: {growlog_data['title']}")
                    self.logger.info(f"Strain: {growlog_data['strain']}")
                    self.logger.info(f"Growing Stage: {growlog_data['growing_stage']}")
                    self.logger.info(f"Timeline Entries: {len(growlog_data['timeline'])}")
                    self.logger.info(f"Total Photos: {len(growlog_data['photos'])}")
                    self.logger.info(f"Environment Parameters: {len(growlog_data['environment'])}")
                    self.logger.info(f"Stages: {growlog_data['stages']}")
                
                await browser.close()
                return growlog_data
                
        except Exception as e:
            if self.verbose:
                self.logger.error(f"Error during scraping: {str(e)}")
            return {}

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extrait le titre du growlog"""
        try:
            if self.verbose:
                self.logger.info("Searching for title element...")
                self.logger.info(f"Page title: {soup.title.string if soup.title else 'No title found'}")
            
            title_elem = soup.find('h1', class_='text-2xl')
            if title_elem:
                if self.verbose:
                    self.logger.info(f"Found title element: {title_elem}")
                title = title_elem.text.strip()
                if self.verbose:
                    self.logger.info(f"Extracted title: {title}")
                return title
            elif self.verbose:
                self.logger.warning("No title element found with class 'text-2xl'")
                # Chercher tous les h1 pour debug
                all_h1 = soup.find_all('h1')
                self.logger.info(f"All h1 elements found: {[h1.text.strip() for h1 in all_h1]}")
        except Exception as e:
            if self.verbose:
                self.logger.error(f"Error extracting title: {str(e)}")
        return ""

    def _extract_strain(self, soup: BeautifulSoup) -> str:
        try:
            strain_section = soup.find('div', attrs={'data-testid': 'growlog-page-strain-breeder'})
            if strain_section:
                strain_name_el = strain_section.find('span', attrs={'data-testid': 'growlog-page-strain-breeder-strain-name'})
                if strain_name_el:
                    # Cherche le nom juste après le label "Strain"
                    value_el = strain_section.find('span', class_='text-lg font-bold')
                    if value_el:
                        return value_el.text.strip()
        except Exception as e:
            if self.verbose:
                self.logger.error(f"Error extracting strain: {str(e)}")
        return "Unknown"

    def _extract_growing_stage(self, soup: BeautifulSoup) -> str:
        """Extrait le stade de croissance actuel"""
        try:
            stage_elem = soup.find('div', string='Tree Stages')
            if stage_elem:
                stage_div = stage_elem.find_next('div')
                if stage_div:
                    stage = stage_div.text.strip()
                    if self.verbose:
                        self.logger.info(f"Extracted growing stage: {stage}")
                    return stage
        except Exception as e:
            if self.verbose:
                self.logger.error(f"Error extracting growing stage: {str(e)}")
        return ""

    def _extract_timeline(self, soup: BeautifulSoup) -> List[Dict]:
        """Extrait la timeline des événements"""
        timeline = []
        try:
            if self.verbose:
                self.logger.info("\n=== TIMELINE EXTRACTION ===")
            
            timeline_elements = soup.find_all('div', attrs={'data-testid': 'growlog-page-timeline-card'})
            
            if self.verbose:
                self.logger.info(f"Found {len(timeline_elements)} timeline entries")
            
            for i, element in enumerate(timeline_elements, 1):
                try:
                    date = self._extract_date(element)
                    actions = self._extract_actions(element)
                    photos = self._extract_event_photos(element)
                    
                    event = {
                        "date": date,
                        "actions": actions,
                        "photos": photos
                    }
                    
                    if self.verbose:
                        self.logger.info(f"\nEntry {i}:")
                        self.logger.info(f"  Date: {date}")
                        if actions:
                            self.logger.info(f"  Actions: {', '.join(actions)}")
                        if photos:
                            self.logger.info(f"  Photos: {len(photos)} found")
                    
                    timeline.append(event)
                except Exception as e:
                    if self.verbose:
                        self.logger.error(f"Error processing entry {i}: {str(e)}")
                    continue
                
            return timeline
        except Exception as e:
            if self.verbose:
                self.logger.error(f"Error extracting timeline: {str(e)}")
            return []

    def _extract_date(self, element: BeautifulSoup) -> str:
        """Extrait la date d'un événement"""
        try:
            date_elem = element.find('div', attrs={'data-testid': 'growlog-page-timeline-card-date'})
            if date_elem:
                date_div = date_elem.find('div', class_='')
                if date_div:
                    return date_div.text.strip()
        except Exception as e:
            if self.verbose:
                self.logger.error(f"Error extracting date: {str(e)}")
        return ""

    def _extract_actions(self, element: BeautifulSoup) -> List[str]:
        """Extrait les actions effectuées"""
        actions = []
        try:
            reminders_section = element.find('div', attrs={'data-testid': 'growlog-page-timeline-reminders'})
            if reminders_section:
                reminder_items = reminders_section.find_all('div', attrs={'data-testid': 'growlog-page-timeline-reminder-item'})
                
                for item in reminder_items:
                    try:
                        action_name = item.find('span', attrs={'data-testid': 'growlog-page-timeline-reminder-item-name'})
                        action_value = item.find('span', attrs={'data-testid': 'growlog-page-timeline-reminder-extra-data-amount-value'})
                        
                        if action_name and action_value:
                            action = f"{action_name.text.strip()}: {action_value.text.strip()}"
                            actions.append(action)
                    except Exception as e:
                        if self.verbose:
                            self.logger.error(f"Error processing action: {str(e)}")
                        continue
        except Exception as e:
            if self.verbose:
                self.logger.error(f"Error extracting actions: {str(e)}")
        return actions

    def _extract_photos(self, soup: BeautifulSoup) -> List[str]:
        """Extrait les URLs des photos"""
        photos = []
        photo_elements = soup.find_all('img', class_='growlog-photo')
        for photo in photo_elements:
            if photo.get('src'):
                photos.append(photo['src'])
        if self.verbose:
            self.logger.info(f"Extracted {len(photos)} photos")
        return photos

    def _extract_event_photos(self, element: BeautifulSoup) -> List[str]:
        """Extrait les URLs des photos d'un événement spécifique"""
        photos = []
        try:
            photos_section = element.find('div', attrs={'data-testid': 'growlog-page-timeline-photos'})
            if photos_section:
                photo_items = photos_section.find_all('img', class_='h-[260px]')
                for photo in photo_items:
                    if photo.get('src'):
                        photos.append(photo['src'])
        except Exception as e:
            if self.verbose:
                self.logger.error(f"Error extracting photos: {str(e)}")
        return photos

    def _extract_environment(self, soup: BeautifulSoup) -> dict:
        environment = {}
        try:
            env_section = soup.find('div', attrs={'data-testid': 'growlog-page-environment-details'})
            if env_section:
                # Name
                name_item = env_section.find('div', attrs={'data-testid': 'growlog-page-environment-details-name'})
                if name_item:
                    name_value = name_item.find('span', attrs={'data-testid': 'growlog-page-environment-details-name'})
                    if name_value:
                        environment["Name"] = name_value.text.strip()
                # Type
                type_item = env_section.find('div', attrs={'data-testid': 'growlog-page-environment-details-type'})
                if type_item:
                    type_value = type_item.find('span', class_='text-lg')
                    if type_value:
                        environment["Type"] = type_value.text.strip()
                # Exposure Time
                exposure_item = env_section.find('div', attrs={'data-testid': 'growlog-page-environment-details-exposure-time'})
                if exposure_item:
                    exposure_value = exposure_item.find('span', class_='text-lg')
                    if exposure_value:
                        environment["Exposure Time"] = exposure_value.text.strip()
                # Environment Size
                size_item = env_section.find('div', attrs={'data-testid': 'growlog-page-environment-details-indoor-size'})
                if size_item:
                    size_value = size_item.find('span', class_='text-lg')
                    if size_value:
                        environment["Environment Size"] = size_value.text.strip()
                # Lights
                lights_item = env_section.find('div', attrs={'data-testid': 'growlog-page-environment-details-lights'})
                if lights_item:
                    lights_value = lights_item.find('p', attrs={'data-testid': 'growlog-page-environment-details-lights-item'})
                    if lights_value:
                        environment["Lights"] = lights_value.text.strip()
        except Exception as e:
            if self.verbose:
                self.logger.error(f"Error extracting environment: {str(e)}")
        return environment

    def _extract_tree_logs(self, element: BeautifulSoup) -> dict:
        """Extrait les Tree Logs d'une carte de timeline"""
        tree_logs = {}
        try:
            tree_log_section = element.find('div', attrs={'data-testid': 'growlog-page-timeline-tree-log'})
            if not tree_log_section:
                if self.verbose:
                    self.logger.info("No tree log section found in this card")
                return tree_logs
            log_items = tree_log_section.find_all('div', attrs={'data-testid': 'growlog-page-timeline-log-item'})
            if self.verbose:
                self.logger.info(f"Found {len(log_items)} tree log items")
            for item in log_items:
                label_el = item.find('div', attrs={'data-testid': 'growlog-page-timeline-log-item-label'})
                value_el = item.find('div', attrs={'data-testid': 'growlog-page-timeline-log-item-value'})
                label = label_el.text.strip() if label_el else ""
                value = value_el.text.strip() if value_el else ""
                if self.verbose:
                    self.logger.info(f"Tree log item: label='{label}', value='{value}'")
                if label and value:
                    tree_logs[label] = value
        except Exception as e:
            if self.verbose:
                self.logger.error(f"Error extracting tree logs: {str(e)}")
        return tree_logs

    def _extract_stage_change_date(self, element: BeautifulSoup) -> str:
        try:
            date_section = element.find('div', attrs={'data-testid': 'growlog-page-timeline-stage-change-date'})
            date_div = date_section.find('div', class_='') if date_section else None
            return date_div.text.strip() if date_div else ""
        except Exception as e:
            if self.verbose:
                self.logger.error(f"Error extracting stage change date: {str(e)}")
            return ""

    def _extract_stage_change_day_count(self, element: BeautifulSoup) -> str:
        try:
            date_section = element.find('div', attrs={'data-testid': 'growlog-page-timeline-stage-change-date'})
            day_count_span = date_section.find('span') if date_section else None
            return day_count_span.text.strip() if day_count_span else ""
        except Exception as e:
            if self.verbose:
                self.logger.error(f"Error extracting stage change day count: {str(e)}")
            return ""

    def _extract_stage_change_text(self, element: BeautifulSoup) -> str:
        try:
            stage_section = element.find('div', attrs={'data-testid': 'growlog-page-timeline-stage-change-stage'})
            if stage_section:
                text_span = stage_section.find('span')
                return text_span.text.strip() if text_span else ""
            return ""
        except Exception as e:
            if self.verbose:
                self.logger.error(f"Error extracting stage change text: {str(e)}")
            return ""

    def _extract_stage_change_state(self, element: BeautifulSoup) -> str:
        try:
            stage_section = element.find('div', attrs={'data-testid': 'growlog-page-timeline-stage-change-stage'})
            if stage_section:
                icon = stage_section.find('i')
                if icon and icon.has_attr('class'):
                    for c in icon['class']:
                        if c.startswith('icon-'):
                            return c.replace('icon-', '')
            return ""
        except Exception as e:
            if self.verbose:
                self.logger.error(f"Error extracting stage change state: {str(e)}")
            return ""

    def _extract_stages(self, soup: BeautifulSoup) -> list:
        stages = []
        try:
            stages_section = soup.find('div', attrs={'data-testid': 'growlog-page-tree-stages'})
            if stages_section:
                stage_items = stages_section.find_all('div', attrs={'data-testid': 'growlog-page-tree-stages-item'})
                for item in stage_items:
                    name_el = item.find('span', attrs={'data-testid': 'growlog-page-tree-stages-item-name-value'})
                    date_el = item.find('div', attrs={'data-testid': 'growlog-page-tree-stages-item-name-date'})
                    name = name_el.text.strip() if name_el else ""
                    date = date_el.find('span').text.strip() if date_el and date_el.find('span') else ""
                    if name:
                        stages.append({"name": name, "date": date})
        except Exception as e:
            if self.verbose:
                self.logger.error(f"Error extracting stages: {str(e)}")
        return stages

    def _extract_medium(self, soup: BeautifulSoup) -> str:
        try:
            medium_section = soup.find('span', attrs={'data-testid': 'growlog-page-medium-nutrients-name-value-name'})
            if medium_section:
                return medium_section.text.strip()
        except Exception as e:
            if self.verbose:
                self.logger.error(f"Error extracting medium: {str(e)}")
        return ""

    def save_to_json(self, data: Dict, filename: str):
        """Sauvegarde les données dans un fichier JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        if self.verbose:
            self.logger.info(f"Data saved to {filename}")

async def main():
    scraper = GrowWithJaneScraper(verbose=True)
    growlog_url = "https://growithjane.com/growlog/mexican-tfovc"
    
    # Créer le dossier output s'il n'existe pas
    os.makedirs('output', exist_ok=True)
    
    # Récupérer et sauvegarder les données
    data = await scraper.get_growlog_data(growlog_url)
    scraper.save_to_json(data, 'output/growlog_data.json')
    print("Données sauvegardées dans output/growlog_data.json")

if __name__ == "__main__":
    asyncio.run(main()) 