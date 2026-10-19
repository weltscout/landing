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

```sh
python3 deploy/build.py dist        # fails loudly on a missing tag, FAQ/JSON-LD mismatch, missing image
cd dist && vercel deploy --prod      # project: welt-scout-web-preview
```

Contact form environment variables (Vercel): `RESEND_API_KEY`, `CONTACT_FROM`, `CONTACT_TO`. Without them the endpoint answers `503 not_configured`.

## Adding a language

1. Copy `i18n/en.html` to `i18n/<code>.html` and translate the visible strings.
2. Add one entry to `langs` in `deploy/langs.json` (code, file, hreflang, locale, flag, name).
3. Optional: `legal/<code>/` with the three legal pages; until then the English text is used.

The language switcher, hreflang, sitemap and JSON-LD languages are generated, never edited by hand.

## Going to production

In `deploy/langs.json`: set `site` to `https://www.weltscout.com` and `indexable` to `true`, then rebuild. That removes `noindex`, adds the sitemap to robots.txt and rewrites every canonical, hreflang and og:url.

Analytics (GA4, PostHog) are described in the legal pages but not installed on this site yet: they need a consent banner first.

Translations (hr, sr, de, nl, fr) and the legal texts are machine translations awaiting review by native speakers and a lawyer.
