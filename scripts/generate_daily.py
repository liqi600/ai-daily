#!/usr/bin/env python3
"""
AI Daily Hot Projects
每日搜索 AI 项目 → 生成 reports/YYYY-MM-DD.md → 更新 README.md 索引
"""

import json, os, re, urllib.request, urllib.error
from datetime import datetime, timezone, timedelta

# ─── Config ─────────────────────────────────────────────────────

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TZ_CN = timezone(timedelta(hours=8))
TODAY = datetime.now(TZ_CN).strftime("%Y-%m-%d")
TODAY_CN = datetime.now(TZ_CN).strftime("%Y年%m月%d日")
WEEKDAY = ["一", "二", "三", "四", "五", "六", "日"][datetime.now(TZ_CN).weekday()]
REPORTS_DIR = os.path.join(REPO_DIR, "reports")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

YESTERDAY = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
DAYS3 = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%d")
DAYS7 = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")

QUERIES = [
    ("🤖 AI Agent", f"topic:ai-agent+pushed:>{DAYS3}", 8),
    ("🧩 Agent Skills", f"agent-skills+OR+claude-skills+pushed:>{DAYS7}", 6),
    ("🔌 MCP 生态", f"topic:mcp+pushed:>{DAYS3}", 6),
    ("📚 LLM 大模型", f"topic:llm+pushed:>{DAYS3}", 6),
    ("🛡️ AI 安全", f"ai+cybersecurity+pushed:>{DAYS7}", 4),
    ("⚡ 今日新星", f"ai+pushed:>{YESTERDAY}+stars:>30", 6),
]

LANG = {"Python":"🐍","TypeScript":"📘","JavaScript":"📒","Rust":"🦀","Go":"🔷","Java":"☕","C++":"⚡","C#":"🎯","C":"🔧","HTML":"🌐","CSS":"🎨","Jupyter Notebook":"📓","Swift":"🍎","Kotlin":"💜","Ruby":"💎","Shell":"🐚","Vue":"💚","Dart":"🎯"}


# ─── GitHub API ─────────────────────────────────────────────────

def api(path):
    url = f"https://api.github.com/{path}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "ai-daily-bot/1.0")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  ⚠️ {e}")
        return {"items": []}


def load_yesterday_stars():
    yesterday = (datetime.now(TZ_CN) - timedelta(days=1)).strftime("%Y-%m-%d")
    path = os.path.join(REPORTS_DIR, f"{yesterday}.md")
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        text = f.read()
    m = {}
    for match in re.finditer(r"### \d+\. \[([\w./_-]+)\].*?\n.*?\*\*([\d,]+) Stars\*\*", text):
        m[match.group(1).lower()] = int(match.group(2).replace(",", ""))
    return m


def search_all():
    yesterday = load_yesterday_stars()
    seen = set()
    all_p = []
    for label, q, n in QUERIES:
        print(f"🔍 {label} ...", end=" ")
        r = api(f"search/repositories?q={q}&sort=stars&order=desc&per_page={n}")
        cnt = 0
        for item in r.get("items", []):
            key = item["full_name"].lower()
            if key in seen: continue
            seen.add(key)
            s = item["stargazers_count"]
            prev = yesterday.get(key)
            delta = s - prev if prev else None
            all_p.append({
                "name": item["full_name"], "url": item["html_url"],
                "desc": (item.get("description") or "").strip()[:200],
                "stars": s, "delta": delta,
                "lang": item.get("language") or "N/A",
                "topics": item.get("topics", [])[:4],
                "cat": label, "created": item["created_at"][:10],
            })
            cnt += 1
        print(f"{cnt}")
    # sort: known-delta first, then by delta+stars
    all_p.sort(key=lambda p: (p["delta"] is not None and p["delta"] > 0, p["delta"] or 0, p["stars"]), reverse=True)
    return all_p


# ─── Report ─────────────────────────────────────────────────────

