from flask import Flask, render_template, request, jsonify
import sqlite3
import json
import os
from datetime import datetime
from rich import print as rprint

import openai

app = Flask(__name__)
DB_FILE = 'schemas_templates.db'

# --- Helper functions for database interaction ---

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_template(table_name, template_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name} WHERE name = ?", (template_name,))
    template = cursor.fetchone()
    conn.close()
    return template

# --- Schema Generation Functions ---

def generate_faq_schema(data):
    questions_answers = []
    for i in range(1, 5):
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
        return {}

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
        schema["about"] = event_details
    return schema

def generate_review_schema(data):
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
            "@type": "Event",
            "name": data.get('reviewEventName'),
            "startDate": data.get('reviewEventDate'),
            "location": {
                "@type": "Place",
                "name": data.get('reviewEventLocation')
            }
        },
        "keywords": f"Betting Pick, {data.get('reviewMarketType')}, {data.get('reviewSelection')}",
        "offers": {
            "@type": "Offer",
            "category": data.get('reviewMarketType'),
            "itemOffered": data.get('reviewSelection'),
            "price": data.get('reviewOdds'),
            "priceCurrency": "USD",
            "seller": {
                "@type": "Organization",
                "name": data.get('reviewBookmaker')
            }
        },
        "valueAdded": {
            "@type": "PropertyValue",
            "name": "Units/Risk",
            "value": data.get('reviewUnits')
        }
    }
    return schema

# --- Flask Routes ---

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/generate_schema', methods=['POST'])
def generate_schema():
    schema_type = request.form.get('schemaType')
    form_data = request.form.to_dict()
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
    rprint(generated_schema)
    return jsonify(generated_schema)

@app.route('/get_template/<template_type>/<template_name>', methods=['GET'])
def get_schema_template(template_type, template_name):
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
        return jsonify(dict(template_data))
    else:
        return jsonify({"error": "Template not found"}), 404

# ----------- FAQ Generator OpenAI Endpoint ------------

openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route('/api/generate-faq', methods=['POST'])
def generate_faq():
    data = request.get_json()
    title = data.get('title')
    summary = data.get('summary')
    keywords = data.get('keywords', '')

    if not title or not summary:
        return jsonify({'error': 'Missing title or summary'}), 400

    prompt = (
        f"Given the article information below, suggest 3 relevant, precise FAQ questions that target user intent for SEO. "
        f"Use the title, summary and focus keywords if possible. Don't write answers, just the 3 questions.\n\n"
        f"Title: {title}\n"
        f"Summary: {summary}\n"
        f"Keywords: {keywords}\n\n"
        "Example Output:\n"
        "1. [Question about topic...]\n"
        "2. [Another question...]\n"
        "3. [Third question...]"
    )

    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=150,
            temperature=0.7
        )
        text = response.choices[0].text.strip()
        faqs = []
        for line in text.split('\n'):
            line = line.strip()
            if line and not line.startswith('Example Output:'):
                faqs.append(line.lstrip('1234. ').strip())
        faqs = [q for q in faqs if q]
        return jsonify({'faqs': faqs[:3]})
    except Exception as e:
        print('[OpenAI Error]', e)
        return jsonify({'error': 'Error generating FAQs'}), 500

if __name__ == '__main__':
    if not os.path.exists(DB_FILE):
        print(f"Database '{DB_FILE}' not found. Please run 'python create_db.py' first.")
    app.run(debug=True)
