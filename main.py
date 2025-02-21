"""
Main script for the GrowLog Scraper.
"""
import argparse
from selenium.webdriver.common.by import By
from src.utils import load_config, log_message
from src.scraper import configure_driver, load_page, extract_logs
from src.pdf_generator import generate_pdf
from src.video_generator import generate_video

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    try:
        # Load configuration
        config = load_config(args.verbose)
        
        # Initialize driver
        driver = configure_driver(config['chromedriver_path'], args.verbose)
        
        # Load and process page
        log_containers = load_page(driver, config['url'], args.verbose)
        
        # Extract title
        title = driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
        log_message(f"Extracted Title: {title}", args.verbose)
        
        # Extract log entries
        entries = extract_logs(driver, args.verbose)
        
        # Close driver
        driver.quit()
        
        # Generate PDF
        pdf_file = generate_pdf(title, entries, verbose=args.verbose)
        
        print(f"PDF generated successfully: {pdf_file}")
        
        video_output = title + ".mp4"
        generate_video(pdf_file, video_output)
        print(f"Vidéo créée avec succès : {video_output}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())