"""Translate the Vercel config that build.py writes (dist/vercel.json) into AWS hosting files in dist/aws/.

    python3 deploy/build.py dist && python3 deploy/aws.py dist

Writes: CloudFront Function viewer-request.js (redirects + clean URLs), response-headers.json (CloudFront
response headers policy), s3-sync.sh (upload with Content-Type and Cache-Control per file), the AWS Amplify
alternative (amplify-redirects.json, customHttp.yml), contact-lambda/ (Lambda adapter around
deploy/api/contact.js) and README.md. Exits non-zero on any vercel.json construct it cannot translate
faithfully; it never writes a partial translation.
"""

import fnmatch
import itertools
import json
import os
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE / "aws-templates"
CONTACT_SRC = HERE / "api" / "contact.js"
LANGS = HERE / "langs.json"

CF_FUNCTION_MAX_BYTES = (
    10 * 1024
)  # CloudFront Functions quota: maximum function code size
STATUS_FOR_PERMANENT = {True: 301, False: 302}
STATUS_TEXT = {
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
}
CLEAN_URL_STATUS = (
    301  # Vercel answers cleanUrls with 308; the order asks for 301 everywhere
)
# CloudFront KeyValueStore quotas (exact redirects live there; the function holds only patterns and code).
KVS_MAX_KEY_BYTES = 512
KVS_MAX_VALUE_BYTES = 1024
KVS_MAX_FILE_BYTES = 5 * 1024 * 1024
KVS_UPDATE_BATCH = 50
KVS_ARN_ENV = "WS_CF_KVS_ARN"
KVS_ARN_RE = re.compile(r"^arn:aws:cloudfront::\d{12}:key-value-store/([0-9a-fA-F-]{36})$")
KVS_ID_PLACEHOLDER = "SET-" + KVS_ARN_ENV + "-AND-RERUN-AWS-PY"
PASSTHROUGH = ["/api/"]  # served by their own CloudFront behavior, never rewritten
SKIP_UPLOAD = ["api/*", "aws/*", "vercel.json"]  # Vercel-only files and this output
# Vercel's Cache-Control for a static file with no header rule (observed on the preview deployment).
DEFAULT_CACHE_CONTROL = "public, max-age=0, must-revalidate"
CONTENT_TYPES = {
    "html": "text/html; charset=utf-8",
    "css": "text/css; charset=utf-8",
    "js": "text/javascript; charset=utf-8",
    "mjs": "text/javascript; charset=utf-8",
    "json": "application/json; charset=utf-8",
    "txt": "text/plain; charset=utf-8",
    "xml": "application/xml; charset=utf-8",
    "svg": "image/svg+xml",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "avif": "image/avif",
    "gif": "image/gif",
    "ico": "image/x-icon",
    "mp4": "video/mp4",
    "webm": "video/webm",
    "woff2": "font/woff2",
    "woff": "font/woff",
    "pdf": "application/pdf",
}
KNOWN_TOP_KEYS = {"cleanUrls", "headers", "redirects"}
KNOWN_REDIRECT_KEYS = {"source", "destination", "permanent", "statusCode"}
OBJECT_METADATA_HEADERS = {
    "cache-control",
    "content-type",
}  # per-path headers that become S3 object metadata
REFERRER_POLICIES = {
    "no-referrer",
    "no-referrer-when-downgrade",
    "origin",
    "origin-when-cross-origin",
    "same-origin",
    "strict-origin",
    "strict-origin-when-cross-origin",
    "unsafe-url",
}
DEFAULT_PARAM_PATTERN = r"[^\/#\?]+?"  # path-to-regexp 6.1 default segment pattern (Vercel @vercel/routing-utils)
PREFIX_CHARS = "./"
SIMPLE_ALTERNATION = re.compile(r"^[A-Za-z0-9_.-]+(\|[A-Za-z0-9_.-]+)*$")
CATCH_ALL_PATTERN = ".*"
TOKEN = re.compile(
    r":(?P<name>[A-Za-z0-9_]+)(?:\((?P<npat>[^()]*)\))?(?P<nmod>[*+?])?|\((?P<upat>[^()]*)\)(?P<umod>[*+?])?"
)
LITERAL_FORBIDDEN = set("()*+?{}\\:[]|")
CATCH_ALL_PROBES = ["/", "/a", "/a/b/c.d"]


