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
  /ok        302 -> /echo?... 200 ACAO:*            -> the REAL Apps Script flow
  /ok-direct 200 + ACAO:* + normal body             -> must show GREEN success
  /nocors    200, NO ACAO header                   -> browser rejects -> unconfirmed
  /fail500   500, NO ACAO header                   -> browser rejects -> unconfirmed
  /fail403   403, NO ACAO header                   -> browser rejects -> unconfirmed
  /authwall  200 + ACAO:* + Google sign-in body    -> must NOT show success
  /offsite   302 -> https://example.invalid/login  -> must NOT show success

The /ok -> 302 -> /echo route is the important one
-----------------------------------------------
A POST to a Google Apps Script /exec URL does NOT return the script's output
directly. It returns **302 Moved Temporarily** with
`Access-Control-Allow-Origin: *` and a Location of

    https://script.googleusercontent.com/macros/echo?user_content_key=...&lib=...

i.e. a DIFFERENT HOST. The browser then follows it and GETs the echo URL,
which is where the real ContentService payload comes back (also with ACAO:*).

Confirmed against the live deployment with curl: an anonymous GET of the
production /exec answers 200 from script.google.com itself, so the redirect
chain is not observable from this host for a GET. The POST path is what
redirects, and it cannot be probed here without writing a real lead row — so
the flow is reproduced from the documented/observed Apps Script behaviour
(302 + ACAO + script.googleusercontent.com/macros/echo).

The consequence for the page is that after a genuinely successful write,
`res.url` is on script.googleusercontent.com, NOT on the endpoint host. A
guard that requires res.url's host to equal the endpoint's host therefore
rejects EVERY real success. That is the false negative this mock exists to
catch, and why /ok (the redirecting route) is the default success case.

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
# Apps Script 404s with this exact text when the function does not exist.
NO_FUNCTION_BODY = b"<html><body>Error: Script function not found: doPost</body></html>"

# Where the /ok 302 sends the browser. It MUST be a different host from the
# endpoint or the cross-host hop that causes the production bug is not
# reproduced. Port 0 asks the OS for a free one, so two mock servers can run
# side by side (endpoint + redirect target).
REDIRECT_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8789
ECHO_URL = ("https://script.googleusercontent.com:%d/echo"
            "?user_content_key=fakekey&lib=fakelib" % REDIRECT_PORT)


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

    def do_GET(self):
        # The redirect target. Apps Script serves the script's output here and
        # only ever accepts GET on it (a POST to the echo URL returns 405).
        if self.path.split("?")[0].rstrip("/") == "/echo":
            self._send(200, OK_BODY, cors=True)
        else:
            self._send(404, b"<html>Not found</html>", cors=False)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n:
            self.rfile.read(n)  # drain; never log lead data
        path = self.path.split("?")[0].rstrip("/") or "/ok"

        # The page posts to https://script.google.com/macros/s/<id>/<route>,
        # so the route is normally the LAST path segment. Exact matches on the
        # whole path (e.g. a bare /ok) are honoured first; otherwise the tail
        # segment is the route, as long as it is one we know.
        KNOWN = ("/ok", "/ok-direct", "/nocors", "/fail500", "/fail403",
                 "/fail404", "/echo-post", "/authwall", "/offsite")
        if path in KNOWN:
            route = path
        else:
            tail = "/" + path.rsplit("/", 1)[-1]
            if tail in KNOWN:
                route = tail
            elif path.endswith("/exec"):
                # A realistic /exec with no explicit route behaves like Apps
                # Script's own path: the default success flow.
                route = "/ok"
            else:
                route = path  # unknown -> 404 below

        if route == "/ok":
            # The real Apps Script flow: 302 + ACAO to a DIFFERENT host, which
            # the browser then follows with a GET.
            #
            # The Location is ABSOLUTE and points at the redirect host, because
            # that is what decides the bug: after a genuinely successful write
            # res.url is on script.googleusercontent.com, not on the endpoint
            # host. A relative Location would keep the hop on one host and hide
            # exactly the defect this route exists to catch.
            self.send_response(302)
            self.send_header("Location", ECHO_URL)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", "0")
            self.end_headers()
        elif route == "/ok-direct":
            self._send(200, OK_BODY, cors=True)
        elif route == "/nocors":
            self._send(200, OK_BODY, cors=False)
        elif route == "/fail500":
            self._send(500, b"<html>Error</html>", cors=False)
        elif route == "/fail403":
            self._send(403, b"<html>Access Denied</html>", cors=False)
        elif route == "/fail404":
            self._send(404, NO_FUNCTION_BODY, cors=False)
        elif route == "/echo-post":
            # Apps Script's echo endpoint accepts GET only.
            self._send(405, b"<html>Method Not Allowed</html>", cors=False)
        elif route == "/authwall":
            self._send(200, AUTH_BODY, cors=True)
        elif route == "/offsite":
            self.send_response(302)
            self.send_header("Location", "https://example.invalid/login")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", "0")
            self.end_headers()
        else:
            self._send(404, b"<html>Not found</html>", cors=False)


