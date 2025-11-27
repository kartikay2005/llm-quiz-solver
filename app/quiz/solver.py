"""Main quiz solver orchestration with recursive solving and retries."""
import time
from typing import Any, Dict
from pathlib import Path
from app.quiz.browser import fetch_page_and_downloads
from app.quiz.extractor import (
    parse_html_for_quiz,
    parse_csv,
    parse_xlsx,
    parse_pdf
)
from app.quiz.llm import solve_with_llm
from app.quiz.submitter import submit_answer
from app.utils.logger import get_logger
from app.utils.config import settings

logger = get_logger("solver")


def solve_quiz(url: str, email: str, start_time: float | None = None, depth: int = 0) -> Dict[str, Any]:
    """Recursively solve quiz at given URL.
    
    This function:
    1. Fetches the page with Playwright
    2. Extracts question, data, and submit endpoint
    3. Parses downloaded files (CSV, PDF, etc.)
    4. Calls LLM to solve the question
    5. Submits the answer
    6. If incorrect and within time window, retries
    7. If new URL returned, recursively solves next quiz
    
    Args:
        url: Quiz URL
        email: User email
        start_time: Timestamp when solving started (for 3-minute window)
        depth: Recursion depth (to prevent infinite loops)
        
    Returns:
        Final quiz result
        
    Raises:
        ValueError: If max depth or retries exceeded
    """
    if depth > 10:
        raise ValueError("Max recursion depth exceeded")
    
    if start_time is None:
        start_time = time.time()
    
    elapsed = time.time() - start_time
    if elapsed > settings.RETRY_WINDOW_SECONDS:
        raise ValueError("Exceeded 3-minute time window")
    
    logger.info("Solving quiz at depth=%d url=%s", depth, url)
    
    # Step 1: Fetch page and downloads
    try:
        logger.info("Fetching page with Playwright...")
        page_data = fetch_page_and_downloads(url)
        logger.info("Page fetched successfully")
    except Exception as e:
        logger.exception("Failed to fetch page: %s", e)
        raise ValueError(f"Browser automation failed: {str(e)}")
    
    html = page_data["html"]
    downloads = page_data["downloads"]
    js_data = page_data.get("js_data", {})
    
    # Step 2: Extract quiz info
    quiz_info = parse_html_for_quiz(html, js_data)
    question = quiz_info.get("question")
    submit_url = quiz_info.get("submit_url")
    
    if not question:
        raise ValueError("Could not extract question from page")
    
    if not submit_url:
        # try to infer from URL
        if "/demo" in url:
            submit_url = url.replace("/demo", "/submit")
        elif "/quiz/" in url:
            submit_url = url.replace("/quiz/", "/submit/")
        else:
            # Extract base URL and add /submit
            from urllib.parse import urlparse
            parsed = urlparse(url)
            submit_url = f"{parsed.scheme}://{parsed.netloc}/submit"
    
    logger.info("Question: %s", question[:100])
    logger.info("Submit URL: %s", submit_url)
    
    # Step 3: Parse downloaded files
    context = {
        "tables": quiz_info.get("tables", []),
        "embedded_json": quiz_info.get("embedded_json", []),
        "csv_data": {},
        "pdf_text": ""
    }
    
    for fpath in downloads:
        p = Path(fpath)
        ext = p.suffix.lower()
        
        try:
            if ext == ".csv":
                df = parse_csv(fpath)
                context["csv_data"][p.name] = df
                logger.info("Parsed CSV: %s with %d rows", p.name, len(df))
            elif ext in (".xlsx", ".xls"):
                df = parse_xlsx(fpath)
                context["csv_data"][p.name] = df
                logger.info("Parsed Excel: %s with %d rows", p.name, len(df))
            elif ext == ".pdf":
                text = parse_pdf(fpath)
                context["pdf_text"] += f"\n\n{p.name}:\n{text}"
                logger.info("Parsed PDF: %s (%d chars)", p.name, len(text))
        except Exception as e:
            logger.exception("Failed to parse %s: %s", fpath, e)
    
    # Step 4: Solve with LLM
    try:
        logger.info("Calling LLM to solve question...")
        answer = solve_with_llm(question, context)
        logger.info("LLM answer: %s", answer)
    except Exception as e:
        logger.exception("LLM failed: %s", e)
        # Use a default answer instead of crashing
        logger.warning("Using default answer due to LLM failure")
        answer = "Unable to solve"
    
    # Step 5: Submit answer
    for attempt in range(settings.MAX_RETRIES):
        try:
            logger.info(f"Submitting answer (attempt {attempt + 1}/{settings.MAX_RETRIES})...")
            result = submit_answer(submit_url, answer, email, settings.SECRET, url)
            
            # check if correct
            if result.get("correct") or result.get("status") == "success":
                logger.info("Answer correct!")
                
                # check for next URL
                next_url = result.get("next_url") or result.get("url")
                if next_url:
                    logger.info("Next quiz URL: %s", next_url)
                    return solve_quiz(next_url, email, start_time, depth + 1)
                
                return result
            
            # incorrect
            logger.warning("Answer incorrect on attempt %d", attempt + 1)
            
            # check time window
            elapsed = time.time() - start_time
            if elapsed > settings.RETRY_WINDOW_SECONDS:
                logger.error("Exceeded time window, cannot retry")
                return result
            
            # retry with updated context
            if attempt < settings.MAX_RETRIES - 1:
                logger.info("Retrying with refined prompt...")
                # optionally refine prompt here
                answer = solve_with_llm(
                    f"{question}\n\nPrevious answer was incorrect: {answer}\nPlease reconsider and provide a different answer.",
                    context
                )
        
        except Exception as e:
            logger.exception("Submit failed on attempt %d: %s", attempt + 1, e)
            if attempt == settings.MAX_RETRIES - 1:
                # Return error response instead of crashing
                return {
                    "status": "error",
                    "message": f"Submit failed: {str(e)}",
                    "answer": answer,
                    "question": question[:100]
                }
    
    return {
        "status": "failed", 
        "message": "Max retries exceeded",
        "answer": answer,
        "question": question[:100] if question else None
    }
