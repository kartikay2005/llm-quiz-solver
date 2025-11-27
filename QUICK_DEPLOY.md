# 🚀 Quick Deploy to Vercel

## Fastest Method (1-Click)

Click this button:

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/kartikay2005/llm-quiz-solver)

## What Happens Next?

1. **Vercel will ask you to:**
   - Connect your GitHub account
   - Name your project (default: llm-quiz-solver)
   - Configure environment variables

2. **Add these Environment Variables:**
   ```
   QUIZ_SECRET = eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjMwMDIyNjRAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.haMtw8VQmQ7d1hwehI-u-fZCIiR-vFXz5xCqO_6Wd8M
   STUDENT_EMAIL = 23f3002264@ds.study.iitm.ac.in
   OPENAI_API_KEY = (optional - your OpenAI key)
   ```

3. **Click "Deploy"**
   - Build takes ~2-3 minutes
   - You'll get a URL like: `https://your-project.vercel.app`

4. **Test Your Deployment:**
   ```bash
   # Health check
   curl https://your-project.vercel.app/healthz
   
   # Solve a quiz
   curl -X POST https://your-project.vercel.app/solving \
     -H "Content-Type: application/json" \
     -d '{
       "email": "23f3002264@ds.study.iitm.ac.in",
       "secret": "your_jwt_token",
       "url": "https://example.com/quiz"
     }'
   ```

## ⚠️ Limitations

- ❌ No Playwright (no JavaScript execution)
- ❌ No file downloads
- ❌ No window.quizData extraction
- ✅ Works for simple HTML quizzes
- ✅ Fast response times
- ✅ Auto-scaling

## 📚 Full Documentation

- **Comprehensive Guide:** [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md)
- **Main README:** [README.md](README.md)
- **GitHub Repo:** https://github.com/kartikay2005/llm-quiz-solver

---

**That's it! Your quiz solver will be live in minutes!** 🎉
