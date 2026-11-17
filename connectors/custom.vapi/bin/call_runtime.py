"""Autonomous outbound delivery with a private journal; no per-call approval prompt.

Only GET requests retry. An ambiguous POST is reconciled, never blindly redialed.
The journal contains HMAC target identifiers and provider IDs, not phone numbers
or transcripts. This is delivery control, not proof of consent or a booking tool.
"""
import copy
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

OUTREACH_ID = "c36426ed-b325-46c8-9287-2da3471fddd9"
OWN_NUMBERS = {"+19293072035", "+19293070119"}
ACTIVE = ("submitting", "uncertain", "queued", "ringing", "in-progress", "forwarding", "scheduled")


def diagnosis(call):
    reason = call.get("endedReason") or ""
    if not reason:
        return "Pending; a created call is not proof of connection."
    if "get-transport" in reason:
        return "Carrier refused the call. Check carrier account status, destination permissions and outbound voice profile."
    if "outbound-daily-limit" in reason:
        return "Outbound limit reached; check the number/provider plan. Do not keep redialing."
    if "credit" in reason or "balance" in reason:
        return "Provider balance or credit limit needs attention."
    if reason in ("customer-did-not-answer", "customer-busy"):
        return "Recipient unavailable. This is not a connected conversation."
    if "llm" in reason or "voice" in reason or "transcriber" in reason:
        return "Speech/model provider failed. Inspect provider credentials, quota and call logs."
    if reason in ("customer-ended-call", "assistant-ended-call"):
        return "Call ended. Consult the transcript/outcome before claiming a conversation, meeting or sale."
    return "Inspect provider status and endedReason; do not assume delivery or a booking."


def prospect_numbers():
    # Support both the checked-out repository and the existing Muse installation.
    root = Path(__file__).resolve().parents[3]
    paths = [root/"business"/"ops"/name for name in ("citywide-list.md", "premium-list.md", "call-kit.md")]
    hidden = Path.home()/"workspace/goals/ai-front-desk-business-for-salons-and-barbershops/hidden_files"
    paths += [hidden/name for name in ("citywide-list.md", "premium-list.md", "call-kit.md")]
    numbers = set()
    for path in paths:
        if path.is_file():
            numbers.update(re.findall(r"\+[1-9][0-9]{7,14}\b", path.read_text()))
    return numbers - OWN_NUMBERS


