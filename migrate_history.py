"""
migrate_history.py
──────────────────
Chuyển history.json từ dạng cũ (list of URL strings)
sang dạng mới (list of {"title": ..., "url": ...}).

Các entry đã là dict thì giữ nguyên, chỉ bổ sung title
nếu title đang rỗng.

Chạy: python migrate_history.py
      python migrate_history.py --cookies cookies.txt
      python migrate_history.py --browser chrome
"""

import json
import os
import sys
from yt_dlp import YoutubeDL

HISTORY_FILE = "history.json"
COOKIES_FILE  = "cookies.txt"


def load():
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_ydl_opts(cookies_file: str | None, browser: str | None) -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        # Bypass JS-runtime requirement
        "extractor_args": {
            "youtube": {"player_client": ["ios", "web"]}
        },
    }
    if cookies_file and os.path.exists(cookies_file):
        opts["cookiefile"] = cookies_file
        print(f"🍪 Dùng cookies từ file: {cookies_file}")
    elif browser:
        opts["cookiesfrombrowser"] = (browser,)
        print(f"🍪 Dùng cookies từ trình duyệt: {browser}")
    return opts


def fetch_title(url: str, ydl_opts: dict) -> str:
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get("title") or ""
    except Exception as e:
        print(f"  ⚠ Không lấy được title: {e}")
        return ""


def main():
    # ── Parse args ──────────────────────────────────────────────────────
    import argparse
    parser = argparse.ArgumentParser(description="Migrate history.json")
    parser.add_argument("--cookies", default=None,
                        help="Đường dẫn file cookies.txt (mặc định tự tìm cookies.txt)")
    parser.add_argument("--browser", default=None,
                        help="Lấy cookies từ trình duyệt: chrome/firefox/edge/...")
    args = parser.parse_args()

    # Tự dùng cookies.txt nếu không truyền tham số và file tồn tại
    cookies_file = args.cookies
    if not cookies_file and not args.browser and os.path.exists(COOKIES_FILE):
        cookies_file = COOKIES_FILE

    ydl_opts = build_ydl_opts(cookies_file, args.browser)

    # ── Migrate ─────────────────────────────────────────────────────────
    if not os.path.exists(HISTORY_FILE):
        print("Không tìm thấy history.json")
        sys.exit(1)

    history = load()
    total = len(history)
    print(f"Tổng số entry: {total}\n")

    updated = []
    for i, entry in enumerate(history, start=1):
        if isinstance(entry, str):
            url = entry
            print(f"[{i}/{total}] Đang lấy title: {url}")
            title = fetch_title(url, ydl_opts)
            print(f"         → {title or '(không lấy được)'}")
            updated.append({"title": title, "url": url})
        elif isinstance(entry, dict):
            url   = entry.get("url", "")
            title = entry.get("title", "")
            if not title and url:
                print(f"[{i}/{total}] Bổ sung title cho: {url}")
                title = fetch_title(url, ydl_opts)
                print(f"         → {title or '(không lấy được)'}")
                entry["title"] = title
            else:
                print(f"[{i}/{total}] Đã có title: {title}")
            updated.append(entry)
        else:
            updated.append(entry)

    save(updated)
    print(f"\n✅ Xong! Đã cập nhật {total} entry vào {HISTORY_FILE}")


if __name__ == "__main__":
    main()
