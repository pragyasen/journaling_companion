"""
AI-Powered Journaling Companion - Gradio Interface
Combines BERT analysis with Llama conversational responses
"""

import os
import html
import gradio as gr
from transformers import pipeline
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime
import database as db
import threading
import time
import sqlite3
import json

# Load environment
load_dotenv()

# Google OAuth (optional): enable with GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
try:
    import drive_storage
    _google_oauth_available = bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET"))
except Exception:
    _google_oauth_available = False

_current_user = {"email": None, "upload_cb": None}


def get_redirect_uri():
    return os.getenv("GOOGLE_REDIRECT_URI") or "http://localhost:7860/login/callback"


def get_login_html():
    """Return HTML for login bar (right split): link or logged-in message."""
    data_note = " Login is required for data-related features."
    if not _google_oauth_available:
        return f'<div id="login-bar" class="login-bar"><span>Sign in not configured.</span>{data_note}</div>'
    if _current_user["email"]:
        return f'<div id="login-bar" class="login-bar">Logged in as <strong>{html.escape(_current_user["email"])}</strong> — journal saved to Drive.</div>'
    try:
        auth_url = drive_storage.get_auth_url(get_redirect_uri())
        return f'<div id="login-bar" class="login-bar"><a href="{html.escape(auth_url)}" target="_blank" rel="noopener">Login with Google</a> — save your journal to your Drive.{data_note}</div>'
    except Exception as e:
        return f'<div id="login-bar" class="login-bar">Login unavailable: {html.escape(str(e))}.{data_note}</div>'


def logout_user():
    """Clear Google login and switch back to local DB."""
    global _current_user
    _current_user["email"] = None
    _current_user["upload_cb"] = None
    db.set_db_path(None)
    db.set_after_commit(None)
    return get_login_html(), gr.update(visible=False)


# Check Groq API key
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key or groq_api_key == "your_groq_api_key_here":
    raise ValueError("Please set GROQ_API_KEY in .env file")

# Initialize models
print("Loading AI models...")
print("Loading sentiment analysis model...")

try:
    sentiment_analyzer = pipeline(
        "sentiment-analysis",
        model="cardiffnlp/twitter-roberta-base-sentiment-latest"
    )
    print("Sentiment analyzer loaded successfully")
except Exception as e:
    print(f"Failed to load sentiment analyzer: {e}")
    print("This is usually a temporary HuggingFace API issue. Please try running again.")
    raise e

print("Loading theme classifier model...")

try:
    theme_classifier = pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli"
    )
    print("Theme classifier loaded successfully")
except Exception as e:
    print(f"Failed to load theme classifier: {e}")
    raise e

groq_client = Groq(api_key=groq_api_key)

print("All models loaded successfully!")

# Theme categories
THEMES = [
    "Work & Career",
    "Relationships & Social",
    "Health & Wellness",
    "Personal Growth",
    "Creativity & Hobbies",
    "Emotions & Mental Health",
    "Daily Life & Routine",
    "Nature & Outdoors"
]

def get_sentiment_emoji(label):
    """Get label for sentiment"""
    return ""  # No emojis

def analyze_entry(text):
    """Analyze journal entry with BERT"""
    # Sentiment analysis
    sentiment = sentiment_analyzer(text)[0]
    
    # Theme classification
    theme_result = theme_classifier(
        text,
        candidate_labels=THEMES,
        multi_label=True
    )
    
    # Get top 3 themes with score > 0.3
    top_themes = []
    for label, score in zip(theme_result['labels'], theme_result['scores']):
        if score > 0.3 and len(top_themes) < 3:
            top_themes.append((label, score))
    
    return {
        'sentiment': sentiment['label'],
        'sentiment_score': sentiment['score'],
        'themes': top_themes
    }

def generate_response(entry_text, analysis):
    """Generate empathetic response using Groq/Llama"""
    themes_str = ", ".join([theme for theme, _ in analysis['themes']]) if analysis['themes'] else "general reflection"
    sentiment_str = analysis['sentiment'].lower()
    
    system_prompt = """You are Luna, a warm and empathetic journaling companion. You guide users through meaningful self-reflection by adapting to different journaling styles.

YOUR APPROACH - Detect the type of journaling and respond accordingly:

1. FACTUAL ACCOUNT (Events without emotions):
   Signs: "I went to...", "I did...", descriptive without feelings
   → Ask: "What part of today stood out the most for you?"
   → If they mention emotions next → explore those feelings
   → If they mention learning → ask how it might be useful

2. SELF REFLECTION (Negative or complex emotions):
   Signs: "I felt stressed/sad/overwhelmed/angry/anxious"
   → Ask: "What do you think caused that feeling today?"
   → Gently explore the cause
   → Then transition: "Even in challenging moments, was there anything you're grateful for?"

3. GRATITUDE (Thankfulness expressed):
   Signs: "I'm thankful/grateful", "I appreciate", or after reflection
   → Ask: "That sounds meaningful. Why do you think that mattered to you today?"
   → Then: "What's one intention you'd like to set for tomorrow?"

4. LEARNING (Insights and realizations):
   Signs: "I learned", "I realized", "I discovered", "I understood"
   → Ask: "How do you think this might be useful in your life?"
   → Connect to future goals or gratitude

5. FUTURE SELF (Aspirations and hopes):
   Signs: "I want", "I hope", "In the future", "One day"
   → Ask: "What's one small step you could take toward that?"
   → Help them set concrete intentions

6. INTENTION SETTING (Commitments):
   Signs: "I will", "Tomorrow I want to", "My goal is", "I plan to"
   → Ask: "What might get in the way of this intention?"
   → Help anticipate obstacles, then encourage

IMPORTANT RULES:
- Only ask ONE question per response
- Keep responses 2-3 sentences maximum
- Be warm, caring, and non-judgmental
- Don't explicitly mention category names
- Flow naturally between types based on their responses
- Never give medical advice - you're a supportive friend, not a therapist

Your tone is gentle, encouraging, and genuinely curious about their experience."""

    user_prompt = f"""The user just wrote:

"{entry_text}"

Context from analysis:
- Emotional tone: {sentiment_str}
- Topics they're thinking about: {themes_str}

Respond with empathy and ask a thoughtful follow-up question that matches their journaling style."""

    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"I'm having trouble connecting right now. Error: {str(e)}"

