"""
Zillow Property Scraper using Botasaurus Framework

High-volume scraper with advanced anti-bot protection, rate limiting, and caching.
Capable of scraping 10k+ properties/day with resume capability.

Usage:
    from zillow_scraper import fetch_zillow_properties

    properties = fetch_zillow_properties("Dallas, TX", 500000)
"""

from botasaurus.browser import browser, Driver
from typing import List, Dict, Optional
import json
import time
import os
from datetime import datetime
import re


# ============================================================================
# CONFIGURATION
# ============================================================================

ZILLOW_CONFIG = {
    # Anti-bot settings
    "headless": True,  # Headless mode (no browser window)
    "user_agent": "random",
    "block_images": False,  # Keep images for better detection bypass
    "wait_for_complete_page_load": True,

    # Performance
    "parallel": 1,  # Single browser for debugging
    "max_retry": 3,
    "retry_wait": 10,  # 10 seconds between retries

    # Caching (disabled for debugging)
    "cache": False,
    "cache_duration": 86400,

    # Browser reuse
    "reuse_driver": False,
    "keep_driver_alive": False,
}

# Rate limiting for high-volume scraping
# 12 req/min = 720/hour = 17,280/day (with 40 props/page = 691k props/day theoretical)
RATE_LIMITS = {
    "requests_per_minute": 12,
    "requests_per_hour": 600,
    "delay_between_requests": 5,  # 5 seconds
    "backoff_multiplier": 2,
}


# ============================================================================
# RATE LIMITER
# ============================================================================

class RateLimiter:
    """Token bucket rate limiter for high-volume scraping"""

    def __init__(self, limits: Dict = None):
        if limits is None:
            limits = RATE_LIMITS
        self.requests_per_minute = limits["requests_per_minute"]
        self.delay_between_requests = limits["delay_between_requests"]
        self.last_request_time = 0
        self.request_times = []

    def wait_if_needed(self):
        """Enforce rate limits before making request"""
        current_time = time.time()

        # Remove requests older than 1 minute
        self.request_times = [
            t for t in self.request_times
            if current_time - t < 60
        ]

        # Check if we've hit the per-minute limit
        if len(self.request_times) >= self.requests_per_minute:
            wait_time = 60 - (current_time - self.request_times[0])
            if wait_time > 0:
                print(f"[Rate Limit] Waiting {wait_time:.1f}s...")
                time.sleep(wait_time)

        # Enforce minimum delay between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.delay_between_requests:
            wait_time = self.delay_between_requests - time_since_last
            time.sleep(wait_time)

        # Record this request
        self.last_request_time = time.time()
        self.request_times.append(self.last_request_time)


# ============================================================================
# SESSION MANAGER (Resume Capability)
# ============================================================================

