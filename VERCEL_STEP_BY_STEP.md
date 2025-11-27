# 🚀 Vercel Deployment - Step-by-Step Guide

## Prerequisites
- GitHub account with repository pushed
- Vercel account (free tier works)

---

## Step 1: Create Vercel Account (if needed)

1. Go to: **https://vercel.com/signup**
2. Click **"Continue with GitHub"**
3. Authorize Vercel to access your GitHub account
4. Complete account setup

✅ **You should now be on the Vercel dashboard**

---

## Step 2: Import Your GitHub Repository

1. On Vercel dashboard, click **"Add New..."** → **"Project"**
   - URL: https://vercel.com/new

2. You'll see "Import Git Repository" section

3. Find your repository:
   - Look for **`kartikay2005/llm-quiz-solver`**
   - If you don't see it, click **"Adjust GitHub App Permissions"**
   - Grant Vercel access to the repository

4. Click **"Import"** next to `llm-quiz-solver`

✅ **You should now be on the project configuration page**

---

## Step 3: Configure Project Settings

### 3.1 Project Name (Optional)
- Default: `llm-quiz-solver`
- You can change it or leave as is
- Click **Continue**

### 3.2 Framework Preset
- Vercel should auto-detect: **"Other"**
- Leave as is, no changes needed

### 3.3 Root Directory
- Leave as **`./`** (root of repository)
- Do NOT change this

### 3.4 Build and Output Settings
- **Build Command:** Leave empty (auto-detected)
- **Output Directory:** Leave empty
- **Install Command:** Leave empty

✅ **Configuration should look minimal - Vercel handles everything via vercel.json**

---

## Step 4: Add Environment Variables ⚠️ IMPORTANT

Click **"Environment Variables"** section (expand if collapsed)

Add these **THREE** variables:

### Variable 1: QUIZ_SECRET
- **Name:** `QUIZ_SECRET`
- **Value:** 
  ```
  eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjMwMDIyNjRAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.haMtw8VQmQ7d1hwehI-u-fZCIiR-vFXz5xCqO_6Wd8M
  ```
- **Environment:** Select all (Production, Preview, Development)
- Click **"Add"**

### Variable 2: STUDENT_EMAIL
- **Name:** `STUDENT_EMAIL`
- **Value:** `23f3002264@ds.study.iitm.ac.in`
- **Environment:** Select all
- Click **"Add"**

### Variable 3: OPENAI_API_KEY (Optional)
- **Name:** `OPENAI_API_KEY`
- **Value:** Your OpenAI API key (if you have one, otherwise skip)
- **Environment:** Select all
- Click **"Add"**

✅ **You should see 2-3 environment variables listed**

---

## Step 5: Deploy! 🚀

1. Click the big **"Deploy"** button at the bottom

2. Wait for deployment (2-4 minutes)
   - You'll see a build log in real-time
   - Watch for:
     ```
     Installing dependencies...
     Building project...
     Deploying...
     ```

3. Look for success indicators:
   - ✅ Green checkmarks
   - "Congratulations!" message
   - Your deployment URL

✅ **Deployment should complete with a URL like: `https://llm-quiz-solver-xxxxx.vercel.app`**

---

## Step 6: Test Your Deployment

### 6.1 Test Health Endpoint

Open your browser or use curl:

```bash
# Replace with your actual Vercel URL
curl https://llm-quiz-solver-xxxxx.vercel.app/healthz
```

**Expected Response:**
```json
{"status": "healthy"}
```

### 6.2 Test Authentication

```bash
curl -X POST https://llm-quiz-solver-xxxxx.vercel.app/solving \
  -H "Content-Type: application/json" \
  -d '{
    "email": "23f3002264@ds.study.iitm.ac.in",
    "secret": "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjMwMDIyNjRAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.haMtw8VQmQ7d1hwehI-u-fZCIiR-vFXz5xCqO_6Wd8M",
    "url": "https://httpbin.org/html"
  }'
```

**Expected:** 200 OK with quiz solving response

✅ **If both tests pass, deployment is successful!**

---

## Step 7: Get Your Production URL

1. In Vercel dashboard, go to your project
2. Click on the deployment (topmost one)
3. Copy the **"Domains"** URL
4. This is your production endpoint

**Your URLs:**
- Production: `https://llm-quiz-solver.vercel.app` (or custom domain)
- All deployments: `https://llm-quiz-solver-xxxxx.vercel.app`

---

## Troubleshooting Common Issues

### Issue 1: Build Fails - "Module not found"

**Solution:** Check `requirements-vercel.txt` has all dependencies
```bash
# Should include:
fastapi, uvicorn, pydantic, httpx, requests, pandas, numpy, beautifulsoup4, lxml, PyJWT
```

### Issue 2: 500 Internal Server Error