def format_analysis_display(analysis):
    """Format analysis for display panel with fancy styling"""
    
    # Get sentiment emoji and color
    sentiment_icons = {
        'positive': '😊',
        'negative': '😔',
        'neutral': '😐'
    }
    sentiment_lower = analysis['sentiment'].lower()
    sentiment_icon = sentiment_icons.get(sentiment_lower, '💭')
    
    display = f"""
<div class="analysis-content">

<div class="analysis-section">
<div class="section-header">
<span class="section-icon">🎭</span>
<span class="section-title">Sentiment Analysis</span>
</div>
<div class="sentiment-display">
<span class="sentiment-icon">{sentiment_icon}</span>
<span class="sentiment-text">{analysis['sentiment']}</span>
<div class="confidence-bar-container">
<div class="confidence-bar" style="width: {analysis['sentiment_score']*100}%"></div>
</div>
<span class="confidence-text">{analysis['sentiment_score']:.1%} confidence</span>
</div>
</div>

<div class="analysis-divider"></div>

<div class="analysis-section">
<div class="section-header">
<span class="section-icon">🏷️</span>
<span class="section-title">Themes Detected</span>
</div>
<div class="themes-container">
"""
    
    if analysis['themes']:
        for theme, score in analysis['themes']:
            display += f"""
<div class="theme-item">
<span class="theme-name">{theme}</span>
<div class="theme-bar-container">
<div class="theme-bar" style="width: {score*100}%"></div>
</div>
<span class="theme-score">{score:.0%}</span>
</div>
"""
    else:
        display += '<div class="no-themes">No specific themes detected</div>'
    
    display += """
</div>
</div>

</div>
"""
    
    return display

def format_stats_bar():
    """Format the left stats bar only (right bar is login, separate component)."""
    stats = db.get_stats()
    return f"""
<div id="stats-bar-left" class="stats-bar-box">
<strong>Your Stats:</strong> {stats['total_entries']} days journaled | Last journal date: {stats['last_entry'] or 'Never'}
</div>
"""

def format_stats_sidebar():
    """Format the stats in the sidebar"""
    stats = db.get_stats()
    return f"""
### Stats
- Total: {stats['total_entries']}
- Positive: {stats['sentiment_counts'].get('POSITIVE', 0)}
- Neutral: {stats['sentiment_counts'].get('NEUTRAL', 0)}
- Negative: {stats['sentiment_counts'].get('NEGATIVE', 0)}

### Privacy
- Local database
- Secure & private

### Powered By
- RoBERTa (Sentiment)
- BART (Themes)
- Llama 3.3 (Chat)
- Whisper v3 (Speech-to-Text)
"""

# Mood color mappings
MOOD_COLORS = {
    'calm': {'color': '#FFFFFF', 'name': 'Calm'},
    'happy': {'color': '#FFF44F', 'name': 'Happy'},
    'energetic': {'color': '#FF6347', 'name': 'Energetic'},
    'anxious': {'color': '#9370DB', 'name': 'Anxious'},
    'sad': {'color': '#4169E1', 'name': 'Sad'},
    'angry': {'color': '#DC143C', 'name': 'Angry'}
}

def save_mood_color_handler(mood_name):
    """Handler for saving mood color selection"""
    color_hex = MOOD_COLORS[mood_name]['color']
    db.save_mood_color(f"{mood_name}:{color_hex}")
    return get_mood_status()

def get_mood_status():
    """Get current mood color status"""
    saved_color = db.get_mood_color_for_today()
    if saved_color:
        mood_name = saved_color.split(':')[0]
        mood_info = MOOD_COLORS.get(mood_name, {})
        name = mood_info.get('name', mood_name.title())
        color = mood_info.get('color', '#FFFFFF')
        return f'<div style="display: flex; align-items: center; justify-content: center; gap: 10px;"><span style="display: inline-block; width: 20px; height: 20px; background: {color}; border-radius: 50%; border: 2px solid rgba(255,255,255,0.5);"></span><span>Today\'s mood: <strong>{name}</strong></span></div>'
    return "*No mood color selected yet for today*"

def transcribe_audio(audio_path):
    """Transcribe audio using Groq Whisper API"""
    if audio_path is None:
        return ""
    
    try:
        client = Groq(api_key=groq_api_key)
        
        with open(audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                response_format="text",
                language="en"
            )
        
        return transcription
    except Exception as e:
        print(f"Transcription error: {e}")
        return ""

def chat_interface(message, history):
    """Main chat function"""
    if not message.strip():
        return history, "", load_history(), format_stats_bar(), format_stats_sidebar()
    
    # Analyze the entry
    analysis = analyze_entry(message)
    
    # Generate AI response
    ai_response = generate_response(message, analysis)
    
    # Save to database (appends to today's entry if exists)
    themes_list = [theme for theme, _ in analysis['themes']]
    entry_id = db.save_conversation_message(
        user_message=message,
        ai_response=ai_response,
        sentiment=analysis['sentiment'],
        sentiment_score=analysis['sentiment_score'],
        themes=themes_list
    )
    
    print(f"💾 Saved to today's journal (entry #{entry_id})")
    
    # Format analysis display
    analysis_display = format_analysis_display(analysis)
    
    # Gradio 6.0 format: list of dicts with 'role' and 'content'
    new_history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": ai_response}
    ]
    
    # Also refresh the history view and stats
    updated_history_view = load_history()
    updated_stats_bar = format_stats_bar()
    updated_stats_sidebar = format_stats_sidebar()
    
    return new_history, analysis_display, updated_history_view, updated_stats_bar, updated_stats_sidebar