class Untranslatable(Exception):
    pass


def fail(msg):
    raise Untranslatable(msg)


def parse_path(source, where):
    """Split a path-to-regexp 6.1 source into literal strings and parameter dicts (Vercel's subset)."""
    out, pos, unnamed = [], 0, 0
    for m in TOKEN.finditer(source):
        lit = source[pos : m.start()]
        if LITERAL_FORBIDDEN & set(lit):
            fail(f"{where}: unsupported syntax in literal part {lit!r} of {source!r}")
        prefix = ""
        if lit and lit[-1] in PREFIX_CHARS:
            prefix, lit = lit[-1], lit[:-1]
        if lit:
            out.append(lit)
        if m.group("name"):
            name, pat, mod = m.group("name"), m.group("npat"), m.group("nmod") or ""
        else:
            name, pat, mod = unnamed, m.group("upat"), m.group("umod") or ""
            unnamed += 1
        if (
            pat is not None
            and pat != CATCH_ALL_PATTERN
            and not SIMPLE_ALTERNATION.match(pat)
        ):
            fail(
                f"{where}: custom pattern ({pat}) in {source!r} is not a plain alternation or (.*)"
            )
        out.append({"name": name, "pattern": pat, "modifier": mod, "prefix": prefix})
        pos = m.end()
    tail = source[pos:]
    if LITERAL_FORBIDDEN & set(tail):
        fail(f"{where}: unsupported syntax in literal part {tail!r} of {source!r}")
    if tail:
        out.append(tail)
    if not source.startswith("/"):
        fail(f"{where}: source {source!r} must start with '/'")
    return out


def to_regex(tokens):
    """Same regex as path-to-regexp 6.1 tokensToRegexp with strict, sensitive, end (Vercel's options)."""
    rx = "^"
    for t in tokens:
        if isinstance(t, str):
            rx += re.escape(t)
            continue
        pat = t["pattern"] if t["pattern"] is not None else DEFAULT_PARAM_PATTERN
        pre = re.escape(t["prefix"])
        if t["prefix"]:
            if t["modifier"] in ("+", "*"):
                opt = "?" if t["modifier"] == "*" else ""
                rx += f"(?:{pre}((?:{pat})(?:{pre}(?:{pat}))*)){opt}"
            else:
                rx += f"(?:{pre}({pat})){t['modifier']}"
        else:
            rx += f"({pat}){t['modifier']}"
    return rx + "$"


def js_regex(py_rx):
    js = py_rx.replace("\\/", "/").replace("/", "\\/")
    for py_only in ("(?P<", "(?#", "\\A", "\\Z"):
        if py_only in js:
            fail(f"regex {py_rx!r} uses Python-only syntax")
    return js


def destination_parts(dest, params, where):
    """Destination as a list of literal strings and [capture group, prefix] pairs."""
    parsed = urlparse(dest)
    if parsed.query or parsed.fragment:
        fail(
            f"{where}: destination {dest!r} has a query or fragment; merging it with the request query is not translated"
        )
    if not (dest.startswith("/") or parsed.scheme in ("http", "https")):
        fail(f"{where}: destination {dest!r} is neither a path nor an http(s) URL")
    origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme else ""
    if ":" in origin.split("://", 1)[-1]:
        fail(
            f"{where}: parameters or ports in the destination host are not translated ({dest!r})"
        )
    path = dest[len(origin) :]
    parts = [origin] if origin else []
    for t in parse_path(path or "/", where):
        if isinstance(t, str):
            parts.append(t)
            continue
        if t["pattern"] is not None or t["name"] not in params:
            fail(
                f"{where}: destination parameter {t['name']!r} in {dest!r} is not a named parameter of the source"
            )
        parts.append([params[t["name"]], t["prefix"]])
    merged = []
    for p in parts:
        if isinstance(p, str) and merged and isinstance(merged[-1], str):
            merged[-1] += p
        else:
            merged.append(p)
    return merged


