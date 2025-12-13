import atexit
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from bson import ObjectId
from flask import Flask

from backend.db import get_db
from crawler.tasks import run_crawl

scheduler = BackgroundScheduler()
_app: Optional[Flask] = None
# 使用线程池异步执行爬取任务，避免阻塞主线程
_executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="crawl")


def setup_scheduler(app: Flask):
    global _app
    _app = app
    scheduler.configure(timezone="Asia/Shanghai")
    if not scheduler.running:
        scheduler.start()
        import time
        time.sleep(1.0)  # 等待调度器完全启动
        logging.info("Scheduler started, timezone: Asia/Shanghai")
        # 注册退出时的清理函数
        atexit.register(lambda: scheduler.shutdown(wait=False) if scheduler.running else None)
        atexit.register(lambda: _executor.shutdown(wait=True))
    refresh_jobs()


def refresh_jobs():
    if _app is None:
        raise RuntimeError("Scheduler not initialized with app")
    with _app.app_context():
        # 确保调度器正在运行
        if not scheduler.running:
            logging.warning("Scheduler not running, starting it...")
            scheduler.start()
            import time
            time.sleep(1.0)

        scheduler.remove_all_jobs()
        targets = list(get_db()["targets"].find({"enabled": True}))

        # 收集需要立即执行的目标（daily 模式且今天的执行时间已过，但今天还未执行过）
        tz = pytz.timezone("Asia/Shanghai")
        current_time = datetime.now(tz)
        today = current_time.date()
        targets_to_execute = set()

        for target in targets:
            mode = target.get("schedule_mode") or "daily"
            if mode == "daily":
                # 检查今天是否已经执行过
                last_run_at = target.get("last_run_at")
                already_ran_today = False
                if last_run_at:
                    # 将 UTC 时间转换为上海时区
                    if isinstance(last_run_at, datetime):
                        # 如果已经是 datetime 对象，转换为上海时区
                        if last_run_at.tzinfo is None:
                            # 假设是 UTC
                            last_run_at_tz = pytz.UTC.localize(last_run_at).astimezone(tz)
                        else:
                            last_run_at_tz = last_run_at.astimezone(tz)
                        # 检查是否是今天
                        if last_run_at_tz.date() == today:
                            already_ran_today = True

                # 如果今天已经执行过，跳过
                if already_ran_today:
                    continue

                # 检查是否有执行时间已过
                times = target.get("daily_times") or ["09:00", "13:00", "18:00", "22:00"]
                for t in times:
                    try:
                        hh, mm = t.split(":")
                        scheduled_time = tz.localize(datetime.combine(
                            today, datetime.min.time().replace(hour=int(hh), minute=int(mm))))
                        if scheduled_time < current_time:
                            # 今天的执行时间已经过去，且今天还未执行过
                            targets_to_execute.add(str(target["_id"]))
                            break  # 只要有一个时间点过去，就执行一次
                    except Exception:
                        pass

            _add_jobs_for_target(target)

        # 立即执行错过的目标（每个目标只执行一次，异步执行避免阻塞）
        for target_id in targets_to_execute:
            logging.info("Scheduling missed daily jobs for target %s", target_id)
            _executor.submit(_execute_target_async, target_id)

        # 等待任务被调度器处理
        import time
        time.sleep(0.2)

        # 验证所有任务的下次执行时间
        all_jobs = scheduler.get_jobs()
        tz = pytz.timezone("Asia/Shanghai")
        current_time = datetime.now(tz)
        logging.info("Scheduler loaded %s targets, total %s jobs (current time: %s)",
                     len(targets), len(all_jobs), current_time)
        for job in all_jobs:
            if hasattr(job, "next_run_time") and job.next_run_time:
                logging.info("Job %s next run: %s (in %s)",
                             job.id, job.next_run_time,
                             job.next_run_time - current_time if job.next_run_time > current_time else "PAST")
            else:
                logging.warning("Job %s has no next_run_time", job.id)


def trigger_target(target_id: str):
    """触发目标爬取（异步执行，不阻塞）"""
    _executor.submit(_execute_target_async, target_id)


def _execute_target_async(target_id: str):
    """异步执行目标爬取任务"""
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
            logging.info("Starting crawl for target %s", target_id)
            run_crawl(target, account)
            get_db()["targets"].update_one({"_id": target["_id"]}, {"$set": {"last_run_at": datetime.utcnow()}})
            logging.info("Completed crawl for target %s", target_id)
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
        try:
            scheduler.add_job(
                trigger_target,
                id=job["id"],
                trigger=job["trigger"],
                args=[target_id],
                replace_existing=True,
                max_instances=1,
                misfire_grace_time=300,
            )
        except Exception as exc:
            logging.error("Failed to add job %s: %s", job["id"], exc)
            continue


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
