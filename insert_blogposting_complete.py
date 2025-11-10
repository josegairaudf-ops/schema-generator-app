# insert_blogposting_complete.py
import sqlite3
from datetime import datetime
import os #

DB_FILE = 'schemas_templates.db'

def insert_blog_complete_template():
    """
    Inserts a comprehensive BlogPosting template with nested SportEvent details.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        template_data = {
            "name": "Complete Sports Blog Post",
            "title": "Analyzing the Epic World Cup Final: Argentina vs France",
            "author": "Football Fanatic",
            "publication_date": "2022-12-19",
            "image_url": "https://example.com/worldcup_final.jpg",
            "content": "The 2022 FIFA World Cup Final was a match for the ages, with Lionel Messi leading Argentina to victory against a valiant French side. Kylian Mbappé's hat-trick kept France in the game...",
            "event_name": "FIFA World Cup Final 2022",
            "event_start_date": "2022-12-18T15:00:00",
            "event_end_date": "2022-12-18T18:00:00",
            "event_location": "Lusail Stadium, Lusail, Qatar",
            "event_organizer": "FIFA",
            "event_description": "The final match of the 2022 FIFA World Cup in Qatar.",
            "event_status": "EventFinished", # Changed from EventScheduled after event
            "event_image_url": "https://example.com/lusail_stadium.jpg",
            "event_offers_url": "https://example.com/past_event_highlights",
            "event_team1": "Argentina National Football Team",
            "event_team2": "France National Football Team"
        }

        cursor.execute('''
            INSERT INTO blog_templates (
                name, title, author, publication_date, image_url, content,
                event_name, event_start_date, event_end_date, event_location,
                event_organizer, event_description, event_status, event_image_url,
                event_offers_url, event_team1, event_team2
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            template_data['name'], template_data['title'], template_data['author'],
            template_data['publication_date'], template_data['image_url'], template_data['content'],
            template_data['event_name'], template_data['event_start_date'], template_data['event_end_date'],
            template_data['event_location'], template_data['event_organizer'], template_data['event_description'],
            template_data['event_status'], template_data['event_image_url'], template_data['event_offers_url'],
            template_data['event_team1'], template_data['event_team2']
        ))
        conn.commit()
        print(f"Inserted complete BlogPosting template: '{template_data['name']}'")

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
        insert_blog_complete_template()