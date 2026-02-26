"""
QiA QA Worker - Main Script
Ejecutado dentro de Cloud Build
"""
import asyncio
import logging
from typing import Optional

from github_analyzer import GitHubPRAnalyzer
from browser_automation import BrowserAutomator
from agents.qa_agent import QAAgent
from report_generator import ReportGenerator
from storage import CloudStorageUploader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """
    Flujo principal del QA Worker:
    1. Analizar PR
    2. Navegar a cambios
    3. Capturar screenshots
    4. Analizar con LangChain + Vertex AI
    5. Generar reporte
    6. Subir a Cloud Storage
    7. Enviar notificaciones
    """
    try:
        # Obtener variables de entorno
        import os
        pr_number = int(os.getenv("PR_NUMBER"))
        repo_name = os.getenv("REPO_NAME")
        app_url = os.getenv("APP_URL", "http://localhost:3000")
        
        logger.info(f"Starting QA for PR #{pr_number} in {repo_name}")
        
        # 1. Analizar PR
        logger.info("Step 1: Analyzing PR...")
        analyzer = GitHubPRAnalyzer()
        pr_data = await analyzer.analyze_pr(repo_name, pr_number)
        
        # 2. Navegar a cambios
        logger.info("Step 2: Navigating to changes...")
        browser = BrowserAutomator()
        await browser.launch()
        
        # Login si es necesario
        username = os.getenv("APP_USERNAME")
        password = os.getenv("APP_PASSWORD")
        if username and password:
            await browser.login(username, password)
        
        # Navegar a vista modificada
        await browser.navigate_to_changes(pr_data["modified_routes"])
        
        # 3. Capturar screenshots
        logger.info("Step 3: Capturing screenshots...")
        screenshots = await browser.capture_screenshots()
        await browser.close()
        
        # 4. Analizar con LangChain + Vertex AI
        logger.info("Step 4: Analyzing with LangChain + Vertex AI...")
        qa_agent = QAAgent()
        analysis = await qa_agent.analyze(
            pr_data=pr_data,
            screenshots=screenshots,
            design_image=pr_data.get("design_image")
        )
        
        # 5. Generar reporte
        logger.info("Step 5: Generating report...")
        generator = ReportGenerator()
        report = generator.generate(analysis, pr_data, screenshots)
        
        # 6. Subir a Cloud Storage
        logger.info("Step 6: Uploading to Cloud Storage...")
        uploader = CloudStorageUploader()
        report_url = await uploader.upload_report(report, pr_number)
        screenshot_urls = await uploader.upload_screenshots(screenshots, pr_number)
        
        # 7. Enviar notificaciones
        logger.info("Step 7: Sending notifications...")
        # TODO: Implementar email y GitHub comment
        
        logger.info(f"QA completed for PR #{pr_number}")
        logger.info(f"Report: {report_url}")
        logger.info(f"Status: {analysis['status']}")
        logger.info(f"Confidence: {analysis.get('confidence', 0) * 100:.0f}%")
        
        # Exit code 0 - el pipeline se completó exitosamente
        # El resultado del análisis (approved/needs_review/rejected) va en el reporte
        exit(0)
            
    except Exception as e:
        logger.error(f"Error in QA pipeline: {e}", exc_info=True)
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
