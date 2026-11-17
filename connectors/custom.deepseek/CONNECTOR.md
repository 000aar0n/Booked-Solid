# Deepseek

- `custom.deepseek` connects Muse to DeepSeek through its REST API. It authenticates with the registered `api_key` credential and calls only `api.deepseek.com`.

- Helpers live in `~/workspace/custom-connectors/custom.deepseek/bin/`. `deepseek.py` lists models, shows the account balance and sends one-shot chat completions.

## Connect

- The connection was registered with `credentials.request_api_access` and these details. Reuse them to reconnect:

```json
{
  "provider": "deepseek",
  "auth_scheme": "api_key",
  "placement": "bearer_header",
  "api_hosts": ["api.deepseek.com"]
}
```

- Before the first change in a conversation, prove access with a harmless read:

```text
python3 ~/workspace/custom-connectors/custom.deepseek/bin/deepseek.py models
```

## Credentials

- The registered connection holds the credential. Helpers import `/opt/muse/skills/custom-connector-setup/bin/dynamic_credentials.py`, which returns an `hsurr:` surrogate and places it where the provider reads the key. Muse swaps in the real credential only on an approved request to a registered host.

- Never put a key, token, password or cookie in this doc, a helper, a command argument, an environment variable or a log. Never ask the user to paste one in chat.

- Keep redirects disabled on authenticated requests.

- On a 401 or 403, check the request first. Confirm that the helper attached the credential, that the host is registered and that the placement and scopes match.

- Only when a request that carried the credential is still rejected, call `credentials.request_api_access` with the details above and `"reconnect": true`.

## List models

- List the models the account can call. This read also proves the key authenticates:

```text
python3 ~/workspace/custom-connectors/custom.deepseek/bin/deepseek.py models
```

- Verified 2026-11-16 with status 200. The account offers exactly two models, `deepseek-flash` (DeepSeek-V4.1-Flash) and `deepseek-v4-pro`, each with a 1,048,576 token context window. There is no `deepseek-chat` alias on this account.

## Check balance

- Show the account balance and whether the account can serve requests:

```text
python3 ~/workspace/custom-connectors/custom.deepseek/bin/deepseek.py balance
```

- The output carries `is_available` plus `balance_infos` with `total_balance`, `granted_balance` and `topped_up_balance` in USD. Verified 2026-11-16 with status 200, when the balance was 0.00 and `is_available` was false.

## Chat completion

- Send one user prompt and print the full JSON response:

```text
python3 ~/workspace/custom-connectors/custom.deepseek/bin/deepseek.py chat deepseek-flash "your prompt"
```

- The first argument is the model id and the second is the prompt. Use `deepseek-flash` for voice and other latency sensitive work.

- This operation is written but not yet verified end to end. On 2026-11-16 it returned status 402 because the account balance was zero. The request shape follows the documented OpenAI compatible format.

## Recover from errors

- Status 402 with `insufficient_balance_error` means the account has no funds. The user tops up at platform.deepseek.com under billing. Do not retry chat calls until the balance read shows funds and `is_available` true.

- Status 401 or 403 means the credential did not authenticate. Follow the credential checks above before reconnecting.

- After a failed or timed-out change, check the current state with a read before trying again, because the first request may have completed.

## Limits

- Chat completions bill against the account balance and stop working at zero. Reads such as models and balance still answer with an empty balance.

- This connector reaches only `api.deepseek.com`. It cannot manage the account, add funds or create keys.

## Related skills

- Use `muse.skill_search` to find other skills and `muse.connector_search` to find other connectors.