class Delivery:
    def __init__(self, api, directory=None, now=time.time, allowed_targets=None):
        self.api, self.now = api, now
        self.allowed_targets = allowed_targets
        self.directory = Path(directory or os.environ.get("BOOKED_SOLID_STATE_DIR", Path.home()/".local/state/booked-solid"))
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.directory, 0o700)
        self.path = self.directory/"calls.sqlite3"
        self.key_path = self.directory/"target.key"
        try:
            fd = os.open(self.key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            pass
        else:
            with os.fdopen(fd, "wb") as stream:
                stream.write(secrets.token_bytes(32))
        self.key = self.key_path.read_bytes()
        if len(self.key) != 32:
            raise RuntimeError("Private delivery key unavailable; retry initialization")
        os.chmod(self.key_path, 0o600)
        with self.db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS attempts(
                    id TEXT PRIMARY KEY,target TEXT,created REAL,state TEXT,call_id TEXT,reason TEXT);
                CREATE TABLE IF NOT EXISTS blocked(target TEXT PRIMARY KEY);
            """)
        os.chmod(self.path, 0o600)

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=20)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def target(self, number):
        return hmac.new(self.key, number.encode(), hashlib.sha256).hexdigest()

    def block(self, number):
        if not re.fullmatch(r"\+[1-9][0-9]{7,14}", number):
            raise ValueError("Use an E.164 number")
        with self.db() as db:
            db.execute("INSERT OR IGNORE INTO blocked VALUES(?)", (self.target(number),))

    def update(self, attempt, call):
        state = call.get("status") or "uncertain"
        if state not in ACTIVE and state != "ended":
            state = "uncertain"
        with self.db() as db:
            db.execute("UPDATE attempts SET state=?,call_id=?,reason=? WHERE id=?",
                       (state, call.get("id"), (call.get("endedReason") or "")[:200], attempt["id"]))
            # An opt-out in a finished call suppresses future attempts even if the
            # scheduled prose forgets its do-not-call list. No transcript is saved.
            if state == "ended" and re.search(r"\b(do not call|don't call|stop calling|remove me from)\b", call.get("transcript") or "", re.I):
                db.execute("INSERT OR IGNORE INTO blocked VALUES(?)", (attempt["target"],))

    def reconcile(self):
        with self.db() as db:
            rows = [dict(r) for r in db.execute("SELECT * FROM attempts WHERE state IN ("+",".join("?"*len(ACTIVE))+")", ACTIVE)]
        summaries = []
        for row in rows:
            if row["state"] == "submitting" and self.now()-row["created"] < 45:
                continue
            if row["call_id"]:
                status, data = self.api("GET", "/call/"+row["call_id"])
            else:
                status, data = self.api("GET", "/call?limit=100")
                calls = data if isinstance(data, list) else data.get("results", [])
                data = next((c for c in calls if c.get("name") == "BS-"+row["id"]), None)
            if 200 <= status < 300 and isinstance(data, dict) and data.get("id"):
                self.update(row, data)
                summaries.append({"attempt_id":row["id"], "call_id":data["id"], "state":data.get("status"),
                                  "endedReason":data.get("endedReason"), "diagnosis":diagnosis(data)})
            else:
                summaries.append({"attempt_id":row["id"], "state":"uncertain", "diagnosis":"No authoritative receipt yet; no automatic redial."})
        return summaries

    def dial(self, original):
        body = copy.deepcopy(original)
        number = (body.get("customer") or {}).get("number", "")
        if not re.fullmatch(r"\+[1-9][0-9]{7,14}", number):
            return 400, {"error":"invalid_destination", "detail":"Use E.164 with country code; no call placed."}
        try:
            duration = float((body.get("assistantOverrides") or {}).get("maxDurationSeconds",600))
            if not 10 <= duration <= 600:
                raise ValueError
        except (ValueError, TypeError):
            return 400, {"error":"invalid_duration", "detail":"Call duration must be between 10 and 600 seconds."}
        if body.get("assistantId") == OUTREACH_ID:
            allowed = self.allowed_targets if self.allowed_targets is not None else prospect_numbers()
            if number not in allowed or number in OWN_NUMBERS:
                return 403, {"error":"outside_outreach_scope", "detail":"Sales outreach is limited to the existing prospect lists; self/demo loops are excluded."}
        # Harmless preflight catches missing resources before any paid call.
        for resource, resource_id in (("assistant",body.get("assistantId")), ("phone-number",body.get("phoneNumberId"))):
            try:
                uuid.UUID(str(resource_id))
            except (ValueError, TypeError):
                return 400, {"error":"invalid_"+resource+"_id"}
            status, data = self.api("GET", "/"+resource+"/"+resource_id)
            if not 200 <= status < 300:
                return status, {"error":"preflight_failed", "resource":resource, "detail":"Check access/configuration; no call placed."}
            if resource == "phone-number" and (data.get("provider") == "vapi" or data.get("number") == number):
                return 409, {"error":"unsuitable_caller_number", "detail":"Use an imported outbound-capable number, and do not call its own line."}
        self.reconcile()
        target = self.target(number)
        attempt = uuid.uuid4().hex
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM blocked WHERE target=?", (target,)).fetchone():
                return 403, {"error":"do_not_call", "detail":"Destination is suppressed; no call placed."}
            existing = db.execute("SELECT * FROM attempts WHERE target=? ORDER BY created DESC LIMIT 1", (target,)).fetchone()
            if existing and (existing["state"] in ACTIVE or self.now()-existing["created"] < 60):
                return 409, {"error":"duplicate_or_pending", "attempt_id":existing["id"],"call_id":existing["call_id"],
                             "detail":"Check the existing call receipt rather than dialing twice."}
            active = db.execute("SELECT id,call_id FROM attempts WHERE state IN ("+",".join("?"*len(ACTIVE))+") LIMIT 1", ACTIVE).fetchone()
            if active:
                return 409, {"error":"another_call_pending","attempt_id":active["id"],"call_id":active["call_id"],"detail":"Wait for and reconcile the current call before the next destination."}
            db.execute("INSERT INTO attempts VALUES(?,?,?,?,?,?)", (attempt,target,self.now(),"submitting",None,None))
        body["name"] = "BS-"+attempt
        overrides = body.setdefault("assistantOverrides", {})
        overrides["maxDurationSeconds"] = duration
        try:
            status, data = self.api("POST", "/call", body)
        except Exception:
            status, data = 503, {"error":"uncertain_submission", "detail":"Delivery outcome unknown; reconcile before retrying."}
        row = {"id":attempt,"target":target}
        if 200 <= status < 300 and isinstance(data, dict) and data.get("id"):
            self.update(row, data)
            return status, {**data,"delivery_notice":"Created does not mean answered. Check status and endedReason.","attempt_id":attempt}
        # A definite validation/auth/rate response rejected the request. A 5xx,
        # timeout or malformed success could already have created a call.
        state = "rejected" if 400 <= status < 500 and status != 408 else "uncertain"
        with self.db() as db:
            db.execute("UPDATE attempts SET state=? WHERE id=?", (state,attempt))
        return status if status >= 300 else 502, {"error":state,"attempt_id":attempt,
                  "detail":"Check credentials, balance, number permissions and carrier profile." if state == "rejected" else "Outcome unknown; no automatic redial. Reconcile with provider call logs."}
