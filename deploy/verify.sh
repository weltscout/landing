#!/usr/bin/env bash
# Post-deploy smoke test against the live edge — fails loudly on any mismatch.
# The redirect and contact checks only pass if the generated middleware is
# serving; the security-header check alone would pass on the CDN edge rule.
set -euo pipefail
BASE="${BASE_URL:-https://weltscout-landing.b-cdn.net}"

code=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/")
[ "$code" = 200 ] || { echo "GET / -> $code (want 200)"; exit 1; }

hdrs=$(curl -sI "$BASE/")
grep -qi '^x-content-type-options: nosniff' <<<"$hdrs" || { echo "missing security headers on /"; exit 1; }

redir=$(curl -sI "$BASE/post/")
{ grep -q '^HTTP/[^ ]* 301' <<<"$redir" && grep -qi '^location: /sl/' <<<"$redir"; } || {
  echo "GET /post/ is not 301 -> /sl/:"
  echo "$redir"
  exit 1
}

# The honeypot proves the middleware serves /api/contact without ever sending
# mail — valid submissions would email info@weltscout.com on every deploy once
# RESEND_API_KEY lands, and "not_configured" would vanish when it does.
body=$(mktemp)
contact_code=$(curl -s -o "$body" -w '%{http_code}' -X POST "$BASE/api/contact" \
  -H 'content-type: application/json' \
  -d '{"name":"smoke","email":"smoke@example.com","msg":"deploy check","consent":true,"website":"bot"}')
contact=$(cat "$body")
{ [ "$contact_code" = 200 ] && grep -q '"ok":true' <<<"$contact"; } || {
  echo "/api/contact is not serving the middleware ($contact_code): $contact"
  exit 1
}

echo "verified: $BASE serves the site through the middleware"
