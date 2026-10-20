# WeltScout landing

Marketing site for [WeltScout](https://www.weltscout.com): used-vehicle search for dealers and brokers.
Static HTML, no framework. Preview: https://welt-scout-web-preview.vercel.app/

## Structure

| Path | What |
|---|---|
| `index.html` | Slovenian page, the source every translation follows |
| `i18n/<code>.html` | Translations (hr, sr, en, de, nl, fr), same markup |
| `legal/<code>/<slug>.html` | Legal page bodies (privacy policy, terms and conditions, cookie policy); a missing language falls back to `en` |
| `deploy/langs.json` | Single source for languages, site URL, indexing switch, company data, icons |
| `deploy/build.py` | Builds `/<code>/` per language: language switcher, hreflang, canonical, Open Graph, JSON-LD, robots.txt, sitemap.xml, llms.txt, legal pages, root page |
| `deploy/og.js` | Renders `img/og/<code>.jpg` (1200x630) from each page's og:title (Playwright) |
| `deploy/api/contact.js` | Contact form endpoint (Vercel function, sends via Resend) |
| `tokens.css` | Colour tokens |

## Build and deploy

Production (https://www.weltscout.com, indexable; these are the defaults in `deploy/langs.json`):

```sh
python3 deploy/build.py dist        # fails loudly on a missing tag, FAQ/JSON-LD mismatch, missing image
cd dist && vercel deploy --prod      # or upload dist/ to any static host that runs the api/ function
```

`dist/` is the whole site: `/` serves the default language, `/<code>/` each language, `/<code>/<legal-slug>/` the legal pages, plus `robots.txt`, `sitemap.xml`, `llms.txt` and `vercel.json` (headers, clean URLs).

Preview on another domain, kept out of search engines:

```sh
WS_SITE=https://welt-scout-web-preview.vercel.app WS_INDEXABLE=0 python3 deploy/build.py dist
```

`WS_SITE` and `WS_INDEXABLE` override `site` and `indexable` from `langs.json` without editing it.

Contact form environment variables (Vercel): `RESEND_API_KEY`, `CONTACT_FROM`, `CONTACT_TO`. Without them the endpoint answers `503 not_configured`.

## AWS

```sh
python3 deploy/build.py dist && python3 deploy/aws.py dist
```

`deploy/aws.py` translates `dist/vercel.json` into `dist/aws/`: a CloudFront Function for the redirects (301) and clean URLs, a CloudFront response headers policy, `s3-sync.sh` (Content-Type and Cache-Control per file), the AWS Amplify alternative (`amplify-redirects.json`, `customHttp.yml`), and `contact-lambda/` (a Lambda adapter around `deploy/api/contact.js`, same env vars, so `/api/contact` keeps working through a CloudFront behavior). Step-by-step deploy and curl checks: `dist/aws/README.md` (template in `deploy/aws-templates/`). It fails loudly on any `vercel.json` construct it cannot translate and when the function would exceed the CloudFront Functions size limit. Test: `python3 -m unittest deploy/test_aws.py -v` (needs node 20+).

## Bunny

```sh
python3 deploy/build.py dist && python3 deploy/edge_script.py dist
```

`deploy/edge_script.py` translates `dist/vercel.json` into `dist/edge_script.js` — the Bunny middleware (before-cache edge script): redirects (301/302) and clean URLs, response headers, and `/api/contact` (port of `deploy/api/contact.js`, same env vars; `503 not_configured` without them). The routing logic lives in `deploy/edge_core.js` and is shared verbatim into the generated script. It fails loudly on any `vercel.json` construct it cannot translate and never writes a partial translation. Test: `python3 -m unittest deploy/test_edge_script.py -v` (needs node 20+).

## Blog

`blog/<code>/<slug>.html` are the posts (18 topics in sl, hr, en, de). Each file starts with a JSON front matter comment; the format and the checks are in `deploy/blog.py`. The build makes `/<code>/blog/` and `/<code>/blog/<slug>/`, hreflang between translations (same `hreflang_group`), BlogPosting/Breadcrumb JSON-LD, sitemap entries with `lastmod`, a Blog link in the nav, and a 301 from every old Webflow post URL listed in the post's `legacy` field. It fails on a missing field, a second `<h1>`, a portal name, "24/7"/"real-time"/"instant", or a missing image. Which statuses are indexed: `blogIndexStatuses` in `langs.json`.

## Adding a language

1. Copy `i18n/en.html` to `i18n/<code>.html` and translate the visible strings.
2. Add one entry to `langs` in `deploy/langs.json` (code, file, hreflang, locale, flag, name).
3. Optional: `legal/<code>/` with the three legal pages; until then the English text is used.

The language switcher, hreflang, sitemap and JSON-LD languages are generated, never edited by hand.

## Production notes

`langs.json` already points at `https://www.weltscout.com` with `indexable: true`: no `noindex`, sitemap listed in robots.txt, every canonical, hreflang and og:url on www.weltscout.com. All 92 URLs of the old Webflow sitemap resolve: legal pages redirect to the new legal pages, `/blog` and `/<lang>/post/*` redirect (301) to the language home page until the articles are moved (rules in `legacyRedirects` in `langs.json`).

Analytics: GA4 (`analytics.ga4` in `langs.json`) loads only after the visitor clicks Accept in the consent banner; Decline sets nothing and removes `_ga` cookies; the footer link reopens the banner. `WS_GA=off` builds without analytics.

Translations (hr, sr, de, nl, fr) and the legal texts are machine translations awaiting review by native speakers and a lawyer.
