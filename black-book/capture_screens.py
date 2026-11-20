"""Plots of the dashboard for Chapter 7 of the black book.

Start the dashboard on localhost first (from the repository root):

    streamlit run examples/dashboard/app.py --server.headless true --server.address 127.0.0.1 --server.port 8599

then run `python paper/black-book/make_figures.py --screens`. Headless Chromium is driven over
the DevTools protocol, as in examples/paper/capture_dashboard.py. Only the plots are kept:
every Plotly chart between one step heading and the next is drawn again with Plotly.toImage
at a larger font, placed where the dashboard places it, and the white space left by the text
in between is closed up. The CLEAR-10 maps are drawn from the images the dashboard shows;
the overview keeps only its headline numbers and the strip of steps. Written at twice the
CSS resolution to paper/black-book/figures/ui_*.png.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

from PIL import Image, ImageChops

URL = "http://127.0.0.1:8599/"
OUT = Path(__file__).resolve().parent / "figures"
WIDTH, HEIGHT, SCALE = 1100, 16000, 2
PLOT_W, FONT, GAP = 860, 14, 28      # width of a figure in CSS px, chart font in px, gap between rows
CAM_DIR = Path(__file__).resolve().parents[2] / "outputs" / "figures" / "cam"

HIDE = ("(()=>{const s=document.createElement('style'); s.textContent='.modebar-container,.modebar{display:none"
        " !important} header[data-testid=stHeader],[data-testid=stToolbar]{display:none !important}';"
        " document.head.appendChild(s);})()")

# (file, tab, heading the shot starts at, heading it stops before or "" for the end of the tab)
SHOTS = [
    ("ui_overview", "ACS (census)", "Data Drift Autopsy", "1. Initial setup"),
    ("ui_setup", "ACS (census)", "1. Initial setup", "Measured accuracy"),
    ("ui_cbpe", "ACS (census)", "2a.", "2b."),
    ("ui_detection", "ACS (census)", "2b.", "2c."),
    ("ui_localization", "ACS (census)", "2c.", "3. Root cause"),
    ("ui_shap", "ACS (census)", "3a.", "3b."),
    ("ui_diagnosis", "ACS (census)", "3b.", "4."),
    ("ui_reliability", "ACS (census)", "4.", "5."),
    ("ui_remediation", "ACS (census)", "5.", "Did the triage"),
    ("ui_clear", "CLEAR-10 (images)", "3a.", "3b."),
    ("ui_bench_type", "Injection benchmark", "6. Drift type", "7. Baselines"),
    ("ui_bench_baselines", "Injection benchmark", "7. Baselines", "8. Per-prediction"),
]

REGION = """(()=>{
  const vis = e => e.offsetParent !== null && e.getBoundingClientRect().height > 0;
  const hs = [...document.querySelectorAll('h1,h2,h3,h4')].filter(vis);
  const a = hs.find(e => e.textContent.trim().startsWith(%s));
  if (!a) return null;
  const top = a.getBoundingClientRect().top + window.scrollY;
  let bottom = null;
  const stop = %s;
  if (stop) {
    const all = [...document.querySelectorAll('h1,h2,h3,h4,summary,p')].filter(vis);
    const b = all.find(e => e.textContent.trim().startsWith(stop) && e.getBoundingClientRect().top + window.scrollY > top + 5);
    if (b) bottom = b.getBoundingClientRect().top + window.scrollY;
  }
  if (bottom === null) {
    const panel = a.closest('[role=tabpanel]') || document.body;
    bottom = panel.getBoundingClientRect().bottom + window.scrollY;
  }
  return [0, top - 10, %d, bottom - top + 4];
})()"""


# every chart in the region, drawn again at width PLOT_W for the full content width
PLOTS = """(async()=>{
  const vis = e => e.offsetParent !== null && e.getBoundingClientRect().height > 0;
  const r = %s; if (!r) return null;
  const top = r[1], bottom = r[1] + r[3];
  const divs = [...document.querySelectorAll('.js-plotly-plot')].filter(vis).filter(d => {
    const t = d.getBoundingClientRect().top + window.scrollY; return t >= top && t < bottom; });
  if (!divs.length) return null;
  const left = Math.min(...divs.map(d => d.getBoundingClientRect().left));
  const right = Math.max(...divs.map(d => d.getBoundingClientRect().right));
  const k = %d / (right - left), out = [];
  for (const d of divs) {
    const b = d.getBoundingClientRect();
    const lay = JSON.parse(JSON.stringify(d.layout));
    const fam = 'Liberation Sans, Arial, sans-serif';   // measured and drawn in the same font
    lay.font = Object.assign({}, lay.font || {}, {size: %d, family: fam});
    const w = Math.round(b.width * k), h = Math.round(b.height * k);
    Object.assign(lay, {width: w, height: h, autosize: false});
    // a title or a horizontal legend wider than a narrow chart is set smaller instead of cut off
    const fit = (text, size, extra) => Math.max(9, Math.min(size, Math.floor((w - extra) / (0.56 * text.length))));
    const title = lay.title && (typeof lay.title === 'string' ? lay.title : lay.title.text);
    if (title) {
      const plain = String(title).replace(/<[^>]*>/g, '');
      const t = typeof lay.title === 'string' ? {text: lay.title} : lay.title;
      lay.title = Object.assign({}, t, {font: Object.assign({}, t.font || {}, {family: fam, size: fit(plain, (t.font && t.font.size) || %d + 3, 20)})});
    }
    const names = d.data.filter(t => t.showlegend !== false && t.name).map(t => String(t.name).replace(/<[^>]*>/g, ''));
    if (names.length && (!lay.legend || lay.legend.orientation === 'h')) {
      const text = names.join('').length + 7 * names.length;
      lay.legend = Object.assign({}, lay.legend || {}, {font: Object.assign({}, (lay.legend && lay.legend.font) || {}, {family: fam, size: fit('x'.repeat(text), %d, 30)})});
    }
    lay.margin = Object.assign({}, lay.margin || {}, {r: ((lay.margin && lay.margin.r) || 20) + 30});
    const url = await Plotly.toImage({data: d.data, layout: lay}, {format: 'png', width: w, height: h, scale: %d});
    out.push([Math.round((b.left - left) * k), Math.round((b.top + window.scrollY - top) * k), w, h, url]);
  }
  return out;
})()"""


def compose(parts) -> Image.Image:
    """Charts placed where the dashboard puts them, with the space left by text closed up."""
    s = SCALE
    height = max(y + h for _, y, _, h, _ in parts) * s
    canvas = Image.new("RGB", (PLOT_W * s, height), "white")
    for x, y, _, _, url in parts:
        canvas.paste(Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1]))).convert("RGB"), (x * s, y * s))
    # rows that hold no chart become at most GAP px high
    covered = [False] * height
    for _, y, _, h, _ in parts:
        for r in range(y * s, (y + h) * s):
            covered[r] = True
    rows, run = [], 0
    for r in range(height):
        run = 0 if covered[r] else run + 1
        if covered[r] or run <= GAP * s:
            rows.append(r)
    out = Image.new("RGB", (canvas.width, len(rows)), "white")
    for i, r in enumerate(rows):
        out.paste(canvas.crop((0, r, canvas.width, r + 1)), (0, i))
    return out


def cam_grid() -> Image.Image:
    """The CLEAR-10 class activation maps as the dashboard shows them: image, then its map."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    cam = json.loads((CAM_DIR / "cam_manifest.json").read_text())
    n = len(cam["images"])
    fig, axes = plt.subplots(2, n, figsize=(2.1 * n, 4.6), dpi=200)
    for j, im in enumerate(cam["images"]):
        ok = "correct" if im["predicted"] == im["true"] else "wrong"
        for row, key in enumerate(("image_png", "overlay_png")):
            ax = axes[row, j]
            ax.imshow(Image.open(CAM_DIR / im[key]))
            ax.set_xticks([]), ax.set_yticks([])
        axes[0, j].set_title(f"predicted {im['predicted']}\ntrue {im['true']} ({ok})", fontsize=11)
        axes[1, j].set_xlabel(f"OOD score {im['ood_unclipped']:.1f}", fontsize=11)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor="white")
    plt.close(fig)
    return Image.open(buf).convert("RGB")


