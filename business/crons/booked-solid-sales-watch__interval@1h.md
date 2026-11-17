---
id: booked-solid-sales-watch
title: Booked Solid sales watch
enabled: true
owner: goal:ai-front-desk-business-for-salons-and-barbershops
mode: task
schedule:
  kind: interval
  timezone: America/New_York
  at: 2026-11-17T00:57:05
  every: 1h
delivery:
  - chat_id: 8177e88f-de81-4cb5-88eb-5ac0d2dc7bd3
metadata:
  tags: [cron:automatic-interval-anchor]
  originating_chat_context_json: '{"chat_id":"8177e88f-de81-4cb5-88eb-5ac0d2dc7bd3","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"7ed4b6ca-9633-4c69-9a89-11add05c602e"}'
  presentation_locale: en-US
---
Sales watch for Booked Solid. Aaron wants to know the moment money comes in.

State file: ~/workspace/goals/ai-front-desk-business-for-salons-and-barbershops/hidden_files/sales-watch.md (create it if missing). It holds the newest Stripe charge id already reported. Read it first.

Check: run /opt/hatch/bin/stripe charges list --limit 20 (live account "Booked Solid"). Look for charges with status succeeded or paid that are newer than the watermark charge id in the state file (on the first run, treat everything already there as old and just set the watermark).

For each genuinely new paid charge: update the watermark, send Aaron a message in this chat (Booked Solid sale: amount, customer name or email if shown, and what it likely is, setup fee or monthly), and, if the local time in America/New_York is between 08:00 and 22:00, place one alert call: python3 ~/workspace/custom-connectors/custom.vapi/bin/vapi.py alert-call "Booked Solid just made a sale. <customer or shop if known> paid <amount>."

If there is no new paid charge, update nothing and send nothing.
