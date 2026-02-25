"""
Browser Automation con Playwright
"""
from playwright.async_api import async_playwright, Browser, Page
import logging
from typing import List, Optional
import os

logger = logging.getLogger(__name__)


class BrowserAutomator:
    """Automatiza navegación y captura de screenshots"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def launch(self):
        """Inicia el browser"""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=self.headless)
            self.page = await self.browser.new_page()
            
            # Configurar viewport
            await self.page.set_viewport_size({"width": 1920, "height": 1080})
            
            logger.info("Browser launched successfully")
            
        except Exception as e:
            logger.error(f"Error launching browser: {e}")
            raise
    
    async def navigate(self, url: str):
        """Navega a una URL"""
        try:
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            logger.info(f"Navigated to {url}")
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            raise
    
    async def login(self, username: str, password: str, login_url: Optional[str] = None):
        """Realiza login en la aplicación"""
        try:
            if login_url:
                await self.navigate(login_url)
            
            # Buscar campos de login (selectores comunes)
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[id="email"]',
                '#email'
            ]
            
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[id="password"]',
                '#password'
            ]
            
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Iniciar")'
            ]
            
            # Encontrar y llenar email
            for selector in email_selectors:
                try:
                    await self.page.fill(selector, username, timeout=2000)
                    logger.info(f"Email filled using selector: {selector}")
                    break
                except:
                    continue
            
            # Encontrar y llenar password
            for selector in password_selectors:
                try:
                    await self.page.fill(selector, password, timeout=2000)
                    logger.info(f"Password filled using selector: {selector}")
                    break
                except:
                    continue
            
            # Click submit
            for selector in submit_selectors:
                try:
                    await self.page.click(selector, timeout=2000)
                    logger.info(f"Submit clicked using selector: {selector}")
                    break
                except:
                    continue
            
            # Esperar navegación
            await self.page.wait_for_load_state("networkidle", timeout=10000)
            
            logger.info("Login successful")
            
        except Exception as e:
            logger.error(f"Error during login: {e}")
            raise
    
    async def navigate_to_changes(self, routes: List[str]):
        """Navega a las rutas modificadas"""
        screenshots = []
        
        for route in routes:
            try:
                url = f"{os.getenv('APP_URL')}{route}"
                await self.navigate(url)
                
                # Esperar a que cargue
                await self.page.wait_for_load_state("networkidle", timeout=10000)
                
                # Capturar screenshot
                screenshot = await self.page.screenshot(full_page=True)
                screenshots.append({
                    "route": route,
                    "screenshot": screenshot
                })
                
                logger.info(f"Screenshot captured for route: {route}")
                
            except Exception as e:
                logger.error(f"Error navigating to {route}: {e}")
                continue
        
        return screenshots
    
    async def capture_screenshots(self, routes: Optional[List[str]] = None) -> List[bytes]:
        """Captura screenshots"""
        screenshots = []
        
        try:
            if routes:
                # Capturar rutas específicas
                for route in routes:
                    url = f"{os.getenv('APP_URL')}{route}"
                    await self.navigate(url)
                    screenshot = await self.page.screenshot(full_page=True)
                    screenshots.append(screenshot)
            else:
                # Capturar página actual
                screenshot = await self.page.screenshot(full_page=True)
                screenshots.append(screenshot)
            
            logger.info(f"Captured {len(screenshots)} screenshots")
            
        except Exception as e:
            logger.error(f"Error capturing screenshots: {e}")
            raise
        
        return screenshots
    
    async def close(self):
        """Cierra el browser"""
        try:
            if self.browser:
                await self.browser.close()
                logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
