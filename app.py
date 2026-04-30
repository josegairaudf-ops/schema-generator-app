from flask import Flask, render_template, request, jsonify
import json
from datetime import datetime # Todavía útil para isoformat si lo usas

app = Flask(__name__)

# --- Funciones de Generación de Esquemas (Minimalistas y sin DB) ---
# Si estas funciones no las usas con tu formulario actual, puedes eliminarlas.
# Las he dejado como placeholders simplificados.
def generate_faq_schema(data):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [{
            "@type": "Question",
            "name": data.get("faqQuestion", "Pregunta de Ejemplo"),
            "acceptedAnswer": {
                "@type": "Answer",
                "text": data.get("faqAnswer", "Respuesta de Ejemplo")
            }
        }]
    }

def generate_blog_schema(data):
    return {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": data.get("blogHeadline", "Titular de Blog Ejemplo"),
        "datePublished": data.get("blogDatePublished", datetime.now().isoformat())
    }

def generate_review_schema(data):
    return {
        "@context": "https://schema.org",
        "@type": "Review",
        "itemReviewed": {
            "@type": "Thing",
            "name": data.get("reviewItem", "Item de Revisión Ejemplo")
        },
        "reviewRating": {
            "@type": "Rating",
            "ratingValue": data.get("reviewRating", "4.5"),
            "bestRating": "5"
        }
    }

# --- Función Principal de Generación de SportsEvent y Parlays (sin DB) ---
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
    sport_name = league_to_sport.get(league_value)

    if league_value == "Other":
        league = data.get("seLeagueCustom") or "Other"
        sport_name = data.get("seSportCustom") or "Sports"

    home_team = data.get("seTeamA") or data.get("seTeamACustom")
    away_team = data.get("seTeamB")

    schema = {
        "@context": "https://schema.org",
        "@type": "SportsEvent",
        "@id": data.get("seUrl") if data.get("seUrl") else None,
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
            } if data.get("seCity") or data.get("seRegion") or data.get("seCountry") else None
        } if data.get("seStadium") else None,
        "competitor": [
            {"@type": "SportsTeam", "name": home_team} if home_team else None,
            {"@type": "SportsTeam", "name": away_team} if away_team else None
        ],
        "url": data.get("seUrl"),
        "image": data.get("seImage"),
        "description": data.get("seDescription"),
        "isAccessibleForFree": is_free,
        "inLanguage": data.get("seLanguage")
    }

    # Limpiar campos None en location y competitor
    if schema.get("location") and schema["location"]["address"] is None:
        del schema["location"]["address"]
    if schema.get("competitor"):
        schema["competitor"] = [comp for comp in schema["competitor"] if comp is not None]

    # Inicializa la lista de offers DENTRO del esquema
    schema["offers"] = []

    # Helper interno para no repetir código y añadir offers directamente al esquema
    def add_offer_to_schema(name_key, price_key, url_key, description_key=None):
        name = data.get(name_key)
        price = data.get(price_key)
        url = data.get(url_key)
        description = data.get(description_key) if description_key else None

        if name or price or url or description:
            offer_item = {
                "@type": "Offer",
                "name": name,
                "price": price,
                "priceCurrency": "USD",
                "url": url
            }
            if description:
                offer_item["description"] = description
            if url:
                cleaned_name = (name or "no-name").lower().replace(" ", "-").replace(":", "").replace("/", "").replace("#", "").replace(".", "")
                offer_item["@id"] = url + "#" + cleaned_name[:50]
            schema["offers"].append(offer_item)

    # 0) Offer “principal”
    add_offer_to_schema("seOfferName", "seOfferPrice", "seOfferUrl")

    # 1) Picks 1 a 7
    add_offer_to_schema("pick1Name", "pick1Price", "pick1Url")
    add_offer_to_schema("pick2Name", "pick2Price", "pick2Url")
    add_offer_to_schema("pick3Name", "pick3Price", "pick3Url")
    add_offer_to_schema("pick4Name", "pick4Price", "pick4Url")
    add_offer_to_schema("pick5Name", "pick5Price", "pick5Url")
    add_offer_to_schema("pick6Name", "pick6Price", "pick6Url")
    add_offer_to_schema("pick7Name", "pick7Price", "pick7Url")

    # -------------------------
    # Añadir la Offer de Parlay
    # -------------------------
    parlay_name = data.get('parlayName')
    parlay_description = data.get('parlayDescription')
    parlay_odds = data.get('parlayOdds')
    parlay_url = data.get('parlayUrl')

    if parlay_name or parlay_odds or parlay_url or parlay_description:
        parlay_offer = {
            "@type": "Offer",
            "name": parlay_name,
            "description": parlay_description,
            "price": parlay_odds,
            "priceCurrency": "USD",
            "url": parlay_url
        }
        if parlay_url:
            cleaned_parlay_name = (parlay_name or "no-name-parlay").lower().replace(" ", "-").replace(":", "").replace("/", "").replace("#", "").replace(".", "")
            parlay_offer["@id"] = parlay_url + "#" + cleaned_parlay_name[:50]
        schema["offers"].append(parlay_offer)

    # Limpiar offers vacías si no hay datos significativos
    schema["offers"] = [offer for offer in schema["offers"] if any(k for k in offer if k not in ["@type", "@id"] and offer[k] is not None)]

    return schema

# --- Rutas de la Aplicación ---
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
    elif schema_type == 'SportsEvent':
        generated_schema = generate_sportsevent_schema(form_data)
    else: # Por defecto, si no se especifica un tipo válido
        generated_schema = generate_sportsevent_schema(form_data)

    generated_schema = {k: v for k, v in generated_schema.items() if v is not None}
    
    if 'location' in generated_schema and generated_schema['location']:
        if generated_schema['location'].get('address') is None:
            del generated_schema['location']['address']
        if not any(generated_schema['location'].values()):
            del generated_schema['location']

    schema_json = json.dumps(generated_schema, indent=2)

    return render_template('result.html', schema_json=schema_json)

# --- Ejecutar la Aplicación ---
if __name__ == '__main__':
    # La línea db.create_all() y la gestión de la DB se han eliminado completamente
    app.run(debug=True)
