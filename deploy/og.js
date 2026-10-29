// Renders img/og/<code>.jpg (1200x630) from each language page's <title> (build.py derives og:title from it). Run: NODE_PATH=<dir with playwright>/node_modules node deploy/og.js
const { chromium } = require("playwright");
const fs = require("fs"), os = require("os"), path = require("path");
const SRC = path.resolve(__dirname, ".."), CONF = JSON.parse(fs.readFileSync(path.join(__dirname, "langs.json")));
const esc = s => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
(async () => {
  const b = await chromium.launch(), p = await b.newPage({ viewport: { width: 1200, height: 630 } });
  for (const l of CONF.langs) {
    const h = fs.readFileSync(path.join(SRC, l.file), "utf8");
    const t = h.match(/<title>([^<]+)<\/title>/)[1].replace(/&amp;/g, "&").replace(/^WeltScout[\s ]*:\s*/, "").replace(/\s*\|\s*WeltScout$/, "").replace(/^./, c => c.toLocaleUpperCase());
    const html = `<!doctype html><meta charset=utf-8><style>
@font-face{font-family:Geist;src:url(file://${SRC}/fonts/geist-latin.woff2);font-weight:400 700;unicode-range:U+0000-00FF,U+2000-206F,U+20AC}
@font-face{font-family:Geist;src:url(file://${SRC}/fonts/geist-latin-ext.woff2);font-weight:400 700;unicode-range:U+0100-02FF,U+1E00-1EFF}
*{margin:0;box-sizing:border-box}body{width:1200px;height:630px;overflow:hidden;font-family:Geist,sans-serif;color:#fff;background:linear-gradient(135deg,#00122E,#253650 55%,#002A82);position:relative}
img.lg{position:absolute;left:64px;top:56px;height:40px}
h1{position:absolute;left:64px;top:190px;width:500px;font-size:56px;line-height:1.12;font-weight:600;letter-spacing:-.02em}
.sc{position:absolute;left:620px;top:120px;width:640px;border-radius:18px 0 0 0;border:1px solid rgba(255,255,255,.18);box-shadow:0 30px 80px rgba(0,0,0,.45)}
</style><img class=lg src="file://${SRC}/img/logo-weltscout-t2-dark.svg"><h1>${esc(t)}</h1><img class=sc src="file://${SRC}/img/08-results-v2.webp">`;
    const f = path.join(os.tmpdir(), `og-${l.code}.html`); fs.writeFileSync(f, html);
    await p.goto("file://" + f); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(200);
    await p.screenshot({ path: path.join(SRC, "img/og", l.code + ".jpg"), type: "jpeg", quality: 86 });
  }
  await b.close();
})();
