"""
PropFusion FastAPI Backend
Main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="PropFusion API",
    description="Real Estate Investment Platform API",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'propfusion')

# Global MongoDB client
mongodb_client: AsyncIOMotorClient = None
database = None

@app.on_event("startup")
async def startup_db_client():
    """Initialize MongoDB connection on startup"""
    global mongodb_client, database
    mongodb_client = AsyncIOMotorClient(MONGODB_URI)
    database = mongodb_client[MONGODB_DB_NAME]
    print(f"✅ Connected to MongoDB: {MONGODB_DB_NAME}")

@app.on_event("shutdown")
async def shutdown_db_client():
    """Close MongoDB connection on shutdown"""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        print("👋 MongoDB connection closed")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "PropFusion API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test MongoDB connection
        await database.command('ping')
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

# Import routers
from app.api import properties

app.include_router(properties.router, prefix="/api/properties", tags=["properties"])
