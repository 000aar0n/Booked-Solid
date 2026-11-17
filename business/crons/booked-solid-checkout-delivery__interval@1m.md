---
id: booked-solid-checkout-delivery
title: Booked Solid requested checkout links
enabled: true
owner: goal:ai-front-desk-business-for-salons-and-barbershops
mode: task
schedule:
  kind: interval
  timezone: America/New_York
  at: 2026-11-17T07:50:17
  every: 1m
delivery:
  - chat_id: 8177e88f-de81-4cb5-88eb-5ac0d2dc7bd3
metadata:
  tags: [cron:automatic-interval-anchor]
  originating_chat_context_json: '{"chat_id":"8177e88f-de81-4cb5-88eb-5ac0d2dc7bd3","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"26cd7709-95f9-45f3-897d-659c6f4732fd"}'
  presentation_locale: en-US
---
Deliver requested Booked Solid purchase links through Muse Mail using business/ops/checkout-delivery.md. Run checkout-pending, then validate each call's human request and confirmed email against its transcript. Use checkout-claim immediately before sending. Send only the fixed Stripe URL and the generated clear upfront/monthly terms. Record the actual Muse Mail send receipt using checkout-complete, and post the result to Aaron in this Muse chat. If a send or claim has an unknown outcome, reconcile Sent mail; do not retry blindly. No SMS and no extra alert call. Never mark a requested or sent link as payment received. Report unsupported mail access or missing Vapi analysis to Muse. Installing this exported task in Muse is required; this markdown does not schedule itself.

