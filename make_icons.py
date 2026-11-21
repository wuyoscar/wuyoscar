# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""README 项目表格里的小图标：icons/<仓库名>.svg。

    uv run make_icons.py     # 重新生成全部图标

每个图标是 24x24 的圆角色块 + 白色线条图形，深浅色页面都能用。
要加图标：在 ICONS 里加一项（仓库名 -> 底色、图形），图形画在 5..19 的范围内。
图标是静态文件，改了这里才需要重新生成；每天的 Action 不会跑这个脚本。
"""
from pathlib import Path

HERE = Path(__file__).parent

# 仓库名（不带 owner）-> (底色, 图形)。图形默认是白色描边、不填充；要实心的地方自己写 fill="#fff"。
ICONS = {
    # 画框：远山和太阳
    "GPT-Image2-Skill": ("#be4bdb", """
        <rect x="5.5" y="6.5" width="13" height="11" rx="2"/>
        <circle cx="9.3" cy="10.2" r="1.2" fill="#fff" stroke="none"/>
        <path d="M6 16l3.6-3.4 2.6 2.2 2.2-1.9 3.6 3.1"/>"""),
    # 裂开的盾牌
    "Internal-Safety-Collapse": ("#e03131", """
        <path d="M12 5l5.8 2v4.6c0 3.4-2.3 6-5.8 7.4-3.5-1.4-5.8-4-5.8-7.4V7z"/>
        <path d="M12.8 8.2l-1.9 3.3 2.3 1-1.6 3.3"/>"""),
    # 火焰
    "AISafetyHot": ("#f76707", """
        <path fill="#fff" stroke="none" d="M12.4 4.6c.3 3 4.4 4.3 4.4 8.6a4.8 4.8 0 0 1-9.6 0c0-1.9.8-3.2 2-4.2.1 1.4.7 2.2 1.5 2.5-.4-2.6.3-5 1.7-6.9z"/>
        <path fill="#f76707" stroke="none" d="M12.1 12.6c.2 1.2 1.7 1.7 1.7 3.3a1.8 1.8 0 0 1-3.6 0c0-.7.3-1.2.8-1.6.1.5.3.8.6.9-.1-1 .1-1.9.5-2.6z"/>"""),
    # 工作流：两个节点汇到一个
    "jev-skill": ("#37b24d", """
        <circle cx="7.3" cy="8" r="1.9"/><circle cx="7.3" cy="16" r="1.9"/><circle cx="16.7" cy="12" r="1.9"/>
        <path d="M9.2 8h1.6c2 0 1.6 4 4 4M9.2 16h1.6c2 0 1.6-4 4-4"/>"""),
    # 摊开的书
    "Awesome-Large-Model-Safety": ("#1c7ed6", """
        <path d="M12 8.2c-1.8-1.2-4-1.5-6.3-1v9.6c2.3-.5 4.5-.2 6.3 1 1.8-1.2 4-1.5 6.3-1V7.2c-2.3-.5-4.5-.2-6.3 1z"/>
        <path d="M12 8.2v9.6"/>"""),
    # 三道爪痕
    "XSafeClaw": ("#12b886", """
        <g stroke-width="2.1">
        <path d="M7.6 6.2c-1 3.8-.5 7.6 1.6 11.4"/><path d="M11.8 5.6c-1 4.2-.5 8.4 1.6 12.6"/>
        <path d="M16 6.2c-1 3.8-.5 7.6 1.6 11.4"/></g>"""),
    # 两张叠着的图文卡片
    "Vibepost": ("#f0386b", """
        <rect x="9.6" y="5.3" width="9" height="11.4" rx="1.8" opacity=".65"/>
        <rect x="5.4" y="7.6" width="9" height="11.4" rx="1.8" fill="#f0386b"/>
        <path d="M7.8 11.2h4.2M7.8 13.8h4.2M7.8 16.4h2.4"/>"""),
    # 带问号的对话气泡
    "JustAsk": ("#f59f00", """
        <path d="M7.4 5.6h9.2a2 2 0 0 1 2 2v6.2a2 2 0 0 1-2 2h-4.2l-3.6 3v-3H7.4a2 2 0 0 1-2-2V7.6a2 2 0 0 1 2-2z"/>
        <path d="M10.4 9.3a1.7 1.7 0 1 1 2.5 1.5c-.6.3-.9.6-.9 1.2"/>
        <circle cx="12" cy="13.5" r=".55" fill="#fff" stroke="none"/>"""),
    # 论文 -> 箭头
    "arxiv2agent": ("#5c7cfa", """
        <path d="M7.4 5.2h5.4l3.8 3.8v9.8H7.4z"/><path d="M12.8 5.2V9h3.8"/>
        <path d="M9.6 14.4h4.6M12.6 12.6l1.8 1.8-1.8 1.8"/>"""),
    # 鱼钩
    "scamworld-bench": ("#1098ad", """
        <circle cx="14" cy="6.2" r="1.2"/>
        <path d="M14 7.4v6.9a3.5 3.5 0 0 1-7 0v-2.9l2.5 2.2"/>"""),
    # 放大镜里一个对勾
    "VEX-Bench": ("#7950f2", """
        <circle cx="11" cy="11" r="5.2"/><path d="M14.9 14.9l3.6 3.6"/>
        <path d="M8.7 11.2l1.6 1.6 3-3.2"/>"""),
}


def icon_svg(color, glyph):
    body = "\n".join(line.strip() for line in glyph.strip().splitlines())
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">\n'
        f'<rect width="24" height="24" rx="6" fill="{color}"/>\n'
        '<g fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">\n'
        f"{body}\n</g>\n</svg>\n"
    )


if __name__ == "__main__":
    out = HERE / "icons"
    out.mkdir(exist_ok=True)
    for name, (color, glyph) in ICONS.items():
        (out / f"{name}.svg").write_text(icon_svg(color, glyph), encoding="utf-8")
    print("icons written:", len(ICONS))
