#!/usr/bin/env bash
set -euo pipefail
F="${HOME}/.hermes/secrets/spaceship-clinixospro.txt"
KEY=$(grep "^Key:" "$F" | awk '{print $2}')
SEC=$(grep "^Secret:" "$F" | awk '{print $2}')
DOMAIN="clinixospro.com"
NS1="nina.ns.cloudflare.com"
NS2="ram.ns.cloudflare.com"
if [[ -z "${SEC}" ]]; then
  echo "ERROR: fill Secret: line in $F (Spaceship API Manager -> reveal secret)"
  exit 1
fi
echo "Current domain state:"
curl -s "https://spaceship.dev/api/v1/domains/${DOMAIN}" \
  -H "X-API-Key: $KEY" -H "X-API-Secret: $SEC" -H "Content-Type: application/json" \
  | python3 -m json.tool | head -40

echo "Setting nameservers to $NS1 / $NS2 ..."
code=$(curl -s -o /tmp/sp-ns.json -w "%{http_code}" -X PUT \
  "https://spaceship.dev/api/v1/domains/${DOMAIN}/nameservers" \
  -H "X-API-Key: $KEY" -H "X-API-Secret: $SEC" -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0" \
  -d "{\"provider\":\"custom\",\"hosts\":[\"$NS1\",\"$NS2\"]}")
echo "HTTP $code"
cat /tmp/sp-ns.json; echo

echo "Verify after PUT:"
curl -s "https://spaceship.dev/api/v1/domains/${DOMAIN}" \
  -H "X-API-Key: $KEY" -H "X-API-Secret: $SEC" -H "Content-Type: application/json" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('nameservers'))"

ZT=$(head -1 "$HOME/.hermes/secrets/cloudflare-zone-token.txt" | tr -d '\r\n' | sed 's/^CLOUDFLARE_ZONE_TOKEN=//')
ZID=8657a8e9cd1d3eced9196e02dfaa4a34
curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/${ZID}/activation_check" -H "Authorization: Bearer $ZT" --max-time 15
echo
echo "Poll zone until active, then Pages domains should verify."
