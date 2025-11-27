# Token Testing Suite

This folder contains scripts to test if the institution token is working correctly.

## Quick Test

```powershell
# Make sure virtual environment is activated
.\.venv\Scripts\Activate.ps1

# Install optional dependency for JWT decoding
pip install pyjwt

# Run the test suite
python test_key/test_token.py
```

## What Gets Tested

1. **Token Format** - Validates token structure
2. **JWT Decode** - Decodes token to see payload (optional)
3. **API Connection** - Tests connection to potential IITM endpoints
4. **Local API** - Checks if your FastAPI server is running
5. **Solving Endpoint** - Tests `/solving` endpoint with the token

## Expected Output

```
🧪 INSTITUTION TOKEN TEST SUITE
============================================================
Email: 23f3002264@ds.study.iitm.ac.in
============================================================

TEST 1: Token Format Validation
✅ Token format looks valid

TEST 2: JWT Token Decode
✅ Token decoded successfully

...

TEST SUMMARY
============================================================
Token Format         ✅ PASS
JWT Decode          ✅ PASS
API Connection      ✅ PASS
Local API           ✅ PASS
Solving Endpoint    ✅ PASS
============================================================

Passed: 5/5

🎉 All tests passed!
```

## Troubleshooting

### "Local API not running"
Start your server first:
```powershell
uvicorn app.server.main:app --reload
```

### "Token rejected (403 Forbidden)"
The token might not match the one configured in `.env`. Check:
- `.env` file has correct `QUIZ_SECRET`
- Server was restarted after changing `.env`
