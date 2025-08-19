import os, re, time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify

app = Flask(__name__)

BASE = "https://thptnguyenhuuhuan.hcm.edu.vn"
LIST_PATH = "/tin-tuc-su-kien/c/14105"

# headers để tránh 403
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/119.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": urljoin(BASE, LIST_PATH),
    "Connection": "keep-alive",
})

def absolute(href: str) -> str:
    return urljoin(BASE, (href or "").strip())

def clean(text: str) -> str:
    return " ".join((text or "").split())

def extract_attachments(scope):
    atts = []
    for a in scope.select(".Filedinhkem_P a"):
        atts.append({
            "text": clean(a.get_text(" ", strip=True)),
            "url": absolute(a.get("href"))
        })
    return atts

def extract_id(abs_url: str) -> str:
    m = re.search(r"/ct/\d+/(\d+)", abs_url)
    return m.group(1) if m else abs_url

def parse_big(div):
    a_title = div.select_one("h1 a")
    a_img = div.select_one("a.image_big_item")
    img = a_img.select_one("img") if a_img else None

    href = a_title.get("href") if a_title else (a_img.get("href") if a_img else "")
    abs_url = absolute(href)

    return {
        "id": extract_id(abs_url),
        "title": clean(a_title.get("title") or a_title.get_text()) if a_title else "",
        "url": abs_url,
        "date": clean(div.select_one("label.date_and_cate span").get_text()) if div.select_one("label.date_and_cate span") else "",
        "category": clean(div.select_one("label.date_and_cate a").get_text()) if div.select_one("label.date_and_cate a") else "",
        "image": img.get("src") if img else "",
        "attachments": extract_attachments(div),
    }

def parse_li(li):
    a_title = li.select_one("div.item h1 a")
    a_img = li.select_one("a.image_item_hint")
    img = a_img.select_one("img") if a_img else None

    href = a_title.get("href") if a_title else (a_img.get("href") if a_img else "")
    abs_url = absolute(href)

    return {
        "id": extract_id(abs_url),
        "title": clean(a_title.get("title") or a_title.get_text()) if a_title else "",
        "url": abs_url,
        "date": clean(li.select_one("label.date_and_cate span").get_text()) if li.select_one("label.date_and_cate span") else "",
        "category": clean(li.select_one("label.date_and_cate a").get_text()) if li.select_one("label.date_and_cate a") else "",
        "image": img.get("src") if img else "",
        "attachments": extract_attachments(li),
    }

def fetch_page(page: int):
    url = urljoin(BASE, LIST_PATH + (f"/{page}" if page > 1 else ""))
    r = session.get(url, timeout=20)
    r.raise_for_status()
    return r.text, url

def parse_page(html: str):
    soup = BeautifulSoup(html, "html.parser")
    root = soup.select_one("#ContentPlaceHolder1_ContentPlaceHolder1_UpdatePanel1")
    items = []
    if not root:
        return items
    big = root.select_one(".big_item_news")
    if big:
        items.append(parse_big(big))
    for li in root.select("ul.item_hint > li"):
        items.append(parse_li(li))
    return items

# cache nhẹ để giảm tải
_CACHE = {"ts": 0.0, "data": None}
TTL = 120  # giây

@app.get("/crawl/nhh")
def crawl_nhh():
    pages = max(1, int(request.args.get("pages", 1)))
    now = time.time()
    if pages == 1 and _CACHE["data"] and now - _CACHE["ts"] < TTL:
        return jsonify(_CACHE["data"])

    all_items, urls = [], []
    for p in range(1, pages + 1):
        html, url = fetch_page(p)
        urls.append(url)
        all_items.extend(parse_page(html))

    data = {
        "source": absolute(LIST_PATH),
        "fetched_pages": pages,
        "count": len(all_items),
        "items": all_items,
    }
    if pages == 1:
        _CACHE.update({"ts": now, "data": data})
    return jsonify(data)

@app.get("/")
def home():
    return jsonify({"ok": True, "usage": "/crawl/nhh?pages=1"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
