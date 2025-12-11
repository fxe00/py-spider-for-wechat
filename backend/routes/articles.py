from datetime import datetime

from flask import Blueprint, request, jsonify
from bson import ObjectId

from backend.db import get_db
from backend.security import jwt_required

bp = Blueprint("articles", __name__, url_prefix="/api/articles")


def _serialize(doc):
    return {
        "id": str(doc["_id"]),
        "mp_name": doc.get("mp_name"),
        "mp_id": doc.get("mp_id"),
        "title": doc.get("title"),
        "url": doc.get("url"),
        "publish_at": doc.get("publish_at"),
        "cover": doc.get("cover"),
        "digest": doc.get("digest"),
        "target_id": str(doc["target_id"]) if doc.get("target_id") else None,
        "created_at": doc.get("created_at"),
    }


@bp.route("", methods=["GET"])
@jwt_required
def list_articles():
    args = request.args
    mp_name = args.get("mp_name")
    q = args.get("q")
    start = args.get("start")
    end = args.get("end")
    page = int(args.get("page", 1))
    page_size = int(args.get("page_size", 20))
    query = {}
    if mp_name:
        query["mp_name"] = mp_name
    if q:
        query["title"] = {"$regex": q, "$options": "i"}
    if start:
        query.setdefault("publish_at", {})["$gte"] = parse_dt(start)
    if end:
        query.setdefault("publish_at", {})["$lte"] = parse_dt(end)

    cursor = get_db()["articles"].find(query).sort("publish_at", -1)
    total = get_db()["articles"].count_documents(query)
    cursor = cursor.skip((page - 1) * page_size).limit(page_size)
    data = [_serialize(x) for x in cursor]
    return jsonify({"total": total, "items": data})


def parse_dt(value):
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None
