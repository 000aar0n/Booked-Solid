---
id: booked-solid-telnyx-upgrade-reminder
title: 'Booked Solid Wave 1: Upper East Side calls'
enabled: true
owner: goal:ai-front-desk-business-for-salons-and-barbershops
mode: task
schedule:
  kind: runonce
  timezone: America/New_York
  at: 2026-11-17T11:39:00
delivery:
  - chat_id: 8177e88f-de81-4cb5-88eb-5ac0d2dc7bd3
metadata:
  tags: [cron:flexible-time]
  originating_chat_context_json: '{"chat_id":"8177e88f-de81-4cb5-88eb-5ac0d2dc7bd3","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"26cd7709-95f9-45f3-897d-659c6f4732fd"}'
  presentation_locale: en-US
---
Run Wave 1 of the Booked Solid outreach calls: the Upper East Side. Budget about an hour for the whole wave. Calls go one at a time, never in parallel. Context: Aaron upgraded his Telnyx account to Paid on Mon 2026-11-16 night (verified by a live test call to a non-verified number, which connected). Aaron chose live calls over voicemail drops. Stripe is connected (live account "Booked Solid") and the checkout link is live: https://buy.stripe.com/9B6cN492O8PQ3dm4uiejK00 ($249.99 setup charged once, then $199.99 a month).

Instant alerts (Aaron's rule): the moment a call ends with any of these outcomes, signed up, booked with Jarvis, or Aaron to call them, do not wait for the end-of-wave summary. Immediately send Aaron a short message in this chat naming the shop and what they agreed to, and place one alert call: python3 ~/workspace/custom-connectors/custom.vapi/bin/vapi.py alert-call "<one sentence: shop name, what they want, and when>". Only place the alert call between 08:00 and 22:00 New York time; outside that window the chat message alone is enough.

Use the Vapi helper at ~/workspace/custom-connectors/custom.vapi/bin/vapi.py. Place each call as: python3 vapi.py call 45d8d383-906e-4b88-ad9c-5da9ef6ce10a c36426ed-b325-46c8-9287-2da3471fddd9 <shop number>. That is the Telnyx phone number +1 (929) 307-0119 and the Booked Solid Outreach assistant. The shops for this wave, with hours and angles, are in ~/workspace/goals/ai-front-desk-business-for-salons-and-barbershops/hidden_files/call-kit.md: Hair Bar NYC +12122192211, Beyond The Beard +18624320121, Debonair +15165571508, Willy's Hair Styling +12126283198, Sharp Styles Barbershop +19172612031, Honeybliss Salon +12122881676.

The assistant's script (already loaded on it): the open tells them they can hang up any time if not interested; if interested, PATH A books a 10-minute meeting with Aaron right on the call (day, time, call or in person, callback number captured), and PATH B, for the skeptical, has Aaron call them personally at a time they pick, or gives them Aaron's number 917-565-7862 to reach him directly. If a shop says yes to starting, Jarvis confirms the prices and captures the owner's email and mobile, and promises the secure checkout link by email right after the call. Lukewarm contacts may agree to receive the one-page summary.

Payment step: after any call where the shop said yes to starting and gave an email, immediately send that email the checkout link https://buy.stripe.com/9B6cN492O8PQ3dm4uiejK00 via Muse Mail: a short note from Booked Solid thanking them, restating $249.99 setup today then $199.99 a month, no contract, and the link. Log that the link was sent. Never send the checkout link to a shop that did not say yes.

Rules: one call per shop, wait for each call to end before placing the next (check with vapi.py get-call <id>), and read its outcome from the call record. If a shop asked not to be called again, record it as DO NOT CALL in the call kit and never dial it again. Log every outcome in the Outcomes log section of call-kit.md using these categories: signed up, checkout link sent (include the email) / booked with Jarvis (include the day, time and format captured) / Aaron to call them (include the time and number captured) / send one-pager (include the email or number captured) / reached staff, owner not in (include when the owner is usually in) / voicemail / no answer / hung up / not interested / DO NOT CALL, each with a one-line note from the transcript.

When the wave is done, send Aaron one summary message in this chat: shop by shop outcomes, any signups and whether their checkout link went out, any meetings booked with their day and time, any Aaron-callback commitments with their times, and anything that needs his personal follow-up. Keep it short and plain, no em dashes.

Results email (Aaron's ask, Tue 2026-11-17): after the chat summary, also email the same results to Aaron at aaronkotchen@gmail.com via Muse Mail, subject "Booked Solid Wave 1 results: Upper East Side", written from Booked Solid. This email goes only to Aaron.
