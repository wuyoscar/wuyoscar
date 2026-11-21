# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""README 项目表格里的像素小图标：icons/<仓库名>.svg。

    uv run make_icons.py     # 重新生成全部图标

每个图标是一张 16x16 的像素图，一个字符一个像素，"." 透明，其他字符的颜色在各自的调色板里。
在 README 里按 32px 显示（一格正好 2px）。要加图标：在 ICONS 里加一项（仓库名 -> 调色板、16 行）。
图标是静态文件，改了这里才需要重新生成；每天的 Action 不会跑这个脚本。
"""
from pathlib import Path

HERE = Path(__file__).parent
N = 16

ICONS = {
    # 画框里的风景
    "GPT-Image2-Skill": ({"P": "#7048e8", "S": "#d0ebff", "Y": "#ffd43b", "G": "#51cf66", "g": "#2f9e44"}, [
        "................",
        "................",
        ".PPPPPPPPPPPPPP.",
        ".PSSSSSSSSSSSSP.",
        ".PSSYYSSSSSSSSP.",
        ".PSSYYSSSSSSSSP.",
        ".PSSSSSSSSgSSSP.",
        ".PSSSSSSSgggSSP.",
        ".PSSSGSSgggggSP.",
        ".PSSGGGgggggggP.",
        ".PSGGGGGggggggP.",
        ".PGGGGGGGgggggP.",
        ".PGGGGGGGGggggP.",
        ".PPPPPPPPPPPPPP.",
        "................",
        "................"]),
    # 裂开的盾牌
    "Internal-Safety-Collapse": ({"D": "#c92a2a", "R": "#fa5252", "L": "#ffa8a8", "W": "#ffffff"}, [
        "................",
        ".......DD.......",
        ".....DDRWDD.....",
        "..DDDRRRWRRDDD..",
        "..DLLRRWWRRRRD..",
        "..DLRRRWRRRRRD..",
        "..DLRRRWWRRRRD..",
        "..DRRRRRWWRRRD..",
        "..DRRRRRRWRRRD..",
        "..DRRRRRWWRRRD..",
        "...DRRRRWRRRD...",
        "...DRRRRRRRRD...",
        "....DRRRRRRD....",
        ".....DRRRRD.....",
        "......DRRD......",
        ".......DD......."]),
    # 火焰
    "AISafetyHot": ({"R": "#e8590c", "O": "#ff922b", "Y": "#ffd43b", "W": "#fff3bf"}, [
        "................",
        ".......R........",
        ".......RR.......",
        "......ROR.......",
        "......ROOR......",
        ".....ROOOR..R...",
        ".....ROOOOR.RR..",
        "..R.ROOYOORROR..",
        "..RRROOYYOOOOR..",
        "..ROROYYYYOOOR..",
        "..ROOOYYWYYOOR..",
        "..ROOYYWWYYOOR..",
        "..ROOYYWWWYOOR..",
        "...ROOYWWYYOR...",
        "....RROOOORR....",
        "......RRRR......"]),
    # 拼图块
    "jev-skill": ({"G": "#2b8a3e", "L": "#51cf66", "H": "#b2f2bb"}, [
        "................",
        "......GGGG......",
        ".....GHLLLG.....",
        ".....GLLLLG.....",
        "..GGGGGLLGGGGG..",
        "..GLLLLLLLLLLG..",
        "..GGGLLLLLLLLGGG",
        "....GLLLLLLLLLLG",
        "....GLLLLLLLLLLG",
        "..GGGLLLLLLLLGGG",
        "..GLLLLLLLLLLG..",
        "..GLLLGGGGLLLG..",
        "..GLLLG..GLLLG..",
        "..GGGGG..GGGGG..",
        "................",
        "................"]),
    # 摊开的书
    "Awesome-Large-Model-Safety": ({"D": "#1864ab", "B": "#339af0", "W": "#ffffff", "S": "#d0d7de", "T": "#74c0fc"}, [
        "................",
        "................",
        "................",
        ".DDDDDD..DDDDDD.",
        "DWWWWWWDDWWWWWWD",
        "DWTTTTWSSWTTTTWD",
        "DWWWWWWSSWWWWWWD",
        "DWTTTTWSSWTTTTWD",
        "DWWWWWWSSWWWWWWD",
        "DWTTTWWSSWTTTWWD",
        "DWWWWWWSSWWWWWWD",
        "DWWWWWWSSWWWWWWD",
        "DBBBBBBDDBBBBBBD",
        ".DDDDDDDDDDDDDD.",
        "................",
        "................"]),
    # 蟹钳
    "XSafeClaw": ({"D": "#087f5b", "C": "#20c997", "L": "#96f2d7"}, [
        "................",
        "....DDDD...DD...",
        "...DCCCCD.DCCD..",
        "..DCCCCCD..DCCD.",
        ".DCCLCCD....DCD.",
        ".DCLCCCD...DCCD.",
        ".DCLCCCD..DCCCD.",
        ".DCCCCCCDDCCCCD.",
        ".DCCCCCCCCCCCD..",
        "..DCCCCCCCCCCD..",
        "..DCCCCCCCCCD...",
        "...DDCCCCCDD....",
        ".....DCCD.......",
        "....DCCD........",
        "...DCCD.........",
        "...DDD.........."]),
    # 两张叠着的图文卡片
    "Vibepost": ({"P": "#e64980", "W": "#ffffff", "L": "#ffc9d6", "R": "#ff8fab", "T": "#faa2c1"}, [
        "................",
        ".....PPPPPPPPPP.",
        ".....PLLLLLLLLP.",
        ".PPPPPPPPPPLLLP.",
        ".PWWWWWWWWPLLLP.",
        ".PWRRRRRRWPLLLP.",
        ".PWRRRRRRWPLLLP.",
        ".PWRRRRRRWPLLLP.",
        ".PWRRRRRRWPLLLP.",
        ".PWWWWWWWWPLLLP.",
        ".PWTTTTTTWPLLLP.",
        ".PWWWWWWWWPLLLP.",
        ".PWTTTTWWWPPPPP.",
        ".PWWWWWWWWP.....",
        ".PPPPPPPPPP.....",
        "................"]),
    # 带问号的对话气泡
    "JustAsk": ({"A": "#f08c00", "Y": "#fff3bf", "D": "#d9480f"}, [
        "................",
        "...AAAAAAAAAA...",
        "..AYYYYYYYYYYA..",
        ".AYYYYDDDDYYYYA.",
        ".AYYYDDYYDDYYYA.",
        ".AYYYYYYYDDYYYA.",
        ".AYYYYYYDDYYYYA.",
        ".AYYYYYDDYYYYYA.",
        ".AYYYYYYYYYYYYA.",
        ".AYYYYYDDYYYYYA.",
        "..AYYYYYYYYYYA..",
        "...AAAYYAAAAA...",
        ".....AYYA.......",
        ".....AYA........",
        ".....AA.........",
        "................"]),
    # 论文，上面一个箭头
    "arxiv2agent": ({"I": "#4c6ef5", "W": "#ffffff", "F": "#bac8ff", "T": "#bac8ff", "O": "#ff922b"}, [
        "..IIIIIIII......",
        "..IWWWWWWIFI....",
        "..IWWWWWWIFFI...",
        "..IWTTTTWIIIII..",
        "..IWWWWWWWWWWI..",
        "..IWTTTTTTTTWI..",
        "..IWWWWWWWWWWI..",
        "..IWTTTTTTTTWI..",
        "..IWWWWWWWWWWI..",
        "..IWWWWWWOWWWI..",
        "..IWWWWWWOOWWI..",
        "..IWOOOOOOOOWI..",
        "..IWWWWWWOOWWI..",
        "..IWWWWWWOWWWI..",
        "..IWWWWWWWWWWI..",
        "..IIIIIIIIIIII.."]),
    # 鱼钩
    "scamworld-bench": ({"D": "#1098ad", "S": "#99e9f2"}, [
        ".........DDD....",
        "........D...D...",
        "........D...D...",
        ".........DDD....",
        ".........DSD....",
        ".........DSD....",
        ".........DSD....",
        ".........DSD....",
        "..D......DSD....",
        "..DD.....DSD....",
        "..DSD....DSD....",
        "..DSSD...DSD....",
        "..DSD...DSSD....",
        "..DSSDDDDSSD....",
        "...DSSSSSSD.....",
        "....DDDDDD......"]),
    # 放大镜里一个对勾
    "VEX-Bench": ({"V": "#7048e8", "L": "#e5dbff", "G": "#2f9e44", "H": "#5f3dc4"}, [
        "................",
        "....VVVVVV......",
        "..VVLLLLLLVV....",
        ".VVLLLLLLLLVV...",
        ".VLLLLLLLGLLV...",
        "VVLLLLLLGGLLVV..",
        "VLLLGLLGGLLLLV..",
        "VLLLGGGGLLLLLV..",
        "VVLLLGGLLLLLVV..",
        ".VLLLLLLLLLLV...",
        ".VVLLLLLLLLVV...",
        "..VVLLLLLLVVHH..",
        "....VVVVVV.HHH..",
        "............HHH.",
        ".............HHH",
        "..............HH"]),
}


def icon_svg(colors, grid):
    assert len(grid) == N and all(len(r) == N for r in grid), [len(r) for r in grid]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{N * 2}" height="{N * 2}" '
           f'viewBox="0 0 {N} {N}" shape-rendering="crispEdges">']
    for y, row in enumerate(grid):
        x = 0
        while x < N:               # 同一行里相邻的同色像素合并成一个 rect
            ch, x1 = row[x], x
            while x1 < N and row[x1] == ch:
                x1 += 1
            if ch != ".":
                out.append(f'<rect x="{x}" y="{y}" width="{x1 - x}" height="1" fill="{colors[ch]}"/>')
            x = x1
    out.append("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    out = HERE / "icons"
    out.mkdir(exist_ok=True)
    for name, (colors, grid) in ICONS.items():
        (out / f"{name}.svg").write_text(icon_svg(colors, grid), encoding="utf-8")
    print("icons written:", len(ICONS))
