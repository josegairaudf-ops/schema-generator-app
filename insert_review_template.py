# insert_review_template.py
import sqlite3
import os #
from datetime import date

DB_FILE = 'schemas_templates.db'

def insert_review_template():
    """
    Inserts a basic Review (Betting Pick) template.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        template_data = {
            "name": "NBA Moneyline Pick",
            "author": "ProPicks Analytics",
            "publication_date": date.today().isoformat(),
            "reasoning": "Team X has a strong home record and key players are returning from injury. Team Y struggles on the road against top-tier opponents.",
            "rating": 4, # On a scale of 1-5
            "event_name": "NBA Regular Season - Lakers vs Celtics",
            "event_date": "2023-11-15",
            "event_location": "Crypto.com Arena, Los Angeles",
            "market_type": "Moneyline",
            "selection": "Los Angeles Lakers to Win",
            "odds": "1.90",
            "bookmaker": "DraftKings",
            "units": 2.5
        }

        cursor.execute('''
            INSERT INTO review_templates (
                name, author, publication_date, reasoning, rating,
                event_name, event_date, event_location, market_type,
                selection, odds, bookmaker, units
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            template_data['name'], template_data['author'], template_data['publication_date'],
            template_data['reasoning'], template_data['rating'], template_data['event_name'],
            template_data['event_date'], template_data['event_location'], template_data['market_type'],
            template_data['selection'], template_data['odds'], template_data['bookmaker'],
            template_data['units']
        ))
        conn.commit()
        print(f"Inserted Review template: '{template_data['name']}'")

    except sqlite3.IntegrityError:
        print(f"Template '{template_data['name']}' already exists.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    if not os.path.exists(DB_FILE):
        print(f"Error: Database '{DB_FILE}' not found. Please run 'python create_db.py' first.")
    else:
        insert_review_template()