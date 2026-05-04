from flask import Flask, render_template, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

# --- Generadores de Esquemas Secundarios ---
def generate_faq_schema(data):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [{
            "@type": "Question",
            "name": data.get("faqQuestion"),
            "acceptedAnswer": {"@type": "Answer", "text": data.get("faqAnswer")}
        }]
    }

def generate_blog_schema(data):
    return {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": data.get("blogHeadline"),
        "datePublished": data.get("blogDatePublished") or datetime.now().isoformat(),
        "author": {"@type": "Person", "name": data.get("blogAuthor", "Expert")}
    }

def generate_review_schema(data):
    return {
        "@context": "https://schema.org",
        "@type": "Review",
        "itemReviewed": {"@type": "Thing", "name": data.get("reviewItem")},
        "reviewRating": {"@type": "Rating", "ratingValue": data.get("reviewRating", "5")},
        "reviewBody": data.get("reviewBody")
    }

# --- Generador de SportsEvent (El que recuperamos) ---
def generate_sportsevent_schema(data):
    league_val = data.get("seSport")
    if league_val == "Other":
        league = data.get("seLeagueCustom")
        sport = data.get("seSportCustom")
        team_a = data.get("seTeamACustom")
        team_b = data.get("seTeamBCustom")
    else:
        league = league_val
        sport_map = {"NFL": "American Football", "NBA": "Basketball", "MLB": "Baseball", "NHL": "Ice Hockey"}
        sport = sport_map.get(league_val, "Sports")
        team_a = data.get("seTeamA")
        team_b = data.get("seTeamB")

    schema = {
        "@context": "https://schema.org",
        "@type": "SportsEvent",
        "name": data.get("seName"),
        "sport": sport,
        "league": league,
        "startDate": data.get("seStartDate"),
        "eventStatus": data.get("seEventStatus"),
        "location": {
            "@type": "Place",
            "name": data.get("seStadium"),
            "address": {
                "@type": "PostalAddress",
                "addressLocality": data.get("seCity"),
                "addressRegion": data.get("seRegion"),
                "addressCountry": data.get("seCountry")
            }
        } if data.get("seStadium") else None,
        "competitor": [
            {"@type": "SportsTeam", "name": team_a} if team_a else None,
            {"@type": "SportsTeam", "name": team_b} if team_b else None
        ],
        "image": data.get("seImage"),
        "description": data.get("seDescription"),
        "offers": []
    }
    
    # Ofertas y Picks
    def add_off(n, p, u):
        if n or p:
            schema["offers"].append({"@type": "Offer", "name": n, "price": p, "priceCurrency": "USD", "url": u})

    add_off(data.get("seOfferName"), data.get("seOfferPrice"), data.get("seOfferUrl"))
    for i in range(1, 8):
        add_off(data.get(f"pick{i}Name"), data.get(f"pick{i}Price"), data.get(f"pick{i}Url"))

    return schema

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_schema', methods=['POST'])
def generate_schema():
    stype = request.form.get('schemaType')
    data = request.form.to_dict()
    
    if stype == 'FAQPage': res = generate_faq_schema(data)
    elif stype == 'BlogPosting': res = generate_blog_schema(data)
    elif stype == 'Review': res = generate_review_schema(data)
    else: res = generate_sportsevent_schema(data)
    
    return jsonify(res)

if __name__ == '__main__':
    app.run(debug=True)
