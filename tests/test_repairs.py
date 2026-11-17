import concurrent.futures
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"connectors/custom.vapi/bin"))
import call_runtime
import checkout
import vapi

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result

server=module("lookup_test","jarvis/server.py")
watchdog=module("watchdog_test","jarvis/stack_watchdog.py")
ASSISTANT=call_runtime.OUTREACH_ID
NUMBER="45d8d383-906e-4b88-ad9c-5da9ef6ce10a"
TARGET="+12125550101"

class FakeAPI:
    def __init__(self):
        self.requests=[];self.calls={};self.post_error=None
    def __call__(self,method,path,body=None):
        self.requests.append((method,path,body))
        if method=="GET" and path.startswith("/assistant/"):
            return 200,{"id":ASSISTANT,"model":{"provider":"openai","model":"gpt-4.1","messages":[{"role":"system","content":"Existing instructions."}]},"maxDurationSeconds":600}
        if method=="GET" and path.startswith("/phone-number/"):
            return 200,{"provider":"telnyx","number":"+19293070119"}
        if method=="GET" and path.startswith("/call?"):
            return 200,list(self.calls.values())
        if method=="GET" and path.startswith("/call/"):
            return (200,self.calls[path.split("/")[-1]]) if path.split("/")[-1] in self.calls else (404,{})
        if method=="POST":
            call={"id":str(len(self.calls)+1),"name":body["name"],"status":"queued"}
            self.calls[call["id"]]=call
            return self.post_error or (201,call)
        return 200,body

