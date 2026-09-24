import requests
from bs4 import BeautifulSoup
import os
import json
import logging
import hashlib
from urllib.parse import urljoin, urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GovScraper:
    def __init__(self, output_dir: str = "../../data/raw"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.archive_dir = os.path.abspath(os.path.join(self.output_dir, "../archive"))
        self.memory_path = os.path.join(self.archive_dir, "spider_memory.json")
        self.memory = {}
        self.load_memory()

    def load_memory(self):
        if os.path.exists(self.memory_path):
            try:
                with open(self.memory_path, 'r', encoding='utf-8') as f:
                    self.memory = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load memory: {e}")
                self.memory = {}

    def save_memory(self):
        os.makedirs(os.path.dirname(self.memory_path), exist_ok=True)
        try:
            with open(self.memory_path, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")

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

    def get_file_hash(self, file_path: str) -> str:
        """Returns the SHA-256 hash of a file."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def download_pdfs_from_url(self, seed_url: str, archive_dir: str, limit: int = 5, max_depth: int = 1):
        """Scrapes a URL recursively for PDF links, downloading them and checking hashes to detect updates."""
        base_domain = urlparse(seed_url).netloc
        queue = [(seed_url, 0)]
        visited_urls = set()
        downloaded = 0
        
        logger.info(f"Spider starting at {seed_url} with max depth {max_depth} and limit {limit}...")
        
        while queue and downloaded < limit:
            current_url, depth = queue.pop(0)
            
            if current_url in visited_urls:
                continue
            visited_urls.add(current_url)
            
            logger.info(f"Scanning {current_url} (Depth: {depth})...")
            try:
                response = requests.get(current_url, headers=self.headers, timeout=15, verify=False)
                response.raise_for_status()
                
                # Basic check to skip non-HTML content like zip files that masquerade without extensions
                if 'text/html' not in response.headers.get('Content-Type', ''):
                    continue
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                links = soup.find_all('a', href=True)
                
                for link in links:
                    if downloaded >= limit:
                        break
                        
                    href = link['href']
                    
                    if href.startswith('/'):
                        full_url = urljoin(current_url, href)
                    elif not href.startswith('http'):
                        full_url = urljoin(current_url, href)
                    else:
                        full_url = href
                        
                    # 1. PDF Download & Hash Check
                    if full_url.lower().split('?')[0].endswith('.pdf'):
                        filename = full_url.split('/')[-1].split('?')[0]
                        raw_path = os.path.join(self.output_dir, filename)
                        
                        logger.info(f"Found PDF: {filename}. Doing HEAD request...")
                        try:
                            # Use HEAD to check metadata before downloading
                            head_res = requests.head(full_url, headers=self.headers, timeout=10, verify=False, allow_redirects=True)
                            last_modified = head_res.headers.get("Last-Modified")
                            etag = head_res.headers.get("ETag")
                            
                            metadata_key = f"{last_modified}|{etag}"
                            
                            # If metadata perfectly matches memory, skip download entirely
                            if (last_modified or etag) and self.memory.get(full_url) == metadata_key:
                                logger.info(f"Skipping download (Metadata unchanged): {filename}")
                                continue

                            logger.info(f"Metadata changed or missing. Downloading {filename} to verify hash...")
                            pdf_res = requests.get(full_url, headers=self.headers, timeout=30, verify=False)
                            pdf_res.raise_for_status()
                            with open(raw_path, 'wb') as f:
                                f.write(pdf_res.content)
                                
                            new_hash = self.get_file_hash(raw_path)
                            
                            is_duplicate = False
                            if os.path.exists(archive_dir):
                                for arch_file in os.listdir(archive_dir):
                                    if arch_file.endswith(filename):
                                        arch_path = os.path.join(archive_dir, arch_file)
                                        old_hash = self.get_file_hash(arch_path)
                                        if old_hash == new_hash:
                                            is_duplicate = True
                                        break
                                        
                            if is_duplicate:
                                logger.info(f"PDF is unchanged (hashes match). Skipping: {filename}")
                                os.remove(raw_path)
                                # Update memory even if hash is same so we don't download it next time
                                if last_modified or etag:
                                    self.memory[full_url] = metadata_key
                                    self.save_memory()
                            else:
                                logger.info(f"New or Updated PDF! Kept: {filename}")
                                if last_modified or etag:
                                    self.memory[full_url] = metadata_key
                                    self.save_memory()
                                downloaded += 1
                        except Exception as e:
                            logger.error(f"Failed to process {full_url}: {e}")
                            
                    # 2. Add sub-pages to queue if within depth
                    elif depth < max_depth:
                        link_domain = urlparse(full_url).netloc
                        # Domain Lock Check
                        if link_domain == base_domain or link_domain == "":
                            clean_url = full_url.split('#')[0]
                            if clean_url not in visited_urls:
                                queue.append((clean_url, depth + 1))
                                
            except Exception as e:
                logger.error(f"Failed to scan {current_url}: {e}")
                
        logger.info(f"Spider finished! Downloaded {downloaded} PDFs from {seed_url} and its sub-pages.")
        return downloaded

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
