---
title: Luna - Journaling Companion
emoji: 📔
colorFrom: purple
colorTo: indigo
sdk: gradio
sdk_version: "4.36.1"
app_file: app.py
pinned: false
python_version: "3.12"
---

# Luna - AI-Powered Journaling Companion ✍️

<div align="center">

**An empathetic, intelligent journaling companion that transforms self-reflection into an insightful daily habit.**

[![Live Demo](https://img.shields.io/badge/🌐_Live_Demo-Hugging_Face-yellow)](https://huggingface.co/spaces/pragyasen1/luna-journal)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[Live Demo](https://huggingface.co/spaces/pragyasen1/luna-journal) • [Video Walkthrough](#video-demo) • [Documentation](#documentation)

</div>

---

## 🎯 Problem Statement

While the mental health benefits of journaling are well-documented, many people struggle with:
- **Blank page anxiety** - not knowing what to write
- **Lack of structure** - random thoughts without meaningful reflection
- **No insights** - unable to identify patterns in emotions and behaviors
- **Inconsistency** - difficulty maintaining a daily habit

**Luna solves these problems** by providing intelligent guidance, automatic analysis, and personalized insights.

---

## ✨ Key Features

### 🤖 Conversational AI Journaling
- Dynamic, context-aware prompts using **Llama 3.3 70B**
- Guided journaling flow through 6 categories:
  - Factual Account → Self Reflection → Gratitude → Learning → Future Self → Intention Setting
- Empathetic responses that encourage deeper reflection

### 🎭 Advanced Sentiment Analysis
- Real-time emotional analysis using **CardiffNLP RoBERTa**
- Confidence scoring with visual progress bars
- Tracks sentiment trends over time (Positive, Neutral, Negative)

### 🏷️ Automatic Theme Detection
- Zero-shot classification with **BART-MNLI**
- Identifies recurring themes: Work, Relationships, Health, Personal Growth, Creativity, Goals
- Visual theme cards with relevance scoring

### 📊 Analytics Dashboard
- Daily statistics and journaling streaks
- Sentiment distribution visualization
- Weekly engagement metrics

### 🎨 Mood Color Palette
- Quick visual mood tracking for busy days
- 6 mood colors: Happy, Calm, Sad, Energetic, Anxious, Angry
- Integrated with journal history

### 📅 Weekly Wrap Feature
- AI-generated summaries using **Llama 3.3**
- Highlights gratitude moments and key learnings
- Personalized reflections on emotional journey

### 🎤 Voice-to-Text Journaling
- **Groq Whisper Large v3** transcription
- Perfect for hands-free journaling
- Auto-populates text input for editing before sending

### 🔒 Privacy-First Design
- Local SQLite database
- No data leaves your device (except API calls for AI processing)
- Daily conversation grouping

---

## 🎥 Video Demo

> **Note:** Video demonstration available at: [Add your video link here]

*A 3-5 minute walkthrough showcasing all features, UI/UX design decisions, and technical implementation.*

---

## 🌐 Live Demo

**Try it here:** [https://huggingface.co/spaces/pragyasen1/luna-journal](https://huggingface.co/spaces/pragyasen1/luna-journal)

⏱️ *First load may take 30-60 seconds as the Space wakes up (free tier). Models are cached after initial download.*

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
- **Multi-tab Navigation**: Smooth transitions between Journal, History, and Weekly Wrap
- **Typography**: Courgette for headings, Georgia for body text

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
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# Run the application
python app.py
```

The app will be available at `http://localhost:7860`

---

## 🚀 Deploy to Hugging Face Spaces

### 1. Create a Space (if you haven’t already)
- Go to [huggingface.co/spaces](https://huggingface.co/spaces) → **Create new Space**
- Choose **Gradio** as SDK, pick a name (e.g. `luna-journal`), set visibility, then create

### 2. Add secrets (required for the app)
In your Space → **Settings** → **Repository secrets**, add:

| Secret            | Description                          |
|------------------|--------------------------------------|
| `GROQ_API_KEY`   | Your Groq API key (required)         |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID (optional)  |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret (optional) |
| `GOOGLE_REDIRECT_URI` | e.g. `https://YOUR-USERNAME-YOUR-SPACE.hf.space/login/callback` (optional) |

### 3. Push your code

From your project folder (replace `YOUR_HF_USERNAME` and `YOUR_SPACE_NAME` with your Space’s user and repo name):

```bash
# Add Hugging Face remote (one-time)
git remote add huggingface https://huggingface.co/spaces/YOUR_HF_USERNAME/YOUR_SPACE_NAME

# Or if the Space already exists and you cloned it, you may already have "origin" pointing to HF.
# Then push (use main; HF Spaces use main by default)
git push huggingface main
```

If your default branch is `master`:

```bash
git push huggingface master
```

Your Space will build and then run at  
`https://huggingface.co/spaces/YOUR_HF_USERNAME/YOUR_SPACE_NAME`.

---

## 📖 Usage Guide

### Basic Journaling Flow
1. **Start Writing**: Type or speak your thoughts
2. **AI Response**: Luna guides you through reflective questions
3. **View Analysis**: Check sentiment, themes, and patterns in real-time
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

- **Lines of Code**: ~1,700+
- **AI Models Used**: 4 (Llama, RoBERTa, BART, Whisper)
- **Features Implemented**: 8 major features
- **Development Time**: [Add your timeline]

---

## 🎨 UI/UX Design Decisions

1. **Lavender Color Scheme**: Calming, associated with mental wellness
2. **Animated Elements**: Subtle butterflies and hearts for positive reinforcement
3. **Glass Morphism**: Modern, non-intrusive panels
4. **Single-line Input**: Encourages focused, thoughtful entries
5. **Visual Feedback**: Confidence bars, progress indicators, glow effects

---

## 🔮 Future Enhancements

- [ ] Multi-user authentication system
- [ ] Export journal as PDF with visualizations
- [ ] Mobile app (React Native)
- [ ] Habit tracking integration
- [ ] AI-powered writing prompts library
- [ ] Data visualization dashboard (charts, graphs)
- [ ] Integration with calendar apps
- [ ] Encrypted cloud backup

---

## 🏆 Success Metrics

- **Engagement**: Encourages daily journaling through AI guidance
- **Insightfulness**: Provides meaningful sentiment and theme analysis
- **Privacy**: Local-first architecture ensures data security
- **Accessibility**: Voice input and simple UI remove barriers to entry
- **Technical Excellence**: Production-ready code with error handling

---

## 📚 Documentation

- [Setup Guide](GROQ_SETUP.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Hugging Face Checklist](HUGGINGFACE_CHECKLIST.md)

---

## 🤝 Acknowledgments

- **Groq** for lightning-fast LLM inference
- **Hugging Face** for model hosting and Spaces platform
- **Gradio** for rapid UI development
- **Cardiff NLP** for sentiment analysis model

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 👤 Author

**Pragya Sen**
- Hugging Face: [@pragyasen1](https://huggingface.co/pragyasen1)
- Project: [Luna Journal](https://huggingface.co/spaces/pragyasen1/luna-journal)

---

<div align="center">

**Built with ❤️ for mental wellness and personal growth**

[⬆ Back to Top](#luna---ai-powered-journaling-companion-️)

</div>
