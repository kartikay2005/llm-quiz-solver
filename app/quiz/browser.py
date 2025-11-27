"""Serverless-compatible browser utilities.

For Vercel deployment, Playwright cannot run in serverless functions.
This module provides fallback using httpx for basic HTML fetching.
"""
import os
from typing import Dict, Any
from pathlib import Path
from app.utils.logger import get_logger

logger = get_logger("browser")

# Check if running in serverless environment
IS_SERVERLESS = os.getenv("VERCEL", "").lower() == "1" or os.getenv("AWS_LAMBDA_FUNCTION_NAME")


def fetch_page_and_downloads(url: str, download_dir: str | None = None, timeout: int = 30) -> Dict[str, Any]:
    """Fetch page content with appropriate method based on environment.
    
    In serverless mode (Vercel): Uses httpx for basic HTML fetching
    In local mode: Uses Playwright for full browser automation
    
    Args:
        url: URL to visit
        download_dir: Directory to save downloads
        timeout: Request timeout in seconds
        
    Returns:
        Dict with keys: html, url, downloads, js_data
    """
    if IS_SERVERLESS:
        logger.info("Running in serverless mode - using httpx")
        return _fetch_with_httpx(url, timeout)
    else:
        logger.info("Running in local mode - using Playwright")
        return _fetch_with_playwright(url, download_dir, timeout)


def _fetch_with_httpx(url: str, timeout: int) -> Dict[str, Any]:
    """Fetch HTML using httpx (serverless-compatible)."""
    import httpx
    
    try:
        logger.info("Fetching %s with httpx", url)
        
        # Handle file:// URLs
        if url.startswith("file://"):
            file_path = url.replace("file://", "")
            with open(file_path, 'r', encoding='utf-8') as f:
                html = f.read()
            return {"html": html, "url": url, "downloads": [], "js_data": {}}
        
        # Fetch HTTP/HTTPS URLs
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            html = response.text
            final_url = str(response.url)
            
        logger.info("Successfully fetched %d bytes", len(html))
        return {"html": html, "url": final_url, "downloads": [], "js_data": {}}
        
    except Exception as e:
        logger.exception("HTTP fetch failed: %s", e)
        raise


def _fetch_with_playwright(url: str, download_dir: str | None, timeout: int) -> Dict[str, Any]:
    """Fetch HTML using Playwright (local mode only)."""
    from app.utils.config import settings
    
    download_dir = download_dir or settings.DOWNLOAD_DIR
    download_path = Path(download_dir)
    download_path.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=settings.PLAYWRIGHT_HEADLESS, timeout=60000)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()
            page.set_default_timeout(timeout * 1000)
            
            logger.info("Navigating to %s", url)
            
            try:
                page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
            except Exception as e:
                logger.warning("Page navigation timeout/error: %s", e)
                # Continue with whatever loaded
                pass

            # collect downloads triggered by initial load
            downloads = []
            
            def on_download(download):
                try:
                    suggested = download.suggested_filename
                    dest = download_path / suggested
                    download.save_as(str(dest))
                    downloads.append(str(dest))
                    logger.info("Saved download %s", dest)
                except Exception as e:
                    logger.exception("Download failed: %s", e)

            page.on("download", on_download)

            # allow some network activity (with shorter timeout)
            try:
                page.wait_for_load_state("networkidle", timeout=min(timeout * 1000, 10000))
            except Exception:
                logger.warning("Network idle timeout - continuing anyway")

            html = page.content()
            final_url = page.url

            # Extract JavaScript global variables that might contain quiz data
            js_data = {}
            try:
                # Try to extract common quiz data variable names
                for var_name in ['quizData', 'quiz_data', 'data', 'questionData', 'question_data']:
                    try:
                        result = page.evaluate(f'window.{var_name}')
                        if result:
                            js_data[var_name] = result
                            logger.info(f"Extracted JS variable: {var_name}")
                    except Exception:
                        pass
            except Exception as e:
                logger.warning(f"Failed to extract JS variables: {e}")

            # find typical links and trigger downloads for direct links (but skip to avoid hanging)
            logger.info("Skipping automatic downloads to prevent timeout")
            
            context.close()
            browser.close()

            return {"html": html, "url": final_url, "downloads": downloads, "js_data": js_data}

    except Exception as e:
        logger.exception("Playwright navigation failed: %s", e)
        raise
