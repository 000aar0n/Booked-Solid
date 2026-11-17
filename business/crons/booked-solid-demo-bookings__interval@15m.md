---
id: booked-solid-demo-bookings
title: Booked Solid demo bookings to Aaron's inbox
enabled: true
owner: goal:ai-front-desk-business-for-salons-and-barbershops
mode: task
schedule:
  kind: interval
  timezone: America/New_York
  at: 2026-11-17T07:50:17
  every: 15m
delivery:
  - chat_id: 8177e88f-de81-4cb5-88eb-5ac0d2dc7bd3
metadata:
  tags: [cron:automatic-interval-anchor]
  originating_chat_context_json: '{"chat_id":"8177e88f-de81-4cb5-88eb-5ac0d2dc7bd3","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"26cd7709-95f9-45f3-897d-659c6f4732fd"}'
  presentation_locale: en-US
---
Watch the Booked Solid demo line for completed bookings and email them to Aaron, the way a shop owner would receive them.

State file: ~/workspace/goals/ai-front-desk-business-for-salons-and-barbershops/hidden_files/demo-bookings-watch.md (create it if missing). It holds the ids of demo calls already processed. Read it first.

Check: run python3 ~/workspace/custom-connectors/custom.vapi/bin/vapi.py calls and look at recent inbound calls handled by the demo assistant (assistantId bd9a8a3a-ece8-4028-94fd-b5262fdf32d5, the Marlowe Barber Company demo desk on +1 (929) 307-2035) that are not in the state file. For each, fetch the record with vapi.py get-call <id> and read the conversation.

A call counts as a completed booking only if the desk captured a service, a day and time, and the caller's name (ideally also a barber and a mobile number) and read the booking back as booked. Questions-only calls, date checks, hang-ups and test chats are not bookings.

For each completed booking not yet emailed: send one email to aaronkotchen@gmail.com via Muse Mail, from Booked Solid, subject "New booking: Marlowe Barber Company (demo line)", body listing the booking exactly as an owner would want it: service, barber, day and date, time, customer name, customer mobile, and a line noting it came in on the demo line and the call time. Then record the call id in the state file.

If there are no new completed bookings, send nothing and just update the state file with any non-booking demo call ids you reviewed so they are not re-read forever.
