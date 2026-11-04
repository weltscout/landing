"""Run the actual post-deploy verifier against a local, side-effect-free edge."""

import json
import os
import subprocess
import threading
import unittest
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://www.weltscout.com"
PREVIEW = "https://weltscout-landing.b-cdn.net"
HONEYPOT = {
    "name": "smoke", "email": "smoke@example.com", "msg": "deploy check",
    "consent": True, "website": "bot",
}


@contextmanager
def edge(**changes):
    config = {
        "site": SITE, "noindex": False, "meta_noindex": False, "status": 200,
        "canonical_site": None, "sitemap_site": None, "robots_site": None,
        "security": True, "redirect_status": 301, "redirect": "/sl/",
        "contact_status": 200, "contact_body": {"ok": True},
        "robots_blocked": False,
    }
    config.update(changes)
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_HEAD(self):
            self.respond()

        def do_GET(self):
            self.respond()

        def do_POST(self):
            self.respond()

        def respond(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            calls.append((self.command, self.path, body, self.headers.get("Content-Type")))
            status, headers, payload = 200, {}, ""
            if self.path == "/":
                status = config["status"]
                canonical = config["canonical_site"] or config["site"]
                payload = f'<link rel="canonical" href="{canonical}/sl/"><meta property="og:url" content="{canonical}/sl/">'
                if config["meta_noindex"]:
                    payload += '<meta name="robots" content="noindex, nofollow">'
                if config["noindex"]:
                    headers["X-Robots-Tag"] = "noindex, nofollow"
                if config["security"]:
                    headers["X-Content-Type-Options"] = "nosniff"
            elif self.path == "/robots.txt":
                payload = "User-agent: *\nAllow: /\nDisallow: /api/\n"
                if config["robots_blocked"]:
                    payload += "Disallow: /\n"
                if not config["noindex"]:
                    payload += f'Sitemap: {config["robots_site"] or config["site"]}/sitemap.xml\n'
            elif self.path == "/sitemap.xml":
                site = config["sitemap_site"] or config["site"]
                payload = f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{site}/sl/</loc></url></urlset>'
            elif self.path == "/post/":
                status = config["redirect_status"]
                headers["Location"] = config["redirect"]
            elif self.path == "/api/contact":
                status = config["contact_status"]
                payload = json.dumps(config["contact_body"], separators=(",", ":"))
            else:
                status = 404
            self.send_response(status)
            for key, value in headers.items():
                self.send_header(key, value)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(payload.encode())

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


class VerifyDeploy(unittest.TestCase):
    def verify(self, base, site=SITE, indexable="1"):
        return subprocess.run(
            ["bash", str(ROOT / "deploy/verify.sh")],
            env={**os.environ, "BASE_URL": base, "SITE_URL": site, "INDEXABLE": indexable},
            text=True, capture_output=True, timeout=15,
        )

    def test_production_fetches_each_boundary_once_and_only_submits_honeypot(self):
        with edge() as (base, calls):
            result = self.verify(base)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual([(method, path) for method, path, _, _ in calls], [
            ("GET", "/"), ("GET", "/robots.txt"), ("GET", "/sitemap.xml"),
            ("HEAD", "/post/"), ("POST", "/api/contact"),
        ])
        self.assertEqual(json.loads(calls[-1][2]), HONEYPOT)
        self.assertEqual(calls[-1][3], "application/json")

    def test_preview_remains_verifiable_before_the_production_build(self):
        with edge(site=PREVIEW, noindex=True, meta_noindex=True) as (base, _):
            result = self.verify(base, PREVIEW, "0")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_stale_or_broken_production_responses(self):
        cases = {
            "noindex header": {"noindex": True},
            "noindex meta": {"meta_noindex": True},
            "preview canonical": {"canonical_site": PREVIEW},
            "preview sitemap": {"sitemap_site": PREVIEW},
            "preview robots sitemap": {"robots_site": PREVIEW},
            "blocked robots": {"robots_blocked": True},
            "HTTP failure": {"status": 503},
            "missing security": {"security": False},
            "wrong redirect status": {"redirect_status": 302},
            "wrong redirect location": {"redirect": "/en/"},
            "contact failure": {"contact_status": 502},
            "contact malformed response": {"contact_body": {"message": 'not actually "ok":true'}},
        }
        for name, config in cases.items():
            with self.subTest(name=name), edge(**config) as (base, _):
                result = self.verify(base)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_preview_requires_both_header_and_meta_noindex(self):
        for missing in ("noindex", "meta_noindex"):
            with self.subTest(missing=missing):
                config = {"site": PREVIEW, "noindex": True, "meta_noindex": True, missing: False}
                with edge(**config) as (base, _):
                    result = self.verify(base, PREVIEW, "0")
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_invalid_mode_fails_before_any_request(self):
        with edge() as (base, calls):
            result = self.verify(base, indexable="typo")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, [])
