# insert_template_ampliado.py (Detailed FAQPage Template)
import sqlite3
import os #
from datetime import datetime

DB_FILE = 'schemas_templates.db'

def insert_detailed_faq_template():
    """
    Inserts a detailed FAQPage template.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        template_data = {
            "name": "Detailed SEO FAQ",
            "author": "SEO Specialist",
            "created_at": datetime.now().isoformat(),
            "modified_at": datetime.now().isoformat(),
            "q1": "What is SEO and why is it important?",
            "a1": "SEO (Search Engine Optimization) is the practice of increasing the quantity and quality of traffic to your website through organic search engine results. It's crucial for visibility and reaching your target audience.",
            "q2": "How long does it take to see SEO results?",
            "a2": "SEO is a long-term strategy, and results can vary. Typically, you might start seeing noticeable improvements in 4-6 months, with significant gains taking 6-12 months or more, depending on competition and effort.",
            "q3": "What's the difference between on-page and off-page SEO?",
            "a3": "On-page SEO refers to optimizing elements on your website (content, keywords, meta tags, images). Off-page SEO involves activities done outside your website to improve its ranking (link building, social media marketing).",
            "q4": "Do I need technical SEO?",
            "a4": "Yes, technical SEO is fundamental. It ensures search engine crawlers can efficiently access, crawl, and index your website. This includes site speed, mobile-friendliness, structured data, and XML sitemaps."
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
        print(f"Inserted detailed FAQPage template: '{template_data['name']}'")

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
        insert_detailed_faq_template()