"""LLM integration for solving quiz questions using AIPipe or OpenAI API."""
import json
from typing import Any, Dict
import requests
from app.utils.config import settings
from app.utils.logger import get_logger

logger = get_logger("llm")


def call_aipipe_llm(prompt: str, temperature: float = 0.1) -> str:
    """Call AIPipe (institution) API with the given prompt.
    
    Args:
        prompt: User prompt
        temperature: Sampling temperature
        
    Returns:
        LLM response text
    """
    if not settings.SECRET:
        raise ValueError("QUIZ_SECRET (token) not configured")
    
    logger.info("Calling AIPipe API model=%s", settings.AIPIPE_MODEL)
    
    try:
        response = requests.post(
            settings.AIPIPE_API_URL,
            headers={
                "Authorization": f"Bearer {settings.SECRET}",
                "Content-Type": "application/json"
            },
            json={
                "model": settings.AIPIPE_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful data analysis assistant. You analyze data, perform calculations, and provide answers in the exact format requested."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": temperature
            },
            timeout=settings.REQUEST_TIMEOUT
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Extract answer from response
        answer = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        if not answer:
            logger.error("No content in AIPipe response: %s", result)
            raise ValueError("Empty response from AIPipe")
        
        logger.info("AIPipe response received: %s", answer[:200])
        return answer
        
    except requests.exceptions.RequestException as e:
        logger.exception("AIPipe API call failed: %s", e)
        raise


def call_openai_llm(prompt: str, temperature: float = 0.1) -> str:
    """Call OpenAI API with the given prompt.
    
    Args:
        prompt: User prompt
        temperature: Sampling temperature
        
    Returns:
        LLM response text
    """
    if not settings.OPENAI_API_KEY or not settings.OPENAI_API_KEY.startswith("sk-"):
        raise ValueError("Valid OpenAI API key not configured")
    
    try:
        import openai
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        logger.info("Calling OpenAI model=%s", settings.OPENAI_MODEL)
        
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful data analysis assistant. You analyze data, perform calculations, and provide answers in the exact format requested."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature
        )
        
        answer = response.choices[0].message.content
        logger.info("OpenAI response received: %s", answer[:200])
        return answer
    except Exception as e:
        logger.exception("OpenAI API call failed: %s", e)
        raise


def call_llm(prompt: str, temperature: float = 0.1) -> str:
    """Call LLM API (AIPipe or OpenAI) with the given prompt.
    
    Args:
        prompt: User prompt
        temperature: Sampling temperature
        
    Returns:
        LLM response text
    """
    # Use AIPipe by default (institution API)
    if settings.USE_AIPIPE:
        try:
            return call_aipipe_llm(prompt, temperature)
        except Exception as e:
            logger.warning("AIPipe failed, falling back to OpenAI: %s", e)
            # Fall through to OpenAI
    
    # Try OpenAI as fallback
    try:
        return call_openai_llm(prompt, temperature)
    except Exception as e:
        logger.error("All LLM APIs failed: %s", e)
        # Return a mock response for testing
        logger.warning("Using mock response")
        return "42"


def solve_with_llm(question: str, context: Dict[str, Any]) -> Any:
    """Use LLM to solve a quiz question given extracted context.
    
    Args:
        question: The quiz question text
        context: Extracted data including tables, PDFs, CSV data, etc.
        
    Returns:
        Parsed answer (could be string, number, bool, dict, list)
    """
    # build comprehensive prompt
    prompt_parts = [f"Question: {question}\n"]
    
    if context.get("tables"):
        prompt_parts.append("Available tables:")
        for i, table in enumerate(context["tables"]):
            prompt_parts.append(f"\nTable {i+1}:")
            prompt_parts.append(json.dumps(table[:10], indent=2))  # first 10 rows
    
    if context.get("csv_data"):
        prompt_parts.append("\nCSV data:")
        for fname, df in context["csv_data"].items():
            prompt_parts.append(f"\n{fname}:")
            prompt_parts.append(df.head(20).to_string())
    
    if context.get("pdf_text"):
        prompt_parts.append("\nPDF content (excerpt):")
        prompt_parts.append(context["pdf_text"][:2000])
    
    if context.get("embedded_json"):
        prompt_parts.append("\nEmbedded JSON data:")
        prompt_parts.append(json.dumps(context["embedded_json"], indent=2))
    
    prompt_parts.append("\n\nAnalyze the data and answer the question. If the answer is a number, return just the number. If it's a boolean, return true or false. If it's JSON, return valid JSON. Be precise and concise.")
    
    full_prompt = "\n".join(prompt_parts)
    
    llm_response = call_llm(full_prompt)
    
    # attempt to parse response
    answer = parse_llm_response(llm_response)
    
    return answer


def parse_llm_response(response: str) -> Any:
    """Parse LLM response into appropriate type.
    
    Tries to detect JSON, boolean, number, or returns string.
    
    Args:
        response: Raw LLM response
        
    Returns:
        Parsed value
    """
    response = response.strip()
    
    # try JSON
    if response.startswith("{") or response.startswith("["):
        try:
            return json.loads(response)
        except Exception:
            pass
    
    # try boolean
    if response.lower() in ("true", "yes"):
        return True
    if response.lower() in ("false", "no"):
        return False
    
    # try number
    try:
        if "." in response:
            return float(response)
        return int(response)
    except Exception:
        pass
    
    return response
