# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow"]
# ///
"""生成 neofetch 风格的 GitHub profile 卡片：dark_mode.svg / light_mode.svg。

    uv run build.py                 # 抓 GitHub 数据并生成两套主题
    uv run build.py --offline       # 不联网，用 stats.json 里上次的数字
    uv run build.py --art pixel     # 左图风格：photo（默认，Python 的照片）/ dog / pixel / image / hybrid / ascii
    uv run build.py --all-styles    # 所有风格都生成到 variants/，用来对比

文字内容在 SECTIONS / PROJECTS 里；star 等数字由脚本抓取，不要手写。
"""
import argparse
import base64
import colorsys
import io
import json
import os
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageEnhance, ImageOps

HERE = Path(__file__).parent
USER = "wuyoscar"
DEFAULT_ART = "photo"

# ---- 版式（px）----
FONT, LH, PAD = 15, 18, 22
CW = FONT * 0.602          # 等宽字符宽度；每行再用 textLength 锁死，换字体不会错位
ART_COLS, GAP_COLS, INFO_COLS = 24, 3, 64
ART_ROWS = 16            # 头像高度（按右栏行数算），顶部对齐，不再撑满整列
STAR_COLS = 9              # Open Source 每行右侧留给 star 数的宽度
ART_FONT, ART_LH = 6, 7    # 字符画用小字号，分辨率才够
ART_CW = ART_FONT * 0.602

# ---- 内容 ----
# (标题, [(key, value), ...])；"@projects" / "@stats" 由抓到的数据填充
SECTIONS = [
    (None, [("Location", "Melbourne, Australia")]),
    ("Topics", [
        ("Agents", "multi-agent workflows, agent skills"),
        ("Agent.Safety", "web, GUI, coding, computer-use agents"),
        ("RedTeaming", "jailbreaks, prompt injection"),
        ("Robustness", "backdoors, poisoning, transferable attacks"),
        ("Retrieval", "paper search & reading, RAG, hallucination"),
        ("Multimodal", "vision-language models, image generation"),
        ("Misinformation", "fact checking, fake media, web scams"),
        ("Governance", "AI safety & frontier-AI policy"),
    ]),
    ("Open Source", "@projects"),
    ("Contact", [
        ("Email", "wuy7117@gmail.com"),
        ("Website", "aisafetyhot.com"),
        ("Scholar", "scholar.google.com/citations?user=F41UYqAAAAAJ"),
        ("LinkedIn", "linkedin.com/in/oscar-wu-"),
    ]),
]
# 左栏窄板块（宽 ART_COLS，每行最多 22 个字符）
OFFLINE = ["basketball, swimming,", "hiking, cooking,", "League of Legends,", "Elden Ring"]

# 左图：像素画的金毛 Python。一个字符 = 一个像素，颜色见 DOG_COLORS，"." 透明
DOG = [
    "......................",
    "....KKK........KKK....",
    "...KDDDKKKKKKKKDDDK...",
    "..KDDDKGGGGGGGGKDDDK..",
    "..KDDKGGGGGGGGGGKDDK..",
    "..KDDKGGGGGGGGGGKDDK..",
    "..KDDKGGKWGGGKWGKDDK..",
    "..KDDKGGKKGGGKKGKDDK..",
    "..KDKGGGLLLLLLGGGKDK..",
    "...KKGGLLLNNLLLGGKK...",
    "....KGGLLLNNLLLGGK....",
    "....KGGLLKLLKLLGGK....",
    ".....KGLLLKKLLLGK.....",
    ".....KGGLLTTLLGGK.....",
    "......KGGGTTGGGK......",
    ".....KGGGGGGGGGGK.....",
    "....KGGGLLLLLLGGGK....",
    "...KGGGGLLLLLLGGGGK...",
    "...KGGGGLLLLLLGGGGK...",
    "...KGGGGGLLLLGGGGGK...",
    "...KGGKGGGLLGGGKGGK...",
    "...KGGKGGGGGGGGKGGK...",
    "...KLLKGGKKKKGGKLLK...",
    "....KKKKKK..KKKKKK....",
]
DOG_TAIL = (18, 17, ["..KK", ".KGK", "KGGK", "KGK."])  # (列, 行, 像素)，单独一组用来摇
DOG_COLORS = {"K": "#4a3020", "G": "#e9a23b", "L": "#f7cf7e", "D": "#b97428",
              "N": "#2a1a12", "W": "#ffffff", "T": "#f28a9b"}
