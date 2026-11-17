# Repair and activation status

This changes repository source. It does not prove the live Muse VM, Vapi assistants or scheduled jobs were updated. No real calls, emails, SMS messages or payments were performed from Work.

## Source fixes

- Fixed the undefined Telnyx number constant that broke alert calls.
- Existing routine prospect outreach uses standing owner permission with no per-call approval prompt. Sales targets are limited to the citywide, premium and original call-kit lists; own/demo numbers are excluded to prevent bot loops. Explicit do-not-call entries and finished-call opt-outs suppress future calls.
- Outbound creates use the current documented POST /call endpoint. Resource preflight, E.164 validation, one active attempt, a private HMAC-indexed SQLite journal and provider-call reconciliation distinguish created, queued, connected, ended, rejected and uncertain outcomes. POST never retries blindly; GET can retry transient errors. A provider timeout with no conclusive receipt deliberately holds further dialing until reconciled.
- Fixed-duration calls stop after at most 600 seconds. The assistant prompt and goodbye phrase address bot-to-bot/goodbye loops. Voice behavior remains probabilistic and still needs real testing.
- Removed simulated bookings/confirmation-text claims and unsupported promises about Aaron's availability or next-day deployment. No real calendar booking adapter is present in this repository.
- Interested owners can request the fixed Stripe purchase link without a prior meeting. Ended human calls with verified opt-in/email are prepared for Muse Mail. Shared atomic claims and send receipts prevent wave/watch jobs from blindly duplicating an email. A requested/sent link is not a paid signup.
- No SMS integration. Owner updates go through Muse. The exported one-minute checkout task must actually be installed before it can run.
- Lookup requests have bounded payloads, strict routing, correct tool-call envelopes, a shared six-second batch deadline and at most four outstanding lookup workers. Optional JARVIS_LOOKUP_TOKEN authentication is supported; it is not enabled or wired to Vapi automatically by this patch.
- The watchdog now requires the actual service's versioned health result, checks tool-update subprocess success, returns failure exit codes and does not kill unrelated localhost.run tunnels. Existing old bridge processes require a controlled restart while calls are idle.
- Provider keys remain inside the Muse credential-surrogate boundary. Error bodies and credential-like response fields are not printed. No key is copied from Muse or stored in GitHub.

## Activation in Muse

Sync this repository's latest main into the authorized Muse VM. Keep the existing registered custom.vapi connection and current working model/voice settings.

Run from the checked-out repo:

```sh
python3 ops/install_repairs.py
python3 ops/install_repairs.py --apply
```

The first command performs read-only preflight. The second runs offline tests, backs up/replaces source helpers and updates the four existing saved assistants, then reads them back. It makes no calls or mail sends. A partial/uncertain update must be inspected before retrying. New helper modules call_runtime.py and checkout.py must accompany vapi.py; do not copy only vapi.py.

Use Muse's scheduler to sync the revised existing waves and install business/crons/booked-solid-checkout-delivery__interval@1m.md. A markdown export does not update a live schedule by itself. Follow business/ops/checkout-delivery.md for the single send/receipt procedure.

Inspect the live Stripe account/link before activation: the repo describes setup plus the first month ($449.98 before taxes/fees) and $199.99/month thereafter. Work could not independently load the Stripe page, and has not verified tax, trial, cancellation or current price settings. Never quote an unverified payable total or mark a customer paid without a Stripe receipt.

Do not interrupt an active customer call to restart the lookup process. When idle, restart only the known jarvis-brain/server.py process through Muse's existing process controls, run stack_watchdog.py, require HEALTHY and verify the live tool result. If enabling lookup authentication, set the private token in both the bridge runtime and the existing Vapi tool header; preserve other server configuration.

Then verify a real owner-authorized test call, a rejected destination, an unanswered call and a completed conversation. Confirm each status/endedReason and no duplicate calls. Verify an opted-in checkout email with Muse Mail's provider receipt. Never claim every call will connect: carrier account limits, outages, blocked numbers and recipient availability remain outside the helper's control.

## Work environment limits

This Work container lacks /opt/muse/skills/custom-connector-setup/bin/dynamic_credentials.py and has no authenticated Vapi/Telnyx/Stripe/Muse Mail session. The credentials were not requested in chat or extracted. Source repairs and offline tests are possible here; live assistant changes, real call validation, Stripe verification and Muse task installation require the authorized Muse runtime.

## Validation

Run `python -m unittest discover -s tests -v` and `python -m compileall -q jarvis connectors ops tests`. Tests use fake providers and local HTTP only. They exercise timeout reconciliation, duplicate/concurrent delivery, scope/do-not-call handling, exact checkout terms, consent/email validation, atomic email claims, read-only preview, assistant readback and a real bounded local lookup server. No test contacts a live telephony or payment provider.
