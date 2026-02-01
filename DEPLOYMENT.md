# Deployment Guide: Hugging Face Spaces

## Step-by-Step Deployment

### 1. Create Hugging Face Account
- Go to https://huggingface.co/join
- Sign up (free)

### 2. Create a New Space
1. Click your profile → "New Space"
2. Name: `luna-journal` (or any name)
3. Select: **Gradio** as SDK
4. Visibility: **Public** (for demo) or **Private** (for personal use)
5. Click "Create Space"

### 3. Upload Files

Upload these files to your Space:
```
luna-journal/
├── app.py
├── database.py
├── requirements.txt
└── README.md
```

**Important**: DO NOT upload:
- `.env` (contains your API key)
- `journal_entries.db` (your personal data)
- `test_*.py` files

### 4. Add Secrets (IMPORTANT!)

In your Space settings:
1. Go to "Settings" tab
2. Scroll to "Repository secrets"
3. Click "New secret"
4. Name: `GROQ_API_KEY`
5. Value: Your Groq API key
6. Click "Add"

### 5. Modify app.py for Deployment

Change the launch settings at the bottom of `app.py`:

```python
if __name__ == "__main__":
    print("\n" + "="*70)
    print("Launching Luna (AI Journaling Companion)")
    print("="*70)
    demo.launch()  # Simple launch for Hugging Face
```

Remove or comment out:
- `server_name` parameter
- `server_port` parameter  
- The "Quit App" button (since users don't control the server)

### 6. Deploy

1. Commit files to your Space
2. Wait 2-3 minutes for build
3. Your app will be live at: `https://huggingface.co/spaces/YOUR_USERNAME/luna-journal`

## Alternative: Using Git

```bash
# 1. Clone your space repository
git clone https://huggingface.co/spaces/YOUR_USERNAME/luna-journal
cd luna-journal

# 2. Copy files
cp ../journaling_companion/app.py .
cp ../journaling_companion/database.py .
cp ../journaling_companion/requirements.txt .
cp ../journaling_companion/README.md .

# 3. Push to Hugging Face
git add .
git commit -m "Deploy Luna journal app"
git push
```

## Database Considerations

Since each user should have their own data:

### Option 1: Temporary Storage (Recommended for Demo)
- Each user gets a fresh database per session
- Data is lost when session ends
- Good for public demos

### Option 2: User-Specific Storage
Add user authentication:
```python
with gr.Blocks() as demo:
    user_id = gr.State(value=lambda: str(uuid.uuid4()))
    # Use user_id for separate databases
```

## Cost Considerations

**Groq API Usage**:
- Free tier: 14,400 requests/day
- If sharing publicly, your API key will be used by all users
- Consider adding rate limiting or usage monitoring

## Rate Limiting (Optional)

Add to `app.py`:
```python
import time
from functools import wraps

# Simple rate limiter
last_request = {}

def rate_limit(seconds=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_ip = gr.Request.client.host
            now = time.time()
            if user_ip in last_request:
                if now - last_request[user_ip] < seconds:
                    return "⏳ Please wait a moment before sending another message."
            last_request[user_ip] = now
            return func(*args, **kwargs)
        return wrapper
    return decorator

@rate_limit(seconds=2)
def chat_interface(message, history):
    # ... existing code
```

## Monitoring

Check Space logs:
1. Go to your Space
2. Click "Logs" tab
3. Monitor usage and errors

## Updating Your Space

```bash
# Make changes locally
# Then push:
git add .
git commit -m "Update: description of changes"
git push
```

## Troubleshooting

### Build Fails
- Check requirements.txt for typos
- Ensure all dependencies are compatible

### API Key Not Working
- Verify secret name is exactly `GROQ_API_KEY`
- Check the key is valid on Groq console

### Models Not Loading
- Increase CPU/RAM in Space settings
- Use smaller models if needed

## Your Live Link

Once deployed, share:
```
https://huggingface.co/spaces/YOUR_USERNAME/luna-journal
```

Anyone can access it instantly - no setup required! 🚀
