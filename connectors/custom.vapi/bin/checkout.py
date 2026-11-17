"""Fixed checkout handoffs. This prepares an email; Muse Mail sends it separately."""
import re
from call_runtime import OUTREACH_ID

CHECKOUT_URL = "https://buy.stripe.com/9B6cN492O8PQ3dm4uiejK00"
PURCHASE_RULES = (
    " DIRECT PURCHASE: An interested owner can buy without first booking a meeting. "
    "Offer to email the secure Stripe checkout link immediately after this call. "
    "Ask whether they want that link; obtain and spell back their email. Do not "
    "collect card numbers, payment credentials or passwords by voice. Explain the "
    "listed $249.99 setup fee plus $199.99 per month; the documented initial "
    "checkout collects setup and the first month ($449.98 before any taxes/fees). "
    "Stripe's displayed total and recurring terms must be reviewed before payment. "
    "The authorized checkout URL is "+CHECKOUT_URL+". Do not invent shorter URLs. "
    "A link request is not a sale or proof of payment. Do not promise the email "
    "has been sent while it is only queued for Muse. Tell Muse the email and "
    "that the owner explicitly requested checkout. No SMS is configured or promised."
)


def extraction_plan():
    return {"enabled":True,"schema":{
        "type":"object", "additionalProperties":False,
        "properties":{
            "checkout_requested":{"type":"boolean","description":"True only if the human explicitly asked for or agreed to receive the payment link; false for voicemail, refusal, demo and assistant suggestions alone."},
            "email":{"type":"string","description":"Exact buyer email spelled back and confirmed by the human; empty if missing or uncertain."},
            "email_confirmed":{"type":"boolean"},
            "do_not_call":{"type":"boolean"},
            "human_conversation":{"type":"boolean"},
        },"required":["checkout_requested","email","email_confirmed","do_not_call","human_conversation"]}}


def handoff(call):
    if call.get("assistantId") != OUTREACH_ID or call.get("status") != "ended":
        return None
    data = (call.get("analysis") or {}).get("structuredData") or {}
    if not isinstance(data,dict) or not all(data.get(k) is True for k in ("checkout_requested","email_confirmed","human_conversation")):
        return None
    if data.get("do_not_call") is not False:
        return None
    email = data.get("email", "")
    if not isinstance(email,str) or len(email)>254 or not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", email):
        return None
    return {"call_id":call["id"],"to":email,"subject":"Your Booked Solid checkout link",
            "body":"Thanks for asking for the Booked Solid checkout link.\n\n"+
            CHECKOUT_URL+"\n\nThe listed plan is $249.99 setup plus $199.99/month. "
            "Our documented initial checkout total is $449.98 for setup and the first month, "
            "before any taxes or fees. Review Stripe's displayed total and recurring terms "
            "before paying. Aaron will confirm your setup timeline.\n\nBooked Solid",
            "state":"prepared_not_sent", "notice":"Muse Mail must return a send receipt. Sending this link does not prove payment."}
