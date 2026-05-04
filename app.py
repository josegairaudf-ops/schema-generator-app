from flask import Flask, render_template, request, jsonify
import json

app = Flask(__name__)

def generate_sportsevent_schema(data):
    league_val = data.get("seSport")
    
    # Lógica de Deporte/Liga
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
                "addressCountry": data.get("seCountry")
            }
        } if data.get("seStadium") else None,
        "competitor": [
            {"@type": "SportsTeam", "name": team_a},
            {"@type": "SportsTeam", "name": team_b}
        ],
        "image": data.get("seImage"),
        "inLanguage": data.get("seLanguage"),
        "offers": []
    }

    # Añadir Oferta Principal
    if data.get("seOfferName") or data.get("seOfferPrice"):
        schema["offers"].append({
            "@type": "Offer",
            "name": data.get("seOfferName"),
            "price": data.get("seOfferPrice"),
            "priceCurrency": "USD",
            "url": data.get("seOfferUrl")
        })

    # Añadir Picks 1-7
    for i in range(1, 8):
        name = data.get(f"pick{i}Name")
        price = data.get(f"pick{i}Price")
        if name or price:
            schema["offers"].append({
                "@type": "Offer",
                "name": name,
                "price": price,
                "priceCurrency": "USD",
                "url": data.get(f"pick{i}Url")
            })

    return schema

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_schema', methods=['POST'])
def generate_schema():
    return jsonify(generate_sportsevent_schema(request.form.to_dict()))

if __name__ == '__main__':
    app.run(debug=True)
