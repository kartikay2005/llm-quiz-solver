"""Vercel serverless function entry point for FastAPI."""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os

# Create FastAPI app
app = FastAPI(title="LLM Quiz Solver")


class SolveRequest(BaseModel):
    email: str
    secret: str
    url: str


@app.get("/api/index")
@app.get("/")
def root():
    return {"message": "LLM Quiz Solver API", "status": "running", "version": "1.0"}


@app.get("/api/index/healthz")
@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/api/index/solving")
@app.post("/solving")
async def solving(request: SolveRequest):
    """Solve a quiz from the given URL."""
    import httpx
    
    # Validate secret
    expected_secret = os.getenv("QUIZ_SECRET", "")
    if not expected_secret or request.secret != expected_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    # Validate email
    if not request.email or not request.email.strip():
        raise HTTPException(status_code=422, detail="Email cannot be empty")
    
    try:
        # Fetch the page
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(request.url, follow_redirects=True)
            html = response.text
        
        # Parse HTML for question
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract question text
        question = None
        for selector in [".question", "#question", "h1", "h2", "p"]:
            el = soup.select_one(selector)
            if el and el.get_text(strip=True):
                text = el.get_text(separator=" ", strip=True)
                if len(text) > 10:
                    question = text
                    break
        
        if not question:
            question = soup.get_text(separator=" ", strip=True)[:500]
        
        # Try to call LLM
        answer = None
        aipipe_key = os.getenv("QUIZ_SECRET", "")
        
        if aipipe_key:
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    llm_response = await client.post(
                        "https://aipipe.org/openrouter/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {aipipe_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "openai/gpt-4o-mini",
                            "messages": [
                                {"role": "system", "content": "You are a quiz solver. Answer concisely."},
                                {"role": "user", "content": f"Question: {question}\n\nProvide only the answer."}
                            ],
                            "max_tokens": 100
                        }
                    )
                    if llm_response.status_code == 200:
                        data = llm_response.json()
                        answer = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            except Exception as e:
                answer = f"LLM Error: {str(e)}"
        
        if not answer:
            answer = "Unable to determine answer"
        
        return {
            "status": "success",
            "question": question[:200] if question else "No question found",
            "answer": answer,
            "url": request.url
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Vercel requires this handler
handler = app
