from flask import Blueprint, request, jsonify
from bson import ObjectId

from backend.db import get_db
from backend.security import jwt_required
import time

bp = Blueprint("mp_accounts", __name__, url_prefix="/api/mp-accounts")


def _serialize(doc):
    return {
        "id": str(doc["_id"]),
        "name": doc.get("name"),
        "token": doc.get("token"),
        "cookie": doc.get("cookie"),
        "remark": doc.get("remark"),
        "updated_at": doc.get("updated_at"),
    }


@bp.route("", methods=["GET"])
@jwt_required
def list_accounts():
    q = (request.args.get("q") or "").strip()
    query = {}
    if q:
        query["name"] = {"$regex": q, "$options": "i"}
    data = [_serialize(x) for x in get_db()["mp_accounts"].find(query).sort("updated_at", -1)]
    return jsonify(data)


@bp.route("", methods=["POST"])
@jwt_required
def create_account():
    body = request.get_json(force=True, silent=True) or {}
    name = (body.get("name") or "").strip()
    token = (body.get("token") or "").strip()
    cookie = (body.get("cookie") or "").strip()
    remark = (body.get("remark") or "").strip()
    if not name or not token or not cookie:
        return jsonify({"message": "name/token/cookie 必填"}), 400
    payload = {
        "name": name,
        "token": token,
        "cookie": cookie,
        "remark": remark,
        "updated_at": body.get("updated_at") or time.time(),
    }
    result = get_db()["mp_accounts"].insert_one(payload)
    payload["_id"] = result.inserted_id
    return jsonify(_serialize(payload)), 201


@bp.route("/<id>", methods=["PUT"])
@jwt_required
def update_account(id):
    body = request.get_json(force=True, silent=True) or {}
    updates = {k: v for k, v in body.items() if k in {"name", "token", "cookie", "remark", "updated_at"}}
    if not updates:
        return jsonify({"message": "无更新字段"}), 400
    get_db()["mp_accounts"].update_one({"_id": ObjectId(id)}, {"$set": updates})
    doc = get_db()["mp_accounts"].find_one({"_id": ObjectId(id)})
    if not doc:
        return jsonify({"message": "未找到记录"}), 404
    return jsonify(_serialize(doc))


@bp.route("/<id>", methods=["DELETE"])
@jwt_required
def delete_account(id):
    get_db()["mp_accounts"].delete_one({"_id": ObjectId(id)})
    return jsonify({"deleted": True})
