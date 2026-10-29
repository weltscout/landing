// Renders img/og/<code>.jpg (1200x630) for every language from that language's own page, so the share image carries the
// page's current brand: the wordmark, the hero H1 (its second sentence in the hero's green), the trial pill and the
// hero's WhatsApp phone with its real alert (the mobile.de car, 24.840 €). No app screenshot: the app still shows the
// old logo. The page is loaded with font-display:block so Geist is always the face in the image (the site itself uses
// optional). build.py publishes each image under a name with a hash of its bytes.
// Run: NODE_PATH=<dir with playwright>/node_modules node deploy/og.js
const { chromium } = require("playwright");
const fs = require("fs"), os = require("os"), path = require("path");
const SRC = path.resolve(__dirname, ".."), CONF = JSON.parse(fs.readFileSync(path.join(__dirname, "langs.json")));
const W = 1200, H = 630, TITLE_MAX = 64, TITLE_MIN = 56;

const compose = ({ W, H, TITLE_MAX, TITLE_MIN }) => {
  const $ = s => document.querySelector(s), txt = e => e.textContent.replace(/\s+/g, " ").trim();
  const b1 = $(".hero h1 .b1"), b2 = $(".hero h1 .b2"), pills = [...document.querySelectorAll(".hero .offer-pts .nocard")], phone = $(".hero .waph"), logo = $("img.lg-l");
  if (!b1 || !b2 || pills.length < 2 || !phone || !logo) throw new Error("og: hero H1, trial pills, WhatsApp phone or logo not found");
  const green = getComputedStyle(b2).color;
  const og = document.createElement("div"); og.className = "og";
  og.innerHTML = `<style>
html,body{overflow:hidden!important}
body>*:not(.og){display:none!important}
.og{position:fixed;left:0;top:0;width:${W}px;height:${H}px;z-index:2147483647;overflow:hidden;color:var(--tx);font-family:Geist,'Geist Fallback',system-ui,sans-serif;
  background:radial-gradient(560px 560px at 935px 380px,color-mix(in oklch,var(--acc) 20%,transparent),transparent 70%),var(--pg)}
.og-lg{position:absolute;left:64px;top:56px;height:40px;width:auto}
.og-copy{position:absolute;left:64px;top:144px;bottom:56px;width:660px;display:flex;flex-direction:column;justify-content:center}
.og h1{margin:0;font-weight:600;letter-spacing:-.035em;line-height:1.06;text-wrap:balance}
.og h1 span{display:block}
.og h1 .og-b2{margin-top:.14em;color:${green};font-weight:700}
.og-pill{align-self:flex-start;display:inline-flex;align-items:center;gap:12px;margin:36px 0 0;padding:10px 24px 10px 20px;border-radius:999px;background:var(--ok-hi);color:var(--ok-ink);font-size:26px;font-weight:700;line-height:1.3;white-space:nowrap}
.og-pill:before{content:"✓";font-weight:700}
.og-ph{position:absolute;right:60px;top:60px;zoom:1.42}
.og-ph .waph{position:relative;inset:auto;margin:0}
.og-ph .waph-btn{visibility:hidden}
</style><img class="og-lg" alt=""><div class="og-copy"><h1><span class="og-b1"></span><span class="og-b2"></span></h1><p class="og-pill"></p></div><div class="og-ph"></div>`;
  og.querySelector(".og-lg").src = logo.currentSrc || logo.src;
  og.querySelector(".og-b1").textContent = txt(b1); og.querySelector(".og-b2").textContent = txt(b2);
  og.querySelector(".og-pill").textContent = pills.map(txt).join(" · ");
  og.querySelector(".og-ph").append(phone.cloneNode(true));
  document.body.append(og);
  const copy = og.querySelector(".og-copy"), h1 = og.querySelector("h1");
  let size = TITLE_MAX;
  for (; size >= TITLE_MIN; size -= 2) { h1.style.fontSize = size + "px"; if (copy.scrollHeight <= copy.clientHeight && h1.scrollWidth <= h1.clientWidth) break; }
  if (size < TITLE_MIN) throw new Error(`og: the title does not fit at ${TITLE_MIN}px`);
  const ph = og.querySelector(".og-ph").getBoundingClientRect(), cp = copy.getBoundingClientRect();
  if (ph.left < cp.right + 24) throw new Error("og: the phone overlaps the title column");
  return { size, lines: Math.round(h1.getBoundingClientRect().height / (size * 1.06)), pill: og.querySelector(".og-pill").textContent };
};

(async () => {
  const b = await chromium.launch(), p = await b.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1, colorScheme: "light" });
  for (const l of CONF.langs) {
    const src = fs.readFileSync(path.join(SRC, l.file), "utf8").replace("<head>", `<head><base href="file://${SRC}/">`).replace(/font-display:\s*optional/g, "font-display:block");
    const f = path.join(os.tmpdir(), `og-src-${l.code}.html`); fs.writeFileSync(f, src);
    await p.goto(`file://${f}?still&theme=light`, { waitUntil: "load" });
    await p.evaluate(() => document.fonts.ready);
    const r = await p.evaluate(compose, { W, H, TITLE_MAX, TITLE_MIN });
    await p.evaluate(() => Promise.all([document.fonts.ready, ...[...document.querySelectorAll(".og img")].map(i => i.decode().catch(() => {}))]));
    const geist = await p.evaluate(() => [...document.fonts].some(x => x.family.replace(/"/g, "") === "Geist" && x.status === "loaded"));
    if (!geist) throw new Error(`${l.code}: Geist did not load`);
    await p.screenshot({ path: path.join(SRC, "img/og", l.code + ".jpg"), type: "jpeg", quality: 88 });
    console.log(l.code, r);
  }
  await b.close();
})().catch(e => { console.error(e.message); process.exit(1); });
