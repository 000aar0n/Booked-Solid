# Direct purchase handoff through Muse

Interested owners can request the payment link during outreach without booking a meeting first. The assistant collects and spells back their email and explains the upfront and recurring charges. It never collects card details.

Fixed URL: https://buy.stripe.com/9B6cN492O8PQ3dm4uiejK00 .
The repository documents $249.99 setup plus the first $199.99 month at checkout ($449.98 before taxes/fees), then $199.99/month. The live Stripe page could not be independently loaded from Work. Muse must read the live Stripe account/link before activation and reconcile any different amount, trial or tax setting; do not quote an unverified payable total.

1. Run `vapi.py checkout-pending`. It reads the latest 100 calls and prepares emails only for ended outreach calls with structured data reporting a human request, a confirmed valid email and no do-not-call flag. This bounded scan is not an unlimited backfill.
2. Read the exact call transcript to verify the request and spelled-back email. Structured extraction can be wrong; do not send solely because a boolean is true.
3. Run `vapi.py checkout-claim CALL_ID` immediately before sending. A 409 means another task already claimed/sent it. Wave jobs and the one-minute watcher must use this same claim.
4. Use the existing authorized Muse Mail connection to send the prepared recipient/subject/body. No per-link owner approval is needed for this requested ordinary business handoff. Do not substitute SMS or email someone who did not request it.
5. Only after Muse Mail returns a provider message ID, run `vapi.py checkout-complete CALL_ID MESSAGE_ID`, then notify Aaron in Muse.
6. If a send times out or crashes, the claim stays in sending state and is excluded from automatic sends. Check Muse Mail's Sent folder and reconcile the provider result. Do not delete the claim and blindly resend.
7. A link request, successful email send or a caller saying yes is not payment. Verify a Stripe payment/subscription receipt before reporting a paid customer. If Stripe is unavailable, report payment as unverified.
8. No texting integration is requested. Muse chat is the owner notification channel.

The one-minute exported task must actually be installed in Muse using its scheduler. Until then, an active wave can execute the same procedure after each call. No external emails or payments are performed by the repository's tests.

