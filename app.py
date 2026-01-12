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
    "name": data.get('blogAuthor'),
    "url": data.get('blogAuthorUrl')
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
            "name": data.get('blogAuthor'),
            "url": data.get('blogAuthorUrl')
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

def generate_sportsevent_schema(data):
    is_free = bool(data.get('seFree'))

    league = data.get("seSport")  # NFL / NBA / MLB / NHL / Other

    # mapear liga -> deporte legible
    league_to_sport = {
        "NFL": "American Football",
        "NBA": "Basketball",
        "MLB": "Baseball",
        "NHL": "Ice Hockey",
    }
    sport_name = league_to_sport.get(league, "Sports")  # fallback genérico

    home_team = data.get("seTeamA") or data.get("seTeamACustom")
    away_team = data.get("seTeamB")

    schema = {
        "@context": "https://schema.org",
        "@type": "SportsEvent",
        "name": data.get("seName"),
        "sport": sport_name,      # ← deporte legible (Basketball, etc.)
        "league": league,         # ← tu liga tal cual (NBA, NFL, etc.)
        "startDate": data.get("seStartDate"),
        "endDate": data.get("seEndDate"),
        "eventStatus": data.get("seEventStatus"),
        "eventAttendanceMode": data.get("seEventAttendanceMode"),
        "location": {
            "@type": "Place",
            "name": data.get("seStadium"),
            "address": {
                "@type": "PostalAddress",
                "addressLocality": data.get("seCity"),
                "addressRegion": data.get("seRegion"),
                "addressCountry": data.get("seCountry")
            }
        },
        "competitor": [
            {"@type": "SportsTeam", "name": home_team},
            {"@type": "SportsTeam", "name": away_team}
        ],
        "performer": [
            {"@type": "SportsTeam", "name": home_team},
            {"@type": "SportsTeam", "name": away_team}
        ],
        "organizer": {
            "@type": "Organization",
            "name": "BetUS",
            "url": "https://www.betus.com.pa/"
        },
        "url": data.get("seUrl"),
        "image": data.get("seImage"),
        "description": data.get("seDescription"),
        "isAccessibleForFree": is_free,
        "inLanguage": data.get("seLanguage")
    }
    # -------------------------
    # construir lista de offers
    # -------------------------
    offers = []
    # 0) Offer “principal” (los campos que ya tenías)
    base_name = data.get("seOfferName")
    base_price = data.get("seOfferPrice")
    base_url = data.get("seOfferUrl")
    if base_name or base_price or base_url:
        offers.append({
            "@type": "Offer",
            "name": base_name,
            "price": base_price,
            "priceCurrency": "USD",
            "url": base_url
        })

    # helper interno para no repetir código
    def add_pick(name_key, price_key, url_key):
        name = data.get(name_key)
        price = data.get(price_key)
        url = data.get(url_key)
        if name or price or url:
            offers.append({
                "@type": "Offer",
                "name": name,
                "price": price,
                "priceCurrency": "USD",
                "url": url
            })

    # 1) Pick 1, 2 y 3
    add_pick("pick1Name", "pick1Price", "pick1Url")
    add_pick("pick2Name", "pick2Price", "pick2Url")
    add_pick("pick3Name", "pick3Price", "pick3Url")
    add_pick("pick4Name", "pick4Price", "pick4Url")  # ← nuevo
    add_pick("pick5Name", "pick5Price", "pick5Url")  # ← nuevo


    # si hay al menos un offer, lo añadimos al schema
    if offers:
        schema["offers"] = offers

    return schema

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_schema', methods=['POST'])
def generate_schema():
    schema_type = request.form.get('schemaType')
    print("DEBUG schema_type:", schema_type)
    form_data = request.form.to_dict()
    generated_schema = {}
    if schema_type == 'FAQPage':
        generated_schema = generate_faq_schema(form_data)
    elif schema_type == 'BlogPosting':
        generated_schema = generate_blog_schema(form_data)
    elif schema_type == 'Review':
        generated_schema = generate_review_schema(form_data)
    elif schema_type == 'SportsEvent':
        generated_schema = generate_sportsevent_schema(form_data)
    else:
        return jsonify({"error": "Invalid schema type selected"}), 400
    return jsonify(generated_schema)

if __name__ == '__main__':
    app.run(debug=True)
