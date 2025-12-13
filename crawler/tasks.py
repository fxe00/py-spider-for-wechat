import logging
from datetime import datetime
from typing import Dict, Optional

from backend.db import get_db
from backend.config import get_settings
from utils.getFakId import get_fakid
from utils.getAllUrls import getAllUrl

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"


def run_crawl(target: Dict, account: Optional[Dict], page_num: int = 3):
    """
    结合现有 utils 实现的简易爬取：
    1) 优先使用缓存的 fakeid，如果没有或失效则查询并保存
    2) 用 getAllUrl 拉取最近 page_num 页（每页5篇）基础信息
    3) 去重写入 Mongo articles
    TODO: 若需正文，可对 links 再调用内容抓取模块。
    """
    if not account:
        logging.warning("No account bound for target=%s", target.get("name"))
        return
    token = (account.get("token") or "").strip()
    cookie = (account.get("cookie") or "").strip()
    mp_name = target.get("name") or ""
    if not token or not cookie or not mp_name:
        _set_last_error(target, "token/cookie/name 缺失")
        logging.warning("Missing token/cookie/name for target=%s", target.get("_id"))
        return

    headers = _build_headers(cookie)
    settings = get_settings()

    # 1. 获取或查询 fakeid（优先使用缓存的）
    fakeid = target.get("fakeid")
    mp_avatar = target.get("mp_avatar")
    need_refresh_fakeid = False
    need_refresh_avatar = False
    search_results = None  # 用于保存查询结果，以便后续保存头像

    if not fakeid:
        # 如果没有缓存的 fakeid，查询并保存
        logging.info("No cached fakeid for target=%s, querying...", mp_name)
        search_results = get_fakid(headers, token, mp_name)
        if not search_results:
            _set_last_error(target, "未找到 fakeid，可能 token/cookie 失效")
            logging.warning("No fakeid found for mp=%s", mp_name)
            return
        fakeid = search_results[0]["wpub_fakid"]
        need_refresh_fakeid = True
    else:
        logging.info("Using cached fakeid for target=%s", mp_name)
        # 如果 fakeid 已缓存但头像为空，尝试获取头像
        if not mp_avatar:
            logging.info("No cached avatar for target=%s, querying avatar...", mp_name)
            search_results = get_fakid(headers, token, mp_name)
            if search_results:
                need_refresh_avatar = True

    # 记录开始日志
    _append_log(target, status="start", message="开始爬取")

    # 2. 拉取文章列表
    titles, links, update_times = getAllUrl(
        page_num=page_num,
        start_page=0,
        fad=fakeid,
        tok=token,
        headers=headers,
        delay_range=(settings.request_min_delay, settings.request_max_delay),
        retries=settings.request_retries,
        timeout=settings.request_timeout,
    )

    # 如果使用缓存的 fakeid 但返回空结果，可能是 fakeid 失效，清除缓存并重新查询
    if not need_refresh_fakeid and (not titles or len(titles) == 0):
        logging.warning("Cached fakeid returned empty results for target=%s, clearing and retrying...", mp_name)
        _clear_fakeid(target)
        # 重新查询 fakeid
        search_results = get_fakid(headers, token, mp_name)
        if not search_results:
            _set_last_error(target, "fakeid 失效，重新查询失败")
            logging.error("Failed to refresh fakeid for mp=%s", mp_name)
            return
        fakeid = search_results[0]["wpub_fakid"]
        need_refresh_fakeid = True
        # 重试爬取
        titles, links, update_times = getAllUrl(
            page_num=page_num,
            start_page=0,
            fad=fakeid,
            tok=token,
            headers=headers,
            delay_range=(settings.request_min_delay, settings.request_max_delay),
            retries=settings.request_retries,
            timeout=settings.request_timeout,
        )
        # 如果重试后仍然为空，记录错误
        if not titles or len(titles) == 0:
            _set_last_error(target, "重新查询 fakeid 后仍无法获取文章")
            logging.warning("Still got empty results after refreshing fakeid for mp=%s", mp_name)
            return

    # 如果获取到新的 fakeid 或头像，保存到 targets 表
    if (need_refresh_fakeid or need_refresh_avatar) and search_results:
        update_data = {}
        if need_refresh_fakeid:
            update_data["fakeid"] = fakeid
        # 如果获取到头像，也保存
        if "wpub_avatar" in search_results[0] and search_results[0]["wpub_avatar"]:
            update_data["mp_avatar"] = search_results[0]["wpub_avatar"]

        if update_data:
            try:
                get_db()["targets"].update_one(
                    {"_id": target["_id"]},
                    {"$set": update_data}
                )
                if need_refresh_fakeid:
                    logging.info("Saved fakeid and avatar for target=%s", target.get("name"))
                else:
                    logging.info("Saved avatar for target=%s", target.get("name"))
            except Exception:
                logging.exception("Failed to save fakeid/avatar for target=%s", target.get("_id"))

    articles = []
    for title, link, ts in zip(titles, links, update_times):
        publish_at = datetime.utcfromtimestamp(int(ts))
        articles.append(
            {
                "mp_name": mp_name,
                "mp_id": target.get("biz"),
                "title": title,
                "url": link,
                "publish_at": publish_at,
                "cover": "",
                "digest": "",
                "target_id": target["_id"],
                "created_at": datetime.utcnow(),
            }
        )

    # 3. 去重写入
    col = get_db()["articles"]
    inserted = 0
    for art in articles:
        result = col.update_one({"url": art["url"]}, {"$setOnInsert": art}, upsert=True)
        if result.upserted_id:
            inserted += 1
    _set_last_error(target, None)
    _append_log(target, status="finish", message=f"完成，获取 {len(articles)} 篇，新入库 {inserted}")
    logging.info("Crawled mp=%s got=%s new=%s", mp_name, len(articles), inserted)


def _build_headers(cookie: str):
    return {
        "cookie": cookie,
        "user-agent": USER_AGENT,
        "referer": "https://mp.weixin.qq.com/",
        "accept": "application/json,text/javascript,*/*;q=0.01",
    }


def _set_last_error(target: Dict, message: Optional[str]):
    try:
        get_db()["targets"].update_one({"_id": target["_id"]}, {"$set": {"last_error": message}})
    except Exception:
        logging.exception("Failed to update last_error for target=%s", target.get("_id"))


def _clear_fakeid(target: Dict):
    """清除缓存的 fakeid"""
    try:
        get_db()["targets"].update_one(
            {"_id": target["_id"]},
            {"$unset": {"fakeid": ""}}
        )
        logging.info("Cleared cached fakeid for target=%s", target.get("name"))
    except Exception:
        logging.exception("Failed to clear fakeid for target=%s", target.get("_id"))


def _append_log(target: Dict, status: str, message: str):
    try:
        get_db()["crawl_logs"].insert_one(
            {
                "target_id": target.get("_id"),
                "target_name": target.get("name"),
                "status": status,
                "message": message,
                "created_at": datetime.utcnow(),
            }
        )
    except Exception:
        logging.exception("Failed to append crawl log for target=%s", target.get("_id"))
