from flask import Flask, render_template, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

# --- Limpiador de diccionarios (Elimina campos vacíos) ---
def clean_nones(value):
    if isinstance(value, dict):
        return {k: v for k, v in ((k, clean_nones(v)) for k, v in value.items()) if v}
    if isinstance(value, list):
        return [v for v in (clean_nones(v) for v in value) if v]
    return value

# --- GENERADORES ---

def gen_faq(data):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [{
            "@type": "Question",
            "name": data.get("faqQ1"),
            "acceptedAnswer": {"@type": "Answer", "text": data.get("faqA1")}
        }]
    }

def gen_blog(data):
    return {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": data.get("blogHeadline"),
        "description": data.get("blogDesc"),
        "image": data.get("blogImage"),
        "datePublished": data.get("blogDate") or datetime.now().isoformat(),
        "author": {"@type": "Person", "name": data.get("blogAuthor")},
        "publisher": {"@type": "Organization", "name": data.get("blogPub")},
        "mainEntityOfPage": {"@type": "WebPage", "@id": data.get("blogUrl")}
    }

def gen_review(data):
    return {
        "@context": "https://schema.org",
        "@type": "Review",
        "itemReviewed": {"@type": "Thing", "name": data.get("revItem")},
        "reviewRating": {
            "@type": "Rating",
            "ratingValue": data.get("revValue"),
            "bestRating": "5",
            "worstRating": "1"
        },
        "author": {"@type": "Person", "name": data.get("revAuthor")},
        "reviewBody": data.get("revBody")
    }

def gen_sports(data):
    l_val = data.get("seSport")
    if l_val == "Other":
        league, sport = data.get("seLeagueCustom"), data.get("seSportCustom")
        t_a, t_b = data.get("seTeamACustom"), data.get("seTeamBCustom")
    else:
        league = l_val
        sport = {"NFL": "American Football", "NBA": "Basketball", "MLB": "Baseball", "NHL": "Ice Hockey"}.get(l_val, "Sports")
        t_a, t_b = data.get("seTeamA"), data.get("seTeamB")

    # Estructura completa para pasar el Rich Results Test
    schema = {
        "@context": "https://schema.org",
        "@type": "SportsEvent",
        "name": data.get("seName"),
        "description": data.get("seDesc"),
        "sport": sport,
        "startDate": data.get("seStartDate"),
        "endDate": data.get("seEndDate"), # REQUERIDO
        "eventStatus": data.get("seStatus"),
        "image": [data.get("seImage")] if data.get("seImage") else [],
        "homeTeam": {"@type": "SportsTeam", "name": t_a},
        "awayTeam": {"@type": "SportsTeam", "name": t_b},
        "performer": [ # REQUERIDO
            {"@type": "SportsTeam", "name": t_a},
            {"@type": "SportsTeam", "name": t_b}
        ],
        "organizer": { # REQUERIDO
            "@type": "Organization",
            "name": data.get("seOrganizer") or "BetUS",
            "url": "https://www.betus.com.pa"
        },
        "location": {
            "@type": "Place",
            "name": data.get("seStadium"),
            "address": {
                "@type": "PostalAddress",
                "addressLocality": data.get("seCity"),
                "addressRegion": data.get("seRegion"),
                "addressCountry": data.get("seCountry") or "US"
            }
        },
        "offers": {
            "@type": "Offer",
            "url": data.get("seOfferUrl"),
            "availability": "https://schema.org/InStock", # REQUERIDO
            "price": data.get("seOfferPrice") or "0",
            "priceCurrency": "USD",
            "validFrom": data.get("seValidFrom") # REQUERIDO
        }
    }
    
    return schema
def gen_parlay(data):
    # Estructura de Parlay basada en CreativeWork + ItemList
    schema = {
        "@context": "https://schema.org",
        "@type": "CreativeWork",
        "name": data.get("parlayName"),
        "description": data.get("parlayDesc"),
        "author": {"@type": "Organization", "name": data.get("seOrganizer") or "BetUS"},
        "offers": {
            "@type": "Offer",
            "name": "Total Parlay Odds",
            "price": data.get("parlayTotalOdds"),
            "priceCurrency": "USD",
            "url": data.get("parlayUrl"),
            "availability": "https://schema.org/InStock",
            "validFrom": data.get("seValidFrom")
        },
        "mainEntity": {
            "@type": "ItemList",
            "name": "Parlay Selection Details",
            "numberOfItems": 0,
            "itemListElement": []
        }
    }

    legs = []
    # Recorremos los 7 posibles picks del parlay
    for i in range(1, 8):
        p_event = data.get(f"pPick{i}Event")
        p_name = data.get(f"pPick{i}Name")
        p_odds = data.get(f"pPick{i}Price")
        
        if p_event and p_name:
            legs.append({
                "@type": "ListItem",
                "position": len(legs) + 1,
                "item": {
                    "@type": "Offer",
                    "name": p_name,
                    "price": p_odds,
                    "itemOffered": {
                        "@type": "SportsEvent",
                        "name": p_event
                    }
                }
            })

    schema["mainEntity"]["itemListElement"] = legs
    schema["mainEntity"]["numberOfItems"] = len(legs)
    return schema
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_schema', methods=['POST'])
def generate():
    stype = request.form.get('schemaType')
    data = request.form.to_dict()
    
    if stype == 'FAQPage': res = gen_faq(data)
    elif stype == 'BlogPosting': res = gen_blog(data)
    elif stype == 'Review': res = gen_review(data)
    else: res = gen_sports(data)
    elif stype == 'Parlay': res = gen_parlay(data)
    return jsonify(clean_nones(res))

if __name__ == '__main__':
    app.run(debug=True)
