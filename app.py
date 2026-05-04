from flask import Flask, render_template, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

def generate_sportsevent_schema(data):
    is_free = bool(data.get('seFree'))
    league_value = data.get("seSport")
    
    league_to_sport = {
        "NFL": "American Football",
        "NBA": "Basketball",
        "MLB": "Baseball",
        "NHL": "Ice Hockey",
    }

    league = league_value
    sport_name = league_to_sport.get(league_value, "Sports")

    if league_value == "Other":
        league = data.get("seLeagueCustom") or "Other"
        sport_name = data.get("seSportCustom") or "Sports"

    home_team = data.get("seTeamA")
    away_team = data.get("seTeamB")

    schema = {
        "@context": "https://schema.org",
        "@type": "SportsEvent",
        "name": data.get("seName"),
        "sport": sport_name,
        "league": league,
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
        } if data.get("seStadium") else None,
        "url": data.get("seUrl"),
        "image": data.get("seImage"),
        "description": data.get("seDescription"),
        "isAccessibleForFree": is_free
    }

    # Limpieza de nulos
    if schema.get("location") and not schema["location"].get("name"):
        del schema["location"]

    # Ofertas y Picks
    offers = []
    
    # Función auxiliar para añadir ofertas
    def add_offer(name, price, url):
        if name or price:
            offers.append({
                "@type": "Offer",
                "name": name,
                "price": price,
                "priceCurrency": "USD",
                "url": url
            })

    # Oferta Principal
    add_offer(data.get("seOfferName"), data.get("seOfferPrice"), data.get("seOfferUrl"))

    # Picks 1 al 7
    for i in range(1, 8):
        add_offer(
            data.get(f"pick{i}Name"), 
            data.get(f"pick{i}Price"), 
            data.get(f"pick{i}Url")
        )

    schema["offers"] = offers
    return schema

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_schema', methods=['POST'])
def generate_schema():
    form_data = request.form.to_dict()
    # Forzamos a SportsEvent ya que es la herramienta que funciona
    generated_schema = generate_sportsevent_schema(form_data)
    return jsonify(generated_schema)

if __name__ == '__main__':
    app.run(debug=True)
