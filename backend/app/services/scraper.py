import requests
from bs4 import BeautifulSoup
import os
import json
import logging
from urllib.parse import urljoin

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

    def download_pdfs_from_url(self, url: str, archive_dir: str, limit: int = 3):
        """Scrapes a URL for PDF links and downloads them if not already archived."""
        logger.info(f"Scanning {url} for PDFs...")
        try:
            response = requests.get(url, headers=self.headers, timeout=15, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=True)
            
            downloaded = 0
            for link in links:
                if downloaded >= limit:
                    logger.info(f"Reached download limit of {limit} PDFs. Stopping scrape.")
                    break
                    
                href = link['href']
                if href.lower().endswith('.pdf'):
                    # Handle relative URLs
                    if href.startswith('/'):
                        pdf_url = urljoin(url, href)
                    elif not href.startswith('http'):
                        # Could be relative without slash, e.g. "docs/file.pdf"
                        pdf_url = urljoin(url, href)
                    else:
                        pdf_url = href
                        
                    filename = pdf_url.split('/')[-1]
                    # Check if it exists in raw
                    raw_path = os.path.join(self.output_dir, filename)
                    
                    # Check archive dir (archive filenames have timestamp prepended)
                    is_archived = False
                    if os.path.exists(archive_dir):
                        for arch_file in os.listdir(archive_dir):
                            if arch_file.endswith(filename):
                                is_archived = True
                                break
                    
                    if os.path.exists(raw_path) or is_archived:
                        logger.info(f"Skipping already downloaded/archived PDF: {filename}")
                        continue
                        
                    # Download PDF
                    logger.info(f"Downloading new PDF: {filename}")
                    try:
                        pdf_res = requests.get(pdf_url, headers=self.headers, timeout=30, verify=False)
                        pdf_res.raise_for_status()
                        with open(raw_path, 'wb') as f:
                            f.write(pdf_res.content)
                        downloaded += 1
                    except Exception as e:
                        logger.error(f"Failed to download {pdf_url}: {e}")
                        
            logger.info(f"Successfully downloaded {downloaded} new PDFs from {url}")
            return downloaded
            
        except Exception as e:
            logger.error(f"Failed to scan {url} for PDFs: {e}")
            return 0

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