def redirect_status(rule, where):
    if "statusCode" in rule:
        if "permanent" in rule:
            fail(f"{where}: statusCode and permanent together")
        code = rule["statusCode"]
        if code not in STATUS_TEXT:
            fail(f"{where}: statusCode {code!r} is not a redirect status")
        return code
    return STATUS_FOR_PERMANENT[rule.get("permanent", True) is True]


def translate_redirects(rules):
    exact, patterns, compiled, shadowed = {}, [], [], []
    for i, rule in enumerate(rules):
        where = f"redirects[{i}]"
        extra = set(rule) - KNOWN_REDIRECT_KEYS
        if extra:
            fail(
                f"{where}: keys {sorted(extra)} (has/missing/locale/...) are not translated"
            )
        tokens = parse_path(rule["source"], where)
        status = redirect_status(rule, where)
        if all(isinstance(t, str) for t in tokens):
            src = rule["source"]
            if src in exact or any(rx.match(src) for rx in compiled):
                shadowed.append(src)
                continue
            exact[src] = [status, destination_parts(rule["destination"], {}, where)]
            continue
        params, group = {}, 1
        for t in tokens:
            if isinstance(t, dict):
                params[t["name"]] = group
                group += 1
        rx = to_regex(tokens)
        compiled.append(re.compile(rx))
        patterns.append(
            [
                js_regex(rx),
                status,
                destination_parts(rule["destination"], params, where),
            ]
        )
    for src, (status, dest) in exact.items():
        if any(isinstance(p, list) for p in dest):
            fail(f"exact redirect {src!r} references a parameter")
        exact[src] = [status, "".join(dest)]
    return exact, patterns, shadowed


def is_catch_all(source):
    rx = re.compile(to_regex(parse_path(source, f"headers source {source!r}")))
    return all(rx.match(p) for p in CATCH_ALL_PROBES)


def source_globs(source):
    """A header source as S3/fnmatch globs relative to the bucket root (alternations expanded)."""
    tokens = parse_path(source, f"headers source {source!r}")
    choices = []
    for idx, t in enumerate(tokens):
        if isinstance(t, str):
            choices.append([t])
        elif t["pattern"] == CATCH_ALL_PATTERN or t["modifier"] in ("*", "+"):
            if idx != len(tokens) - 1:
                fail(
                    f"headers source {source!r}: a wildcard is only translated at the end"
                )
            choices.append([t["prefix"] + "*"])
        elif t["pattern"] is not None and not t["modifier"]:
            choices.append([t["prefix"] + alt for alt in t["pattern"].split("|")])
        else:
            fail(
                f"headers source {source!r}: parameter {t['name']!r} cannot become a file glob"
            )
    return ["".join(c).lstrip("/") for c in itertools.product(*choices)]


def translate_headers(rules):
    global_headers, path_rules = [], []
    for i, rule in enumerate(rules):
        if set(rule) - {"source", "headers"}:
            fail(
                f"headers[{i}]: keys {sorted(set(rule) - {'source', 'headers'})} are not translated"
            )
        if is_catch_all(rule["source"]):
            global_headers += [(h["key"], h["value"]) for h in rule["headers"]]
            continue
        keys = {h["key"].lower() for h in rule["headers"]}
        if keys - OBJECT_METADATA_HEADERS:
            fail(
                f"headers[{i}] ({rule['source']}): only {sorted(OBJECT_METADATA_HEADERS)} are translated for a path rule, got {sorted(keys)}"
            )
        path_rules.append(
            {
                "source": rule["source"],
                "globs": source_globs(rule["source"]),
                "headers": [(h["key"], h["value"]) for h in rule["headers"]],
            }
        )
    return global_headers, path_rules


