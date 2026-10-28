"""Builds the profile SVGs into assets/, in a light and a dark version each.

    python3 art/build.py    # needs a logged-in `gh`, or GH_TOKEN (what the daily Action uses)

All text is drawn from art/glyphs.json (Archivo, the font on emil-fabel.vercel.app), so the SVGs look the same
everywhere and need no web fonts. The headline never changes; the chart is redrawn from live contribution data.
"""
import json
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
USER = "EmilFabel04"
FONT = json.loads((ROOT / "art" / "glyphs.json").read_text())

# Bull and bear colours from the site. Chart bars use darker or lighter versions so they keep 3:1 contrast.
THEMES = {
    "light": dict(ink="#1a1d24", muted="#59606c", rule="#d0d7de", bull="#f2a900", bear="#23395b",
                  up="#c48a00", down="#23395b"),
    "dark": dict(ink="#e8eaee", muted="#a2a9b5", rule="#30363d", bull="#f2a900", bear="#5b7bb0",
                 up="#f2a900", down="#5b7bb0"),
}
STILL = ("@media (prefers-reduced-motion: reduce) { * { animation: none !important; } .moving { display: none; } }\n"
         "@media (prefers-reduced-motion: no-preference) { .still { display: none; } }")
EASE = "cubic-bezier(.2,.8,.1,1)"


def svg(w, h, css, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
            f'aria-label="{label}">\n<style>\n{css}\n{STILL}\n</style>\n{body}\n</svg>\n')


def text(s, style, size, x, base, track=0.0, anchor="start"):
    """Outlines s as one path. Returns (path data, width)."""
    g, scale = FONT["styles"][style], size / FONT["upem"]
    width, prev = 0.0, None
    for c in s:
        width += (g["kern"].get(prev + c, 0) if prev else 0) * scale + g["glyphs"][c]["adv"] * scale + track * size
        prev = c
    width -= track * size
    pen = x - (width if anchor == "end" else width / 2 if anchor == "middle" else 0)
    d, prev = [], None
    for c in s:
        if prev:
            pen += g["kern"].get(prev + c, 0) * scale
        glyph = g["glyphs"][c]
        for op, *v in glyph["d"]:
            pts = [f"{pen + v[i] * scale:.1f} {base - v[i + 1] * scale:.1f}" for i in range(0, len(v), 2)]
            d.append(op + " ".join(pts))
        pen += glyph["adv"] * scale + track * size
        prev = c
    return "".join(d), width


# ---------------------------------------------------------------- headline
def head(t):
    """The site's question rises line by line and bulks up from thin to heavy, then the bull and bear bars meet."""
    W, size, lead = 840, 112, 114
    lines = ["Should you hire", "Emil Fabel?"]
    css = [f"""
.ink {{ fill: {t['ink']}; }}
.rise {{ animation: rise .9s {EASE} both; }}
@keyframes rise {{ from {{ transform: translateY({size}px); }} }}
.bar {{ transform-box: fill-box; animation: grow .8s 1.15s {EASE} both; }}
.bull {{ transform-origin: left; }} .bear {{ transform-origin: right; }}
@keyframes grow {{ from {{ transform: scaleX(0); }} }}"""]
    body, still = [], []
    for i, line in enumerate(lines):
        base = size * 0.84 + i * lead
        heavy, _ = text(line, "head", size, 0, base, track=-0.012)
        thin, _ = text(line, "thin", size, 0, base, track=0.02)
        delay = 0.1 + i * 0.12
        body.append(
            f'<clipPath id="l{i}"><rect x="-10" y="{base - size * 0.84 - 6:.0f}" width="{W + 20}" height="{size * 1.1 + 6:.0f}"/></clipPath>'
            f'<g clip-path="url(#l{i})"><g class="rise" style="animation-delay:{delay}s">'
            f'<path class="ink" d="{heavy}"><animate attributeName="d" values="{thin};{heavy}" dur="1.4s" begin="{delay}s" '
            f'calcMode="spline" keyTimes="0;1" keySplines=".3 .7 .1 1" fill="freeze"/></path></g></g>')
        still.append(f'<path class="ink" d="{heavy}"/>')
    y = size * 0.84 + lead + 34
    bars = (f'<rect class="bar bull" x="0" y="{y:.0f}" width="{W / 2}" height="12" fill="{t["bull"]}"/>'
            f'<rect class="bar bear" x="{W / 2}" y="{y:.0f}" width="{W / 2}" height="12" fill="{t["bear"]}"/>')
    return svg(W, int(y + 14), "\n".join(css),
               f'<g class="moving">{"".join(body)}</g>\n<g class="still">{"".join(still)}</g>\n{bars}',
               "Should you hire Emil Fabel?")


