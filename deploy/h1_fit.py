"""Measures how wide each hero H1 line (span.b1, the keyword line, and span.b2, the green line) must be, in em, to wrap
into at most two rows, and writes the width into the language sources as --fit on <h1>. The CSS sizes both H1 lines with
min(1em, 100cqi / var(--fit)): the breakpoint size stays unless a line would need a third row, and both lines keep one
size. The keyword line always gets its two rows. The green line gets them only while that does not make the H1 smaller
than the smallest H1 the keyword lines already need (the largest keyword-line width over all languages); past that it
keeps its third row instead of shrinking the heading further.

Run after changing H1 copy, against a served build of the current sources:
    python3 deploy/build.py <dist> && (cd <dist> && python3 -m http.server 8822) &
    python3 deploy/h1_fit.py http://127.0.0.1:8822
Needs the Python Playwright package with Chromium, like deploy/og.js needs the Node one.
"""

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

SRC = Path(__file__).resolve().parents[1]
CONF = json.loads((SRC / "deploy" / "langs.json").read_text())
PROBE_PX = 100
SAFETY = 1.02
MAX_LINES = 2
KEYWORD, GREEN = "b1", "b2"

MEASURE = """([cls, px, maxLines]) => {
  const h1 = document.querySelector('.hero h1'), el = h1.querySelector('.' + cls);
  const lines = () => { const r = document.createRange(); r.selectNodeContents(el); return new Set([...r.getClientRects()].map(q => Math.round(q.top))).size; };
  let lo = px, hi = px * 40;
  while (hi - lo > 1) { const mid = (lo + hi) / 2; h1.style.width = mid + 'px'; if (lines() <= maxLines) hi = mid; else lo = mid; }
  return hi / px;
}"""


def main(base):
    found = {}
    need = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        for l in CONF["langs"]:
            pg = b.new_page(viewport={"width": 1440, "height": 900})
            pg.goto(f"{base}/{l['code']}/?still", wait_until="load")
            pg.evaluate("document.fonts.ready")
            pg.add_style_tag(
                content=f".hero h1{{font-size:{PROBE_PX}px!important;max-width:none!important;animation:none!important}}"
                ".hero h1 .b1,.hero h1 .b2{font-size:1em!important;animation:none!important}"
            )
            need[l["code"]] = {
                span: round(pg.evaluate(MEASURE, [span, PROBE_PX, MAX_LINES]) * SAFETY, 2)
                for span in (KEYWORD, GREEN)
            }
            pg.close()
        b.close()
    floor = max(n[KEYWORD] for n in need.values())
    for code, n in need.items():
        found[code] = max(n[KEYWORD], n[GREEN]) if n[GREEN] <= floor else n[KEYWORD]
    for l in CONF["langs"]:
        path = SRC / l["file"]
        html, n = re.subn(
            r'<h1(?: style="--fit:[0-9.]+")?>(?=<span class="b1")',
            f'<h1 style="--fit:{found[l["code"]]}">',
            path.read_text(),
            count=1,
        )
        if n != 1:
            sys.exit(f"{l['file']}: hero <h1> with span.b1 not found")
        path.write_text(html)
        n = need[l["code"]]
        print(l["code"], found[l["code"]], f"(keyword {n[KEYWORD]}, green {n[GREEN]}{', green keeps 3 rows' if n[GREEN] > found[l['code']] else ''})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8822")
