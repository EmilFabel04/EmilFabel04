"""Outlines Archivo into art/glyphs.json, so build.py (and the daily Action) never needs the font itself.

    python art/glyphs.py path/to/Archivo-variable.woff2    # needs fonttools, brotli and uharfbuzz

Only rerun this to change the styles or add characters. Archivo is by Omnibus-Type, under the SIL Open Font License.
"""
import io
import json
import sys
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

OUT = Path(__file__).resolve().parent / "glyphs.json"
# The headline matches the site (weight 880, width 66%) and starts from the thinnest weight so it can bulk up.
STYLES = {"head": (880, 66), "thin": (100, 66), "label": (640, 88)}
CHARS = ("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
         " ,.?!:;'’-–()%+/&")


class Recorder(BasePen):
    """Records each glyph as plain M/L/Q/C/Z segments in font units, y up."""

    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.d = []

    def _moveTo(self, p):
        self.d.append(["M", *p])

    def _lineTo(self, p):
        self.d.append(["L", *p])

    def _qCurveToOne(self, p1, p2):
        self.d.append(["Q", *p1, *p2])

    def _curveToOne(self, p1, p2, p3):
        self.d.append(["C", *p1, *p2, *p3])

    def _closePath(self):
        self.d.append(["Z"])


def main(src):
    data = io.BytesIO()
    font = TTFont(src)
    font.flavor = None
    font.save(data)
    face = hb.Face(data.getvalue())
    cmap = font.getBestCmap()
    missing = [c for c in CHARS if ord(c) not in cmap]
    if missing:
        sys.exit(f"Font has no glyph for: {''.join(missing)}")

    out = {"upem": font["head"].unitsPerEm, "styles": {}}
    for name, (wght, wdth) in STYLES.items():
        inst = instantiateVariableFont(TTFont(src), {"wght": wght, "wdth": wdth})
        glyphset = inst.getGlyphSet()
        hbfont = hb.Font(face)
        hbfont.set_variations({"wght": wght, "wdth": wdth})

        def shape(text):
            buf = hb.Buffer()
            buf.add_str(text)
            buf.guess_segment_properties()
            hb.shape(hbfont, buf, {"kern": True, "liga": False})
            return [p.x_advance for p in buf.glyph_positions]

        glyphs, kern = {}, {}
        for c in CHARS:
            pen = Recorder(glyphset)
            glyphset[inst.getBestCmap()[ord(c)]].draw(pen)
            glyphs[c] = {"adv": shape(c)[0], "d": [[s[0], *(round(v, 1) for v in s[1:])] for s in pen.d]}
        for a in CHARS:
            for b in CHARS:
                k = shape(a + b)[0] - glyphs[a]["adv"]
                if k:
                    kern[a + b] = k
        out["styles"][name] = {"glyphs": glyphs, "kern": kern}

    # The bulk-up morphs thin outlines into heavy ones, which only works if every segment lines up.
    for c in CHARS:
        ops = [[s[0] for s in out["styles"][n]["glyphs"][c]["d"]] for n in ("thin", "head")]
        if ops[0] != ops[1]:
            sys.exit(f"Thin and heavy outlines of {c!r} don't match, so they can't morph")

    OUT.write_text(json.dumps(out, separators=(",", ":")))
    print(f"Wrote {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main(sys.argv[1])
