"""
Import Pennsylvania properties to MongoDB
"""
import os
import json
from pymongo import MongoClient, GEOSPHERE
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'propfusion')

def import_properties():
    """Import properties from JSON to MongoDB"""

    print("=" * 70)
    print("PROPFUSION - MONGODB IMPORT")
    print("=" * 70)
    print()

    # Find the latest Pennsylvania properties file
    import glob
    json_files = glob.glob('data/pennsylvania_properties_*.json')

    if not json_files:
        print("❌ No Pennsylvania properties JSON file found!")
        print("   Please run: python collect_pennsylvania_properties.py")
        return

    # Get the latest file
    latest_file = sorted(json_files)[-1]
    print(f"📄 Loading data from: {latest_file}")

    # Load properties
    with open(latest_file, 'r') as f:
        properties = json.load(f)

    print(f"✅ Loaded {len(properties)} properties")
    print()

    # Connect to MongoDB
    print("🔌 Connecting to MongoDB...")
    print(f"   URI: {MONGODB_URI[:50]}...")
    print(f"   Database: {MONGODB_DB_NAME}")

    try:
        client = MongoClient(MONGODB_URI)
        db = client[MONGODB_DB_NAME]

        # Test connection
        client.admin.command('ping')
        print("✅ MongoDB connected successfully!")
        print()

    except Exception as e:
        print(f"❌ MongoDB connection failed: {str(e)}")
        return

    # Get/Create properties collection
    collection = db['properties']

    # Check if collection exists and has data
    existing_count = collection.count_documents({})
    print(f"📊 Existing properties in database: {existing_count}")

    if existing_count > 0:
        print()
        response = input("⚠️  Collection has existing data. Drop and reimport? (yes/no): ")
        if response.lower() == 'yes':
            print("🗑️  Dropping existing collection...")
            collection.drop()
            collection = db['properties']
            print("✅ Collection dropped")
        else:
            print("❌ Import cancelled")
            return

    print()
    print("📥 Importing properties to MongoDB...")

    # Insert properties
    result = collection.insert_many(properties)

    print(f"✅ Imported {len(result.inserted_ids)} properties")
    print()

    # Create indexes
    print("🔧 Creating indexes...")

    # Geo-spatial index for location-based queries (skip properties with null coordinates)
    try:
        collection.create_index([("location", GEOSPHERE)])
        print("  ✅ Geo-spatial index on 'location'")
    except Exception as e:
        print(f"  ⚠️  Skipping geo-spatial index (some properties have null coordinates)")

    # Regular indexes
    collection.create_index("city")
    print("  ✅ Index on 'city'")

    collection.create_index("state")
    print("  ✅ Index on 'state'")

    collection.create_index("list_price")
    print("  ✅ Index on 'list_price'")

    collection.create_index("investment_metrics.cap_rate")
    print("  ✅ Index on 'cap_rate'")

    collection.create_index("investment_metrics.investment_score")
    print("  ✅ Index on 'investment_score'")

    collection.create_index("beds")
    print("  ✅ Index on 'beds'")

    collection.create_index("baths")
    print("  ✅ Index on 'baths'")

    print()

    # Show statistics
    print("=" * 70)
    print("DATABASE STATISTICS")
    print("=" * 70)

    total = collection.count_documents({})
    print(f"Total Properties: {total}")

    # Count by city
    pipeline = [
        {"$group": {"_id": "$city", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    cities = list(collection.aggregate(pipeline))

    print()
    print("Properties by City:")
    for city in cities[:10]:
        print(f"  {city['_id']}: {city['count']}")

    # Average metrics
    pipeline = [
        {"$match": {"investment_metrics.cap_rate": {"$ne": None}}},
        {"$group": {
            "_id": None,
            "avg_price": {"$avg": "$list_price"},
            "avg_cap_rate": {"$avg": "$investment_metrics.cap_rate"},
            "avg_cash_flow": {"$avg": "$investment_metrics.monthly_cash_flow"},
            "avg_score": {"$avg": "$investment_metrics.investment_score"}
        }}
    ]

    metrics = list(collection.aggregate(pipeline))

    if metrics:
        m = metrics[0]
        print()
        print("Average Investment Metrics:")
        print(f"  Price: ${m['avg_price']:,.0f}")
        print(f"  Cap Rate: {m['avg_cap_rate']:.2f}%")
        print(f"  Monthly Cash Flow: ${m['avg_cash_flow']:.0f}")
        print(f"  Investment Score: {m['avg_score']:.1f}/100")

    print()
    print("✅ Import complete! MongoDB is ready for FastAPI backend.")
    print()

if __name__ == "__main__":
    import_properties()
