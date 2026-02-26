"""
Report Generator - HTML Reports
"""
from jinja2 import Environment, FileSystemLoader
from typing import Dict, List
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Genera reportes HTML para QiA"""
    
    def __init__(self):
        # Usar ruta absoluta al directorio templates
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.template = self.env.get_template('report.html')
    
    def generate(
        self,
        analysis: Dict,
        pr_data: Dict,
        screenshots: List[Dict]
    ) -> str:
        """
        Genera reporte HTML
        
        Args:
            analysis: Resultado del análisis de IA
            pr_data: Datos del PR
            screenshots: Lista de screenshots
        
        Returns:
            HTML string
        """
        try:
            # Determinar status class y text
            status_class = self._get_status_class(analysis["status"])
            status_text = self._get_status_text(analysis["status"])
            
            # Preparar datos para template
            context = {
                "pr_number": pr_data["number"],
                "pr_title": pr_data["title"],
                "repo_name": pr_data.get("repo_name", "unknown"),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status_class": status_class,
                "status_text": status_text,
                "confidence": int(analysis.get("confidence", 0) * 100),
                "summary": analysis.get("summary", "No summary available"),
                "files_changed": pr_data.get("changed_files", 0),
                "additions": pr_data.get("additions", 0),
                "deletions": pr_data.get("deletions", 0),
                "screenshots_count": len(screenshots),
                "screenshots": screenshots,
                "issues": analysis.get("issues", [])
            }
            
            # Renderizar template
            html = self.template.render(**context)
            
            logger.info(f"Report generated for PR #{pr_data['number']}")
            
            return html
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise
    
    def _get_status_class(self, status: str) -> str:
        """Obtiene clase CSS para el status"""
        status_classes = {
            "approved": "approved",
            "rejected": "rejected",
            "needs_review": "needs-review"
        }
        return status_classes.get(status, "needs-review")
    
    def _get_status_text(self, status: str) -> str:
        """Obtiene texto para el status"""
        status_texts = {
            "approved": "✅ APPROVED",
            "rejected": "❌ REJECTED",
            "needs_review": "⚠️ NEEDS REVIEW"
        }
        return status_texts.get(status, "NEEDS REVIEW")
