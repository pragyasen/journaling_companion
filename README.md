---
title: Luna - Journaling Companion
sdk: gradio
sdk_version: "4.36.1"
app_file: app.py
python_version: "3.12"
---

# Luna - AI-Powered Journaling Companion

<div align="center">

**An empathetic, intelligent journaling companion that transforms self-reflection into an insightful daily habit.**

[Live Demo](https://pragyasen1-luna-journal.hf.space) • [Video Walkthrough](https://drive.google.com/file/d/1hRYcYVOpQV6rhR5Sbj0yOXuftj3XGs5z/view?usp=sharing) • [Documentation](DOCUMENTATION.md)

</div>

---

## 🎯 Problem Statement

While the mental health benefits of journaling are well-documented, many people struggle with:
- **Blank page anxiety** - not knowing what to write
- **Lack of structure** - random thoughts without meaningful reflection
- **No insights** - unable to identify patterns in emotions and behaviors
- **Inconsistency** - difficulty maintaining a daily habit

**Luna solves these problems** by providing intelligent guidance, automatic analysis, quick options and personalized insights.

---

## ✨ Key Features

### 1. Conversational AI Journaling
- Dynamic, context-aware prompts using **Llama 3.3 70B**
- Guided journaling flow through 6 categories:
  - Factual Account → Self Reflection → Gratitude → Learning → Future Self → Intention Setting
- Empathetic responses that encourage deeper reflection

### 2. Advanced Sentiment Analysis
- Real-time emotional analysis using **CardiffNLP RoBERTa**
- Confidence scoring with visual progress bars
- Tracks sentiment trends over time (Positive, Neutral, Negative)

### 3. Privacy-First Design
- **SQLite database:** When app is run locally, data stays in a SQLite file on your device.
- On Hugging Face demo:
  1. **Logged-in via Google:** SQLite file gets saved in the user's Google Drive
  2. **Without log-in:** SQLite file on the Space’s server (session-only; it may not persist across restarts)
- **Minimal data leaving your device:** Your journal text is only sent where needed for AI features (e.g. Groq for chat and voice, Hugging Face for sentiment and themes). When you use the HF demo without logging in, that data is processed on the Space’s servers.
- **Daily conversation grouping:** Entries are grouped by day so you can browse and reflect day by day.

### 4. Automatic Theme Detection
- Zero-shot classification with **BART-MNLI**
- Identifies recurring themes: Work, Relationships, Health, Personal Growth, Creativity, Goals
- Visual theme cards with relevance scoring

### 5. Weekly Wrap Feature
- AI-generated summaries using **Llama 3.3**
- Highlights gratitude moments and key learnings
- Personalized reflections on emotional journey

### 6. Voice-to-Text Journaling
- **Groq Whisper Large v3** transcription
- Perfect for hands-free journaling
- Auto-populates text input for editing before sending

### 7. Mood Color Palette
- Quick visual mood tracking for busy days
- 6 mood colors: Happy, Calm, Sad, Energetic, Anxious, Angry
- Integrated with journal history

### 8. Statistics
- Daily statistics and journaling streaks
- Sentiment distribution visualization
- Weekly engagement metrics

---

## 🎥 Video Demo

> Video demonstration available at: [Add your video link here]

*A 5-7 minute walkthrough showcasing all features, UI/UX design decisions and technical implementation.*

---

## 🌐 Live Demo

**Try it here:** [https://pragyasen1-luna-journal.hf.space/](https://pragyasen1-luna-journal.hf.space/)

⏱️ *First load may take 30-60 seconds as the Space wakes up (free tier of Hugging Face used). Models are cached after initial download.*

---

## 🏗️ Architecture & Tech Stack

### AI Models
- **Llama 3.3 70B Versatile** - Conversational AI and prompt generation
- **CardiffNLP RoBERTa** - Sentiment analysis (twitter-roberta-base-sentiment-latest)
- **Facebook BART-Large-MNLI** - Zero-shot theme classification
- **Whisper Large v3** - Speech-to-text transcription

### Infrastructure
- **Backend**: Python 3.10+
- **UI Framework**: Gradio 6.0
- **Database**: SQLite with JSON storage for conversations
- **ML Framework**: PyTorch, Transformers (Hugging Face)
- **API**: Groq Cloud for optimized LLM inference

### Design Highlights
- **Custom CSS**: Lavender theme with animated butterflies and hearts
- **Responsive Layout**: Split-view interface (chat + analysis panel)
- **Multi-tab Navigation**: Smooth transitions between Journal, History and Weekly Wrap

---

## 🚀 Local Setup

### Prerequisites
- Python 3.10 or higher
- Groq API key ([Get one here](https://console.groq.com))

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/luna-journal.git
cd luna-journal

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
# Add GROQ_API_KEY to a .env file

# Run the application
python app.py
```

The app will be available at `http://localhost:7860`

---

## 📖 Usage Guide

### Basic Journaling Flow
1. **Start Writing**: Type or speak your thoughts
2. **AI Response**: Luna guides you through reflective questions (Takes 6 categories into consideration)
3. **View Analysis**: Check sentiment, themes and patterns in real-time
4. **Track Mood**: Select a mood color if too tired to write
5. **Review History**: Browse past entries by date
6. **Weekly Insights**: Generate AI summaries of your week

### Voice Input
1. Click "Record" button
2. Speak your journal entry
3. Click "Stop recording"
4. Edit transcribed text if needed
5. Click "Send"

---

## 🔬 Technical Implementation Details

### Prompt Engineering
The journaling flow is implemented entirely through **prompt engineering** (no fine-tuning):
- Structured system prompts guide conversation flow
- Context-aware follow-up questions
- Category-specific triggers

### Database Schema
```sql
entries (
    id INTEGER PRIMARY KEY,
    entry_date TEXT,
    conversation JSON,  -- List of {user_message, ai_response}
    overall_sentiment TEXT,
    sentiment_score REAL,
    themes JSON,
    mood_color TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### Daily Conversation Grouping
- All messages from a single day are stored as one entry
- Enables coherent daily narratives
- Simplifies weekly analysis

---

## 📊 Project Statistics

- **AI Models Used**: 4 (Llama, RoBERTa, BART, Whisper)
- **Features Implemented**: 8 major features

---

## 🎨 UI/UX Design Decisions

1. **Lavender Color Scheme**: Calming, associated with mental wellness (also my favorite color :P)
2. **Animated Elements**: Subtle butterflies and hearts for positive reinforcement
3. **Glass Morphism**: Modern, non-intrusive panels
4. **Single-line Input**: Encourages focused, thoughtful entries
5. **Visual Feedback**: Confidence bars, progress indicators, glow effects

---

## 🔮 Future Enhancements

- [ ] Mobile app
- [ ] Integration with calendar apps
- [ ] Encrypted cloud backup
