#!/usr/bin/env python3
"""Dumb pass-through proxy: Vapi -> this proxy -> DeepSeek API.

Exists so the Jarvis phone assistant can run on DeepSeek without
the real API key ever leaving the Secure Vault. The proxy attaches
the vault surrogate to each outgoing request exactly the way the
custom.deepseek connector helper does; the runtime swaps it for
the real key on the way to api.deepseek.com. The proxy holds no
credential itself and translates nothing: DeepSeek speaks native
OpenAI format, including tool calls and streaming, so bytes pass
through untouched in both directions.

Binds 127.0.0.1:8793. Exposed to Vapi through a localhost.run
tunnel maintained by stack_watchdog.py.
"""
import json
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
from dynamic_credentials import add_surrogate_to_request

TARGET = "https://api.deepseek.com/chat/completions"
HOSTS = ["api.deepseek.com"]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        raise RuntimeError("redirect refused")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(),
                                        fmt % args))

    def do_GET(self):
        if self.path in ("/", "/health"):
            body = b'{"ok": true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)

    def do_POST(self):
        if not self.path.rstrip("/").endswith("chat/completions"):
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b"{}"
        # Voice cannot wait for a reasoning pass: deepseek-flash
        # otherwise streams a long reasoning_content preamble before
        # the first spoken word, which reads as dead air on a call.
        # Disabling thinking makes answers start immediately.
        try:
            parsed = json.loads(body)
            parsed["thinking"] = {"type": "disabled"}
            body = json.dumps(parsed).encode()
        except Exception:
            pass
        req = urllib.request.Request(TARGET, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        try:
            add_surrogate_to_request(req, "custom.deepseek",
                                     allowed_hosts=HOSTS)
        except Exception as e:
            self.send_error(500, "credential attach failed: %s" % e)
            return
        opener = urllib.request.build_opener(NoRedirect())
        try:
            resp = opener.open(req, timeout=120)
        except urllib.error.HTTPError as e:
            payload = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type",
                             e.headers.get("Content-Type",
                                           "application/json"))
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        except Exception as e:
            self.send_error(502, "upstream failed: %s" % e)
            return
        self.send_response(resp.status)
        self.send_header("Content-Type",
                         resp.headers.get("Content-Type",
                                          "text/event-stream"))
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        try:
            # Forward line by line: SSE events are line delimited,
            # and a block read would buffer many small token deltas
            # into one late lump, which makes Vapi give up on the
            # stream mid-sentence.
            while True:
                line = resp.readline()
                if not line:
                    break
                self.wfile.write(b"%x\r\n%s\r\n" % (len(line), line))
                self.wfile.flush()
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8793), Handler)
    print("deepseek proxy listening on 127.0.0.1:8793", flush=True)
    server.serve_forever()
