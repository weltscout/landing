"""deploy/edge_script.py: builds the site, generates the Bunny middleware, and runs the
generated logic (deploy/edge_core.js) in node.

    python3 -m unittest deploy/test_edge_script.py -v      (needs node 20+)

Expected outcomes are derived here independently of the generator: rule order and
Vercel's first-match semantics from dist/vercel.json, destinations with sample
values filled in, cleanUrls resolution against the built file list, and the contact
status matrix from deploy/api/contact.js. submitContact payloads are asserted
structurally — the boundary to the Chatwoot Client API is part of the contract.
"""

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent

NODE_DRIVER = """
const [corePath, dataPath, casesJson] = process.argv.slice(1);
const core = require(corePath);
const data = require(dataPath);
const cases = JSON.parse(casesJson);
(async () => {
  const decisions = [], sent = [];
  for (const c of cases) {
    const deps = {
      submitContact: async (p) => { sent.push(p); return c.send || { ok: true }; },
    };
    decisions.push(await core.wsHandle(data, c.req, deps));
  }
  console.log(JSON.stringify({ decisions, sent }));
})();
"""

VALID_BODY = {
    "name": "Ana",
    "company": "Acme",
    "email": "ana@example.com",
    "tel": "+38612345678",
    "msg": "Pozdravljeni",
    "topic": "preizkus",
    "consent": True,
    "lang": "sl",
}

PARAM = re.compile(r":([A-Za-z_][A-Za-z0-9_]*)\(([^()]*)\)([*+?])?|:([A-Za-z_][A-Za-z0-9_]*)([*+?])?")
SRC_TOKEN = re.compile(
    r":([A-Za-z_][A-Za-z0-9_]*)\(([^()]*)\)([*+?])?|:([A-Za-z_][A-Za-z0-9_]*)([*+?])?|\(([^()]*)\)"
)


