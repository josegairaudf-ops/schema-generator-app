from flask import Flask, render_template, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

# --- Limpiador de diccionarios (Elimina campos vacíos) ---
def clean_nones(value):
    if isinstance(value, dict):
        return {k: v for k, v in ((k, clean_nones(v)) for k, v in value.items()) if v is not None and v != ""}
    if isinstance(value, list):
        return [v for v in (clean_nones(v) for v in value) if v is not None and v != ""]
    return value

# --- GENERADORES ---

def gen_faq(data):
    main_entity = []
    
    # Buscamos pares de Q y A del 1 al 20 para capturar todas las dinámicas
    for i in range(1, 21):
        question = data.get(f"faqQ{i}")
        answer = data.get(f"faqA{i}")
        
        # Solo agregamos si ambos campos tienen contenido
        if question and answer:
            main_entity.append({
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": answer
                }
            })
            
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": main_entity
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
        "publisher": {"@type": "Organization", "name": data.get("blogPub", "BetUS")},
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
            "bestRating": "5"
        },
        "author": {"@type": "Person", "name": data.get("revAuthor")},
        "reviewBody": data.get("revBody")
    }

def gen_sports(data):
    l_val = data.get("seSport")
    if l_val == "Other":
        league = data.get("seLeagueCustom")
        sport = data.get("seSportCustom")
        t_a = data.get("seTeamACustom")
        t_b = data.get("seTeamBCustom")
    else:
        league = l_val
        sport_map = {"NFL": "American Football", "NBA": "Basketball", "MLB": "Baseball", "NHL": "Ice Hockey"}
        sport = sport_map.get(l_val, "Sports")
        t_a = data.get("seTeamA")
        t_b = data.get("seTeamB")

    # 1. Creamos la estructura base del evento
    schema = {
        "@context": "https://schema.org",
        "@type": "SportsEvent",
        "name": data.get("seName"),
        "description": data.get("seDesc"),
        "sport": sport,
        "league": league,
        "startDate": data.get("seStartDate"),
        "endDate": data.get("seEndDate"),
        "eventStatus": "https://schema.org/EventScheduled",
        "image": [data.get("seImage")] if data.get("seImage") else [],
        "homeTeam": {"@type": "SportsTeam", "name": t_a},
        "awayTeam": {"@type": "SportsTeam", "name": t_b},
        "performer": [
            {"@type": "SportsTeam", "name": t_a},
            {"@type": "SportsTeam", "name": t_b}
        ],
        "organizer": {
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
                "addressCountry": "US"
            }
        }
    }

    # 2. Lógica para agrupar todas las ofertas (Picks)
    all_offers = []

    # Agregar Oferta Principal (si existe)
    if data.get("seOfferName") or data.get("seOfferPrice"):
        all_offers.append({
            "@type": "Offer",
            "name": data.get("seOfferName") or "Main Market",
            "price": data.get("seOfferPrice") or "0",
            "priceCurrency": "USD",
            "url": data.get("seOfferUrl"),
            "availability": "https://schema.org/InStock",
            "validFrom": data.get("seValidFrom")
        })

    # Agregar los 7 Picks adicionales
    for i in range(1, 8):
        p_name = data.get(f"pick{i}Name")
        p_price = data.get(f"pick{i}Price")
        p_url = data.get(f"pick{i}Url")
        
        if p_name or p_price:
            all_offers.append({
                "@type": "Offer",
                "name": p_name or f"Pick {i}",
                "price": p_price or "0",
                "priceCurrency": "USD",
                "url": p_url or data.get("seOfferUrl"),
                "availability": "https://schema.org/InStock",
                "validFrom": data.get("seValidFrom")
            })

    # Asignamos la lista de ofertas al schema
    schema["offers"] = all_offers
    
    return schema
