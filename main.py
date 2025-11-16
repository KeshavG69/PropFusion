from utils.agno_tools import create_fetch_properties_function

def main():
    """Example usage of fetch_properties function"""

    # # Example 1: Philadelphia properties under $500k
    # print("\n" + "="*60)
    # print("Example 1: Philadelphia, PA - Budget $500,000")
    # print("="*60)
    fetch_properties = create_fetch_properties_function(session_id="example_session_123",user_id="example_user_456")
    # properties = fetch_properties("Philadelphia, PA", 500000)

    # if properties:
    #     print(f"\nFound {len(properties)} properties:\n")
    #     for i, prop in enumerate(properties[:5], 1):  # Show first 5
    #         print(f"{i}. {prop['address']}")
    #         print(f"   Price: ${prop['sale_price']:,}")
    #         print(f"   Size: {prop['beds']}bd/{prop['baths']}ba, {prop['sqft']:,} sqft")
    #         if prop['estimated_rent']:
    #             print(f"   Est. Rent: ${prop['estimated_rent']}/mo")
    #         if prop['property_tax']:
    #             print(f"   Property Tax: ${prop['property_tax']}/yr")
    #         if prop['hoa']:
    #             print(f"   HOA: ${prop['hoa']}/mo")
    #         else:
    #             print(f"   HOA: Not available")
    #         print()

    #     if len(properties) > 5:
    #         print(f"... and {len(properties) - 5} more properties\n")

    # Example 2: Simple usage
    print("\n" + "="*60)
    print("Example 2: New York, NY - Budget $700,000")
    print("="*60)

    ny_properties = fetch_properties("New York, NY", 700000)
    print(f"Found {len(ny_properties)} properties in New York under $700k\n")


if __name__ == "__main__":
    main()