class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.api=FakeAPI();self.clock=[1000]
        self.delivery=call_runtime.Delivery(self.api,self.temp.name,now=lambda:self.clock[0],allowed_targets={TARGET,"+12125550102"})
        self.body={"assistantId":ASSISTANT,"phoneNumberId":NUMBER,"customer":{"number":TARGET}}
    def tearDown(self): self.temp.cleanup()
    def posts(self):return [x for x in self.api.requests if x[0]=="POST"]
    def test_automatic_delivery_has_no_per_call_approval(self):
        status,result=self.delivery.dial(self.body)
        self.assertEqual(status,201);self.assertEqual(self.posts()[0][1],"/call")
        self.assertIn("not mean answered",result["delivery_notice"])
        self.assertEqual(self.posts()[0][2]["assistantOverrides"]["maxDurationSeconds"],600)
        self.assertNotIn("assistantOverrides",self.body)
    def test_invalid_number_or_duration_never_dials(self):
        self.body["customer"]["number"]="2125550101"
        self.assertEqual(self.delivery.dial(self.body)[0],400)
        self.body["customer"]["number"]=TARGET;self.body["assistantOverrides"]={"maxDurationSeconds":float("nan")}
        self.assertEqual(self.delivery.dial(self.body)[0],400);self.assertFalse(self.posts())
    def test_sales_scope_excludes_unlisted_and_own_numbers(self):
        for number in ("+12125550999","+19293072035"):
            self.body["customer"]["number"]=number
            self.assertEqual(self.delivery.dial(self.body)[0],403)
        self.assertFalse(self.posts())
    def test_provider_preflight_failure_never_dials(self):
        self.delivery.api=lambda *args:(401,{})
        self.assertEqual(self.delivery.dial(self.body)[0],401)
    def test_duplicate_running_call_is_not_dialed_twice(self):
        self.delivery.dial(self.body)
        self.assertEqual(self.delivery.dial(self.body)[0],409);self.assertEqual(len(self.posts()),1)
    def test_timeout_reconciles_call_name_without_redial(self):
        self.api.post_error=(503,{"error":"timeout"})
        status,_=self.delivery.dial(self.body);self.assertEqual(status,503)
        self.clock[0]+=61
        self.assertEqual(self.delivery.dial(self.body)[0],409)
        self.assertEqual(len(self.posts()),1)
    def test_missing_receipt_stays_uncertain(self):
        self.api.post_error=(503,{})
        self.delivery.dial(self.body);self.api.calls.clear();self.clock[0]+=61
        self.assertEqual(self.delivery.dial(self.body)[0],409);self.assertEqual(len(self.posts()),1)
    def test_finished_call_allows_next_destination(self):
        self.delivery.dial(self.body);self.api.calls["1"]["status"]="ended"
        self.body["customer"]["number"]="+12125550102"
        self.assertEqual(self.delivery.dial(self.body)[0],201)
    def test_other_active_call_serializes_destinations(self):
        self.delivery.dial(self.body);self.body["customer"]["number"]="+12125550102"
        self.assertEqual(self.delivery.dial(self.body)[0],409);self.assertEqual(len(self.posts()),1)
    def test_explicit_suppression_and_opt_out_persist(self):
        self.delivery.block(TARGET)
        self.assertEqual(self.delivery.dial(self.body)[0],403)
        self.assertFalse(self.posts())
    def test_transcript_opt_out_suppresses_future_call(self):
        self.delivery.dial(self.body);self.api.calls["1"].update(status="ended",transcript="User: Please do not call again.")
        self.clock[0]+=61
        self.assertEqual(self.delivery.dial(self.body)[0],403)
    def test_concurrent_submissions_reserve_once(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            statuses=list(pool.map(lambda _:self.delivery.dial(self.body)[0],range(2)))
        self.assertEqual(sorted(statuses),[201,409]);self.assertEqual(len(self.posts()),1)
    def test_private_journal_does_not_store_number_or_transcript(self):
        self.delivery.dial(self.body)
        self.assertNotIn(TARGET.encode(),self.delivery.path.read_bytes())
        self.assertEqual(self.delivery.path.stat().st_mode & 0o777,0o600)

class CheckoutTests(unittest.TestCase):
    def call(self):
        return {"id":"test-call","assistantId":ASSISTANT,"status":"ended","analysis":{"structuredData":{
            "checkout_requested":True,"email_confirmed":True,"human_conversation":True,"do_not_call":False,"email":"owner@example.com"}}}
    def test_opted_in_owner_gets_exact_link_and_clear_terms(self):
        result=checkout.handoff(self.call())
        self.assertIn(checkout.CHECKOUT_URL,result["body"]);self.assertIn("$449.98",result["body"])
        self.assertEqual(result["state"],"prepared_not_sent")
    def test_no_message_for_no_consent_bad_email_dnc_or_nonhuman(self):
        for key,value in (("checkout_requested",False),("email_confirmed",False),("human_conversation",False),("do_not_call",True),("email","victim@example.com\nBcc:other@example.com")):
            call=self.call();call["analysis"]["structuredData"][key]=value
            self.assertIsNone(checkout.handoff(call))
    def test_demo_unfinished_and_missing_analysis_ignored(self):
        for key,value in (("assistantId","demo"),("status","ringing"),("analysis",{})):
            call=self.call();call[key]=value;self.assertIsNone(checkout.handoff(call))
    def test_claim_is_atomic_and_completion_requires_claim(self):
        with tempfile.TemporaryDirectory() as temp,patch.dict(os.environ,{"BOOKED_SOLID_STATE_DIR":temp}),contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(vapi.main(["vapi.py","checkout-claim","test-call"]),0)
            self.assertEqual(vapi.main(["vapi.py","checkout-claim","test-call"]),1)
            self.assertEqual(vapi.main(["vapi.py","checkout-complete","unknown","receipt"]),1)
            self.assertEqual(vapi.main(["vapi.py","checkout-complete","test-call","receipt"]),0)

class HelperTests(unittest.TestCase):
    def test_alert_caller_id_is_defined_and_uses_delivery_wrapper(self):
        with patch.object(vapi,"call_api",return_value=(201,{})) as api,contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(vapi.main(["vapi.py","alert-call","Example alert"]),0)
        self.assertEqual(api.call_args.args[2]["phoneNumberId"],NUMBER)
    def test_get_retries_but_post_never_retries(self):
        with patch.object(vapi,"transport",side_effect=[(503,{}),(200,{})]) as api,patch.object(vapi.time,"sleep"):
            self.assertEqual(vapi.read_api("GET","/assistant")[0],200);self.assertEqual(api.call_count,2)
        with patch.object(vapi,"transport",return_value=(503,{})) as api:
            self.assertEqual(vapi.read_api("POST","/call",{})[0],503);self.assertEqual(api.call_count,1)
    def test_repair_preview_is_read_only(self):
        api=FakeAPI()
        with patch.object(vapi,"read_api",side_effect=api):
            status,result=vapi.repair_assistants()
        self.assertEqual(status,200);self.assertTrue(result["preview"])
        self.assertTrue(all(r[0]=="GET" for r in api.requests))
    def test_repair_preserves_model_and_is_verified(self):
        saved={};api=FakeAPI()
        def provider(method,path,body=None):
            if method=="PATCH":saved[path]=body;return 200,body
            if path in saved:return 200,saved[path]
            return api(method,path,body)
        with patch.object(vapi,"read_api",side_effect=provider):status,result=vapi.repair_assistants(True)
        self.assertEqual(status,200);self.assertTrue(all(r["verified"] for r in result["results"]))
        self.assertEqual(saved["/assistant/"+ASSISTANT]["model"]["model"],"gpt-4.1")
        self.assertIn(checkout.PURCHASE_RULES,saved["/assistant/"+ASSISTANT]["model"]["messages"][0]["content"])
    def test_provider_error_does_not_leak_secrets(self):
        original={"model":{"apiKey":"secret"},"server":{"headers":{"Authorization":"secret"}},"password":"secret"}
        self.assertNotIn("secret",json.dumps(vapi.redact(original)))
    def test_policy_has_no_false_success_and_stops_goodbye_loop(self):
        body=vapi.assistant_policy({"model":{"messages":[{"role":"system","content":"Hello"}]}},outreach=True)
        self.assertIn("Goodbye.",body["endCallPhrases"])
        self.assertIn("no booking or SMS tool",body["model"]["messages"][0]["content"])
    def test_demo_and_sales_builders_do_not_reintroduce_false_promises(self):
        for command in ("create-demo","update-demo","update-outreach"):
            with patch.object(vapi,"call_api",return_value=(200,{})) as api,contextlib.redirect_stdout(io.StringIO()):
                vapi.main(["vapi.py",command])
            body=api.call_args.args[2]
            text=json.dumps(body)
            self.assertNotIn("it is booked and that a confirmation text will follow",text)
            self.assertNotIn("setup charged today and $199.99 a month after that",text)
            self.assertNotIn("promise the shop will call back as soon as it opens",text)

class BridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http=server.ThreadingHTTPServer(("127.0.0.1",0),server.Handler)
        cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.thread.start()
        cls.url="http://127.0.0.1:"+str(cls.http.server_port)
    @classmethod
    def tearDownClass(cls):cls.http.shutdown();cls.http.server_close()
    def request(self,path,data,headers=None):
        try:
            with urlopen(Request(self.url+path,data=json.dumps(data).encode(),headers={"Content-Type":"application/json",**(headers or {})}),timeout=2) as r:return r.status,json.load(r)
        except HTTPError as e:return e.code,json.load(e)
    def test_health_and_strict_routes(self):
        with urlopen(self.url+"/health") as r:self.assertEqual(json.load(r)["version"],2)
        self.assertEqual(self.request("/unrelated",{"query":"test"})[0],404)
    def test_optional_token_enforced(self):
        with patch.dict(os.environ,{"JARVIS_LOOKUP_TOKEN":"synthetic"}),patch.object(server,"lookup",return_value="ok"):
            self.assertEqual(self.request("/lookup",{"query":"test"})[0],401)
            self.assertEqual(self.request("/lookup",{"query":"test"},{"Authorization":"Bearer synthetic"})[0],200)
    def test_tool_envelope_and_invalid_payloads(self):
        with patch.object(server,"lookup",return_value="A result"):
            code,data=self.request("/lookup",{"message":{"type":"tool-calls","toolCallList":[{"id":"tool-1","function":{"arguments":"{\"query\":\"weather\"}"}}]}})
            self.assertEqual(data["results"],[{"toolCallId":"tool-1","result":"A result"}])
            self.assertEqual(self.request("/lookup",[])[0],400)
            self.assertEqual(self.request("/lookup",{"message":{"toolCallList":[1]}})[0],400)
    def test_lookup_deadline_is_real(self):
        def slow(q):time.sleep(.1);return "late"
        with patch.object(server,"lookup_sources",side_effect=slow),patch.object(server,"DEADLINE",.01):
            before=time.monotonic();result=server.lookup("test")
            self.assertLess(time.monotonic()-before,.08);self.assertIn("timed out",result)
        time.sleep(.11)
    def test_busy_lookup_never_adds_unbounded_work(self):
        with patch.object(server,"SLOTS") as slots:
            slots.acquire.return_value=False
            self.assertIn("busy",server.lookup("test"))
    def test_watchdog_rejects_arbitrary_http_listener(self):
        with patch.object(watchdog,"fetch",return_value=(404,"not found")):
            self.assertFalse(watchdog.local_ok(8791))
        with patch.object(watchdog,"fetch",return_value=(200,json.dumps({"ok":True,"service":"booked-solid-lookup","version":2}))):
            self.assertTrue(watchdog.local_ok(8791))
    def test_failed_tool_update_does_not_publish_new_tunnel_as_active(self):
        with tempfile.TemporaryDirectory() as temp:
            urls=Path(temp)/"urls.json";urls.write_text(json.dumps({"bridge":"https://old.example"}))
            with patch.object(watchdog,"URLS_FILE",str(urls)),patch.object(watchdog,"start_tunnel",return_value="https://new.example"),patch.object(watchdog.subprocess,"run") as run:
                run.return_value.returncode=1
                with self.assertRaises(RuntimeError):watchdog.rebuild_tunnel()
            self.assertEqual(json.loads(urls.read_text())["bridge"],"https://old.example")

if __name__=="__main__":unittest.main()
