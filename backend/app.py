import logging
import os

from flask import Flask, jsonify
from flask_cors import CORS
from flask import send_from_directory

from backend.auth import auth_bp
from backend.config import get_settings
from backend.db import init_db
from backend.routes.articles import bp as articles_bp
from backend.routes.mp_accounts import bp as accounts_bp
from backend.routes.targets import bp as targets_bp
from backend.routes.logs import bp as logs_bp
from backend.scheduler import setup_scheduler, refresh_jobs
from backend.security import hash_password


def create_app() -> Flask:
    settings = get_settings()
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": settings.cors_allow_origin}})

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    init_db(app)
    ensure_admin(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(targets_bp)
    app.register_blueprint(articles_bp)
    app.register_blueprint(logs_bp)

    setup_scheduler(app)

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok"})

    dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        # 避免与 API 冲突
        if path.startswith("api/"):
            return jsonify({"message": "Not Found"}), 404
        if os.path.exists(os.path.join(dist_dir, path)):
            return send_from_directory(dist_dir, path)
        index_path = os.path.join(dist_dir, "index.html")
        if os.path.exists(index_path):
            return send_from_directory(dist_dir, "index.html")
        return jsonify({"status": "ok", "message": "wechat spider backend running"})

    @app.route("/api/admin/refresh-jobs", methods=["POST"])
    def refresh():
        refresh_jobs()
        return jsonify({"refreshed": True})

    return app


def ensure_admin(app: Flask):
    settings = get_settings()
    db = getattr(app, "mongo", None)
    if db is None:
        raise RuntimeError("Database not initialized on app")
    user = db["users"].find_one({"username": settings.default_admin_user})
    if not user:
        db["users"].insert_one(
            {
                "username": settings.default_admin_user,
                "password_hash": hash_password(settings.default_admin_pass),
                "roles": ["admin"],
            }
        )
        logging.info("Created default admin user=%s", settings.default_admin_user)


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
