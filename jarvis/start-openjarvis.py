#!/usr/bin/env python3
"""Launch OpenJarvis (jarvis serve) with the DeepSeek credential surrogate.

The real DeepSeek key never touches this process. We fetch the hsurr:
surrogate for the custom.deepseek connection from authd and place it in
DEEPSEEK_API_KEY, where OpenJarvis's cloud engine reads it. Authd swaps
the surrogate for the real key on the outbound request to
api.deepseek.com. The surrogate is never written to disk or logged.

Also sanitizes NO_PROXY: the sandbox default contains bracketed IPv6
entries that make httpx throw "Invalid port: ':1]'", which silently
disables every HTTP engine in OpenJarvis.
"""
import os
import sys

sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
from dynamic_credentials import dynamic_credential_entry

entry = dynamic_credential_entry("custom.deepseek")
os.environ["DEEPSEEK_API_KEY"] = str(entry["surrogate"]).strip()
os.environ["NO_PROXY"] = "localhost,127.0.0.1"
os.environ["no_proxy"] = "localhost,127.0.0.1"

home = os.path.expanduser("~")
os.chdir(os.path.join(home, "workspace", "openjarvis"))
jarvis_bin = os.path.join(home, "workspace", "openjarvis", ".venv", "bin", "jarvis")
os.execv(jarvis_bin, ["jarvis", "serve", "--port", "8000"])
