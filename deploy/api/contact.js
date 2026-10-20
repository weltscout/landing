// Vercel Node function: contact form -> Chatwoot conversation (Client API).
// No secrets to configure: the Client API is keyed by the inbox identifier,
// which is public by design (the dashboard widget ships it to every browser).
const TOPICS = { preizkus: "Preizkus", enterprise: "Business MAX za ekipo", portal: "Nov portal", drugo: "Drugo" };
const MAX = { name: 120, company: 160, email: 200, tel: 40, msg: 4000 };
const CHATWOOT = { apiUrl: "https://chatwoot.weltscout.com/public/api/v1/", inbox: "6v8z6KrTPtUF7VWRRrBqvq8o" };

module.exports = async (req, res) => {
  if (req.method !== "POST") { res.setHeader("Allow", "POST"); return res.status(405).json({ ok: false }); }
  let b = req.body || {};
  if (typeof b === "string") { try { b = JSON.parse(b); } catch (e) { return res.status(400).json({ ok: false, error: "json" }); } }
  if (b.website) return res.status(200).json({ ok: true });
  const f = {};
  for (const k of Object.keys(MAX)) f[k] = String(b[k] || "").trim().slice(0, MAX[k]);
  const topic = TOPICS[b.topic] ? b.topic : "drugo";
  if (!f.name || !f.msg || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(f.email) || b.consent !== true) return res.status(422).json({ ok: false, error: "invalid" });
  const lang = String(b.lang || "sl").slice(0, 2);
  const rows = [["Ime", f.name], ["Podjetje", f.company], ["E-pošta", f.email], ["Telefon", f.tel], ["Zanima ga", TOPICS[topic]], ["Jezik strani", lang]];
  const content = rows.map(([k, v]) => `${k}: ${v || "–"}`).join("\n") + "\n\n" + f.msg;
  const submitted = await submitContact({ name: f.name, email: f.email, content });
  if (submitted.ok !== true) return res.status(502).json({ ok: false, error: "send_failed" });
  return res.status(200).json({ ok: true });
};

// Chatwoot Client API: contact -> conversation -> message — the same endpoints
// the dashboard widget speaks (web/src/components/ChatWoot/ChatWoot.ts). Kept
// verbatim in sync with deploy/edge-templates/script.template.js (tripwire).
async function submitContact(sub) {
  const base = CHATWOOT.apiUrl + "inboxes/" + CHATWOOT.inbox;
  const created = await fetch(base + "/contacts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: sub.name, email: sub.email }),
  });
  if (!created.ok) return { ok: false };
  const sourceId = (await created.json()).source_id;
  const conversation = await fetch(base + "/contacts/" + sourceId + "/conversations", { method: "POST" });
  if (!conversation.ok) return { ok: false };
  const conversationId = (await conversation.json()).id;
  const message = await fetch(base + "/contacts/" + sourceId + "/conversations/" + conversationId + "/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content: sub.content }),
  });
  return { ok: message.ok };
}
