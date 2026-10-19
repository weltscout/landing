// Vercel Node function: contact form -> e-mail via Resend.
// Env: RESEND_API_KEY, CONTACT_FROM (verified sender), CONTACT_TO (default info@weltscout.com).
const TOPICS = { preizkus: "Preizkus", enterprise: "Business MAX za ekipo", portal: "Nov portal", drugo: "Drugo" };
const MAX = { name: 120, company: 160, email: 200, tel: 40, msg: 4000 };
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

module.exports = async (req, res) => {
  if (req.method !== "POST") { res.setHeader("Allow", "POST"); return res.status(405).json({ ok: false }); }
  let b = req.body || {};
  if (typeof b === "string") { try { b = JSON.parse(b); } catch (e) { return res.status(400).json({ ok: false, error: "json" }); } }
  if (b.website) return res.status(200).json({ ok: true });
  const f = {};
  for (const k of Object.keys(MAX)) f[k] = String(b[k] || "").trim().slice(0, MAX[k]);
  const topic = TOPICS[b.topic] ? b.topic : "drugo";
  if (!f.name || !f.msg || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(f.email) || b.consent !== true) return res.status(422).json({ ok: false, error: "invalid" });
  const key = process.env.RESEND_API_KEY, from = process.env.CONTACT_FROM, to = process.env.CONTACT_TO || "info@weltscout.com";
  if (!key || !from) return res.status(503).json({ ok: false, error: "not_configured" });
  const lang = String(b.lang || "sl").slice(0, 2);
  const rows = [["Ime", f.name], ["Podjetje", f.company], ["E-pošta", f.email], ["Telefon", f.tel], ["Zanima ga", TOPICS[topic]], ["Jezik strani", lang]];
  const html = `<table>${rows.map(([k, v]) => `<tr><td><b>${k}</b></td><td>${esc(v || "–")}</td></tr>`).join("")}</table><p>${esc(f.msg).replace(/\n/g, "<br>")}</p>`;
  const r = await fetch("https://api.resend.com/emails", {
    method: "POST", headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({ from, to: [to], reply_to: f.email, subject: `WeltScout kontakt: ${TOPICS[topic]} · ${f.name}`, html, text: rows.map(([k, v]) => `${k}: ${v || "–"}`).join("\n") + "\n\n" + f.msg })
  });
  if (!r.ok) return res.status(502).json({ ok: false, error: "send_failed" });
  return res.status(200).json({ ok: true });
};
