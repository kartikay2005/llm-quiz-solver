"""Extract question, submit endpoint and embedded data from HTML and downloaded files."""
from typing import Dict, Any
from bs4 import BeautifulSoup
import pandas as pd
import json
from app.utils.logger import get_logger
import pdfplumber

logger = get_logger("extractor")


def parse_html_for_quiz(html: str, js_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Parse HTML and extract likely question text, submit endpoint, and data links.
    
    Args:
        html: Raw HTML content
        js_data: Optional JavaScript data extracted from browser
        
    Returns:
        Dict with keys: question, submit_url, links, embedded_json, tables
    """
    js_data = js_data or {}
    soup = BeautifulSoup(html, "html.parser")
    
    # heuristic: look for element with class or id containing 'question'
    question = None
    for sel in [".question", "#question", "[data-question]", "h1", "h2", "p"]:
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            text = el.get_text(separator=" ", strip=True)
            if "question" in sel.lower() or len(text) > 20:
                question = text
                break
    
    # if still no question, get all text
    if not question:
        question = soup.get_text(separator=" ", strip=True)[:500]

    # find forms
    submit_url = None
    form = soup.find("form")
    if form and form.get("action"):
        submit_url = form.get("action")

    # find data links
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(href.lower().endswith(ext) for ext in (".pdf", ".csv", ".xlsx", ".xls", ".json")):
            links.append(href)

    # Add JavaScript data to embedded_json if available
    embedded_json = []
    if js_data:
        for var_name, data in js_data.items():
            if isinstance(data, dict):
                embedded_json.append(data)
                logger.info(f"Added JS variable {var_name} to embedded_json")
                
                # Override question and submit_url if present in JS data
                if 'question' in data and not question:
                    question = data['question']
                if 'submit_url' in data and not submit_url:
                    submit_url = data['submit_url']
    
    # try to find JSON embedded in scripts (fallback)
    for script in soup.find_all("script"):
        try:
            text = script.string
            if not text:
                continue
            if "{" in text and "}" in text:
                # naive search
                start = text.find("{")
                end = text.rfind("}")
                cand = text[start:end+1]
                try:
                    obj = json.loads(cand)
                    embedded_json.append(obj)
                except Exception:
                    continue
        except Exception:
            continue

    # parse HTML tables
    tables = []
    try:
        dfs = pd.read_html(html)
        tables = [df.to_dict(orient="records") for df in dfs]
    except Exception:
        pass

    return {
        "question": question,
        "submit_url": submit_url,
        "links": links,
        "embedded_json": embedded_json,
        "tables": tables
    }


def parse_csv(path: str) -> pd.DataFrame:
    """Parse CSV file into DataFrame."""
    return pd.read_csv(path)


def parse_xlsx(path: str) -> pd.DataFrame:
    """Parse Excel file into DataFrame."""
    return pd.read_excel(path)


def parse_pdf(path: str) -> str:
    """Extract text from PDF file.
    
    Args:
        path: Path to PDF file
        
    Returns:
        Extracted text content
    """
    text = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text.append(page.extract_text() or "")
    except Exception as e:
        logger.exception("PDF parse failed: %s", e)
    return "\n".join(text)


def parse_table_html(html: str):
    """Extract tables from HTML.
    
    Args:
        html: HTML content
        
    Returns:
        List of DataFrames
    """
    dfs = pd.read_html(html)
    return dfs
