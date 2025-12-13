from datetime import datetime, timedelta
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
        # 详细信息字段
        "step": doc.get("step"),
        "articles_count": doc.get("articles_count"),
        "new_count": doc.get("new_count"),
        "fakeid": doc.get("fakeid"),
        "avatar_fetched": doc.get("avatar_fetched"),
        "error_type": doc.get("error_type"),
        "duration_ms": doc.get("duration_ms"),
        "page_num": doc.get("page_num"),
        "avatar_size": doc.get("avatar_size"),
    }


def _cleanup_stale_progress_logs():
    """
    清理长时间处于 progress 状态的日志，将其标记为超时
    阈值：30分钟
    """
    threshold_time = datetime.utcnow() - timedelta(minutes=30)
    result = get_db()["crawl_logs"].update_many(
        {
            "status": "progress",
            "created_at": {"$lt": threshold_time}
        },
        {
            "$set": {
                "status": "error",
                "message": "任务超时（长时间未完成）"
            }
        }
    )
    if result.modified_count > 0:
        print(f"Cleaned up {result.modified_count} stale progress logs")


@bp.route("", methods=["GET"])
@jwt_required
def list_logs():
    # 每次查询时自动清理超时的 progress 日志
    _cleanup_stale_progress_logs()

    target_id = request.args.get("target_id")
    target_name = request.args.get("target_name")
    status = request.args.get("status")
    latest_only = request.args.get("latest_only", "false").lower() == "true"  # 是否只显示每个任务的最新日志
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 20))

    query = {}
    if target_id:
        query["target_id"] = ObjectId(target_id)
    if target_name:
        query["target_name"] = {"$regex": target_name, "$options": "i"}
    if status:
        query["status"] = status

    if latest_only:
        # 只返回每个任务的最新日志（按 target_id 分组，取最新的）
        pipeline = [
            {"$match": query},
            {"$sort": {"created_at": -1}},
            {
                "$group": {
                    "_id": "$target_id",
                    "latest_log": {"$first": "$$ROOT"}
                }
            },
            {"$replaceRoot": {"newRoot": "$latest_log"}},
            {"$sort": {"created_at": -1}},
        ]
        cursor = get_db()["crawl_logs"].aggregate(pipeline)
        all_logs = list(cursor)
        total = len(all_logs)
        # 手动分页
        skip = (page - 1) * page_size
        paged_logs = all_logs[skip:skip + page_size]
        return jsonify({"total": total, "items": [_serialize(x) for x in paged_logs]})
    else:
        # 返回所有日志（包括所有步骤）
        total = get_db()["crawl_logs"].count_documents(query)
        skip = (page - 1) * page_size
        cursor = get_db()["crawl_logs"].find(query).sort("created_at", -1).skip(skip).limit(page_size)
        return jsonify({"total": total, "items": [_serialize(x) for x in cursor]})


@bp.route("/cleanup", methods=["POST"])
@jwt_required
def cleanup_stale_logs():
    """手动清理超时的 progress 日志"""
    _cleanup_stale_progress_logs()
    return jsonify({"message": "清理完成"})
