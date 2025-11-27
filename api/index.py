"""Vercel serverless function entry point."""
from http.server import BaseHTTPRequestHandler
import json
import os


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/healthz" or self.path == "/api/index/healthz":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        elif self.path == "/" or self.path == "/api/index":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "message": "LLM Quiz Solver API",
                "status": "running",
                "version": "1.0"
            }).encode())
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"detail": "Not Found"}).encode())
    
    def do_POST(self):
        """Handle POST requests."""
        if self.path == "/solving" or self.path == "/api/index/solving":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode()
                data = json.loads(body)
                
                email = data.get("email", "")
                secret = data.get("secret", "")
                url = data.get("url", "")
                
                # Validate
                expected_secret = os.getenv("QUIZ_SECRET", "")
                if not expected_secret or secret != expected_secret:
                    self.send_response(403)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"detail": "Invalid secret"}).encode())
                    return
                
                if not email or not email.strip():
                    self.send_response(422)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"detail": "Email cannot be empty"}).encode())
                    return
                
                # Fetch and solve
                import urllib.request
                from urllib.error import URLError
                
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=30) as response:
                        html = response.read().decode("utf-8", errors="ignore")
                except URLError as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"detail": f"Failed to fetch URL: {str(e)}"}).encode())
                    return
                
                # Simple question extraction
                import re
                question = ""
                match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
                if match:
                    question = re.sub(r"<[^>]+>", "", match.group(1)).strip()
                
                if not question:
                    match = re.search(r"<p[^>]*>(.*?)</p>", html, re.IGNORECASE | re.DOTALL)
                    if match:
                        question = re.sub(r"<[^>]+>", "", match.group(1)).strip()
                
                if not question:
                    question = re.sub(r"<[^>]+>", " ", html)
                    question = re.sub(r"\s+", " ", question).strip()[:500]
                
                # Call LLM
                answer = "Unable to determine answer"
                aipipe_key = os.getenv("QUIZ_SECRET", "")
                
                if aipipe_key and question:
                    try:
                        import urllib.request
                        llm_data = json.dumps({
                            "model": "openai/gpt-4o-mini",
                            "messages": [
                                {"role": "system", "content": "You are a quiz solver. Answer concisely."},
                                {"role": "user", "content": f"Question: {question[:500]}\n\nProvide only the answer."}
                            ],
                            "max_tokens": 100
                        }).encode()
                        
                        llm_req = urllib.request.Request(
                            "https://aipipe.org/openrouter/v1/chat/completions",
                            data=llm_data,
                            headers={
                                "Authorization": f"Bearer {aipipe_key}",
                                "Content-Type": "application/json"
                            },
                            method="POST"
                        )
                        
                        with urllib.request.urlopen(llm_req, timeout=60) as llm_response:
                            llm_result = json.loads(llm_response.read().decode())
                            answer = llm_result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    except Exception as e:
                        answer = f"LLM Error: {str(e)}"
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "question": question[:200] if question else "No question found",
                    "answer": answer,
                    "url": url
                }).encode())
                
            except json.JSONDecodeError:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"detail": "Invalid JSON"}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"detail": str(e)}).encode())
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"detail": "Not Found"}).encode())
