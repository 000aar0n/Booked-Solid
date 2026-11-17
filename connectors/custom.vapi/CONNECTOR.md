# Vapi

- `custom.vapi` connects Muse to Vapi through its REST API. It authenticates with the registered `api_key` credential and calls only `api.vapi.ai`.

- The helper is `~/workspace/custom-connectors/custom.vapi/bin/vapi.py`. It verifies the key, lists assistants and phone numbers, creates the Jarvis assistant and a Vapi phone number, attaches the assistant to the number for inbound calls, and places outbound phone calls.

## Connect

- The connection was registered with `credentials.request_api_access` and these details. Reuse them to reconnect:

```json
{
  "provider": "vapi",
  "auth_scheme": "api_key",
  "placement": "bearer_header",
  "api_hosts": ["api.vapi.ai"]
}
```

- Before the first change in a conversation, prove access with a harmless read:

```text
python3 ~/workspace/custom-connectors/custom.vapi/bin/vapi.py assistants
```

## Credentials

- The registered connection holds the credential. Helpers import `/opt/muse/skills/custom-connector-setup/bin/dynamic_credentials.py`, which returns an `hsurr:` surrogate and places it where the provider reads the key. Muse swaps in the real credential only on an approved request to a registered host.

- Never put a key, token, password or cookie in this doc, a helper, a command argument, an environment variable or a log. Never ask the user to paste one in chat.

- Keep redirects disabled on authenticated requests.

- On a 401 or 403, check the request first. Confirm that the helper attached the credential, that the host is registered and that the placement and scopes match.

- Only when a request that carried the credential is still rejected, call `credentials.request_api_access` with the details above and `"reconnect": true`.

## Current resources

- The Jarvis assistant has id `189f4d6b-44b8-407b-9ff6-93b88a6a5f43`. It uses OpenAI gpt-4o, the Vapi voice Elliot and Deepgram nova-2 transcription.

- The Vapi phone number is +19293072035 with id `b323d332-22ad-43b1-8ddc-3737e61c7552`. The Jarvis assistant is attached to it, so inbound calls to that number reach Jarvis.

- The outbound number is the imported Telnyx number +19293070119 with id `45d8d383-906e-4b88-ad9c-5da9ef6ce10a`, labelled Jarvis. Outbound calls to the user go from this number. The first successful outbound call was placed on 2026-11-16.

- The Telnyx account is a trial account. It may dial only its one verified number, the user's cell, and calls cap at 10 minutes. The Telnyx number is reclaimed within 30 days unless the account upgrades.

- A default sample assistant named Riley also exists in the organization. Leave it alone unless the user asks.

## List assistants and phone numbers

- Read the assistants or phone numbers in the organization:

```text
python3 ~/workspace/custom-connectors/custom.vapi/bin/vapi.py assistants
python3 ~/workspace/custom-connectors/custom.vapi/bin/vapi.py numbers
```

- Both commands print the HTTP status and the JSON payload. The numbers output shows each number, its id, its provider and its status.

## Create the Jarvis assistant

- Create the Jarvis assistant with its system prompt, first message and voice:

```text
python3 ~/workspace/custom-connectors/custom.vapi/bin/vapi.py create-assistant
```

- The command returns status 201 and the new assistant id. Run `assistants` first and skip this when a Jarvis assistant already exists, because a timed-out create may still have landed.

## Create a Vapi phone number

- Create a free Vapi-managed number in a US area code:

```text
python3 ~/workspace/custom-connectors/custom.vapi/bin/vapi.py create-number 929
```

- The area code argument is required by the API. Area code 212 was unavailable and the API suggested 929, 516 and 585. A new number starts in status `activating` and turns `active` within a few minutes.

## Attach the assistant for inbound calls

- Attach an assistant to a phone number so inbound calls reach it:

```text
python3 ~/workspace/custom-connectors/custom.vapi/bin/vapi.py attach <phoneNumberId> <assistantId>
```

- The command returns the updated number with its assistantId set.

## Place an outbound call

- Place an outbound phone call from a phone number to a customer number in E.164 format:

```text
python3 ~/workspace/custom-connectors/custom.vapi/bin/vapi.py call <phoneNumberId> <assistantId> <customerNumberE164>
python3 ~/workspace/custom-connectors/custom.vapi/bin/vapi.py get-call <callId>
python3 ~/workspace/custom-connectors/custom.vapi/bin/vapi.py calls
```

- On the free Vapi number this returns a 400 error, because free Vapi numbers are inbound only. Use the imported Telnyx number id for outbound calls.

## Recover from errors

- A 400 saying the phoneNumber is activating means the new number is still provisioning. Wait a few minutes, confirm status `active` with the numbers command, then retry.

- A 400 saying numbers bought on Vapi have a daily outbound call limit means the number is a free Vapi number. Free Vapi numbers cannot dial out at all, so retrying does not help.

- An ended call with reason `call.start.error-get-transport` and a Telnyx 403 means Telnyx refused the dial. Check two things in the Telnyx portal: the destination is the account's verified number (trial accounts may dial nothing else), and the Vapi Call Control application has an Outbound Voice Profile assigned. A missing profile was the cause on 2026-11-16 and creating the profile fixed it.

- Requests sometimes time out through the network tunnel. After a failed or timed-out change, check the current state with a read before trying again, because the first request may have completed.

## Limits

- Free Vapi numbers are inbound only. Outbound calling needs a number imported from a telephony provider such as Twilio, Telnyx or Vonage.

- Vapi SMS needs a 10DLC-approved Twilio number imported into Vapi, and the assistant cannot send the first text. Plain Jarvis texting is not available on the free number.

- Calls consume Vapi credits even on the free number. The account started with a small free credit balance.

- Use `muse.skill_search` to find other skills and `muse.connector_search` to find other connectors.
