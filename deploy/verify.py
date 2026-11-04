"""Side-effect-free deploy checks; fetch origin and canonical site may differ."""

import json
import os
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class PageHead(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonicals = []
        self.og_urls = []
        self.robots = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and "canonical" in attrs.get("rel", "").lower().split():
            self.canonicals.append(attrs.get("href"))
        if tag == "meta" and attrs.get("property", "").lower() == "og:url":
            self.og_urls.append(attrs.get("content"))
        if tag == "meta" and attrs.get("name", "").lower() in ("robots", "googlebot"):
            self.robots.append(attrs.get("content", ""))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fetch(opener, base, path, method="GET", body=None):
    headers = {"Content-Type": "application/json"} if body is not None else {}
    request = urllib.request.Request(base + path, data=body, headers=headers, method=method)
    try:
        response = opener.open(request, timeout=10)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, response.headers, response.read().decode("utf-8")


def verify(base, site, indexable, default_language):
    opener = urllib.request.build_opener(NoRedirect())
    status, headers, html = fetch(opener, base, "/")
    require(status == 200, f"GET / returned {status}, expected 200")
    require(headers.get("X-Content-Type-Options") == "nosniff", "missing security header on /")
    page = PageHead()
    page.feed(html)
    canonical = f"{site}/{default_language}/"
    require(page.canonicals == [canonical], f"wrong canonical on /: {page.canonicals}")
    require(page.og_urls == [canonical], f"wrong og:url on /: {page.og_urls}")
    header_noindex = any(re.search(r"\b(noindex|none)\b", value, re.I) for value in headers.get_all("X-Robots-Tag", []))
    meta_noindex = any(re.search(r"\b(noindex|none)\b", value, re.I) for value in page.robots)
    if indexable:
        require(not header_noindex and not meta_noindex, "production page still has noindex")
    else:
        require(header_noindex and meta_noindex, "preview requires header and meta noindex")

    status, _, robots = fetch(opener, base, "/robots.txt")
    require(status == 200, f"GET /robots.txt returned {status}")
    if indexable:
        require(not re.search(r"^\s*Disallow:\s*/\s*$", robots, re.I | re.M), "robots.txt blocks production crawling")
        sitemaps = [line.split(":", 1)[1].strip() for line in robots.splitlines() if line.lower().startswith("sitemap:")]
        require(sitemaps == [site + "/sitemap.xml"], "robots.txt has the wrong production sitemap")

    status, _, sitemap = fetch(opener, base, "/sitemap.xml")
    require(status == 200, f"GET /sitemap.xml returned {status}")
    tree = ET.fromstring(sitemap)
    locations = [node.text for node in tree.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
    alternates = [node.get("href") for node in tree.iter() if node.get("href") is not None]
    require(bool(locations), "sitemap.xml has no URLs")
    require(all(url and url.startswith(site + "/") for url in locations + alternates), "sitemap.xml contains URLs outside the expected site")

    status, headers, _ = fetch(opener, base, "/post/", method="HEAD")
    require(status == 301 and headers.get("Location") == f"/{default_language}/", "legacy /post/ redirect is wrong")

    # A populated honeypot returns before Chatwoot delivery. Never send a real
    # contact message from CI, even when testing the production site.
    body = json.dumps({
        "name": "smoke", "email": "smoke@example.com", "msg": "deploy check",
        "consent": True, "website": "bot",
    }).encode()
    status, _, response = fetch(opener, base, "/api/contact", method="POST", body=body)
    require(status == 200 and json.loads(response) == {"ok": True}, "contact honeypot smoke check failed")


def main():
    config = json.loads((Path(__file__).parent / "langs.json").read_text())
    site = os.environ.get("SITE_URL", config["site"]).rstrip("/")
    base = os.environ.get("BASE_URL", site).rstrip("/")
    mode = os.environ.get("INDEXABLE", "1")
    require(mode in ("0", "1"), "INDEXABLE must be 0 (preview) or 1 (production)")
    verify(base, site, mode == "1", config["default"])
    print(f"verified: {base} serves {'production' if mode == '1' else 'preview'} content for {site}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, ET.ParseError, urllib.error.URLError, TimeoutError) as error:
        print(f"deploy verification failed: {error}", file=sys.stderr)
        sys.exit(1)