**Possible Causes:**
1. Missing environment variables
2. Wrong QUIZ_SECRET value
3. Import errors

**Fix:**
1. Go to Project Settings → Environment Variables
2. Verify all variables are set
3. Click **"Redeploy"** in Deployments tab

### Issue 3: 403 Forbidden

**Cause:** Wrong JWT token

**Fix:**
1. Check `QUIZ_SECRET` environment variable
2. Must match exactly:
   ```
   eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjMwMDIyNjRAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.haMtw8VQmQ7d1hwehI-u-fZCIiR-vFXz5xCqO_6Wd8M
   ```

### Issue 4: Timeout Errors

**Cause:** Quiz takes too long (>60 seconds)

**Solutions:**
- Simplify the quiz
- Upgrade to Vercel Pro (300s timeout)
- Use Railway/Render for complex quizzes

### Issue 5: "Cannot find module 'pdfplumber'"

**Cause:** Code trying to import removed libraries

**Fix:** Already fixed in latest code - redeploy from GitHub

---

## Viewing Deployment Logs

1. Go to Vercel dashboard
2. Click your project
3. Click **"Deployments"** tab
4. Click on a deployment
5. Click **"Build Logs"** or **"Function Logs"**

**Look for:**
- Build errors in Build Logs
- Runtime errors in Function Logs

---

## Redeploying After Changes

### If you push to GitHub:
- Vercel **automatically redeploys**
- Wait 2-3 minutes
- Check deployment status in dashboard

### Manual redeploy:
1. Go to Deployments tab
2. Click **"⋯"** (three dots) on latest deployment
3. Click **"Redeploy"**
4. Wait for completion

---

## Environment Variable Management

### To add/edit variables:

1. Go to Project Settings
2. Click **"Environment Variables"**
3. Add new or edit existing
4. **Important:** Changes require redeployment
5. Go to Deployments → Redeploy

### To test variable changes:

```bash
# Test endpoint to verify variables are loaded
curl https://your-app.vercel.app/healthz
```

---

## Setting Up Custom Domain (Optional)

1. Go to Project Settings → **Domains**
2. Click **"Add Domain"**
3. Enter your domain: `quiz-solver.yourdomain.com`
4. Follow DNS configuration instructions
5. Wait for DNS propagation (5-30 minutes)

---

## Monitoring Your Deployment

### Check Deployment Status:
- **Dashboard:** https://vercel.com/kartikay2005/llm-quiz-solver
- **Deployments:** List of all deployments with status
- **Analytics:** Request counts and performance

### Function Logs:
- Real-time logs of serverless function calls
- Errors and exceptions
- Request/response times

---

## Cost Considerations

### Free Tier Includes:
- ✅ Unlimited deployments
- ✅ 100GB bandwidth/month
- ✅ 100 GB-hours compute/month
- ✅ 10 second function timeout
- ✅ HTTPS & CDN included

### If you need more:
- **Pro Plan:** $20/month
  - 60 second timeout
  - 1TB bandwidth
  - Priority support

---

## Production Checklist

Before going live, verify:

- [ ] Health endpoint returns 200 OK
- [ ] Authentication works (test with your JWT)
- [ ] Environment variables are set
- [ ] All secrets are in Vercel (not in code)
- [ ] Error handling works (test with invalid inputs)
- [ ] Response times are acceptable
- [ ] Logs are clean (no errors)

---

## Quick Reference Commands

### Test from command line:

```bash
# Set your URL
export VERCEL_URL="https://llm-quiz-solver-xxxxx.vercel.app"

# Test health
curl $VERCEL_URL/healthz

# Test solving
curl -X POST $VERCEL_URL/solving \
  -H "Content-Type: application/json" \
  -d '{
    "email": "23f3002264@ds.study.iitm.ac.in",
    "secret": "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjMwMDIyNjRAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.haMtw8VQmQ7d1hwehI-u-fZCIiR-vFXz5xCqO_6Wd8M",
    "url": "https://example.com/quiz"
  }'
```

---

## Need Help?

- **Vercel Docs:** https://vercel.com/docs
- **Support:** https://vercel.com/support
- **Status:** https://vercel-status.com
- **Community:** https://github.com/vercel/vercel/discussions

---

## Summary

✅ **You've deployed your quiz solver to Vercel!**

**Your endpoints:**
- Health: `https://your-app.vercel.app/healthz`
- Solving: `https://your-app.vercel.app/solving`

**What works:**
- Simple HTML quizzes
- JSON/CSV embedded data
- LLM integration
- Fast response times
- Auto-scaling

**What doesn't work:**
- Playwright/JavaScript execution
- PDF/Excel file parsing
- Heavy data processing

**For full features, deploy locally or use Railway/Render.**

---

🎉 **Congratulations! Your quiz solver is live!**
