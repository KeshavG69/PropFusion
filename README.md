# Real Estate Property Fetcher

A simple Python tool to fetch for-sale properties by locality and budget, with estimated rental income and property costs for investment analysis.

## Features

-  Fetch active for-sale listings by city/area and budget
-  Get property details: price, beds, baths, square footage
-  Estimate rental income using Census Bureau median rent data
-  Estimate property taxes from Census data
-  Get HOA fees when available in listings
-  100% free to use (uses free government APIs)

## Data Sources

| Data Point | Source | Notes |
|------------|--------|-------|
| For-sale listings | HomeHarvest (scrapes Realtor.com) | Free, unlimited |
| Rental estimates | Census Bureau API | Free, unlimited |
| Fair Market Rent (backup) | HUD API | Free, unlimited |
| Property tax estimates | Census Bureau API | Free, unlimited |
| HOA fees | From listing data | Available ~40% of the time |

## Installation

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

1. **Clone or navigate to the project directory:**
   ```bash
   cd Zillow
   ```

2. **Install dependencies using uv:**
   ```bash
   uv pip install -e .
   ```

   Or if you prefer to sync:
   ```bash
   uv sync
   ```

3. **Get free API keys (optional but recommended):**

   **Census Bureau API Key** (for rent and property tax data):
   - Sign up: https://api.census.gov/data/key_signup.html
   - You'll receive your free API key instantly via email

   **HUD API Token** (backup for rent data):
   - Register: https://www.huduser.gov/hudapi/public/register
   - Confirm your email and generate a token

4. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```

5. **Add your API keys to `.env`:**
   ```env
   CENSUS_API_KEY=your_census_api_key_here
   HUD_API_TOKEN=your_hud_api_token_here
   ```

   **Note:** The tool will still work without API keys, but rent and property tax estimates will be less accurate.

## Usage

### Basic Usage

```python
from main import fetch_properties

# Fetch properties in Philadelphia under $500,000
properties = fetch_properties("Philadelphia, PA", 500000)

# Print results
for prop in properties:
    print(f"{prop['address']} - ${prop['sale_price']:,}")
```

### Complete Example

```python
from main import fetch_properties

# Search for properties
properties = fetch_properties(
    locality="New York, NY",
    budget=700000
)

# Display detailed information
for prop in properties:
    print(f"\n{prop['address']}")
    print(f"  Price: ${prop['sale_price']:,}")
    print(f"  Size: {prop['beds']}bd/{prop['baths']}ba, {prop['sqft']:,} sqft")

    if prop['estimated_rent']:
        print(f"  Est. Rent: ${prop['estimated_rent']}/mo")

    if prop['property_tax']:
        print(f"  Property Tax: ${prop['property_tax']}/yr")

    if prop['hoa']:
        print(f"  HOA: ${prop['hoa']}/mo")
    else:
        print(f"  HOA: Not available")
```

### Run Examples

The `main.py` file includes example usage. Run it directly:

```bash
python main.py
```

This will fetch properties in Philadelphia and New York and display the results.

## Return Data Format

The `fetch_properties()` function returns a list of dictionaries, each containing:

```python
{
    "address": str,           # Full property address
    "zipcode": str,          # ZIP code
    "sale_price": int,       # Current listing price
    "beds": int,             # Number of bedrooms
    "baths": float,          # Number of bathrooms
    "sqft": int,             # Square footage
    "estimated_rent": int,   # Estimated monthly rent (or None)
    "property_tax": int,     # Estimated annual property tax (or None)
    "hoa": int               # Monthly HOA fee (or None if not in listing)
}
```

## How It Works

1. **Fetches For-Sale Listings:**
   - Uses HomeHarvest library to scrape Realtor.com
   - Filters by locality and budget
   - Gets property details: price, beds, baths, sqft, HOA (if available)

2. **Estimates Rental Income:**
   - Fetches median rent for each ZIP code from Census Bureau API
   - Adjusts rent based on number of bedrooms:
     - 1BR: 70% of median
     - 2BR: 100% of median (baseline)
     - 3BR: 130% of median
     - 4BR: 160% of median
     - 5BR: 190% of median
   - Falls back to HUD Fair Market Rent if Census data unavailable

3. **Estimates Property Tax:**
   - Fetches median property tax for each ZIP code from Census Bureau
   - Falls back to 1.5% of sale price if data unavailable

4. **Gets HOA Fees:**
   - Extracts from listing data when available
   - Returns `None` if not included in listing (~60% of properties)

## Limitations

- **Rent estimates** are based on neighborhood medians, not property-specific valuations
- **Property tax estimates** use area medians, actual taxes may vary
- **HOA fees** only available when included in listings (~40% coverage)
- **Listing data** comes from web scraping, may occasionally fail if Realtor.com changes their site
- **Geographic coverage** limited to areas covered by Realtor.com (US properties)

## Tips for Best Results

1. **Use specific city names:** `"Philadelphia, PA"` works better than just `"Philadelphia"`
2. **Set realistic budgets:** Very high budgets may return too many results and slow down processing
3. **Get API keys:** While optional, Census and HUD API keys significantly improve data accuracy
4. **Check HOA availability:** Not all properties include HOA data - factor this into your analysis
5. **Verify estimates:** Use the returned estimates as starting points, not exact figures

## Example Localities

```python
# City, State
fetch_properties("Philadelphia, PA", 500000)
fetch_properties("New York, NY", 700000)
fetch_properties("San Francisco, CA", 1000000)

# State-wide (may return many results)
fetch_properties("Pennsylvania", 400000)

# Specific neighborhoods (if recognized by Realtor.com)
fetch_properties("Brooklyn, New York", 600000)
```

## Troubleshooting

### No properties found
- Try a different locality name format
- Increase your budget
- Check if the area has active listings on Realtor.com

### API errors
- Verify your API keys are correctly set in `.env`
- Check that your API keys are active (Census keys never expire, HUD tokens can be regenerated)
- Ensure you have internet connection

### Rent estimates are None
- Some ZIP codes may not have Census rent data
- The tool will try HUD Fair Market Rent as backup
- Without API keys, rent estimates won't be available

## Contributing

This is a simple tool for personal use. Feel free to modify and extend as needed!

## License

This project is for educational and personal use only. Web scraping should be done responsibly and in compliance with website terms of service.

## Disclaimer

- This tool provides **estimates only** and should not be used as the sole basis for investment decisions
- Always conduct proper due diligence before making any real estate investment
- Property data is scraped from public listings and may not be 100% accurate or current
- The authors are not responsible for any investment decisions made based on this tool's output

## Credits

- Property listings: [HomeHarvest](https://github.com/ZacharyHampton/HomeHarvest)
- Rent data: [US Census Bureau API](https://www.census.gov/data/developers/data-sets.html)
- Fair Market Rent: [HUD API](https://www.huduser.gov/portal/dataset/fmr-api.html)
