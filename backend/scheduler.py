import logging
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from bson import ObjectId
from flask import Flask

from backend.db import get_db
from crawler.tasks import run_crawl

scheduler = BackgroundScheduler()
_app: Optional[Flask] = None


def setup_scheduler(app: Flask):
    global _app
    _app = app
    scheduler.configure(timezone="Asia/Shanghai")
    scheduler.start()
    refresh_jobs()
    app.teardown_appcontext(lambda _exc=None: scheduler.shutdown(wait=False) if scheduler.running else None)


def refresh_jobs():
    if _app is None:
        raise RuntimeError("Scheduler not initialized with app")
    with _app.app_context():
        scheduler.remove_all_jobs()
        targets = list(get_db()["targets"].find({"enabled": True}))
        for target in targets:
            _add_jobs_for_target(target)
        logging.info("Scheduler loaded %s targets", len(targets))


def trigger_target(target_id: str):
    if _app is None:
        raise RuntimeError("Scheduler not initialized with app")
    with _app.app_context():
        target = get_db()["targets"].find_one({"_id": ObjectId(target_id)})
        if not target or not target.get("enabled", True):
            return
        account = None
        if target.get("account_id"):
            account = get_db()["mp_accounts"].find_one({"_id": ObjectId(target["account_id"])})
        try:
            run_crawl(target, account)
            get_db()["targets"].update_one({"_id": target["_id"]}, {"$set": {"last_run_at": datetime.utcnow()}})
        except Exception as exc:
            logging.exception("Crawl failed for target %s: %s", target_id, exc)
            get_db()["targets"].update_one({"_id": ObjectId(target_id)}, {"$set": {"last_error": str(exc)}})


def _add_jobs_for_target(target: dict):
    target_id = str(target["_id"])
    mode = target.get("schedule_mode") or "daily"
    jobs = []
    if mode == "interval":
        minutes = _interval_to_minutes(target)
        if minutes:
            jobs.append(
                {
                    "id": target_id,
                    "trigger": IntervalTrigger(minutes=minutes),
                }
            )
    elif mode == "daily":
        times = target.get("daily_times") or ["09:00", "13:00", "18:00", "22:00"]
        for idx, t in enumerate(times):
            try:
                hh, mm = t.split(":")
                cron = CronTrigger(hour=int(hh), minute=int(mm), timezone="Asia/Shanghai")
                jobs.append(
                    {
                        "id": f"{target_id}-{idx}",
                        "trigger": cron,
                    }
                )
                logging.info("Added daily job for target %s at %s (job id: %s-%s)", target_id, t, target_id, idx)
            except Exception as exc:
                logging.warning("Invalid daily time %s for target %s: %s", t, target_id, exc)
    elif mode == "cron":
        expr = (target.get("cron_expr") or "").strip()
        if expr:
            try:
                cron = CronTrigger.from_crontab(expr)
                jobs.append({"id": target_id, "trigger": cron})
            except Exception as exc:
                logging.warning("Invalid cron expr %s for target %s: %s", expr, target_id, exc)
    else:
        # 兼容旧数据：使用 freq_minutes
        minutes = _interval_to_minutes(target)
        if minutes:
            jobs.append({"id": target_id, "trigger": IntervalTrigger(minutes=minutes)})

    for job in jobs:
        scheduler.add_job(
            trigger_target,
            id=job["id"],
            trigger=job["trigger"],
            args=[target_id],
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=300,
        )


def _interval_to_minutes(target: dict):
    mode = target.get("schedule_mode")
    if mode == "interval":
        val = target.get("interval_value")
        unit = target.get("interval_unit") or "minute"
        if not val:
            return None
        v = float(val)
        if unit == "hour":
            return max(int(v * 60), 1)
        if unit == "day":
            return max(int(v * 1440), 1)
        return max(int(v), 1)
    # fallback freq_minutes
    minutes = target.get("freq_minutes")
    if minutes:
        return max(int(minutes), 1)
    return None
