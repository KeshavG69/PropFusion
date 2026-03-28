"""
PropFusion MVP - Pennsylvania Properties Only
Fetches all for-sale properties in Pennsylvania using HasData Zillow API
"""
import os
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Pennsylvania Cities (Major markets)
PENNSYLVANIA_CITIES = [
    "Philadelphia",
    "Pittsburgh",
    "Allentown",
    "Erie",
    "Reading",
    "Scranton",
    "Bethlehem",
    "Lancaster",
    "Harrisburg",
    "York",
    "Wilkes-Barre",
    "Chester",
    "Altoona",
    "Easton"
]

# API Configuration
BASE_URL = "https://api.hasdata.com/scrape/zillow/listing"
API_KEY = os.getenv('HASDATA_API_KEY')

def fetch_city_properties(city: str):
    """Fetch properties for a Pennsylvania city from Zillow"""

    location = f"{city}, PA"
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(
            BASE_URL,
            headers=headers,
            params={
                "keyword": location,
                "type": "forSale"
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            properties = data.get('properties', data.get('results', data))

            if isinstance(properties, list):
                return properties
            else:
                print(f"  ⚠️  Unexpected response format")
                return []

        elif response.status_code == 429:
            print(f"  ⚠️  Rate limit hit!")
            return None  # Signal rate limit

        else:
            print(f"  ❌ Error {response.status_code}")
            return []

    except Exception as e:
        print(f"  ❌ Exception: {str(e)}")
        return []

def transform_to_propfusion_schema(zillow_property: dict, city: str) -> dict:
    """Transform Zillow data to PropFusion schema"""

    address = zillow_property.get('address', {})

    return {
        # Core Property Info
        "property_id": f"zillow_{zillow_property.get('id')}",
        "source": "zillow",
        "source_id": zillow_property.get('id'),
        "source_url": zillow_property.get('url'),

        # Address
        "street_address": address.get('street', ''),
        "city": address.get('city', city),
        "state": "PA",
        "zip_code": address.get('zipcode', ''),
        "full_address": zillow_property.get('addressRaw', ''),

        # Location (for MongoDB geo-spatial queries)
        "location": {
            "type": "Point",
            "coordinates": [
                zillow_property.get('longitude'),
                zillow_property.get('latitude')
            ]
        },
        "latitude": zillow_property.get('latitude'),
        "longitude": zillow_property.get('longitude'),

        # Property Details
        "property_type": zillow_property.get('homeType', ''),
        "beds": zillow_property.get('beds'),
        "baths": zillow_property.get('baths'),
        "sqft": zillow_property.get('area'),
        "lot_size": zillow_property.get('lotAreaValue'),
        "lot_size_units": zillow_property.get('lotAreaUnits', 'sqft'),

        # Pricing
        "list_price": zillow_property.get('price'),
        "currency": zillow_property.get('currency', 'USD'),

        # Zillow-Specific Data
        "zestimate": zillow_property.get('zestimate'),
        "rent_estimate": zillow_property.get('rentZestimate'),
        "days_on_zillow": zillow_property.get('daysOnZillow'),

        # Listing Info
        "status": zillow_property.get('status', 'FOR_SALE'),
        "image_url": zillow_property.get('image'),

        # Investment Metrics (calculated below)
        "investment_metrics": {},

        # Metadata
        "scraped_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat()
    }

def calculate_investment_metrics(property_data: dict) -> dict:
    """Calculate investment metrics using Zillow's rent estimate"""

    list_price = property_data.get('list_price')
    rent_estimate = property_data.get('rent_estimate')

    if not list_price or not rent_estimate:
        property_data['investment_metrics'] = {
            "cap_rate": None,
            "monthly_cash_flow": None,
            "investment_score": None
        }
        return property_data

    # Conservative estimates
    annual_rent = rent_estimate * 12
    operating_expenses_rate = 0.35  # 35% of rent for taxes, insurance, maintenance, vacancies
    annual_expenses = annual_rent * operating_expenses_rate
    noi = annual_rent - annual_expenses

    # Cap Rate = (NOI / Purchase Price) * 100
    cap_rate = (noi / list_price) * 100 if list_price > 0 else 0

    # Monthly Cash Flow (assuming 20% down, 7% interest, 30yr mortgage)
    down_payment = list_price * 0.20
    loan_amount = list_price - down_payment
    monthly_payment = loan_amount * 0.00665  # Approx monthly payment factor for 7% 30yr
    monthly_expenses = annual_expenses / 12
    monthly_cash_flow = rent_estimate - monthly_expenses - monthly_payment

    # Investment Score (0-100 scale)
    # Weighted: Cap Rate (40%), Cash Flow (30%), Rent-to-Price ratio (30%)
    cap_rate_score = min(cap_rate * 10, 40)  # Cap at 40 points
    cash_flow_score = min((monthly_cash_flow / 10), 30) if monthly_cash_flow > 0 else 0
    rent_ratio_score = min((rent_estimate / (list_price / 1000)) * 30, 30)
    investment_score = cap_rate_score + cash_flow_score + rent_ratio_score

    property_data['investment_metrics'] = {
        "cap_rate": round(cap_rate, 2),
        "monthly_cash_flow": round(monthly_cash_flow, 2),
        "annual_noi": round(noi, 2),
        "investment_score": round(investment_score, 2),
        "rent_to_price_ratio": round((rent_estimate / (list_price / 1000)), 2)
    }

    return property_data

def main():
    """Main execution function"""

    print("=" * 70)
    print("PROPFUSION MVP - PENNSYLVANIA PROPERTIES")
    print("=" * 70)
    print()

    if not API_KEY:
        print("❌ ERROR: HASDATA_API_KEY not found in .env file")
        return

    print(f"📊 Collecting properties from {len(PENNSYLVANIA_CITIES)} PA cities")
    print(f"🔑 API Key: {API_KEY[:10]}...")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    all_properties = []
    api_calls_used = 0

    for i, city in enumerate(PENNSYLVANIA_CITIES, 1):
        print(f"[{i}/{len(PENNSYLVANIA_CITIES)}] 🏘️  {city}, PA...", end=" ")

        properties = fetch_city_properties(city)

        if properties is None:
            # Rate limit hit
            print(f"\n⚠️  Rate limit exceeded at city {i}.")
            print(f"   Collected {len(all_properties)} properties from {i-1} cities so far.")
            break

        if properties:
            api_calls_used += 1
            print(f"✅ {len(properties)} properties")

            # Transform and calculate metrics
            for prop in properties:
                transformed = transform_to_propfusion_schema(prop, city)
                transformed = calculate_investment_metrics(transformed)
                all_properties.append(transformed)

            # Rate limiting - be nice to the API
            time.sleep(2)
        else:
            print(f"⚠️  0 properties")

    print()
    print("=" * 70)
    print("COLLECTION COMPLETE")
    print("=" * 70)
    print(f"✅ Total Properties: {len(all_properties)}")
    print(f"🏙️  Cities Processed: {api_calls_used}/{len(PENNSYLVANIA_CITIES)}")
    print(f"🔥 API Calls Used: {api_calls_used}/1000 (free tier)")
    print()

    # Save to JSON
    output_file = f"data/pennsylvania_properties_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(all_properties, f, indent=2)

    print(f"💾 Saved to: {output_file}")

    # Statistics
    if all_properties:
        print()
        print("=" * 70)
        print("STATISTICS")
        print("=" * 70)

        with_metrics = sum(1 for p in all_properties
                          if p.get('investment_metrics', {}).get('cap_rate'))

        properties_with_price = [p for p in all_properties if p.get('list_price')]
        properties_with_rent = [p for p in all_properties if p.get('rent_estimate')]

        if properties_with_price:
            avg_price = sum(p['list_price'] for p in properties_with_price) / len(properties_with_price)
            print(f"Average Price: ${avg_price:,.0f}")

        if properties_with_rent:
            avg_rent = sum(p['rent_estimate'] for p in properties_with_rent) / len(properties_with_rent)
            print(f"Average Rent: ${avg_rent:,.0f}/month")

        print(f"Properties with Investment Metrics: {with_metrics} ({with_metrics/len(all_properties)*100:.1f}%)")

        # Top 5 by Cap Rate
        print()
        print("🏆 TOP 5 PROPERTIES BY CAP RATE:")
        sorted_props = sorted(
            [p for p in all_properties if p.get('investment_metrics', {}).get('cap_rate')],
            key=lambda x: x['investment_metrics']['cap_rate'],
            reverse=True
        )[:5]

        for i, prop in enumerate(sorted_props, 1):
            metrics = prop['investment_metrics']
            print(f"  {i}. {prop['city']}, PA")
            print(f"     ${prop['list_price']:,} | Cap Rate: {metrics['cap_rate']:.2f}% | "
                  f"Cash Flow: ${metrics['monthly_cash_flow']:.0f}/mo")

        # Top 5 by Investment Score
        print()
        print("🌟 TOP 5 PROPERTIES BY INVESTMENT SCORE:")
        sorted_props = sorted(
            [p for p in all_properties if p.get('investment_metrics', {}).get('investment_score')],
            key=lambda x: x['investment_metrics']['investment_score'],
            reverse=True
        )[:5]

        for i, prop in enumerate(sorted_props, 1):
            metrics = prop['investment_metrics']
            print(f"  {i}. {prop['city']}, PA")
            print(f"     Score: {metrics['investment_score']:.1f}/100 | "
                  f"${prop['list_price']:,} | Cap Rate: {metrics['cap_rate']:.2f}%")

    print()
    print("✅ Pennsylvania data collection complete!")
    print("📊 Ready to import to MongoDB!")
    print()

if __name__ == "__main__":
    main()
