from flask import Blueprint, request, jsonify
from bson import ObjectId

from backend.db import get_db
from backend.security import jwt_required
from backend.scheduler import trigger_target, refresh_jobs

bp = Blueprint("targets", __name__, url_prefix="/api/targets")


def _serialize(doc):
    return {
        "id": str(doc["_id"]),
        "name": doc.get("name"),
        "biz": doc.get("biz"),
        "category": doc.get("category"),
        "freq_minutes": doc.get("freq_minutes"),
        "schedule_mode": doc.get("schedule_mode"),
        "interval_value": doc.get("interval_value"),
        "interval_unit": doc.get("interval_unit"),
        "daily_times": doc.get("daily_times"),
        "cron_expr": doc.get("cron_expr"),
        "enabled": doc.get("enabled", True),
        "account_id": str(doc["account_id"]) if doc.get("account_id") else None,
        "last_run_at": doc.get("last_run_at"),
        "created_at": doc.get("created_at"),
        # 公众号详细信息
        "mp_avatar": doc.get("mp_avatar"),
        "mp_alias": doc.get("mp_alias"),
        "mp_service_type": doc.get("mp_service_type"),
        "mp_verify_type": doc.get("mp_verify_type"),
        "mp_signature": doc.get("mp_signature"),
        "mp_user_name": doc.get("mp_user_name"),
        "last_error": doc.get("last_error"),
    }


@bp.route("", methods=["GET"])
@jwt_required
def list_targets():
    q = (request.args.get("q") or "").strip()
    query = {}
    if q:
        query["name"] = {"$regex": q, "$options": "i"}
    data = [_serialize(x) for x in get_db()["targets"].find(query).sort("created_at", -1)]
    return jsonify(data)


@bp.route("", methods=["POST"])
@jwt_required
def create_target():
    body = request.get_json(force=True, silent=True) or {}
    name = (body.get("name") or "").strip()
    schedule_mode = body.get("schedule_mode") or "daily"
    interval_value = body.get("interval_value")
    interval_unit = body.get("interval_unit")
    daily_times = body.get("daily_times") or ["09:00", "13:00", "18:00", "22:00"]
    cron_expr = (body.get("cron_expr") or "").strip()
    freq = body.get("freq_minutes")
    account_id = body.get("account_id")
    if not name or not account_id:
        return jsonify({"message": "name/account_id 必填"}), 400

    # 检查名称是否已存在
    existing = get_db()["targets"].find_one({"name": name})
    if existing:
        return jsonify({"message": f"公众号名称 '{name}' 已存在"}), 400

    payload = {
        "name": name,
        "biz": (body.get("biz") or "").strip(),
        "category": (body.get("category") or "").strip() or None,
        "freq_minutes": int(freq) if freq else None,
        "schedule_mode": schedule_mode,
        "interval_value": interval_value,
        "interval_unit": interval_unit,
        "daily_times": daily_times,
        "cron_expr": cron_expr,
        "enabled": bool(body.get("enabled", True)),
        "account_id": ObjectId(account_id),
        "created_at": body.get("created_at"),
        "last_run_at": None,
    }
    try:
        result = get_db()["targets"].insert_one(payload)
        payload["_id"] = result.inserted_id
        refresh_jobs()
        return jsonify(_serialize(payload)), 201
    except Exception as exc:
        # 捕获唯一索引冲突
        if "duplicate key" in str(exc).lower() or "E11000" in str(exc):
            return jsonify({"message": f"公众号名称 '{name}' 已存在"}), 400
        raise


@bp.route("/<id>", methods=["PUT"])
@jwt_required
def update_target(id):
    body = request.get_json(force=True, silent=True) or {}
    updates = {}
    for key in [
        "name",
        "biz",
        "category",
        "freq_minutes",
        "enabled",
        "schedule_mode",
        "interval_value",
        "interval_unit",
        "daily_times",
        "cron_expr",
    ]:
        if key in body:
            if key == "category":
                updates[key] = (body[key] or "").strip() or None
            else:
                updates[key] = body[key]
    if "account_id" in body and body["account_id"]:
        updates["account_id"] = ObjectId(body["account_id"])
    if not updates:
        return jsonify({"message": "无更新字段"}), 400

    # 如果更新名称，检查是否与其他记录冲突
    if "name" in updates:
        name = (updates["name"] or "").strip()
        if not name:
            return jsonify({"message": "公众号名称不能为空"}), 400
        updates["name"] = name  # 更新清理后的名称
        existing = get_db()["targets"].find_one({"name": name, "_id": {"$ne": ObjectId(id)}})
        if existing:
            return jsonify({"message": f"公众号名称 '{name}' 已存在"}), 400

    try:
        get_db()["targets"].update_one({"_id": ObjectId(id)}, {"$set": updates})
        doc = get_db()["targets"].find_one({"_id": ObjectId(id)})
        if not doc:
            return jsonify({"message": "未找到记录"}), 404
        refresh_jobs()
        return jsonify(_serialize(doc))
    except Exception as exc:
        # 捕获唯一索引冲突
        if "duplicate key" in str(exc).lower() or "E11000" in str(exc):
            name = updates.get("name", "")
            return jsonify({"message": f"公众号名称 '{name}' 已存在"}), 400
        raise


@bp.route("/<id>", methods=["DELETE"])
@jwt_required
def delete_target(id):
    get_db()["targets"].delete_one({"_id": ObjectId(id)})
    refresh_jobs()
    return jsonify({"deleted": True})


@bp.route("/<id>", methods=["GET"])
@jwt_required
def get_target(id):
    doc = get_db()["targets"].find_one({"_id": ObjectId(id)})
    if not doc:
        return jsonify({"message": "未找到记录"}), 404
    return jsonify(_serialize(doc))


@bp.route("/<id>/run", methods=["POST"])
@jwt_required
def run_target(id):
    trigger_target(id)
    return jsonify({"triggered": True})


@bp.route("/categories", methods=["GET"])
@jwt_required
def list_categories():
    """获取所有已使用的分类列表"""
    categories = get_db()["targets"].distinct("category")
    # 过滤掉 None 和空字符串
    categories = [c for c in categories if c]
    return jsonify(sorted(categories))
