"""
Database module for storing journal entries.
Supports local file or Google Drive-backed storage (path set at runtime).
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

# Default local path; can be overridden for Drive-backed storage
_default_db_path = Path(__file__).parent / "journal_entries.db"
_db_path = _default_db_path
_after_commit = None

# Keep for code that references db.DB_PATH (e.g. app.py get_weekly_entries)
DB_PATH = _default_db_path


def _get_db_path():
    """Return the current database path (local or Drive-synced temp file)."""
    return _db_path


def set_db_path(path):
    """Set the database path (e.g. to a temp file synced with Google Drive)."""
    global _db_path, DB_PATH
    _db_path = Path(path) if path else _default_db_path
    DB_PATH = _db_path


def set_after_commit(callback):
    """Set a callback to run after any write (e.g. upload DB to Drive)."""
    global _after_commit
    _after_commit = callback


def _notify_after_commit():
    if _after_commit:
        try:
            _after_commit()
        except Exception as e:
            print(f"⚠️ after_commit callback error: {e}")


def init_database():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(_get_db_path())
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date DATE NOT NULL UNIQUE,
            conversation TEXT NOT NULL,
            overall_sentiment TEXT,
            sentiment_score REAL,
            themes TEXT,
            mood_color TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")


def save_conversation_message(user_message, ai_response, sentiment, sentiment_score, themes):
    """Save or append to today's journal entry"""
    conn = sqlite3.connect(_get_db_path())
    cursor = conn.cursor()
    
    # Get today's date
    today = datetime.now().date().isoformat()
    
    # Check if entry exists for today
    cursor.execute("SELECT id, conversation FROM entries WHERE entry_date = ?", (today,))
    existing = cursor.fetchone()
    
    # Create conversation message
    message_data = {
        'user': user_message,
        'luna': ai_response,
        'timestamp': datetime.now().isoformat()
    }
    
    if existing:
        # Append to existing entry
        entry_id = existing[0]
        conversation = json.loads(existing[1])
        conversation.append(message_data)
        
        # Update conversation and timestamp
        cursor.execute("""
            UPDATE entries 
            SET conversation = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (json.dumps(conversation), entry_id))
    else:
        # Create new entry for today
        conversation = [message_data]
        themes_json = json.dumps(themes)
        
        cursor.execute("""
            INSERT INTO entries (entry_date, conversation, overall_sentiment, sentiment_score, themes)
            VALUES (?, ?, ?, ?, ?)
        """, (today, json.dumps(conversation), sentiment, sentiment_score, themes_json))
        
        entry_id = cursor.lastrowid
    
    conn.commit()
    _notify_after_commit()
    conn.close()
    
    return entry_id


def get_all_entries(limit=100):
    """Get all journal entries, most recent first"""
    conn = sqlite3.connect(_get_db_path())
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, entry_date, conversation, overall_sentiment, sentiment_score, themes, mood_color, created_at
        FROM entries
        ORDER BY entry_date DESC
        LIMIT ?
    """, (limit,))
    
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

def get_entry_by_date(entry_date):
    """Get a specific entry by date"""
    conn = sqlite3.connect(_get_db_path())
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, entry_date, conversation, overall_sentiment, sentiment_score, themes, mood_color, created_at
        FROM entries
        WHERE entry_date = ?
    """, (entry_date,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'id': row[0],
            'entry_date': row[1],
            'conversation': json.loads(row[2]),
            'sentiment': row[3],
            'sentiment_score': row[4],
            'themes': json.loads(row[5]) if row[5] else [],
            'mood_color': row[6],
            'created_at': row[7]
        }
    return None

def get_stats():
    """Get statistics about journal entries"""
    conn = sqlite3.connect(_get_db_path())
    cursor = conn.cursor()
    
    # Total days with actual journal entries (not just mood colors)
    cursor.execute("SELECT COUNT(*) FROM entries WHERE conversation != '[]'")
    total_entries = cursor.fetchone()[0]
    
    # Average sentiment
    cursor.execute("SELECT AVG(sentiment_score) FROM entries WHERE overall_sentiment = 'positive'")
    avg_positive = cursor.fetchone()[0] or 0
    
    # Count by sentiment (only entries with conversations)
    cursor.execute("SELECT overall_sentiment, COUNT(*) FROM entries WHERE overall_sentiment IS NOT NULL GROUP BY overall_sentiment")
    sentiment_counts = {}
    for row in cursor.fetchall():
        if row[0]:
            sentiment_counts[row[0].upper()] = row[1]
    
    # Most recent entry date
    cursor.execute("SELECT MAX(entry_date) FROM entries WHERE conversation != '[]'")
    last_entry = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_entries': total_entries,
        'avg_positive': avg_positive,
        'sentiment_counts': sentiment_counts,
        'last_entry': last_entry
    }

def delete_entry(entry_id):
    """Delete an entry by ID"""
    conn = sqlite3.connect(_get_db_path())
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    
    conn.commit()
    _notify_after_commit()
    conn.close()

def search_entries(search_term):
    """Search entries by text or date"""
    conn = sqlite3.connect(_get_db_path())
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, entry_date, conversation, overall_sentiment, sentiment_score, themes, mood_color, created_at
        FROM entries
        WHERE entry_date LIKE ? OR conversation LIKE ?
        ORDER BY entry_date DESC
    """, (f'%{search_term}%', f'%{search_term}%'))
    
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

def save_mood_color(color):
    """Save or update mood color for today's date"""
    conn = sqlite3.connect(_get_db_path())
    cursor = conn.cursor()
    
    # Get today's date
    today = datetime.now().date().isoformat()
    
    # Check if entry exists for today
    cursor.execute("SELECT id FROM entries WHERE entry_date = ?", (today,))
    existing = cursor.fetchone()
    
    if existing:
        # Update existing entry
        cursor.execute("""
            UPDATE entries 
            SET mood_color = ?, updated_at = CURRENT_TIMESTAMP
            WHERE entry_date = ?
        """, (color, today))
    else:
        # Create new entry with just the color
        cursor.execute("""
            INSERT INTO entries (entry_date, conversation, mood_color)
            VALUES (?, ?, ?)
        """, (today, json.dumps([]), color))
    
    conn.commit()
    _notify_after_commit()
    conn.close()
    return True


def get_mood_color_for_today():
    """Get the mood color for today's date"""
    conn = sqlite3.connect(_get_db_path())
    cursor = conn.cursor()
    
    today = datetime.now().date().isoformat()
    cursor.execute("SELECT mood_color FROM entries WHERE entry_date = ?", (today,))
    result = cursor.fetchone()
    
    conn.close()
    return result[0] if result and result[0] else None

# Initialize database on import
init_database()
