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
                
                # Enhanced question extraction
                import re
                from html.parser import HTMLParser
                
                class TextExtractor(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.text = []
                        self.skip_tags = {'script', 'style', 'head', 'meta', 'link'}
                        self.current_tag = None
                    def handle_starttag(self, tag, attrs):
                        self.current_tag = tag
                    def handle_data(self, data):
                        if self.current_tag not in self.skip_tags:
                            self.text.append(data.strip())
                    def get_text(self):
                        return ' '.join(filter(None, self.text))
                
                question = ""
                
                # Try to find question in common selectors
                patterns = [
                    r'class=["\'][^"\']*question[^"\']*["\'][^>]*>(.*?)</div>',
                    r'id=["\']question["\'][^>]*>(.*?)</div>',
                    r'<h1[^>]*>(.*?)</h1>',
                    r'<h2[^>]*>(.*?)</h2>',
                    r'<p[^>]*class=["\'][^"\']*question[^"\']*["\'][^>]*>(.*?)</p>',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
                    if match:
                        text = re.sub(r'<[^>]+>', ' ', match.group(1))
                        text = re.sub(r'\s+', ' ', text).strip()
                        if len(text) > 10:
                            question = text
                            break
                
                # Look for embedded JSON with question data
                if not question:
                    json_match = re.search(r'["\']question["\']\s*:\s*["\']([^"\']+)["\']', html)
                    if json_match:
                        question = json_match.group(1)
                
                # Extract all visible text as fallback
                if not question or len(question) < 20:
                    extractor = TextExtractor()
                    try:
                        extractor.feed(html)
                        full_text = extractor.get_text()
                        if full_text:
                            question = full_text[:1000]
                    except:
                        question = re.sub(r'<[^>]+>', ' ', html)
                        question = re.sub(r'\s+', ' ', question).strip()[:1000]
                
                # Call LLM
                answer = "Unable to determine answer"
                aipipe_key = os.getenv("QUIZ_SECRET", "")
                
                if aipipe_key and question:
                    try:
                        import urllib.request
                        llm_data = json.dumps({
                            "model": "openai/gpt-4o-mini",
                            "messages": [
                                {"role": "system", "content": "You are an expert quiz solver for IIT Madras TDS (Tools in Data Science) course. Analyze the question carefully and provide ONLY the final answer. For multiple choice, give only the letter or text of the correct option. For numerical answers, give only the number. For code output questions, give only the output value. Be precise and concise."},
                                {"role": "user", "content": f"Question/Content:\n{question[:1500]}\n\nProvide ONLY the answer, nothing else."}
                            ],
                            "max_tokens": 200,
                            "temperature": 0.1
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
