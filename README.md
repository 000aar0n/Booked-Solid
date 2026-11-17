# Booked Solid

An AI front desk business for salons and barbershops, founded by Aaron Kotchen (New York). Aaron is the human front: sales and relationships. Jarvis, his AI agent, runs the operation: it answers calls, messages and email around the clock, books appointments, handles support and follows up with customers, sold as a monthly service.

Pricing: $249.99 setup fee plus $199.99 per month per location. No contract.

Live pieces:

- Demo line: call +1 (929) 307-2035 and book a haircut at the fictional Marlowe Barber Company. That is the sales demo.
- Pitch caller: an AI caller that phones prospect shops, pitches the service, books 10-minute meetings with Aaron, and captures signups.
- Aaron's personal Jarvis line: +1 (929) 307-0119.

## Layout

- `jarvis/` — the phone stack code.
  - `server.py` — the live lookup bridge behind the assistants' live_lookup tool (weather, stock quotes, news, facts). Speaks Vapi's tool-calls envelope and answers with a results array. Hard 6 second deadline per lookup.
  - `stack_watchdog.py` — keeps the lookup bridge and its tunnel alive and repoints the tool URL when the tunnel rotates. It never touches the assistant models.
  - `deepseek_proxy.py` — a pass-through proxy that was used to run the phone brain on DeepSeek without the API key leaving the vault. Retired from the live path on 2026-11-17; kept for reference.
  - `proxyconnect.py`, `start-openjarvis.py` — tunnel and legacy brain helpers from the same era.
- `connectors/` — the API helpers.
  - `custom.vapi/bin/vapi.py` — every Vapi operation: assistants, phone numbers, calls, tools, and the commands that configure the Jarvis, demo, outreach and alerts assistants. Credentials are fetched from a secure vault at runtime; no keys exist in this code.
  - `custom.deepseek/` — the DeepSeek helper (models, balance, chat), same vault pattern.
- `business/` — the operating record.
  - `GOAL.md` — day-1 decisions, pricing, market notes, prospect research.
  - `ops/` — the call kit and outreach script outcomes log, the citywide and premium prospect lists, and the watch files for sales, credits and demo bookings.
  - `crons/` — the scheduled jobs: the four outreach call waves (Nov 17 to 20, 2026) and the sales, credit and demo-booking watchers.
  - `website/` — the reference record for the public one-page site.

## Current state (2026-11-17)

- All four voice assistants (personal Jarvis, demo desk, outreach caller, alerts) run on Vapi-hosted OpenAI gpt-4.1 with the Vapi Elliot voice. The ElevenLabs George voice was retired after it repeatedly truncated speech mid-sentence; the DeepSeek and local-server brains were retired after tunnel failures caused hangups. Reliability won over novelty in both calls.
- Stripe is connected under the Booked Solid account; the checkout link charges the setup fee plus the first month.
- Outreach runs in waves, one call at a time, premium shops first. Any shop that says yes gets the checkout link by email; Aaron gets an instant alert call on any signup or meeting booked, and a results email after each wave.

## Editing notes

The assistants' prompts live inside `connectors/custom.vapi/bin/vapi.py` as command builders (set-cloud-brain, update-demo, update-outreach, set-speaking-plans, set-voice). The live assistants are configured by running those commands, not by editing this repo; this repo is the source and the record.
