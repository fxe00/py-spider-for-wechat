import logging
from flask import Blueprint, request, jsonify

from backend.db import get_db
from backend.security import verify_password, create_token

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    body = request.get_json(force=True, silent=True) or {}
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""
    if not username or not password:
        return jsonify({"message": "用户名或密码不能为空"}), 400

    user = get_db()["users"].find_one({"username": username})
    if not user or not verify_password(password, user.get("password_hash", "")):
        logging.warning("Login failed for user=%s", username)
        return jsonify({"message": "用户名或密码错误"}), 401

    token = create_token({"user_id": str(user["_id"]), "username": username})
    return jsonify({"token": token, "username": username})


@auth_bp.route("/me", methods=["GET"])
def me():
    # This endpoint relies on gateway/guard to inject user in request; kept simple here.
    return jsonify({"status": "ok"})