def hsts(value):
    out = {"Override": True, "IncludeSubdomains": False, "Preload": False}
    for part in [p.strip() for p in value.split(";") if p.strip()]:
        low = part.lower()
        if low.startswith("max-age="):
            out["AccessControlMaxAgeSec"] = int(low.split("=", 1)[1])
        elif low == "includesubdomains":
            out["IncludeSubdomains"] = True
        elif low == "preload":
            out["Preload"] = True
        else:
            fail(f"Strict-Transport-Security directive {part!r} is not translated")
    if "AccessControlMaxAgeSec" not in out:
        fail("Strict-Transport-Security without max-age")
    return out


def security_entry(key, value):
    k = key.lower()
    if k == "x-content-type-options":
        if value.lower() != "nosniff":
            fail(f"X-Content-Type-Options {value!r}: CloudFront only sends nosniff")
        return "ContentTypeOptions", {"Override": True}
    if k == "referrer-policy":
        if value not in REFERRER_POLICIES:
            fail(f"Referrer-Policy {value!r} is not a CloudFront ReferrerPolicy value")
        return "ReferrerPolicy", {"ReferrerPolicy": value, "Override": True}
    if k == "x-frame-options":
        if value.upper() not in ("DENY", "SAMEORIGIN"):
            fail(f"X-Frame-Options {value!r} is not DENY or SAMEORIGIN")
        return "FrameOptions", {"FrameOption": value.upper(), "Override": True}
    if k == "content-security-policy":
        return "ContentSecurityPolicy", {
            "ContentSecurityPolicy": value,
            "Override": True,
        }
    if k == "strict-transport-security":
        return "StrictTransportSecurity", hsts(value)
    if k == "x-xss-protection":
        fail(
            "X-XSS-Protection is not translated (deprecated header; remove it from vercel.base.json)"
        )
    return None


def response_headers_policy(name, global_headers):
    security, custom = {}, []
    for key, value in global_headers:
        entry = security_entry(key, value)
        if entry:
            security[entry[0]] = entry[1]
        else:
            custom.append({"Header": key, "Value": value, "Override": True})
    cfg = {
        "Name": name,
        "Comment": "Generated by deploy/aws.py from vercel.json headers for source /(.*)",
    }
    if security:
        cfg["SecurityHeadersConfig"] = security
    if custom:
        cfg["CustomHeadersConfig"] = {"Quantity": len(custom), "Items": custom}
    return cfg


def site_files(dist):
    files = []
    for p in sorted(dist.rglob("*")):
        rel = p.relative_to(dist).as_posix()
        if p.is_file() and not any(fnmatch.fnmatch(rel, g) for g in SKIP_UPLOAD):
            files.append(rel)
    return files


def object_metadata(files, path_rules):
    meta = {}
    for rel in files:
        ext = rel.rsplit(".", 1)[-1].lower() if "." in rel.rsplit("/", 1)[-1] else ""
        if ext not in CONTENT_TYPES:
            fail(
                f"no Content-Type known for {rel!r}: add the extension to CONTENT_TYPES in deploy/aws.py"
            )
        h = {"content-type": CONTENT_TYPES[ext], "cache-control": DEFAULT_CACHE_CONTROL}
        for r in path_rules:
            if any(fnmatch.fnmatch(rel, g) for g in r["globs"]):
                h.update({k.lower(): v for k, v in r["headers"]})
        meta[rel] = (h["content-type"], h["cache-control"])
    return meta


def cover(group, files):
    """Fewest fnmatch globs that select exactly the files of one metadata group."""

    def safe(glob):
        return all(f in group for f in files if fnmatch.fnmatch(f, glob))

    globs, left = [], set(group)
    for f in sorted(group):
        if f not in left:
            continue
        ext = f.rsplit(".", 1)[-1]
        top = f.split("/", 1)[0] if "/" in f else None
        for g in [f"*.{ext}"] + ([f"{top}/*.{ext}"] if top else []) + [f]:
            if safe(g):
                globs.append(g)
                left -= {x for x in group if fnmatch.fnmatch(x, g)}
                break
    return globs


