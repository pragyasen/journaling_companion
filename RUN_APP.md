# Running Your Gradio App

## Quick Start

### 1. Install Gradio
```bash
pip install gradio
```

Or update all requirements:
```bash
pip install -r requirements.txt
```

### 2. Make Sure You Have Your Groq API Key
Check that `.env` file exists with:
```
GROQ_API_KEY=gsk_your_actual_key_here
```

### 3. Launch the App
```bash
python app.py
```

### 4. Open in Browser
The app will automatically open, or go to:
```
http://127.0.0.1:7860
```

## What You'll See

```
┌────────────────────────────────────────────────────────┐
│  🌟 AI-Powered Journaling Companion                    │
├──────────────────────────┬─────────────────────────────┤
│                          │  📊 Analysis Panel          │
│  Chat Area               │                             │
│  (Your conversation)     │  Sentiment: 😊 POSITIVE     │
│                          │  Confidence: 89%            │
│  User: "Today was..."    │                             │
│                          │  Themes Detected:           │
│  AI: "I hear you..."     │  • Work & Career ████ 85%   │
│                          │  • Personal Growth ██ 65%   │
│                          │                             │
│  [Write here...]  [Send] │  🔒 Privacy Info            │
└──────────────────────────┴─────────────────────────────┘
```

## Features

✅ **Split View Design**
- Chat on the left
- Live analysis on the right

✅ **Real-time Analysis**
- Sentiment detection
- Theme classification
- Visual progress bars

✅ **Conversational AI**
- Empathetic responses
- Context-aware
- Powered by Llama 3.3

✅ **Beautiful Styling**
- Gradient colors
- Clean layout
- Professional look

## Tips for Demo

1. **Sample Entries to Try:**
   - "Today was stressful at work but I took a walk"
   - "Had amazing coffee with my best friend!"
   - "Starting a meditation practice"

2. **Show These Features:**
   - How sentiment changes with different entries
   - Multiple theme detection
   - Natural conversational responses

3. **For Presentation:**
   - Set `share=True` in app.py for public link
   - Pre-write 2-3 entries before demo
   - Test internet connection

## Customization

### Change Colors
Edit the `custom_css` section in `app.py`:
```python
#analysis-panel {
    background: linear-gradient(135deg, #YOUR_COLOR_1, #YOUR_COLOR_2);
}
```

### Change Port
```python
demo.launch(server_port=8000)  # Use different port
```

### Get Public Link (for demo)
```python
demo.launch(share=True)  # Creates shareable link
```

## Troubleshooting

### Port already in use
```bash
# Change port in app.py or kill the process
netstat -ano | findstr :7860
taskkill /PID <PID> /F
```

### Models loading slowly
- Normal on first run (downloads ~2GB)
- Subsequent runs are much faster

### Gradio not found
```bash
pip install --upgrade gradio
```

## Next Steps

Once this works:
1. ✅ Test with various entries
2. ✅ Customize colors/styling
3. ✅ Add to presentation
4. ✅ Get public share link for demo

Enjoy! 🎉
