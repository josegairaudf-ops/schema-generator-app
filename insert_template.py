# insert_template.py (Basic FAQPage Template)
import sqlite3
import os #
from datetime import datetime

DB_FILE = 'schemas_templates.db'

def insert_basic_faq_template():
    """
    Inserts a basic FAQPage template (only two questions for simplicity).
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        template_data = {
            "name": "Basic Product FAQ",
            "author": "Product Support",
            "created_at": datetime.now().isoformat(),
            "modified_at": datetime.now().isoformat(),
            "q1": "How do I use this product?",
            "a1": "Refer to the user manual for detailed instructions, or visit our online help center.",
            "q2": "What is the warranty policy?",
            "a2": "Our product comes with a one-year limited warranty. Please check our website for full terms and conditions.",
            "q3": None, "a3": None, # Unused
            "q4": None, "a4": None  # Unused
        }

        cursor.execute('''
            INSERT INTO faq_templates (
                name, author, created_at, modified_at,
                q1, a1, q2, a2, q3, a3, q4, a4
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            template_data['name'], template_data['author'], template_data['created_at'],
            template_data['modified_at'], template_data['q1'], template_data['a1'],
            template_data['q2'], template_data['a2'], template_data['q3'],
            template_data['a3'], template_data['q4'], template_data['a4']
        ))
        conn.commit()
        print(f"Inserted basic FAQPage template: '{template_data['name']}'")

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
        insert_basic_faq_template()