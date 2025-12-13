from datetime import datetime

from flask import Blueprint, request, jsonify
from bson import ObjectId

from backend.db import get_db
from backend.security import jwt_required

bp = Blueprint("articles", __name__, url_prefix="/api/articles")


def _serialize(doc, category=None, mp_avatar=None):
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
        "category": category,
        "mp_avatar": mp_avatar or doc.get("mp_avatar"),
        "created_at": doc.get("created_at"),
    }


@bp.route("", methods=["GET"])
@jwt_required
def list_articles():
    args = request.args
    mp_name = args.get("mp_name")
    q = args.get("q")
    category = args.get("category")
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

    # 如果指定了分类，需要通过 target_id 关联 targets 表
    if category:
        target_objs = list(get_db()["targets"].find({"category": category}, {"_id": 1}))
        if target_objs:
            # articles 表中的 target_id 是 ObjectId 类型
            target_ids = [t["_id"] for t in target_objs]
            query["target_id"] = {"$in": target_ids}
        else:
            # 如果没有找到匹配的目标，返回空结果
            return jsonify({"total": 0, "items": []})

    cursor = get_db()["articles"].find(query).sort("publish_at", -1)
    total = get_db()["articles"].count_documents(query)

    # 先获取所有文章的target_id（不限制数量，用于批量查询targets）
    all_docs = list(cursor)
    target_ids = list(set([ObjectId(doc.get("target_id")) for doc in all_docs if doc.get("target_id")]))

    # 批量查询targets获取分类和头像
    targets_map = {}
    if target_ids:
        targets = list(get_db()["targets"].find({"_id": {"$in": target_ids}},
                       {"_id": 1, "category": 1, "mp_avatar": 1}))
        targets_map = {str(t["_id"]): {"category": t.get("category"), "mp_avatar": t.get("mp_avatar")} for t in targets}

    # 分页处理
    start = (page - 1) * page_size
    paged_docs = all_docs[start:start + page_size]

    data = []
    for doc in paged_docs:
        target_id_str = str(doc.get("target_id")) if doc.get("target_id") else None
        target_info = targets_map.get(target_id_str, {}) if target_id_str else {}
        data.append(_serialize(doc, category=target_info.get("category"), mp_avatar=target_info.get("mp_avatar")))

    return jsonify({"total": total, "items": data})


def parse_dt(value):
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None