class SessionManager:
    """Manages scraping sessions with resume capability"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.cache_dir = f"data/zillow_sessions/{session_id}"
        os.makedirs(self.cache_dir, exist_ok=True)

    def save_progress(self, location: str, properties: List[Dict]):
        """Save incremental progress to disk"""
        safe_name = location.replace(", ", "_").replace(" ", "_")
        filepath = f"{self.cache_dir}/{safe_name}.json"

        with open(filepath, 'w') as f:
            json.dump({
                "location": location,
                "timestamp": datetime.now().isoformat(),
                "count": len(properties),
                "properties": properties
            }, f, indent=2)

        print(f"[Session] Saved {len(properties)} properties to {filepath}")

    def get_cached_market(self, location: str) -> Optional[List[Dict]]:
        """Check if we already scraped this market (within 24 hours)"""
        safe_name = location.replace(", ", "_").replace(" ", "_")
        filepath = f"{self.cache_dir}/{safe_name}.json"

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                # Check if cache is fresh (< 24 hours)
                cached_time = datetime.fromisoformat(data["timestamp"])
                age_seconds = (datetime.now() - cached_time).total_seconds()
                if age_seconds < 86400:  # 24 hours
                    print(f"[Cache Hit] Using cached data for {location} ({len(data['properties'])} properties)")
                    return data["properties"]
        except FileNotFoundError:
            pass

        return None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_price(price_text: str) -> int:
    """Parse price string to integer"""
    if not price_text:
        return 0
    # Remove $ and commas, extract numbers
    numbers = re.sub(r'[^\d]', '', price_text)
    return int(numbers) if numbers else 0


def parse_number(text: str) -> float:
    """Parse number from text (handles '3 bd', '2.5 ba', '1,800 sqft')"""
    if not text:
        return 0
    # Extract first number (int or float)
    match = re.search(r'(\d+\.?\d*)', text.replace(',', ''))
    return float(match.group(1)) if match else 0


def build_zillow_search_url(location: str, max_price: int, page: int = 1) -> str:
    """Build Zillow search URL for given location and price"""
    # Zillow URL format: /city-state/price_rb/page_p/
    # Example: /dallas-tx/0-500000_price/1_p/

    # Clean location: "Dallas, TX" -> "dallas-tx"
    location_slug = location.lower().replace(", ", "-").replace(" ", "-")

    # Build URL
    url = f"https://www.zillow.com/{location_slug}/"

    # Add price filter
    if max_price > 0:
        url += f"0-{max_price}_price/"

    # Add pagination
    if page > 1:
        url += f"{page}_p/"

    return url


# ============================================================================
# DATA EXTRACTION FUNCTIONS
# ============================================================================

def extract_next_data(driver: Driver) -> Optional[Dict]:
    """
    Extract __NEXT_DATA__ JSON from Zillow page

    Zillow embeds all property data in a <script id="__NEXT_DATA__"> tag.
    This is the most reliable way to get structured data.
    """
    try:
        print("[Debug] Attempting to extract __NEXT_DATA__...")

        # Use JavaScript to extract the data (most reliable method for Botasaurus)
        next_data = driver.run_js("""
            var elem = document.getElementById('__NEXT_DATA__');
            if (elem && elem.textContent) {
                return elem.textContent;
            }
            return null;
        """)

        if next_data:
            print(f"[Debug] ✓ Got data via JavaScript ({len(next_data)} chars)")
            data = json.loads(next_data)
            print(f"[Debug] ✓ Successfully parsed JSON")
            return data
        else:
            print("[Debug] ✗ JavaScript method returned null")
            return None

    except json.JSONDecodeError as e:
        print(f"[Zillow] JSON decode error: {e}")
        return None
    except Exception as e:
        print(f"[Zillow] Error extracting __NEXT_DATA__: {e}")
        return None


def parse_zillow_next_data(next_data: Dict) -> List[Dict]:
    """
    Parse Zillow's __NEXT_DATA__ structure to extract property listings

    Structure: props.pageProps.searchPageState.cat1.searchResults.listResults
    """
    try:
        print("[Debug] Parsing __NEXT_DATA__ structure...")

        # Navigate nested structure with debug logging
        props = next_data.get("props", {})
        print(f"[Debug] - props keys: {list(props.keys())[:5] if props else 'None'}")

        page_props = props.get("pageProps", {})
        print(f"[Debug] - pageProps keys: {list(page_props.keys())[:5] if page_props else 'None'}")

        search_page_state = page_props.get("searchPageState", {})
        print(f"[Debug] - searchPageState keys: {list(search_page_state.keys())[:5] if search_page_state else 'None'}")

        cat1 = search_page_state.get("cat1", {})
        print(f"[Debug] - cat1 keys: {list(cat1.keys())[:5] if cat1 else 'None'}")

        search_results_obj = cat1.get("searchResults", {})
        print(f"[Debug] - searchResults keys: {list(search_results_obj.keys())[:5] if search_results_obj else 'None'}")

        search_results = search_results_obj.get("listResults", [])
        print(f"[Debug] - listResults count: {len(search_results) if search_results else 0}")

        if not search_results:
            print("[Zillow] No listResults found in __NEXT_DATA__")
            print(f"[Debug] Full structure preview: {str(next_data)[:500]}...")
            return []

        properties = []
        for listing in search_results:
            # Skip non-property results
            if not isinstance(listing, dict):
                continue

            # Extract key fields
            prop = {
                "zillow_id": listing.get("zpid"),
                "url": f"https://www.zillow.com{listing.get('detailUrl', '')}" if listing.get('detailUrl') else None,
                "address": listing.get("address"),
                "city": listing.get("addressCity"),
                "state": listing.get("addressState"),
                "zipcode": listing.get("addressZipcode"),
                "price": listing.get("price"),
                "beds": listing.get("beds"),
                "baths": listing.get("baths"),
                "area": listing.get("area"),  # sqft
                "latitude": listing.get("latLong", {}).get("latitude") if isinstance(listing.get("latLong"), dict) else None,
                "longitude": listing.get("latLong", {}).get("longitude") if isinstance(listing.get("latLong"), dict) else None,
                "property_type": listing.get("hdpData", {}).get("homeInfo", {}).get("homeType") if isinstance(listing.get("hdpData"), dict) else None,
                "zestimate": listing.get("zestimate"),
                "rent_zestimate": listing.get("rentZestimate"),
                "days_on_zillow": listing.get("daysOnZillow", 0),
                "listing_status": listing.get("statusType"),
                "year_built": listing.get("hdpData", {}).get("homeInfo", {}).get("yearBuilt") if isinstance(listing.get("hdpData"), dict) else None,
                "lot_size": listing.get("lotAreaValue"),
            }

            # Extract all photos (multiple approaches to handle different Zillow formats)
            photos = []

            # Method 1: carouselPhotos (most comprehensive)
            carousel_photos = listing.get("carouselPhotos", [])
            if carousel_photos and isinstance(carousel_photos, list):
                for photo in carousel_photos:
                    if isinstance(photo, dict):
                        photo_url = photo.get("url") or photo.get("mixedSources", {}).get("jpeg", [{}])[0].get("url")
                        if photo_url:
                            photos.append(photo_url)
                    elif isinstance(photo, str):
                        photos.append(photo)

            # Method 2: imgSrc (fallback - usually just the primary photo)
            if not photos:
                img_src = listing.get("imgSrc")
                if img_src:
                    photos.append(img_src)

            # Method 3: hdpData photos
            if not photos:
                hdp_photos = listing.get("hdpData", {}).get("homeInfo", {}).get("photos", [])
                if isinstance(hdp_photos, list):
                    for photo in hdp_photos:
                        if isinstance(photo, dict):
                            photo_url = photo.get("url")
                            if photo_url:
                                photos.append(photo_url)

            prop["photos"] = photos
            prop["primary_photo"] = photos[0] if photos else None

            properties.append(prop)

        return properties

    except Exception as e:
        print(f"[Zillow] Error parsing __NEXT_DATA__: {e}")
        return []


def parse_zillow_dom(driver: Driver) -> List[Dict]:
    """
    Fallback DOM parser if __NEXT_DATA__ extraction fails
    Scrapes visible property cards using JavaScript
    """
    properties = []

    try:
        # Use JavaScript to extract property data from DOM
        properties_data = driver.run_js("""
            const cards = document.querySelectorAll('article[data-test="property-card"]');
            const properties = [];

            cards.forEach(card => {
                const prop = {};

                // Price
                const priceElem = card.querySelector('[data-test="property-card-price"]');
                if (priceElem) {
                    prop.price_text = priceElem.textContent.trim();
                }

                // Address
                const addressElem = card.querySelector('address');
                if (addressElem) {
                    prop.address = addressElem.textContent.trim();
                }

                // Beds/Baths/Sqft
                const details = card.querySelectorAll('li');
                prop.details = [];
                for (let i = 0; i < Math.min(3, details.length); i++) {
                    prop.details.push(details[i].textContent.trim());
                }

                // URL
                const linkElem = card.querySelector('a');
                if (linkElem && linkElem.href) {
                    prop.url = linkElem.href;
                }

                properties.push(prop);
            });

            return properties;
        """)

        if not properties_data:
            print(f"[Zillow DOM] No properties found via JavaScript")
            return []

        print(f"[Zillow DOM] Found {len(properties_data)} property cards via JavaScript")

        # Parse the extracted data
        for prop_data in properties_data:
            prop = {}

            # Parse price
            if 'price_text' in prop_data:
                prop["price"] = parse_price(prop_data['price_text'])

            # Address
            if 'address' in prop_data:
                prop["address"] = prop_data['address']

            # Parse details (beds/baths/sqft)
            if 'details' in prop_data:
                for detail in prop_data['details']:
                    if "bd" in detail.lower():
                        prop["beds"] = int(parse_number(detail))
                    elif "ba" in detail.lower():
                        prop["baths"] = parse_number(detail)
                    elif "sqft" in detail.lower():
                        prop["area"] = int(parse_number(detail))

            # URL
            if 'url' in prop_data:
                prop["url"] = prop_data['url']

            if prop:  # Only add if we got some data
                properties.append(prop)

        return properties

    except Exception as e:
        print(f"[Zillow] Error parsing DOM: {e}")
        return []


# ============================================================================
# CORE SCRAPING FUNCTION (with Botasaurus)
# ============================================================================

@browser(
    parallel=ZILLOW_CONFIG["parallel"],
    headless=ZILLOW_CONFIG["headless"],
    cache=ZILLOW_CONFIG["cache"],
    max_retry=ZILLOW_CONFIG["max_retry"],
    block_images=ZILLOW_CONFIG["block_images"]
)
def scrape_zillow_search(driver: Driver, search_params: Dict) -> List[Dict]:
    """
    Scrape Zillow search results using Botasaurus browser automation

    Args:
        driver: Botasaurus Driver instance
        search_params: {"location": "Dallas, TX", "max_price": 500000, "page": 1}

    Returns:
        List of property dictionaries
    """
    location = search_params["location"]
    max_price = search_params.get("max_price", 1000000)
    page = search_params.get("page", 1)

    # Build Zillow search URL
    url = build_zillow_search_url(location, max_price, page)

    print(f"[Zillow] Scraping: {location} (page {page}) - {url}")

    try:
        # Navigate with Botasaurus (automatically handles bot detection)
        driver.get(url)

        # Wait for results to load (Zillow uses React)
        time.sleep(3)  # Give page time to load

        # Debug: Check page title
        page_title = driver.title
        print(f"[Debug] Page title: {page_title}")

        # Check if results loaded
        if not driver.is_element_present("#grid-search-results"):
            print(f"[Zillow] Results grid not found, checking for properties anyway...")
        else:
            print(f"[Zillow] ✓ Results grid found")

        # Small delay for complete page load
        time.sleep(2)

        # Debug: Save page HTML for inspection
        page_html = driver.page_html
        print(f"[Debug] Page HTML length: {len(page_html)} characters")

        # Check if we have __NEXT_DATA__
        if "__NEXT_DATA__" in page_html:
            print(f"[Debug] ✓ __NEXT_DATA__ found in page HTML")
        else:
            print(f"[Debug] ✗ __NEXT_DATA__ NOT found in page HTML")

        # Extract __NEXT_DATA__ JSON (hidden data Zillow uses for rendering)
        next_data_json = extract_next_data(driver)

        if next_data_json:
            properties = parse_zillow_next_data(next_data_json)
            if properties:
                print(f"[Zillow] ✓ Found {len(properties)} properties via __NEXT_DATA__")
                return properties

        # Fallback: Parse DOM if __NEXT_DATA__ fails
        print("[Zillow] __NEXT_DATA__ not found, trying DOM parsing...")
        properties = parse_zillow_dom(driver)
        if properties:
            print(f"[Zillow] ✓ Found {len(properties)} properties via DOM parsing")
            return properties

        print(f"[Zillow] ✗ No properties found on page {page}")
        return []

    except Exception as e:
        print(f"[Zillow] ✗ Error scraping page {page}: {e}")
        return []


# ============================================================================
# DATA TRANSFORMATION
# ============================================================================

def transform_zillow_to_propfusion(zillow_prop: Dict) -> Dict:
    """
    Transform Zillow property schema to PropFusion schema
    Matches the format in agno_tools.py _process_single_property()
    """
    # Extract address components
    address = zillow_prop.get("address", "")
    city = zillow_prop.get("city", "")
    state = zillow_prop.get("state", "")
    zipcode = zillow_prop.get("zipcode", "")

    # Build full address
    if all([address, city, state, zipcode]):
        full_address = f"{address}, {city}, {state} {zipcode}"
    elif address:
        full_address = address
    else:
        full_address = "Address not available"

    # Price - handle both string "$265,000" and number formats
    price_raw = zillow_prop.get("price", 0)
    if isinstance(price_raw, str):
        sale_price = parse_price(price_raw)
    elif isinstance(price_raw, (int, float)):
        sale_price = int(price_raw)
    else:
        sale_price = 0

    # Basic specs
    beds = int(zillow_prop.get("beds", 2)) if zillow_prop.get("beds") else 2
    baths = float(zillow_prop.get("baths", 2.0)) if zillow_prop.get("baths") else 2.0
    sqft = int(zillow_prop.get("area", 0)) if zillow_prop.get("area") else 0

    # Estimate property tax (1.5% if not available)
    property_tax = round(sale_price * 0.015, 0) if sale_price > 0 else 0

    # Use Zillow's rent estimate if available
    estimated_rent = zillow_prop.get("rent_zestimate")
    if not estimated_rent or estimated_rent == 0:
        estimated_rent = round(sale_price * 0.008, 0) if sale_price > 0 else None

    # Build PropFusion-compatible dict
    return {
        "address": full_address,
        "zipcode": str(zipcode).split('-')[0] if zipcode else "",
        "sale_price": sale_price,
        "beds": beds,
        "baths": baths,
        "sqft": sqft,
        "estimated_rent": int(estimated_rent) if estimated_rent else None,
        "property_tax": int(property_tax) if property_tax else None,
        "hoa": None,  # Zillow doesn't always provide HOA
        "property_type": zillow_prop.get("property_type"),
        "year_built": zillow_prop.get("year_built"),
        "days_on_market": zillow_prop.get("days_on_zillow", 0),
        "property_url": zillow_prop.get("url"),
        "primary_photo": zillow_prop.get("primary_photo"),
        "photos": zillow_prop.get("photos", []),  # All property photos
        "last_sold_price": None,
        "latitude": zillow_prop.get("latitude"),
        "longitude": zillow_prop.get("longitude"),
        "zestimate": zillow_prop.get("zestimate"),
        "source": "zillow",
        "zillow_id": str(zillow_prop.get("zillow_id")) if zillow_prop.get("zillow_id") else None,
        # Tax summary fields (not available from Zillow scrape)
        "current_assessment": None,
        "tax_trend_pct": None,
        "assessment_trend_5yr": None,
        "effective_tax_rate": None,
    }


# ============================================================================
# HIGH-VOLUME BATCH SCRAPER
# ============================================================================

class ZillowBatchScraper:
    """
    High-volume scraper with rate limiting, caching, and resume capability
    """

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or f"zillow_{int(time.time())}"
        self.rate_limiter = RateLimiter(RATE_LIMITS)
        self.session_manager = SessionManager(self.session_id)

    def scrape_market(
        self,
        location: str,
        max_price: int = 1000000,
        max_pages: int = 20
    ) -> List[Dict]:
        """
        Scrape all pages for a single market

        Args:
            location: "Dallas, TX"
            max_price: Maximum property price
            max_pages: Maximum pages to scrape (Zillow shows ~40 results/page)

        Returns:
            List of all properties from all pages
        """
        all_properties = []

        # Check if we already scraped this market (resume capability)
        cached = self.session_manager.get_cached_market(location)
        if cached:
            return cached

        # Build search params for all pages
        search_params_list = [
            {
                "location": location,
                "max_price": max_price,
                "page": page
            }
            for page in range(1, max_pages + 1)
        ]

        # Scrape with rate limiting
        for params in search_params_list:
            # Rate limit check
            self.rate_limiter.wait_if_needed()

            try:
                # Scrape single page (uses Botasaurus caching)
                properties = scrape_zillow_search(params)

                if not properties or len(properties) == 0:
                    print(f"[Zillow] No more results at page {params['page']}, stopping")
                    break

                all_properties.extend(properties)

                # Save progress incrementally
                self.session_manager.save_progress(location, all_properties)

                print(f"[Progress] {location}: {len(all_properties)} properties total")

            except Exception as e:
                print(f"[Error] Failed page {params['page']}: {e}")
                # Continue to next page instead of failing entirely
                continue

        return all_properties

    def scrape_all_markets(
        self,
        markets: List[Dict],
        max_price: int = 500000
    ) -> Dict[str, List[Dict]]:
        """
        Scrape all target markets for high-volume collection

        Target: 10k+ properties/day
        Strategy: 3 parallel browsers, 12 req/min = 17k+ properties/day

        Args:
            markets: [{"city": "Dallas", "state": "TX"}, ...]
            max_price: Maximum property price

        Returns:
            {
                "Dallas, TX": [properties...],
                "Houston, TX": [properties...],
                ...
            }
        """
        results = {}
        total_properties = 0

        print(f"[Zillow Batch] Starting scrape of {len(markets)} markets")
        print(f"[Config] Parallel browsers: {ZILLOW_CONFIG['parallel']}")
        print(f"[Config] Rate limit: {RATE_LIMITS['requests_per_minute']}/min")
        print("=" * 60)

        for i, market in enumerate(markets, 1):
            location = f"{market['city']}, {market['state']}"

            print(f"\n[{i}/{len(markets)}] Scraping {location}...")

            try:
                properties = self.scrape_market(location, max_price=max_price)

                if properties:
                    results[location] = properties
                    total_properties += len(properties)

                    print(f"[Success] {location}: {len(properties)} properties")
                else:
                    print(f"[Warning] {location}: No properties found")

            except Exception as e:
                print(f"[Error] {location} failed: {e}")
                continue

        print("\n" + "=" * 60)
        print(f"[Complete] Scraped {len(results)}/{len(markets)} markets")
        print(f"[Total] {total_properties} properties collected")
        print("=" * 60)

        return results


# ============================================================================
# PUBLIC API (Matches agno_tools.py signature)
# ============================================================================

def fetch_zillow_properties(
    locality: str,
    budget: float,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None
) -> List[Dict]:
    """
    Public API matching agno_tools.py fetch_properties() signature

    This allows drop-in replacement:
        from zillow_scraper import fetch_zillow_properties
        properties = fetch_zillow_properties("Dallas, TX", 500000)

    Args:
        locality: City/state (e.g., "Dallas, TX")
        budget: Maximum purchase price
        user_id: Optional user ID for MongoDB storage
        session_id: Optional session ID for MongoDB storage

    Returns:
        List of PropFusion-formatted property dicts
    """
    print(f"\n{'='*60}")
    print(f"[Zillow] Fetching properties in {locality} under ${budget:,}...")
    print(f"{'='*60}\n")

    # Initialize scraper
    scraper = ZillowBatchScraper(session_id=session_id)

    # Scrape single market
    zillow_properties = scraper.scrape_market(locality, max_price=int(budget), max_pages=20)

    if not zillow_properties:
        print(f"[Zillow] No properties found in {locality}")
        return []

    print(f"\n[Zillow] Found {len(zillow_properties)} raw properties. Transforming...")

    # Transform to PropFusion schema
    transformed = []
    for zprop in zillow_properties:
        try:
            prop = transform_zillow_to_propfusion(zprop)

            # Filter by budget
            if prop["sale_price"] > 0 and prop["sale_price"] <= budget:
                transformed.append(prop)
        except Exception as e:
            print(f"[Error] Failed to transform property: {e}")
            continue

    print(f"[Zillow] ✓ Returning {len(transformed)} properties within budget\n")

    # Optional: Store to MongoDB (matching agno_tools pattern)
    if user_id and session_id:
        try:
            from clients.mongo_client import PropertyMongoClient
            mongo_client = PropertyMongoClient(user_id, session_id)
            mongo_client.store_properties(locality, budget, transformed)
            print(f"[MongoDB] Stored {len(transformed)} properties")
        except Exception as e:
            print(f"[MongoDB] Warning: Failed to store: {e}")

    return transformed


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    # Test with Dallas, TX
    print("Testing Zillow Scraper...")
    properties = fetch_zillow_properties("Dallas, TX", 500000)

    if properties:
        print(f"\n✓ Success! Found {len(properties)} properties")
        print("\nSample property:")
        print(json.dumps(properties[0], indent=2))
    else:
        print("\n✗ No properties found")
