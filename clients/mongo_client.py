"""
MongoDB Client for Property Storage
Stores property search results organized by user_id and session_id
"""

import os
from typing import List, Dict, Optional
from datetime import datetime
from pymongo import MongoClient, DESCENDING
from pymongo.errors import ConnectionFailure, PyMongoError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class PropertyMongoClient:
    """
    MongoDB client for storing and retrieving property search results

    Storage schema:
    {
        "user_id": str,
        "session_id": str,
        "search_query": {
            "locality": str,
            "budget": float
        },
        "timestamp": datetime,
        "properties": [
            {
                "address": str,
                "sale_price": int,
                "beds": int,
                "baths": float,
                ...all property fields...
            }
        ]
    }
    """

    def __init__(self, user_id: str, session_id: str, mongo_uri: Optional[str] = None, db_name: Optional[str] = None):
        """
        Initialize MongoDB client for a specific user and session

        Args:
            user_id: Unique user identifier
            session_id: Unique session identifier
            mongo_uri: MongoDB connection URI (defaults to MONGODB_URI env var)
            db_name: Database name (defaults to MONGODB_DB_NAME env var)
        """
        self.user_id = user_id
        self.session_id = session_id

        # Get MongoDB URI from environment or parameter
        self.mongo_uri = mongo_uri or os.getenv("MONGODB_URI")
        if not self.mongo_uri:
            raise ValueError("MongoDB URI not provided. Set MONGODB_URI environment variable or pass mongo_uri parameter.")

        # Get database name from environment or parameter
        self.db_name = db_name or os.getenv("MONGODB_DB_NAME")
        if not self.db_name:
            raise ValueError("MongoDB database name not provided. Set MONGODB_DB_NAME environment variable or pass db_name parameter.")

        # Initialize MongoDB connection
        try:
            self.client = MongoClient(self.mongo_uri)
            # Test connection
            self.client.admin.command('ping')

            # Get database and collection
            self.db = self.client.get_database(self.db_name)
            self.collection = self.db.get_collection("searches")

            # Create indexes for efficient querying
            self.collection.create_index([("user_id", 1), ("session_id", 1)])
            self.collection.create_index([("user_id", 1), ("timestamp", DESCENDING)])
            self.collection.create_index([("timestamp", DESCENDING)])

        except ConnectionFailure as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")

    def store_properties(self, locality: str, budget: float, properties: List[Dict]) -> str:
        """
        Store property search results to MongoDB

        Args:
            locality: Search locality (e.g., "Philadelphia, PA")
            budget: Maximum budget searched
            properties: List of property dictionaries returned from fetch_properties()

        Returns:
            Inserted document ID as string

        Raises:
            PyMongoError: If storage fails
        """
        try:
            document = {
                "user_id": self.user_id,
                "session_id": self.session_id,
                "search_query": {
                    "locality": locality,
                    "budget": budget
                },
                "timestamp": datetime.utcnow(),
                "properties": properties,
                "property_count": len(properties)
            }

            result = self.collection.insert_one(document)
            print(f"Stored {len(properties)} properties for user {self.user_id}, session {self.session_id}")
            return str(result.inserted_id)

        except PyMongoError as e:
            raise PyMongoError(f"Failed to store properties: {e}")

    def get_session_properties(self) -> Optional[Dict]:
        """
        Retrieve all properties for the current session

        Returns:
            Dictionary with search data and properties, or None if not found
        """
        try:
            result = self.collection.find_one(
                {"user_id": self.user_id, "session_id": self.session_id},
                sort=[("timestamp", DESCENDING)]
            )

            if result:
                # Convert ObjectId to string for JSON serialization
                result['_id'] = str(result['_id'])

            return result

        except PyMongoError as e:
            print(f"Error retrieving session properties: {e}")
            return None

    def get_user_history(self, limit: int = 10) -> List[Dict]:
        """
        Get search history for the current user across all sessions

        Args:
            limit: Maximum number of searches to return (default: 10)

        Returns:
            List of search documents, most recent first
        """
        try:
            cursor = self.collection.find(
                {"user_id": self.user_id},
                sort=[("timestamp", DESCENDING)],
                limit=limit
            )

            results = []
            for doc in cursor:
                # Convert ObjectId to string
                doc['_id'] = str(doc['_id'])
                results.append(doc)

            return results

        except PyMongoError as e:
            print(f"Error retrieving user history: {e}")
            return []

    def get_all_sessions_for_user(self) -> List[str]:
        """
        Get all unique session IDs for the current user

        Returns:
            List of session IDs
        """
        try:
            sessions = self.collection.distinct("session_id", {"user_id": self.user_id})
            return sessions

        except PyMongoError as e:
            print(f"Error retrieving user sessions: {e}")
            return []

    def delete_session(self) -> int:
        """
        Delete all data for the current session

        Returns:
            Number of documents deleted
        """
        try:
            result = self.collection.delete_many({
                "user_id": self.user_id,
                "session_id": self.session_id
            })
            print(f"Deleted {result.deleted_count} documents for session {self.session_id}")
            return result.deleted_count

        except PyMongoError as e:
            print(f"Error deleting session: {e}")
            return 0

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connection"""
        self.close()
