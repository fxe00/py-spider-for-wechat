import logging
import base64
import io
import requests
from datetime import datetime
from typing import Dict, Optional
from PIL import Image

from backend.db import get_db
from backend.config import get_settings
from utils.getFakId import get_fakid
from utils.getAllUrls import getAllUrl

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"

# 缩略图配置
THUMBNAIL_SIZE = (64, 64)  # 缩略图尺寸
THUMBNAIL_QUALITY = 75  # JPEG质量（1-100）


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

        result = search_results[0]

        # 保存其他公众号信息
        if "alias" in result:
            update_data["mp_alias"] = result["alias"]
        if "service_type" in result:
            update_data["mp_service_type"] = result["service_type"]
        if "verify_type" in result:
            update_data["mp_verify_type"] = result["verify_type"]
        if "signature" in result:
            update_data["mp_signature"] = result["signature"]
        if "user_name" in result:
            update_data["mp_user_name"] = result["user_name"]

        # 如果获取到头像URL，下载并转换为base64保存
        if "wpub_avatar" in result and result["wpub_avatar"]:
            avatar_url = result["wpub_avatar"]
            # 如果已经是base64格式（data URI），直接保存
            if avatar_url.startswith("data:image/"):
                update_data["mp_avatar"] = avatar_url
            else:
                # 下载图片并转换为base64
                logging.info("Attempting to download avatar for target=%s from URL: %s", mp_name, avatar_url)
                avatar_base64 = _download_avatar_as_base64(avatar_url, headers)
                if avatar_base64:
                    update_data["mp_avatar"] = avatar_base64
                    logging.info("Downloaded and converted avatar to base64 for target=%s (length: %d chars)",
                                 mp_name, len(avatar_base64))
                else:
                    logging.warning("Failed to download avatar for target=%s from URL: %s", mp_name, avatar_url)
        else:
            # 记录为什么没有获取到头像
            logging.warning("No avatar URL found for target=%s. Available fields: %s",
                            mp_name, list(result.keys()) if result else "N/A")
            if "_raw_data" in result:
                # 检查原始数据中是否有头像字段
                raw_data = result["_raw_data"]
                logging.debug("Raw data keys for %s: %s", mp_name, list(raw_data.keys()))
                # 尝试从原始数据中查找头像
                for key in raw_data.keys():
                    if any(x in key.lower() for x in ['img', 'avatar', 'head']):
                        logging.info("Found potential avatar field '%s' in raw data for %s", key, mp_name)

        if update_data:
            try:
                result = get_db()["targets"].update_one(
                    {"_id": target["_id"]},
                    {"$set": update_data}
                )
                if need_refresh_fakeid:
                    logging.info("Saved fakeid and avatar for target=%s (matched: %d, modified: %d)",
                                 target.get("name"), result.matched_count, result.modified_count)
                else:
                    logging.info("Saved avatar for target=%s (matched: %d, modified: %d)",
                                 target.get("name"), result.matched_count, result.modified_count)
                # 验证保存是否成功
                if "mp_avatar" in update_data:
                    saved_target = get_db()["targets"].find_one({"_id": target["_id"]}, {"mp_avatar": 1})
                    if saved_target and saved_target.get("mp_avatar"):
                        logging.info("Verified: mp_avatar saved successfully for target=%s (length: %d chars)",
                                     target.get("name"), len(saved_target.get("mp_avatar", "")))
                    else:
                        logging.error("Warning: mp_avatar not found after save for target=%s", target.get("name"))
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


def _download_avatar_as_base64(avatar_url: str, headers: Dict, thumbnail: bool = True) -> Optional[str]:
    """
    下载头像图片并转换为base64字符串（可选生成缩略图）

    Args:
        avatar_url: 头像URL
        headers: HTTP请求头（包含cookie等）
        thumbnail: 是否生成缩略图（默认True，减少流量）

    Returns:
        base64编码的图片字符串（data URI格式），失败返回None
    """
    if not avatar_url:
        return None

    try:
        # 处理相对URL
        if avatar_url.startswith("//"):
            avatar_url = "https:" + avatar_url
        elif avatar_url.startswith("/"):
            avatar_url = "https://mp.weixin.qq.com" + avatar_url

        logging.info("Downloading avatar from URL: %s", avatar_url)
        # 下载图片
        response = requests.get(avatar_url, headers=headers, timeout=10, stream=True)
        response.raise_for_status()

        # 检查Content-Type
        content_type = response.headers.get("Content-Type", "").lower()
        if not content_type.startswith("image/"):
            logging.warning("Avatar URL does not return an image: %s", avatar_url)
            return None

        # 读取图片数据
        image_data = response.content
        if len(image_data) > 2 * 1024 * 1024:  # 限制2MB
            logging.warning("Avatar image too large: %d bytes", len(image_data))
            return None

        # 如果需要生成缩略图
        if thumbnail:
            try:
                # 使用PIL处理图片
                img = Image.open(io.BytesIO(image_data))

                # 转换为RGB模式（如果是RGBA或其他模式）
                if img.mode in ("RGBA", "LA", "P"):
                    # 创建白色背景
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                # 生成缩略图（保持宽高比）
                # 兼容不同版本的PIL
                try:
                    img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                except AttributeError:
                    # 旧版本PIL使用LANCZOS常量
                    img.thumbnail(THUMBNAIL_SIZE, Image.LANCZOS)

                # 转换为字节流
                output = io.BytesIO()
                img.save(output, format="JPEG", quality=THUMBNAIL_QUALITY, optimize=True)
                image_data = output.getvalue()
                mime_type = "image/jpeg"

                logging.debug("Generated thumbnail: %d bytes (original: %d bytes)",
                              len(image_data), len(response.content))
            except Exception as img_exc:
                logging.warning("Failed to generate thumbnail, using original image: %s", img_exc)
                # 如果缩略图生成失败，使用原图
                mime_type = content_type
                if mime_type == "image/jpg":
                    mime_type = "image/jpeg"
        else:
            # 使用原图
            mime_type = content_type
            if mime_type == "image/jpg":
                mime_type = "image/jpeg"

        # 转换为base64
        base64_str = base64.b64encode(image_data).decode("utf-8")

        # 返回data URI格式
        return f"data:{mime_type};base64,{base64_str}"
    except Exception as exc:
        logging.warning("Failed to download avatar from %s: %s", avatar_url, exc)
        return None


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
