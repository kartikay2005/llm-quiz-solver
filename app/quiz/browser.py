"""Browser automation utilities using Playwright sync API.

This module provides functions to load pages, capture HTML, and download linked files.
"""
from typing import Dict, Any
from pathlib import Path
from app.utils.config import settings
from app.utils.logger import get_logger

logger = get_logger("browser")


def _ensure_download_dir(base: str) -> Path:
    """Ensure download directory exists."""
    p = Path(base)
    p.mkdir(parents=True, exist_ok=True)
    return p


def fetch_page_and_downloads(url: str, download_dir: str | None = None, timeout: int = 30) -> Dict[str, Any]:
    """Visit `url` with Playwright, return page HTML, final URL, and list of downloaded file paths.

    Downloads are saved to `download_dir`.
    
    Args:
        url: URL to visit
        download_dir: Directory to save downloads (defaults to settings.DOWNLOAD_DIR)
        timeout: Page load timeout in seconds
        
    Returns:
        Dict with keys: html, url, downloads (list of file paths)
    """
    download_dir = download_dir or settings.DOWNLOAD_DIR
    download_path = _ensure_download_dir(download_dir)

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
