#!/usr/bin/env python3
"""
Mock of the Google Apps Script /exec endpoint, to test the ClinixOS order form's
success/failure logic WITHOUT sending a real lead and without touching the live
script.

Why this exists
---------------
The live endpoint cannot be exercised from this host: the browser has no external
egress (every fetch, even to example.com, fails), and curl only ever gets Google's
403 interstitial. So the response headers on the SUCCESS path are unverified.

The form's correctness depends entirely on those headers:
  - Apps Script sends Access-Control-Allow-Origin:* on a successful /exec response.
  - It sends NO access-control-* header on its 403/404 error pages.
  - When a cross-origin response lacks ACAO, the browser REJECTS the fetch,
    which is how the form learns "unconfirmed".

This mock reproduces both cases so the branch logic can be proven locally.

Routes (all POST):
  /ok        200 + ACAO:* + normal body            -> must show GREEN success
  /nocors    200, NO ACAO header                   -> browser rejects -> unconfirmed
  /fail500   500, NO ACAO header                   -> browser rejects -> unconfirmed
  /fail403   403, NO ACAO header                   -> browser rejects -> unconfirmed
  /authwall  200 + ACAO:* + Google sign-in body    -> must NOT show success
  /offsite   302 -> https://example.invalid/login  -> must NOT show success

Run:  python3 tools/mock_apps_script.py 8788
"""
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8788

AUTH_BODY = (
    b'<!doctype html><html><head><title>Sign in - Google Accounts</title></head>'
    b'<body><form action="https://accounts.google.com/ServiceAuth">'
    b'ServiceLogin</form></body></html>'
)
OK_BODY = b'{"result":"ok"}'


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *a):
        sys.stderr.write("MOCK %s\n" % (format % a))

    def _send(self, status, body, cors):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if cors:
            self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n:
            self.rfile.read(n)  # drain; never log lead data
        path = self.path.split("?")[0].rstrip("/") or "/ok"

        if path == "/ok":
            self._send(200, OK_BODY, cors=True)
        elif path == "/nocors":
            self._send(200, OK_BODY, cors=False)
        elif path == "/fail500":
            self._send(500, b"<html>Error</html>", cors=False)
        elif path == "/fail403":
            self._send(403, b"<html>Access Denied</html>", cors=False)
        elif path == "/authwall":
            self._send(200, AUTH_BODY, cors=True)
        elif path == "/offsite":
            self.send_response(302)
            self.send_header("Location", "https://example.invalid/login")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", "0")
            self.end_headers()
        else:
            self._send(404, b"<html>Not found</html>", cors=False)


if __name__ == "__main__":
    print(f"mock Apps Script on http://127.0.0.1:{PORT}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
