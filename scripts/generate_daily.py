#!/usr/bin/env python3
"""
AI Daily Hot Projects
每日搜索 AI 项目 → 生成 reports/YYYY-MM-DD.md → 更新 README.md 索引
"""

import json, os, re, urllib.request, urllib.error, html
from datetime import datetime, timezone, timedelta

# ─── Config ─────────────────────────────────────────────────────

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TZ_CN = timezone(timedelta(hours=8))
TODAY = datetime.now(TZ_CN).strftime("%Y-%m-%d")
TODAY_CN = datetime.now(TZ_CN).strftime("%Y年%m月%d日")
WEEKDAY = ["一", "二", "三", "四", "五", "六", "日"][datetime.now(TZ_CN).weekday()]
REPORTS_DIR = os.path.join(REPO_DIR, "reports")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

# Time windows
DAY3 = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%d")
DAY7 = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
DAY14 = (datetime.now(timezone.utc) - timedelta(days=14)).strftime("%Y-%m-%d")

# High-quality queries: stars:>200 ensures projects are not garbage
QUERIES = [
    ("🤖 AI Agent", f"topic:ai-agent+stars:>200+pushed:>{DAY3}", 10),
    ("🧩 Agent Skills", f"agent-skills+OR+claude-skills+stars:>100+pushed:>{DAY7}", 8),
    ("🔌 MCP 生态", f"topic:mcp+stars:>100+pushed:>{DAY7}", 8),
    ("📚 LLM 大模型", f"topic:llm+stars:>200+pushed:>{DAY7}", 8),
    ("🛡️ AI 安全", f"ai+security+OR+pentest+stars:>50+pushed:>{DAY14}", 6),
]

LANG = {"Python":"🐍","TypeScript":"📘","JavaScript":"📒","Rust":"🦀","Go":"🔷","Java":"☕","C++":"⚡","C#":"🎯","C":"🔧","HTML":"🌐","CSS":"🎨","Jupyter Notebook":"📓","Swift":"🍎","Kotlin":"💜","Ruby":"💎","Shell":"🐚","Vue":"💚","Dart":"🎯"}

# ─── Chinese Description Generator ──────────────────────────────

def cn_desc(p):
    """Generate Chinese description from project metadata."""
    desc = p["desc"].lower()
    topics = " ".join(p["topics"]).lower()
    name = p["name"].lower()
    cat = p["cat"]

    # Agent frameworks
    if "agent harness" in desc or "agent framework" in desc:
        return f"AI Agent 开发框架，为编码助手提供 Skills、记忆、安全等增强能力，兼容 Claude Code/Codex/Cursor 等主流工具"
    if "ai agent" in desc or "ai-agent" in topics:
        if "coding" in desc:
            return f"AI 编码 Agent，让 AI 在终端中自主编程，支持多模型后端，大幅提升开发效率"
        if "browser" in desc or "web" in desc:
            return f"AI 浏览器操控 Agent，让 AI 像人一样浏览网页、点击操作，实现自动化测试和数据采集"
        if "computer" in desc or "desktop" in desc:
            return f"计算机操控 Agent，让 AI 接管桌面操作，自动完成复杂任务"
        if "search" in desc or "internet" in desc:
            return f"AI 搜索 Agent，让 AI 自主检索互联网信息，获取实时数据"
        return f"AI 智能体框架，可自主执行任务、使用工具，让 AI 真正成为你的数字助手"

    # Skills
    if "skill" in desc or "skill" in topics or "skills" in name:
        if "claude" in desc or "codex" in desc:
            return f"Agent Skills 集合，为 Claude Code/Codex 等工具提供扩展技能包，让 AI 编码能力成倍提升"
        return f"AI Agent 技能库，提供可复用的 Agent 能力模块，快速扩展 AI 工作流"

    # MCP
    if "mcp" in desc or "mcp" in topics:
        if "server" in desc:
            return f"MCP 服务端实现，为 AI Agent 提供标准化工具接入能力，让 LLM 与外部系统无缝交互"
        if "chrome" in desc or "browser" in desc or "devtools" in desc:
            return f"浏览器 MCP 工具，让 AI Agent 直接操控 Chrome 进行调试、测试和自动化操作"
        return f"MCP 生态项目，扩展 AI Agent 的能力边界，让 LLM 连接更多工具和数据源"

    # LLM / Models
    if "llm" in desc or "large language" in desc:
        if "inference" in desc or "serving" in desc:
            return f"LLM 推理优化框架，提升大模型运行效率，降低部署成本"
        if "train" in desc or "fine-tune" in desc:
            return f"LLM 训练/微调工具，让开发者高效定制大语言模型"
        return f"大语言模型相关项目，推动 LLM 技术发展和应用落地"

    if "model" in desc or "deepseek" in topics or "qwen" in topics:
        return f"AI 模型相关项目，涉及大模型推理、部署和应用，为 AI 应用提供核心动力"

    # Memory
    if "memory" in desc or "context" in desc or "mem" in name:
        return f"AI 记忆系统，解决 Agent 会话间遗忘问题，让 AI 拥有持久化记忆，跨会话保持上下文连贯"

    # Security
    if "security" in desc or "pentest" in desc or "vulnerability" in desc:
        return f"AI 安全工具，用 AI 技术进行自动化渗透测试和漏洞挖掘，提升应用安全性"

    # Automation / Workflow
    if "automation" in desc or "workflow" in desc or "orchestrat" in desc:
        return f"AI 自动化工作流平台，可视化编排 AI Agent，构建端到端的智能自动化流程"

    # App builder / vibe coding
    if "app builder" in desc or "vibe" in desc or "build" in desc:
        return f"AI 应用构建器，通过自然语言描述即可生成完整应用，让非开发者也能创造软件"

    # Generic fallbacks based on category
    if "AI Agent" in cat:
        return f"AI Agent 项目，让 AI 智能体自主完成复杂任务，是当前最热门的 AI 应用方向"
    if "Skills" in cat:
        return f"Agent Skills 项目，为 AI 编码助手提供技能扩展，增强 AI 的实战能力"
    if "MCP" in cat:
        return f"MCP 生态项目，遵循 Model Context Protocol 标准，连接 AI 与现实世界"
    if "LLM" in cat:
        return f"LLM 大模型项目，涉及大语言模型的最新进展和应用实践"
    if "安全" in cat:
        return f"AI 安全项目，用人工智能技术守护数字世界的安全防线"

    # Absolute fallback
    return f"AI 开源项目，在 {cat} 领域受到广泛关注，Star 增长迅速"


