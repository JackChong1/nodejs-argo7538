"""rss_digest.py — fetch RSS → AI summarize → markdown digest."""
import feedparser, os, json, httpx, sys
from datetime import datetime

# ── RSS 源（10 个精品源，覆盖投资·科技·深度思想）──
SOURCES = [
    # 投资·经济
    "https://www.morningstar.com/feed/global-market",
    "https://aswathdamodaran.blogspot.com/feeds/posts/default",
    "https://www.calculatedriskblog.com/feeds/posts/default",

    # AI·科技
    "https://hnrss.org/frontpage?count=10",
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://www.technologyreview.com/feed/",
    "https://www.ben-evans.com/feed",

    # 深度·思想
    "https://aeon.co/feed",
    "https://www.theguardian.com/news/series/the-long-read/rss",
    "https://www.bbc.com/future/feed",
]
MAX_PER_FEED = 3           # 宁缺毋滥
SUMMARY_MAX = 200          # 缩短摘要省 token
MODEL = os.getenv("RSS_MODEL", "llama-3.3-70b-versatile")
API_KEY = os.getenv("RSS_API_KEY", os.getenv("GROQ_API_KEY", ""))
API_BASE = os.getenv("RSS_API_BASE", "https://api.groq.com/openai/v1")
OUT_FILE = "docs/index.md"

def item_score(item):
    """利用元数据排序：HN 分数优先，其余为 0"""
    try:
        return float(item.get("hnscore", 0))
    except (ValueError, TypeError):
        return 0.0

def fetch():
    items = []
    for url in SOURCES:
        try:
            d = feedparser.parse(url)
            for e in d.entries[:MAX_PER_FEED]:
                summary = (e.get("summary") or e.get("description") or "")[:SUMMARY_MAX]
                it = {
                    "title": e.get("title", ""),
                    "link": e.get("link", ""),
                    "summary": summary,
                }
                # 保留 HN 分数作排序信号
                for tag in getattr(e, "tags", []):
                    if "score" in str(tag.get("term", "")).lower():
                        it["hnscore"] = tag["term"]
                        break
                hs = e.get("hnscore") or e.get("score")
                if hs:
                    it["hnscore"] = str(hs)
                items.append(it)
        except Exception as ex:
            print(f"[warn] fetch {url}: {ex}", file=sys.stderr)
    # 按分数预排序（高分在前，AI 优先看到优质内容）
    items.sort(key=item_score, reverse=True)
    return items

def summarize(items):
    if not items:
        return "暂无内容。"
    prompt = f"""你是一位眼光挑剔的精品编辑，从以下{len(items)}条中选出最重要的3-5条。
选择标准（按优先级）：
① 有实质洞见的长文或分析
② 对投资、科技或认知有实际启发
③ 值得追踪的重要趋势或事件
剔除：纯资讯播报、娱乐内容、没有新信息的产品发布。

输出格式（每项一行）：
- [标题](链接) — 1句话推荐理由

当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}

{json.dumps(items, ensure_ascii=False, indent=2)[:8000]}"""
    try:
        r = httpx.post(
            f"{API_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.3, "max_tokens": 1024},
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
*by rss-digest*
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
