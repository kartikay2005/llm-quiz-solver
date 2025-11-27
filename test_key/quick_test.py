"""Quick test - just validates token with running server."""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
import requests

load_dotenv()

TOKEN = os.getenv("QUIZ_SECRET")
EMAIL = "23f3002264@ds.study.iitm.ac.in"

print("\n🧪 QUICK TOKEN TEST")
print("="*60)

# Test 1: Token format
print(f"\n✅ Token: {TOKEN[:30]}... (length: {len(TOKEN)})")

# Test 2: JWT Decode
try:
    import jwt
    decoded = jwt.decode(TOKEN, options={"verify_signature": False})
    print(f"✅ JWT Email: {decoded.get('email')}")
except Exception as e:
    print(f"⚠️  JWT decode: {e}")

# Test 3: Server health
try:
    r = requests.get("http://127.0.0.1:8000/healthz", timeout=2)
    if r.status_code == 200:
        print(f"✅ Server running: {r.json()}")
    else:
        print(f"❌ Server error: {r.status_code}")
except:
    print("❌ Server not running - start with:")
    print("   D:/coding/TDS/.venv/Scripts/python.exe -m uvicorn app.server.main:app --host 127.0.0.1 --port 8000")
    sys.exit(1)

# Test 4: Token validation
print(f"\n🔐 Testing token validation...")
payload = {
    "email": EMAIL,
    "secret": TOKEN,
    "url": "https://httpbin.org/html"  # Simple HTML page
}

try:
    print("Sending request (may take 10-30 seconds for browser automation)...")
    r = requests.post("http://127.0.0.1:8000/solving", json=payload, timeout=60)
    print(f"Status: {r.status_code}")
    
    if r.status_code == 403:
        print("❌ Token REJECTED (403)")
    elif r.status_code == 400:
        print(f"⚠️  Bad request (400) - likely URL/parsing issue")
        print(f"Response: {r.text[:500]}")
    elif r.status_code == 500:
        print(f"⚠️  Server error (500) - check server logs")
        print(f"Response: {r.text[:500]}")
    elif r.status_code == 200:
        print(f"✅ Token ACCEPTED!")
        print(f"Response: {r.text[:500]}")
    else:
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:200]}")
except requests.exceptions.Timeout:
    print(f"❌ Request timed out after 60s")
    print("   This might be due to:")
    print("   - Playwright browser taking too long")
    print("   - OpenAI API key not configured (using mock mode)")
    print("   - Network issues")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)
