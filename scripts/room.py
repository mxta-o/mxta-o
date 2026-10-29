"""A pastel pixel room for the profile README: python scripts/room.py [--cached]

Drawn on a 480 x 340 grid of one-unit pixels (shown at 2x), with black outlines and soft colours.
Words come pre-rendered from lettering.json (see lettering.py); rerun that after changing any text.
"""
import datetime as dt
import html
import json
import sys
import zlib
from pathlib import Path

import data

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "room.svg"
LETTERING = Path(__file__).resolve().parent / "lettering.json"
W, H = 480, 340
EM = 128          # lettering units per em
DIGITS = "0123456789,"

# Dusk, after the profile picture: coral sky, dusty rose, cream, warm near-black lines
C = {
    "ink": "#241b20", "white": "#fbf1e6",
    "wall": "#d9b3ab", "wall_hi": "#c99f98", "base": "#9c6f6e", "floor": "#d8b9a5", "floor_lo": "#c6a28d",
    "wood": "#a97c78", "wood_hi": "#c49a92", "wood_lo": "#87605e", "shelf_back": "#5d4146",
    "sky0": "#a8899a", "sky1": "#cf8f8a", "sky2": "#e49a7c", "sky3": "#f1b98e", "sun": "#fde0b0",
    "city": "#5a3f4a", "lit": "#ffd59a", "glow": "#ffc79a",
    "cork": "#d7b08b", "cork_lo": "#c39a76", "paper": "#f8ebdd",
    "note_p": "#f2b3a3", "note_m": "#e0c9d0", "note_b": "#c7cad8",
    "case": "#eee2d4", "case_lo": "#ccb9a9", "screen": "#261d22", "dim": "#a08b8d",
    "heat": ["#3b2c32", "#74474b", "#ad5d57", "#de866b", "#ffc79a"],
    "cal_red": "#d0675a", "rug": "#e0a093", "rug_hi": "#f2c8bb", "rug_ink": "#7e3a36",
    "mug": "#fbf1e6", "pot": "#c0705f", "leaf": "#8f9a72", "duck": "#f3cf86",
    "cat": "#241c22", "cat_hi": "#3d2f38", "cat_eye": "#f1e4dc", "pink": "#e7a2a0", "red": "#c94a3f",
}

TITLE, SUBTITLE = "hey, i'm jaelan :)", "cs student @ yorku, toronto"
NOTES = [("note_p", ["full-stack", "@foregoneSI"]), ("note_m", ["next up:", "browsers,", "renderers"]),
         ("note_b", ["exploring", "c++,", "graphics,", "backends"])]
SHELVES = [
    ("languages", [("java", "#007396"), ("python", "#3776AB"), ("sql", "#4479A1"), ("c", "#A8B9CC"),
                   ("c++", "#00599C"), ("javascript", "#F7DF1E"), ("typescript", "#3178C6"), ("html", "#E34F26"),
                   ("css", "#1572B6")]),
    ("frameworks & libs", [("react", "#61DAFB"), ("expo", "#000020"), ("react native", "#61DAFB"),
                           ("fastapi", "#009688"), ("astro", "#FF5D01"), ("svelte", "#FF3E00"), ("three.js", "#000000"),
                           ("flask", "#000000"), ("tailwind css", "#06B6D4"), ("opengl", "#000000"), ("webgl", "#162236"),
                           ("gsap", "#162236"), ("formik", "#FF4154"), ("pydantic", "#4EA94B")]),
    ("data & tools", [("postgresql", "#4169E1"), ("sqlite", "#003B57"), None, ("git", "#F05032"),
                      ("github", "#181717"), ("aws", "#232F3E"), ("aws s3", "#569A31"), ("cognito", "#FF9900"),
                      ("docker", "#2496ED"), ("maven", "#C71A36"), ("figma", "#F24E1E"), ("notion", "#000000")]),
]
RUG = ["got questions or wanna be friends?", "come say hi :)"]
LABELS = ["streak", "days", "record!", "best:", "~ $ git stats", "contributions this year", "all time", "z"]


def static_strings():
    return {TITLE, SUBTITLE, *RUG, *LABELS, *(l for _, ls in NOTES for l in ls),
            *(n for n, _ in SHELVES), *(b[0] for _, bs in SHELVES for b in bs if b)}


# ---- lettering ------------------------------------------------------------

