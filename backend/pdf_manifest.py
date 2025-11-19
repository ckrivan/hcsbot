"""
PDF Manifest for external PDF hosting
For now, we'll disable external PDFs and let the system fail gracefully
until proper OneDrive integration is set up
"""

import requests
import tempfile
import os
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# PDF URLs using OneDrive shared folder direct download links
# Based on your shared folder: https://1drv.ms/f/c/950f0852825412c4/Ehu0VYfY9pRBulx3bEQ6sdEBoDyjBw-Gn1YxLuSkQ4uIhQ
BASE_DOWNLOAD_URL = "https://api.onedrive.com/v1.0/shares/u!aHR0cHM6Ly8xZHJ2Lm1zL2YvYy85NTBmMDg1MjgyNTQxMmM0L0VodDBWWWZZOXBSQnVseDNiRVE2c2RFQm9EeWpCdy1HbjFZeEx1U2tRNHVJaFE/root/children"

# Core PDFs to start with (we'll load a subset for faster initialization)
PDF_URLS = {
    "Apple_Configurator_2_Blueprints.pdf": f"{BASE_DOWNLOAD_URL}/Apple_Configurator_2_Blueprints.pdf:/content?download=true",
    "Jamf_Connect_Azure.pdf": f"{BASE_DOWNLOAD_URL}/Jamf_Connect_Azure.pdf:/content?download=true", 
    "apple-style-guide.pdf": f"{BASE_DOWNLOAD_URL}/apple-style-guide.pdf:/content?download=true",
    "Getting_Started_Sonoma.pdf": f"{BASE_DOWNLOAD_URL}/Getting_Started_Sonoma.pdf:/content?download=true",
    "System_Settings_Sequoia.pdf": f"{BASE_DOWNLOAD_URL}/System_Settings_Sequoia.pdf:/content?download=true"
    # Will add more PDFs once core functionality is working
}

class ExternalPDFManager:
    def __init__(self):
        self.cache_dir = tempfile.gettempdir()
        
    def download_pdf(self, filename: str) -> Optional[str]:
        """Download PDF from OneDrive and return local path"""
        if filename not in PDF_URLS:
            logger.error(f"PDF not found in manifest: {filename}")
            return None
            
        url = PDF_URLS[filename]
        local_path = os.path.join(self.cache_dir, filename)
        
        # Check if already cached
        if os.path.exists(local_path):
            logger.info(f"Using cached PDF: {filename}")
            return local_path
            
        try:
            logger.info(f"Downloading PDF: {filename}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            logger.info(f"Successfully downloaded: {filename}")
            return local_path
            
        except Exception as e:
            logger.error(f"Failed to download {filename}: {e}")
            return None
            
    def get_all_pdf_paths(self) -> Dict[str, str]:
        """Download all PDFs and return filename -> local_path mapping"""
        pdf_paths = {}
        for filename in PDF_URLS.keys():
            path = self.download_pdf(filename)
            if path:
                pdf_paths[filename] = path
        return pdf_paths