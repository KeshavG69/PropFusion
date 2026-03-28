"""
Simple test script for Zillow scraper

Usage:
    python test_zillow_simple.py
"""

from zillow_scraper import fetch_zillow_properties
import json

def main():
    """Test Zillow scraper with single market"""

    print("\n" + "="*60)
    print("ZILLOW SCRAPER TEST")
    print("="*60 + "\n")

    # Test configuration
    test_location = "Dallas, TX"
    test_budget = 500000

    print(f"Testing: {test_location} under ${test_budget:,}")
    print("This will take 2-3 minutes...\n")

    # Fetch properties
    properties = fetch_zillow_properties(test_location, test_budget)

    if properties:
        print(f"\n{'='*60}")
        print(f"✓ SUCCESS! Retrieved {len(properties)} properties")
        print("="*60)

        # Show first 3 properties
        print("\nFirst 3 Properties:")
        for i, prop in enumerate(properties[:3], 1):
            print(f"\n{i}. {prop['address']}")
            print(f"   Price: ${prop['sale_price']:,}")
            print(f"   Size: {prop['beds']}bd/{prop['baths']}ba, {prop['sqft']:,} sqft")
            if prop['estimated_rent']:
                print(f"   Est. Rent: ${prop['estimated_rent']}/mo")
            if prop['property_url']:
                print(f"   URL: {prop['property_url']}")

        # Save to file
        output_file = "data/zillow_test_output.json"
        with open(output_file, 'w') as f:
            json.dump(properties, f, indent=2)

        print(f"\n✓ Full data saved to: {output_file}")

        # Summary stats
        avg_price = sum(p['sale_price'] for p in properties) / len(properties)
        avg_sqft = sum(p['sqft'] for p in properties if p['sqft'] > 0) / len([p for p in properties if p['sqft'] > 0])

        print(f"\nSummary Statistics:")
        print(f"  Total Properties: {len(properties)}")
        print(f"  Average Price: ${avg_price:,.0f}")
        print(f"  Average Size: {avg_sqft:,.0f} sqft")

    else:
        print("\n✗ No properties found")

if __name__ == "__main__":
    main()
