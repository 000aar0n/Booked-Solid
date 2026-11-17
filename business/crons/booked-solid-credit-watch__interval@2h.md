---
id: booked-solid-credit-watch
title: Booked Solid credit watch
enabled: true
owner: goal:ai-front-desk-business-for-salons-and-barbershops
mode: task
schedule:
  kind: interval
  timezone: America/New_York
  at: 2026-11-17T01:53:58
  every: 2h
delivery:
  - chat_id: 8177e88f-de81-4cb5-88eb-5ac0d2dc7bd3
metadata:
  tags: [cron:automatic-interval-anchor]
  originating_chat_context_json: '{"chat_id":"8177e88f-de81-4cb5-88eb-5ac0d2dc7bd3","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"7ed4b6ca-9633-4c69-9a89-11add05c602e"}'
  presentation_locale: en-US
---
Credit watch for the Booked Solid phone operation. Aaron asked to be called by Jarvis if credits run low.

State file: ~/workspace/goals/ai-front-desk-business-for-salons-and-barbershops/hidden_files/credit-watch.md (create it if missing). It holds the last check time and the last alert time and reason. Read it first, update it every run.

Checks:
1. DeepSeek balance: run python3 ~/workspace/custom-connectors/custom.deepseek/bin/deepseek.py balance and read the total balance.
2. Vapi usage: run python3 ~/workspace/custom-connectors/custom.vapi/bin/vapi.py calls and sum the cost of calls created in the last 24 hours. Also note any calls since the last check whose endedReason points at transport or billing trouble (for example error-get-transport or a payment failure).

Breach if any of these is true: DeepSeek balance under $3; Vapi spend in the last 24 hours over $30; or two or more calls since the last check ended with transport or billing errors.

On a breach, if no alert was sent for the same breach in the last 12 hours: send Aaron one message in this chat with the actual numbers, and, if the local time in America/New_York is between 08:00 and 22:00, also place one alert call with: python3 ~/workspace/custom-connectors/custom.vapi/bin/vapi.py alert-call "<one short sentence naming what is low or failing and the number>". Record the alert time and reason in the state file.

If there is no breach, update the state file and send nothing.