_lettering = None


def glyphs(s):
    global _lettering
    if _lettering is None:
        _lettering = json.loads(LETTERING.read_text(encoding="utf-8"))
    if s in _lettering:
        return [_lettering[s]]
    if all(c in _lettering for c in s):
        return [_lettering[c] for c in s]
    raise KeyError(f"{s!r} isn't in lettering.json: run python scripts/lettering.py")


def width(s, size):
    return sum(g["w"] for g in glyphs(s)) * size / EM


def say(s, x, y, size, fill="ink", anchor="start", cls=""):
    """Text with its baseline at y."""
    x -= {"start": 0, "middle": width(s, size) / 2, "end": width(s, size)}[anchor]
    out, k = [], size / EM
    for g in glyphs(s):
        out.append(f'<path d="{g["d"]}" transform="translate({x:g} {y:g}) scale({k:g})"/>')
        x += g["w"] * k
    c = f' class="{cls}"' if cls else ""
    return f'<g{c} fill="{C.get(fill, fill)}" shape-rendering="geometricPrecision">{"".join(out)}</g>'


# ---- pixels ---------------------------------------------------------------

def rect(x, y, w, h):
    return f"M{x:g} {y:g}h{w:g}v{h:g}h{-w:g}z"


def p(d, fill, cls="", extra=""):
    c = f' class="{cls}"' if cls else ""
    return f'<path{c} d="{d}" fill="{C.get(fill, fill)}"{extra}/>'


def obox(x, y, w, h, fill):
    """A filled box with a one-pixel ink outline."""
    return p(rect(x, y, w, h), "ink") + p(rect(x + 1, y + 1, w - 2, h - 2), fill)


def bits(rows, x, y, ch="#"):
    d = []
    for j, row in enumerate(rows):
        i = 0
        while i < len(row):
            if row[i] == ch:
                k = i
                while k < len(row) and row[k] == ch:
                    k += 1
                d.append(rect(x + i, y + j, k - i, 1))
                i = k
            else:
                i += 1
    return "".join(d)


def sprite(rows, x, y, palette, cls=""):
    body = "".join(p(bits(rows, x, y, ch), colour) for ch, colour in palette.items())
    return f'<g class="{cls}">{body}</g>' if cls else body


