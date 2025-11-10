# insert_blogposting_template.py
import sqlite3
import os #

DB_FILE = 'schemas_templates.db'

def insert_blog_template():
    """
    Inserts a basic BlogPosting template without event details.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        template_data = {
            "name": "Basic Tech Blog Post",
            "title": "The Rise of AI in Everyday Life",
            "author": "Tech Enthusiast",
            "publication_date": "2023-10-26",
            "image_url": "https://example.com/ai_blog.jpg",
            "content": "Artificial intelligence is no longer a futuristic concept but a tangible part of our daily routines. From smart assistants to personalized recommendations, AI's influence is growing...",
            # Event fields are left empty for a basic template
            "event_name": None, "event_start_date": None, "event_end_date": None,
            "event_location": None, "event_organizer": None, "event_description": None,
            "event_status": None, "event_image_url": None, "event_offers_url": None,
            "event_team1": None, "event_team2": None
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
        print(f"Inserted basic BlogPosting template: '{template_data['name']}'")

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
        insert_blog_template()