def s3_script(files, meta):
    groups = defaultdict(set)
    for rel, key in meta.items():
        groups[key].add(rel)
    skip = " ".join(f'--exclude "{g}"' for g in SKIP_UPLOAD)
    lines = [
        "#!/bin/sh",
        "# Generated by deploy/aws.py: uploads the built site to S3 with Content-Type and Cache-Control per file group.",
        f"# Usage: BUCKET=<bucket> {KVS_ARN_ENV}=<kvs arn> [DISTRIBUTION_ID=<id>] sh dist/aws/s3-sync.sh",
        "# Credentials come from your AWS CLI profile (AWS_PROFILE); none are stored here.",
        "set -eu",
        ': "${BUCKET:?set BUCKET to the S3 bucket name}"',
        'DIST="$(cd "$(dirname "$0")/.." && pwd)"',
        "",
        "# 1. cp (not sync) for every group, so changed headers always reach S3 even when a file did not change.",
    ]
    for (ctype, cache), group in sorted(
        groups.items(), key=lambda kv: (kv[0][1], kv[0][0])
    ):
        inc = " ".join(f'--include "{g}"' for g in cover(group, files))
        lines.append(f"# {len(group)} file(s)")
        lines.append(
            f'aws s3 cp "$DIST" "s3://$BUCKET" --recursive --only-show-errors --exclude "*" {inc} {skip} '
            f'--content-type "{ctype}" --cache-control "{cache}"'
        )
    lines += [
        "",
        "# 2. Remove objects that are no longer in dist/ (uploads nothing: every remote object is newer).",
        f'aws s3 sync "$DIST" "s3://$BUCKET" --delete --only-show-errors {skip}',
        "",
        "# 3. Exact redirects: make the KeyValueStore equal to kvs-redirects.json (needs WS_CF_KVS_ARN).",
        f'if [ -n "${{{KVS_ARN_ENV}:-}}" ]; then',
        '  python3 "$DIST/aws/kvs-sync.py"',
        "else",
        f'  echo "s3-sync: {KVS_ARN_ENV} not set, KeyValueStore NOT updated (redirects unchanged)" >&2',
        "fi",
        "",
        "# 4. Optional: drop CloudFront's cached copies.",
        'if [ -n "${DISTRIBUTION_ID:-}" ]; then',
        '  aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" --paths "/*"',
        "fi",
        "",
    ]
    return "\n".join(lines), groups


def amplify_rules(rules):
    """Vercel redirects as Amplify rules: alternations expanded, :x* as a bare rule plus a /<*> rule."""
    out = []
    for i, rule in enumerate(rules):
        where = f"redirects[{i}]"
        tokens = parse_path(rule["source"], where)
        status = str(redirect_status(rule, where))
        params = [t for t in tokens if isinstance(t, dict)]
        if any(t["modifier"] == "?" for t in params):
            fail(f"{where}: optional parameter in {rule['source']!r} has no Amplify form")
        star = [t for t in params if t["modifier"] in ("*", "+") or t["pattern"] == CATCH_ALL_PATTERN]
        if len(star) > 1 or (star and (tokens[-1] is not star[0] or star[0]["prefix"] != "/")):
            fail(f"{where}: Amplify allows one <*>, only at the end after '/' ({rule['source']!r})")
        alts = [
            t
            for t in tokens
            if isinstance(t, dict)
            and t["pattern"] not in (None, CATCH_ALL_PATTERN)
            and t not in star
        ]
        for combo in itertools.product(*[t["pattern"].split("|") for t in alts]):
            value = {t["name"]: v for t, v in zip(alts, combo)}
            variants = (
                [""]
                if not star
                else (["/<*>"] if star[0]["modifier"] == "+" else ["", "/<*>"])
            )
            for variant in variants:
                src = ""
                for t in tokens:
                    if isinstance(t, str):
                        src += t
                    elif t is (star[0] if star else None):
                        src += variant
                    elif t["name"] in value:
                        src += t["prefix"] + value[t["name"]]
                    else:
                        src += f"{t['prefix']}<{t['name']}>"
                dest = rule["destination"]
                for name, v in value.items():
                    dest = re.sub(rf":{re.escape(str(name))}(?![A-Za-z0-9_])", v, dest)
                if star and isinstance(star[0]["name"], str):
                    dest = re.sub(
                        rf"/:{star[0]['name']}[*+?]?(?![A-Za-z0-9_])",
                        "/<*>" if variant else "",
                        dest,
                    )
                for t in tokens:
                    if isinstance(t, dict) and t not in star and t["name"] not in value:
                        dest = re.sub(
                            rf":{t['name']}(?![A-Za-z0-9_])", f"<{t['name']}>", dest
                        )
                if re.search(r":[A-Za-z0-9_]", urlparse(dest).path):
                    fail(
                        f"{where}: destination {rule['destination']!r} keeps an untranslated parameter"
                    )
                out.append(
                    {"source": src, "target": dest, "status": status, "condition": None}
                )
    return out