# Custom CSS for styling
custom_css = """
/* Import fonts - Courgette for heading, Georgia for body */
@import url('https://fonts.googleapis.com/css2?family=Courgette&display=swap');

/* Global styles and light theme */
:root {
    color-scheme: light !important;
    background: #F2ECFF !important;
}

* {
    box-sizing: border-box;
    transition: all 0.3s ease;
}

html, body, .gradio-container, #root, main, .app, .contain {
    background: #F2ECFF !important;
    min-height: 100vh;
    font-family: Georgia, 'Times New Roman', serif !important;
}

body {
    margin: 0;
    padding: 0;
    color: #000000 !important;
    overflow-x: hidden;
}

/* Override dark mode */
@media (prefers-color-scheme: dark) {
    html, body, .gradio-container, #root, main {
        background: #F2ECFF !important;
        filter: none !important;
    }
}

/* Floating butterflies - glowy white */
.butterfly {
    position: fixed;
    font-size: 28px;
    pointer-events: none;
    z-index: 9999 !important;
    animation: float 25s infinite ease-in-out;
    filter: brightness(0) invert(1);
    text-shadow: 0 0 15px rgba(255, 255, 255, 0.9), 0 0 25px rgba(255, 255, 255, 0.6);
    display: block !important;
    visibility: visible !important;
}

/* Floating hearts - glowy pink */
.heart {
    position: fixed;
    font-size: 28px;
    pointer-events: none;
    z-index: 9999 !important;
    animation: float 25s infinite ease-in-out;
    color: #ff69b4 !important;
    text-shadow: 0 0 15px #ff69b4, 0 0 25px #ff1493, 0 0 35px #ff69b4;
    display: block !important;
    visibility: visible !important;
}

@keyframes float {
    0% {
        transform: translateY(0px) translateX(0px) rotate(0deg);
    }
    25% {
        transform: translateY(-40px) translateX(30px) rotate(5deg);
    }
    50% {
        transform: translateY(-80px) translateX(60px) rotate(-3deg);
    }
    75% {
        transform: translateY(-120px) translateX(90px) rotate(5deg);
    }
    100% {
        transform: translateY(-150px) translateX(120px) rotate(0deg);
        opacity: 0;
    }
}

#main-container {
    max-width: 1400px;
    margin: 0 auto;
    position: relative;
    z-index: 1;
}

.gradio-container {
    background: transparent !important;
    position: relative;
    z-index: 1;
    padding: 20px !important;
}

/* Main container with subtle glow */
#root, main {
    animation: fadeIn 0.6s ease-out !important;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

#chatbot {
    height: 320px;
    background: linear-gradient(145deg, #0a1929 0%, #1a2942 100%) !important;
    border: 2px solid #d0b0ff !important;
    border-radius: 20px !important;
    box-shadow: 0 10px 40px rgba(106, 48, 147, 0.3), 
                inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
}
/* Chatbot label: light blue background (was bright blue) */
#chatbot-column label,
div:has(> #chatbot) > label {
    background: #cce5ff !important;
    color: #1a1a2e !important;
}

#analysis-panel-top {
    background: linear-gradient(135deg, #7642a0 0%, #5a2d7a 100%);
    border-radius: 20px 20px 0 0;
    padding: 25px;
    color: white;
    height: 300px;
    overflow-y: auto;
    box-shadow: 0 10px 40px rgba(106, 48, 147, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-bottom: none;
}

#analysis-panel-top *, #analysis-panel-top .markdown *, .analysis-content {
    color: white !important;
}

.analysis-section {
    margin-bottom: 25px;
}

.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 2px solid rgba(255, 255, 255, 0.2);
}

.section-icon {
    font-size: 24px;
    filter: drop-shadow(0 0 8px rgba(255, 255, 255, 0.3));
}

.section-title {
    font-size: 18px;
    font-weight: 600;
    color: white !important;
    letter-spacing: 0.5px;
}

/* Sentiment Display */
.sentiment-display {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 15px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.1);
}

.sentiment-icon {
    font-size: 48px;
    margin-bottom: 10px;
    filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3));
    animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}

.sentiment-text {
    font-size: 20px;
    font-weight: bold;
    color: white !important;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 12px;
}

.confidence-bar-container {
    width: 100%;
    height: 8px;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 8px;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
}

.confidence-bar {
    height: 100%;
    background: linear-gradient(90deg, #FFF44F 0%, #FFA500 50%, #FF6347 100%);
    border-radius: 10px;
    box-shadow: 0 0 10px rgba(255, 244, 79, 0.5);
    transition: width 0.6s ease;
    animation: shimmer 2s infinite;
}

@keyframes shimmer {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.8; }
}

.confidence-text {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.8) !important;
    font-style: italic;
}

/* Analysis Divider */
.analysis-divider {
    height: 1px;
    background: linear-gradient(90deg, 
        transparent 0%, 
        rgba(255, 255, 255, 0.3) 50%, 
        transparent 100%);
    margin: 20px 0;
}

/* Themes Container */
.themes-container {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.theme-item {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding: 12px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    transition: all 0.3s ease;
}

.theme-item:hover {
    background: rgba(255, 255, 255, 0.15);
    transform: translateX(5px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.theme-name {
    font-size: 15px;
    font-weight: 600;
    color: white !important;
    text-transform: capitalize;
}

.theme-bar-container {
    width: 100%;
    height: 6px;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 10px;
    overflow: hidden;
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.3);
}

.theme-bar {
    height: 100%;
    background: linear-gradient(90deg, #87CEEB 0%, #4169E1 100%);
    border-radius: 10px;
    transition: width 0.6s ease;
    box-shadow: 0 0 8px rgba(135, 206, 235, 0.5);
}

.theme-score {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.7) !important;
    text-align: right;
    font-weight: 600;
}

.no-themes {
    padding: 20px;
    text-align: center;
    color: rgba(255, 255, 255, 0.6) !important;
    font-style: italic;
    font-size: 14px;
}

/* Aesthetic divider between panels */
.panel-divider {
    height: 2px;
    background: linear-gradient(90deg, 
        transparent 0%, 
        rgba(230, 230, 250, 0.3) 10%, 
        rgba(230, 230, 250, 0.8) 50%, 
        rgba(230, 230, 250, 0.3) 90%, 
        transparent 100%);
    margin: 0 !important;
    position: relative;
}

.panel-divider::before {
    content: '✨';
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    font-size: 16px;
    background: #7642a0;
    padding: 5px 10px;
    border-radius: 50px;
    box-shadow: 0 0 15px rgba(230, 230, 250, 0.5);
}

/* Color Panel */
#color-panel {
    background: linear-gradient(135deg, #5a2d7a 0%, #7642a0 100%);
    border-radius: 0 0 20px 20px;
    padding: 25px 25px 45px 25px;
    box-shadow: 0 10px 40px rgba(106, 48, 147, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-top: none;
    min-height: 260px;
}

.color-panel-title, .color-panel-title * {
    color: white !important;
    font-size: 18px !important;
    margin-bottom: 8px !important;
    text-align: center !important;
}

.color-panel-subtitle, .color-panel-subtitle * {
    color: rgba(255, 255, 255, 0.7) !important;
    font-size: 13px !important;
    font-style: italic !important;
    margin-bottom: 15px !important;
    text-align: center !important;
}

.color-picker-row {
    gap: 15px !important;
    margin-bottom: 15px !important;
    justify-content: center !important;
    display: flex !important;
    flex-wrap: wrap !important;
}

/* Color mood buttons - actual color swatches with glow */
.color-btn {
    min-width: 60px !important;
    height: 60px !important;
    cursor: pointer !important;
    border: 3px solid rgba(255, 255, 255, 0.4) !important;
    transition: all 0.3s ease !important;
    position: relative !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2), 
                0 0 20px currentColor,
                inset 0 0 20px rgba(255, 255, 255, 0.3) !important;
    filter: brightness(1.1) !important;
}

.color-btn:hover {
    transform: translateY(-5px) scale(1.08) !important;
    border-color: rgba(255, 255, 255, 0.9) !important;
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3),
                0 0 30px currentColor,
                0 0 50px currentColor,
                inset 0 0 30px rgba(255, 255, 255, 0.5) !important;
    filter: brightness(1.3) !important;
}

/* Add hover labels using ::after */
.color-btn::after {
    content: attr(data-label);
    position: absolute;
    bottom: -35px;
    left: 50%;
    transform: translateX(-50%) scale(0);
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 5px 12px;
    border-radius: 6px;
    font-size: 13px;
    white-space: nowrap;
    opacity: 0;
    transition: all 0.3s ease;
    pointer-events: none;
    z-index: 1000;
}

.color-btn:hover::after {
    transform: translateX(-50%) scale(1);
    opacity: 1;
}

/* Specific color backgrounds with individual glows */
#color-calm-btn, .color-calm { 
    background: #FFFFFF !important;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2), 
                0 0 20px rgba(255, 255, 255, 0.8),
                inset 0 0 20px rgba(255, 255, 255, 0.3) !important;
}
#color-calm-btn:hover {
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3),
                0 0 30px rgba(255, 255, 255, 1),
                0 0 50px rgba(255, 255, 255, 0.8),
                inset 0 0 30px rgba(255, 255, 255, 0.5) !important;
}
#color-calm-btn::after { content: 'Calm'; }

#color-happy-btn, .color-happy { 
    background: #FFF44F !important;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2), 
                0 0 20px rgba(255, 244, 79, 0.6),
                inset 0 0 20px rgba(255, 255, 255, 0.3) !important;
}
#color-happy-btn:hover {
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3),
                0 0 30px rgba(255, 244, 79, 0.9),
                0 0 50px rgba(255, 244, 79, 0.6),
                inset 0 0 30px rgba(255, 255, 255, 0.5) !important;
}
#color-happy-btn::after { content: 'Happy'; }

#color-energetic-btn, .color-energetic { 
    background: #FF6347 !important;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2), 
                0 0 20px rgba(255, 99, 71, 0.6),
                inset 0 0 20px rgba(255, 255, 255, 0.3) !important;
}
#color-energetic-btn:hover {
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3),
                0 0 30px rgba(255, 99, 71, 0.9),
                0 0 50px rgba(255, 99, 71, 0.6),
                inset 0 0 30px rgba(255, 255, 255, 0.5) !important;
}
#color-energetic-btn::after { content: 'Energetic'; }

#color-anxious-btn, .color-anxious { 
    background: #9370DB !important;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2), 
                0 0 20px rgba(147, 112, 219, 0.6),
                inset 0 0 20px rgba(255, 255, 255, 0.3) !important;
}
#color-anxious-btn:hover {
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3),
                0 0 30px rgba(147, 112, 219, 0.9),
                0 0 50px rgba(147, 112, 219, 0.6),
                inset 0 0 30px rgba(255, 255, 255, 0.5) !important;
}
#color-anxious-btn::after { content: 'Anxious'; }

#color-sad-btn, .color-sad { 
    background: #4169E1 !important;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2), 
                0 0 20px rgba(65, 105, 225, 0.6),
                inset 0 0 20px rgba(255, 255, 255, 0.3) !important;
}
#color-sad-btn:hover {
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3),
                0 0 30px rgba(65, 105, 225, 0.9),
                0 0 50px rgba(65, 105, 225, 0.6),
                inset 0 0 30px rgba(255, 255, 255, 0.5) !important;
}
#color-sad-btn::after { content: 'Sad'; }

#color-angry-btn, .color-angry { 
    background: #DC143C !important;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2), 
                0 0 20px rgba(220, 20, 60, 0.6),
                inset 0 0 20px rgba(255, 255, 255, 0.3) !important;
}
#color-angry-btn:hover {
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3),
                0 0 30px rgba(220, 20, 60, 0.9),
                0 0 50px rgba(220, 20, 60, 0.6),
                inset 0 0 30px rgba(255, 255, 255, 0.5) !important;
}
#color-angry-btn::after { content: 'Angry'; }

.color-status {
    text-align: center !important;
    color: rgba(255, 255, 255, 0.9) !important;
    margin-top: 20px !important;
    font-size: 15px !important;
    padding: 12px !important;
    background: rgba(255, 255, 255, 0.15) !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
}

.color-status * {
    color: white !important;
}

.color-status span {
    color: white !important;
}

.color-status strong {
    color: white !important;
    font-weight: bold !important;
}

/* Tabs styling */
.tabs {
    background: rgba(255, 255, 255, 0.5) !important;
    border-radius: 15px !important;
    padding: 5px !important;
    box-shadow: 0 4px 15px rgba(147, 112, 219, 0.1) !important;
    overflow: hidden !important;
}

button[role="tab"] {
    color: #4a1f6e !important;
    font-weight: 600 !important;
    font-size: 17px !important;
    padding: 12px 24px !important;
    border-radius: 10px !important;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
    position: relative !important;
}

button[role="tab"]:hover {
    background: rgba(147, 112, 219, 0.1) !important;
    transform: translateY(-2px) !important;
}

button[role="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #7642a0 0%, #9370DB 100%) !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(118, 66, 160, 0.4) !important;
    transform: scale(1.02) !important;
}

/* Smooth tab content transitions */
.tabitem, [role="tabpanel"] {
    animation: fadeInScale 0.5s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

@keyframes fadeInScale {
    0% {
        opacity: 0;
        transform: scale(0.98) translateY(10px);
    }
    100% {
        opacity: 1;
        transform: scale(1) translateY(0);
    }
}

/* Add slide effect on tab change */
.tabs > div[role="tablist"] + * {
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.message-user, .message-bot {
    color: #ffffff !important;
    padding: 14px 18px !important;
    border-radius: 18px !important;
    font-size: 16px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    animation: slideIn 0.3s ease-out !important;
}

.message-user {
    background: linear-gradient(135deg, #1a2942 0%, #253a5c 100%) !important;
    box-shadow: 0 4px 12px rgba(26, 41, 66, 0.4) !important;
}

.message-bot {
    background: linear-gradient(135deg, #0f1c2e 0%, #1a2942 100%) !important;
    box-shadow: 0 4px 12px rgba(15, 28, 46, 0.4) !important;
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}


input, textarea {
    background-color: #ffffff !important;
    color: #000000 !important;
    border: 2px solid #d0b0ff !important;
    border-radius: 24px !important;
    padding: 12px 18px !important;
    -webkit-text-fill-color: #000000 !important;
    box-shadow: none !important;
}

#input-row input, #input-row textarea {
    height: 48px !important;
    min-height: 48px !important;
    border-radius: 24px !important;
}

input::placeholder, textarea::placeholder {
    color: #cccccc !important;
    opacity: 1 !important;
}

/* Focus: keep nice purple outline, no thick glow */
textarea:focus, input:focus {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    border: 2px solid #9370DB !important;
    box-shadow: none !important;
    outline: none !important;
}

/* Remove the black/dark box around textbox - target wrapper and all container divs, not the input */
#input-row > *:first-child,
#input-row > *:first-child div {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
/* Keep the nice 2px purple curved outline on the actual textbox */
#input-row input,
#input-row textarea {
    border: 2px solid #d0b0ff !important;
    box-shadow: none !important;
}
#input-row textarea:focus,
#input-row input:focus {
    border: 2px solid #9370DB !important;
}

button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 10px 20px !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
    cursor: pointer !important;
}

button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6) !important;
}

/* Send button in input row - cleaner style */
#input-row button[variant="primary"] {
    border-radius: 50px !important;
    padding: 12px 24px !important;
    min-width: 80px !important;
    height: 48px !important;
}

#quit-btn {
    background: linear-gradient(135deg, #FFB6C1 0%, #FF91B4 100%) !important;
    color: #000000 !important;
    box-shadow: 0 4px 15px rgba(255, 182, 193, 0.4) !important;
}

#quit-btn:hover {
    box-shadow: 0 6px 20px rgba(255, 182, 193, 0.6) !important;
}

/* Microphone audio input: only the "Voice Input (Click to record...)" label is light blue */
#mic-input {
    margin-top: 10px !important;
    border: 2px solid #d0b0ff !important;
    border-radius: 12px !important;
    padding: 15px !important;
    background: transparent !important;
}

/* Hide Gradio's giant music/note icon - keep just the label text and Record button */
#mic-input svg {
    display: none !important;
}
/* Restore the close (X) icon - it's an SVG inside a button */
#mic-input button svg {
    display: inline-block !important;
    visibility: visible !important;
}

/* No black borders - use subtle purple everywhere in voice input */
#mic-input * {
    border-color: #b8a0e0 !important;
}

#mic-input label {
    background: #cce5ff !important;
    color: #2d3748 !important;
    font-weight: 600 !important;
    margin-bottom: 10px !important;
    padding: 8px 14px !important;
    border-radius: 8px !important;
    display: inline-block !important;
}

#mic-input button {
    background: linear-gradient(135deg, #e8e0f5 0%, #d8d0e8 100%) !important;
    color: #2d3748 !important;
    border: 1px solid #b8a0e0 !important;
    border-radius: 8px !important;
    padding: 8px 16px !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    text-align: center !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

#mic-input button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 14px rgba(147, 112, 219, 0.3) !important;
}

/* Input row styling - WhatsApp inspired */
#input-row {
    gap: 10px !important;
    align-items: center !important;
    margin-top: 10px !important;
    display: flex !important;
}

#input-row > * {
    margin: 0 !important;
}

/* Title header styling */
#title-header {
    background: linear-gradient(135deg, rgba(147, 112, 219, 0.1) 0%, rgba(230, 230, 250, 0.2) 100%);
    border-radius: 20px;
    padding: 30px;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px rgba(147, 112, 219, 0.15);
    border: 1px solid rgba(147, 112, 219, 0.2);
}

/* Glowy dark purple title - only h1 */
#title-header h1 {
    font-family: 'Courgette', cursive !important;
    color: #4a1f6e !important;
    text-shadow: 0 0 20px rgba(74, 31, 110, 0.8),
                 0 0 40px rgba(74, 31, 110, 0.5),
                 0 0 60px rgba(74, 31, 110, 0.3);
    font-size: 52px !important;
    margin-bottom: 10px !important;
    font-weight: bold !important;
    font-style: normal !important;
    letter-spacing: 1px !important;
}

/* Regular subtitle text - no glow */
#title-header h3, #title-header p {
    font-family: Georgia, 'Times New Roman', serif !important;
    color: #4a1f6e !important;
    text-shadow: none !important;
    font-size: 18px !important;
    font-style: italic !important;
}

/* Tips and Stats section styling */
.tips-section, .stats-section {
    background: rgba(200, 180, 230, 0.35) !important;
    padding: 18px !important;
    border-radius: 15px !important;
    border: 1px solid rgba(147, 112, 219, 0.3) !important;
    box-shadow: 0 4px 15px rgba(147, 112, 219, 0.15) !important;
}

.stats-section {
    margin-top: 15px !important;
}

.tips-section *, .stats-section * {
    color: #4a1f6e !important;
}

.history-section * {
    color: #8B5FC7 !important;
}

.weekly-wrap-section * {
    color: #C44FC1 !important;
}

/* Top bar: stats (fixed size) | login (extends to fill rest) */
#top-bar-row {
    display: flex !important;
    flex-wrap: nowrap !important;
    gap: 12px !important;
    align-items: stretch !important;
}
#top-bar-row > * {
    flex: 0 1 auto !important;
    max-width: 380px !important;
    min-width: 0 !important;
}
#login-bar-wrap {
    flex: 1 1 auto !important;
    max-width: none !important;
    min-width: 220px !important;
}
.stats-bar-box, .login-bar, #stats-bar-left-wrap, #login-bar-wrap {
    background: linear-gradient(135deg, #7a4a9e 0%, #9b6bb8 100%) !important;
    padding: 12px 18px !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 18px rgba(74, 31, 110, 0.35),
                inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #ffffff !important;
    font-size: 14px !important;
}
#stats-bar-left-wrap {
    max-width: 380px !important;
    width: auto !important;
    min-width: 200px !important;
}
#login-bar-wrap { width: auto !important; }
#stats-bar-left-wrap *, #login-bar-wrap *, .stats-bar-box *, .login-bar * {
    color: #ffffff !important;
}
.login-bar a {
    color: #e0c4ff !important;
    font-weight: 600;
    text-decoration: underline;
}
#logout-btn { margin-left: 8px; }

footer {
    display: none !important;
}

/* Custom scrollbar styling */
::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}

::-webkit-scrollbar-track {
    background: rgba(147, 112, 219, 0.1);
    border-radius: 5px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #9370DB 0%, #7642a0 100%);
    border-radius: 5px;
    border: 2px solid rgba(255, 255, 255, 0.1);
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #7642a0 0%, #6a3093 100%);
}
"""


