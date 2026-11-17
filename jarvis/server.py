#!/usr/bin/env python3
"""Jarvis live-data bridge for the Vapi phone assistant.

Exposes one function endpoint, POST /lookup, that Vapi calls when the
phone assistant needs current facts. It answers from free keyless
sources: Open-Meteo (weather), Stooq (stock quotes), Google News RSS
(headlines), DuckDuckGo Instant Answers and Wikipedia (general facts).

Vapi function-call envelope in, {"result": "..."} out. Plain
{"query": "..."} is also accepted for local testing.
"""
import json
import hmac
import os
import re
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UA = {"User-Agent": "Mozilla/5.0 (JarvisBrain/1.0)"}
TIMEOUT = 3
# Hard ceiling for one lookup. A phone call cannot sit in silence
# while slow fallbacks chain; past the deadline the bridge answers
# "empty" and the assistant replies from general knowledge.
DEADLINE = 6.0
POOL = ThreadPoolExecutor(max_workers=4, thread_name_prefix="lookup")
SLOTS = threading.BoundedSemaphore(4)
MAX_BODY = 16384


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", "replace")


def fetch_json(url):
    return json.loads(fetch(url))


TICKERS = {
    "apple": "AAPL", "nvidia": "NVDA", "amd": "AMD",
    "tesla": "TSLA", "microsoft": "MSFT", "amazon": "AMZN",
    "google": "GOOGL", "alphabet": "GOOGL", "meta": "META",
    "netflix": "NFLX", "coinbase": "COIN", "palantir": "PLTR",
    "bitcoin": "BTC-USD", "ethereum": "ETH-USD",
}


def stock_lookup(query):
    q = query.lower()
    symbol = None
    for name, sym in TICKERS.items():
        if name in q:
            symbol = sym
            break
    if not symbol:
        m = re.search(r"\b([A-Z]{1,5})\b", query)
        if m:
            symbol = m.group(1)
    if not symbol:
        return None
    try:
        data = fetch_json("https://query1.finance.yahoo.com/v8/finance"
                          "/chart/%s" % urllib.parse.quote(symbol))
        meta = data["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice")
        prev = meta.get("chartPreviousClose")
        if price is None:
            return None
        text = "%s last traded at $%s" % (meta.get("symbol", symbol),
                                          price)
        if prev:
            change = (price - prev) / prev * 100
            text += ", %s %.2f percent on the day" % (
                "up" if change >= 0 else "down", abs(change))
        return text + ". Quote may be delayed by several minutes."
    except Exception:
        return None


def weather_lookup(query):
    m = re.search(r"(?:in|for|at)\s+([A-Za-z ]+)$", query.strip(), re.I)
    place = m.group(1).strip() if m else "New York"
    place = re.sub(r"\s+(right now|today|tonight|tomorrow|now|please)$",
                   "", place, flags=re.I).strip() or "New York"
    try:
        geo = fetch_json("https://geocoding-api.open-meteo.com/v1/search"
                         "?name=%s&count=1&language=en&format=json"
                         % urllib.parse.quote(place))
        if not geo.get("results"):
            return None
        r = geo["results"][0]
        fc = fetch_json(
            "https://api.open-meteo.com/v1/forecast?latitude=%s"
            "&longitude=%s&current=temperature_2m,weather_code,"
            "wind_speed_10m&daily=temperature_2m_max,temperature_2m_min"
            "&temperature_unit=fahrenheit&timezone=auto"
            % (r["latitude"], r["longitude"]))
        cur = fc["current"]
        daily = fc["daily"]
        return ("In %s it is currently %s degrees Fahrenheit with "
                "wind at %s km/h. Today's high %s, low %s."
                % (r["name"], cur["temperature_2m"],
                   cur["wind_speed_10m"], daily["temperature_2m_max"][0],
                   daily["temperature_2m_min"][0]))
    except Exception:
        return None


def news_lookup(query):
    topic = re.sub(r"\b(latest|news|headlines?|about|on|the)\b", " ",
                   query, flags=re.I)
    topic = re.sub(r"\s+", " ", topic).strip() or query
    try:
        rss = fetch("https://news.google.com/rss/search?q=%s"
                    "&hl=en-US&gl=US&ceid=US:en"
                    % urllib.parse.quote(topic))
        root = ET.fromstring(rss)
        items = root.findall(".//item")[:5]
        if not items:
            return None
        lines = []
        for it in items:
            title = it.findtext("title") or ""
            lines.append(title)
        return "Top headlines: " + " | ".join(lines)
    except Exception:
        return None


