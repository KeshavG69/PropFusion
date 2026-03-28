"""
Property data models
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class Location(BaseModel):
    """GeoJSON Point"""
    type: str = "Point"
    coordinates: List[Optional[float]]


class InvestmentMetrics(BaseModel):
    """Investment calculation metrics"""
    cap_rate: Optional[float] = None
    monthly_cash_flow: Optional[float] = None
    annual_noi: Optional[float] = None
    investment_score: Optional[float] = None
    rent_to_price_ratio: Optional[float] = None


class Property(BaseModel):
    """Property model"""
    property_id: str
    source: str
    source_id: str
    source_url: Optional[str] = None

    # Address
    street_address: Optional[str] = None
    city: str
    state: str
    zip_code: Optional[str] = None
    full_address: Optional[str] = None

    # Location
    location: Optional[Location] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Property Details
    property_type: Optional[str] = None
    beds: Optional[int] = None
    baths: Optional[float] = None
    sqft: Optional[int] = None
    lot_size: Optional[float] = None
    lot_size_units: Optional[str] = None

    # Pricing
    list_price: Optional[int] = None
    currency: Optional[str] = "USD"

    # Zillow-Specific
    zestimate: Optional[int] = None
    rent_estimate: Optional[int] = None
    days_on_zillow: Optional[int] = None

    # Listing Info
    status: Optional[str] = "FOR_SALE"
    image_url: Optional[str] = None

    # Investment Metrics
    investment_metrics: Optional[InvestmentMetrics] = None

    # Metadata
    scraped_at: Optional[str] = None
    last_updated: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "property_id": "zillow_123456",
                "city": "Philadelphia",
                "state": "PA",
                "list_price": 150000,
                "beds": 3,
                "baths": 2,
                "sqft": 1500,
                "investment_metrics": {
                    "cap_rate": 10.84,
                    "monthly_cash_flow": 500,
                    "investment_score": 85.5
                }
            }
        }


class PropertyListResponse(BaseModel):
    """Response for property list endpoint"""
    total: int
    page: int
    page_size: int
    total_pages: int
    properties: List[Property]


class PropertyFilters(BaseModel):
    """Filters for property search"""
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    min_beds: Optional[int] = None
    max_beds: Optional[int] = None
    min_baths: Optional[float] = None
    max_baths: Optional[float] = None
    min_sqft: Optional[int] = None
    max_sqft: Optional[int] = None
    min_cap_rate: Optional[float] = None
    max_cap_rate: Optional[float] = None
    min_investment_score: Optional[float] = None
    city: Optional[str] = None
    state: Optional[str] = None
    property_type: Optional[str] = None
