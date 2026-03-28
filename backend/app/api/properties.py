"""
Properties API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import math

from app.models.property import Property, PropertyListResponse

router = APIRouter()


def get_database():
    """Get database instance from main app"""
    from app.main import database
    return database


@router.get("/", response_model=PropertyListResponse)
async def get_properties(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    # Filters
    min_price: Optional[int] = Query(None, description="Minimum price"),
    max_price: Optional[int] = Query(None, description="Maximum price"),
    min_beds: Optional[int] = Query(None, description="Minimum bedrooms"),
    max_beds: Optional[int] = Query(None, description="Maximum bedrooms"),
    min_baths: Optional[float] = Query(None, description="Minimum bathrooms"),
    max_baths: Optional[float] = Query(None, description="Maximum bathrooms"),
    min_sqft: Optional[int] = Query(None, description="Minimum square feet"),
    max_sqft: Optional[int] = Query(None, description="Maximum square feet"),
    min_cap_rate: Optional[float] = Query(None, description="Minimum cap rate %"),
    max_cap_rate: Optional[float] = Query(None, description="Maximum cap rate %"),
    min_investment_score: Optional[float] = Query(None, description="Minimum investment score"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state"),
    property_type: Optional[str] = Query(None, description="Filter by property type"),
    sort_by: Optional[str] = Query("investment_score", description="Sort field"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc/desc)")
):
    """
    Get list of properties with filtering and pagination

    Similar to: https://investor-marketplace.lennar.com/portal/properties
    """
    db = get_database()
    collection = db['properties']

    # Build filter query
    query = {}

    # Price filters
    if min_price or max_price:
        query['list_price'] = {}
        if min_price:
            query['list_price']['$gte'] = min_price
        if max_price:
            query['list_price']['$lte'] = max_price

    # Beds filters
    if min_beds or max_beds:
        query['beds'] = {}
        if min_beds:
            query['beds']['$gte'] = min_beds
        if max_beds:
            query['beds']['$lte'] = max_beds

    # Baths filters
    if min_baths or max_baths:
        query['baths'] = {}
        if min_baths:
            query['baths']['$gte'] = min_baths
        if max_baths:
            query['baths']['$lte'] = max_baths

    # Sqft filters
    if min_sqft or max_sqft:
        query['sqft'] = {}
        if min_sqft:
            query['sqft']['$gte'] = min_sqft
        if max_sqft:
            query['sqft']['$lte'] = max_sqft

    # Cap Rate filters
    if min_cap_rate or max_cap_rate:
        query['investment_metrics.cap_rate'] = {}
        if min_cap_rate:
            query['investment_metrics.cap_rate']['$gte'] = min_cap_rate
        if max_cap_rate:
            query['investment_metrics.cap_rate']['$lte'] = max_cap_rate

    # Investment Score filter
    if min_investment_score:
        query['investment_metrics.investment_score'] = {'$gte': min_investment_score}

    # City/State filters
    if city:
        query['city'] = city
    if state:
        query['state'] = state

    # Property type filter
    if property_type:
        query['property_type'] = property_type

    # Get total count
    total = await collection.count_documents(query)

    # Calculate pagination
    skip = (page - 1) * page_size
    total_pages = math.ceil(total / page_size)

    # Sort
    sort_direction = -1 if sort_order == "desc" else 1
    sort_field = f"investment_metrics.{sort_by}" if sort_by in ['cap_rate', 'investment_score', 'monthly_cash_flow'] else sort_by

    # Fetch properties
    cursor = collection.find(query).sort(sort_field, sort_direction).skip(skip).limit(page_size)
    properties = await cursor.to_list(length=page_size)

    # Convert MongoDB _id to string
    for prop in properties:
        prop['_id'] = str(prop['_id'])

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "properties": properties
    }


@router.get("/{property_id}", response_model=Property)
async def get_property_by_id(property_id: str):
    """
    Get single property by ID

    Similar to: https://investor-marketplace.lennar.com/portal/properties/{id}/home-info
    """
    db = get_database()
    collection = db['properties']

    property_data = await collection.find_one({"property_id": property_id})

    if not property_data:
        raise HTTPException(status_code=404, detail="Property not found")

    # Convert MongoDB _id to string
    property_data['_id'] = str(property_data['_id'])

    return property_data


@router.get("/stats/summary")
async def get_property_stats():
    """
    Get summary statistics for all properties
    """
    db = get_database()
    collection = db['properties']

    pipeline = [
        {
            "$facet": {
                "total": [{"$count": "count"}],
                "price_stats": [
                    {
                        "$group": {
                            "_id": None,
                            "avg_price": {"$avg": "$list_price"},
                            "min_price": {"$min": "$list_price"},
                            "max_price": {"$max": "$list_price"}
                        }
                    }
                ],
                "investment_stats": [
                    {
                        "$match": {"investment_metrics.cap_rate": {"$ne": None}}
                    },
                    {
                        "$group": {
                            "_id": None,
                            "avg_cap_rate": {"$avg": "$investment_metrics.cap_rate"},
                            "avg_cash_flow": {"$avg": "$investment_metrics.monthly_cash_flow"},
                            "avg_investment_score": {"$avg": "$investment_metrics.investment_score"}
                        }
                    }
                ],
                "by_city": [
                    {
                        "$group": {
                            "_id": "$city",
                            "count": {"$sum": 1}
                        }
                    },
                    {"$sort": {"count": -1}},
                    {"$limit": 10}
                ]
            }
        }
    ]

    result = await collection.aggregate(pipeline).to_list(length=1)

    if result:
        stats = result[0]
        return {
            "total_properties": stats['total'][0]['count'] if stats['total'] else 0,
            "price_stats": stats['price_stats'][0] if stats['price_stats'] else {},
            "investment_stats": stats['investment_stats'][0] if stats['investment_stats'] else {},
            "top_cities": stats['by_city']
        }

    return {}


@router.get("/search/autocomplete")
async def search_autocomplete(q: str = Query(..., min_length=2, description="Search query")):
    """
    Autocomplete search for cities and addresses
    """
    db = get_database()
    collection = db['properties']

    # Search in city and address fields
    query = {
        "$or": [
            {"city": {"$regex": f"^{q}", "$options": "i"}},
            {"full_address": {"$regex": q, "$options": "i"}}
        ]
    }

    # Get unique cities
    cities = await collection.distinct("city", query)

    # Get matching addresses (limit to 5)
    cursor = collection.find(query, {"full_address": 1, "_id": 0}).limit(5)
    addresses = await cursor.to_list(length=5)

    return {
        "cities": cities[:5],
        "addresses": [addr['full_address'] for addr in addresses if addr.get('full_address')]
    }
