# 🚀 Hugging Face Deployment Checklist

## ✅ Pre-Deployment (Files are Ready!)

Your app is now ready for Hugging Face! Here's what's been prepared:

- ✅ `app.py` - Modified for HF deployment
- ✅ `database.py` - Database logic
- ✅ `requirements.txt` - Dependencies
- ✅ `README.md` - Project description
- ✅ `.gitignore` - Prevents uploading sensitive files

## 📋 Deployment Steps

### Step 1: Create Hugging Face Account (2 min)
1. Go to https://huggingface.co/join
2. Sign up with email or GitHub
3. Verify your email

### Step 2: Create a New Space (1 min)
1. Click your profile picture → **New Space**
2. Fill in:
   - **Owner**: Your username
   - **Space name**: `luna-journal` (or any name you like)
   - **License**: MIT
   - **Select SDK**: **Gradio**
   - **Visibility**: Public (for demo) or Private (personal use)
3. Click **Create Space**

### Step 3: Upload Files (3 min)

**IMPORTANT**: Only upload these 4 files:
- [ ] `app.py`
- [ ] `database.py`
- [ ] `requirements.txt`
- [ ] `README.md`

**DO NOT upload**:
- ❌ `.env` (contains your secret API key!)
- ❌ `journal_entries.db` (your personal data!)
- ❌ `test_*.py` files (not needed)

**How to upload**:
1. Click "Files" tab in your Space
2. Click "Add file" → "Upload files"
3. Drag and drop the 4 files above
4. Click "Commit changes to main"

### Step 4: Add Your API Key Secret (2 min) ⚠️ IMPORTANT!

1. In your Space, click **Settings** tab
2. Scroll down to **Variables and secrets**
3. Under "Secrets", click **New secret**
4. Fill in:
   - **Name**: `GROQ_API_KEY` (exactly like this!)
   - **Value**: Your Groq API key (from your `.env` file)
5. Click **Save**

### Step 5: Wait for Build (2-3 min)
1. Go back to **App** tab
2. You'll see "Building..." at the top
3. Wait 2-3 minutes for the build to complete
4. Your app will appear!

### Step 6: Test Your App (1 min)
1. Try typing a journal entry
2. Click "Send"
3. Check if Luna responds
4. Try the voice input feature

### Step 7: Share Your Link! 🎉

Your app is live at:
```
https://huggingface.co/spaces/YOUR_USERNAME/luna-journal
```

Share this link with anyone - no setup required!

## 🔧 Troubleshooting

### Build Failed?
- Check the "Logs" tab for errors
- Make sure all files uploaded correctly
- Verify `requirements.txt` has no typos

### API Key Error?
- Verify secret name is exactly `GROQ_API_KEY`
- Check your key is valid at https://console.groq.com
- Make sure you saved the secret (not just a variable)

### Models Not Loading?
- Be patient - first load takes 3-5 minutes
- Check Logs tab for progress
- Models are cached after first load

### Can't Find Logs?
- Click "Logs" tab at the top of your Space
- Shows real-time server output

## 📊 Monitoring Usage

### Check API Usage:
Go to https://console.groq.com to monitor:
- Number of requests
- API credits used
- Rate limits

### Check Space Stats:
In your Space:
- Click "Insights" tab
- See number of visitors
- View usage over time

## 🔄 Updating Your App

Made changes locally? Update your Space:

1. Go to "Files" tab
2. Click on file to edit (e.g., `app.py`)
3. Click "Edit" button
4. Make changes
5. Click "Commit changes"

OR use Git:
```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/luna-journal
cd luna-journal
# Copy updated files
cp ../journaling_companion/app.py .
git add .
git commit -m "Update app"
git push
```

## 💡 Tips for Public Demo

### Protect Your API Credits:
Consider adding a note in README:
```markdown
## Note for Demo Users
This is a demo app using my personal API key. Please use responsibly!
```

### Monitor Usage:
- Check Groq console regularly
- Free tier: 14,400 requests/day
- If usage is high, you can make Space private

### Record a Video:
- Record a demo video before deploying
- In case of any issues during live demo
- Good backup for hackathon submission

## 🎯 Your Deployment URL

Once deployed, your app will be at:

```
🌐 https://huggingface.co/spaces/YOUR_USERNAME/luna-journal
```

**No Python. No installation. Just click and use!** ✨

---

## Need Help?

- 📖 Full guide: See `DEPLOYMENT.md`
- 🐛 Issues: Check Logs tab in your Space
- 💬 Questions: Ask in HF forums or Discord

Good luck with your hackathon! 🚀