class EdgeScript(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="ws-edge-"))
        cls.dist = cls.tmp / "dist"
        for script in ("build.py", "edge_script.py"):
            r = subprocess.run(
                [sys.executable, str(HERE / script), str(cls.dist)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            if r.returncode != 0:
                raise AssertionError(f"{script} failed:\n{r.stdout}\n{r.stderr}")
            print(r.stdout.strip().splitlines()[-1])
        cls.vercel = json.loads((cls.dist / "vercel.json").read_text())
        cls.rules = cls.vercel["redirects"]
        cls.data = json.loads((cls.dist / "edge_data.json").read_text())
        cls.bundle = (cls.dist / "edge_script.js").read_text()
        cls.core = HERE / "edge_core.js"

    # --- redirects ---

    def test_every_rule_is_translated_in_order(self):
        self.assertEqual(len(self.data["redirects"]), len(self.rules))
        for vr, dr in zip(self.rules, self.data["redirects"]):
            want_status = vr.get("statusCode") if "statusCode" in vr else (301 if vr.get("permanent") else 302)
            self.assertEqual(dr["status"], want_status, vr["source"])

    def test_redirects_first_match_wins(self):
        for rule in self.rules:
            path = sample_path(rule["source"])
            want = first_match(self.rules, path)
            self.assertEqual(
                want, rule, f"{rule['source']}: sample {path} is shadowed by an earlier rule"
            )
            out = self.run_cases([{"req": {"method": "GET", "path": path, "query": ""}}])
            got = out["decisions"][0]
            self.assertEqual(got["type"], "redirect", rule["source"])
            self.assertEqual(got["status"], redirect_status(rule), rule["source"])
            self.assertEqual(got["location"], expected_destination(rule), rule["source"])
            self.assertEqual(got["headers"], self.expected_headers(path), rule["source"])

    def test_redirects_keep_the_query_string(self):
        rule = next(r for r in self.rules if is_exact(r["source"]))
        path = rule["source"]
        out = self.run_cases([{"req": {"method": "GET", "path": path, "query": "utm=x"}}])
        self.assertEqual(out["decisions"][0]["location"], expected_destination(rule) + "?utm=x")

    # --- cleanUrls ---

    def test_html_extension_redirects_like_clean_urls(self):
        paths = ["/sl/index.html", "/index.html", "/hr/privacy-policy/index.html"]
        want = ["/sl", "/", "/hr/privacy-policy"]
        out = self.run_cases([{"req": {"method": "GET", "path": p, "query": ""}} for p in paths])
        self.assertEqual([d.get("location") for d in out["decisions"]], want)
        self.assertEqual([d["status"] for d in out["decisions"]], [301, 301, 301])

    def test_extensionless_paths_resolve_to_real_files(self):
        blog_file = self.blog_file()
        blog_path, blog_file = clean_path_and_file(blog_file)
        candidates = {"/": "index.html", "/sl": "sl/index.html", "/sl/": "sl/index.html", blog_path: blog_file}
        # A path claimed by a redirect rule must redirect (/hr/privacy-policy
        # does) — only unclaimed paths exercise clean-URL resolution.
        samples = {p: f for p, f in candidates.items() if not matches_any(self.rules, p)}
        self.assertGreaterEqual(len(samples), 3, candidates)
        out = self.run_cases([{"req": {"method": "GET", "path": p, "query": ""}} for p in samples])
        self.assertEqual([d["path"] for d in out["decisions"]], ["/" + f for f in samples.values()])
        self.assertTrue(all(d["type"] == "rewrite" for d in out["decisions"]))

    # Old URLs that earned clicks or impressions in GSC but had no specific rule (SEO audit
    # 28. 10., DEMAND.md section 6): each must reach its same-topic page in one 301, and
    # that page must be a built file.
    AUDITED_OLD_URLS = {
        "/hr/post/skriveni-troskovi-pri-kupnji-rabljenog-vozila-na-sto-treba-obratiti-paznju": "/hr/blog/troskovi-kupnje-rabljenog-automobila/",
        "/en/post/how-to-use-the-weltscout-platform": "/en/blog/how-to-use-weltscout-platform/",
        "/en/post/hidden-costs-when-buying-a-used-vehicle-what-should-you-pay-attention-to": "/en/blog/hidden-costs-buying-used-car/",
        "/en/post/news-on-the-weltscout-platform": "/en/blog/what-weltscout-does-today/",
        "/en/post/news-on-the-wltscout-platform": "/en/blog/what-weltscout-does-today/",
        "/hr/post/kako-koristiti-platformu-weltscout": "/hr/blog/kako-koristiti-weltscout-platformu/",
        "/hr/post/novosti-na-platformi-weltscout": "/hr/blog/sto-weltscout-nudi-danas/",
        "/post/kateri-mesec-najcenejsi-za-nakup-avtomobila": "/sl/blog/kdaj-je-najbolje-kupiti-avto/",
        "/post/best-car-sourcing-platforms-3": "/sl/blog/avto-iskalnik/",
        "/fr/blog": "/fr/blog/",
        "/fr/post/kateri-so-najboljsi-rabljeni-avti": "/fr/",
        "/legal": "/sl/splosni-pogoji/",
    }

    def assert_one_hop(self, table):
        first = self.run_cases([{"req": {"method": "GET", "path": p, "query": ""}} for p in table])
        for (src, want), d in zip(table.items(), first["decisions"]):
            self.assertEqual((d["type"], d.get("status"), d.get("location")), ("redirect", 301, want), src)
        second = self.run_cases([{"req": {"method": "GET", "path": w, "query": ""}} for w in table.values()])
        for w, d in zip(table.values(), second["decisions"]):
            self.assertEqual(d["type"], "rewrite", w)
            self.assertIn(d["path"].lstrip("/"), self.data["files"], w)

    def test_audited_old_urls_reach_their_page_in_one_hop(self):
        self.assert_one_hop(self.AUDITED_OLD_URLS)

    def test_unknown_old_posts_land_on_their_language_home_in_every_language(self):
        codes = [l["code"] for l in json.loads((HERE / "langs.json").read_text())["langs"]]
        self.assert_one_hop({f"/{c}/post/no-such-old-post": f"/{c}/" for c in codes})

    def test_trailing_slash_form_of_every_exact_legacy_url_redirects_the_same_way(self):
        exact = [r for r in self.rules if is_exact(r["source"]) and "/post" in r["source"] and not r["source"].endswith("/")]
        self.assertTrue(exact)
        table = {r["source"] + "/": r["destination"] for r in exact}
        self.assert_one_hop(table)
        self.assert_one_hop({"/post/no-such-old-post/": "/sl/", "/en/post/no-such-old-post/": "/en/"})

    def test_every_response_carries_hsts(self):
        for path in ("/", "/sl/", "/en/blog/", "/img/logo-weltscout-t3.svg", "/no/such/page"):
            self.assertRegex(self.expected_headers(path).get("Strict-Transport-Security", ""), r"^max-age=\d+$", path)

    def test_unknown_paths_get_the_branded_404_of_their_language(self):
        # Paths that are no built file used to pass through to the origin, whose default
        # 404 loads a third-party font; now the edge answers 404 with the built page.
        table = {"/no/such/page": "/404.html", "/en/no-such-page": "/en/404.html", "/hr/blog/nope/": "/hr/404.html", "/xx/y": "/404.html"}
        out = self.run_cases([{"req": {"method": "GET", "path": p, "query": ""}} for p in table])
        for (path, page), got in zip(table.items(), out["decisions"]):
            self.assertEqual((got["type"], got["status"], got["path"]), ("notfound", 404, page), path)
            self.assertEqual(got["headers"], self.expected_headers(path))
            self.assertIn(page.lstrip("/"), self.data["files"])

    def test_api_source_is_not_uploaded_but_the_endpoint_answers(self):
        self.assertFalse([f for f in self.data["files"] if f.startswith("api/")])
        out = self.run_cases([{"req": {"method": "GET", "path": "/api/contact.js", "query": ""}}, {"req": {"method": "GET", "path": "/api/contact", "query": ""}}])
        self.assertEqual(out["decisions"][0]["status"], 404)
        self.assertEqual(out["decisions"][1]["status"], 405)

    def test_every_built_file_is_served_not_404(self):
        files = [f for f in self.data["files"] if not f.endswith(".html")][:40]
        out = self.run_cases([{"req": {"method": "GET", "path": "/" + f, "query": ""}} for f in files])
        for f, got in zip(files, out["decisions"]):
            self.assertEqual((got["type"], got["path"]), ("rewrite", "/" + f), f)

    # --- /api/contact (deploy/api/contact.js) ---

    def test_contact_status_matrix(self):
        cases = [
            {"req": {"method": "GET", "path": "/api/contact"}},
            {"req": {"method": "POST", "path": "/api/contact", "body": json.dumps({**VALID_BODY, "name": ""})}},
            {"req": {"method": "POST", "path": "/api/contact", "body": json.dumps({**VALID_BODY, "website": "spam"})}},
            {"req": {"method": "POST", "path": "/api/contact", "body": json.dumps({**VALID_BODY, "email": "nope"})}},
            {"req": {"method": "POST", "path": "/api/contact", "body": json.dumps({k: v for k, v in VALID_BODY.items() if k != "consent"})}},
            {"req": {"method": "POST", "path": "/api/contact", "body": json.dumps(VALID_BODY)}, "send": {"ok": False}},
            {"req": {"method": "POST", "path": "/api/contact", "body": json.dumps(VALID_BODY)}, "send": {"ok": True}},
            {"req": {"method": "POST", "path": "/api/contact", "body": "{bad json"}},
        ]
        want_status = [405, 422, 200, 422, 422, 502, 200, 400]
        out = self.run_cases(cases)
        self.assertEqual([d["status"] for d in out["decisions"]], want_status)
        self.assertEqual(out["decisions"][0]["headers"].get("Allow"), "POST")
        self.assertEqual(len(out["sent"]), 2)  # the 502 and the 200 both reach submitContact
        for payload in out["sent"]:
            self.assertEqual(sorted(payload), ["content", "email", "name"])
            self.assertEqual(payload["name"], VALID_BODY["name"])
            self.assertEqual(payload["email"], VALID_BODY["email"])
            self.assertIn("Ime: Ana", payload["content"])
            self.assertIn("Zanima ga: Preizkus", payload["content"])
            self.assertIn(VALID_BODY["msg"], payload["content"])

    # --- response headers (vercel.json headers) ---

    def test_response_headers_apply_in_rule_order(self):
        # Contract: the middleware attaches exactly the headers vercel.json
        # declares for the request path (the noindex header only exists when the
        # build ran with WS_INDEXABLE=0 — expected_headers tracks the config).
        paths = ["/", "/sl/blog/x/", "/fonts/a.woff2", "/img/b.png", "/llms.txt"]
        out = self.run_cases([{"req": {"method": "GET", "path": p, "query": ""}} for p in paths])
        for path, got in zip(paths, out["decisions"]):
            self.assertEqual(got["headers"], self.expected_headers(path), path)
        self.assertIn("max-age=86400", out["decisions"][2]["headers"].get("Cache-Control", ""))
        self.assertNotIn("Cache-Control", out["decisions"][0]["headers"])
        self.assertEqual(out["decisions"][4]["headers"].get("Content-Type"), "text/plain; charset=utf-8")

    def test_contact_constants_match_contact_js(self):
        # edge_core.js is a hand port of deploy/api/contact.js — the shared
        # literals must not drift apart silently. (Behavior is pinned by the
        # status matrix above; test_aws.py runs the real contact.js against the
        # same matrix.) The delivery block is shared between contact.js and the
        # edge bundle template the same way.
        src = (HERE / "api" / "contact.js").read_text()
        core = self.core.read_text()
        template = (HERE / "edge-templates" / "script.template.js").read_text()
        for decl in ("const TOPICS =", "const MAX =", "const rows =", "const content ="):
            self.assertEqual(line_with(src, decl), line_with(core, decl), decl)
        self.assertIn(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$", src)
        self.assertIn(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$", core)
        self.assertEqual(line_with(src, "const CHATWOOT ="), line_with(template, "const CHATWOOT ="))
        self.assertEqual(fn_block(src, "submitContact"), fn_block(template, "submitContact"))

    # --- generator contract ---

    def test_untranslatable_constructs_fail_without_output(self):
        broken = [
            {"cleanUrls": True, "headers": [], "redirects": [], "rewrites": []},
            {"cleanUrls": True, "headers": [], "redirects": [{"source": "/a/:slug+", "destination": "/b/", "permanent": True}]},
            {"cleanUrls": True, "headers": [], "redirects": [{"source": "/ab:rest*", "destination": "/b/", "permanent": True}]},
            {"cleanUrls": True, "headers": [], "redirects": [{"source": "/a", "destination": "/:x/", "permanent": True}]},
            {"cleanUrls": True, "headers": [], "redirects": [{"source": "/a", "destination": "/b", "permanent": True, "has": []}]},
            {"cleanUrls": True, "headers": [], "redirects": [{"source": "/a", "destination": "/b", "permanent": True, "statusCode": 301}]},
            {"cleanUrls": False, "headers": [], "redirects": []},
        ]
        for cfg in broken:
            d = Path(tempfile.mkdtemp(prefix="ws-edge-broken-")) / "dist"
            d.mkdir(parents=True)
            (d / "vercel.json").write_text(json.dumps(cfg))
            (d / "index.html").write_text("x")
            r = subprocess.run(
                [sys.executable, str(HERE / "edge_script.py"), str(d)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(r.returncode, 0, cfg)
            self.assertFalse((d / "edge_script.js").exists(), cfg)

    def test_pattern_rules_match_vercel_semantics(self):
        # Concrete match tables for the two pattern rules — the sample-based
        # redirect test above cannot catch a wrong generated regex on
        # zero-segment or multi-segment edges.
        tables = {
            "/post/:slug*": {
                "/post": True, "/post/": True, "/post/a": True, "/post/a/b": True, "/post/a/": True, "/post/a/b/": True,
                "/posta": False, "/other": False,
            },
            # the language catch-all covers every language in langs.json (no hand list)
            "/:lang({})/post/:slug*".format("|".join(l["code"] for l in json.loads((HERE / "langs.json").read_text())["langs"])): {
                "/hr/post": True, "/hr/post/x": True, "/de/post/a/b": True, "/fr/post/x": True, "/sr/post/x": True, "/en/post/x/": True,
                "/xx/post": False, "/hr/other": False,
            },
        }
        patterns = [
            (vr["source"], dr["re"])
            for vr, dr in zip(self.rules, self.data["redirects"])
            if not is_exact(vr["source"])
        ]
        self.assertEqual([s for s, _ in patterns], list(tables))
        for source, re_src in patterns:
            for path, want in tables[source].items():
                self.assertEqual(bool(re.fullmatch(re_src, path)), want, f"{source} vs {path}")

    def test_bundle_is_core_plus_data_plus_glue(self):
        self.assertIn(self.core.read_text(), self.bundle)
        self.assertIn(json.dumps(self.data, ensure_ascii=False, indent=1), self.bundle)
        self.assertIn(".onClientRequest(", self.bundle)
        self.assertIn(".onClientResponse(", self.bundle)
        self.assertIn("weltscout-landing.b-cdn.net", self.bundle)
        mjs = Path(tempfile.mkdtemp(prefix="ws-edge-syntax-")) / "edge_script.mjs"
        mjs.write_text(self.bundle)
        r = subprocess.run(["node", "--check", str(mjs)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_stage_upload_copies_exactly_the_site_files(self):
        # The upload set and the middleware's clean-URL file list must be the
        # same set — both come from edge_script.site_files.
        dest = self.tmp / "upload"
        r = subprocess.run(
            [sys.executable, str(HERE / "stage_upload.py"), str(self.dist), str(dest)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        copied = sorted(p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file())
        self.assertEqual(copied, sorted(self.data["files"]))
        for banned in ("vercel.json", "edge_script.js", "edge_data.json"):
            self.assertNotIn(banned, copied)

    # --- helpers ---

    def run_cases(self, cases):
        r = subprocess.run(
            ["node", "-e", NODE_DRIVER, str(self.core), str(self.dist / "edge_data.json"), json.dumps(cases)],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            raise AssertionError(f"node driver failed:\n{r.stdout}\n{r.stderr}")
        return json.loads(r.stdout)

    def blog_file(self):
        files = [f for f in self.data["files"] if f.startswith("sl/blog/")]
        plain = [f for f in files if not f.endswith("/index.html")]
        return (plain or files)[0]

    def expected_headers(self, path):
        out = {}
        for rule in self.vercel["headers"]:
            if re.fullmatch(translate_source(rule["source"]), path):
                for h in rule["headers"]:
                    out[h["key"]] = h["value"]
        return out


# --- independent expectation derivation (not shared with the generator) ---


def is_exact(source):
    return ":" not in source and "(" not in source


def line_with(text, decl):
    return next(line.strip() for line in text.splitlines() if decl in line)


def fn_block(text, name):
    start = text.index("async function " + name + "(")
    end = text.index("\n}\n", start) + len("\n}\n")
    return text[start:end]


def sample_path(source):
    """Fill every :param with a value matching its constraint."""
    return PARAM.sub(lambda m: sample_value(m), source)


def redirect_status(rule):
    return rule.get("statusCode") if "statusCode" in rule else (301 if rule.get("permanent") else 302)


def first_match(rules, path):
    for r in rules:
        if is_exact(r["source"]):
            if r["source"] == path:
                return r
            continue
        if re.fullmatch(translate_source(r["source"]), path):
            return r
    raise AssertionError(f"no rule matches {path}")


def matches_any(rules, path):
    try:
        first_match(rules, path)
        return True
    except AssertionError:
        return False


def translate_source(source):
    """Independent path-to-regexp subset matcher: :name, :name(regex), :name*,
    and bare (regex) groups stay regex — only literal chunks are escaped."""
    out = []
    pos = 0
    for m in SRC_TOKEN.finditer(source):
        out.append(re.escape(source[pos:m.start()]))
        if m.group(6) is not None:
            out.append("(" + m.group(6) + ")")
        elif (m.group(3) or m.group(5)) == "*":
            out.append(".*")
        else:
            out.append("(" + (m.group(2) or "[^/]+") + ")")
        pos = m.end()
    out.append(re.escape(source[pos:]))
    return "".join(out)


def expected_destination(rule):
    dest = rule["destination"]
    if is_exact(rule["source"]):
        return dest
    for m in PARAM.finditer(rule["source"]):
        dest = dest.replace(":" + (m.group(1) or m.group(4)), sample_value(m))
    return dest


def sample_value(m):
    custom = m.group(2)
    mod = m.group(3) or m.group(5)
    if mod == "*":
        return "a/b"
    return custom.split("|")[0] if custom else "seg"


def clean_path_and_file(file):
    if file.endswith("/index.html"):
        return "/" + file[: -len("/index.html")], file
    return "/" + file[: -len(".html")], file


if __name__ == "__main__":
    unittest.main()