def format_entry_for_display(entry):
    """Format a single day's journal entry for display"""
    themes_str = ", ".join(entry['themes']) if entry['themes'] else "No themes"
    message_count = len(entry['conversation'])
    
    # Get mood color info if available
    mood_display = ""
    if entry.get('mood_color'):
        mood_name = entry['mood_color'].split(':')[0]
        mood_info = MOOD_COLORS.get(mood_name, {})
        mood_name_display = mood_info.get('name', mood_name.title())
        mood_color_hex = mood_info.get('color', '#FFFFFF')
        mood_display = f' | <span style="display: inline-flex; align-items: center; gap: 5px; vertical-align: middle;"><strong>Mood:</strong> <span style="display: inline-block; width: 15px; height: 15px; background: {mood_color_hex}; border-radius: 50%; border: 1px solid rgba(0,0,0,0.2); box-shadow: 0 0 8px {mood_color_hex};"></span>{mood_name_display}</span>'
    
    # Build conversation display
    conversation_html = f"""
### {entry['entry_date']} ({message_count} messages)
**Sentiment:** {entry['sentiment']} | **Themes:** {themes_str}{mood_display}

"""
    
    for i, msg in enumerate(entry['conversation'], 1):
        conversation_html += f"""
**You:** {msg['user']}

**Luna:** {msg['luna']}

---
"""
    
    return conversation_html

