from flask import Flask, render_template, request, jsonify
import os
from datetime import datetime

app = Flask(__name__)

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
        "description": data.get('blogDescription'),
        "mainEntityOfPage": data.get('blogUrl'),
        "author": {
            "@type": "Person",
            "name": data.get('blogAuthor')
        },
        "publisher": {
            "@type": "Organization",
            "name": data.get('blogPublisherName'),
            "logo": {
                "@type": "ImageObject",
                "url": data.get('blogPublisherLogo')
            }
        },
        "datePublished": data.get('blogPublicationDate'),
        "dateModified": data.get('blogModifiedDate'),
        "image": data.get('blogImage'),
        "inLanguage": data.get('blogLanguage', 'en'),
        "keywords": data.get('blogKeywords'),
        "wordCount": int(data.get('blogWordCount', 0)) if data.get('blogWordCount') else None,
        "articleBody": data.get('blogContent')
    }
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

@app.route('/')
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
    return jsonify(generated_schema)

if __name__ == '__main__':
    app.run(debug=True)
