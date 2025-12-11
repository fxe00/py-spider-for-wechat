import datetime
from functools import wraps
from typing import Dict, Optional

import jwt
from flask import request, jsonify, g
from werkzeug.security import check_password_hash, generate_password_hash

from backend.config import get_settings


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)


def create_token(payload: Dict) -> str:
    settings = get_settings()
    exp = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.jwt_expire_minutes)
    data = {**payload, "exp": exp}
    return jwt.encode(data, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> Optional[Dict]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


def jwt_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"message": "Unauthorized"}), 401
        token = auth_header.replace("Bearer ", "", 1).strip()
        decoded = decode_token(token)
        if not decoded:
            return jsonify({"message": "Unauthorized"}), 401
        g.user = decoded
        return func(*args, **kwargs)

    return wrapper