def load_history():
    """Load and display all entries"""
    entries = db.get_all_entries(limit=50)
    
    if not entries:
        return "No entries yet. Start journaling to see your history here!"
    
    history_text = f"## Your Journal History ({len(entries)} days)\n\n"
    
    for entry in entries:
        history_text += format_entry_for_display(entry)
    
    return history_text

def search_history(search_term):
    """Search entries by date or content"""
    if not search_term.strip():
        return load_history()
    
    entries = db.search_entries(search_term)
    
    if not entries:
        return f"No entries found matching '{search_term}'"
    
    history_text = f"## Search Results for '{search_term}' ({len(entries)} days)\n\n"
    
    for entry in entries:
        history_text += format_entry_for_display(entry)
    
    return history_text

def get_weekly_entries():
    """Get entries from the past 7 days (only entries with actual journal content)"""
    conn = sqlite3.connect(db.DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, entry_date, conversation, overall_sentiment, sentiment_score, themes, mood_color, created_at
        FROM entries
        WHERE entry_date >= date('now', '-7 days')
        AND conversation != '[]'
        ORDER BY entry_date DESC
    """)
    
    entries = []
    for row in cursor.fetchall():
        entries.append({
            'id': row[0],
            'entry_date': row[1],
            'conversation': json.loads(row[2]),
            'sentiment': row[3],
            'sentiment_score': row[4],
            'themes': json.loads(row[5]) if row[5] else [],
            'mood_color': row[6],
            'created_at': row[7]
        })
    
    conn.close()
    return entries

def generate_weekly_wrap():
    """Generate a weekly wrap-up of gratitude and learnings"""
    entries = get_weekly_entries()
    
    if not entries:
        return """
<div style="text-align: center; padding: 40px 20px;">

# 💗 Weekly Wrap 💗

<div style="font-size: 48px; margin: 30px 0;">✍🏼</div>

### No entries found for the past 7 days

<div style="margin: 30px 0; padding: 20px; background: rgba(147, 112, 219, 0.1); border-radius: 15px; border: 1px solid rgba(147, 112, 219, 0.3);">

**Start journaling to see your weekly wrap-up here!**

</div>

*Tip: Journal for at least 3-4 days this week to get meaningful insights!*

</div>
"""
    
    # Compile all conversations from the week
    all_messages = []
    for entry in entries:
        for msg in entry['conversation']:
            all_messages.append(f"**Date: {entry['entry_date']}**\nYou: {msg['user']}\nLuna: {msg['luna']}\n")
    
    week_text = "\n".join(all_messages)
    
    # Use Llama to analyze and extract gratitude and learnings
    try:
        prompt = f"""Analyze the following week of journal entries and create a warm, personalized weekly wrap-up.

Extract and summarize:
1. Things the user expressed gratitude for
2. New things they learned or insights they gained

Journal entries from the past week:

{week_text}

Format your response as:

## Gratitude This Week
[List the things they were grateful for, with brief context]

## What You Learned
[List new insights, learnings, or realizations they had]

## Reflection
[A short, warm reflection on their week - 2-3 sentences]

Be specific and personal. Quote or paraphrase their own words where relevant."""

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are Luna, an empathetic journaling companion. Analyze journal entries and create thoughtful weekly summaries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        wrap_content = response.choices[0].message.content
        
        # Check if response contains placeholder text (means not enough content to analyze)
        if "[List" in wrap_content or "[A short" in wrap_content:
            days_text = "day" if len(entries) == 1 else "days"
            return f"""
<div style="text-align: center; padding: 40px 20px;">

# 💗 Weekly Wrap 💗

### {entries[-1]['entry_date']} to {entries[0]['entry_date']}
*{len(entries)} {days_text} journaled this week*

<div style="font-size: 48px; margin: 30px 0;">✍️</div>

<div style="margin: 30px 0; padding: 20px; background: rgba(147, 112, 219, 0.1); border-radius: 15px; border: 1px solid rgba(147, 112, 219, 0.3);">

**Not enough content to generate insights yet**

Your journal entries this week are a great start! However, we need a bit more content to create meaningful patterns and insights.

</div>

*Tip: Try to journal for at least 100 words per day for richer insights!*

</div>
"""
        
        # Add header
        days_text = "day" if len(entries) == 1 else "days"
        header = f"""# 💗 Weekly Wrap 💗
*{entries[-1]['entry_date']} to {entries[0]['entry_date']}*
*{len(entries)} {days_text} journaled this week*

---

"""
        return header + wrap_content
        
    except Exception as e:
        print(f"Error generating weekly wrap: {e}")
        return f"""
<div style="text-align: center; padding: 40px 20px;">

# 💗 Weekly Wrap 💗

<div style="font-size: 48px; margin: 30px 0;">⚠️</div>

### Couldn't generate analysis

<div style="margin: 30px 0; padding: 20px; background: rgba(220, 20, 60, 0.1); border-radius: 15px; border: 1px solid rgba(220, 20, 60, 0.3);">

Found **{len(entries)}** days of entries, but couldn't generate the weekly wrap.

**Possible reasons:**
- API connection issue
- Service temporarily unavailable
- Rate limit reached

**What to do:**
- Click the refresh button to try again
- Check your internet connection
- Try again in a few minutes

</div>

*Error details: {str(e)}*

</div>
"""

# Lavender look: head HTML (butterflies, ripple, background) — also passed to mount_gradio_app when OAuth is on
custom_head = """
    <style>
        /* Force lavender background everywhere */
        body, html, .gradio-container, #root, main {
            background: #E6E6FA !important;
            background-color: #E6E6FA !important;
        }
    </style>
    <script>
        function createButterflies() {
            const container = document.body;
            
            // Create mix of butterflies and hearts (6 butterflies, 3 hearts)
            for (let i = 0; i < 9; i++) {
                const element = document.createElement('div');
                
                // Every 3rd item is a heart, rest are butterflies
                if (i % 3 === 0) {
                    element.className = 'heart';
                    element.innerHTML = '&#x2665;'; // Heart symbol
                } else {
                    element.className = 'butterfly';
                    element.innerHTML = '&#x1F98B;'; // Butterfly emoji
                }
                
                element.style.left = Math.random() * 100 + '%';
                element.style.top = Math.random() * 100 + '%';
                element.style.animationDelay = Math.random() * 10 + 's';
                element.style.animationDuration = (15 + Math.random() * 10) + 's';
                element.style.opacity = 0.8 + Math.random() * 0.2;
                container.appendChild(element);
            }
        }
        
        // Create butterflies and hearts when page loads
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', createButterflies);
        } else {
            createButterflies();
        }
        
        // Enhanced tab switching with smooth transitions
        function initSmoothTabs() {
            // Wait for tabs to be rendered
            setTimeout(() => {
                const tabs = document.querySelectorAll('button[role="tab"]');
                const tabPanels = document.querySelectorAll('[role="tabpanel"]');
                
                if (tabs.length === 0) return;
                
                tabs.forEach((tab, index) => {
                    tab.addEventListener('click', () => {
                        // Add ripple effect on click
                        const ripple = document.createElement('span');
                        ripple.style.position = 'absolute';
                        ripple.style.width = '100%';
                        ripple.style.height = '100%';
                        ripple.style.background = 'rgba(255, 255, 255, 0.3)';
                        ripple.style.borderRadius = '10px';
                        ripple.style.top = '0';
                        ripple.style.left = '0';
                        ripple.style.animation = 'ripple 0.6s ease-out';
                        ripple.style.pointerEvents = 'none';
                        tab.style.position = 'relative';
                        tab.appendChild(ripple);
                        
                        setTimeout(() => ripple.remove(), 600);
                        
                        // Smooth scroll to top when switching tabs
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                    });
                });
                
                // Add ripple animation
                const style = document.createElement('style');
                style.textContent = `
                    @keyframes ripple {
                        0% {
                            transform: scale(0);
                            opacity: 1;
                        }
                        100% {
                            transform: scale(2);
                            opacity: 0;
                        }
                    }
                `;
                document.head.appendChild(style);
            }, 500);
        }
        
        // Initialize smooth tabs
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initSmoothTabs);
        } else {
            initSmoothTabs();
        }
        
        // Fix Voice Input: Gradio shows two "Stop" buttons; relabel the second one as "Clear"
        function fixMicInputLabels() {
            const mic = document.getElementById('mic-input');
            if (!mic) return;
            const buttons = mic.querySelectorAll('button');
            let stopCount = 0;
            buttons.forEach(btn => {
                const text = (btn.textContent || '').trim();
                if (text === 'Stop') {
                    stopCount++;
                    if (stopCount === 2) {
                        btn.textContent = 'Clear';
                    }
                }
            });
        }
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => setTimeout(fixMicInputLabels, 800));
        } else {
            setTimeout(fixMicInputLabels, 800);
        }
        
    </script>
