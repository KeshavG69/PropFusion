from main import fetch_properties

print("Testing property fetcher...")
props = fetch_properties('Philadelphia, PA', 100000)
print(f"Got {len(props)} properties")

if props:
    print("\nFirst property:")
    for key, value in props[0].items():
        print(f"  {key}: {value}")