def yaml_str(s):
    return "'" + str(s).replace("'", "''") + "'"


def amplify_glob(glob):
    """fnmatch's * crosses '/', Amplify's does not: a trailing * becomes ** so img/og/x.jpg stays covered."""
    return glob[:-1] + "**" if glob.endswith("/*") else glob


def custom_http(global_headers, path_rules):
    lines = [
        "# Generated by deploy/aws.py from vercel.json headers (AWS Amplify Hosting custom headers).",
        "customHeaders:",
    ]
    blocks = [("**", global_headers)]
    for r in path_rules:
        blocks += [(amplify_glob(g), r["headers"]) for g in r["globs"]]
    for pattern, headers in blocks:
        lines.append(f"  - pattern: {yaml_str(pattern)}")
        lines.append("    headers:")
        for k, v in headers:
            lines.append(f"      - key: {yaml_str(k)}")
            lines.append(f"        value: {yaml_str(v)}")
    return "\n".join(lines) + "\n"


def kvs_target():
    """(arn, id) from WS_CF_KVS_ARN, or (None, placeholder) with a warning: the function then cannot run."""
    arn = os.environ.get(KVS_ARN_ENV, "").strip()
    if not arn:
        print(
            f"aws.py: WARNING {KVS_ARN_ENV} is not set: viewer-request.js uses the placeholder KVS id "
            f"{KVS_ID_PLACEHOLDER!r} and must not be published; create the KeyValueStore, then rerun with "
            f"{KVS_ARN_ENV}=<arn>",
            file=sys.stderr,
        )
        return None, KVS_ID_PLACEHOLDER
    m = KVS_ARN_RE.match(arn)
    if not m:
        fail(f"{KVS_ARN_ENV}={arn!r} is not a CloudFront KeyValueStore ARN (arn:aws:cloudfront::<account>:key-value-store/<id>)")
    return arn, m.group(1)


def kvs_data(exact):
    """Exact redirects as a KeyValueStore import file; the status goes into the value only if one differs."""
    with_status = any(status != STATUS_FOR_PERMANENT[True] for status, _ in exact.values())
    data = [
        {"key": src, "value": f"{status} {dest}" if with_status else dest}
        for src, (status, dest) in exact.items()
    ]
    for d in data:
        if len(d["key"].encode()) > KVS_MAX_KEY_BYTES:
            fail(f"KVS key {d['key'][:60]!r}... is over {KVS_MAX_KEY_BYTES} bytes")
        if len(d["value"].encode()) > KVS_MAX_VALUE_BYTES:
            fail(f"KVS value for {d['key']!r} is over {KVS_MAX_VALUE_BYTES} bytes")
    text = json.dumps({"data": data}, indent=1, ensure_ascii=False) + "\n"
    if len(text.encode()) > KVS_MAX_FILE_BYTES:
        fail(f"kvs-redirects.json is {len(text.encode())} bytes, over the {KVS_MAX_FILE_BYTES}-byte KeyValueStore limit")
    return text, with_status, len(text.encode())