"""

# Build Gradio interface
with gr.Blocks(
    title="AI Journaling Companion",
    css=custom_css,
    theme=gr.themes.Soft(),
    head=custom_head,
) as demo:
    
    gr.Markdown("""
    <div id="title-header">
    
    # Luna - your new bestie <3
    ### Your empathetic space for reflection and growth
    
    Write about your day, thoughts, or feelings. Luna will listen, analyze, and respond with care.
    
    </div>
    """, elem_id="title-header")
    
    
    # We need to define history_display first so it can be referenced in journal tab
    # Create it as a placeholder, will be properly set up in the View History tab
    with gr.Tabs() as tabs:
        # Define Journal Chat tab
        with gr.TabItem("Journal Chat") as journal_tab:
            # Top bar: two physical bars – left = stats, right = login (+ logout when logged in)
            with gr.Row(elem_id="top-bar-row"):
                stats_bar_display = gr.Markdown(
                    value=format_stats_bar(),
                    elem_id="stats-bar-left-wrap"
                )
                with gr.Column(elem_id="login-bar-wrap"):
                    login_display = gr.HTML(value=get_login_html(), elem_id="login-bar-inner")
                    logout_btn = gr.Button("Logout", visible=bool(_current_user["email"]), elem_id="logout-btn")
            logout_btn.click(logout_user, outputs=[login_display, logout_btn])

            def refresh_login():
                return get_login_html(), gr.update(visible=bool(_current_user["email"]))
            demo.load(refresh_login, outputs=[login_display, logout_btn])

            with gr.Row(elem_id="main-container"):
                # Left column - Chat
                with gr.Column(scale=2, elem_id="chatbot-column"):
                    chatbot = gr.Chatbot(
                        elem_id="chatbot",
                        label="Conversation (Luna's Replies)",
                        height=320
                    )
                    
                    with gr.Row(elem_id="input-row"):
                        msg = gr.Textbox(
                            placeholder="Write your journal entry here...",
                            show_label=False,
                            scale=10,
                            lines=1,
                            max_lines=1
                        )
                        submit_btn = gr.Button("Send", scale=2, variant="primary")
                    
                    mic_btn = gr.Audio(
                        sources=["microphone"],
                        type="filepath",
                        label="🎤 Voice Input (Click to record, click again to stop)",
                        show_label=True,
                        elem_id="mic-input",
                        streaming=False
                    )
                    
                    gr.Markdown("""
                    **Tips:** 
                    - Share your thoughts freely. This is a judgment-free space :)
                    - No need to worry about grammar or structure
                    - 🎤 Too tired to type? Use voice input above to record your thoughts!
                    """, elem_classes="tips-section")
                
                # Right column - Analysis
                with gr.Column(scale=1):
                    # Analysis Panel (Top Half)
                    analysis_display = gr.Markdown(
                        """
                        <div class="analysis-content">
                        <div class="analysis-section">
                        <div class="section-header">
                        <span class="section-icon">✨</span>
                        <span class="section-title">Analysis Panel</span>
                        </div>
                        <div style="padding: 30px 20px; text-align: center;">
                        <div style="font-size: 48px; margin-bottom: 15px;">🔮</div>
                        <div style="font-size: 16px; color: rgba(255, 255, 255, 0.9); margin-bottom: 10px;">
                        <strong>Write your first entry to see the magic!</strong>
                        </div>
                        <div style="font-size: 14px; color: rgba(255, 255, 255, 0.7); font-style: italic;">
                        I'll analyze your:
                        </div>
                        <div style="margin-top: 15px; display: flex; flex-direction: column; gap: 8px; align-items: center;">
                        <div style="color: rgba(255, 255, 255, 0.8);">🎭 Sentiment & Emotions</div>
                        <div style="color: rgba(255, 255, 255, 0.8);">🏷️ Themes & Topics</div>
                        <div style="color: rgba(255, 255, 255, 0.8);">💭 Emotional Patterns</div>
                        </div>
                        </div>
                        </div>
                        </div>
                        """,
                        elem_id="analysis-panel-top"
                    )
                    
                    # Aesthetic Divider
                    gr.Markdown("""<div class="panel-divider"></div>""")
                    
                    # Color Panel (Bottom Half)
                    with gr.Column(elem_id="color-panel"):
                        gr.Markdown("### Today's Mood Palette", elem_classes="color-panel-title")
                        gr.Markdown("*Too tired to write? Pick a color that reflects your mood today*", elem_classes="color-panel-subtitle")
                        
                        # Color picker with preset mood colors
                        with gr.Row(elem_classes="color-picker-row"):
                            color_calm = gr.Button("", elem_classes="color-btn color-calm", variant="secondary", elem_id="color-calm-btn")
                            color_happy = gr.Button("", elem_classes="color-btn color-happy", variant="secondary", elem_id="color-happy-btn")
                            color_energetic = gr.Button("", elem_classes="color-btn color-energetic", variant="secondary", elem_id="color-energetic-btn")
                        
                        with gr.Row(elem_classes="color-picker-row"):
                            color_anxious = gr.Button("", elem_classes="color-btn color-anxious", variant="secondary", elem_id="color-anxious-btn")
                            color_sad = gr.Button("", elem_classes="color-btn color-sad", variant="secondary", elem_id="color-sad-btn")
                            color_angry = gr.Button("", elem_classes="color-btn color-angry", variant="secondary", elem_id="color-angry-btn")
                        
                        color_status = gr.Markdown(value=get_mood_status(), elem_classes="color-status")
                    
                    stats_sidebar_display = gr.Markdown(
                        value=format_stats_sidebar(),
                        elem_classes="stats-section"
                    )
        
        # Define View History tab
        with gr.TabItem("View History"):
            gr.Markdown("## View Your Past Entries", elem_classes="history-section")
            
            with gr.Row():
                search_box = gr.Textbox(
                    placeholder="Search your entries...",
                    label="Search",
                    scale=4
                )
                search_btn = gr.Button("Search", scale=1)
                refresh_btn = gr.Button("Refresh", scale=1)
            
            history_display = gr.Markdown(
                value=load_history(),
                label="Your Entries",
                elem_classes="history-section"
            )
            
            # Event handlers for history tab
            search_btn.click(search_history, inputs=search_box, outputs=history_display)
            refresh_btn.click(load_history, outputs=history_display)
            search_box.submit(search_history, inputs=search_box, outputs=history_display)
        
        # Define Weekly Wrap tab
        with gr.TabItem("Weekly Wrap"):
            gr.Markdown("""
            ## Your Weekly Summary
            
            Get a personalized wrap-up of your gratitude moments and learnings from the past week.
            """, elem_classes="weekly-wrap-section")
            
            weekly_refresh_btn = gr.Button("🔄 Refresh Weekly Wrap", variant="primary", scale=1)
            
            weekly_wrap_display = gr.Markdown(
                value=generate_weekly_wrap(),
                elem_classes="weekly-wrap-section"
            )
            
            # Event handler for weekly wrap
            weekly_refresh_btn.click(generate_weekly_wrap, outputs=weekly_wrap_display)
    
    # Event handler for microphone - transcribe audio to text
    mic_btn.change(transcribe_audio, inputs=mic_btn, outputs=msg)
    
    # Event handlers for journal tab - now also updates history and stats
    msg.submit(chat_interface, [msg, chatbot], [chatbot, analysis_display, history_display, stats_bar_display, stats_sidebar_display])
    submit_btn.click(chat_interface, [msg, chatbot], [chatbot, analysis_display, history_display, stats_bar_display, stats_sidebar_display])
    
    # Clear message box after submission
    msg.submit(lambda: "", None, msg)
    submit_btn.click(lambda: "", None, msg)
    
    # Event handlers for color panel
    color_happy.click(lambda: save_mood_color_handler('happy'), outputs=color_status)
    color_calm.click(lambda: save_mood_color_handler('calm'), outputs=color_status)
    color_sad.click(lambda: save_mood_color_handler('sad'), outputs=color_status)
    color_energetic.click(lambda: save_mood_color_handler('energetic'), outputs=color_status)
    color_anxious.click(lambda: save_mood_color_handler('anxious'), outputs=color_status)
    color_angry.click(lambda: save_mood_color_handler('angry'), outputs=color_status)

# Mount on FastAPI when Google OAuth enabled (so we can handle /login/callback)
if _google_oauth_available:
    from fastapi import FastAPI
    from fastapi.responses import RedirectResponse

    app = FastAPI()

    @app.get("/login/callback")
    def login_callback(code: str = None):
        if not code:
            return RedirectResponse(url="/")
        try:
            redirect_uri = get_redirect_uri()
            creds = drive_storage.exchange_code_for_credentials(code, redirect_uri)
            local_path, upload_cb = drive_storage.get_or_create_db_file(creds)
            db.set_db_path(local_path)
            db.set_after_commit(upload_cb)
            db.init_database()
            _current_user["email"] = drive_storage.get_user_email(creds)
            _current_user["upload_cb"] = upload_cb
        except Exception as e:
            print(f"Login error: {e}")
        return RedirectResponse(url="/")

    app = gr.mount_gradio_app(
        app, demo, path="/",
        theme=gr.themes.Soft(),
        css=custom_css,
        head=custom_head,
    )
else:
    app = demo.app

# Launch the app
if __name__ == "__main__":
    print("\n" + "="*70)
    print("Launching Luna (AI Journaling Companion)")
    print("="*70)
    if _google_oauth_available:
        print("Google login enabled — sign in to save your journal to Drive.")
    else:
        print("Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env to enable login.")
    print("="*70)

    port = int(os.environ.get("PORT", 7860))
    if _google_oauth_available:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        demo.launch(server_name="0.0.0.0", server_port=port, share=False)
