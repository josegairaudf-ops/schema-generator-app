# app.py
from flask import Flask, render_template, request, jsonify
import sqlite3
import json
import os #
from datetime import datetime
from rich import print as rprint # For pretty printing JSON in console

app = Flask(__name__)
DB_FILE = 'schemas_templates.db'

# --- Helper functions for database interaction ---

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
    return conn

def get_template(table_name, template_name):
    """Fetches a specific template by name from a given table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name} WHERE name = ?", (template_name,))
    template = cursor.fetchone()
    conn.close()
    return template

# --- Schema Generation Functions ---

def generate_faq_schema(data):
    """Generates JSON-LD for FAQPage based on form data."""
    questions_answers = []
    for i in range(1, 5): # Assuming 4 FAQ pairs
        q = data.get(f'faqQ{i}')
        a = data.get(f'faqA{i}')
        if q and a:
            questions_answers.append({
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": a
                }
            })

    if not questions_answers:
        return {} # Return empty if no valid Q&A

    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": questions_answers,
        "dateCreated": data.get('faqCreatedAt', datetime.now().isoformat()),
        "dateModified": data.get('faqModifiedAt', datetime.now().isoformat()),
        "author": {
            "@type": "Person",
            "name": data.get('faqAuthor', 'Anonymous')
        }
    }
    return schema

def generate_blog_schema(data):
    """Generates JSON-LD for BlogPosting based on form data."""
    schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": data.get('blogTitle'),
        "author": {
            "@type": "Person",
            "name": data.get('blogAuthor')
        },
        "datePublished": data.get('blogPublicationDate'),
        "image": data.get('blogImage'),
        "articleBody": data.get('blogContent')
    }

    # Add SportEvent details if provided
    if data.get('eventName'):
        event_details = {
            "@type": "SportingEvent",
            "name": data.get('eventName'),
            "startDate": data.get('eventStartDate'),
            "endDate": data.get('eventEndDate'),
            "location": {
                "@type": "Place",
                "name": data.get('eventLocation')
            },
            "organizer": {
                "@type": "Organization",
                "name": data.get('eventOrganizer')
            },
            "description": data.get('eventDescription'),
            "eventStatus": f"https://schema.org/{data.get('eventStatus')}" if data.get('eventStatus') else None,
            "image": data.get('eventImage'),
            "offers": {
                "@type": "Offer",
                "url": data.get('eventOffers')
            },
            "performer": []
        }
        if data.get('eventTeam1'):
            event_details["performer"].append({"@type": "SportsTeam", "name": data.get('eventTeam1')})
        if data.get('eventTeam2'):
            event_details["performer"].append({"@type": "SportsTeam", "name": data.get('eventTeam2')})

        schema["about"] = event_details # "about" is a good property for related entities
    return schema

def generate_review_schema(data):
    """Generates JSON-LD for Review based on form data (betting pick)."""
    rating = int(data['reviewRating']) if data.get('reviewRating') else None
    
    schema = {
        "@context": "https://schema.org",
        "@type": "Review",
        "author": {
            "@type": "Person",
            "name": data.get('reviewAuthor')
        },
        "datePublished": data.get('reviewPublicationDate'),
        "reviewBody": data.get('reviewReasoning'),
        "reviewRating": {
            "@type": "Rating",
            "ratingValue": rating,
            "bestRating": 5,
            "worstRating": 1
        },
        "itemReviewed": {
            "@type": "Event", # Or SportingEvent depending on detail
            "name": data.get('reviewEventName'),
            "startDate": data.get('reviewEventDate'),
            "location": {
                "@type": "Place",
                "name": data.get('reviewEventLocation')
            }
        },
        # Custom properties for betting picks
        "keywords": f"Betting Pick, {data.get('reviewMarketType')}, {data.get('reviewSelection')}",
        "offers": { # Using offers to represent the betting opportunity
            "@type": "Offer",
            "category": data.get('reviewMarketType'),
            "itemOffered": data.get('reviewSelection'),
            "price": data.get('reviewOdds'),
            "priceCurrency": "USD", # Assuming currency, could be dynamic
            "seller": {
                "@type": "Organization",
                "name": data.get('reviewBookmaker')
            }
        },
        "valueAdded": { # To represent units/risk
            "@type": "PropertyValue",
            "name": "Units/Risk",
            "value": data.get('reviewUnits')
        }
    }
    return schema


# --- Flask Routes ---

@app.route('/', methods=['GET'])
def index():
    """Serves the main HTML form."""
    # You could fetch templates here and pass them to the template
    # For now, we'll keep it simple and load the form
    return render_template('index.html')

@app.route('/generate_schema', methods=['POST'])
def generate_schema():
    """Handles schema generation based on form submission."""
    schema_type = request.form.get('schemaType')
    form_data = request.form.to_dict() # Get all form data as a dictionary

    generated_schema = {}
    if schema_type == 'FAQPage':
        generated_schema = generate_faq_schema(form_data)
    elif schema_type == 'BlogPosting':
        generated_schema = generate_blog_schema(form_data)
    elif schema_type == 'Review':
        generated_schema = generate_review_schema(form_data)
    else:
        return jsonify({"error": "Invalid schema type selected"}), 400

    rprint("[bold blue]Generated Schema:[/bold blue]")
    rprint(generated_schema) # Print to console for debugging

    # Return the generated schema as JSON
    return jsonify(generated_schema)

@app.route('/get_template/<template_type>/<template_name>', methods=['GET'])
def get_schema_template(template_type, template_name):
    """
    API endpoint to fetch a specific template by type and name.
    Example: /get_template/faq/MyBasicFAQ
    """
    table_map = {
        'faq': 'faq_templates',
        'blog': 'blog_templates',
        'review': 'review_templates'
    }
    table_name = table_map.get(template_type)

    if not table_name:
        return jsonify({"error": "Invalid template type"}), 400

    template_data = get_template(table_name, template_name)
    if template_data:
        # Convert sqlite3.Row to dict for JSON serialization
        return jsonify(dict(template_data))
    else:
        return jsonify({"error": "Template not found"}), 404

if __name__ == '__main__':
    # Ensure the database exists before running the app
    if not os.path.exists(DB_FILE):
        print(f"Database '{DB_FILE}' not found. Please run 'python create_db.py' first.")
    app.run(debug=True)