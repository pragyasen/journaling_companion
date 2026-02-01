# 🚀 Quick Deploy to Google Cloud Run

## ⚡ Fast Track (If you have gcloud CLI installed)

```bash
# 1. Navigate to your project
cd "C:\Users\pragy\OneDrive\Desktop\trial\journaling_companion"

# 2. Login (opens browser)
gcloud auth login

# 3. Set project (create one at console.cloud.google.com if needed)
gcloud config set project YOUR_PROJECT_ID

# 4. Enable APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com

# 5. Deploy (replace YOUR_KEY with your actual Groq API key)
gcloud run deploy luna-journal --source . --region us-central1 --platform managed --allow-unauthenticated --set-env-vars GROQ_API_KEY=YOUR_GROQ_API_KEY

# 6. Done! Copy the Service URL from output
```

**That's it!** Takes 5-7 minutes.

---

## 📝 First Time Setup?

**See full guide:** `CLOUD_RUN_DEPLOYMENT.md`

**Steps:**
1. Create Google Cloud account (get $300 free credit)
2. Install gcloud CLI
3. Run commands above
4. Get your live URL

---

## 🔄 Update After Changes

```bash
# Just run deploy again
gcloud run deploy luna-journal --source . --region us-central1 --platform managed --allow-unauthenticated --set-env-vars GROQ_API_KEY=YOUR_KEY
```

---

## ✅ Files Ready for Deployment

- ✅ `Dockerfile` - Container configuration
- ✅ `.dockerignore` - Excludes unnecessary files
- ✅ `app.py` - Updated for Cloud Run (PORT handling)
- ✅ `requirements.txt` - Dependencies
- ✅ `database.py` - Database logic

**Everything is ready to deploy!**

---

## 🎯 Your URL Will Be:

```
https://luna-journal-xxxxx-uc.a.run.app
```

**Always available, fast loading, professional!**
