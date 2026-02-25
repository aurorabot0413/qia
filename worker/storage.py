"""
Cloud Storage Uploader
"""
from google.cloud import storage
from typing import List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class CloudStorageUploader:
    """Sube artifacts a Cloud Storage"""
    
    def __init__(self, bucket_name: str = None):
        self.client = storage.Client()
        self.bucket_name = bucket_name or "qia-artifacts-bucket"
        self.bucket = self.client.bucket(self.bucket_name)
    
    async def upload_report(self, report_html: str, pr_number: int) -> str:
        """
        Sube reporte HTML a Cloud Storage
        
        Args:
            report_html: Contenido HTML del reporte
            pr_number: Número del PR
        
        Returns:
            URL pública del reporte
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            blob_name = f"reports/pr-{pr_number}/report_{timestamp}.html"
            
            blob = self.bucket.blob(blob_name)
            blob.upload_from_string(report_html, content_type="text/html")
            
            # Hacer público
            blob.make_public()
            
            url = blob.public_url
            logger.info(f"Report uploaded: {url}")
            
            return url
            
        except Exception as e:
            logger.error(f"Error uploading report: {e}")
            raise
    
    async def upload_screenshots(
        self,
        screenshots: List[bytes],
        pr_number: int
    ) -> List[dict]:
        """
        Sube screenshots a Cloud Storage
        
        Args:
            screenshots: Lista de screenshots en bytes
            pr_number: Número del PR
        
        Returns:
            Lista de dicts con route y url
        """
        try:
            urls = []
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            for i, screenshot in enumerate(screenshots):
                blob_name = f"screenshots/pr-{pr_number}/screenshot_{timestamp}_{i}.png"
                
                blob = self.bucket.blob(blob_name)
                blob.upload_from_string(screenshot, content_type="image/png")
                
                # Hacer público
                blob.make_public()
                
                url = blob.public_url
                urls.append({
                    "route": f"/screenshot_{i}",
                    "url": url
                })
                
                logger.info(f"Screenshot {i} uploaded: {url}")
            
            return urls
            
        except Exception as e:
            logger.error(f"Error uploading screenshots: {e}")
            raise
