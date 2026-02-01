# Luna – Design Documentation

Design outline, tech stack, future enhancements and responsible AI (ethics, security, limitations) for the Luna AI-Powered Journaling Companion.

---

## 1. Design Outline

### 1.1 Product Vision

Luna is an empathetic journaling companion that reduces blank-page anxiety and inconsistency by providing:
- **Guided reflection** via conversational AI (Luna)
- **Automatic analysis** of sentiment and themes
- **Low-friction input** (text + voice + mood colors)
- **Privacy-conscious storage** (local SQLite or user’s Google Drive)

### 1.2 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Gradio UI (app.py)                        │
│  Tabs: Journal Chat | View History | Weekly Wrap                   │
│  Components: Chatbot, Analysis Panel, Mood Palette, Stats         │
└───────────────────────────────┬─────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  database.py  │       │  AI / APIs    │       │ drive_storage │
│  SQLite CRUD  │       │  Groq, HF     │       │  (optional)   │
│  entries,     │       │  Llama,       │       │  OAuth +       │
│  stats,       │       │  Whisper,     │       │  Drive API    │
│  weekly wrap  │       │  RoBERTa, BART│       │               │
└───────────────┘       └───────────────┘       └───────────────┘
```

- **app.py**: Single Gradio app with FastAPI mount when Google OAuth is enabled (for `/login/callback`).
- **database.py**: SQLite schema, daily conversation grouping, stats, weekly-entry aggregation. DB path can be overridden (e.g. Drive-synced temp file).
- **drive_storage.py**: Optional Google OAuth 2.0 + Drive API; one SQLite file per user.

### 1.3 User Flows

- **Journal Chat**: User types or uses voice → entry analyzed (sentiment + themes) → Luna reply generated → saved to today’s entry; analysis panel and stats update.
- **View History**: Search/refresh journal entries; content is read from the same DB (local or Drive-backed).
- **Weekly Wrap**: AI summary of the past week’s entries (from DB); refresh on demand.
- **Mood palette**: One-tap mood color for the day; stored with that day’s entry.
- **Login (optional)**: Google sign-in → DB path set to Drive-synced file → all features use that DB.

### 1.4 UI/UX Design

- **Theme**: Lavender palette (#F2ECFF, purple gradients), Courgette + Georgia typography, custom CSS.
- **Layout**: Split view—chat + input on the left; analysis panel, mood palette, and “Powered by” stats on the right.
- **Tabs**: Journal Chat (main), View History, Weekly Wrap; transitions and layout tuned for both local and Hugging Face (HF) deployment.
- **Accessibility**: Voice input (Whisper), simple controls, clear labels; layout and scroll behavior fixed for HF (no extra empty space, analysis panel scrollable).

### 1.5 Data Model (Conceptual)

- **Entry** = one day: `entry_date`, `conversation` (JSON: list of user/assistant turns), `overall_sentiment`, `sentiment_score`, `themes` (JSON), `mood_color`, timestamps.
- **Daily grouping**: All messages for a given day are stored as a single entry; weekly wrap reads entries by date range.

### 1.6 Prompt Engineering: Six Journaling Styles

Luna’s conversational flow is driven entirely by **prompt engineering** (no fine-tuning). The system prompt instructs the model to detect the user’s journaling style and respond with one short, empathetic follow-up question. The six styles and how Luna adapts:

| # | Style | Signs (user language) | Luna’s approach |
|---|--------|------------------------|------------------|
| 1 | **Factual account** | “I went to…”, “I did…”, events without emotions | Ask what stood out most; if they mention emotions or learning next, explore those. |
| 2 | **Self reflection** | “I felt stressed/sad/overwhelmed/angry/anxious” | Ask what caused that feeling; gently explore, then transition to gratitude (“Was there anything you’re grateful for?”). |
| 3 | **Gratitude** | “I’m thankful/grateful”, “I appreciate”, or after reflection | Ask why it mattered today; then one intention for tomorrow. |
| 4 | **Learning** | “I learned”, “I realized”, “I discovered”, “I understood” | Ask how it might be useful; connect to future goals or gratitude. |
| 5 | **Future self** | “I want”, “I hope”, “In the future”, “One day” | Ask for one small step toward that; help set concrete intentions. |
| 6 | **Intention setting** | “I will”, “Tomorrow I want to”, “My goal is”, “I plan to” | Ask what might get in the way; help anticipate obstacles, then encourage. |

**Rules baked into the prompt**: One question per response; 2–3 sentences max; warm and non-judgmental; never name the category; flow naturally between types; no medical advice. The user prompt also passes **context from analysis** (sentiment + themes) so Luna’s tone and focus can match the user’s emotional state and topics.

---

## 2. Tech Stack

### 2.1 Core Application

| Layer        | Technology        | Purpose                                      |
|-------------|--------------------|----------------------------------------------|
| Language    | Python 3.12        | Runtime (HF Spaces); 3.10+ supported locally |
| UI          | Gradio 4.36.1      | Web interface, tabs, chatbot, inputs         |
| Backend     | —                  | Logic in app.py; no separate server          |
| OAuth server| FastAPI + Uvicorn  | Mounted when Google OAuth enabled; `/login/callback` |

### 2.2 AI & APIs

| Component        | Technology                    | Use case                          |
|-----------------|-------------------------------|-----------------------------------|
| Chat + prompts  | Groq API (Llama 3.3 70B)      | Luna’s replies, weekly wrap       |
| Speech-to-text  | Groq Whisper Large v3        | Voice journal input               |
| Sentiment       | Hugging Face Transformers     | CardiffNLP RoBERTa (sentiment)    |
| Themes          | Hugging Face Transformers     | BART-MNLI (zero-shot themes)      |

### 2.3 Data & Storage

| Component     | Technology        | Notes                                              |
|---------------|-------------------|----------------------------------------------------|
| Primary store | SQLite            | `database.py`; default path next to app            |
| Optional sync | Google Drive API  | `drive_storage.py`; OAuth 2.0; one DB file per user|
| Env/config    | python-dotenv     | API keys, optional Google OAuth credentials       |

### 2.4 Dependencies (Summary)

- **ML**: `transformers`, `torch`, `huggingface_hub` (pinned &lt;0.23 for compatibility).
- **LLM**: `groq`.
- **UI**: `gradio==4.36.1` (for HF compatibility).
- **Google**: `google-auth`, `google-auth-oauthlib`, `google-api-python-client`.
- **App server**: `fastapi`, `uvicorn`.

---

## 3. Future Enhancements

- **Multi-user / auth**: Proper user accounts and per-user data when not using Google (e.g. email/password or other IdP).
- **Export**: Export journal (e.g. PDF) with optional sentiment/theme visualizations.
- **Mobile**: Native or PWA (e.g. React Native or responsive PWA) for on-the-go journaling.
- **Habit tracking**: Streaks, reminders, and simple habit metrics tied to journaling.
- **Prompt library**: Curated or AI-suggested writing prompts by mood/goal.
- **Data viz**: Charts and trends (sentiment over time, theme distribution, mood calendar).
- **Calendar integration**: Optional link to Google Calendar or similar for “journal days” or reminders.
- **Encrypted backup**: Encrypted cloud backup (e.g. user-owned bucket or Drive folder) with client-side or server-side encryption.
- **Offline / PWA**: Service worker and local-first behavior so the app works offline and syncs when online.
- **Local LLM option**: Optional path to run a local model (e.g. Ollama) instead of Groq for users who want no cloud LLM.

---

## 4. Responsible AI: Ethics, Security & Limitations

### 4.1 Ethical Considerations

- **Not a substitute for professional care**: Luna is a supportive journaling companion, not a therapist or mental health professional. The system prompt explicitly instructs the model not to give medical or clinical advice and to encourage users to seek professional help when appropriate.
- **Sensitive content/Transparency**: Users should be aware that when using the Hugging Face demo, their text is sent to third-party services for processing. The UI surfaces “Powered by” model names (RoBERTa, BART, Llama, Whisper) so users know which systems are involved. Privacy and data-handling behavior is documented (local vs HF vs Google Drive).
- **Bias and fairness**: Sentiment and theme models (RoBERTa, BART) are general-purpose and may not reflect every user’s cultural or linguistic context.

### 4.2 Security

- **Credentials**: API keys (e.g. `GROQ_API_KEY`) and Google OAuth credentials are loaded from environment variables (e.g. `.env` or HF Secrets), not hardcoded. `.env` should be listed in `.gitignore` and never committed.
- **OAuth**: Google sign-in uses the OAuth 2.0 authorization code flow. Redirect URI must match Google Cloud Console and (on HF) the Space’s callback URL. Scopes are limited to `drive.file` (app-created files only).
- **Data in transit**: When using Groq or Hugging Face APIs, journal text is sent over HTTPS. Data handling is governed by those providers’ terms and policies.
- **Data at rest**: Local SQLite files are stored on the user’s machine or (when using Drive) in the user’s Google Drive. On Hugging Face Spaces without login, the DB lives on the Space’s server and may be ephemeral.
- **No built-in auth for HF demo**: The public HF Space does not enforce user authentication; anyone with the link can use it. Optional Google login only switches storage to the signed-in user’s Drive; it does not restrict who can open the app.

### 4.3 Limitations

- **Availability**: When running on Hugging Face (free tier), the Space can sleep; first load may be slow. Groq and Hugging Face APIs are subject to rate limits and provider outages.
- **HF without login**: Data is stored on the Space’s server and may be lost on restart or sleep; it is not “local” to the user’s device. For persistent, user-owned data, sign in with Google (Drive) or run the app locally.
- **Google login (testing)**: The app is still in testing. Google OAuth is not in “production” mode, so sign-in is only allowed for test users added to the Google Cloud Console test list. Until the app is officially verified by Google, other users will not be able to use “Sign in with Google.” Everyone can still use the app without logging in (session/local or HF server storage).

---

*This document summarizes the design, tech stack, main challenges, planned improvements, and responsible-AI stance for Luna. For setup and usage, see [README.md](README.md).*
