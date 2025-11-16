from typing import List, Optional, Dict
import pandas as pd
from homeharvest import scrape_property
from multiprocessing import Pool, cpu_count





def extract_tax_summary(tax_history: list) -> Dict[str, Optional[float]]:
    """
    Extract tax summary metrics from tax_history array

    Args:
        tax_history: List of tax records with assessment and tax data

    Returns:
        Dictionary with:
        - current_assessment: Latest assessed value
        - tax_trend_pct: Year-over-year tax change %
        - assessment_trend_5yr: 5-year assessment growth rate
        - effective_tax_rate: Tax as % of assessed value
    """
    result = {
        'current_assessment': None,
        'tax_trend_pct': None,
        'assessment_trend_5yr': None,
        'effective_tax_rate': None
    }

    if not tax_history or len(tax_history) == 0:
        return result

    try:
        # Filter out None values and sort by year descending (most recent first)
        valid_history = [record for record in tax_history if record is not None and isinstance(record, dict)]
        if not valid_history:
            return result

        sorted_history = sorted(valid_history, key=lambda x: x.get('year', 0), reverse=True)

        # Current assessment (most recent year)
        current_record = sorted_history[0]
        if current_record.get('assessment') and current_record['assessment'].get('total'):
            result['current_assessment'] = float(current_record['assessment']['total'])

            # Effective tax rate
            if current_record.get('tax') and result['current_assessment'] > 0:
                result['effective_tax_rate'] = round(
                    (float(current_record['tax']) / result['current_assessment']) * 100, 2
                )

        # Year-over-year tax change
        if len(sorted_history) >= 2:
            current_tax = current_record.get('tax')
            previous_record = sorted_history[1]
            if isinstance(previous_record, dict):
                previous_tax = previous_record.get('tax')
                if current_tax and previous_tax and previous_tax > 0:
                    result['tax_trend_pct'] = round(
                        ((float(current_tax) - float(previous_tax)) / float(previous_tax)) * 100, 2
                    )

        # 5-year assessment growth rate
        if len(sorted_history) >= 6:
            current_assessment_dict = current_record.get('assessment')
            if isinstance(current_assessment_dict, dict):
                current_assessment = current_assessment_dict.get('total')
            else:
                current_assessment = None

            five_years_record = sorted_history[5]
            if isinstance(five_years_record, dict):
                five_years_assessment_dict = five_years_record.get('assessment')
                if isinstance(five_years_assessment_dict, dict):
                    five_years_ago = five_years_assessment_dict.get('total')
                else:
                    five_years_ago = None
            else:
                five_years_ago = None

            if current_assessment and five_years_ago and five_years_ago > 0:
                result['assessment_trend_5yr'] = round(
                    ((float(current_assessment) - float(five_years_ago)) / float(five_years_ago)) * 100, 2
                )

    except Exception as e:
        print(f"Error extracting tax summary: {e}")

    return result


def _process_single_property(prop: Dict, budget: float) -> Optional[Dict]:
    """
    Process a single property dict and return filtered essential fields

    Args:
        prop: Property dictionary from HomeHarvest (with pandas NA already replaced)
        budget: Maximum budget to filter against

    Returns:
        Property data dict with essential fields, or None if should be skipped
    """
    try:
        # Extract basic property info
        zipcode_val = prop.get('zip_code')
        zipcode = str(zipcode_val).split('-')[0] if zipcode_val else ''

        bedrooms = int(prop.get('beds')) if prop.get('beds') is not None else 2
        sale_price = float(prop.get('list_price')) if prop.get('list_price') is not None else 0

        # Skip if missing critical data
        if not sale_price or sale_price > budget:
            return None

        # Get address
        address = str(prop.get('formatted_address')) if prop.get('formatted_address') else 'Address not available'

        # Get bathrooms
        full_baths = float(prop.get('full_baths')) if prop.get('full_baths') is not None else 0
        half_baths = float(prop.get('half_baths')) if prop.get('half_baths') is not None else 0
        bathrooms = full_baths + (half_baths * 0.5)

        # Get square footage
        sqft = int(prop.get('sqft')) if prop.get('sqft') is not None else 0

        # Get property tax
        tax_val = prop.get('tax')
        if tax_val is not None and tax_val > 0:
            property_tax = float(tax_val)
        else:
            property_tax = round(sale_price * 0.015, 0)

        # Get HOA fee
        hoa_val = prop.get('hoa_fee')
        hoa_fee = float(hoa_val) if (hoa_val is not None and hoa_val > 0) else None

        # Estimate rent
        estimated_value_val = prop.get('estimated_value')
        if estimated_value_val is not None and estimated_value_val > 0:
            estimated_rent = round(float(estimated_value_val) * 0.008, 0)
        elif sale_price > 0:
            estimated_rent = round(sale_price * 0.008, 0)
        else:
            estimated_rent = None

        # Get additional property details
        property_type = str(prop.get('style')) if prop.get('style') else None
        year_built = int(prop.get('year_built')) if prop.get('year_built') is not None else None
        days_on_market = int(prop.get('days_on_mls')) if prop.get('days_on_mls') is not None else None
        property_url = str(prop.get('property_url')) if prop.get('property_url') else None
        primary_photo = str(prop.get('primary_photo')) if prop.get('primary_photo') else None
        last_sold_price = float(prop.get('last_sold_price')) if prop.get('last_sold_price') is not None else None

        # Extract tax summary
        tax_history_val = prop.get('tax_history')
        if isinstance(tax_history_val, list) and len(tax_history_val) > 0:
            tax_summary = extract_tax_summary(tax_history_val)
        else:
            tax_summary = {
                'current_assessment': None,
                'tax_trend_pct': None,
                'assessment_trend_5yr': None,
                'effective_tax_rate': None
            }

        # Build result dict
        return {
            "address": address,
            "zipcode": zipcode,
            "sale_price": int(sale_price),
            "beds": bedrooms,
            "baths": bathrooms,
            "sqft": sqft,
            "estimated_rent": int(estimated_rent) if estimated_rent else None,
            "property_tax": int(property_tax) if property_tax else None,
            "hoa": int(hoa_fee) if hoa_fee else None,
            "property_type": property_type,
            "year_built": year_built,
            "days_on_market": days_on_market,
            "property_url": property_url,
            "primary_photo": primary_photo,
            "last_sold_price": int(last_sold_price) if last_sold_price else None,
            "current_assessment": int(tax_summary['current_assessment']) if tax_summary['current_assessment'] else None,
            "tax_trend_pct": tax_summary['tax_trend_pct'],
            "assessment_trend_5yr": tax_summary['assessment_trend_5yr'],
            "effective_tax_rate": tax_summary['effective_tax_rate']
        }

    except Exception as e:
        print(f"Error processing property: {e}")
        return None


