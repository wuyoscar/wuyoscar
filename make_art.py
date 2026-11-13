# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow"]
# ///
"""python.png（抠好背景的照片）-> 字符画数据 art.json，供 build.py 使用。

只在换照片或调参数时手动跑一次；每周的 Action 不需要它。

    uv run make_art.py                       # 按默认参数生成 art.json
    uv run make_art.py --cols 46 --crop 0.74 # 调列数 / 取景（保留照片上方多少比例）
    uv run make_art.py --sheet               # 生成多组参数的对比图 variants/sheet.svg
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageOps

HERE = Path(__file__).parent
GLYPH_ASPECT = 0.602   # 等宽字体：字符宽 / 字号
LINE = 1.18            # 字符画行高 / 字号（略紧，画面才连得起来）

THEME_BG = {"dark": (0x16, 0x1B, 0x22), "light": (0xF6, 0xF8, 0xFA)}
# 一份字符，两套颜色。下标：0 = 眼睛/鼻子/嘴，1..6 = 毛从暗到亮，7 = 舌头
PALETTE = {
    "dark": ["#56606e", "#a8702f", "#c98a35", "#e3a548", "#f2bf68", "#f8d592", "#fde9c0", "#f58ea4"],
    "light": ["#2e1a0c", "#6f451a", "#8a5a22", "#a5702b", "#bd8636", "#cf9a48", "#dcae62", "#c2506a"],
}
FUR_CHARS = "=+*#%@"       # 毛：暗 -> 亮，字符越来越密
COAT = 0.55                # 分层时毛色深浅占多少比重（0 = 只看明暗）
SMOOTH = 0.9               # 分层前先模糊多少（单位：一个字符格），越大色块越整
FEATURE_CHAR = "@"         # 眼睛/鼻子/嘴：实心深色，而不是留空（留空在深色底上像窟窿）
FEATURE_BELOW = 78         # 原图亮度低于它算五官


def convert(cols, crop, eq=0.75):
    """返回 {"cols", "rows", "line", "lines"}；lines 的每行是 [[调色板下标, 文本], ...]。

    像 neofetch 的 logo 那样用成片的彩色字符“画”出来：
    - 毛：只在狗身上做直方图均衡，把一身浅色的毛拉成 6 档明暗，每档一个字符 + 一个金色
    - 五官：原图里真正的暗部，用实心字符 + 深棕色
    - 舌头：按色相单独挑出来，粉色
    """
    img = Image.open(HERE / "python.png").convert("RGBA")
    img = img.crop((0, 0, img.width, int(img.height * crop)))
    rows = round(cols * GLYPH_ASPECT * img.height / img.width / LINE)
    mask = img.getchannel("A").point(lambda v: 255 if v >= 128 else 0)
    rgb = img.convert("RGB")
    gray = rgb.convert("L")
    fur_mask = ImageChops.multiply(mask, gray.point(lambda v: 255 if v >= FEATURE_BELOW else 0))
    # 先模糊再分层：同一档明暗连成整片色块（像 logo），而不是一粒一粒的噪点
    # 分层依据 = 明暗 + 毛色深浅（饱和度）：耳朵比脸更金，会落到更深的档，而不只是跟着光影走
    blur = ImageFilter.GaussianBlur(SMOOTH * img.width / cols)
    soft = gray.filter(blur)
    pale = ImageChops.invert(rgb.convert("HSV").getchannel("S")).filter(blur)
    score = Image.blend(ImageOps.equalize(soft, mask=fur_mask), ImageOps.equalize(pale, mask=fur_mask), COAT)
    tone = Image.blend(soft, ImageOps.equalize(score, mask=fur_mask), eq)
    hsv = rgb.convert("HSV")
    tongue = ImageChops.multiply(ImageChops.multiply(
        hsv.getchannel("H").point(lambda h: 255 if (h > 228 or h < 10) else 0),
        hsv.getchannel("S").point(lambda s: 255 if s > 75 else 0)), mask)

    size, box = (cols, rows), Image.Resampling.BOX
    m = mask.resize(size, box).tobytes()
    g = gray.resize(size, box).tobytes()
    t = tone.resize(size, box).tobytes()
    tg = tongue.resize(size, box).tobytes()
    n = len(FUR_CHARS)
    lines = []
    for y in range(rows):
        runs = []
        for x in range(cols):
            i = y * cols + x
            if m[i] < 128:
                ch, ci = " ", (runs[-1][0] if runs else 0)
            elif tg[i] > 100:
                ch, ci = FEATURE_CHAR, n + 1
            elif g[i] < FEATURE_BELOW + 12:
                ch, ci = FEATURE_CHAR, 0
            else:
                k = min(n - 1, int(t[i] / 256 * n))
                ch, ci = FUR_CHARS[k], k + 1
            if runs and runs[-1][0] == ci:
                runs[-1][1] += ch
            else:
                runs.append([ci, ch])
        lines.append(runs)
    return {"cols": cols, "rows": rows, "line": LINE, "lines": lines}


def art_text_svg(art, theme, x, y, width, prefix):
    """把一份字符画排成 SVG 片段（宽度固定为 width），返回 (css, 片段, 高度)。build.py 用同一套逻辑。"""
    from xml.sax.saxutils import escape
    font = width / (art["cols"] * GLYPH_ASPECT)
    lh = font * art["line"]
    css = "".join(f".{prefix}{i}{{fill:{col}}}" for i, col in enumerate(PALETTE[theme]))
    out = [f'<g font-size="{font:.2f}px" font-weight="bold">']
    for j, runs in enumerate(art["lines"]):
        if not "".join(t for _, t in runs).strip():
            continue
        spans = "".join(f'<tspan class="{prefix}{ci}">{escape(t)}</tspan>' for ci, t in runs)
        out.append(f'<text x="{x:.1f}" y="{y + j * lh + font * 0.82:.1f}" xml:space="preserve" '
                   f'textLength="{width:.1f}" lengthAdjust="spacing">{spans}</text>')
    out.append("</g>")
    return css, out, art["rows"] * lh


def sheet():
    """多组参数排成一张对比图。"""
    variants = [(c, crop, th) for th in ("dark", "light") for c, crop in ((46, 0.74), (46, 0.92), (56, 0.92))]
    W, pad, cell_w, cell_h = 420, 24, 420 + 24, 560
    css, body = "", []
    for i, (c, crop, th) in enumerate(variants):
        art = convert(c, crop)
        col, row = i % 3, i // 3
        x, y = pad + col * cell_w, pad + 20 + row * (cell_h + 10)
        bg = "#%02x%02x%02x" % THEME_BG[th]
        k, frag, _ = art_text_svg(art, th, x, y, W, f"v{i}c")
        css += k
        body.append(f'<rect x="{x - 10}" y="{y - 26}" width="{W + 20}" height="{cell_h}" fill="{bg}"/>')
        body.append(f'<text x="{x}" y="{y - 10}" font-size="11" fill="#8b949e">'
                    f'{th} cols={c} crop={crop} rows={art["rows"]}</text>')
        body += frag
    width, height = pad * 2 + 3 * cell_w, 24 + 2 * (cell_h + 10) + 10
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
           f'font-family="Menlo, monospace"><style>text{{white-space:pre}}{css}</style>'
           f'<rect width="100%" height="100%" fill="#30363d"/>' + "\n".join(body) + "</svg>")
    (HERE / "variants").mkdir(exist_ok=True)
    (HERE / "variants" / "sheet.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cols", type=int, default=46)
    ap.add_argument("--crop", type=float, default=0.84)
    ap.add_argument("--sheet", action="store_true")
    args = ap.parse_args()
    if args.sheet:
        sheet()
    else:
        art = convert(args.cols, args.crop)
        art["palette"] = PALETTE
        (HERE / "art.json").write_text(json.dumps(art, ensure_ascii=False, separators=(",", ":")) + "\n")
        print(art["cols"], art["rows"])
