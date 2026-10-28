# Profile art

The SVGs in `assets/` come from `build.py`. Each one has a light and a dark version, and the profile README picks
one to match the viewer's GitHub theme. The animation is CSS and SVG only, and it stops when the viewer has reduced
motion turned on.

| File | What it is |
| --- | --- |
| `head-*.svg` | "Should you hire Emil Fabel?", which rises and bulks up from thin to heavy like the headline on emil-fabel.vercel.app |
| `chart-*.svg` | Contributions per week over the last 12 months, redrawn every day at 02:00 UTC by `.github/workflows/daily.yml` |

```bash
python3 art/build.py    # needs a logged-in gh, or GH_TOKEN
```

All text is drawn as outlines from `glyphs.json`, so the SVGs need no web fonts. `glyphs.py` makes that file from the
Archivo variable font and only needs to run again to change the type styles or add characters.

`glyphs.json` holds outlines from Archivo, Copyright 2020 The Archivo Project Authors
(https://github.com/Omnibus-Type/Archivo), licensed under the SIL Open Font License 1.1 (https://openfontlicense.org).
