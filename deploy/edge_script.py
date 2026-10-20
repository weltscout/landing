"""Translate the Vercel config that build.py writes (dist/vercel.json) into the Bunny
middleware script (dist/edge_script.js) and its data (dist/edge_data.json).

    python3 deploy/build.py dist && python3 deploy/edge_script.py dist

The deployed script ports vercel.json semantics through deploy/edge_core.js:
redirects first-match-wins in rule order (301/302, as settled in deploy/aws.py),
cleanUrls (301), response headers, and /api/contact (deploy/api/contact.js).
Exits non-zero on any vercel.json construct it cannot translate faithfully;
it never writes a partial translation.
"""

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
CORE = HERE / "edge_core.js"
SDK = "https://esm.sh/@bunny.net/edgescript-sdk@0.13.0"
SITE_URL = "https://weltscout-landing.b-cdn.net"

KNOWN_TOP_KEYS = {"cleanUrls", "headers", "redirects"}
KNOWN_REDIRECT_KEYS = {"source", "destination", "permanent", "statusCode"}
KNOWN_HEADER_KEYS = {"source", "headers"}
KNOWN_STATUS_CODES = {301, 302, 307, 308}
STATUS_FOR_PERMANENT = {True: 301, False: 302}
NOT_UPLOADED = {"vercel.json", "edge_script.js", "edge_data.json"}


def fail(msg):
    sys.exit(f"edge_script: {msg}")


