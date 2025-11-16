from homeharvest import scrape_property

print("Fetching one property to see available fields...")
props = scrape_property(
    location="Philadelphia, PA",
    listing_type="for_sale",
    price_max=100000
)

if props is not None and len(props) > 0:
    print("\nAvailable columns in HomeHarvest DataFrame:")
    print(props.columns.tolist())

    print("\nFirst property data:")
    first_prop = props.iloc[0]
    for col in props.columns:
        value = first_prop[col]
        print(f"{col}: {value}")
