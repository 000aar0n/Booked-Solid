# Booked Solid credit watch state

- Last check: 2026-11-17T09:53:58-05:00 (Tue 2026-11-17 09:53 EST, America/New_York)
- Last alert: 2026-11-17T01:53:58-05:00
- Last alert reason: Breach - 4 Vapi calls since last check (first check, no prior state file) ended with call.start.error-get-transport, meeting the >=2 transport/billing error threshold. Alert sent as a message in chat; no alert phone call placed because local time 01:53 EST is outside the 08:00-22:00 window.

## Last check details
- DeepSeek balance: $11.99 total (is_available: true) - not under $3 threshold
- Vapi spend last 24 hours: $8.6979 across 49 calls - not over $30 threshold
- Vapi transport/billing errors since last check (2026-11-17T07:53:58-05:00 / 12:53:58Z): 0 based on endedReason
- Calls since last check: 18 (12 customer-ended-call, 3 call.in-progress.error-providerfault-custom-llm-llm-failed, 1 exceeded-max-duration, 1 call.in-progress.error-assistant-did-not-receive-customer-audio, 1 silence-timed-out - the LLM-failed and other non-transport errors are not transport/billing errors under this watch's definition, so they do not count toward the breach threshold, but they were noted)
- Breach: NO