def gen_parlay(data):
    legs = []
    # Buscamos hasta 20 picks dinámicos
    for i in range(1, 21):
        event = data.get(f"pPick{i}Event")
        pick_name = data.get(f"pPick{i}Name")
        odds = data.get(f"pPick{i}Price")
        
        # Datos específicos por cada pick
        stadium = data.get(f"pPick{i}Stadium")
        city = data.get(f"pPick{i}City")
        region = data.get(f"pPick{i}Region")
        start = data.get(f"pPick{i}Start")
        end = data.get(f"pPick{i}End")

        if event and pick_name:
            legs.append({
                "@type": "ListItem",
                "position": len(legs) + 1,
                "item": {
                    "@type": "Offer",
                    "name": pick_name,
                    "price": odds,
                    "priceCurrency": "USD",
                    "itemOffered": {
                        "@type": "SportsEvent",
                        "name": event,
                        "startDate": start,
                        "endDate": end,
                        "eventStatus": "https://schema.org/EventScheduled",
                        "location": {
                            "@type": "Place",
                            "name": stadium,
                            "address": {
                                "@type": "PostalAddress",
                                "addressLocality": city,
                                "addressRegion": region,
                                "addressCountry": "US"
                            }
                        },
                        "organizer": {
                            "@type": "Organization",
                            "name": "BetUS",
                            "url": "https://www.betus.com.pa"
                        }
                    }
                }
            })

    return {
        "@context": "https://schema.org",
        "@type": "CreativeWork",
        "name": data.get("parlayName"),
        "description": data.get("parlayDesc"),
        "offers": {
            "@type": "Offer",
            "name": "Total Parlay Odds",
            "price": data.get("parlayTotalOdds"),
            "priceCurrency": "USD",
            "url": data.get("parlayUrl"),
            "availability": "https://schema.org/InStock"
        },
        "mainEntity": {
            "@type": "ItemList",
            "numberOfItems": len(legs),
            "itemListElement": legs
        }
    }
def gen_takeaways(data):
    theme = data.get("tkTheme", "General")
    icon = data.get("tkIcon", "💡")
    points = []
    
    # Buscamos puntos del 1 al 10 para capturar cualquier cantidad dinámica
    for i in range(1, 11):
        p = data.get(f"tkPoint{i}")
        if p and p.strip():
            points.append(p)

    # 1. Schema JSON-LD (ItemList Detectable)
    schema = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"Quick Takeaways: {theme}",
        "description": f"Key betting takeaways and strategic points for {theme}",
        "numberOfItems": len(points),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": idx + 1,
                "name": p.split(':')[0][:70],
                "description": p
            } for idx, p in enumerate(points)
        ]
    }

    # 2. HTML Visual
    list_items = "".join([f'<li style="margin-bottom: 8px;">{p}</li>' for p in points])
    visual_html = f'''<div style="margin: 25px auto; max-width: 650px; background-color: #f8fafc; border-left: 4px solid #013369; border-top: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; border-radius: 0 8px 8px 0; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;"><h2 style="margin: 0 0 12px 0; font-size: 1.2rem; font-weight: 700; color: #013369; display: flex; align-items: center; gap: 8px; border: none; background: none; padding: 0;">{icon} Quick Takeaways: {theme}</h2><ul style="margin: 0; padding-left: 20px; color: #334155; font-size: 0.95rem; line-height: 1.6;">{list_items}</ul></div>'''

    return {
        "visual": visual_html,
        "schema": schema
    }
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_schema', methods=['POST'])
def generate_schema():
    try:
        stype = request.form.get('schemaType')
        data = request.form.to_dict()
        
        if stype == 'FAQPage': 
            res = gen_faq(data)
        elif stype == 'BlogPosting': 
            res = gen_blog(data)
        elif stype == 'Review': 
            res = gen_review(data)
        elif stype == 'Parlay': 
            res = gen_parlay(data)
        elif stype == 'Takeaways':
            res = gen_takeaways(data)
        else: 
            res = gen_sports(data)
        
        return jsonify(clean_nones(res))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