def cn_pros(p):
    """Generate detailed Chinese advantages."""
    pros = []
    v = p["velocity"]
    s = p["stars"]
    desc = (p["desc"] + " " + " ".join(p["topics"])).lower()

    # Star velocity highlights
    if v > 5000:
        pros.append(f"🔥 现象级爆发：日均增长 {v:.0f} Stars，全网瞩目")
    elif v > 1000:
        pros.append(f"🔥 飞速增长：日均 {v:.0f} Stars，已成为热门趋势")
    elif v > 200:
        pros.append(f"📈 快速增长：日均 {v:.0f} Stars，势头强劲")
    elif v > 50:
        pros.append(f"🚀 稳定上升：日均 {v:.0f} Stars，持续受到关注")
    elif v > 10:
        pros.append(f"📊 稳步增长：日均 {v:.0f} Stars，口碑发酵中")
    else:
        pros.append(f"💡 新晋项目：刚刚起步，潜力可期")

    # Feature-based pros
    if "open-source" in desc or "open source" in desc:
        pros.append("完全开源免费，社区驱动开发，代码透明可审计")

    if "local" in desc or "offline" in desc or "self-host" in desc:
        pros.append("支持本地部署/离线运行，数据不出设备，隐私安全有保障")

    if "cross-platform" in desc or "mac" in desc:
        pros.append("跨平台兼容，macOS/Linux/Windows 全覆盖")

    if "api" in desc:
        pros.append("提供标准 API 接口，易于集成到现有系统和工作流中")

    if "docker" in desc or "container" in desc:
        pros.append("支持 Docker 容器化部署，一键启动，运维成本低")

    if "plugin" in desc or "extension" in desc or "modular" in desc:
        pros.append("插件化/模块化架构，灵活可扩展，按需装配功能")

    if "claude" in desc or "anthropic" in desc:
        pros.append("与 Claude/Anthropic 生态深度集成，开箱即用")
    if "gpt" in desc or "openai" in desc or "chatgpt" in desc:
        pros.append("兼容 OpenAI/GPT 生态，多模型自由切换")
    if "codex" in desc or "copilot" in desc or "cursor" in desc:
        pros.append("支持 Codex/Copilot/Cursor 等主流编码工具，覆盖面广")

    if "lightweight" in desc or "fast" in desc or "perform" in desc:
        pros.append("轻量级高性能设计，启动快、占用低、响应迅速")
    if "rust" in desc:
        pros.append("采用 Rust 开发，内存安全、性能卓越")
    if "python" in desc:
        pros.append("Python 生态友好，学习成本低，社区资源丰富")

    # Fill to at least 5 pros
    generic_pros = [
        f"社区活跃度高，Star 增长速度在同类项目中名列前茅",
        f"代码质量优秀，文档完善，适合学习和二次开发",
        f"与 AI Agent 生态紧密相连，是当前技术趋势的代表项目",
        f"开发者体验极佳，配置简单，上手快",
        f"适合企业和个人使用，应用场景广泛",
    ]
    for gp in generic_pros:
        if len(pros) < 6:
            pros.append(gp)

    return pros[:7]


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


