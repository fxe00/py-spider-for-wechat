import json
import logging
import re
import time
import os
from typing import Tuple, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)


def login_and_fetch(account: str, password: str, wait_seconds: int = 8) -> Tuple[str, str]:
    """
    使用 Selenium 登录微信公众平台，返回 (token, cookie_string)
    """
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")
    driver_path = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=Service(driver_path), options=options)
    try:
        logger.info("auto_login: open mp.weixin.qq.com (headless)")
        driver.get("https://mp.weixin.qq.com")
        wait = WebDriverWait(driver, 20)

        # 某些情况下默认是扫码界面，需要切换到“账号密码登录”
        try:
            switch_btn = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//a[contains(text(),'帐号密码登录') or contains(text(),'账号密码登录') or contains(text(),'使用账号登录')]",
                    )
                )
            )
            driver.execute_script("arguments[0].click();", switch_btn)
            logger.info("auto_login: switched to password login")
            time.sleep(0.5)
        except Exception:
            logger.info("auto_login: password-login switch not found (maybe already in form)")

        try:
            account_input = wait.until(EC.visibility_of_element_located((By.NAME, "account")))
            pwd_input = wait.until(EC.visibility_of_element_located((By.NAME, "password")))
            logger.info("auto_login: inputs located and visible")
        except Exception as exc:
            logger.error("auto_login: account/password input not present. url=%s", driver.current_url)
            raise RuntimeError(f"未找到账号/密码输入框: {exc}")

        try:
            driver.execute_script(
                """
                const el = arguments[0];
                el.removeAttribute('readonly');
                el.style.display='block';
                el.style.visibility='visible';
                el.value = arguments[1];
                el.dispatchEvent(new Event('input', {bubbles:true}));
                el.dispatchEvent(new Event('change', {bubbles:true}));
                """,
                account_input,
                account,
            )
            logger.info("auto_login: account filled via JS (no click)")
        except Exception as exc:
            logger.error("auto_login: account input not interactable. url=%s", driver.current_url)
            raise RuntimeError(f"账号输入框不可用: {exc}")

        try:
            driver.execute_script(
                """
                const el = arguments[0];
                el.removeAttribute('readonly');
                el.style.display='block';
                el.style.visibility='visible';
                el.value = arguments[1];
                el.dispatchEvent(new Event('input', {bubbles:true}));
                el.dispatchEvent(new Event('change', {bubbles:true}));
                """,
                pwd_input,
                password,
            )
            logger.info("auto_login: password filled via JS (no click)")
        except Exception as exc:
            logger.error("auto_login: password input not interactable. url=%s", driver.current_url)
            raise RuntimeError(f"密码输入框不可用: {exc}")

        try:
            login_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btn_login")))
            driver.execute_script("arguments[0].click();", login_btn)
            logger.info("auto_login: login button clicked (js)")
        except Exception as exc:
            logger.error("auto_login: login button not clickable. url=%s", driver.current_url)
            raise RuntimeError(f"未找到登录按钮: {exc}")

        time.sleep(wait_seconds)

        cookie_list = driver.get_cookies()
        cookie_string = "; ".join([f"{c['name']}={c['value']}" for c in cookie_list])

        current_url = driver.current_url
        token = ""
        if "token=" in current_url:
            m = re.search(r"token=(\d+)", current_url)
            if m:
                token = m.group(1)
        if not token:
            # 兜底：从首页链接解析
            page_source = driver.page_source
            m = re.search(r"token=(\d+)", page_source)
            if m:
                token = m.group(1)
        if not token:
            logger.error("auto_login: token not found. url=%s", current_url)
            raise RuntimeError("未能提取 token")
        return token, cookie_string
    finally:
        try:
            driver.quit()
        except Exception:
            logging.exception("quit chrome failed")
