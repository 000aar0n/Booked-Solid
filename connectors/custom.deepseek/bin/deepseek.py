#!/usr/bin/env python3
"""DeepSeek API helper for the custom.deepseek connector.

Usage:
  deepseek.py models                      list available models (auth check)
  deepseek.py balance                     show account balance
  deepseek.py chat <model> <prompt>       one-shot chat completion

The API key is never read from disk or the environment here. The
request carries a surrogate credential that the runtime swaps for
the real key on the way to api.deepseek.com.
"""
import json
import sys
import urllib.request

sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
from dynamic_credentials import add_surrogate_to_request, read_json_response

BASE = "https://api.deepseek.com"
HOSTS = ["api.deepseek.com"]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        raise RuntimeError("redirect refused, verify the endpoint")


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(BASE + path, data=data, method=method)
    if data is not None:
        request.add_header("Content-Type", "application/json")
    add_surrogate_to_request(request, "custom.deepseek", allowed_hosts=HOSTS)
    opener = urllib.request.build_opener(NoRedirect())
    try:
        with opener.open(request, timeout=60) as response:
            return response.status, read_json_response(response)
    except urllib.error.HTTPError as err:
        try:
            detail = err.read().decode("utf-8", "replace")[:500]
        except Exception:
            detail = ""
        return err.code, {"error": detail}


def main():
    if len(sys.argv) < 2:
        print("usage: deepseek.py models|balance|chat <model> <prompt>")
        return 2
    cmd = sys.argv[1]
    if cmd == "models":
        status, payload = call("GET", "/models")
    elif cmd == "balance":
        status, payload = call("GET", "/user/balance")
    elif cmd == "chat":
        model = sys.argv[2] if len(sys.argv) > 2 else "deepseek-chat"
        prompt = sys.argv[3] if len(sys.argv) > 3 else "Say hello in one short sentence."
        status, payload = call("POST", "/chat/completions", {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        })
    else:
        print("unknown command:", cmd)
        return 2
    print(json.dumps({"status": status, "payload": payload}, indent=1)[:3000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