# (仓库名, 一句话说明)；star 数按仓库名从 API 取
PROJECTS = [
    ("Internal-Safety-Collapse", "red teaming, NeurIPS'26"),
    ("AISafetyHot", "daily AI safety news & papers"),
    ("GPT-Image2-Skill", "image prompts, CLI, agent skill"),
    ("jev-skill", "agent skills & workflows"),
    ("arxiv2agent", "arXiv -> agent-readable digests"),
    ("scamworld-bench", "web agents vs. online fraud"),
]

THEMES = {
    "dark": dict(bg="#161b22", fg="#c9d1d9", key="#ffa657", val="#a5d6ff", dot="#586069",
                 star="#e3b341", border="#30363d", panel="#0d1117", glow="#ff5c6c",
                 dogpanel="#0d1117"),
    "light": dict(bg="#f6f8fa", fg="#24292f", key="#953800", val="#0a3069", dot="#afb8c1",
                  star="#9a6700", border="#d0d7de", panel="#0d1117", glow="#cf222e",
                  dogpanel="#ffffff"),
}

# 左图每种风格在头像上的取景：上边、下边、水平中心（占原图比例）
CROPS = {
    "image": (0.00, 1.00, 0.62),
    "hybrid": (0.00, 0.80, 0.64),
    "ascii": (0.00, 0.62, 0.69),   # 只取头部，眼睛才够大
    "pixel": (0.00, 0.60, 0.69),
}
# pixel 风格：字符放大到看得出是字符，底下垫一层同网格的马赛克
PIXEL_FONT, PIXEL_LH = 7, 8


# ---------------------------------------------------------------- 数据
def fetch_stats(offline=False):
    """GitHub 公开 API：自有仓库数、总 star、followers、各仓库 star。失败时回退到 stats.json。"""
    cache = HERE / "stats.json"
    if not offline:
        try:
            def get(url):
                req = urllib.request.Request(url, headers={"User-Agent": "profile-card",
                                                           "Accept": "application/vnd.github+json"})
                if os.environ.get("GITHUB_TOKEN"):
                    req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
                with urllib.request.urlopen(req, timeout=30) as r:
                    return json.load(r)
            repos, page = [], 1
            while True:
                batch = get(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}")
                repos += batch
                if len(batch) < 100:
                    break
                page += 1
            own = [r for r in repos if not r["fork"]]
            stats = {
                "repos": len(own),
                "stars": sum(r["stargazers_count"] for r in own),
                "followers": get(f"https://api.github.com/users/{USER}")["followers"],
                "repo_stars": {r["name"]: r["stargazers_count"] for r in own},
            }
            cache.write_text(json.dumps(stats, indent=2, sort_keys=True) + "\n")
            return stats
        except Exception as e:  # 网络或限流：用上次的数字，不让构建失败
            print(f"fetch failed ({e}); using {cache.name}")
    return json.loads(cache.read_text())


def short(n):
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