def fill_template(text, values, pattern, what):
    """Replace every pattern.format(NAME); any placeholder left over is an error, never shipped."""
    for k, v in values.items():
        text = text.replace(pattern.format(k), str(v))
    head, tail = pattern.format("\0").split("\0")
    left = re.findall(re.escape(head) + "([A-Z_]+)" + re.escape(tail), text)
    if left:
        fail(f"{what} placeholders not filled: {left}")
    return text


def viewer_function(kvs_id, with_status, patterns, flat):
    code = fill_template(
        (TEMPLATES / "viewer-request.template.js").read_text(),
        {
            "KVS_ID": json.dumps(kvs_id),
            "VALUE_HAS_STATUS": "true" if with_status else "false",
            "DEFAULT_STATUS": str(STATUS_FOR_PERMANENT[True]),
            "PATTERNS": json.dumps(patterns, separators=(",", ":"), ensure_ascii=False),
            "FLAT": json.dumps(flat, separators=(",", ":")),
            "PASSTHROUGH": json.dumps(PASSTHROUGH),
            "CLEAN_STATUS": str(CLEAN_URL_STATUS),
            "STATUS_TEXT": json.dumps({str(k): v for k, v in STATUS_TEXT.items()}, separators=(",", ":")),
        },
        "/*__{}__*/",
        "viewer-request template",
    )
    size = len(code.encode())
    if size > CF_FUNCTION_MAX_BYTES:
        fail(
            f"viewer-request.js is {size} bytes, above the CloudFront Functions limit of {CF_FUNCTION_MAX_BYTES} "
            "even with the exact redirects in the KeyValueStore: too many pattern rules or flat pages"
        )
    return code, size


def flat_pages(dist, files):
    """Pages that cleanUrls serves from x.html (not x/index.html); both forms at once are ambiguous."""
    flat = []
    for rel in files:
        if rel.endswith(".html") and not rel.endswith("index.html"):
            clean = "/" + rel[: -len(".html")]
            if (dist / rel[: -len(".html")] / "index.html").exists():
                fail(
                    f"both {rel} and {rel[: -len('.html')]}/index.html exist; Vercel's choice between them is not translated"
                )
            flat.append(clean)
    return flat


def site_url():
    return os.environ.get("WS_SITE") or json.loads(LANGS.read_text())["site"]


def readme_samples(dist, files, amplify):
    """Example paths for the curl checks, taken from this build so the README never names a stale URL."""
    star = next((r for r in amplify if r["source"].endswith("/<*>")), None)
    clean = next(("/" + f[: -len("/index.html")] for f in files if f.count("/") == 2 and f.endswith("/index.html")), "/")
    return {
        "SAMPLE_PATTERN": star["source"].replace("<*>", "any/old-slug") if star else "/",
        "SAMPLE_PATTERN_DEST": star["target"].replace("<*>", "any/old-slug") if star else "(no pattern rule)",
        "SAMPLE_CLEAN": clean,
    }


def render_readme(values):
    return fill_template((TEMPLATES / "README.template.md").read_text(), values, "{{{{{}}}}}", "README template")


