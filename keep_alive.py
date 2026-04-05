#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""网站保活脚本 - GitHub Actions 专用"""

import requests
import time
import random
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

URLS = [
    "https://89mugbbs.kbcrt.fun/",
    "https://ssbbs.kbcrt.fun/",
    "https://sserbbs.000.pe/",
    "https://quizme.kbcrt.fun/",
    "https://kbcrtssf17.page.gd/notifications.php",
    "https://kbcrtssf12.page.gd/notifications.php",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
}

def visit_url(url: str, retry: int = 0) -> bool:
    try:
        logger.info(f"Visiting: {url}")
        resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        if 200 <= resp.status_code < 400:
            logger.info(f"✓ {url} | Status: {resp.status_code} | Size: {len(resp.content)}B")
            return True
        else:
            logger.warning(f"✗ {url} | Status: {resp.status_code}")
    except Exception as e:
        logger.error(f"✗ {url} | Error: {type(e).__name__}: {e}")
    
    if retry < 2:
        time.sleep(2 ** retry)
        return visit_url(url, retry + 1)
    return False

def main():
    logger.info("=== Keep-Alive Task Started ===")
    success = 0
    for i, url in enumerate(URLS, 1):
        if visit_url(url):
            success += 1
        if i < len(URLS):
            time.sleep(random.uniform(3, 8))
    logger.info(f"=== Done | Success: {success}/{len(URLS)} ===")
    return 0 if success > 0 else 1

if __name__ == "__main__":
    exit(main())
