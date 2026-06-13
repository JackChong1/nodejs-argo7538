# rss-digest

RSS 精选摘要 — 每天 2 次自动生成，GitHub Pages 展示。

**依赖：** GitHub Actions (cron) + Groq API (免费)

## 使用

1. **生成 Groq API Key** → https://console.groq.com/keys
2. 仓库 Settings → Secrets and variables → Actions → 添加 `RSS_API_KEY`
3. 仓库 Settings → Pages → Source: `docs/` → Save
4. Actions → RSS Digest → Run workflow（手动测试）
5. 之后每天 06:00 / 18:00 UTC 自动运行

## 自定义

- 编辑 `rss_digest.py` 中的 `SOURCES` 列表增删 RSS 源
- 编辑 `.github/workflows/rss.yml` 或 `cron` 表达式调整频率
- 修改 `MODEL` 环境变量切换模型（`gemini-2.0-flash-001` / `qwen-2.5-72b` 等）