class RedirectHandler(Handler):
    """The script.googleusercontent.com side of the hop: GET /echo only."""

    def do_GET(self):
        if self.path.split("?")[0].rstrip("/") == "/echo":
            # Proof log: the browser really followed the 302 here. The branch
            # harness checks this file to guard against vacuous passes.
            try:
                with open("/tmp/mock-echo-hits.log", "a") as f:
                    f.write("echo-hit\n")
            except OSError:
                pass
            self._send(200, OK_BODY, cors=True)
        else:
            self._send(404, b"<html>Not found</html>", cors=False)

    def do_POST(self):
        # Apps Script's echo endpoint accepts GET only.
        self._send(405, b"<html>Method Not Allowed</html>", cors=False)


def _self_signed_cert(certdir):
    """A throwaway cert for the fake googleusercontent host.

    Chrome must be run with --ignore-certificate-errors for this. Using TLS is
    the point: Apps Script redirects to an https:// URL, and an http:// stand-in
    would not exercise the same code path.
    """
    import os
    import subprocess
    cert = os.path.join(certdir, "mock-googleusercontent.pem")
    if os.path.exists(cert):
        return cert
    key = cert + ".key"
    cnf = os.path.join(certdir, "openssl.cnf")
    with open(cnf, "w") as f:
        f.write(
            "[req]\ndistinguished_name=dn\nx509_extensions=v3\n[dn]\n"
            "CN=script.googleusercontent.com\n[v3]\n"
            "subjectAltName=DNS:script.googleusercontent.com,DNS:script.google.com\n"
        )
    subprocess.run(
        ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
         "-keyout", key, "-out", cert, "-days", "2", "-config", cnf,
         "-subj", "/CN=script.googleusercontent.com"],
        check=True, capture_output=True,
    )
    return cert


if __name__ == "__main__":
    import os
    import ssl
    import tempfile
    from http.server import ThreadingHTTPServer

    tmp = tempfile.mkdtemp(prefix="mock-apps-script-")
    cert = _self_signed_cert(tmp)

    # Both sides speak TLS. Production is https on BOTH legs: the page posts to
    # https://script.google.com/.../exec and is redirected to
    # https://script.googleusercontent.com/macros/echo. An http:// stand-in for
    # either leg would not reproduce the real code path.
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(cert, cert + ".key")

    endpoint = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    endpoint.socket = ctx.wrap_socket(endpoint.socket, server_side=True)
    redirect = ThreadingHTTPServer(("127.0.0.1", REDIRECT_PORT), RedirectHandler)
    redirect.socket = ctx.wrap_socket(redirect.socket, server_side=True)

    import threading
    threading.Thread(target=redirect.serve_forever, daemon=True).start()
    print(f"mock Apps Script endpoint  https://script.google.com:{PORT}", flush=True)
    print(f"mock redirect target      {ECHO_URL}  (TLS, self-signed)", flush=True)
    print("  NOTE: the browser needs --ignore-certificate-errors.", flush=True)
    try:
        endpoint.serve_forever()
    except KeyboardInterrupt:
        pass

