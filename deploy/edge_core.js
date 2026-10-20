// Pure routing core for the Bunny middleware. Generated into the deployed
// script by deploy/edge_script.py and executed directly (in node) by
// deploy/test_edge_script.py. No imports and no platform APIs: requests come
// in as plain objects, decisions go out as plain objects.
//
// The contract is Vercel semantics (dist/vercel.json), as translated by
// deploy/aws.py: redirects first-match-wins in rule order (301 permanent /
// 302 temporary), cleanUrls answers 301, unknown constructs are fatal in the
// generator — never silently ignored.
"use strict";

// Port of deploy/api/contact.js — same status matrix:
// 405 method, 400 bad JSON, 200 honeypot, 422 validation, 503 not_configured,
// 502 send_failed, 200 ok.
const TOPICS = { preizkus: "Preizkus", enterprise: "Business MAX za ekipo", portal: "Nov portal", drugo: "Drugo" };
const MAX = { name: 120, company: 160, email: 200, tel: 40, msg: 4000 };
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

async function contact(req, deps) {
  const respond = (status, body, headers) => ({ type: "response", status, headers: headers || {}, body });
  if (req.method !== "POST") return respond(405, { ok: false }, { Allow: "POST" });
  let b = req.body || {};
  if (typeof b === "string") {
    try { b = JSON.parse(b); } catch (e) { return respond(400, { ok: false, error: "json" }); }
  }
  if (b.website) return respond(200, { ok: true });
  const f = {};
  for (const k of Object.keys(MAX)) f[k] = String(b[k] || "").trim().slice(0, MAX[k]);
  const topic = TOPICS[b.topic] ? b.topic : "drugo";
  if (!f.name || !f.msg || !EMAIL_RE.test(f.email) || b.consent !== true) {
    return respond(422, { ok: false, error: "invalid" });
  }
  const env = deps.env || {};
  if (!env.RESEND_API_KEY || !env.CONTACT_FROM) return respond(503, { ok: false, error: "not_configured" });
  const lang = String(b.lang || "sl").slice(0, 2);
  const rows = [["Ime", f.name], ["Podjetje", f.company], ["E-pošta", f.email], ["Telefon", f.tel], ["Zanima ga", TOPICS[topic]], ["Jezik strani", lang]];
  const html = `<table>${rows.map(([k, v]) => `<tr><td><b>${k}</b></td><td>${esc(v || "–")}</td></tr>`).join("")}</table><p>${esc(f.msg).replace(/\n/g, "<br>")}</p>`;
  const sent = await deps.sendEmail({
    from: env.CONTACT_FROM,
    to: [env.CONTACT_TO || "info@weltscout.com"],
    reply_to: f.email,
    subject: `WeltScout kontakt: ${TOPICS[topic]} · ${f.name}`,
    html,
    text: rows.map(([k, v]) => `${k}: ${v || "–"}`).join("\n") + "\n\n" + f.msg,
  });
  if (!sent || sent.ok !== true) return respond(502, { ok: false, error: "send_failed" });
  return respond(200, { ok: true });
}

// --- decision paths use precompiled regexes (built once per data object) ---
function compiled(data) {
  if (!data._compiled) {
    data._compiled = {
      redirects: data.redirects.map((r) => new RegExp(r.re)),
      headerRules: data.headerRules.map((r) => new RegExp(r.re)),
    };
  }
  return data._compiled;
}

// First match wins across the ordered rule list, exactly as on Vercel.
function matchRedirect(data, path) {
  const res = compiled(data).redirects;
  for (let i = 0; i < res.length; i++) {
    const m = res[i].exec(path);
    if (m) return { status: data.redirects[i].status, location: fill(data.redirects[i].dest, m) };
  }
  return null;
}

// Destinations are positional templates ($1..$n): edge_script.py maps every
// :name in the destination to its source capture index at generation time.
function fill(dest, m) {
  return dest.replace(/\$(\d+)/g, (whole, i) => (m[+i] === undefined ? "" : m[+i]));
}

// Vercel cleanUrls: "/x.html" and "/x/index.html" redirect (301) to "/x";
// extensionless paths resolve to a real file. The file list is the built dist,
// baked in by the generator — the edge never guesses what the origin holds.
function cleanResolve(data, path) {
  if (path.endsWith("/index.html")) {
    const clean = path.slice(0, -"index.html".length).replace(/\/$/, "");
    return { type: "redirect", status: 301, location: clean || "/" };
  }
  if (path.endsWith(".html")) return { type: "redirect", status: 301, location: path.slice(0, -".html".length) || "/" };
  const base = path === "/" ? "" : path.replace(/\/$/, "");
  for (const cand of [base + ".html", base + "/index.html"]) {
    if (data.files.indexOf(cand.replace(/^\//, "")) >= 0) return { type: "rewrite", path: cand };
  }
  return { type: "rewrite", path };
}

// All matching header rules apply, in rule order (Vercel semantics); later
// rules overwrite same-named headers.
function responseHeaders(data, path) {
  const out = {};
  const rules = data.headerRules;
  const res = compiled(data).headerRules;
  for (let i = 0; i < rules.length; i++) {
    if (res[i].test(path)) Object.assign(out, rules[i].headers);
  }
  return out;
}

async function wsHandle(data, req, deps) {
  const headers = responseHeaders(data, req.path);
  if (req.path === "/api/contact") {
    const res = await contact(req, deps);
    res.headers = Object.assign({}, headers, res.headers);
    return res;
  }
  const hit = matchRedirect(data, req.path);
  if (hit) {
    const location = hit.location + (req.query ? "?" + req.query : "");
    return { type: "redirect", status: hit.status, location, headers };
  }
  const resolved = cleanResolve(data, req.path);
  resolved.headers = headers;
  if (resolved.type === "redirect" && req.query) resolved.location += "?" + req.query;
  return resolved;
}

if (typeof module !== "undefined") module.exports = { wsHandle, contact, matchRedirect, cleanResolve, responseHeaders };
