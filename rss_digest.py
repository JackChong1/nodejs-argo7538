"""rss_digest.py — fetch RSS → AI summarize → markdown digest."""
import feedparser, os, json, httpx, sys
from datetime import datetime

# ── RSS 源（按需增删，建议 5-10 个）──
SOURCES = [
    "https://hnrss.org/frontpage?count=10",
    "https://feeds.feedburner.com/TheLindegaard",
    "https://www.morningstar.com/feed/global-market",
    # "https://your-other-feed.xml",
]
MAX_PER_FEED = 5
MODEL = os.getenv("RSS_MODEL", "llama-3.3-70b-versatile")
API_KEY = os.getenv("RSS_API_KEY", os.getenv("GROQ_API_KEY", ""))
API_BASE = os.getenv("RSS_API_BASE", "https://api.groq.com/openai/v1")
OUT_FILE = "docs/index.md"

def fetch():
    items = []
    for url in SOURCES:
        try:
            d = feedparser.parse(url)
            for e in d.entries[:MAX_PER_FEED]:
                items.append({
                    "title": e.get("title", ""),
                    "link": e.get("link", ""),
                    "summary": (e.get("summary") or e.get("description") or "")[:400],
                })
        except Exception as ex:
            print(f"[warn] fetch {url}: {ex}", file=sys.stderr)
    return items

def summarize(items):
    if not items:
        return "暂无内容。"
    prompt = f"""从以下{len(items)}条精选3-5条，按Jeff(投资者/知识管理者)偏好排序：
①个股/投资/宏观 ②AI工具/知识管理 ③深度思想/长文
剔除：娱乐、纯产品发布。每项：- [标题](链接) — 推荐理由
时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}

{json.dumps(items, ensure_ascii=False, indent=2)[:6000]}"""
    try:
        r = httpx.post(
            f"{API_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.3, "max_tokens": 2048},
            timeout=60,
        )
        return r.json()["choices"][0]["message"]["content"]
    except Exception as ex:
        return f"AI 摘要失败：{ex}"

def write_output(digest):
    body = f"""# 📡 RSS 每日精选

*生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}*

---

{digest}

---
*由 rss-digest auto-generated*
"""
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w") as f:
        f.write(body)
    print(f"[ok] {OUT_FILE} written ({len(digest)} chars)")

if __name__ == "__main__":
    items = fetch()
    print(f"[ok] fetched {len(items)} articles from {len(SOURCES)} sources")
    digest = summarize(items)
    write_output(digest)
