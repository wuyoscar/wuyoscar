# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""README.md 里卡片下方的项目表格：左列 star 数，右列 emoji + 项目名，下面一行是说明。

    uv run readme_list.py     # 重新抓 star，改写 README.md 里的表格

build.py 每次生成大卡片时也会调用这里的 refresh()，所以每天的 Action 不用单独跑它。
要增删项目或改分组，只改 README_GROUPS。
"""
import json
import os
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
USER = "wuyoscar"

# (分组, [(仓库, emoji, 一句话说明), ...])。自己的仓库只写名字；别人的仓库写 "owner/name"。
# 分组名写 None 就不出小标题。现在项目不多，先不分组；以后要分，把 None 换成组名、再加一组即可。
README_GROUPS = [
    (None, [
        ("Internal-Safety-Collapse", "🚨",
         "Safety failures in coding agents and frontier LLMs, with reproducible workspaces. NeurIPS 2026"),
        ("GPT-Image2-Skill", "🎨", "Prompt gallery, CLI and agent skill for GPT Image 2 generation and editing"),
        ("AISafetyHot", "🔥", "Daily AI safety news, papers and incidents: website, digest, RSS and MCP"),
        ("jev-skill", "🧩", "Jev use cases, workflows and agent skills"),
        ("scamworld-bench", "🎣",
         "ScamWorld, an interactive environment for evaluating web agents against online fraud"),
        ("Vibepost", "🖼️", "Desktop app that lays out Markdown as Xiaohongshu image cards and long images"),
        ("arxiv2agent", "📄", "Turns arXiv papers into structured, agent-readable digest folders"),
        ("XSafeAI/XSafeClaw", "🦞", "Open-source agent safety platform from Fudan University"),
        ("xingjunm/Awesome-Large-Model-Safety", "📚",
         "Safety at Scale: a survey of large model and agent safety"),
        ("x-zheng16/JustAsk", "🙋",
         "JustAsk: curious code agents reveal system prompts in frontier LLMs. ICML 2026"),
        ("HanxunH/VEX-Bench", "🔎",
         "Benchmarking verification complexity of LLM-generated misinformation. NeurIPS 2026"),
    ]),
    # 以后要加的分组照这个格式写，别人的仓库用 "owner/name"：
    # ("Recommended", [
    #     ("owner/name", "🔧", "一句话说明"),
    # ]),
]
START, END = "<!-- PROJECTS:START -->", "<!-- PROJECTS:END -->"


def full_name(repo):
    return repo if "/" in repo else f"{USER}/{repo}"


def listed():
    return [full_name(repo) for _, items in README_GROUPS for repo, _, _ in items]


def short(n):
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


def fetch_stars():
    """{"owner/name": star 数}，只查列表里的仓库。"""
    stars = {}
    for full in listed():
        req = urllib.request.Request(f"https://api.github.com/repos/{full}",
                                     headers={"User-Agent": "profile-card",
                                              "Accept": "application/vnd.github+json"})
        if os.environ.get("GITHUB_TOKEN"):
            req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
        with urllib.request.urlopen(req, timeout=30) as r:
            stars[full] = json.load(r)["stargazers_count"]
    return stars


def readme_block(stars):
    """每组一张两列的 Markdown 表格（有组名时前面加小标题）。star 数单独一列放在行首，
    手机上也放得下；自己的仓库只显示名字，别人的显示 owner/name。"""
    out = [START]
    for group, items in README_GROUPS:
        out.append("")
        if group:
            out += [f"### {group}", ""]
        out += ["| ⭐ | Project |", "|--:|:--|"]
        for repo, emoji, desc in items:
            full = full_name(repo)
            cell = desc.replace("|", "\\|")     # 说明里的竖线要转义，否则会被当成分列
            out.append(f"| {short(stars[full])} | {emoji} **[{repo}](https://github.com/{full})**<br>{cell} |")
    out += ["", END]
    return "\n".join(out)


def refresh():
    """抓 star -> 改写 README.md 里两个标记之间的部分（其余内容不动）。"""
    stars = fetch_stars()
    path = HERE / "README.md"
    text = path.read_text(encoding="utf-8")
    if START not in text or END not in text:
        print("README.md has no PROJECTS markers; skipped")
        return
    head, rest = text.split(START, 1)
    path.write_text(head + readme_block(stars) + rest.split(END, 1)[1], encoding="utf-8")


if __name__ == "__main__":
    refresh()
    print("README.md updated:", len(listed()), "projects")
