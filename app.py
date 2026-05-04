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
    # Lógica de liga y equipos
    l_val = data.get("seSport")
    if l_val == "Other":
        league, sport = data.get("seLeagueCustom"), data.get("seSportCustom")
        t_a, t_b = data.get("seTeamACustom"), data.get("seTeamBCustom")
    else:
        league = l_val
        sport = {"NFL": "American Football", "NBA": "Basketball", "MLB": "Baseball", "NHL": "Ice Hockey"}.get(l_val, "Sports")
        t_a, t_b = data.get("seTeamA"), data.get("seTeamB")

    schema = {
        "@context": "https://schema.org",
        "@type": "SportsEvent",
        "name": data.get("seName"),
        "description": data.get("seDesc"),
        "sport": sport,
        "league": league,
        "startDate": data.get("seStartDate"),
        "endDate": data.get("seEndDate"),
        "eventStatus": data.get("seStatus"),
        "eventAttendanceMode": data.get("seMode"),
        "inLanguage": data.get("seLang"),
        "image": data.get("seImage"),
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
            {"@type": "SportsTeam", "name": t_a},
            {"@type": "SportsTeam", "name": t_b}
        ],
        "offers": []
    }

    # Picks (Principal + 7 adicionales)
    def add_o(prefix):
        name, price, url = data.get(f"{prefix}Name"), data.get(f"{prefix}Price"), data.get(f"{prefix}Url")
        if name or price:
            schema["offers"].append({"@type": "Offer", "name": name, "price": price, "priceCurrency": "USD", "url": url})

    add_o("seOffer")
    for i in range(1, 8): add_o(f"pick{i}")
    
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
    
    return jsonify(clean_nones(res))

if __name__ == '__main__':
    app.run(debug=True)