def main(dist):
    cfg = json.loads((dist / "vercel.json").read_text())
    extra = set(cfg) - KNOWN_TOP_KEYS
    if extra:
        fail(f"vercel.json keys {sorted(extra)} are not translated")
    if cfg.get("cleanUrls") is not True:
        fail("only cleanUrls: true is translated")
    rules = cfg.get("redirects", [])
    exact, patterns, shadowed = translate_redirects(rules)
    global_headers, path_rules = translate_headers(cfg.get("headers", []))
    files = site_files(dist)
    flat = flat_pages(dist, files)
    kvs_arn, kvs_id = kvs_target()
    kvs_text, with_status, kvs_size = kvs_data(exact)
    code, size = viewer_function(kvs_id, with_status, patterns, flat)
    meta = object_metadata(files, path_rules)
    script, groups = s3_script(files, meta)
    host = urlparse(site_url()).netloc
    policy = response_headers_policy(
        re.sub(r"[^A-Za-z0-9-]", "-", host) + "-headers", global_headers
    )
    amplify = amplify_rules(rules)

    out = dist / "aws"
    if out.exists():
        shutil.rmtree(out)
    (out / "contact-lambda").mkdir(parents=True)
    (out / "viewer-request.js").write_text(code)
    (out / "kvs-redirects.json").write_text(kvs_text)
    (out / "kvs-sync.py").write_text(
        fill_template(
            (TEMPLATES / "kvs-sync.py").read_text(),
            {"KVS_UPDATE_BATCH": KVS_UPDATE_BATCH, "KVS_ARN": kvs_arn or ""},
            "{{{{{}}}}}",
            "kvs-sync template",
        )
    )
    (out / "response-headers.json").write_text(json.dumps(policy, indent=2) + "\n")
    (out / "s3-sync.sh").write_text(script)
    (out / "s3-sync.sh").chmod(0o755)
    (out / "amplify-redirects.json").write_text(
        json.dumps(amplify, indent=2, ensure_ascii=False) + "\n"
    )
    (out / "customHttp.yml").write_text(custom_http(global_headers, path_rules))
    shutil.copy(
        TEMPLATES / "contact-lambda" / "index.mjs", out / "contact-lambda" / "index.mjs"
    )
    shutil.copy(CONTACT_SRC, out / "contact-lambda" / "contact.js")
    cache_rows = (
        "\n".join(
            f"| `{', '.join(r['globs'])}` | "
            + "; ".join(f"{k}: `{v}`" for k, v in r["headers"])
            + " |"
            for r in path_rules
        )
        or "| (none) | |"
    )
    global_rows = (
        "\n".join(f"| `{k}` | `{v}` |" for k, v in global_headers) or "| (none) | |"
    )
    (out / "README.md").write_text(
        render_readme(
            {
                "SITE": site_url(),
                "HOST": host,
                "N_RULES": len(rules),
                "N_EXACT": len(exact),
                "KVS_SIZE": kvs_size,
                "KVS_MAX": KVS_MAX_FILE_BYTES,
                "KVS_ENV": KVS_ARN_ENV,
                "KVS_ARN": kvs_arn or "(not set: rerun with " + KVS_ARN_ENV + ")",
                "N_PATTERNS": len(patterns),
                "N_SHADOWED": len(shadowed),
                "FN_SIZE": size,
                "FN_MAX": CF_FUNCTION_MAX_BYTES,
                "N_AMPLIFY": len(amplify),
                "N_FILES": len(files),
                "N_GROUPS": len(groups),
                "POLICY_NAME": policy["Name"],
                "GLOBAL_ROWS": global_rows,
                "CACHE_ROWS": cache_rows,
                "DEFAULT_CACHE": DEFAULT_CACHE_CONTROL,
                "PASSTHROUGH": ", ".join(PASSTHROUGH),
                "SAMPLE_EXACT": next(iter(exact), "/"),
                **readme_samples(dist, files, amplify),
            "SAMPLE_ASSET": next((f for f in files for r in path_rules if "cache-control" in {k.lower() for k, _ in r["headers"]} and any(fnmatch.fnmatch(f, g) for g in r["globs"])), "index.html"),
                "SAMPLE_EXACT_DEST": next(iter(exact.values()), [0, "/"])[1],
            }
        )
    )
    print(
        f"aws: {len(rules)} redirects -> {len(exact)} exact + {len(patterns)} pattern"
        f" ({len(shadowed)} dropped: duplicate source or shadowed by an earlier pattern, first rule wins as on Vercel) | kvs-redirects.json {kvs_size}/{KVS_MAX_FILE_BYTES} bytes"
        f" | viewer-request.js {size}/{CF_FUNCTION_MAX_BYTES} bytes | KVS {kvs_arn or 'PLACEHOLDER'}"
        f" | amplify rules {len(amplify)} | {len(files)} files in {len(groups)} upload groups -> {out}"
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python3 deploy/aws.py <dist>")
    try:
        main(Path(sys.argv[1]).resolve())
    except (Untranslatable, FileNotFoundError) as e:
        sys.exit(f"aws.py: cannot translate: {e}")
