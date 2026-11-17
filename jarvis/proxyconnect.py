#!/usr/bin/env python3
"""ProxyCommand helper: open a TCP connection to host:port through the
HTTP proxy named by the https_proxy environment variable, using
CONNECT, then relay stdin/stdout. Used so ssh can reach an outside
host from this sandbox, where all egress goes through the proxy.
The proxy credential is read from the environment at runtime and is
never stored in this file.
"""
import base64
import os
import select
import socket
import sys
import urllib.parse


def main():
    host = sys.argv[1]
    port = int(sys.argv[2])
    proxy = urllib.parse.urlparse(os.environ.get("https_proxy", ""))
    sock = socket.create_connection((proxy.hostname, proxy.port or 3128),
                                    timeout=20)
    lines = ["CONNECT %s:%d HTTP/1.1" % (host, port),
             "Host: %s:%d" % (host, port)]
    if proxy.username:
        creds = "%s:%s" % (urllib.parse.unquote(proxy.username),
                           urllib.parse.unquote(proxy.password or ""))
        lines.append("Proxy-Authorization: Basic "
                     + base64.b64encode(creds.encode()).decode())
    sock.sendall(("\r\n".join(lines) + "\r\n\r\n").encode())
    buf = b""
    while b"\r\n\r\n" not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            sys.exit("proxy closed during CONNECT")
        buf += chunk
    status_line = buf.split(b"\r\n", 1)[0]
    if b" 200 " not in status_line:
        sys.exit("CONNECT failed: %s" % status_line.decode("utf-8",
                                                          "replace"))
    leftover = buf.split(b"\r\n\r\n", 1)[1]
    if leftover:
        os.write(1, leftover)
    sock.setblocking(False)
    stdin = sys.stdin.buffer
    while True:
        readable, _, _ = select.select([sock, stdin], [], [], 60)
        if not readable:
            break
        for src in readable:
            if src is sock:
                data = sock.recv(65536)
                if not data:
                    return
                os.write(1, data)
            else:
                data = os.read(0, 65536)
                if not data:
                    try:
                        sock.shutdown(socket.SHUT_WR)
                    except OSError:
                        pass
                    continue
                sock.sendall(data)


if __name__ == "__main__":
    main()
