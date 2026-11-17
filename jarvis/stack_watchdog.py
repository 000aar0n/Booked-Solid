#!/usr/bin/env python3
"""Self-healing watchdog for the Jarvis live_lookup bridge.

Current architecture (Tue 2026-11-17, Aaron's final call at
08:59): the Jarvis phone brain is Vapi-hosted OpenAI gpt-4.1.
Nothing about the assistant's model lives on this machine, and
this watchdog must NEVER touch the assistant or its model. The
DeepSeek pass-through proxy stack is retired from the phone path.

The only local piece left is the lookup bridge behind the
live_lookup tool:

1. Lookup bridge on 127.0.0.1:8791 (restarts it if down).
2. Its localhost.run tunnel. If it answers "no tunnel" or fails,
   the tunnel is rebuilt, the live_lookup tool URL in Vapi is
   repointed, and the new URL is saved to tunnel-urls.json.

Prints exactly one line: HEALTHY, REPAIRED <what>, or FAILED <what>.
Never prints secrets. Safe to run any time; a no-op when healthy.
"""
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request

BASE = os.path.expanduser("~/workspace/jarvis-brain")
VAPI = os.path.expanduser(
    "~/workspace/custom-connectors/custom.vapi/bin/vapi.py")
URLS_FILE = os.path.join(BASE, "tunnel-urls.json")
TOOL_ID = "0003283a-a671-4fe2-8c50-a13aae43da2c"
repairs = []


def fetch(url, timeout=10, data=None):
    try:
        req = urllib.request.Request(url, data=data)
        if data:
            req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        # Any HTTP status (even 404) means the server is alive.
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return None, str(e)


def local_ok(port, path="/"):
    status, _ = fetch("http://127.0.0.1:%d%s" % (port, path), timeout=5)
    return status is not None


def launch_detached(argv, logname, cwd=None):
    log = open(os.path.join(BASE, logname), "ab")
    subprocess.Popen(argv, stdout=log, stderr=log, cwd=cwd,
                     start_new_session=True, stdin=subprocess.DEVNULL)


def ensure_bridge():
    if not local_ok(8791, "/"):
        launch_detached(["python3", os.path.join(BASE, "server.py")],
                        "server.log", cwd=BASE)
        time.sleep(3)
        repairs.append("lookup bridge restarted")


def tunnel_alive(base_url):
    if not base_url:
        return False
    status, body = fetch(base_url + "/lookup", timeout=45,
                         data=b'{"query": "weather in New York"}')
    return status == 200 and "no tunnel" not in body


def start_tunnel(port, logname):
    argv = ["ssh", "-o",
            "ProxyCommand=python3 %s %%h %%p"
            % os.path.join(BASE, "proxyconnect.py"),
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", "ServerAliveInterval=30",
            "-R", "80:localhost:%d" % port, "nokey@localhost.run"]
    logpath = os.path.join(BASE, logname)
    # Truncate first: stale URLs from earlier tunnels must never be
    # mistaken for the fresh one.
    try:
        open(logpath, "w").close()
    except OSError:
        pass
    launch_detached(argv, logname)
    for _ in range(12):
        time.sleep(2)
        try:
            with open(logpath) as f:
                found = re.findall(
                    r"https://[a-z0-9]+\.app\.lhr\.life", f.read())
        except OSError:
            found = []
        if found:
            return found[-1]
    return None


def rebuild_tunnel():
    pat = "nokey@" + "localhost" + ".run"
    subprocess.run(["pkill", "-f", pat], capture_output=True)
    time.sleep(2)
    bridge = start_tunnel(8791, "tunnel-8791.log")
    if not bridge:
        return None
    urls = {}
    try:
        with open(URLS_FILE) as f:
            urls = json.load(f)
    except Exception:
        urls = {}
    urls["bridge"] = bridge
    urls.pop("brain", None)
    with open(URLS_FILE, "w") as f:
        json.dump(urls, f)
    subprocess.run(["python3", VAPI, "update-tool-url", TOOL_ID,
                    bridge + "/lookup"], capture_output=True,
                   timeout=60)
    repairs.append("bridge tunnel rebuilt and tool rewired")
    return bridge


def main():
    ensure_bridge()
    urls = {}
    try:
        with open(URLS_FILE) as f:
            urls = json.load(f)
    except Exception:
        urls = {}
    if not tunnel_alive(urls.get("bridge")):
        bridge = rebuild_tunnel()
        if bridge is None:
            print("FAILED bridge tunnel could not be rebuilt")
            return
        if not tunnel_alive(bridge):
            print("FAILED bridge tunnel rebuilt but not answering")
            return
    if repairs:
        print("REPAIRED " + "; ".join(repairs))
    else:
        print("HEALTHY")


if __name__ == "__main__":
    main()
