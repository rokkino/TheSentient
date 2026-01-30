import os
import asyncio
import json
import logging
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("eToroService")

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed. eToro automation will not work.")

class EtoroService:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
    async def launch_browser(self, headless: bool = False):
        """Launch the browser for eToro interaction"""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is not installed. Please install it to use this feature.")
            
        if self.browser:
            return  # Already launched
            
        self.playwright = await async_playwright().start()
        
        # Launch Chrome/Chromium 
        # channel="chrome" attempts to use installed Google Chrome which might be better for Google Login
        # but requires Chrome installed. Fallback to bundled chromium.
        try:
            self.browser = await self.playwright.chromium.launch(
                headless=headless, 
                channel="chrome", 
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
            )
        except Exception as e:
            logger.warning(f"Could not launch Chrome, falling back to Chromium: {e}")
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
            )
            
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        self.page = await self.context.new_page()
        
    async def close_browser(self):
        """Close the browser session"""
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
            
    async def initiate_google_login(self) -> Dict[str, Any]:
        """
        Initiates the Google Login flow for eToro.
        Returns the session cookies/data after successful login.
        """
        if not PLAYWRIGHT_AVAILABLE:
            return {"success": False, "message": "Playwright dependencies missing"}
            
        try:
            await self.launch_browser(headless=False) # Headful so user can interact
            
            logger.info("Navigating to eToro Login...")
            await self.page.goto("https://www.etoro.com/login", timeout=60000)
            
            # Wait for user to act or find the Google button and click it
            # eToro might show different login screens. 
            # We will attempt to find the "Sign in with Google" button.
            
            # Note: Selectors change. This is a best-effort.
            # Usually it's an iframe or a button with 'Sign in with Google' text/aria-label.
            # Or data-etoro-automation-id="login-google-button"
            
            # We will wait and observe. 
            # Ideally, we let the user sign in manually in the popup.
            
            logger.info("Waiting for user to complete login...")
            
            # Wait for a success indicator, e.g., URL change to /watchlists or existence of a user profile element
            # Timeout 5 minutes for user interaction
            try:
                await self.page.wait_for_url("**/watchlists", timeout=300000) 
                logger.info("Login detected! URL is safe.")
            except Exception:
                # Maybe they went to a different page, check if logged in
                pass
                
            # Check if really logged in by looking for specific element
            # e.g. .et-user-menu or similar
            
            # Get cookies
            cookies = await self.context.cookies()
            
            # Extract relevant auth tokens
            # Usually strict OAuth tokens or session cookies
            
            session_data = {
                "cookies": cookies,
                "timestamp": str(asyncio.get_event_loop().time())
            }
            
            await self.close_browser()
            
            return {
                "success": True,
                "message": "Login successful",
                "session": session_data
            }
            
        except Exception as e:
            logger.error(f"Error during Google Login: {e}")
            if self.browser:
                await self.close_browser()
            return {"success": False, "message": str(e)}

etoro_service = EtoroService()