def fact_lookup(query):
    try:
        data = fetch_json("https://api.duckduckgo.com/?q=%s&format=json"
                          "&no_html=1&skip_disambig=1"
                          % urllib.parse.quote(query))
        if data.get("AbstractText"):
            return data["AbstractText"][:600]
        for topic in data.get("RelatedTopics", []):
            if topic.get("Text"):
                return topic["Text"][:600]
    except Exception:
        pass
    try:
        data = fetch_json(
            "https://en.wikipedia.org/w/api.php?action=query"
            "&prop=extracts&exintro&explaintext&format=json&titles=%s"
            % urllib.parse.quote(query))
        pages = data["query"]["pages"]
        for page in pages.values():
            if page.get("extract"):
                return page["extract"][:600]
    except Exception:
        pass
    return None


def lookup_sources(query):
    import time
    t0 = time.time()

    def fresh():
        return time.time() - t0 < DEADLINE

    q = query.strip()
    low = q.lower()
    if "weather" in low or "temperature" in low:
        result = weather_lookup(q)
        if result:
            return result
    if "stock" in low or "share price" in low or "price of" in low:
        result = stock_lookup(q)
        if result:
            return result
    if "news" in low or "headline" in low or "happened" in low:
        result = news_lookup(q)
        if result:
            return result
    if fresh():
        result = fact_lookup(q)
        if result:
            return result
    if fresh():
        result = news_lookup(q)
        if result:
            return result
    return ("No live result found for that. Answer from general "
            "knowledge and say the live lookup came back empty.")


def lookup(query, timeout=None):
    if not SLOTS.acquire(blocking=False):
        return "Live lookup is busy. Say you could not verify the current fact; do not guess."
    def work():
        try:
            return lookup_sources(query)
        finally:
            SLOTS.release()
    future = POOL.submit(work)
    try:
        return future.result(timeout=DEADLINE if timeout is None else max(.001,min(DEADLINE,timeout)))
    except FutureTimeout:
        return "Live lookup timed out. Say you could not verify the current fact; do not guess."
    except Exception:
        return "Live lookup failed. Say you could not verify the current fact; do not guess."


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def reply(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == "/health":
            self.reply(200,{"ok":True,"service":"booked-solid-lookup","version":2})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path != "/lookup":
            self.reply(404,{"error":"not_found"}); return
        token = os.environ.get("JARVIS_LOOKUP_TOKEN")
        if token and not hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer "+token):
            self.reply(401,{"error":"unauthorized"}); return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if not 0 < length <= MAX_BODY:
                self.reply(413,{"error":"body_limit"}); return
            raw = self.rfile.read(length)
            data = json.loads(raw)
            if not isinstance(data,dict):
                raise ValueError
        except (ValueError, socket.timeout):
            self.reply(400,{"error":"invalid_body"}); return
        msg = data.get("message") or {}
        if not isinstance(msg,dict):
            self.reply(400,{"error":"invalid_message"}); return
        # Current Vapi tool protocol: a "tool-calls" envelope with a
        # toolCallList; the answer must come back as a results array
        # keyed by toolCallId, or Vapi reports "No result returned".
        if msg.get("type") == "tool-calls" or msg.get("toolCallList"):
            calls = msg.get("toolCallList") or []
            if not isinstance(calls,list) or len(calls)>3 or any(not isinstance(c,dict) for c in calls):
                self.reply(400,{"error":"invalid_tool_calls"}); return
            results = []
            deadline = time.monotonic() + DEADLINE
            for call in calls:
                function = call.get("function") or {}
                args = function.get("arguments") if isinstance(function,dict) else {}
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except ValueError:
                        args = {}
                if not isinstance(args,dict):
                    args = {}
                q = args.get("query") or ""
                try:
                    remaining = deadline - time.monotonic()
                    r = lookup(str(q)[:1000], remaining) if remaining > 0 else "Lookup deadline reached; current fact could not be verified."
                except Exception:
                    r = "The live lookup failed; the current fact could not be verified."
                results.append({"toolCallId": call.get("id"),
                                "result": r})
            body = json.dumps({"results": results}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        query = None
        if msg.get("type") == "function-call":
            function = msg.get("functionCall") or {}
            params = function.get("parameters") if isinstance(function,dict) else {}
            if not isinstance(params,dict):
                params = {}
            query = params.get("query")
        if not query:
            query = data.get("query") or ""
        try:
            result = lookup(str(query)[:1000])
        except Exception:
            result = "The live lookup failed; the current fact could not be verified."
        body = json.dumps({"result": result}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8791), Handler).serve_forever()

