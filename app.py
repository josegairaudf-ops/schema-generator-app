from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import json
from datetime import datetime

app = Flask(__name__)

# --- Configuración de la Base de Datos (MySQL) ---
# Asegúrate de que 'root' no tenga contraseña en XAMPP o actualiza aquí
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/schema_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Modelos de Base de Datos ---
# Estas clases se usaron inicialmente. Si tu sistema ya no las usa con 'generate_schema',
# puedes comentar o eliminar si no necesitas guardar los datos en MySQL para cada generación.
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    location_name = db.Column(db.String(255))
    sport = db.Column(db.String(100))
    description = db.Column(db.Text)
    # Si quieres que Event tenga una relación con Pick:
    # picks = db.relationship('Pick', backref='event', lazy=True)
    def __repr__(self):
        return f'<Event {self.name}>'

class Pick(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    author_name = db.Column(db.String(100))
    prediction = db.Column(db.Text, nullable=False)
    odds = db.Column(db.String(50))
    bookmaker = db.Column(db.String(100))
    analysis = db.Column(db.Text)
    pick_info_6 = db.Column(db.String(255)) # Columna extra si la mantienes
    # pick_info_7 = db.Column(db.String(255)) # Si añades un 7mo campo en el modelo

    def __repr__(self):
        return f'<Pick {self.prediction} for Event {self.event_id}>'

# --- Funciones de Generación de Esquemas (Placeholders) ---
# Asegúrate de que estas funciones existan si las usas en '/generate_schema'
def generate_faq_schema(data):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": data.get("faqQuestion"), "acceptedAnswer": {"@type": "Answer", "text": data.get("faqAnswer")}}]}

def generate_blog_schema(data):
    return {"@context": "https://schema.org", "@type": "BlogPosting", "headline": data.get("blogHeadline"), "datePublished": data.get("blogDatePublished")}

def generate_review_schema(data):
    return {"@context": "https://schema.org", "@type": "Review", "itemReviewed": {"@type": "Thing", "name": data.get("reviewItem")}, "reviewRating": {"@type": "Rating", "ratingValue": data.get("reviewRating")}}

# --- Función Principal de Generación de SportsEvent y Parlays ---
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
    # Añadimos description_key para poder incluir descripciones en las offers, útil para parlays
    def add_offer_to_schema(name_key, price_key, url_key, description_key=None):
        name = data.get(name_key)
        price = data.get(price_key)
        url = data.get(url_key)
        description = data.get(description_key) if description_key else None

        if name or price or url or description: # Comprobar si hay algún dato para crear la oferta
            offer_item = {
                "@type": "Offer",
                "name": name,
                "price": price,
                "priceCurrency": "USD", # Asumo USD, puedes hacerlo configurable
                "url": url
            }
            if description:
                offer_item["description"] = description
            if url: # Opcional: genera un @id si hay URL
                # Asegura que el ID sea válido eliminando caracteres especiales y limitando longitud
                cleaned_name = (name or "no-name").lower().replace(" ", "-").replace(":", "").replace("/", "").replace("#", "").replace(".", "")
                offer_item["@id"] = url + "#" + cleaned_name[:50]
            schema["offers"].append(offer_item)

    # 0) Offer “principal” (los campos que ya tenías)
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
    # Las claves de los campos de input HTML para el parlay serán 'parlayName', 'parlayDescription', 'parlayOdds', 'parlayUrl'
    parlay_name = data.get('parlayName')
    parlay_description = data.get('parlayDescription')
    parlay_odds = data.get('parlayOdds')
    parlay_url = data.get('parlayUrl')

    if parlay_name or parlay_odds or parlay_url or parlay_description: # Si hay algún dato de parlay
        parlay_offer = {
            "@type": "Offer",
            "name": parlay_name,
            "description": parlay_description,
            "price": parlay_odds,
            "priceCurrency": "USD", # Asumo USD
            "url": parlay_url
        }
        if parlay_url: # Genera un @id para el parlay offer
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
    schema_type = request.form.get('schemaType') # Campo oculto o select en el HTML para elegir tipo de esquema
    
    # Si este formulario SIEMPRE generará SportsEvent, puedes forzar el tipo aquí
    # schema_type = 'SportsEvent' 
    
    form_data = request.form.to_dict()
    generated_schema = {}
    
    # Lógica para seleccionar el generador de esquema basado en 'schema_type'
    if schema_type == 'FAQPage':
        generated_schema = generate_faq_schema(form_data)
    elif schema_type == 'BlogPosting':
        generated_schema = generate_blog_schema(form_data)
    elif schema_type == 'Review':
        generated_schema = generate_review_schema(form_data)
    elif schema_type == 'SportsEvent':
        generated_schema = generate_sportsevent_schema(form_data)
    else: # Si no se especifica o es inválido, asumimos SportsEvent para este contexto
        generated_schema = generate_sportsevent_schema(form_data)

    # Limpiar el esquema de campos con valor None para un JSON más limpio
    generated_schema = {k: v for k, v in generated_schema.items() if v is not None}
    
    # Asegúrate de limpiar sub-diccionarios también si tienen None y no son útiles
    if 'location' in generated_schema and generated_schema['location']:
        if generated_schema['location'].get('address') is None:
            del generated_schema['location']['address']
        if not any(generated_schema['location'].values()): # Si location está vacío después de limpiar address
            del generated_schema['location']

    # Convertir el diccionario a JSON formateado para mostrarlo en result.html
    schema_json = json.dumps(generated_schema, indent=2)

    return render_template('result.html', schema_json=schema_json)

# --- Ejecutar la Aplicación ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Crea las tablas en la base de datos si no existen
    app.run(debug=True)