def _process_property_wrapper(args):
    """Wrapper for multiprocessing - unpacks arguments"""
    prop, budget = args
    return _process_single_property(prop, budget)








def create_fetch_properties_function(session_id: Optional[str] = None, user_id: Optional[str] = None):
    from clients.mongo_client import PropertyMongoClient
    # Initialize MongoDB client (currently commented out due to BSON size limits)
    mongo_client = PropertyMongoClient(user_id, session_id)  # noqa: F841

    def fetch_properties(locality: str, budget: float) -> List[Dict]:
        """
        Fetch for-sale properties by locality within budget

        Args:
            locality: City/area (e.g., "Philadelphia, PA", "New York", "Pennsylvania")
            budget: Maximum purchase price (e.g., 500000)

        Returns:
            List of dictionaries with property data (filtered essential fields):
            [
                {
                    "address": "123 Main St, Philadelphia, PA 19102",
                    "zipcode": "19102",
                    "sale_price": 450000,
                    "beds": 3,
                    "baths": 2.5,
                    "sqft": 1800,
                    "estimated_rent": 2340,
                    "property_tax": 6750,
                    "hoa": 150  # or None if not available
                },
                ...
            ]

        Note: MongoDB storage is currently disabled due to BSON document size limits (16MB).
        """
        print(f"Fetching properties in {locality} under ${budget:,}...")

        try:
            # Fetch properties using HomeHarvest
            properties_df = scrape_property(
                location=locality,
                listing_type="for_sale",
                price_max=int(budget)
            )

            if properties_df is None or len(properties_df) == 0:
                print(f"No properties found in {locality} under ${budget:,}")
                return []

            print(f"Found {len(properties_df)} properties. Processing...")

            # COMMENTED OUT: Store ALL raw data to MongoDB if client is available
            # NOTE: MongoDB has 16MB BSON document size limit - storing 100+ fields for 1000s of properties
            # exceeds this limit. Need to implement batching or store properties individually.
            # if mongo_client:
            #     try:
            #         # Convert ALL raw data to list of dicts
            #         # Replace pandas NA with None for JSON serialization
            #         raw_properties = properties_df.replace({pd.NA: None}).to_dict('records')
            #         mongo_client.store_properties(locality, budget, raw_properties)
            #         print(f"Stored {len(raw_properties)} properties (full raw data) to MongoDB")
            #     except Exception as e:
            #         print(f"Warning: Failed to store to MongoDB: {e}")
            #     finally:
            #         pass
            #         # Close MongoDB connection

            # OPTIMIZED: Convert to list of dicts - This is ~10x faster than iterrows()
            properties_list = properties_df.replace({pd.NA: None}).to_dict('records')

            # OPTIMIZED: Parallel processing with multiprocessing
            # Determine number of workers (use all CPUs but cap at reasonable limit)
            num_workers = min(cpu_count(), 8)  # Cap at 8 to avoid overhead

            print(f"Processing with {num_workers} parallel workers...")

            # Prepare arguments for parallel processing
            args_list = [(prop, budget) for prop in properties_list]

            # Use multiprocessing Pool for parallel processing
            with Pool(num_workers) as pool:
                results_with_none = pool.map(_process_property_wrapper, args_list)

            # Filter out None values (properties that were skipped)
            results = [r for r in results_with_none if r is not None]

            print(f"Successfully processed {len(results)} properties")
            return results

        except Exception as e:
            print(f"Error fetching properties: {e}")
            return []
        
    return fetch_properties

