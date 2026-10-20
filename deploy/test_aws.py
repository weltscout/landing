"""deploy/aws.py: builds the site into a temp dir, translates it, and runs the generated CloudFront Function
and contact Lambda in node.

    python3 -m unittest deploy/test_aws.py -v      (needs node 20+; WS_OLD_URLS overrides the old URL list)

Expected redirect targets are derived here independently of aws.py: a sample path per rule (pattern values
substituted), Vercel's first-match order, the destination with the captured values filled in.
"""

import fnmatch
import importlib.util
import itertools
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OLD_URLS = Path(
    os.environ.get(
        "WS_OLD_URLS",
        Path.home()
        / ".local/state/work/phases/S8/welt-scout/evidence/sitemap-urls.txt",
    )
)
PARAM = re.compile(r"(/):(\w+)(?:\(([^()]*)\))?([*+?]?)")
TEST_KVS_ID = "a1b2c3d4-5678-90ab-cdef-000000000000"
TEST_KVS_ARN = f"arn:aws:cloudfront::123456789012:key-value-store/{TEST_KVS_ID}"
HOSTILE_HTML_PATHS = ["//evil.com.html", "/\\evil.com.html", "///evil.com/index.html", "/\\/evil.com/index.html"]
STAR_SAMPLES = [None, "old-slug", "old/nested-slug"]
PLAIN_SAMPLE = "x1"

RUN_FUNCTION = r"""
// Runs dist/aws/viewer-request.js the way CloudFront does, with a fake 'cloudfront' module whose KeyValueStore
// is kvs-redirects.json: exists() answers, get() throws on a missing key (as the real one does).
// argv: function file, kvs-redirects.json, "fail" to make every KVS call throw (store unavailable).
const fs = require("fs"), vm = require("vm");
const IMPORT = "import cf from 'cloudfront';";
const src = fs.readFileSync(process.argv[2], "utf8");
if (!src.startsWith(IMPORT + "\n")) throw new Error("viewer-request.js does not start with " + IMPORT);
const store = new Map(JSON.parse(fs.readFileSync(process.argv[3], "utf8")).data.map(d => [d.key, d.value]));
const broken = process.argv[4] === "fail";
const kvsIds = [];
const cf = { kvs(id) { kvsIds.push(id); return {
  async exists(k) { if (broken) throw new Error("KVS unavailable"); return store.has(k); },
  async get(k) { if (broken) throw new Error("KVS unavailable"); if (!store.has(k)) throw new Error("Key not found: " + k); return store.get(k); },
}; } };
const handler = vm.runInNewContext("var cf = __cf;\n" + src.slice(IMPORT.length) + "\n;handler", { __cf: cf });
const cases = JSON.parse(fs.readFileSync(0, "utf8"));
(async () => {
  const out = [];
  for (const c of cases) {
    const qs = {};
    for (const [k, v] of c.qs || []) qs[k] = qs[k] ? { value: qs[k].value, multiValue: [...(qs[k].multiValue || [{ value: qs[k].value }]), { value: v }] } : { value: v };
    try {
      const r = await handler({ version: "1.0", context: { eventType: "viewer-request" }, viewer: { ip: "198.51.100.1" },
        request: { method: "GET", uri: c.uri, querystring: qs, headers: { host: { value: "www.example.test" } }, cookies: {} } });
      out.push(r.statusCode ? { status: r.statusCode, text: r.statusDescription, location: r.headers.location.value } : { uri: r.uri });
    } catch (e) { out.push({ error: e.message }); }
  }
  console.log(JSON.stringify({ results: out, kvsIds }));
})();
"""

