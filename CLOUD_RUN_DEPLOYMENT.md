# Google Cloud Run Deployment Guide

## 📋 Prerequisites

- Google account
- Credit/debit card (for $300 free credit - won't be charged)
- Your Groq API key

---

## 🚀 Step-by-Step Deployment

### Step 1: Set Up Google Cloud Account (5 min)

1. Go to https://console.cloud.google.com
2. Sign in with your Google account
3. Click "Try for free" or "Activate"
4. Enter payment details (gets you $300 free credit, valid 90 days)
5. Accept terms and conditions

✅ **You now have $300 free credit!**

---

### Step 2: Install Google Cloud CLI (5 min)

**Windows:**
1. Download: https://cloud.google.com/sdk/docs/install
2. Run the installer
3. Follow prompts (use default settings)
4. When done, open a NEW PowerShell/Terminal window

**Verify installation:**
```bash
gcloud --version
```

---

### Step 3: Initialize and Authenticate (5 min)

```bash
# Login to Google Cloud
gcloud auth login

# This opens a browser - select your Google account and authorize

# Set your project (replace PROJECT_ID with your actual project ID from console)
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

**To find your PROJECT_ID:**
- Go to https://console.cloud.google.com
- Look at the top navbar - you'll see project name/ID
- Or create a new project: Click dropdown → "New Project" → Name it "luna-journal"

---

### Step 4: Navigate to Your App Directory (1 min)

```bash
cd "C:\Users\pragy\OneDrive\Desktop\trial\journaling_companion"
```

---

### Step 5: Deploy to Cloud Run (5 min)

```bash
# Deploy the app
gcloud run deploy luna-journal \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars GROQ_API_KEY=YOUR_GROQ_API_KEY_HERE
```

**Replace `YOUR_GROQ_API_KEY_HERE` with your actual Groq API key from `.env` file**

**What happens:**
- Builds Docker image from your code
- Uploads to Google Container Registry
- Deploys to Cloud Run
- Takes 3-5 minutes first time

**When prompted:**
- "Allow unauthenticated invocations?" → **y** (yes)

---

### Step 6: Get Your URL

After deployment completes, you'll see:
```
Service [luna-journal] revision [luna-journal-00001] has been deployed and is serving 100 percent of traffic.
Service URL: https://luna-journal-xxxxx-uc.a.run.app
```

✅ **Copy this URL - this is your live app!**

---

## 🔧 Update Your App Later

Made changes to your code? Redeploy:

```bash
# Navigate to app directory
cd "C:\Users\pragy\OneDrive\Desktop\trial\journaling_companion"

# Deploy again (uses same command)
gcloud run deploy luna-journal \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars GROQ_API_KEY=YOUR_GROQ_API_KEY_HERE
```

Takes 2-3 minutes for updates.

---

## 🔐 Managing Secrets (Better Way)

Instead of passing API key in command, use Secret Manager:

### Step 1: Enable Secret Manager
```bash
gcloud services enable secretmanager.googleapis.com
```

### Step 2: Create Secret
```bash
echo -n "YOUR_GROQ_API_KEY" | gcloud secrets create GROQ_API_KEY --data-file=-
```

### Step 3: Deploy with Secret
```bash
gcloud run deploy luna-journal \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --set-secrets GROQ_API_KEY=GROQ_API_KEY:latest
```

---

## 📊 Monitor Your App

### View Logs
```bash
gcloud run logs read luna-journal --region us-central1
```

### Check Service Status
```bash
gcloud run services describe luna-journal --region us-central1
```

### View in Console
https://console.cloud.google.com/run

---

## 💰 Cost Monitoring

### Check Usage
1. Go to https://console.cloud.google.com/billing
2. Click "Reports"
3. See your spending (should be $0-5 for review period)

### Set Budget Alert
1. Go to https://console.cloud.google.com/billing/budgets
2. Create budget alert at $10
3. Get email if costs approach limit

---

## 🔄 Common Commands

```bash
# View all your Cloud Run services
gcloud run services list

# Delete the service (to stop billing)
gcloud run services delete luna-journal --region us-central1

# Update environment variables
gcloud run services update luna-journal \
    --region us-central1 \
    --set-env-vars NEW_VAR=value

# Set custom domain (optional)
gcloud run domain-mappings create --service luna-journal --domain yourdomain.com
```

---

## 🐛 Troubleshooting

### Build Fails
```bash
# Check logs
gcloud builds list
gcloud builds log [BUILD_ID]

# Common issue: Missing dependencies
# Fix: Check requirements.txt and Dockerfile
```

### App Crashes on Startup
```bash
# View logs
gcloud run logs read luna-journal --region us-central1 --limit 100

# Common issues:
# - Missing GROQ_API_KEY
# - Model download timeout (increase timeout in Cloud Run settings)
```

### Model Download Takes Too Long
```bash
# Increase timeout and memory
gcloud run services update luna-journal \
    --region us-central1 \
    --timeout 600 \
    --memory 2Gi
```

---

## ⚡ Performance Optimization

### Increase Resources (if needed)
```bash
gcloud run services update luna-journal \
    --region us-central1 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10
```

### Minimum Instances (keeps app warm - costs more)
```bash
gcloud run services update luna-journal \
    --region us-central1 \
    --min-instances 1
```

**Note:** Min instances = always running = higher cost (~$10-20/month)
**For review period:** Not needed, cold starts are fast enough

---

## 🎯 Your Deployment Checklist

- [ ] Google Cloud account created ($300 credit)
- [ ] gcloud CLI installed and authenticated
- [ ] Project created and APIs enabled
- [ ] App deployed successfully
- [ ] Service URL obtained and tested
- [ ] GROQ_API_KEY secret added
- [ ] App loads and works (test all features)
- [ ] URL added to README
- [ ] Budget alert set ($10)

---

## 📞 Support

**Google Cloud Documentation:**
- Cloud Run: https://cloud.google.com/run/docs
- Troubleshooting: https://cloud.google.com/run/docs/troubleshooting

**Your URL Format:**
```
https://luna-journal-[random]-uc.a.run.app
```

---

## 🚀 After Deployment

Update your README.md with the Cloud Run URL:
```markdown
**Live Demo:** https://your-service-url.run.app
```

---

**Estimated Time:** 20-30 minutes total
**Estimated Cost:** $0-3 for entire review period

Good luck! 🎉
