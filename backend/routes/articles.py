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
    # 优化：使用投影只获取 _id 字段，减少数据传输
    if category:
        target_objs = list(get_db()["targets"].find(
            {"category": category},
            {"_id": 1}  # 只获取 _id 字段
        ))
        if target_objs:
            # articles 表中的 target_id 是 ObjectId 类型
            target_ids = [t["_id"] for t in target_objs]
            query["target_id"] = {"$in": target_ids}
        else:
            # 如果没有找到匹配的目标，返回空结果
            return jsonify({"total": 0, "items": []})

    # 优化：如果查询条件简单，使用 estimated_document_count（更快但不精确）
    # 对于复杂查询，使用 count_documents
    use_estimated = not q and not category  # 没有正则查询和分类查询时使用估算
    if use_estimated:
        try:
            total = get_db()["articles"].estimated_document_count()
        except Exception:
            total = get_db()["articles"].count_documents(query)
    else:
        total = get_db()["articles"].count_documents(query)

    # 后端分页：使用 MongoDB 的 skip 和 limit
    # 优化：使用投影减少数据传输（只获取需要的字段）
    projection = {
        "_id": 1,
        "mp_name": 1,
        "mp_id": 1,
        "title": 1,
        "url": 1,
        "publish_at": 1,
        "cover": 1,
        "digest": 1,
        "target_id": 1,
        "created_at": 1,
    }
    skip = (page - 1) * page_size
    cursor = get_db()["articles"].find(query, projection).sort("publish_at", -1).skip(skip).limit(page_size)
    paged_docs = list(cursor)

    # 获取当前页文章的target_id和mp_name（只查询当前页的数据）
    target_ids = list(set([ObjectId(doc.get("target_id")) for doc in paged_docs if doc.get("target_id")]))
    mp_names = list(set([doc.get("mp_name") for doc in paged_docs if doc.get("mp_name")]))

    # 批量查询targets获取分类和头像（优化：合并查询，减少数据库访问次数）
    targets_map = {}
    mp_name_to_avatar = {}

    if target_ids or mp_names:
        # 合并查询：同时通过target_id和mp_name查询
        target_query = {}
        if target_ids and mp_names:
            target_query = {"$or": [
                {"_id": {"$in": target_ids}},
                {"name": {"$in": mp_names}}
            ]}
        elif target_ids:
            target_query = {"_id": {"$in": target_ids}}
        elif mp_names:
            target_query = {"name": {"$in": mp_names}}

        targets = list(get_db()["targets"].find(
            target_query,
            {"_id": 1, "category": 1, "mp_avatar": 1, "name": 1}
        ))

        # 构建两个映射
        for t in targets:
            target_id_str = str(t["_id"])
            targets_map[target_id_str] = {
                "category": t.get("category"),
                "mp_avatar": t.get("mp_avatar")
            }
            # 同时构建mp_name映射
            if t.get("name"):
                mp_name_to_avatar[t["name"]] = {
                    "mp_avatar": t.get("mp_avatar"),
                    "category": t.get("category")
                }

    # 序列化数据
    data = []
    for doc in paged_docs:
        target_id_str = str(doc.get("target_id")) if doc.get("target_id") else None
        target_info = targets_map.get(target_id_str, {}) if target_id_str else {}

        # 如果通过target_id没找到头像，尝试通过mp_name查找
        if not target_info.get("mp_avatar") and doc.get("mp_name"):
            mp_info = mp_name_to_avatar.get(doc.get("mp_name"), {})
            if mp_info.get("mp_avatar"):
                target_info["mp_avatar"] = mp_info["mp_avatar"]
            if mp_info.get("category") and not target_info.get("category"):
                target_info["category"] = mp_info["category"]

        data.append(_serialize(doc, category=target_info.get("category"), mp_avatar=target_info.get("mp_avatar")))

    return jsonify({"total": total, "items": data})


@bp.route("/mp-names", methods=["GET"])
@jwt_required
def list_mp_names():
    """获取所有已使用的公众号名称列表"""
    mp_names = get_db()["articles"].distinct("mp_name")
    # 过滤掉 None 和空字符串
    mp_names = [name for name in mp_names if name]
    return jsonify(sorted(mp_names))


@bp.route("/mp-summary", methods=["GET"])
@jwt_required
def mp_summary():
    """获取所有公众号的汇总统计（文章数、最新发布时间、头像等）"""
    from pymongo import DESCENDING

    # 使用聚合管道统计每个公众号的文章数和最新发布时间
    pipeline = [
        {
            "$group": {
                "_id": "$mp_name",
                "count": {"$sum": 1},
                "latest_publish_at": {"$max": "$publish_at"},
                "target_id": {"$first": "$target_id"},  # 用于获取头像和分类
            }
        },
        {
            "$sort": {"count": DESCENDING}
        }
    ]

    results = list(get_db()["articles"].aggregate(pipeline))

    # 获取所有 target_id 和 mp_name，用于查询头像和分类
    target_ids = [ObjectId(r["target_id"]) for r in results if r.get("target_id")]
    mp_names = [r["_id"] for r in results if r.get("_id")]

    # 批量查询 targets 获取头像和分类
    targets_map = {}
    if target_ids:
        targets = list(get_db()["targets"].find(
            {"_id": {"$in": target_ids}},
            {"_id": 1, "category": 1, "mp_avatar": 1, "name": 1}
        ))
        for t in targets:
            targets_map[str(t["_id"])] = {
                "mp_avatar": t.get("mp_avatar"),
                "category": t.get("category")
            }

    # 通过 mp_name 查找头像（备用方案）
    mp_name_to_avatar = {}
    if mp_names:
        targets_by_name = list(get_db()["targets"].find(
            {"name": {"$in": mp_names}},
            {"name": 1, "mp_avatar": 1, "category": 1}
        ))
        for t in targets_by_name:
            mp_name_to_avatar[t.get("name")] = {
                "mp_avatar": t.get("mp_avatar"),
                "category": t.get("category")
            }

    # 组装返回数据
    summary = []
    for r in results:
        mp_name = r.get("_id") or "未知"
        target_id_str = str(r.get("target_id")) if r.get("target_id") else None

        # 优先使用 target_id 查找头像，其次使用 mp_name
        mp_avatar = None
        if target_id_str and target_id_str in targets_map:
            mp_avatar = targets_map[target_id_str].get("mp_avatar")
        if not mp_avatar and mp_name in mp_name_to_avatar:
            mp_avatar = mp_name_to_avatar[mp_name].get("mp_avatar")

        summary.append({
            "mp_name": mp_name,
            "count": r.get("count", 0),
            "latest_publish_at": r.get("latest_publish_at"),
            "mp_avatar": mp_avatar,
        })

    return jsonify(summary)


def parse_dt(value):
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None