RUN_CONTACT = r"""
const { createRequire } = require("module");
const lambdaDir = process.argv[2], vercelFn = require(process.argv[3]);
let fetchOk = true, fetchCalls = 0;
globalThis.fetch = async (url, opts) => { fetchCalls++; return { ok: fetchOk }; };
const ENV = { RESEND_API_KEY: "test-key", CONTACT_FROM: "from@example.test", CONTACT_TO: "to@example.test" };
const valid = { name: "Ana", email: "ana@example.test", msg: "Zdravo", consent: true, topic: "preizkus", lang: "sl" };
const cases = [
  ["GET", "application/json", undefined, true, true],
  ["POST", "application/json", {}, true, true],
  ["POST", "application/json", { ...valid, website: "bot" }, true, true],
  ["POST", "application/json", { ...valid, consent: "yes" }, true, true],
  ["POST", "application/json", { ...valid, email: "not-an-email" }, true, true],
  ["POST", "application/json", valid, false, true],
  ["POST", "application/json", valid, true, false],
  ["POST", "application/json", valid, true, true],
  ["POST", "text/plain", "{not json", true, true],
];
(async () => {
  const { handler } = await import(lambdaDir + "/index.mjs");
  const out = [];
  for (const [method, type, body, env, ok] of cases) {
    for (const k of Object.keys(ENV)) { if (env) process.env[k] = ENV[k]; else delete process.env[k]; }
    fetchOk = ok;
    let vercel = null;
    const res = { setHeader() { return res; }, status(c) { return { json(o) { vercel = { status: c, body: o }; } }; } };
    await vercelFn({ method, body }, res);
    const raw = body === undefined ? undefined : typeof body === "string" ? body : JSON.stringify(body);
    const l = await handler({ version: "2.0", requestContext: { http: { method } }, headers: { "content-type": type }, body: raw, isBase64Encoded: false });
    const b64 = raw === undefined ? null : await handler({ version: "2.0", requestContext: { http: { method } }, headers: { "Content-Type": type }, body: Buffer.from(raw).toString("base64"), isBase64Encoded: true });
    out.push({ method, body, vercel, lambda: { status: l.statusCode, body: JSON.parse(l.body), type: l.headers["content-type"], allow: l.headers.allow }, b64: b64 && { status: b64.statusCode, body: JSON.parse(b64.body) } });
  }
  process.env.RESEND_API_KEY = "k"; process.env.CONTACT_FROM = "f@example.test";
  const bad = await handler({ requestContext: { http: { method: "POST" } }, headers: { "content-type": "application/json" }, body: "{not json" });
  console.log(JSON.stringify({ cases: out, badJson: { status: bad.statusCode, body: JSON.parse(bad.body) }, fetchCalls }));
})();
"""


def load_aws():
    spec = importlib.util.spec_from_file_location("ws_aws", HERE / "aws.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def node(script, *args, stdin=None):
    with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False) as f:
        f.write(script)
    try:
        r = subprocess.run(
            ["node", f.name, *args],
            input=stdin,
            capture_output=True,
            text=True,
            timeout=120,
        )
    finally:
        os.unlink(f.name)
    if r.returncode != 0:
        raise AssertionError(f"node failed: {r.stderr}")
    return json.loads(r.stdout)


def source_regex(source):
    """Vercel source -> Python regex (strict, case-sensitive) with one group per parameter."""
    rx, pos, names = "^", 0, []
    for m in PARAM.finditer(source):
        rx += re.escape(source[pos : m.start()])
        _, name, alts, mod = m.groups()
        names.append(name)
        if mod == "*":
            rx += r"(?:/([^/]+(?:/[^/]+)*))?"
        elif alts:
            rx += f"/({alts})"
        else:
            rx += r"/([^/]+)"
        pos = m.end()
    return re.compile(rx + re.escape(source[pos:]) + "$"), names


def fill(dest, values):
    def sub(m):
        v = values.get(m.group(2))
        return "" if v is None else "/" + v

    return PARAM.sub(sub, dest)


def samples(source):
    params = PARAM.findall(source)
    choices = []
    for _, _, alts, mod in params:
        choices.append(
            STAR_SAMPLES if mod == "*" else alts.split("|") if alts else [PLAIN_SAMPLE]
        )
    for combo in itertools.product(*choices):
        values = {p[1]: v for p, v in zip(params, combo)}
        yield fill(source, values)