def mix(a, b, f):
    """Blend hex colour a toward b by f."""
    ca, cb = ([int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in (a, b))
    return "#" + "".join(f"{round(x + (y - x) * f):02x}" for x, y in zip(ca, cb))


def shade(hexc, f):
    """Mix a hex colour toward white (f > 0) or black (f < 0)."""
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    mix = (lambda v: v + (255 - v) * f) if f > 0 else (lambda v: v * (1 + f))
    return "#" + "".join(f"{round(mix(v)):02x}" for v in (r, g, b))


# ---- the room -------------------------------------------------------------

def wall():
    out = [p(rect(0, 0, W, 262), "wall"),
           f'<rect width="{W}" height="256" fill="url(#tone)"/>',
           p(rect(0, 256, W, 6), "base"), p(rect(0, 255, W, 1), "ink"),
           p(rect(0, 262, W, H - 262), "floor"),
           p("".join(rect(0, y, W, 1) for y in range(270, H, 9))
             + "".join(rect((j * 71 + (y // 9) * 37) % W, y - 8, 1, 8) for y in range(270, H + 9, 9) for j in range(4)),
             "floor_lo")]
    return "".join(out)


def sunlight():
    """Late light from the window, slanting across the wall."""
    return p("M18 110L106 110L176 256L88 256Z", "glow", extra=' opacity=".22"')


def floorlight():
    return p("M88 262L176 262L198 280L104 280Z", "glow", extra=' opacity=".3"')


BULB = ["..#####..", ".#ooooo#.", "#ooo#ooo#", "#oo#.#oo#", "#ooo#ooo#", ".#ooooo#.", "..#ooo#..", "...###..."]
RAYS = ["#...........#", ".#.........#.", ".............", ".............", "##.........##",
        ".............", ".............", ".#.........#.", "#...........#"]


def bulb():
    x = 121
    return (p(rect(x, 0, 1, 40), "ink") + p(rect(x - 2, 40, 5, 4), "ink")
            + sprite(BULB, x - 4, 44, {"#": "ink", "o": "lit"}) + p(bits(RAYS, x - 6, 43), "ink", "rays"))


def window():
    x0, y0, w, h = 14, 24, 96, 80
    gx, gy, gw, gh = x0 + 4, y0 + 4, w - 8, h - 8
    out = [obox(x0, y0, w, h, "wood"),
           p(rect(gx, gy, gw, 16), "sky0"), p(rect(gx, gy + 16, gw, 16), "sky1"), p(rect(gx, gy + 32, gw, 16), "sky2"),
           p(rect(gx, gy + 48, gw, gh - 48), "sky3"),
           p(bits(["....#####....", "..#########..", ".###########.", "#############", "#############"], gx + 52, gy + 38), "sun")]
    bird = ["#...#", ".#.#."]
    out.append(p(bits(bird, gx + 14, gy + 10) + bits(bird, gx + 24, gy + 16), "city", "birds"))
    base = gy + gh
    blocks = [(0, 16), (8, 24), (16, 12), (30, 30), (38, 20), (48, 34), (58, 18), (66, 28), (76, 14), (82, 22)]
    sky, lit = [], []
    for i, (bx, bh) in enumerate(blocks):
        bw = (blocks[i + 1][0] if i + 1 < len(blocks) else gw) - bx
        sky.append(rect(gx + bx, base - bh, bw, bh))
        lit += [(xx, yy) for yy in range(base - bh + 2, base - 1, 3) for xx in range(gx + bx + 1, gx + bx + bw - 1, 2)
                if zlib.crc32(f"{xx},{yy}".encode()) % 5 == 0]
    tx = gx + 24
    tower = rect(tx, gy + 12, 1, 7) + rect(tx - 1, gy + 19, 3, base - gy - 19) + rect(tx - 3, gy + 34, 7, 3) + rect(tx - 2, gy + 27, 5, 1)
    out.append(p("".join(sky) + tower, "city"))
    out.append(p("".join(rect(x, y, 1, 1) for x, y in lit), "lit"))
    out.append(p(rect(tx, gy + 11, 1, 1), "lit", "beacon"))
    out.append(p(rect(x0 + w // 2 - 2, y0, 4, h) + rect(x0, y0 + h // 2 - 2, w, 4), "ink"))
    out.append(p(rect(x0 + w // 2 - 1, y0 + 1, 2, h - 2) + rect(x0 + 1, y0 + h // 2 - 1, w - 2, 2), "wood"))
    out.append(obox(x0 - 5, y0 + h, w + 10, 6, "wood_hi"))
    return "".join(out)


def corkboard():
    x0, y0, w, h = 132, 16, 154, 102
    out = [obox(x0, y0, w, h, "wood"), p(rect(x0 + 4, y0 + 4, w - 8, h - 8), "ink"), p(rect(x0 + 5, y0 + 5, w - 10, h - 10), "cork"),
           p("".join(rect(x, y, 1, 1) for x in range(x0 + 8, x0 + w - 6, 6) for y in range(y0 + 8 + x % 4, y0 + h - 6, 5)), "cork_lo")]
    cx, cy, cw, ch = x0 + 10, y0 + 10, w - 20, 38
    mid = x0 + w // 2
    out += [p(rect(cx + 2, cy + 2, cw, ch), "cork_lo"), obox(cx, cy, cw, ch, "paper"),
            say(TITLE, mid, cy + 19, 17, anchor="middle"), say(SUBTITLE, mid, cy + 32, 10, "dim", anchor="middle"),
            p(rect(mid - 2, cy - 2, 4, 4), "red")]
    nw, gap = 42, 5
    nx = x0 + (w - (3 * nw + 2 * gap)) // 2
    for i, (colour, lines) in enumerate(NOTES):
        ny = cy + ch + 7 + (2, 0, 1)[i]
        nh = 44
        out += [p(rect(nx + 2, ny + 2, nw, nh), "cork_lo"), obox(nx, ny, nw, nh, colour)]
        top = ny + (nh - len(lines) * 11) // 2 + 8
        out += [say(t, nx + nw / 2, top + j * 11, 9.5, anchor="middle") for j, t in enumerate(lines)]
        out.append(p(rect(nx + nw // 2 - 2, ny - 2, 4, 3), ("red", "#7d6f8f", "#8f9a72")[i]))
        nx += nw + gap
    return "".join(out)


def book(label, colour, x, floor, room):
    """An upright book on floor with its title down the spine, in a pastel of its badge colour."""
    if colour.lower() in ("#000000", "#181717", "#000020", "#162236", "#232f3e", "#003b57"):
        colour = "#6d6266"
    face = mix(colour, "#d4b8aa", .62)
    h = min(room, int(width(label, 9)) + 12 + zlib.crc32(label.encode()) % 4)
    y = floor - h
    return (obox(x, y, 11, h + 1, face) + p(rect(x + 1, y + 3, 9, 1) + rect(x + 1, floor - 4, 9, 1), mix(colour, "#d4b8aa", .4))
            + f'<g transform="translate({x + 3} {y + (h - width(label, 9)) / 2:.1f}) rotate(90)">{say(label, 0, 0, 9)}</g>')


DUCK = ["..###...", ".#ooo#..", "#oo.oo#.", "#ooooo###", ".#ooooo#.", "..#####.."]


def bookshelf():
    x0, y0, w, comp, board = 292, 50, 182, 58, 11
    total = 6 + 3 * (comp + board)
    out = [obox(x0, y0, w, total, "wood"), p(rect(x0 - 3, y0 - 1, w + 6, 5), "ink"), p(rect(x0 - 2, y0, w + 4, 3), "wood_hi")]
    y = y0 + 6
    for name, books in SHELVES:
        floor = y + comp
        out.append(obox(x0 + 4, y - 1, w - 8, comp + 2, "shelf_back"))
        x = x0 + 6
        for b in books:
            if b is None:
                out.append(obox(x, floor - 16, 3, 16, "#cbb9b0") + obox(x, floor - 3, 7, 3, "#cbb9b0"))
                x += 9
                continue
            out.append(book(*b, x, floor, comp - 4))
            x += 12
        if name == "languages":
            out.append(sprite(DUCK, x + 32, floor - 6, {"#": "ink", "o": "duck"}) + p(rect(x + 37, floor - 4, 1, 1), "ink"))
            out.append(p(rect(x + 12, floor - 7, 9, 7), "ink") + p(rect(x + 13, floor - 6, 7, 6), "pot")
                       + p(bits(["#.#.#", ".###.", "..#.."], x + 14, floor - 11), "leaf"))
        out.append(say(name, x0 + w / 2, floor + 9, 9, "ink", anchor="middle"))
        y = floor + board
    out.append(p(rect(x0 + 3, y0 + total, 8, 6) + rect(x0 + w - 11, y0 + total, 8, 6), "ink"))
    return "".join(out)


# Mewo, flat out asleep: k body, w inner ears and closed eyes
CAT = [
    "..................k........k...",
    ".................kk.......kk...",
    "................kwk......kwk...",
    "...............kwwk.....kwwk...",
    "..............kwwwk....kwwwk...",
    "............kkkkkkkkkkkkkkkkk..",
    "...........kkkkkkkkkkkkkkkkkkk.",
    "..........kkkkkkkkkkkkkkkkkkkk.",
    "..........kkkkkkkkkkkkkkkkkkkk.",
    "..........kkkkkkkkkkkkkkkkkkkk.",
    "..........kkkkkkkkkkkkkkkkkkkk.",
    "..........kkkkkkkkkkkkkkkkkkkk.",
    ".kk.......kkkkkkkkkkkkkkkkkkkk.",
    "kkkkkkkkkkkkkkkkkkkkkkkkkkkkkk.",
    "kkkkkkkkkkkkkkkkkkkkkkkkkkkkkk.",
    ".kkkkkkkkkkkkkkwwwkkkkkkwwwkkk.",
    "..........kkkkkkkkkkkkkkkkkkkk.",
    "...........kkkkkkkkkkkkkkkkkk..",
]


def cat(x, y):
    top = y - len(CAT)
    breath = p(rect(x + 19, top + 4, 4, 1), "cat")
    return (sprite(CAT, x, top, {"k": "cat", "w": "cat_eye"})
            + f'<g class="breath">{breath}</g>'
            + "".join(say("z", x + 20 + i * 6, top - 4 - i * 7, 9 + i * 2, "ink", cls=f"z z{i}") for i in range(3)))


def calendar(s):
    x0, y0, w, h = 14, 118, 48, 70
    mid = x0 + w / 2
    best = say("record!", mid, y0 + 63, 9.5, "cal_red", "middle") if s["current"] >= s["longest"] and s["current"] else (
        say("best:", mid - 2, y0 + 63, 9.5, "cal_red", "end") + say(str(s["longest"]), mid + 1, y0 + 63, 9.5, "cal_red"))
    return (p(rect(mid, y0 - 5, 1, 5), "ink") + obox(x0, y0, w, h, "paper") + obox(x0, y0, w, 14, "cal_red")
            + p(rect(x0 + 8, y0 - 2, 2, 4) + rect(x0 + w - 10, y0 - 2, 2, 4), "ink")
            + say("streak", mid, y0 + 11, 10, "white", "middle")
            + say(str(s["current"]), mid, y0 + 38, 24, "ink", "middle") + say("days", mid, y0 + 49, 10, "dim", "middle")
            + p(rect(x0 + 6, y0 + 53, w - 12, 1), "case_lo") + best)


def monitor(s, days):
    x0, y0, w, h = 70, 122, 160, 72
    sx, sy, sw, sh = x0 + 5, y0 + 5, w - 10, h - 13
    tx = sx + 5
    out = [obox(x0, y0, w, h, "case"), p(rect(x0 + 1, y0 + h - 4, w - 2, 3), "case_lo"),
           obox(x0 + 66, y0 + h - 1, 28, 6, "case_lo"), p(rect(x0 + w - 12, y0 + h - 3, 3, 1), "leaf"),
           obox(sx - 1, sy - 1, sw + 2, sh + 2, "screen"),
           say("~ $ git stats", tx, sy + 10, 9, "dim"),
           p(rect(tx + width("~ $ git stats", 9) + 2, sy + 3, 4, 8), "white", "cursor"),
           say("all time", sx + sw - 5 - width(f"{s['total']:,}", 9) - 4, sy + 10, 9, "dim", "end"),
           say(f"{s['total']:,}", sx + sw - 5, sy + 10, 9, "white", "end")]
    big = f"{s['last_year']:,}"
    out += [say(big, tx, sy + 31, 21, "white"), say("contributions this year", tx + width(big, 21) + 4, sy + 31, 9.5, "white")]
    weeks = (sw - 8) // 3
    today = s["today"]
    start = today - dt.timedelta(days=(today.weekday() + 1) % 7 + 7 * (weeks - 1))
    counts = sorted(n for n in days.values() if n)
    cuts = [counts[len(counts) * q // 4] for q in (1, 2, 3)] if counts else [1, 2, 3]
    cells = [[] for _ in C["heat"]]
    for i in range((today - start).days + 1):
        n = days.get((start + dt.timedelta(days=i)).isoformat(), 0)
        cells[0 if not n else 1 + sum(n > c for c in cuts)].append(rect(tx + (i // 7) * 3, sy + 37 + (i % 7) * 3, 2, 2))
    out.append('<g class="heat">' + "".join(p("".join(c), col) for c, col in zip(cells, C["heat"]) if c) + "</g>")
    return "".join(out)


TISSUE = ["..##.....", ".#oo#.##.", "#oooo#oo#", "#ooooooo#"]


def desk():
    top = 200
    out = [obox(8, top, 278, 7, "wood_hi"),
           obox(12, top + 6, 52, 64, "wood"), obox(16, top + 11, 44, 25, "wood_hi"), obox(16, top + 40, 44, 25, "wood_hi"),
           p(rect(35, top + 22, 6, 2) + rect(35, top + 51, 6, 2), "ink"),
           obox(274, top + 6, 9, 64, "wood")]
    # Sketchbook and pencil under the calendar
    out += [obox(18, top - 6, 34, 6, "white"), p(rect(19, top - 5, 32, 1), "red"),
            p("".join(rect(20 + i * 4, top - 7, 2, 2) for i in range(8)), "ink"),
            obox(40, top - 9, 18, 3, "duck"), p(rect(56, top - 8, 2, 1), "ink")]
    # Tissue box, mug with steam
    out += [obox(236, top - 13, 20, 13, "note_b"), p(rect(237, top - 9, 18, 1), "#aeb1c3"),
            sprite(TISSUE, 241, top - 17, {"#": "ink", "o": "white"})]
    mx = 262
    out += [obox(mx, top - 11, 11, 11, "mug"), p(rect(mx + 11, top - 9, 3, 1) + rect(mx + 13, top - 8, 1, 4) + rect(mx + 11, top - 5, 3, 1), "ink"),
            p(rect(mx + 3, top - 7, 2, 2) + rect(mx + 6, top - 7, 2, 2) + rect(mx + 3, top - 5, 5, 1) + rect(mx + 4, top - 4, 3, 1), "pink")]
    out += [p(rect(mx + 3 + i * 2, top - 17, 1, 3) + rect(mx + 4 + i * 2, top - 20, 1, 3), "white", f"steam st{i}")
            for i in range(3)]
    return "".join(out)


def rug():
    x0, y0, w, h = 56, 284, 236, 44
    mid = x0 + w / 2
    body = rect(x0 + 2, y0, w - 4, h) + rect(x0, y0 + 2, w, h - 4)
    inner = rect(x0 + 3, y0 + 1, w - 6, h - 2) + rect(x0 + 1, y0 + 3, w - 2, h - 6)
    stitch = "".join(rect(x, y0 + 4, 3, 1) + rect(x, y0 + h - 5, 3, 1) for x in range(x0 + 6, x0 + w - 6, 6))
    return (p(body, "ink") + p(inner, "rug") + p(stitch, "rug_hi")
            + say(RUG[0], mid, y0 + 20, 12, anchor="middle") + say(RUG[1], mid, y0 + 34, 12, "rug_ink", "middle"))


CSS = """
.rays{animation:flick 4s steps(1) infinite}@keyframes flick{40%{opacity:0}46%{opacity:1}52%{opacity:0}58%{opacity:1}}
.star{animation:twinkle 3s steps(1) infinite}.s1{animation-delay:-1s}.s2{animation-delay:-2s}
@keyframes twinkle{70%{opacity:.2}}
.beacon,.cursor{animation:blink 1.4s steps(1) infinite}@keyframes blink{50%{opacity:0}}
.breath{animation:breath 3.2s steps(1) infinite}@keyframes breath{50%{opacity:0}}
.z{animation:drift 3.6s linear infinite}.z1{animation-delay:-1.2s}.z2{animation-delay:-2.4s}
@keyframes drift{0%{opacity:0;transform:translate(-4px,10px)}30%{opacity:1}100%{opacity:0;transform:translate(3px,-3px)}}
.steam{animation:steam 2.4s steps(6) infinite}.st1{animation-delay:-.8s}.st2{animation-delay:-1.6s}
@keyframes steam{0%{opacity:0;transform:translate(0,3px)}40%{opacity:.9}100%{opacity:0;transform:translate(0,-5px)}}
.heat{animation:reveal 2s steps(47,end) .4s both}
@keyframes reveal{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""


def build(refresh=True):
    days = data.load_days(refresh)
    s = data.stats(days)
    alt = (f"A pixel room at dusk. Corkboard: {TITLE} {SUBTITLE}. Notes: full-stack web dev; next up, cloud eng; "
           f"exploring C++, Java, Node.js. A wall calendar counts a {s['current']}-day streak (best {s['longest']}). "
           f"The monitor shows {s['last_year']:,} contributions this year and {s['total']:,} all time. Bookshelf: "
           + "; ".join(f"{n}: " + ", ".join(b[0] for b in bs if b) for n, bs in SHELVES)
           + ". A black cat sleeps on top under a hanging lightbulb, and sunset light falls through the window. Rug: " + " ".join(RUG))
    body = [wall(), sunlight(), window(), corkboard(), bulb(), calendar(s), desk(), monitor(s, days), bookshelf(),
            cat(330, 50), floorlight(), rug()]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W * 2}" height="{H * 2}" '
           f'role="img" shape-rendering="crispEdges">\n<title>{html.escape(alt)}</title>\n<style>{CSS}</style>\n'
           f'<defs><pattern id="tone" width="6" height="6" patternUnits="userSpaceOnUse">'
           f'<path d="M1 1h1v1h-1zM4 4h1v1h-1z" fill="{C['wall_hi']}"/></pattern><clipPath id="round"><rect width="{W}" height="{H}" rx="6"/></clipPath></defs>\n'
           f'<g clip-path="url(#round)">{"".join(body)}</g>\n</svg>\n')
    OUT.write_text(svg, encoding="utf-8")
    return s


if __name__ == "__main__":
    print(build(refresh="--cached" not in sys.argv))
