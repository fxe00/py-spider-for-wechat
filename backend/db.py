import logging
from typing import Optional

from flask import current_app
from pymongo import MongoClient, ASCENDING

client: Optional[MongoClient] = None


def init_db(app):
    """Initialize Mongo client and create indexes."""
    from backend.config import get_settings

    settings = get_settings()
    global client
    client = MongoClient(settings.mongo_uri)
    app.mongo = client[settings.mongo_db]

    # Indexes for data integrity
    app.mongo["articles"].create_index([("url", ASCENDING)], unique=True)
    app.mongo["targets"].create_index([("enabled", ASCENDING)])
    app.mongo["targets"].create_index([("freq_minutes", ASCENDING)])
    app.mongo["targets"].create_index([("name", ASCENDING)], unique=True)
    app.mongo["mp_accounts"].create_index([("name", ASCENDING)], unique=True)
    app.mongo["users"].create_index([("username", ASCENDING)], unique=True)
    app.mongo["crawl_logs"].create_index([("created_at", ASCENDING)])
    app.mongo["crawl_logs"].create_index([("target_id", ASCENDING)])

    logging.info("MongoDB connected: %s/%s", settings.mongo_uri, settings.mongo_db)


def get_db():
    if not current_app or not hasattr(current_app, "mongo"):
        raise RuntimeError("Database not initialized")
    return current_app.mongo