def vercel_location(rules, path):
    for rule in rules:
        rx, names = source_regex(rule["source"])
        m = rx.match(path)
        if m:
            return fill(rule["destination"], dict(zip(names, m.groups())))
    return None


def amplify_location(rules, path):
    """Amplify semantics as documented: first rule wins, <*> = the rest of the path, <name> = one segment."""
    for rule in rules:
        rx = ""
        for part in re.split(r"(<[^>]+>)", rule["source"]):
            if part == "<*>":
                rx += "(?P<star>.*)"
            elif part.startswith("<"):
                rx += f"(?P<{part[1:-1]}>[^/]+)"
            else:
                rx += re.escape(part)
        m = re.fullmatch(rx, path)
        if m:
            target = rule["target"].replace("<*>", m.groupdict().get("star") or "")
            return rule["status"], re.sub(r"<(\w+)>", lambda x: m.group(x.group(1)), target)
    return None


class AwsTranslation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="ws-aws-"))
        cls.dist = cls.tmp / "dist"
        for script in ("build.py", "aws.py"):
            r = subprocess.run(
                [sys.executable, str(HERE / script), str(cls.dist)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                env={**os.environ, "WS_CF_KVS_ARN": TEST_KVS_ARN},
            )
            if r.returncode != 0:
                raise AssertionError(f"{script} failed:\n{r.stdout}\n{r.stderr}")
            print(r.stdout.strip().splitlines()[-1])
        cls.aws = cls.dist / "aws"
        cls.vercel = json.loads((cls.dist / "vercel.json").read_text())
        cls.rules = cls.vercel["redirects"]

    def run_aws(self, name, cfg, env=None):
        """aws.py on a copy of the built site with a modified vercel.json."""
        d = self.tmp / name
        shutil.copytree(self.dist, d, ignore=shutil.ignore_patterns("aws"))
        (d / "vercel.json").write_text(json.dumps(cfg))
        environ = {k: v for k, v in os.environ.items() if k != "WS_CF_KVS_ARN"}
        r = subprocess.run(
            ["python3", str(HERE / "aws.py"), str(d)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            env={**environ, **(env if env is not None else {"WS_CF_KVS_ARN": TEST_KVS_ARN})},
        )
        return r, d / "aws"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def run_fn(self, cases, aws=None, mode="ok"):
        aws = aws or self.aws
        cases = [c if isinstance(c, dict) else {"uri": c} for c in cases]
        out = node(
            RUN_FUNCTION,
            str(aws / "viewer-request.js"),
            str(aws / "kvs-redirects.json"),
            mode,
            stdin=json.dumps(cases),
        )
        self.last_kvs_ids = out["kvsIds"]
        return out["results"]

    def exists(self, uri):
        return (self.dist / uri.lstrip("/")).is_file()

    def test_every_redirect_source(self):
        paths = sorted({p for rule in self.rules for p in samples(rule["source"])})
        results = self.run_fn(paths)
        wrong = []
        for path, res in zip(paths, results):
            want = vercel_location(self.rules, path)
            if res.get("status") != 301 or res.get("location") != want:
                wrong.append((path, want, res))
        print(f"redirect samples checked: {len(paths)} from {len(self.rules)} rules")
        self.assertEqual(wrong, [])
        self.assertGreater(len(paths), len(self.rules))

    def test_query_string_kept(self):
        res = self.run_fn(
            [{"uri": "/post/anything", "qs": [["x", "1"], ["y", "2"], ["x", "3"]]}]
        )[0]
        self.assertEqual(
            res["location"],
            vercel_location(self.rules, "/post/anything") + "?x=1&x=3&y=2",
        )

    def test_clean_urls(self):
        slug = sorted(
            p.name for p in (self.dist / "de" / "blog").iterdir() if p.is_dir()
        )[0]
        hr_page = sorted(
            p.name for p in (self.dist / "hr").iterdir() if (p / "index.html").is_file() and p.name != "blog"
        )[0]
        cases = {
            "/sl/": "/sl/index.html",
            "/sl": "/sl/index.html",
            f"/de/blog/{slug}/": f"/de/blog/{slug}/index.html",
            f"/hr/{hr_page}": f"/hr/{hr_page}/index.html",
            "/": "/index.html",
            "/tokens.css": "/tokens.css",
            "/api/contact": "/api/contact",
        }
        results = self.run_fn(list(cases))
        for (uri, want), res in zip(cases.items(), results):
            self.assertEqual(res, {"uri": want}, uri)
            if not uri.startswith("/api/"):
                self.assertTrue(self.exists(want), want)
        # /hr/privacy-policy became a 301 to the localized legal page; it must still reach a file in one hop.
        res = self.run_fn(["/hr/privacy-policy"])[0]
        want = vercel_location(self.rules, "/hr/privacy-policy")
        if want is None:
            self.assertEqual(res, {"uri": "/hr/privacy-policy/index.html"})
        else:
            self.assertEqual(res.get("location"), want)
            self.assertTrue(self.exists(self.run_fn([want])[0]["uri"]), want)

    def test_html_extension_redirects_like_clean_urls(self):
        res = self.run_fn(
            ["/sl/index.html", "/index.html", "/hr/privacy-policy/index.html"]
        )
        self.assertEqual(
            [r.get("location") for r in res], ["/sl", "/", "/hr/privacy-policy"]
        )

    def test_old_sitemap_urls_reach_a_file_in_one_redirect(self):
        if not OLD_URLS.is_file():
            self.skipTest(f"old URL list missing: {OLD_URLS} (set WS_OLD_URLS)")
        paths = [
            urlparse(u.strip()).path or "/"
            for u in OLD_URLS.read_text().split()
            if u.strip()
        ]
        first = self.run_fn(paths)
        targets = [
            r["location"] if "location" in r else p for p, r in zip(paths, first)
        ]
        second = self.run_fn(targets)
        bad = []
        for path, a, b in zip(paths, first, second):
            if "uri" not in b or not self.exists(b["uri"]):
                bad.append((path, a, b))
        redirected = sum(1 for r in first if "location" in r)
        print(
            f"old URLs: {len(paths)}, redirected once: {redirected}, served directly: {len(paths) - redirected}"
        )
        self.assertEqual(bad, [])

    def test_function_fits_cloudfront_limit(self):
        size = (self.aws / "viewer-request.js").stat().st_size
        limit = load_aws().CF_FUNCTION_MAX_BYTES
        print(f"viewer-request.js: {size} of {limit} bytes")
        self.assertLessEqual(size, limit)

    def test_amplify_rules_match_vercel(self):
        rules = json.loads((self.aws / "amplify-redirects.json").read_text())
        paths = sorted({p for rule in self.rules for p in samples(rule["source"])})
        wrong = [
            (p, vercel_location(self.rules, p), amplify_location(rules, p))
            for p in paths
            if amplify_location(rules, p) != ("301", vercel_location(self.rules, p))
        ]
        self.assertEqual(wrong, [])

    def test_headers_policy_and_custom_http_carry_every_global_header(self):
        policy = json.loads((self.aws / "response-headers.json").read_text())
        names = {
            h["Header"].lower()
            for h in policy.get("CustomHeadersConfig", {}).get("Items", [])
        }
        sec = {
            "ContentTypeOptions": "x-content-type-options",
            "ReferrerPolicy": "referrer-policy",
            "FrameOptions": "x-frame-options",
            "ContentSecurityPolicy": "content-security-policy",
            "StrictTransportSecurity": "strict-transport-security",
        }
        names |= {sec[k] for k in policy.get("SecurityHeadersConfig", {})}
        glob = [
            h
            for r in self.vercel["headers"]
            if r["source"] == "/(.*)"
            for h in r["headers"]
        ]
        self.assertEqual(names, {h["key"].lower() for h in glob})
        custom = (self.aws / "customHttp.yml").read_text()
        for h in (h for r in self.vercel["headers"] for h in r["headers"]):
            self.assertIn(f"key: '{h['key']}'", custom)
            self.assertIn(f"value: '{h['value']}'", custom)

    def test_s3_upload_covers_every_file_once_with_vercel_headers(self):
        files = sorted(
            p.relative_to(self.dist).as_posix()
            for p in self.dist.rglob("*")
            if p.is_file()
        )
        site = [
            f
            for f in files
            if not (f.startswith(("api/", "aws/")) or f == "vercel.json")
        ]
        seen = {}
        for line in (self.aws / "s3-sync.sh").read_text().splitlines():
            if not line.startswith("aws s3 cp "):
                continue
            argv = shlex.split(line)
            filters = [
                (argv[i], argv[i + 1])
                for i in range(len(argv) - 1)
                if argv[i] in ("--include", "--exclude")
            ]
            ctype, cache = (
                argv[argv.index("--content-type") + 1],
                argv[argv.index("--cache-control") + 1],
            )
            for f in files:
                take = True
                for kind, g in filters:
                    if fnmatch.fnmatch(f, g):
                        take = kind == "--include"
                if take:
                    self.assertNotIn(f, seen, f"{f} uploaded twice")
                    seen[f] = (ctype, cache)
        self.assertEqual(sorted(seen), site)
        img_cache = next(
            h["value"]
            for r in self.vercel["headers"]
            if "img" in r["source"]
            for h in r["headers"]
        )
        self.assertTrue(
            all(
                seen[f][1] == img_cache
                for f in site
                if f.startswith(("img/", "fonts/"))
            )
        )
        self.assertEqual(seen["llms.txt"][0], "text/plain; charset=utf-8")
        self.assertTrue(seen["index.html"][0].startswith("text/html"))

    def test_contact_lambda_answers_like_the_vercel_function(self):
        r = node(
            RUN_CONTACT,
            str(self.aws / "contact-lambda"),
            str(HERE / "api" / "contact.js"),
        )
        for c in r["cases"]:
            self.assertEqual(
                (c["lambda"]["status"], c["lambda"]["body"]),
                (c["vercel"]["status"], c["vercel"]["body"]),
                c,
            )
            self.assertTrue(c["lambda"]["type"].startswith("application/json"))
            if c["b64"]:
                self.assertEqual(
                    c["b64"],
                    {"status": c["vercel"]["status"], "body": c["vercel"]["body"]},
                )
        statuses = [c["lambda"]["status"] for c in r["cases"]]
        print("contact statuses:", statuses, "| bad JSON:", r["badJson"]["status"])
        self.assertEqual(sorted(set(statuses)), [200, 400, 405, 422, 502, 503])
        self.assertEqual(r["cases"][0]["lambda"]["allow"], "POST")
        self.assertEqual(
            r["badJson"], {"status": 400, "body": {"ok": False, "error": "json"}}
        )

    def test_untranslatable_config_fails_loudly(self):
        bad = {
            "rewrites": {
                **self.vercel,
                "rewrites": [{"source": "/a", "destination": "/b"}],
            },
            "has": {
                **self.vercel,
                "redirects": [
                    {
                        "source": "/a",
                        "destination": "/b",
                        "permanent": True,
                        "has": [{"type": "host", "value": "x"}],
                    }
                ],
            },
            "regex": {
                **self.vercel,
                "redirects": [
                    {"source": "/:id(\\d+)", "destination": "/b", "permanent": True}
                ],
            },
            "header": {
                **self.vercel,
                "headers": [
                    {
                        "source": "/img/(.*)",
                        "headers": [{"key": "X-Frame-Options", "value": "DENY"}],
                    }
                ],
            },
        }
        for name, cfg in bad.items():
            d = self.tmp / f"bad-{name}"
            d.mkdir()
            (d / "vercel.json").write_text(json.dumps(cfg))
            r = subprocess.run(
                ["python3", str(HERE / "aws.py"), str(d)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(r.returncode, 0, name)
            self.assertIn("cannot translate", r.stderr, name)
            self.assertFalse((d / "aws").exists(), name)

    def test_exact_redirects_live_in_the_kvs_not_in_the_function(self):
        data = json.loads((self.aws / "kvs-redirects.json").read_text())["data"]
        keys = [d["key"] for d in data]
        exact = [r["source"] for r in self.rules if not PARAM.search(r["source"])]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(set(keys), set(exact))
        code = (self.aws / "viewer-request.js").read_text()
        self.assertFalse([k for k in keys if json.dumps(k) in code], "exact redirect sources inlined in the function")
        self.run_fn([keys[0]])
        self.assertEqual(self.last_kvs_ids, [TEST_KVS_ID])
        print(f"KVS: {len(keys)} keys, function {len(code.encode())} bytes")

    def test_kvs_failure_is_not_swallowed(self):
        res = self.run_fn(["/sl/", self.rules[0]["source"]], mode="fail")
        self.assertTrue(all("error" in r for r in res), res)

    def test_no_location_to_another_host_from_the_uri(self):
        res = self.run_fn(HOSTILE_HTML_PATHS)
        for path, r in zip(HOSTILE_HTML_PATHS, res):
            loc = r.get("location")
            self.assertTrue(loc is None or (loc.startswith("/") and loc[1:2] not in ("/", "\\")), (path, r))
            self.assertNotIn("evil.com", loc or "", (path, r))

    def test_pattern_destination_from_the_uri_stays_on_this_host(self):
        cfg = {**self.vercel, "redirects": [{"source": "/go/:dest*", "destination": "/:dest*", "permanent": True}]}
        r, aws = self.run_aws("hostile-pattern", cfg)
        self.assertEqual(r.returncode, 0, r.stderr)
        res = self.run_fn(["/go/\\evil.com", "/go/ok/path"], aws=aws)
        self.assertNotIn("location", res[0], res[0])
        self.assertEqual(res[1].get("location"), "/ok/path")

    def test_missing_kvs_arn_warns_and_writes_a_placeholder(self):
        r, aws = self.run_aws("no-arn", self.vercel, env={})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("WARNING WS_CF_KVS_ARN is not set", r.stderr)
        self.assertIn("SET-WS_CF_KVS_ARN-AND-RERUN-AWS-PY", (aws / "viewer-request.js").read_text())
        self.assertIn("PLACEHOLDER", r.stdout)
        r, aws = self.run_aws("bad-arn", self.vercel, env={"WS_CF_KVS_ARN": "kvs-123"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("is not a CloudFront KeyValueStore ARN", r.stderr)
        self.assertFalse(aws.exists())

    def test_status_goes_into_the_value_only_when_one_differs(self):
        rules = [dict(r) for r in self.rules]
        first = next(i for i, r in enumerate(rules) if not PARAM.search(r["source"]))
        rules[first]["permanent"] = False
        r, aws = self.run_aws("status", {**self.vercel, "redirects": rules})
        self.assertEqual(r.returncode, 0, r.stderr)
        data = {d["key"]: d["value"] for d in json.loads((aws / "kvs-redirects.json").read_text())["data"]}
        self.assertTrue(data[rules[first]["source"]].startswith("302 /"))
        other = next(k for k in data if k != rules[first]["source"])
        self.assertTrue(data[other].startswith("301 /"))
        res = self.run_fn([rules[first]["source"], other], aws=aws)
        self.assertEqual([x["status"] for x in res], [302, 301])
        self.assertEqual(res[0]["location"], rules[first]["destination"])
        plain = json.loads((self.aws / "kvs-redirects.json").read_text())["data"][0]["value"]
        self.assertTrue(plain.startswith("/"), plain)

    def test_kvs_size_limits_fail_loudly(self):
        long_key = {**self.vercel, "redirects": [{"source": "/" + "k" * 600, "destination": "/sl/", "permanent": True}]}
        long_value = {**self.vercel, "redirects": [{"source": "/a", "destination": "/" + "v" * 1100, "permanent": True}]}
        for name, cfg in (("long-key", long_key), ("long-value", long_value)):
            r, aws = self.run_aws(name, cfg)
            self.assertNotEqual(r.returncode, 0, name)
            self.assertIn("cannot translate", r.stderr, name)
            self.assertFalse(aws.exists(), name)


if __name__ == "__main__":
    unittest.main()
