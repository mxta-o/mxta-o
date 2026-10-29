"""Bake the room's text into outlines: python scripts/lettering.py (needs fonttools and the local font).

The OMORI font isn't committed (it's OMOCAT's), so every string room.py prints is pre-rendered here
into scripts/lettering.json as path data, plus digits for the live numbers. Rerun after changing text.
"""
import json
import re
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

import room

FONT = room.ROOT / "assets" / "fonts" / "OMORI_GAME2.ttf"
OUT = Path(__file__).resolve().parent / "lettering.json"


def main():
    font = TTFont(FONT)
    glyphs, cmap, hmtx = font.getGlyphSet(), font.getBestCmap(), font["hmtx"]
    k = room.EM / font["head"].unitsPerEm

    def outline(text):
        pen, x = SVGPathPen(glyphs), 0
        for c in text:
            name = cmap[ord(c)]
            glyphs[name].draw(TransformPen(pen, (k, 0, 0, -k, x, 0)))
            x += hmtx[name][0] * k
        d = re.sub(r"-?\d+\.\d+", lambda m: str(round(float(m.group()))), pen.getCommands())
        return {"d": d, "w": round(x, 1)}

    out = {s: outline(s) for s in sorted(room.static_strings() | set(room.DIGITS))}
    OUT.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print(f"{len(out)} strings -> {OUT.name} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
