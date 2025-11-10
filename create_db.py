# create_db.py
import sqlite3
import os #
DB_FILE = 'schemas_templates.db'

def create_database():
    """
    Creates the SQLite database and defines tables for FAQPage, BlogPosting, and Review schemas.
    Each table stores template data that can be used to pre-fill forms or generate JSON-LD.
    """
    conn = None
    try:
        # Remove existing DB if it exists to start fresh
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            print(f"Removed existing database: {DB_FILE}")

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Table for FAQPage Templates
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS faq_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                author TEXT,
                created_at TEXT,
                modified_at TEXT,
                q1 TEXT, a1 TEXT,
                q2 TEXT, a2 TEXT,
                q3 TEXT, a3 TEXT,
                q4 TEXT, a4 TEXT
            )
        ''')
        print("Table 'faq_templates' created.")

        # Table for BlogPosting Templates
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blog_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                title TEXT,
                author TEXT,
                publication_date TEXT,
                image_url TEXT,
                content TEXT,
                event_name TEXT,
                event_start_date TEXT,
                event_end_date TEXT,
                event_location TEXT,
                event_organizer TEXT,
                event_description TEXT,
                event_status TEXT,
                event_image_url TEXT,
                event_offers_url TEXT,
                event_team1 TEXT,
                event_team2 TEXT
            )
        ''')
        print("Table 'blog_templates' created.")

        # Table for Review Templates
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS review_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                author TEXT,
                publication_date TEXT,
                reasoning TEXT,
                rating INTEGER,
                event_name TEXT,
                event_date TEXT,
                event_location TEXT,
                market_type TEXT,
                selection TEXT,
                odds TEXT,
                bookmaker TEXT,
                units REAL
            )
        ''')
        print("Table 'review_templates' created.")

        conn.commit()
        print(f"Database '{DB_FILE}' created and tables initialized successfully.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    create_database()