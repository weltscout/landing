// AWS Lambda (Node.js 20+) adapter for the Vercel function deploy/api/contact.js.
// The validation, the status codes and the Resend call stay in contact.js, which deploy/aws.py copies next
// to this file, so the Vercel and the AWS endpoint cannot drift apart.
// Event: Lambda Function URL or API Gateway HTTP API, payload format 2.0.
// Env: RESEND_API_KEY, CONTACT_FROM, CONTACT_TO (the same names as on Vercel).
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const contact = require("./contact.js");

// contact.js calls fetch without a timeout; a hung Resend call would otherwise run until the Lambda timeout.
// Keep the function timeout above this value.
const OUTBOUND_TIMEOUT_MS = 10000;
const baseFetch = globalThis.fetch;
globalThis.fetch = (url, opts = {}) => baseFetch(url, { signal: AbortSignal.timeout(OUTBOUND_TIMEOUT_MS), ...opts });

const reply = (statusCode, body, headers = {}) => ({
  statusCode,
  headers: { "content-type": "application/json; charset=utf-8", ...headers },
  body: JSON.stringify(body),
});

// The parts of Vercel's request body parsing that contact.js relies on.
function parseBody(event) {
  const raw = event.isBase64Encoded ? Buffer.from(event.body || "", "base64").toString("utf8") : event.body || "";
  const headers = Object.fromEntries(Object.entries(event.headers || {}).map(([k, v]) => [k.toLowerCase(), v]));
  const type = String(headers["content-type"] || "").split(";")[0].trim().toLowerCase();
  if (!raw) return { body: undefined };
  if (type === "application/json") {
    try { return { body: JSON.parse(raw) }; } catch (e) { return { error: reply(400, { ok: false, error: "json" }) }; }
  }
  if (type === "application/x-www-form-urlencoded") return { body: Object.fromEntries(new URLSearchParams(raw)) };
  if (type === "text/plain") return { body: raw };
  return { body: undefined };
}

export const handler = async (event) => {
  const method = (event.requestContext && event.requestContext.http && event.requestContext.http.method) || event.httpMethod;
  const parsed = method === "POST" ? parseBody(event) : { body: undefined };
  if (parsed.error) return parsed.error;
  let out = null;
  const headers = {};
  const res = {
    setHeader(k, v) { headers[k.toLowerCase()] = String(v); return res; },
    status(code) { return { json(obj) { out = reply(code, obj, headers); return out; } }; },
  };
  try {
    await contact({ method, body: parsed.body, headers: event.headers || {} }, res);
  } catch (e) {
    console.error("contact failed", e && e.name, e && e.message);
    return reply(500, { ok: false, error: "internal" });
  }
  return out || reply(500, { ok: false, error: "no_response" });
};
