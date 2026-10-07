from flask import Flask, render_template, request, jsonify
import json
from datetime import datetime, timedelta

app = Flask(__name__)

# --- Limpiador de diccionarios (Elimina campos vacíos) ---
def clean_nones(value):
    if isinstance(value, dict):
        return {k: v for k, v in ((k, clean_nones(v)) for k, v in value.items()) if v is not None and v != ""}
    if isinstance(value, list):
        return [v for v in (clean_nones(v) for v in value) if v is not None and v != ""]
    return value

# --- HELPERS PARA PARLAYS Y EVENTOS ---
def calculate_end_date(start_str):
    if not start_str:
        start_dt = datetime.now()
    else:
        try:
            start_dt = datetime.fromisoformat(start_str)
        except Exception:
            try:
                start_dt = datetime.strptime(start_str, "%Y-%m-%dT%H:%M")
            except Exception:
                start_dt = datetime.now()
                
    end_dt = start_dt + timedelta(hours=3, minutes=30)
    return end_dt.isoformat()

def extract_teams_and_venue(event_name, stadium=None, city=None, region=None):
    if not event_name:
        return [], "Sports Stadium", "United States", "US"

    separators = [" vs. ", " vs ", " VS. ", " VS ", " @ ", " at ", " AT ", " v ", " - "]
    team_a, team_b = None, None
    home_team = event_name

    for sep in separators:
        if sep in event_name:
            parts = event_name.split(sep, 1)
            team_a = parts[0].strip()
            team_b = parts[1].strip()
            home_team = team_b
            break

    if team_a and team_b:
        performers = [
            {"@type": "SportsTeam", "name": team_a},
            {"@type": "SportsTeam", "name": team_b}
        ]
    else:
        performers = [{"@type": "SportsTeam", "name": event_name.strip()}]

    venue_name = stadium if stadium else f"{home_team} Stadium"
    venue_city = city if city else "United States"
    venue_region = region if region else "US"

    return performers, venue_name, venue_city, venue_region

# --- GENERADORES DE SCHEMA ---

def gen_faq(data):
    main_entity = []
    for i in range(1, 21):
        question = data.get(f"faqQ{i}")
        answer = data.get(f"faqA{i}")
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

    all_offers = []
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

    schema["offers"] = all_offers
    return schema

def gen_parlay(data):
    legs = []
    parlay_url = data.get("parlayUrl") or "https://www.betus.com.pa/sportsbook/"

    for i in range(1, 21):
        event = data.get(f"pPick{i}Event")
        pick_name = data.get(f"pPick{i}Name")
        odds = data.get(f"pPick{i}Price")

        if event and pick_name:
            start_date = data.get(f"pPick{i}Start") or datetime.now().isoformat()
            end_date = data.get(f"pPick{i}End") or calculate_end_date(start_date)

            stadium_input = data.get(f"pPick{i}Stadium")
            city_input = data.get(f"pPick{i}City")
            region_input = data.get(f"pPick{i}Region")
            performers, venue_name, venue_city, venue_region = extract_teams_and_venue(
                event, stadium_input, city_input, region_input
            )

            leg_offer = {
                "@type": "Offer",
                "name": pick_name,
                "price": str(odds) if odds else "0",
                "priceCurrency": "USD",
                "url": parlay_url,
                "availability": "https://schema.org/InStock",
                "validFrom": start_date
            }

            sports_event = {
                "@type": "SportsEvent",
                "name": event,
                "description": f"Live odds, spread, and betting analysis for {event}.",
                "image": [
                    "https://www.betus.com.pa/wp-content/themes/betus/assets/images/logo.png"
                ],
                "startDate": start_date,
                "endDate": end_date,
                "eventStatus": "https://schema.org/EventScheduled",
                "performer": performers,
                "location": {
                    "@type": "Place",
                    "name": venue_name,
                    "address": {
                        "@type": "PostalAddress",
                        "addressLocality": venue_city,
                        "addressRegion": venue_region,
                        "addressCountry": "US"
                    }
                },
                "organizer": {
                    "@type": "Organization",
                    "name": "BetUS",
                    "url": "https://www.betus.com.pa"
                },
                "offers": [leg_offer]
            }

            legs.append({
                "@type": "ListItem",
                "position": len(legs) + 1,
                "item": {
                    "@type": "Offer",
                    "name": pick_name,
                    "price": str(odds) if odds else "0",
                    "priceCurrency": "USD",
                    "url": parlay_url,
                    "availability": "https://schema.org/InStock",
                    "itemOffered": sports_event
                }
            })

    return {
        "@context": "https://schema.org",
        "@type": "CreativeWork",
        "name": data.get("parlayName") or "Parlay Picks & Predictions",
        "description": data.get("parlayDesc") or "Expert multi-leg parlay selections and odds.",
        "offers": {
            "@type": "Offer",
            "name": "Total Parlay Odds",
            "price": str(data.get("parlayTotalOdds")) if data.get("parlayTotalOdds") else "0",
            "priceCurrency": "USD",
            "url": parlay_url,
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
    
    for i in range(1, 11):
        p = data.get(f"tkPoint{i}")
        if p and p.strip():
            points.append(p)

    schema = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"Key Takeaways: {theme}",
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

    list_items = "".join([f'<li style="margin-bottom: 8px;">{p}</li>' for p in points])
    visual_html = f'''<div style="margin: 25px auto; max-width: 650px; background-color: #f8fafc; border-left: 4px solid #013369; border-top: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; border-radius: 0 8px 8px 0; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;"><h2 style="margin: 0 0 12px 0; font-size: 1.2rem; font-weight: 700; color: #013369; display: flex; align-items: center; gap: 8px; border: none; background: none; padding: 0;">{icon} Key Takeaways: {theme}</h2><ul style="margin: 0; padding-left: 20px; color: #334155; font-size: 0.95rem; line-height: 1.6;">{list_items}</ul></div>'''

    return {
        "visual": visual_html,
        "schema": schema
    }

# --- RUTAS DE FLASK ---

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