def build_report(projects):
    n = min(len(projects), 20)
    projects = projects[:n]
    g = sum(1 for p in projects if p["delta"] and p["delta"] > 0)
    ts = sum(p["stars"] for p in projects)

    out = []
    out.append(f"# 🔥 {TODAY} AI 项目 Star 增长榜\n")
    out.append(f"> 📅 {TODAY_CN} 星期{WEEKDAY} · 上榜 {n} 个 · {g} 个持续增长 · 累计 ⭐{ts:,}\n")
    out.append("---\n\n")

    # Summary table
    out.append("## 📊 今日榜单\n\n")
    out.append("| # | 项目 | ⭐ Stars | 增长 | 分类 |\n")
    out.append("|---|------|---------|------|------|\n")
    for i, p in enumerate(projects, 1):
        d = f"+{p['delta']}" if p['delta'] and p['delta'] > 0 else ("持平" if p['delta'] == 0 else "🆕 新上榜")
        out.append(f"| {i} | [{p['name']}]({p['url']}) | {p['stars']:,} | {d} | {p['cat']} |\n")
    out.append("\n---\n\n")

    # Detail
    for i, p in enumerate(projects, 1):
        out.append(f"## {i}. [{p['name']}]({p['url']})\n\n")

        d = ""
        if p["delta"] and p["delta"] > 0:
            d = f"📈 **+{p['delta']}** 今日新增 · "
        elif p["delta"] == 0:
            d = "📊 保持稳定 · "
        else:
            d = "🆕 新上榜 · "

        le = LANG.get(p["lang"], "📦")
        out.append(f"⭐ **{p['stars']:,}** · {d}{le} {p['lang']} · 创建 {p['created']}\n\n")

        if p["desc"]:
            out.append(f"> {p['desc']}\n\n")

        # highlights
        hl = []
        if p["delta"] and p["delta"] > 1000: hl.append("🔥 暴增 1000+ Stars，今日最热")
        elif p["delta"] and p["delta"] > 200: hl.append(f"📈 今日 +{p['delta']} Stars，增长强劲")
        elif p["delta"] and p["delta"] > 0: hl.append("📊 持续攀升")
        elif p["delta"] == 0: hl.append("🛡️ 高星稳定项目")
        else: hl.append("🚀 首次上榜，关注度上升")

        if p["stars"] > 100000: hl.insert(0, "💎 10万+ Stars 现象级项目")
        elif p["stars"] > 10000: hl.insert(0, "🌟 万星项目，领域标杆")

        out.append(f"**亮点**: {' · '.join(hl[:4])}\n\n")
        if p["topics"]:
            out.append(f"🏷️ {' · '.join(f'`{t}`' for t in p['topics'])}\n\n")
        out.append("---\n\n")

    out.append(f"\n> 🤖 由 [AI Daily Bot](https://github.com/liqi600/ai-daily) 自动生成\n")
    out.append(f"> ⭐ 觉得有用？[给项目 Star](https://github.com/liqi600/ai-daily) 支持每日更新！\n")
    return "".join(out)


def update_readme(projects):
    """Update README.md: add today's link to index + update top-5 summary."""
    path = os.path.join(REPO_DIR, "README.md")
    if not os.path.exists(path):
        return
    with open(path) as f:
        content = f.read()

    top5 = projects[:5]
    medals = ["🥇","🥈","🥉","4","5"]
    rows = []
    for i, p in enumerate(top5):
        d = f"+{p['delta']}" if p['delta'] and p['delta'] > 0 else "新上榜"
        rows.append(f"| {medals[i]} | [{p['name']}]({p['url']}) | {p['stars']:,} | 📈 {d} | {p['cat']} |")
    table = "\n".join(rows)

    today_block = (
        f"## 🌟 今日 ({TODAY})\n\n"
        f"| # | 项目 | Stars | 增长 | 分类 |\n"
        f"|---|------|-------|------|------|\n"
        f"{table}\n"
    )

    # Replace today block
    pat = re.compile(r"## 🌟 今日.*?\n\n(\|.*\n)*", re.DOTALL)
    if pat.search(content):
        content = pat.sub(today_block + "\n", content)
    else:
        content = content.replace("## 📅 历史日报", f"{today_block}\n## 📅 历史日报")

    # Update daily index: add link if not exists
    report_link = f"- [{TODAY_CN} 星期{WEEKDAY}](reports/{TODAY}.md)"
    if report_link not in content:
        # insert after "## 📅 历史日报"
        idx = content.find("## 📅 历史日报")
        if idx != -1:
            nl = content.index("\n", idx) + 1
            content = content[:nl] + f"\n{report_link}" + content[nl:]

    with open(path, "w") as f:
        f.write(content)


# ─── Main ───────────────────────────────────────────────────────

def main():
    print(f"\n🚀 AI Daily · {TODAY_CN} 星期{WEEKDAY}\n")
    ps = search_all()
    if not ps:
        print("⚠️ 未找到项目"); return

    g = sum(1 for p in ps if p["delta"] and p["delta"] > 0)
    print(f"\n✅ {len(ps)} 个上榜 · 📈 {g} 个持续增长\n")

    os.makedirs(REPORTS_DIR, exist_ok=True)
    rp = os.path.join(REPORTS_DIR, f"{TODAY}.md")
    with open(rp, "w") as f:
        f.write(build_report(ps))
    print(f"📝 {rp}")

    update_readme(ps)
    print(f"📋 README.md (索引已更新)")

    print(f"\n🎉 完成！→ https://github.com/liqi600/ai-daily\n")


if __name__ == "__main__":
    main()