async def capture() -> None:
    prof = tempfile.mkdtemp()
    proc = subprocess.Popen(["chromium", "--headless=new", "--remote-debugging-port=9334", f"--user-data-dir={prof}",
                             "--hide-scrollbars", f"--window-size={WIDTH},{HEIGHT}", "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import websockets
    try:
        for _ in range(50):
            try:
                tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9334/json"))
                ws_url = next(t["webSocketDebuggerUrl"] for t in tabs if t["type"] == "page")
                break
            except Exception:
                time.sleep(0.2)
        async with websockets.connect(ws_url, max_size=2 ** 29) as ws:
            n = 0

            async def call(method, **params):
                nonlocal n
                n += 1
                await ws.send(json.dumps({"id": n, "method": method, "params": params}))
                while True:
                    msg = json.loads(await ws.recv())
                    if msg.get("id") == n:
                        return msg.get("result", {})

            async def js(expr):
                res = await call("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
                return res["result"].get("value")

            await call("Emulation.setDeviceMetricsOverride", width=WIDTH, height=HEIGHT, deviceScaleFactor=SCALE,
                       mobile=False)
            await call("Page.navigate", url=URL)
            await asyncio.sleep(25)
            await js(HIDE)
            current = "ACS (census)"
            for name, tab, start, stop in SHOTS:
                if tab != current:
                    await js("[...document.querySelectorAll('button[role=tab]')].find(b=>b.textContent.includes(%s)).click()"
                             % json.dumps(tab))
                    await asyncio.sleep(20)
                    current = tab
                region_js = REGION % (json.dumps(start), json.dumps(stop), WIDTH)
                if name == "ui_clear":
                    im = cam_grid()
                elif name == "ui_overview":     # headline numbers and the strip of steps only
                    box = await js("""(()=>{const r=%s; if(!r) return null;
                      const els=[...document.querySelectorAll('[data-testid=stMetric],[data-testid=stGraphVizChart]')]
                        .filter(e=>e.offsetParent!==null).map(e=>e.getBoundingClientRect())
                        .filter(b=>b.top+window.scrollY>=r[1] && b.top+window.scrollY<r[1]+r[3]);
                      if(!els.length) return null;
                      const l=Math.min(...els.map(b=>b.left)), t=Math.min(...els.map(b=>b.top))+window.scrollY;
                      return [l-8, t-8, Math.max(...els.map(b=>b.right))-l+16, Math.max(...els.map(b=>b.bottom))+window.scrollY-t+16];
                    })()""" % region_js)
                    if not box:
                        print(f"  {name}: heading '{start}' not found")
                        continue
                    shot = await call("Page.captureScreenshot", format="png", captureBeyondViewport=True,
                                      clip={"x": box[0], "y": box[1], "width": box[2], "height": box[3], "scale": 1})
                    im = Image.open(io.BytesIO(base64.b64decode(shot["data"]))).convert("RGB")
                else:
                    parts = await js(PLOTS % (region_js, PLOT_W, FONT, FONT, FONT, SCALE))
                    if not parts:
                        print(f"  {name}: no plots under '{start}'")
                        continue
                    im = compose(parts)
                box = ImageChops.difference(im, Image.new("RGB", im.size, "white")).getbbox()
                if box:
                    im = im.crop((max(box[0] - 16, 0), max(box[1] - 16, 0),
                                  min(box[2] + 16, im.width), min(box[3] + 16, im.height)))
                im.save(OUT / f"{name}.png")
                print(f"  {name}: {im.size[0]} x {im.size[1]} px")
    finally:
        proc.terminate()


def main() -> None:
    asyncio.run(capture())


if __name__ == "__main__":
    main()
