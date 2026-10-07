# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=2.0", "pyyaml"]
# ///
"""AI知识森林 MCP 服务器。

让 Claude Code、WorkBuddy 等支持 MCP 的 AI 工具能直接查询知识森林里的
提示词、Skill 和知识卡片，并把技能装到本机。

数据源策略：本机有仓库时直接读仓库（最快、永远最新），没有时回落到线上 API。

启动（供 MCP 客户端调用）：
    uv run /path/to/server.py
环境变量：
    KNOWLEDGE_FOREST_ROOT   仓库根目录，默认 ~/00_Huaya/07_AI知识森林
    KNOWLEDGE_FOREST_REMOTE 线上 API 根地址，默认见 site_url.py（build_api.py 会校验一致）
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import urllib.request
from pathlib import Path

import yaml
from mcp.server.mcpserver import MCPServer

ROOT = Path(os.environ.get("KNOWLEDGE_FOREST_ROOT", Path.home() / "00_Huaya/07_AI知识森林")).expanduser()
REMOTE = os.environ.get(
    "KNOWLEDGE_FOREST_REMOTE", "https://s393801048.github.io/ai-knowledge-forest/api"
).rstrip("/")
SITE = REMOTE.rsplit("/api", 1)[0]      # 站点根地址，取课程讲次原文时用
CARDS_SRC = Path.home() / "00_Huaya/05_不合理蛙写作/AI第二大脑/03_知识库/03_知识卡片"
LOCAL_API = ROOT / "01_网站工程" / "api"

# 复制技能时跳过的目录
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__",
             ".mypy_cache", ".pytest_cache", ".ruff_cache", ".DS_Store"}

server = MCPServer(
    name="ai-knowledge-forest",
    title="AI知识森林",
    instructions=(
        "作者收集的提示词、Skill、知识卡片、AI 产品和学习资源。"
        "查提示词用 search_prompts / get_prompt（get_prompt 返回可直接使用的原文）；"
        "查技能用 search_skills / get_skill；装技能用 install_skill；"
        "查 AI 产品用 search_products / get_product（返回产品官网）；"
        "查教程课程和别人整理的清单用 search_resources / get_resource"
        "（整门课能取到每一讲的全文）。"
    ),
)


# ── 数据读取 ────────────────────────────────────────────────────────

def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    try:
        meta = yaml.safe_load(text[3:end]) or {}
    except Exception:  # noqa: BLE001
        meta = {}
    return (meta if isinstance(meta, dict) else {}), text[end + 4:].lstrip("\n")


def code_blocks(md: str) -> list[str]:
    """正文里所有的代码块，按出现顺序。提示词是「中文译文、英文原文」两块。"""
    return [b.strip() for b in re.findall(r"```[^\n]*\n(.*?)```", md, re.S)]


def section(md: str, title: str) -> str:
    m = re.search(rf"^##\s+{re.escape(title)}\s*$(.*?)(?=^##\s+|\Z)", md, re.S | re.M)
    return m.group(1).strip() if m else ""


def categories(lib: Path) -> dict[str, int]:
    out = {}
    if not lib.is_dir():
        return out
    for d in sorted(p for p in lib.iterdir() if p.is_dir() and not p.name.startswith("_")):
        n = len([f for f in d.glob("*.md") if not f.name.startswith("_")])
        if n:
            out[re.sub(r"^\d+_", "", d.name)] = n
    return out


def _local_items(lib: Path, kind: str) -> list[dict]:
    items = []
    for d in sorted(p for p in lib.iterdir() if p.is_dir() and not p.name.startswith("_")):
        cat = re.sub(r"^\d+_", "", d.name)
        for md in sorted(d.glob("*.md")):
            if md.name.startswith("_"):
                continue
            meta, body = parse_frontmatter(md.read_text(encoding="utf-8"))
            if kind == "prompt":
                blocks = code_blocks(body)
                items.append({
                    "id": md.stem, "name": str(meta.get("名称", md.stem)),
                    "en": str(meta.get("英文名", "")), "category": cat,
                    "summary": str(meta.get("一句话介绍", "")), "tags": meta.get("标签") or [],
                    "source": str(meta.get("来源链接", "")), "origin": str(meta.get("出处", "")),
                    "prompt": blocks[0] if blocks else "",
                    "prompt_en": blocks[1] if len(blocks) > 1 else "",
                    "detail": section(body, "详细介绍"), "howto": section(body, "怎么用"),
                })
            elif kind == "skill":
                items.append({
                    "id": md.stem, "name": str(meta.get("技能名", md.stem)),
                    "display": str(meta.get("名称", "")), "category": cat,
                    "summary": str(meta.get("一句话介绍", "")), "tags": meta.get("标签") or [],
                    "source": str(meta.get("来源链接", "")), "origin": str(meta.get("出处", "")),
                    "install": str(meta.get("安装方式", "")),
                    "body_path": str(meta.get("本体位置", "")),
                })
            else:  # product / learn：字段一样
                items.append({
                    "id": md.stem, "name": str(meta.get("名称", md.stem)), "category": cat,
                    "summary": str(meta.get("一句话介绍", "")), "tags": meta.get("标签") or [],
                    "source": str(meta.get("来源链接", "")), "origin": str(meta.get("出处", "")),
                    "date": str(meta.get("收录日期", "")),
                    "body": section(body, "详细介绍"),
                })
    return items


def _fetch(name: str) -> dict:
    url = f"{REMOTE}/{name}.json"
    with urllib.request.urlopen(url, timeout=20) as r:  # noqa: S310
        return json.loads(r.read().decode("utf-8"))


def _local_courses() -> list[dict]:
    """课程条目取自本机生成的 api/learn.json（build_api.py 生成，含讲次和 Markdown 地址）。"""
    f = LOCAL_API / "learn.json"
    if not f.is_file():
        return []
    try:
        items = json.loads(f.read_text(encoding="utf-8"))["items"]
    except (OSError, ValueError, KeyError):
        return []
    return [i for i in items if i.get("course")]


CATALOGS = {
    "products": ("AI 产品", "05_AI产品库"),
    "learn": ("学习资源", "06_学习资源"),
}


def load(lib_key: str) -> tuple[list[dict], str]:
    """返回 (条目列表, 数据来源说明)。"""
    if lib_key in CATALOGS:
        label, dirname = CATALOGS[lib_key]
        local = ROOT / dirname
        if local.is_dir():
            items = _local_items(local, "catalog")
            if lib_key == "learn":
                items = items + _local_courses()      # 课程不在 06_学习资源 里，另取
            if items:
                return items, "本机仓库"
    elif lib_key == "prompts":
        local = ROOT / "03_提示词库"
        if local.is_dir():
            return _local_items(local, "prompt"), "本机仓库"
    else:
        local = ROOT / "04_Skill库"
        if local.is_dir():
            return _local_items(local, "skill"), "本机仓库"
    data = _fetch(lib_key)
    return data["items"], "线上 API"


def load_cards() -> tuple[list[dict], str]:
    if CARDS_SRC.is_dir():
        items = []
        for d in sorted(p for p in CARDS_SRC.iterdir()
                        if p.is_dir() and not p.name.startswith("_")):
            cat = re.sub(r"^\d+_", "", d.name)
            for md in sorted(d.glob("*.md")):
                if md.name.startswith("_"):
                    continue
                meta, body = parse_frontmatter(md.read_text(encoding="utf-8"))
                items.append({
                    "id": md.stem, "name": str(meta.get("theme", md.stem)), "category": cat,
                    "summary": str(meta.get("summary", "")),
                    "keywords": meta.get("keywords") or [], "body": body.strip(),
                })
        if items:
            return items, "本机"
    return _fetch("cards")["items"], "线上 API"


# ── 检索 ────────────────────────────────────────────────────────────

def _hit(item: dict, q: str) -> bool:
    if not q:
        return True
    blob = " ".join(str(item.get(k, "")) for k in
                    ("name", "en", "display", "summary", "category", "origin", "detail", "howto"))
    blob += " " + " ".join(str(t) for t in (item.get("tags") or []))
    return q.lower() in blob.lower()


def _rank(item: dict, q: str) -> int:
    """命中名称的排前面。"""
    if not q:
        return 0
    ql = q.lower()
    name = str(item.get("name", "")).lower() + str(item.get("en", "")).lower() \
        + str(item.get("display", "")).lower()
    return 0 if ql in name else 1


def search(items: list[dict], query: str, category: str, limit: int) -> list[dict]:
    rows = [i for i in items
            if (not category or i["category"] == category) and _hit(i, query)]
    rows.sort(key=lambda i: _rank(i, query))
    return rows[:limit]


def brief(item: dict, kind: str) -> dict:
    base = {"name": item.get("name", ""), "category": item["category"],
            "summary": item.get("summary", ""), "tags": item.get("tags") or []}
    if kind == "skill" and item.get("display"):
        base["display"] = item["display"]
    return base


def label(item: dict) -> str:
    """提示词的显示名：中文名（英文原名）。"""
    en = str(item.get("en", "")).strip()
    name = str(item.get("name", ""))
    return f"{name}（{en}）" if en else name


def pick_one(items: list[dict], name: str) -> dict | None:
    """按名字找一条：先精确匹配 id/name/en/display，再退回模糊匹配。"""
    q = name.strip().lower()
    for it in items:
        for k in ("id", "name", "en", "display"):
            v = str(it.get(k, "")).lower()
            if v and (v == q or v.startswith(q)):
                return it
    hits = [i for i in items if _hit(i, name)]
    return hits[0] if hits else None


# ── 工具 ────────────────────────────────────────────────────────────

@server.tool(description="知识森林总览：五个库各有多少条、分类分布、当前数据来自本机仓库还是线上 API")
def site_overview() -> str:
    lines = ["# AI知识森林", ""]
    for key, label, local_dir in (("prompts", "提示词", ROOT / "03_提示词库"),
                                  ("skills", "Skill", ROOT / "04_Skill库"),
                                  ("products", "AI 产品", ROOT / "05_AI产品库"),
                                  ("learn", "学习资源", ROOT / "06_学习资源")):
        if key == "learn":                       # 学习资源里还有课程，得走 load 才能算全
            rows, src = load("learn")
            cats: dict[str, int] = {}
            for i in rows:
                cats[i["category"]] = cats.get(i["category"], 0) + 1
        else:
            cats = categories(local_dir)
            src = "本机仓库" if cats else "线上 API"
            if not cats:
                cats = _fetch(key)["categories"]
        total = sum(cats.values())
        lines.append(f"## {label}（{total} 条，数据来自{src}）")
        lines.append("、".join(f"{k} {v}" for k, v in cats.items()))
        lines.append("")
    cards, csrc = load_cards()
    ccats: dict[str, int] = {}
    for c in cards:
        ccats[c["category"]] = ccats.get(c["category"], 0) + 1
    lines.append(f"## 知识卡片（{len(cards)} 条，数据来自{csrc}）")
    lines.append("、".join(f"{k} {v}" for k, v in ccats.items()))
    lines.append("")
    lines.append("查 AI 产品用 search_products，查学习资源用 search_resources。")
    return "\n".join(lines)


@server.tool(description="搜索提示词。query 中英文都行（匹配中英文名、说明、标签、详解），category 可按分类收窄，留空则全库搜")
def search_prompts(query: str = "", category: str = "", limit: int = 10) -> str:
    items, src = load("prompts")
    rows = search(items, query, category, max(1, min(limit, 50)))
    if not rows:
        return f"没搜到。全库 {len(items)} 条，分类：{'、'.join(sorted({i['category'] for i in items}))}"
    out = [f"找到 {len(rows)} 条（共 {len(items)} 条，数据来自{src}）："]
    for r in rows:
        out.append(f"- **{label(r)}**［{r['category']}］{r['summary']}")
    out.append("\n用 get_prompt 取某条的完整提示词。")
    return "\n".join(out)


@server.tool(description="按名字取一条提示词的完整内容：中文译文和英文原文（都能直接复制使用）+ 详细介绍 + 怎么用")
def get_prompt(name: str) -> str:
    items, _ = load("prompts")
    it = pick_one(items, name)
    if not it:
        return f"没找到「{name}」。可以先用 search_prompts 搜一下。"
    lines = [
        f"# {label(it)}",
        f"分类：{it['category']}　标签：{'、'.join(it.get('tags') or [])}",
        f"来源：{it.get('origin', '')}　{it.get('source', '')}",
        "",
        "## 提示词",
    ]
    zh, en = it.get("prompt", ""), it.get("prompt_en", "")
    if en:
        lines += ["", "中文译文：", "```", zh, "```", "", "英文原文：", "```", en, "```"]
    else:
        lines += ["", "```", zh, "```"]
    lines += ["", "## 详细介绍", it.get("detail", ""), "",
              "## 怎么用", it.get("howto", "")]
    return "\n".join(lines)


@server.tool(description="搜索 Skill。query 匹配技能名、中文名、说明、标签")
def search_skills(query: str = "", category: str = "", limit: int = 10) -> str:
    items, src = load("skills")
    rows = search(items, query, category, max(1, min(limit, 50)))
    if not rows:
        return f"没搜到。全库 {len(items)} 个，分类：{'、'.join(sorted({i['category'] for i in items}))}"
    out = [f"找到 {len(rows)} 个（共 {len(items)} 个，数据来自{src}）："]
    for r in rows:
        name = r.get("display") or r["name"]
        out.append(f"- **{name}**（{r['name']}）［{r['category']}］{r['summary'][:60]}")
    out.append("\n用 get_skill 看详情，用 install_skill 装到本机。")
    return "\n".join(out)


@server.tool(description="看一个 Skill 的详情：干什么、怎么装、从哪来")
def get_skill(name: str) -> str:
    items, _ = load("skills")
    it = pick_one(items, name)
    if not it:
        return f"没找到「{name}」。可以先用 search_skills 搜一下。"
    lines = [
        f"# {it.get('display') or it['name']}（{it['name']}）",
        f"分类：{it['category']}　标签：{'、'.join(it.get('tags') or [])}",
        f"来源：{it.get('origin', '')}",
    ]
    if it.get("source"):
        lines.append(f"安装地址：{it['source']}")
    lines += ["", str(it.get("summary", ""))]
    body_path = it.get("body_path", "")
    if body_path and Path(body_path).exists():
        lines.append("\n技能本体在本机，可以直接用 install_skill 安装。")
    elif it.get("source"):
        lines.append("\n本机没有这个技能的本体，按上面的安装地址去原始来源装。")
    return "\n".join(lines)


@server.tool(description=(
    "把一个 Skill 装到本机。target 留空则装到 ~/.claude/skills/<技能名>；"
    "想装进某个项目就传那个项目的 .claude/skills 路径。"
    "技能本体在本机时直接复制；不在本机时返回技能名和来源网址，由调用方去下载。"))
def install_skill(name: str, target: str = "") -> str:
    items, _ = load("skills")
    it = pick_one(items, name)
    if not it:
        return f"没找到「{name}」。可以先用 search_skills 搜一下。"

    label = it.get("display") or it["name"]
    body = str(it.get("body_path", "") or "").strip()
    src = Path(body) if body else None

    # 本体不在本机：把技能名和来源网址交出去，由调用方自己去下载
    if not src or not src.is_dir():
        url = str(it.get("source", "") or "").strip()
        if not url:
            return (f"「{label}」在本机没有本体，卡片上也没登记来源网址，装不了。\n"
                    f"如果是你自己做的技能，去 magicskills 或魔搭社区传一份，再把网址补进卡片。")
        where = "魔搭社区" if "modelscope" in url else ("GitHub" if "github" in url else "原始来源")
        return "\n".join([
            f"「{label}」的本体不在本机。",
            "",
            f"技能名：{it['name']}",
            f"来源（{where}）：{url}",
            "",
            "请你自己去这个地址把技能下载下来，装到 ~/.claude/skills/ 下（或用户指定的目录）。",
        ])

    dest_root = Path(target).expanduser() if target else Path.home() / ".claude" / "skills"
    dest = dest_root / src.name
    if dest.exists():
        return f"目标已存在：{dest}\n要覆盖就先自己删掉它，或者换一个 target。"

    def ignore(_d, names):
        return [n for n in names if n in SKIP_DIRS]

    dest_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest, ignore=ignore, symlinks=False)
    files = sum(1 for f in dest.rglob("*") if f.is_file())
    return (f"已安装「{label}」\n"
            f"位置：{dest}（{files} 个文件）\n"
            f"在 Claude Code 里用 /{src.name} 调用。")


@server.tool(description="搜索知识卡片：一张卡讲清一个概念、工具、原理或方法")
def search_cards(query: str, limit: int = 8) -> str:
    items, src = load_cards()
    rows = search(items, query, "", max(1, min(limit, 30)))
    if not rows:
        return f"没搜到。全库 {len(items)} 张卡。"
    out = [f"找到 {len(rows)} 张（共 {len(items)} 张，数据来自{src}）："]
    for r in rows:
        out.append(f"- **{r['name']}**［{r['category']}］{r['summary']}")
    out.append("\n用 get_card 取全文。")
    return "\n".join(out)


@server.tool(description="取一张知识卡片的全文")
def get_card(name: str) -> str:
    items, _ = load_cards()
    it = pick_one(items, name)
    if not it:
        return f"没找到「{name}」。可以先用 search_cards 搜一下。"
    return f"# {it['name']}\n\n{it.get('body', '')}"


@server.tool(description=(
    "在 AI 产品库里搜别人做的 AI 产品和 AI 应用。用户问「有没有做 XX 的 AI 工具」"
    "「推荐个好用的 XX 产品」时用这个。query 匹配名称、一句话说明、标签、分类，"
    "category 可按分类收窄（对话助手／图像生成／视频生成／音频音乐／写作办公／"
    "编程开发／智能体／学习与科研／生活娱乐），留空则全库搜"))
def search_products(query: str = "", category: str = "", limit: int = 10) -> str:
    items, src = load("products")
    rows = search(items, query, category, max(1, min(limit, 50)))
    if not rows:
        return f"没搜到。全库 {len(items)} 条，分类：{'、'.join(sorted({i['category'] for i in items}))}"
    out = [f"找到 {len(rows)} 条（共 {len(items)} 条，数据来自{src}）："]
    for r in rows:
        tags = "、".join(str(t) for t in (r.get("tags") or []))
        out.append(f"- **{r['name']}**［{r['category']}］{r['summary']}"
                   + (f"（{tags}）" if tags else ""))
    out.append("\n用 get_product 看某条的官网和详情。")
    return "\n".join(out)


@server.tool(description="看一个 AI 产品的详情：官网地址、谁做的、从哪收录的")
def get_product(name: str) -> str:
    items, _ = load("products")
    it = pick_one(items, name)
    if not it:
        return f"没找到「{name}」。可以先用 search_products 搜一下。"
    lines = [
        f"# {it['name']}",
        f"分类：{it['category']}　标签：{'、'.join(str(t) for t in (it.get('tags') or []))}",
        str(it.get("summary", "")),
        "",
        f"官网：{it.get('source', '')}",
        f"出处：{it.get('origin', '')}",
    ]
    if it.get("body"):
        lines += ["", str(it["body"])]
    return "\n".join(lines)


@server.tool(description=(
    "在「学习资源」库里搜能读的、能学的、能查的资料。用户问「去哪学 XX」"
    "「有没有 XX 的教程」「有没有别人整理好的 XX 清单」「现在哪个模型最强」时用这个。"
    "分类：行业文章／教程与课程／别人的清单／模型排行榜。"
    "教程与课程里有几门完整课程，能用 get_resource 读到每一讲全文"))
def search_resources(query: str = "", category: str = "", limit: int = 10) -> str:
    items, src = load("learn")
    rows = search(items, query, category, max(1, min(limit, 50)))
    if not rows:
        return f"没搜到。全库 {len(items)} 条，分类：{'、'.join(sorted({i['category'] for i in items}))}"
    out = [f"找到 {len(rows)} 条（共 {len(items)} 条，数据来自{src}）："]
    for r in rows:
        mark = "（完整课程，能读全文）" if r.get("course") else ""
        out.append(f"- **{r['name']}**［{r['category']}］{r['summary']}{mark}")
    out.append("\n要完整说明就用 get_resource 取。")
    return "\n".join(out)


def _lesson_text(course: dict, les: dict) -> str:
    """取一讲的原文：本机有发布出来的 Markdown 就读本机，没有就去线上取。"""
    rel = str(les.get("md", ""))
    local = ROOT / "01_网站工程" / rel
    if local.is_file():
        text = local.read_text(encoding="utf-8")
    else:
        url = f"{SITE}/{rel}"
        try:
            with urllib.request.urlopen(url, timeout=20) as r:  # noqa: S310
                text = r.read().decode("utf-8")
        except Exception as e:  # noqa: BLE001
            return f"这一讲的原文没取到（{url}）：{e}"
    head = f'{les.get("no", "")} {les.get("title", "")}'.strip()
    return f"# {course['name']}｜{head}\n\n{text}"


def _course_detail(it: dict, lesson: str) -> str:
    lessons = it.get("lessons") or []
    if lesson:
        q = lesson.strip().lower()
        hit = next((l for l in lessons if str(l.get("no", "")).lower() == q), None)
        if hit is None:
            hits = [l for l in lessons if q in str(l.get("title", "")).lower()]
            hit = hits[0] if hits else None
        if hit is None:
            listing = "、".join(f'{l.get("no") or "附录"} {l.get("title", "")}' for l in lessons)
            return f"「{it['name']}」里没找到「{lesson}」。可选：{listing}"
        return _lesson_text(it, hit)

    lines = [
        f"# {it['name']}",
        f"分类：{it['category']}　标签：{'、'.join(str(t) for t in (it.get('tags') or []))}",
        str(it.get("summary", "")),
        "",
        f"全文页：{it.get('url', '')}",
        f"出处：{it.get('origin', '')}",
        "",
        f"共 {len(lessons)} 讲：",
    ]
    lines += [f'- {l.get("no", "")} {l.get("title", "")}'.replace("  ", " ").strip()
              for l in lessons]
    lines += ["", '要某一讲的原文，再用 get_resource 取，传 lesson="05"（编号或标题里的字样都行）。']
    return "\n".join(lines)


@server.tool(description=(
    "看一条学习资源的详情：讲的什么、在哪看。"
    "如果是完整课程，传 lesson 还能取到某一讲的全文（lesson 用编号如 05，或标题里的字样）"))
def get_resource(name: str, lesson: str = "") -> str:
    items, _ = load("learn")
    it = pick_one(items, name)
    if not it:
        return f"没找到「{name}」。可以先用 search_resources 搜一下。"
    if it.get("course"):
        return _course_detail(it, lesson)
    lines = [
        f"# {it['name']}",
        f"分类：{it['category']}　标签：{'、'.join(str(t) for t in (it.get('tags') or []))}",
        str(it.get("summary", "")),
        "",
        f"地址：{it.get('source', '')}",
        f"出处：{it.get('origin', '')}",
    ]
    if it.get("body"):
        lines += ["", str(it["body"])]
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        print(site_overview())
        print()
        print(search_prompts("少说套话"))
        print()
        print(search_skills("写作", limit=3))
        print()
        print(search_products("小红书", limit=5))
        print()
        print(search_resources("教程", limit=5))
        print()
        print(get_resource("给所有人的 AI 课"))
        print()
        print(get_resource("给所有人的 AI 课", lesson="02")[:300] + "……")
    else:
        server.run("stdio")
