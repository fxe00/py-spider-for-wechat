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

    from pymongo import DESCENDING, TEXT

    # Indexes for data integrity
    app.mongo["articles"].create_index([("url", ASCENDING)], unique=True)

    # Articles 性能优化索引
    # 1. publish_at 索引（用于排序和范围查询）- 最重要
    app.mongo["articles"].create_index([("publish_at", DESCENDING)])
    # 2. target_id 索引（用于分类筛选）
    app.mongo["articles"].create_index([("target_id", ASCENDING)])
    # 3. mp_name 索引（用于公众号筛选）
    app.mongo["articles"].create_index([("mp_name", ASCENDING)])
    # 4. 复合索引：publish_at + target_id（优化分类+排序查询）
    app.mongo["articles"].create_index([("publish_at", DESCENDING), ("target_id", ASCENDING)])
    # 5. 复合索引：publish_at + mp_name（优化公众号+排序查询）
    app.mongo["articles"].create_index([("publish_at", DESCENDING), ("mp_name", ASCENDING)])
    # 6. 文本索引：title（用于标题搜索，但正则查询仍可能较慢）
    try:
        app.mongo["articles"].create_index([("title", TEXT)])
    except Exception:
        # 如果已存在文本索引或创建失败，忽略
        pass

    # Targets 索引
    app.mongo["targets"].create_index([("enabled", ASCENDING)])
    app.mongo["targets"].create_index([("freq_minutes", ASCENDING)])
    app.mongo["targets"].create_index([("name", ASCENDING)], unique=True)
    app.mongo["targets"].create_index([("category", ASCENDING)])  # 用于分类查询

    # 其他集合索引
    app.mongo["mp_accounts"].create_index([("name", ASCENDING)], unique=True)
    app.mongo["users"].create_index([("username", ASCENDING)], unique=True)
    app.mongo["crawl_logs"].create_index([("created_at", DESCENDING)])
    app.mongo["crawl_logs"].create_index([("target_id", ASCENDING)])
    app.mongo["crawl_logs"].create_index([("status", ASCENDING), ("created_at", DESCENDING)])  # 用于状态筛选+排序

    logging.info("MongoDB connected: %s/%s", settings.mongo_uri, settings.mongo_db)
    logging.info("MongoDB indexes created for performance optimization")


def get_db():
    if not current_app or not hasattr(current_app, "mongo"):
        raise RuntimeError("Database not initialized")
    return current_app.mongo
