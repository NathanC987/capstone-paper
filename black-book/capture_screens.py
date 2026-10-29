"""Screenshots of the dashboard for Chapter 7 of the black book.

Start the dashboard on localhost first (from the repository root):

    streamlit run examples/dashboard/app.py --server.headless true --server.address 127.0.0.1 --server.port 8599

then run `python paper/black-book/make_figures.py --screens`. Headless Chromium is driven over
the DevTools protocol, as in examples/paper/capture_dashboard.py: each screenshot is the
part of a tab from one step heading to the next, at twice the CSS resolution, written to
paper/black-book/figures/ui_*.png.
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
                return (await call("Runtime.evaluate", expression=expr, returnByValue=True))["result"].get("value")

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
                region = await js(REGION % (json.dumps(start), json.dumps(stop), WIDTH))
                if not region:
                    print(f"  {name}: heading '{start}' not found")
                    continue
                x, y, w, h = region
                shot = await call("Page.captureScreenshot", format="png", captureBeyondViewport=True,
                                  clip={"x": x, "y": y, "width": w, "height": h, "scale": 1})
                im = Image.open(io.BytesIO(base64.b64decode(shot["data"]))).convert("RGB")
                box = ImageChops.difference(im, Image.new("RGB", im.size, "white")).getbbox()
                if box:
                    im = im.crop((max(box[0] - 16, 0), 0, min(box[2] + 16, im.width), im.height))
                im.save(OUT / f"{name}.png")
                print(f"  {name}: {im.size[0]} x {im.size[1]} px")
    finally:
        proc.terminate()


def main() -> None:
    asyncio.run(capture())


if __name__ == "__main__":
    main()
