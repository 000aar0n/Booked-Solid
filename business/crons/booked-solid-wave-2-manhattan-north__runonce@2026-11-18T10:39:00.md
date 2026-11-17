---
id: booked-solid-wave-2-manhattan-north
title: 'Booked Solid Wave 2: UWS, Harlem, Midtown, Chelsea'
enabled: true
owner: goal:ai-front-desk-business-for-salons-and-barbershops
mode: task
schedule:
  kind: runonce
  timezone: America/New_York
  at: 2026-11-18T10:39:00
delivery:
  - chat_id: 8177e88f-de81-4cb5-88eb-5ac0d2dc7bd3
metadata:
  tags: [cron:flexible-time]
  originating_chat_context_json: '{"chat_id":"8177e88f-de81-4cb5-88eb-5ac0d2dc7bd3","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"26cd7709-95f9-45f3-897d-659c6f4732fd"}'
  presentation_locale: en-US
---
Run Booked Solid outreach Wave 2: the Upper West Side, Harlem, Midtown and Chelsea shops (two per neighborhood) from ~/workspace/goals/ai-front-desk-business-for-salons-and-barbershops/hidden_files/citywide-list.md. Budget about an hour per neighborhood. Calls go one at a time, never in parallel: place a call, wait for it to end, log it, then dial the next.

Premium first (Aaron's rule, Mon 2026-11-16 night): target richer shops most likely to pay. Before the regular list, check ~/workspace/goals/ai-front-desk-business-for-salons-and-barbershops/hidden_files/premium-list.md and call any premium-tier shops in this wave's neighborhoods first, then the regular list.

Instant updates: immediately post outcomes, requested meeting/callback times and checkout-link delivery receipts to Aaron in this Muse chat. No SMS integration is requested. Do not create extra alert calls for these updates.

Mechanics: python3 ~/workspace/custom-connectors/custom.vapi/bin/vapi.py call 45d8d383-906e-4b88-ad9c-5da9ef6ce10a c36426ed-b325-46c8-9287-2da3471fddd9 <shop number> (Telnyx number +1 (929) 307-0119, Booked Solid Outreach assistant). Check each call with vapi.py get-call <id> and read the outcome from the record and transcript. The assistant pitches, books 10-minute meetings with Aaron, offers an Aaron callback for the skeptical, and closes signups by capturing the owner email.

Payment step: when a human explicitly requests or agrees to receive checkout and confirms their email, use the single delivery procedure in business/ops/checkout-delivery.md. No meeting is required before purchase. Claim each call with checkout-claim before Muse Mail sends, then record the provider send receipt with checkout-complete. Wave jobs and the one-minute watcher share this journal; never send twice. A requested or sent link is not a paid signup; verify payment separately through Stripe.

Log every outcome in ~/workspace/goals/ai-front-desk-business-for-salons-and-barbershops/hidden_files/waves-outcomes.md (create it with a header if missing), under a Wave 2 heading, using these categories: signed up, checkout link sent / booked with Jarvis / Aaron to call them / send one-pager / reached staff, owner not in / voicemail / no answer / hung up / not interested / DO NOT CALL, each with the shop name and a one-line note. A shop that asks not to be called again is DO NOT CALL forever.

When the wave is done, send Aaron one summary in this chat: outcomes per shop, signups and links sent, meetings booked with times, Aaron-callback commitments, and anything needing his personal follow-up. Short and plain, no em dashes.

Results email (Aaron's ask, Tue 2026-11-17): after the chat summary, also email the same results to Aaron at aaronkotchen@gmail.com via Muse Mail, subject "Booked Solid Wave 2 results: UWS, Harlem, Midtown, Chelsea", written from Booked Solid. This email goes only to Aaron.


Current operating rules (2026-11-17 repair): routine prospect calls have standing permission; no per-call owner approval prompt. Use the delivery helper so duplicate/uncertain submissions cannot trigger repeat calls. One active outbound call at a time. Reconcile existing provider receipts before dialing again. If the carrier rejects a call, report status and endedReason to Muse instead of claiming it connected. Demo requests are simulated, and meetings remain requested times until calendar confirmation. Checkout collects the documented setup fee and first month ($449.98 before taxes/fees), followed by $199.99/month; verify the current Stripe checkout totals before quoting a charge. Do not promise texts, calendar integrations, paid signups or next-day deployment without verified support. New source schedules only take effect when installed in Muse; updating GitHub does not update live jobs.

