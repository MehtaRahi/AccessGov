import os
import json
import logging
import fitz  
from langchain.text_splitter import RecursiveCharacterTextSplitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentParser:
    def __init__(self, raw_dir: str = "../../../data/raw", processed_dir: str = "../../../data/processed"):
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir
        os.makedirs(self.processed_dir, exist_ok=True)
        
        # Initialize LangChain's chunker
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def parse_pdf(self, file_path: str) -> str:
        """Extract text from a PDF file."""
        text = ""
        try:
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
            logger.info(f"Successfully extracted {len(text)} characters from {os.path.basename(file_path)}")
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
        return text

    def parse_txt(self, file_path: str) -> str:
        """Extract text from a TXT file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error parsing TXT {file_path}: {e}")
            return ""

    def process_all_documents(self):
        """Process all files in the raw directory and save chunks to processed directory."""
        all_chunks = []
        
        if not os.path.exists(self.raw_dir):
            logger.warning(f"Raw directory {self.raw_dir} does not exist.")
            return

        for filename in os.listdir(self.raw_dir):
            file_path = os.path.join(self.raw_dir, filename)
            text = ""
            
            logger.info(f"Processing {filename}...")
            if filename.lower().endswith(".pdf"):
                text = self.parse_pdf(file_path)
            elif filename.lower().endswith(".txt"):
                text = self.parse_txt(file_path)
            else:
                logger.info(f"Skipping unsupported file type: {filename}")
                continue
                
            if not text.strip():
                logger.warning(f"No text extracted from {filename}")
                continue
                
            # Chunk the text using Langchain
            chunks = self.text_splitter.split_text(text)
            logger.info(f"Split {filename} into {len(chunks)} chunks.")
            
            # Format chunks with metadata
            for i, chunk in enumerate(chunks):
                all_chunks.append({
                    "id": f"{filename}_chunk_{i}",
                    "source": filename,
                    "text": chunk
                })
        
        # Save processed chunks
        output_file = os.path.join(self.processed_dir, "processed_chunks.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Successfully saved {len(all_chunks)} total chunks to {output_file}")

if __name__ == "__main__":
    parser = DocumentParser()
    parser.process_all_documents()