def main():
    dist = pathlib.Path(sys.argv[1])
    cfg = json.loads((dist / "vercel.json").read_text())
    data = translate(cfg, dist)
    bundle = bundle_script(data)
    # Only write once the whole translation succeeded — never partial output.
    (dist / "edge_data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1))
    (dist / "edge_script.js").write_text(bundle)
    n_exact = sum(1 for r in data["redirects"] if "exact" in r)
    print(
        f"edge script: {len(data['redirects'])} redirects -> {n_exact} exact + "
        f"{len(data['redirects']) - n_exact} pattern | {len(data['files'])} files | "
        f"{len(data['headerRules'])} header rules | {len(bundle)} bytes"
    )


def translate(cfg, dist):
    unknown = set(cfg) - KNOWN_TOP_KEYS
    if unknown:
        fail(f"vercel.json has untranslatable top-level keys: {sorted(unknown)}")
    if cfg.get("cleanUrls") is not True:
        fail("cleanUrls must be true — the core resolves extensionless URLs assuming it")
    return {
        "redirects": [redirect_rule(r, f"redirects[{i}]") for i, r in enumerate(cfg["redirects"])],
        "headerRules": [header_rule(h, f"headers[{i}]") for i, h in enumerate(cfg["headers"])],
        "files": site_files(dist),
    }


def redirect_rule(rule, where):
    unknown = set(rule) - KNOWN_REDIRECT_KEYS
    if unknown:
        fail(f"{where}: untranslatable keys {sorted(unknown)}")
    status = redirect_status(rule, where)
    re_src, groups, exact = compile_source(rule["source"], where)
    dest = rule["destination"]
    if not isinstance(dest, str) or not dest.startswith("/"):
        fail(f"{where}: destination {dest!r} is not an absolute path")
    if exact is not None:
        if ":" in dest:
            fail(f"{where}: exact source with parameter destination {dest!r}")
        return {"exact": exact, "dest": dest, "status": status}
    return {"re": re_src, "params": groups, "dest": dest, "status": status}


def redirect_status(rule, where):
    if "statusCode" in rule:
        if "permanent" in rule:
            fail(f"{where}: statusCode and permanent together")
        code = rule["statusCode"]
        if code not in KNOWN_STATUS_CODES:
            fail(f"{where}: statusCode {code!r} is not a redirect status")
        return code
    return STATUS_FOR_PERMANENT[bool(rule.get("permanent"))]


def header_rule(rule, where):
    unknown = set(rule) - KNOWN_HEADER_KEYS
    if unknown:
        fail(f"{where}: untranslatable keys {sorted(unknown)}")
    re_src, _groups, _exact = compile_source(rule["source"], where)
    headers = {}
    for h in rule["headers"]:
        if set(h) != {"key", "value"}:
            fail(f"{where}: header entry {sorted(h)} is not key/value")
        headers[h["key"]] = h["value"]
    return {"re": re_src, "headers": headers}


def site_files(dist):
    out = []
    for p in sorted(dist.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(dist).as_posix()
        if rel in NOT_UPLOADED or rel.startswith("aws/"):
            continue
        out.append(rel)
    return out


# --- source compilation: the path-to-regexp subset the config actually uses ---
# literals, :name, :name(regex), :name*, and bare (regex) groups. Anything else
# (modifiers + and ?, wildcards, unnamed tokens) is fatal.

TOKEN = re.compile(
    r":(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?:\((?P<custom>[^()]*)\))?(?P<mod>[*+?])?"
    r"|\((?P<group>[^()]*)\)"
    r"|(?P<lit>[^:()*+?]+)"
)


def compile_source(src, where):
    """Return (js regex source, capture groups in order, exact-or-None)."""
    parts = []
    groups = []
    pos = 0
    while pos < len(src):
        m = TOKEN.match(src, pos)
        if not m:
            fail(f"{where}: unsupported construct in source {src[pos:]!r} (full: {src!r})")
        pos = m.end()
        if m.group("name") is not None:
            name, custom, mod = m.group("name"), m.group("custom"), m.group("mod")
            if mod in ("+", "?"):
                fail(f"{where}: modifier {mod!r} on :{name} is not translated faithfully")
            if mod == "*":
                if m.start() == 0 or src[m.start() - 1] != "/":
                    fail(f"{where}: :{name}* outside a segment separator is not translated faithfully")
                if parts and parts[-1].endswith("/"):
                    parts[-1] = parts[-1][:-1]
                parts.append(r"(?:(?:/((?:[^/]+)(?:/[^/]+)*)?)?)")
            else:
                parts.append("(" + (custom if custom else "[^/]+") + ")")
            groups.append({"name": name, "mod": mod or "seg"})
        elif m.group("group") is not None:
            parts.append("(" + m.group("group") + ")")
            groups.append({"name": None, "mod": "seg"})
        else:
            parts.append(re.escape(m.group("lit")))
    exact = src if not groups else None
    return "^" + "".join(parts) + "$", groups, exact


def bundle_script(data):
    core = CORE.read_text()
    data_json = json.dumps(data, ensure_ascii=False, indent=1)
    return f"""import * as BunnySDK from "{SDK}";

// Generated by deploy/edge_script.py from dist/vercel.json — do not edit.
const DATA = {data_json};

{core}

async function sendEmail(payload) {{
  const r = await fetch("https://api.resend.com/emails", {{
    method: "POST",
    headers: {{ Authorization: `Bearer ${{process.env.RESEND_API_KEY}}`, "Content-Type": "application/json" }},
    body: JSON.stringify(payload),
  }});
  return {{ ok: r.ok }};
}}

function toResponse(decision) {{
  const headers = new Headers(decision.headers || {{}});
  if (decision.location !== undefined) headers.set("Location", decision.location);
  const body = decision.body === undefined ? null : JSON.stringify(decision.body);
  if (decision.body !== undefined) headers.set("Content-Type", "application/json; charset=utf-8");
  return new Response(body, {{ status: decision.status, headers }});
}}

BunnySDK.net.http
  .servePullZone({{ url: "{SITE_URL}" }})
  .onClientRequest(async (ctx) => {{
    const url = new URL(ctx.request.url);
    const decision = await wsHandle(
      DATA,
      {{
        method: ctx.request.method,
        path: url.pathname,
        query: url.search.replace(/^\\?/, ""),
        // Body only for the contact endpoint: any other POST must keep an
        // intact body — the rewrite path clones the request, and cloning a
        // consumed body throws in the edge runtime.
        body: ctx.request.method === "POST" && url.pathname === "/api/contact" ? await ctx.request.text() : undefined,
      }},
      {{ env: process.env, sendEmail }},
    );
    if (decision.type === "rewrite") {{
      if (decision.path === url.pathname) return ctx.request;
      url.pathname = decision.path;
      return new Request(url.toString(), ctx.request);
    }}
    return toResponse(decision);
  }})
  .onClientResponse((ctx) => {{
    const headers = responseHeaders(DATA, new URL(ctx.request.url).pathname);
    for (const [k, v] of Object.entries(headers)) ctx.response.headers.set(k, v);
    return Promise.resolve(ctx.response);
  }});
"""


if __name__ == "__main__":
    main()