# ---------------------------------------------------------------- chart
def weeks():
    q = ('query { user(login: "%s") { contributionsCollection { contributionCalendar { totalContributions '
         'weeks { firstDay contributionDays { contributionCount } } } } } }' % USER)
    res = subprocess.run(["gh", "api", "graphql", "-f", f"query={q}"], capture_output=True, text=True, check=True)
    cal = json.loads(res.stdout)["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    rows = [(date.fromisoformat(w["firstDay"]), sum(d["contributionCount"] for d in w["contributionDays"]))
            for w in cal["weeks"]]
    return rows, cal["totalContributions"]


def chart(t, rows, total):
    """Contributions per week: amber when a week beat the one before, navy when it didn't, with a 4-week average."""
    W, H, top, base = 840, 330, 78, 262
    n, peak = len(rows), max(c for _, c in rows) or 1
    slot = W / n
    bw = slot * 0.66
    h = lambda c: (base - top) * c / peak
    css = [f"""
.ink {{ fill: {t['ink']}; }} .muted {{ fill: {t['muted']}; }}
.b {{ transform-box: fill-box; transform-origin: 50% 100%; animation: grow .55s {EASE} both; }}
@keyframes grow {{ from {{ transform: scaleY(0); }} }}
.avg {{ fill: none; stroke: {t['ink']}; stroke-width: 2.25; stroke-linejoin: round; stroke-linecap: round;
  stroke-dasharray: 1; animation: draw 1.2s 1.6s cubic-bezier(.5,0,.2,1) both; }}
@keyframes draw {{ from {{ stroke-dashoffset: 1; }} to {{ stroke-dashoffset: 0; }} }}"""]
    title, _ = text("Contributions per week", "label", 22, 0, 30)
    sub, _ = text(f"{total:,} in the last 12 months", "label", 15, 0, 54)
    body = [f'<path class="ink" d="{title}"/>', f'<path class="muted" d="{sub}"/>',
            f'<path d="M0 {base + .5} H{W}" stroke="{t["rule"]}"/>']

    best, _ = text(f"{peak:,}", "label", 12, W, top - 6, anchor="end")
    body.append(f'<path d="M0 {top + .5} H{W}" stroke="{t["rule"]}" stroke-dasharray="3 4"/><path class="muted" d="{best}"/>')

    for i, (day, c) in enumerate(rows):
        x = i * slot + (slot - bw) / 2
        up = i > 0 and c > rows[i - 1][1]
        bh = max(h(c), 2)
        body.append(f'<rect class="b" style="animation-delay:{.2 + i * .022:.3f}s" x="{x:.1f}" y="{base - bh:.1f}" '
                    f'width="{bw:.1f}" height="{bh:.1f}" fill="{t["up" if up else "down"]}"/>')
        if day.day <= 7 and i < n - 2:  # the first week that starts in a month carries its label
            m, _ = text(day.strftime("%b"), "label", 12, i * slot, base + 22)
            body.append(f'<path class="muted" d="{m}"/>')

    avg = [sum(c for _, c in rows[max(0, i - 3):i + 1]) / len(rows[max(0, i - 3):i + 1]) for i in range(n)]
    line = " L".join(f"{i * slot + slot / 2:.1f} {base - h(a):.1f}" for i, a in enumerate(avg))
    body.append(f'<path class="avg" pathLength="1" d="M{line}"/>')

    # Legend
    ly, x = H - 14, 0
    for kind, label in (("up", "Up on the week before"), ("down", "Down or flat"), ("avg", "4-week average")):
        if kind == "avg":
            body.append(f'<path d="M{x} {ly - 5} H{x + 22}" stroke="{t["ink"]}" stroke-width="2.25" stroke-linecap="round"/>')
            x += 30
        else:
            body.append(f'<rect x="{x}" y="{ly - 11}" width="11" height="11" fill="{t[kind]}"/>')
            x += 18
        d, w = text(label, "label", 14, x, ly)
        body.append(f'<path class="muted" d="{d}"/>')
        x += w + 26

    alt = (f"Bar chart of Emil's GitHub contributions per week over the last 12 months, {total:,} in total. "
           "Amber weeks were up on the week before, navy weeks were down or flat.")
    return svg(W, H, "\n".join(css), "\n".join(body), alt)


def main():
    rows, total = weeks()
    for name, t in THEMES.items():
        (ROOT / "assets" / f"head-{name}.svg").write_text(head(t))
        (ROOT / "assets" / f"chart-{name}.svg").write_text(chart(t, rows, total))
    print(f"Built assets/ from {len(rows)} weeks, {total:,} contributions")


if __name__ == "__main__":
    main()
