from flask import Blueprint, request, jsonify
from bson import ObjectId

from backend.db import get_db
from backend.security import jwt_required

bp = Blueprint("logs", __name__, url_prefix="/api/logs")


def _serialize(doc):
    return {
        "id": str(doc["_id"]),
        "target_id": str(doc["target_id"]) if doc.get("target_id") else None,
        "target_name": doc.get("target_name"),
        "status": doc.get("status"),
        "message": doc.get("message"),
        "created_at": doc.get("created_at"),
    }


@bp.route("", methods=["GET"])
@jwt_required
def list_logs():
    target_id = request.args.get("target_id")
    limit = int(request.args.get("limit", 100))
    query = {}
    if target_id:
        query["target_id"] = ObjectId(target_id)
    cursor = get_db()["crawl_logs"].find(query).sort("created_at", -1).limit(limit)
    return jsonify([_serialize(x) for x in cursor])

