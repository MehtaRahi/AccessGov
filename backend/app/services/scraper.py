import requests
from bs4 import BeautifulSoup
import os
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GovScraper:
    def __init__(self, output_dir: str = "../../data/raw"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def scrape_url(self, url: str, source_name: str):
        """Scrapes the text content of a given URL and saves it to a file."""
        logger.info(f"Scraping {url} for {source_name}...")
        try:
            response = requests.get(url, headers=self.headers, timeout=15, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove scripts, styles, and navigation
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()
                
            text = soup.get_text(separator='\n', strip=True)
            
            # Save the raw text
            output_path = os.path.join(self.output_dir, f"{source_name}.txt")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"Source URL: {url}\n")
                f.write("="*50 + "\n\n")
                f.write(text)
                
            logger.info(f"Successfully saved content to {output_path}")
            return text
            
        except requests.RequestException as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return None

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    scraper = GovScraper()
    
    # Target URLs for Aadhaar and PAN
    targets = {
        "aadhaar_about": "https://uidai.gov.in/en/about-uidai/unique-identification-authority-of-india/about.html",
        "pan_guidelines": "https://www.protean-tinpan.com/services/pan/pan-index.html" 
    }
    
    for name, url in targets.items():
        scraper.scrape_url(url, name)