def daily_velocity(item):
    """Calculate stars per day since creation. Higher = faster growing."""
    try:
        created = datetime.strptime(item["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        days = (datetime.now(timezone.utc) - created).total_seconds() / 86400
        if days < 0.5:
            days = 0.5  # floor to avoid inflated rates for brand-new repos
        return item["stargazers_count"] / days
    except:
        return 0


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
            velocity = daily_velocity(item)
            all_p.append({
                "name": item["full_name"], "url": item["html_url"],
                "desc": (item.get("description") or "").strip()[:200],
                "stars": s, "delta": delta,
                "lang": item.get("language") or "N/A",
                "topics": item.get("topics", [])[:4],
                "cat": label, "created": item["created_at"][:10],
                "velocity": velocity,  # stars per day
            })
            cnt += 1
        print(f"{cnt}")
    # Sort by daily velocity (stars per day) — fastest growing first
    all_p.sort(key=lambda p: p["velocity"], reverse=True)
    return all_p


# ─── Report ─────────────────────────────────────────────────────

def build_report(projects):
    n = min(len(projects), 20)
    projects = projects[:n]

    out = []
    out.append(f"# 🔥 {TODAY} AI 新项目 Star 增长榜\n")
    out.append(f"> 📅 {TODAY_CN} 星期{WEEKDAY} · 上榜 {n} 个项目 · 按日均 Star 增长排序\n")
    out.append("---\n\n")

    # Summary table
    out.append("## 📊 今日榜单\n\n")
    out.append("| # | 项目 | ⭐ Stars | 🚀 日均增长 | 创建 | 分类 |\n")
    out.append("|---|------|---------|------------|------|------|\n")
    for i, p in enumerate(projects, 1):
        v = f"{p['velocity']:.0f}/天" if p['velocity'] > 0 else "-"
        out.append(f"| {i} | [{p['name']}]({p['url']}) | {p['stars']:,} | {v} | {p['created']} | {p['cat']} |\n")
    out.append("\n---\n\n")

    # Detail
    for i, p in enumerate(projects, 1):
        out.append(f"## {i}. [{p['name']}]({p['url']})\n\n")

        le = LANG.get(p["lang"], "📦")
        out.append(f"⭐ **{p['stars']:,}** · 🚀 **{p['velocity']:.0f} Stars/天** · {le} {p['lang']} · 📅 创建 {p['created']}\n\n")

        # Chinese description
        cnd = cn_desc(p)
        out.append(f"> {cnd}\n\n")

        # Original English desc as reference
        if p["desc"]:
            out.append(f"<details><summary>📝 原项目描述</summary>\n\n> {p['desc']}\n</details>\n\n")

        # Detailed pros
        pros_list = cn_pros(p)
        out.append(f"**✨ 推荐理由**:\n")
        for pro in pros_list:
            out.append(f"- {pro}\n")
        out.append("\n")

        if p["topics"]:
            out.append(f"🏷️ {' · '.join(f'`{t}`' for t in p['topics'])}\n\n")
        out.append("---\n\n")

    out.append(f"\n> 🤖 由 [AI Daily Bot](https://github.com/liqi600/ai-daily) 自动生成\n")
    out.append(f"> ⭐ 觉得有用？[给项目 Star](https://github.com/liqi600/ai-daily) 支持每日更新！\n")
    return "".join(out)


def update_readme(projects):
    """Update README.md: replace today top-5 block + maintain daily index."""
    path = os.path.join(REPO_DIR, "README.md")
    if not os.path.exists(path):
        return
    with open(path) as f:
        content = f.read()

    top5 = projects[:5]
    medals = ["🥇","🥈","🥉","4","5"]
    rows = []
    for i, p in enumerate(top5):
        v = f"🚀 {p['velocity']:.0f}/天" if p['velocity'] > 0 else "新上榜"
        rows.append(f"| {medals[i]} | [{p['name']}]({p['url']}) | {p['stars']:,} | {v} | {p['cat']} |")
    table = "\n".join(rows)

    today_block = (
        f"## 🌟 [今日 ({TODAY})](reports/{TODAY}.md)\n\n"
        f"| # | 项目 | Stars | 日均增长 | 分类 |\n"
        f"|---|------|-------|----------|------|\n"
        f"{table}\n"
    )

    # Replace today block — heading has [今日 (date)](link) format
    pat = re.compile(r"## 🌟 \[今日.*?\n\n(\|.*\n)*", re.DOTALL)
    if pat.search(content):
        content = pat.sub(today_block + "\n", content)
    else:
        # Initial README: insert after first --- divider
        idx = content.find("\n---\n")
        if idx != -1:
            end = content.index("\n", idx + 5) + 1
            content = content[:end] + "\n" + today_block + "\n" + content[end:]

    # Maintain daily index: add today's link if missing
    report_link = f"- [{TODAY_CN} 星期{WEEKDAY}](reports/{TODAY}.md)"
    if report_link not in content:
        idx = content.find("## 📅 历史日报")
        if idx == -1:
            # No index section yet — append after today block
            content = content.rstrip() + "\n\n---\n\n## 📅 历史日报\n\n" + report_link + "\n"
        else:
            nl = content.index("\n", idx) + 1
            content = content[:nl] + f"\n{report_link}" + content[nl:]

    with open(path, "w") as f:
        f.write(content)


# ─── Main ───────────────────────────────────────────────────────

def main():
    # 幂等：同一天已有报告则跳过（兜底 cron 不会重复生成）
    report_path = os.path.join(REPORTS_DIR, f"{TODAY}.md")
    if os.path.exists(report_path):
        print(f"\n⏭️ 今日报告已存在: {report_path}，跳过生成。\n")
        return

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