# ---------------------------------------------------------------- 右栏
def info_lines(stats):
    """每行 = (spans, star)；spans 是 [(css class, text), ...]，star 是右对齐的 star 文本或 None。"""
    lines = []

    def rule(title, bare=False):
        head = f"{title} " if bare else f"- {title} "
        lines.append(([("fg", head + "─" * (INFO_COLS - len(head)))], None))

    def item(k, v, star=None):
        width = INFO_COLS - (STAR_COLS if star is not None else 0)
        dots = width - len(k) - len(v) - 5
        assert dots >= 2, f"太长：{k}: {v}"
        lines.append(([("dot", ". "), ("key", k), ("fg", ":"),
                       ("dot", " " + "." * dots + " "), ("val", v)], star))

    rule(f"oscar@{USER}", bare=True)
    for title, items in SECTIONS:
        if title:
            lines.append(([], None))
            rule(title)
        if items == "@projects":
            for name, desc in PROJECTS:
                item(name, desc, star="★ " + short(stats["repo_stars"].get(name, 0)))
        elif items == "@stats":
            cells = [("Repos", str(stats["repos"])), ("Stars", f"{stats['stars']:,}"),
                     ("Followers", str(stats["followers"]))]
            free = INFO_COLS - 2 - 3 * (len(cells) - 1) - sum(len(k) + len(v) + 3 for k, v in cells)
            fill, extra = divmod(free, len(cells))
            spans = [("dot", ". ")]
            for i, (k, v) in enumerate(cells):
                n = fill + (extra if i == 0 else 0)
                spans += [("key", k), ("fg", ":"), ("dot", " " + "." * n + " "), ("val", v)]
                if i < len(cells) - 1:
                    spans.append(("fg", " | "))
            lines.append((spans, None))
        else:
            for k, v in items:
                item(k, v)
    return lines


def left_lines(stats):
    """左图下方窄栏（宽 ART_COLS）：Offline + GitHub 数字。"""
    W = ART_COLS
    lines = []

    def rule(title):
        head = f"- {title} "
        lines.append([("fg", head + "─" * (W - len(head)))])

    rule("Offline")
    for v in OFFLINE:
        lines.append([("dot", ". "), ("val", v.ljust(W - 2))])
    lines.append([])
    rule("GitHub")
    for k, v in (("Repos", str(stats["repos"])), ("Stars", f"{stats['stars']:,}"),
                 ("Followers", str(stats["followers"]))):
        lines.append([("dot", ". "), ("key", k), ("fg", ":"),
                      ("dot", " " + "." * (W - len(k) - len(v) - 5) + " "), ("val", v)])
    return lines


# ---------------------------------------------------------------- 左图
def crop_avatar(style, w_px, h_px):
    img = Image.open(HERE / "avatar.png").convert("RGB")
    w, h = img.size
    top, bottom, cx = CROPS[style]
    ch = (bottom - top) * h
    cw = min(w, ch * w_px / h_px)
    ch = cw * h_px / w_px
    left = max(0, min(w - cw, w * cx - cw / 2))
    return img.crop((int(left), int(top * h), int(left + cw), int(top * h + ch)))


