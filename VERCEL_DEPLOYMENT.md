# 🚀 Vercel Deployment Guide

## Quick Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/kartikay2005/llm-quiz-solver)

## Prerequisites

- Vercel account (free tier works)
- GitHub repository connected to Vercel
- Environment variables ready

## Step-by-Step Deployment

### 1. Install Vercel CLI (Optional)

```powershell
npm install -g vercel
```

### 2. Configure Environment Variables

In Vercel Dashboard or via CLI, add these secrets:

```bash
# Required
QUIZ_SECRET=your_jwt_token_here
STUDENT_EMAIL=your_email@example.com

# Optional (for OpenAI fallback)
OPENAI_API_KEY=sk-...
AIPIPE_API_KEY=your_aipipe_key
```

**Via Vercel Dashboard:**
1. Go to Project → Settings → Environment Variables
2. Add each variable with the value
3. Select all environments (Production, Preview, Development)

**Via Vercel CLI:**
```bash
vercel env add QUIZ_SECRET
vercel env add STUDENT_EMAIL
vercel env add OPENAI_API_KEY
vercel env add AIPIPE_API_KEY
```

### 3. Deploy

**Option A: Deploy via GitHub (Recommended)**
1. Push to GitHub: `git push origin main`
2. Go to [vercel.com/new](https://vercel.com/new)
3. Import your repository: `kartikay2005/llm-quiz-solver`
4. Configure environment variables
5. Click "Deploy"

**Option B: Deploy via CLI**
```powershell
cd D:\coding\TDS
vercel --prod
```

### 4. Verify Deployment

```bash
# Test health endpoint
curl https://your-project.vercel.app/healthz

# Test solving endpoint
curl -X POST https://your-project.vercel.app/solving \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your_email@example.com",
    "secret": "your_jwt_token",
    "url": "https://example.com/quiz"
  }'
```

## ⚠️ Important Limitations

### Serverless Environment Constraints

1. **No Playwright Browser Automation**
   - Vercel serverless functions cannot run Chromium
   - Falls back to `httpx` for HTML fetching
   - ❌ Cannot execute JavaScript on pages
   - ❌ Cannot download linked files
   - ❌ Cannot capture window.quizData variables

2. **Limited Execution Time**
   - Max execution: 10 seconds (Hobby), 60 seconds (Pro)
   - Complex quizzes may timeout
   - Consider upgrading to Vercel Pro if needed

3. **Cold Starts**
   - First request may take 3-5 seconds
   - Subsequent requests are faster

4. **No File Downloads**
   - Cannot save files to disk
   - File-based quiz data may not work

### What Still Works

✅ FastAPI API endpoints  
✅ JWT authentication  
✅ Basic HTML parsing  
✅ LLM integration (OpenAI/AIPipe)  
✅ JSON/CSV data embedded in HTML  
✅ Multi-format data parsing (except PDFs with downloads)  
✅ Retry logic  
✅ Error handling  

### What Doesn't Work

❌ JavaScript-heavy quizzes (window.quizData)  
❌ PDF/Excel file downloads  
❌ Complex browser interactions  
❌ Playwright automation  

## 🔄 Recommended Architecture

For production use, consider this hybrid approach:

```
┌─────────────┐
│   Vercel    │  ← Handles API, simple quizzes
│  (FastAPI)  │
└──────┬──────┘
       │
       ├─→ Simple HTML quizzes (direct)
       │
       └─→ Complex quizzes → ┌──────────────┐
                              │ External     │
                              │ Worker       │ ← Playwright automation
                              │ (Railway,    │   (Docker container)
                              │  Render, etc)│
                              └──────────────┘
```

**Setup External Worker:**
- Deploy Playwright version on Railway/Render/Fly.io
- Keep Vercel as API gateway
- Route complex requests to worker service

## 📊 Performance Comparison

| Environment | Browser | JS Execution | Response Time | Concurrent |
|-------------|---------|--------------|---------------|------------|
| **Local**   | ✅ Full | ✅ Yes       | 28.7s avg     | Limited    |
| **Vercel**  | ❌ None | ❌ No        | ~5-10s        | Auto-scale |
| **Railway** | ✅ Full | ✅ Yes       | 30s avg       | Manual     |

## 🛠️ Local vs Serverless Mode

The code automatically detects the environment:

```python
# app/quiz/browser.py
IS_SERVERLESS = os.getenv("VERCEL") == "1"

if IS_SERVERLESS:
    # Use httpx (fast, limited)
else:
    # Use Playwright (full features)
```

**Test locally before deploying:**
```bash
# Test serverless mode locally
export VERCEL=1
python -m uvicorn app.server.main:app --host 0.0.0.0 --port 8000
```

## 🔧 Troubleshooting

### Deployment Fails

**Error: "Module not found: playwright"**
- Expected in serverless mode
- Code falls back to httpx automatically

**Error: "Function execution timeout"**
- Quiz too complex for serverless
- Upgrade to Vercel Pro (60s timeout)
- Or use external worker service

**Error: "Environment variable not found"**
```bash
vercel env pull .env.local  # Download env vars
vercel env ls                # List all vars
```

### Runtime Issues

**403 Forbidden**
- Check `QUIZ_SECRET` matches your JWT token
- Verify email matches token payload

**Empty response**
- Quiz requires JavaScript execution
- Not supported in serverless mode
- Deploy worker service for complex quizzes

**Timeout errors**
- Reduce quiz complexity
- Upgrade Vercel plan
- Split into multiple requests

## 📈 Scaling Strategy

### Phase 1: Vercel Only (Simple Quizzes)
- Use for testing
- Handles basic HTML quizzes
- Free tier: 100GB bandwidth, 100k requests

### Phase 2: Hybrid (Recommended)
- Vercel: API gateway + simple quizzes
- Railway/Render: Playwright worker for complex quizzes
- Cost: $5-10/month

### Phase 3: Full Infrastructure
- Vercel: API layer
- AWS Lambda + Docker: Playwright automation
- CloudFlare Workers: Caching layer
- Cost: $20-50/month

## 🌐 Alternative Platforms

If Vercel doesn't meet your needs:

| Platform | Playwright | Timeout | Price | Best For |
|----------|-----------|---------|-------|----------|
| **Railway** | ✅ Yes | 30min | $5/mo | Full automation |
| **Render** | ✅ Yes | 15min | $7/mo | Docker apps |
| **Fly.io** | ✅ Yes | No limit | $5/mo | Global edge |
| **Heroku** | ✅ Yes | 30s (web) | $7/mo | Simple setup |
| **AWS Lambda** | ⚠️ Docker | 15min | Pay-per-use | Enterprise |

**Recommended: Railway** for full Playwright support.

## 📝 Post-Deployment Checklist

- [ ] Environment variables configured
- [ ] Health endpoint returns 200
- [ ] Test with sample quiz URL
- [ ] Monitor execution time (logs)
- [ ] Set up custom domain (optional)
- [ ] Configure CORS if needed
- [ ] Enable deployment protection
- [ ] Set up monitoring/alerts

## 🔗 Useful Links

- **Vercel Dashboard:** https://vercel.com/dashboard
- **Deployment Logs:** https://vercel.com/kartikay2005/llm-quiz-solver/deployments
- **API Endpoint:** https://your-project.vercel.app
- **Documentation:** https://vercel.com/docs

---

**Ready to deploy?** Follow the steps above or click the Deploy button at the top! 🚀
