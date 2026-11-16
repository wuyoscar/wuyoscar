# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""README.md 里卡片下方的项目列表：每个项目一张 GitHub Pinned 样式的小卡片（cards/*.svg）。

    uv run readme_list.py     # 重新抓 star / 语言，生成 cards/*.svg，并改写 README.md 里的列表

build.py 每次生成大卡片时也会调用这里的 refresh()，所以每周的 Action 不用单独跑它。
要增删项目或改分组，只改 README_GROUPS。
"""
import json
import os
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

HERE = Path(__file__).parent
USER = "wuyoscar"

# (分组, [(仓库, 一句话说明), ...])。自己的仓库只写名字；别人的仓库写 "owner/name"。
# 分组名写 None 就不出小标题。现在项目不多，先不分组；以后要分，把 None 换成组名、再加一组即可。
README_GROUPS = [
    (None, [
        ("Internal-Safety-Collapse",
         "Safety failures in coding agents and frontier LLMs, with reproducible workspaces. NeurIPS 2026"),
        ("GPT-Image2-Skill", "Prompt gallery, CLI and agent skill for GPT Image 2 generation and editing"),
        ("AISafetyHot", "Daily AI safety news, papers and incidents: website, digest, RSS and MCP"),
        ("jev-skill", "Jev use cases, workflows and agent skills"),
        ("scamworld-bench",
         "ScamWorld, an interactive environment for evaluating web agents against online fraud"),
        ("Vibepost", "Desktop app that lays out Markdown as Xiaohongshu image cards and long images"),
        ("arxiv2agent", "Turns arXiv papers into structured, agent-readable digest folders"),
    ]),
    # 以后要加的分组照这个格式写，别人的仓库用 "owner/name"：
    # ("Recommended", [
    #     ("owner/name", "一句话说明"),
    # ]),
]
START, END = "<!-- PROJECTS:START -->", "<!-- PROJECTS:END -->"

# ---- 小卡片版式（px），照 GitHub 主页的 Pinned 卡片量的：1px 边框、圆角 6、内边距 16、标题 14/600、正文 12 ----
# 主页 README 的内容区宽 846px：两张卡片（各 416 + 右侧 4px 透明留白）加中间一个空格刚好一行，
# 卡片间距约 8px；手机上放不下两张，自动变成一列
CARD_W, CARD_H, CARD_PAD = 416, 127, 16
GAP_R, GAP_B = 4, 3        # 画在 SVG 里的透明留白，用来拉开卡片之间的距离（README 里不能写 CSS）
DESC_LINES = 2
FONT_STACK = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
# 一张 SVG 同时带两套颜色，由浏览器的深/浅色模式选
CARD_CSS = (
    ".b{fill:none;stroke:#d1d9e0}.n{fill:#0969da;font-size:14px;font-weight:600}"
    ".o{font-weight:400}.m{fill:#59636e;font-size:12px}.i{fill:#59636e}"
    "@media (prefers-color-scheme: dark){.b{stroke:#3d444d}.n{fill:#4493f8}.m{fill:#9198a1}.i{fill:#9198a1}}"
)
# GitHub 语言色（github-linguist），没列到的用灰色
LANG_COLORS = {
    "Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "HTML": "#e34c26",
    "CSS": "#663399", "Jupyter Notebook": "#DA5B0B", "Shell": "#89e051", "Rust": "#dea584",
    "Go": "#00ADD8", "Swift": "#F05138", "TeX": "#3D6117", "Vue": "#41b883",
}
# Octicons（MIT）：repo-16、star-16
ICON_REPO = ("M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 "
             "0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 "
             "1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 "
             ".25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z")
ICON_STAR = ("M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 "
             "4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 "
             "6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Zm0 2.445L6.615 5.5a.75.75 0 0 "
             "1-.564.41l-3.097.45 2.24 2.184a.75.75 0 0 1 .216.664l-.528 3.084 2.769-1.456a.75.75 0 0 1 .698 "
             "0l2.77 1.456-.53-3.084a.75.75 0 0 1 .216-.664l2.24-2.183-3.096-.45a.75.75 0 0 1-.564-.41L8 2.694Z")


def full_name(repo):
    return repo if "/" in repo else f"{USER}/{repo}"


def listed():
    return [full_name(repo) for _, items in README_GROUPS for repo, _ in items]


def short(n):
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


def fetch_repos():
    """{"owner/name": {"stars": int, "language": str | None}}，只查列表里的仓库。"""
    info = {}
    for full in listed():
        req = urllib.request.Request(f"https://api.github.com/repos/{full}",
                                     headers={"User-Agent": "profile-card",
                                              "Accept": "application/vnd.github+json"})
        if os.environ.get("GITHUB_TOKEN"):
            req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
        info[full] = {"stars": d["stargazers_count"], "language": d["language"]}
    return info


# ---------------------------------------------------------------- 小卡片
def text_width(s, size):
    """粗估无衬线字体下的文字宽度（px）。SVG 里的文字不会自动换行，只能自己断行；宁可估宽一点。"""
    em = 0.0
    for ch in s:
        if ch in "iljI.,:;'|! ":
            em += 0.30
        elif ch in "ftr-()":
            em += 0.38
        elif ch in "mwMW@":
            em += 0.88
        elif ch.isupper() or ch.isdigit():
            em += 0.66
        else:
            em += 0.56
    return em * size


def wrap(text, width, size, max_lines):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and text_width(trial, size) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    lines.append(cur)
    if len(lines) > max_lines:  # 放不下就截断，加省略号
        last = lines[max_lines - 1]
        while text_width(last + "…", size) > width:
            last = last.rsplit(" ", 1)[0]
        lines = lines[:max_lines - 1] + [last + "…"]
    return lines


def card_svg(full, desc, info):
    owner, name = full.split("/")
    title = escape(name) if owner == USER else f'<tspan class="o">{escape(owner)}/</tspan>{escape(name)}'
    inner = CARD_W - 2 * CARD_PAD
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W + GAP_R}" height="{CARD_H + GAP_B}" '
        f'viewBox="0 0 {CARD_W + GAP_R} {CARD_H + GAP_B}" font-family="{FONT_STACK}">',
        f"<style>{CARD_CSS}</style>",
        f'<rect class="b" x="0.5" y="0.5" width="{CARD_W - 1}" height="{CARD_H - 1}" rx="6"/>',
        f'<path class="i" transform="translate({CARD_PAD},18.5)" d="{ICON_REPO}"/>',
        f'<text class="n" x="{CARD_PAD + 24}" y="31.5">{title}</text>',
    ]
    for i, line in enumerate(wrap(desc, inner, 12, DESC_LINES)):
        out.append(f'<text class="m" x="{CARD_PAD}" y="{58 + i * 18}">{escape(line)}</text>')
    x, base = CARD_PAD, CARD_H - CARD_PAD - 5          # 底部一行：语言、star
    lang = info.get("language")
    if lang:
        out.append(f'<circle cx="{x + 6}" cy="{base - 4}" r="6" fill="{LANG_COLORS.get(lang, "#8b949e")}"/>')
        out.append(f'<text class="m" x="{x + 18}" y="{base}">{escape(lang)}</text>')
        x += 18 + text_width(lang, 12) + 16
    if info.get("stars"):
        out.append(f'<path class="i" transform="translate({x:.1f},{base - 13})" d="{ICON_STAR}"/>')
        out.append(f'<text class="m" x="{x + 20:.1f}" y="{base}">{short(info["stars"])}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- README
def readme_block():
    """每组一个小标题，下面是一排排卡片。每张卡片是指向仓库的链接，不写死一行几张，由页面宽度决定。"""
    out = [START]
    for group, items in README_GROUPS:
        out += ["", f"### {escape(group)}", ""] if group else [""]
        for repo, desc in items:
            full = full_name(repo)
            name = full.split("/")[1]
            out.append(f'<a href="https://github.com/{full}"><img src="./cards/{name}.svg" '
                       f'width="{CARD_W + GAP_R}" alt={quoteattr(f"{name}: {desc}")}></a>')
    out += ["", END]
    return "\n".join(out)


def refresh():
    """抓数据 -> 写 cards/*.svg -> 改写 README.md 里两个标记之间的部分（其余内容不动）。"""
    info = fetch_repos()
    cards = HERE / "cards"
    cards.mkdir(exist_ok=True)
    keep = set()
    for _, items in README_GROUPS:
        for repo, desc in items:
            full = full_name(repo)
            path = cards / f'{full.split("/")[1]}.svg'
            path.write_text(card_svg(full, desc, info[full]), encoding="utf-8")
            keep.add(path)
    for old in cards.glob("*.svg"):   # 从列表里删掉的项目，卡片也删掉
        if old not in keep:
            old.unlink()
    path = HERE / "README.md"
    text = path.read_text(encoding="utf-8")
    if START not in text or END not in text:
        print("README.md has no PROJECTS markers; skipped")
        return
    head, rest = text.split(START, 1)
    path.write_text(head + readme_block() + rest.split(END, 1)[1], encoding="utf-8")


if __name__ == "__main__":
    refresh()
    print("README.md updated:", len(listed()), "projects")