def image_href(img, w_px, h_px, scale=2):
    img = img.resize((int(w_px * scale), int(h_px * scale)), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=82, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def mosaic_href(img, cols, rows, w_px, h_px):
    """按字符网格缩小再用最近邻放大：每个字符格一个色块。"""
    small = img.resize((cols, rows), Image.Resampling.LANCZOS)
    big = small.resize((int(w_px * 2), int(h_px * 2)), Image.Resampling.NEAREST)
    buf = io.BytesIO()
    big.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def ascii_runs(img, w_px, h_px, lift, n_colors=64, font=ART_FONT, lh=ART_LH,
               ramp=".:;=+*x#%@@@", gamma=0.6):
    """图 -> 彩色字符。颜色取自原图（lift 越大暗部越亮），字符疏密辅助表现明暗。"""
    cols, rows = int(w_px / (font * 0.602)), int(h_px / lh)
    img = img.resize((cols, rows), Image.Resampling.LANCZOS)
    img = ImageEnhance.Color(img).enhance(1.25)
    lum = ImageOps.autocontrast(img.convert("L"), cutoff=1).tobytes()
    q = img.quantize(n_colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    idx, raw = q.tobytes(), q.getpalette()[: n_colors * 3]
    palette = []
    for i in range(0, len(raw), 3):
        hh, ss, vv = colorsys.rgb_to_hsv(*(c / 255 for c in raw[i:i + 3]))
        r, g, b = colorsys.hsv_to_rgb(hh, ss, lift + (1 - lift) * vv ** 0.8)
        palette.append(f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}")
    out = []
    for y in range(rows):
        runs = []
        for x in range(cols):
            v = (lum[y * cols + x] / 255) ** gamma
            ch = ramp[min(len(ramp) - 1, int(v * len(ramp)))]
            c = idx[y * cols + x]
            if runs and runs[-1][0] == c:
                runs[-1][1] += ch
            else:
                runs.append([c, ch])
        out.append(runs)
    return out, palette, rows, cols


def dog_svg(c, x, y, w, h):
    """像素金毛：每个像素一个 rect，尾巴单独一组做摇尾动画。"""
    assert all(len(r) == len(DOG[0]) for r in DOG)
    cap_h = 26
    cell = int(min((w - 24) / (len(DOG[0]) + 2), (h - cap_h - 16) / len(DOG)))
    ox = x + (w - cell * (len(DOG[0]) + 2)) / 2
    oy = y + (h - cap_h - cell * len(DOG)) / 2 + 2

    def pixels(grid, col0, row0):
        out = []
        for r, row in enumerate(grid):
            c0 = 0
            while c0 < len(row):       # 同色的连续像素合并成一个 rect
                ch = row[c0]
                c1 = c0
                while c1 < len(row) and row[c1] == ch:
                    c1 += 1
                if ch != ".":
                    out.append(f'<rect x="{ox + (col0 + c0) * cell:.1f}" y="{oy + (row0 + r) * cell:.1f}" '
                               f'width="{(c1 - c0) * cell}" height="{cell}" fill="{DOG_COLORS[ch]}"/>')
                c0 = c1
        return out

    tc, tr, tail = DOG_TAIL
    body = [
        f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" rx="6" fill="{c["dogpanel"]}" '
        f'stroke="{c["border"]}"/>',
        '<g shape-rendering="crispEdges">',
        '<g class="tail">', *pixels(tail, tc, tr), "</g>",
        *pixels(DOG, 0, 0),
        "</g>",
        f'<text x="{x + w / 2:.1f}" y="{y + h - 12}" text-anchor="middle" font-size="12px" '
        f'class="dot">Python, golden retriever</text>',
    ]
    css = ("@keyframes wag{50%{transform:rotate(16deg)}}"
           ".tail{transform-box:fill-box;transform-origin:0% 100%;animation:wag .5s steps(1) infinite}")
    return css, body


PHOTO_CELL = 5      # 照片像素画：每个像素格的边长（px），越大越“像素”
PHOTO_COLORS = 28


def photo_svg(c, x, y, w, h):
    """python.png（已抠好背景的 RGBA 照片）-> 像素画：缩到格子分辨率、减色，每段同色像素一个 rect。"""
    cap_h = 26
    src = Image.open(HERE / "python.png").convert("RGBA")
    max_cols, max_rows = int((w - 16) / PHOTO_CELL), int((h - cap_h - 10) / PHOTO_CELL)
    scale = min(max_cols / src.width, max_rows / src.height)
    cols, rows = round(src.width * scale), round(src.height * scale)
    # 先预乘 alpha 再缩小，边缘才不会混进背景色
    small = src.convert("RGBa").resize((cols, rows), Image.Resampling.LANCZOS).convert("RGBA")
    alpha = small.getchannel("A").tobytes()
    rgb = ImageEnhance.Contrast(ImageEnhance.Color(small.convert("RGB")).enhance(1.25)).enhance(1.1)
    q = rgb.quantize(PHOTO_COLORS, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    idx, pal = q.tobytes(), q.getpalette()
    ox = x + (w - cols * PHOTO_CELL) / 2
    oy = y + (h - cap_h - rows * PHOTO_CELL) / 2 + 3
    body = [
        f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" rx="6" fill="{c["dogpanel"]}" '
        f'stroke="{c["border"]}"/>',
        '<g shape-rendering="crispEdges">',
    ]
    for r in range(rows):
        c0 = 0
        while c0 < cols:
            i = r * cols + c0
            key = idx[i] if alpha[i] >= 128 else None
            c1 = c0
            while c1 < cols and (idx[r * cols + c1] if alpha[r * cols + c1] >= 128 else None) == key:
                c1 += 1
            if key is not None:
                col = "#%02x%02x%02x" % tuple(pal[key * 3:key * 3 + 3])
                body.append(f'<rect x="{ox + c0 * PHOTO_CELL:.1f}" y="{oy + r * PHOTO_CELL:.1f}" '
                            f'width="{(c1 - c0) * PHOTO_CELL}" height="{PHOTO_CELL}" fill="{col}"/>')
            c0 = c1
    body += ["</g>",
             f'<text x="{x + w / 2:.1f}" y="{y + h - 12}" text-anchor="middle" font-size="12px" '
             f'class="dot">Python, golden retriever</text>']
    return "", body


def art_svg(style, c, x, y, w, h):
    if style == "photo":
        return photo_svg(c, x, y, w, h)
    if style == "dog":
        return dog_svg(c, x, y, w, h)
    """返回 (css, svg 片段列表)。三种风格共用深色面板、圆角裁剪和角标。"""
    img = crop_avatar(style, w, h)
    css, body = "", [
        f'<clipPath id="artclip"><rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" rx="6"/></clipPath>',
        f'<g clip-path="url(#artclip)">',
        f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" fill="{c["panel"]}"/>',
    ]
    if style in ("image", "hybrid"):
        op = "1" if style == "image" else "0.5"
        body.append(f'<image x="{x}" y="{y}" width="{w:.1f}" height="{h}" opacity="{op}" '
                    f'preserveAspectRatio="xMidYMid slice" href="{image_href(img, w, h)}"/>')
    font = ART_FONT
    if style == "pixel":
        font = PIXEL_FONT
        runs, palette, rows, cols = ascii_runs(
            img, w, h, lift=0.42, font=PIXEL_FONT, lh=PIXEL_LH,
            ramp=" .,:;i1tfLCG08@", gamma=0.75)
        body.append(f'<image x="{x}" y="{y}" width="{w:.1f}" height="{h}" opacity="0.5" '
                    f'preserveAspectRatio="none" href="{mosaic_href(img, cols, rows, w, h)}"/>')
    elif style in ("hybrid", "ascii"):
        runs, palette, rows, cols = ascii_runs(img, w, h, lift=0.30 if style == "hybrid" else 0.0)
    if style in ("hybrid", "ascii", "pixel"):
        css += "".join(f".a{i}{{fill:{col}}}" for i, col in enumerate(palette))
        lh = h / rows
        body.append(f'<g font-size="{font}px" font-weight="bold">')
        for j, line in enumerate(runs):
            spans = "".join(f'<tspan class="a{ci}">{escape(t)}</tspan>' for ci, t in line)
            body.append(f'<text x="{x}" y="{y + j * lh + font - 1:.1f}" xml:space="preserve" '
                        f'textLength="{w:.1f}" lengthAdjust="spacing">{spans}</text>')
        body.append("</g>")
    # 扫描线 + 一条从上往下扫的光带（GitHub 里会动；静态渲染时光带在画面外）
    body += [
        f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" fill="url(#scan)"/>',
        f'<rect class="sweep" x="{x}" y="{y - 70}" width="{w:.1f}" height="70" fill="url(#beam)"/>',
        "</g>",
        f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" rx="6" fill="none" '
        f'stroke="{c["glow"]}" stroke-opacity="0.55"/>',
    ]
    k = 14  # 四角的 HUD 角标
    for cx_, cy_, sx, sy in ((x, y, 1, 1), (x + w, y, -1, 1), (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
        body.append(f'<path d="M{cx_ + sx * k:.1f} {cy_ - sy * 4:.1f}H{cx_ - sx * 4:.1f}V{cy_ + sy * k:.1f}" '
                    f'fill="none" stroke="{c["glow"]}" stroke-width="2"/>')
    css += (f"@keyframes sweep{{to{{transform:translateY({h + 70}px)}}}}"
            ".sweep{animation:sweep 6s linear infinite}")
    return css, body


# ---------------------------------------------------------------- 组装
def render(theme, style, stats, out_path):
    c = THEMES[theme]
    info = info_lines(stats) + [([], None), "prompt"]
    left = left_lines(stats)
    rows = max(len(info), ART_ROWS + 1 + len(left))
    art_w, info_w = ART_COLS * CW, INFO_COLS * CW
    art_h = min(rows, ART_ROWS) * LH
    info_x = PAD + art_w + GAP_COLS * CW
    width, height = round(info_x + info_w + PAD), PAD * 2 + rows * LH
    art_css, art_body = art_svg(style, c, PAD, PAD, art_w, art_h)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-size="{FONT}px" '
        "font-family=\"ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, "
        "'Liberation Mono', monospace\">",
        "<style>"
        f".fg{{fill:{c['fg']}}}.key{{fill:{c['key']}}}.val{{fill:{c['val']}}}"
        f".dot{{fill:{c['dot']}}}.star{{fill:{c['star']}}}"
        "text{white-space:pre}"
        "@keyframes blink{50%{opacity:0}}.cursor{animation:blink 1.1s steps(1) infinite}"
        + art_css + "</style>",
        "<defs>"
        '<pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse">'
        '<rect width="4" height="1" fill="#000" opacity="0.28"/></pattern>'
        '<linearGradient id="beam" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{c["glow"]}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{c["glow"]}" stop-opacity="0.22"/></linearGradient>'
        "</defs>",
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" '
        f'fill="{c["bg"]}" stroke="{c["border"]}"/>',
        *art_body,
    ]
    for i, line in enumerate(info):
        y = PAD + i * LH + FONT - 1
        if line == "prompt":
            prompt = f"oscar@{USER}:~$ "
            out.append(f'<text x="{info_x:.1f}" y="{y}" class="key" xml:space="preserve">{prompt}</text>')
            out.append(f'<rect class="cursor" x="{info_x + len(prompt) * CW:.1f}" y="{y - FONT + 3}" '
                       f'width="{CW:.1f}" height="{FONT}" fill="{c["fg"]}"/>')
            continue
        spans, star = line
        if not spans:
            continue
        w = info_w - (STAR_COLS * CW if star else 0)
        text = "".join(f'<tspan class="{cls}">{escape(t)}</tspan>' for cls, t in spans)
        out.append(f'<text x="{info_x:.1f}" y="{y}" xml:space="preserve" '
                   f'textLength="{w:.1f}" lengthAdjust="spacing">{text}</text>')
        if star:
            out.append(f'<text x="{info_x + info_w:.1f}" y="{y}" class="star" '
                       f'text-anchor="end">{escape(star)}</text>')
    for i, spans in enumerate(left):
        if not spans:
            continue
        y = PAD + (ART_ROWS + 1 + i) * LH + FONT - 1
        text = "".join(f'<tspan class="{cls}">{escape(t)}</tspan>' for cls, t in spans)
        out.append(f'<text x="{PAD}" y="{y}" xml:space="preserve" '
                   f'textLength="{art_w:.1f}" lengthAdjust="spacing">{text}</text>')
    out.append("</svg>")
    out_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return width, height, out_path.stat().st_size // 1024


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", choices=["photo", "dog", *CROPS], default=DEFAULT_ART)
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--all-styles", action="store_true")
    args = ap.parse_args()
    stats = fetch_stats(args.offline)
    if args.all_styles:
        (HERE / "variants").mkdir(exist_ok=True)
        for s in CROPS:
            for t in THEMES:
                print(s, t, render(t, s, stats, HERE / "variants" / f"{s}_{t}.svg"))
    else:
        for t in THEMES:
            print(args.art, t, render(t, args.art, stats, HERE / f"{t}_mode.svg"))
