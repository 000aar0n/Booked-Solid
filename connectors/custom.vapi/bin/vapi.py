#!/usr/bin/env python3
"""Vapi helper for Jarvis: verify the key, manage a phone number and the
Jarvis assistant, and place outbound calls to Aaron.

The API key never appears here. dynamic_credentials attaches the surrogate
for the registered connection custom.vapi, and Muse swaps in the real key
only on requests to api.vapi.ai.
"""
import json
import sys
import urllib.request

sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
from dynamic_credentials import add_surrogate_to_request, read_json_response

BASE = "https://api.vapi.ai"
HOSTS = ["api.vapi.ai"]
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        raise RuntimeError("redirect refused, verify the endpoint")


def call_api(method, path, body=None):
    data = None
    headers = {"User-Agent": UA}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(BASE + path, data=data, headers=headers,
                                     method=method)
    add_surrogate_to_request(request, "custom.vapi", allowed_hosts=HOSTS)
    opener = urllib.request.build_opener(NoRedirect())
    try:
        with opener.open(request, timeout=30) as response:
            return response.status, read_json_response(response)
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8", "replace")
        try:
            payload = json.loads(raw)
        except ValueError:
            payload = {"raw": raw[:500]}
        return err.code, payload


def main(argv):
    if len(argv) < 2:
        print("usage: vapi.py <assistants|numbers|create-number|"
              "create-assistant|call|get-call> [args]")
        return 2
    cmd = argv[1]

    if cmd == "assistants":
        status, payload = call_api("GET", "/assistant")
    elif cmd == "numbers":
        status, payload = call_api("GET", "/phone-number")
    elif cmd == "create-number":
        body = {"provider": "vapi"}
        if len(argv) > 2:
            body["numberDesiredAreaCode"] = argv[2]
        status, payload = call_api("POST", "/phone-number", body)
    elif cmd == "create-assistant":
        body = {
            "name": "Jarvis",
            "firstMessage": ("Hello Aaron, this is Jarvis. "
                             "The phone line is live, sir."),
            "firstMessageMode": "assistant-speaks-first",
            "model": {
                "provider": "openai",
                "model": "gpt-4o",
                "messages": [{
                    "role": "system",
                    "content": (
                        "You are Jarvis, Aaron Kotchen's personal agent, "
                        "speaking on a live phone call with Aaron. Be "
                        "proactive, concise, and dry-witted. Keep answers "
                        "short, one or two sentences unless he asks for "
                        "more. You are calling from Muse, his assistant "
                        "app. If he asks what this is, tell him it is the "
                        "first test call on his new Jarvis phone line."
                    ),
                }],
            },
            "voice": {"provider": "vapi", "voiceId": "Elliot"},
            "transcriber": {"provider": "deepgram", "model": "nova-2",
                            "language": "en"},
        }
        status, payload = call_api("POST", "/assistant", body)
    elif cmd == "call":
        # vapi.py call <phoneNumberId> <assistantId> <customerNumberE164>
        body = {
            "phoneNumberId": argv[2],
            "assistantId": argv[3],
            "customer": {"number": argv[4]},
        }
        status, payload = call_api("POST", "/call/phone", body)
    elif cmd == "get-call":
        status, payload = call_api("GET", "/call/" + argv[2])
    elif cmd == "update-assistant":
        # vapi.py update-assistant <assistantId>
        body = {
            "firstMessage": ("Hello Aaron, Jarvis here. "
                             "British voice, less attitude, as requested."),
            "model": {
                "provider": "openai",
                "model": "gpt-4o",
                "messages": [{
                    "role": "system",
                    "content": (
                        "You are Jarvis, Aaron Kotchen's personal agent, "
                        "speaking on a live phone call with Aaron. Be calm, "
                        "polite and understated, in the manner of a British "
                        "butler. No snark, no attitude, no jokes at his "
                        "expense. Keep answers short, one or two sentences "
                        "unless he asks for more. Speak clearly and at a "
                        "measured pace. If he asks what changed, tell him "
                        "the voice is now British, the tone is dialled "
                        "down, and noise cancellation is on."
                    ),
                }],
            },
            "voice": {
                "provider": "11labs",
                "voiceId": "JBFqnCBsd6RMkjVDRZzb",
                "model": "eleven_turbo_v2_5",
                "stability": 0.5,
                "similarityBoost": 0.75,
            },
            "backgroundDenoisingEnabled": True,
            "backgroundSound": "off",
        }
        status, payload = call_api("PATCH", "/assistant/" + argv[2], body)
    elif cmd == "live-brain":
        # vapi.py live-brain <assistantId> [provider] [model]
        provider_name = argv[3] if len(argv) > 3 else "openai"
        model_name = argv[4] if len(argv) > 4 else "gpt-4o-search-preview"
        body = {
            "firstMessage": ("Hello Aaron, Jarvis here, now with live "
                             "data. Ask me something current."),
            "model": {
                "provider": provider_name,
                "model": model_name,
                "messages": [{
                    "role": "system",
                    "content": (
                        "You are Jarvis, Aaron Kotchen's personal agent, "
                        "speaking on a live phone call with Aaron. Be calm, "
                        "polite and understated, in the manner of a British "
                        "butler. No snark and no attitude. You have live "
                        "web search built in: use it for anything current "
                        "or factual, including news, prices, weather and "
                        "scores, and never claim your knowledge stops at "
                        "a cutoff date. Keep spoken answers short, one to "
                        "three sentences, and do not read out citations "
                        "or URLs unless he asks."
                    ),
                }],
            },
        }
        status, payload = call_api("PATCH", "/assistant/" + argv[2], body)
    elif cmd == "set-brain":
        # vapi.py set-brain <assistantId> [model]
        model_name = argv[3] if len(argv) > 3 else "gpt-5.5"
        body = {
            "firstMessage": ("Hello Aaron, Jarvis here, running a "
                             "considerably sharper brain now."),
            "model": {
                "provider": "openai",
                "model": model_name,
                "messages": [{
                    "role": "system",
                    "content": (
                        "You are Jarvis, the personal agent of Aaron "
                        "Kotchen, speaking on a live phone call with him. "
                        "Aaron is a high school sophomore in New York "
                        "City. He runs a clothing brand called "
                        "Chromatism, trades a simulated stock portfolio "
                        "under a system called Protected Momentum, and "
                        "is preparing for the SAT. Be calm, polite and "
                        "understated, in the manner of a British butler. "
                        "No snark and no attitude. Think carefully "
                        "before you answer, be precise, and reason "
                        "through problems step by step internally while "
                        "keeping what you say concise: one to three "
                        "sentences unless he asks for detail. Never "
                        "invent facts. If something depends on current "
                        "information you do not have, say plainly that "
                        "you cannot check live data on this line yet "
                        "rather than guessing or citing a training "
                        "cutoff as an excuse to stop helping. Do the "
                        "math when he gives you numbers. Remember what "
                        "he tells you during the call and build on it."
                    ),
                }],
            },
        }
        status, payload = call_api("PATCH", "/assistant/" + argv[2], body)
    elif cmd == "create-tool":
        # vapi.py create-tool <serverUrl>
        body = {
            "type": "function",
            "function": {
                "name": "live_lookup",
                "description": (
                    "Fetch live, current information: stock prices, "
                    "weather, news headlines, scores and general facts "
                    "that may have changed recently. Use this whenever "
                    "Aaron asks about anything current or time "
                    "sensitive."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "A short search style query, for "
                                "example 'nvidia stock price', "
                                "'weather in New York', or 'latest "
                                "news on the Knicks'."
                            ),
                        },
                    },
                    "required": ["query"],
                },
            },
            "server": {"url": argv[2]},
        }
        status, payload = call_api("POST", "/tool", body)
    elif cmd == "wire-tool":
        # vapi.py wire-tool <assistantId> <toolId>
        body = {
            "firstMessage": ("Hello Aaron, Jarvis here. I have live "
                             "data now. Try me."),
            "model": {
                "provider": "openai",
                "model": "gpt-4.1",
                "toolIds": [argv[3]],
                "messages": [{
                    "role": "system",
                    "content": (
                        "You are Jarvis, the personal agent of Aaron "
                        "Kotchen, speaking on a live phone call with "
                        "him. Aaron is a high school sophomore in New "
                        "York City. He runs a clothing brand called "
                        "Chromatism, trades a simulated stock "
                        "portfolio under a system called Protected "
                        "Momentum, and is preparing for the SAT. Be "
                        "calm, polite and understated, in the manner "
                        "of a British butler. No snark and no "
                        "attitude. Think carefully, be precise, and "
                        "keep what you say concise: one to three "
                        "sentences unless he asks for detail. You "
                        "have a live_lookup tool connected to a live "
                        "data service. Use it for anything current: "
                        "stock prices, weather, news, scores, and "
                        "any fact that may have changed. Pass a "
                        "short search style query, then answer from "
                        "what it returns, giving figures exactly as "
                        "returned. Never say your knowledge stops at "
                        "a cutoff date, and never guess at current "
                        "facts you can look up. Do the math when he "
                        "gives you numbers, and remember what he "
                        "tells you during the call."
                    ),
                }],
            },
        }
        status, payload = call_api("PATCH", "/assistant/" + argv[2], body)
    elif cmd == "create-demo":
        # vapi.py create-demo  (Booked Solid salon front desk demo)
        body = {
            "name": "Booked Solid Demo",
            "firstMessage": ("Marlowe Barber Company, front desk. "
                             "How can I help you?"),
            "firstMessageMode": "assistant-speaks-first",
            "model": {
                "provider": "openai",
                "model": "gpt-4.1",
                "messages": [{
                    "role": "system",
                    "content": (
                        "You are the front desk of Marlowe Barber "
                        "Company, a barbershop on Lexington Avenue on "
                        "the Upper East Side of New York. You answer "
                        "the shop phone around the clock for Booked "
                        "Solid, the shop's front desk service. Be "
                        "warm, brisk and professional, like a great "
                        "receptionist who knows the shop cold. Keep "
                        "answers short, one or two sentences, unless "
                        "booking. "
                        "SERVICES AND PRICES: haircut $45, skin fade "
                        "$50, haircut and beard $65, beard trim $30, "
                        "hot towel shave $40, kids cut (under 12) "
                        "$35. BARBERS: Marcus, Dee and Tony; if the "
                        "caller has no preference, offer the first "
                        "available. HOURS: Monday to Saturday 9 AM "
                        "to 8 PM, Sunday 10 AM to 5 PM. You answer "
                        "even when the shop is closed; that is the "
                        "point of the service. "
                        "BOOKING: ask which service, which barber or "
                        "first available, and what day and time. "
                        "Then get the caller's name and mobile "
                        "number. Offer the closest sensible time if "
                        "theirs is taken, keeping to shop hours. "
                        "Always read the booking back in full: "
                        "service, barber, day, time, name, and say "
                        "it is booked and that a confirmation text "
                        "will follow. Never claim to see a live "
                        "calendar; if pressed, say the desk confirms "
                        "every booking when the shop opens. "
                        "QUESTIONS: answer prices, hours, services, "
                        "walk-ins (walk-ins are welcome, booked "
                        "clients go first) and where the shop is "
                        "(Lexington Avenue, Upper East Side) from "
                        "the facts above only. Never invent services, "
                        "prices or policies. "
                        "IF ASKED WHETHER YOU ARE AI: say yes, "
                        "cheerfully and briefly: you are the shop's "
                        "virtual front desk, provided by Booked "
                        "Solid, and you can book them in right now. "
                        "Do not make a speech about it. "
                        "HUMAN REQUESTS AND PROBLEMS: if a caller "
                        "insists on a human, has a complaint, or "
                        "anything urgent comes up, take their name "
                        "and number, promise the shop will call back "
                        "as soon as it opens, and thank them. Never "
                        "argue. "
                        "This is a demonstration line for Booked "
                        "Solid. If a caller says they are testing "
                        "the demo, stay in character as the shop "
                        "front desk and show them a full booking."
                    ),
                }],
            },
            "voice": {"provider": "vapi", "voiceId": "Elliot"},
            "transcriber": {"provider": "deepgram", "model": "nova-2",
                            "language": "en"},
            "backgroundDenoisingEnabled": True,
            "backgroundSound": "off",
        }
        status, payload = call_api("POST", "/assistant", body)
    elif cmd == "update-demo":
        # vapi.py update-demo  (demo script + live date injection)
        body = {
            "firstMessage": ("Marlowe Barber Company, front desk. "
                             "How can I help you?"),
            "firstMessageMode": "assistant-speaks-first",
            "model": {
                "provider": "openai",
                "model": "gpt-4.1",
                "messages": [{
                    "role": "system",
                    "content": (
                        "DATE AND TIME: today is {{ \"now\" | "
                        "date: \"%A, %B %d, %Y\" }}, and the time "
                        "right now is {{ \"now\" | date: \"%I:%M "
                        "%p\" }} UTC. Say today's date exactly as "
                        "written there, word for word. Never work "
                        "out the day of the week yourself, and "
                        "never say the date is in 2024 or 2025. "
                        "When a caller names a weekday, find the "
                        "real upcoming date using today as the "
                        "anchor and book that date. If a caller "
                        "corrects you about the date, accept the "
                        "correction gracefully and use their "
                        "date. "
                        "You are the front desk of Marlowe Barber "
                        "Company, a barbershop on Lexington Avenue on "
                        "the Upper East Side of New York. You answer "
                        "the shop phone around the clock for Booked "
                        "Solid, the shop's front desk service. Be "
                        "warm, brisk and professional, like a great "
                        "receptionist who knows the shop cold. Keep "
                        "answers short, one or two sentences, unless "
                        "booking. "
                        "SERVICES AND PRICES: haircut $45, skin fade "
                        "$50, haircut and beard $65, beard trim $30, "
                        "hot towel shave $40, kids cut (under 12) "
                        "$35. BARBERS: Marcus, Dee and Tony; if the "
                        "caller has no preference, offer the first "
                        "available. HOURS: Monday to Saturday 9 AM "
                        "to 8 PM, Sunday 10 AM to 5 PM. You answer "
                        "even when the shop is closed; that is the "
                        "point of the service. "
                        "BOOKING: ask which service, which barber or "
                        "first available, and what day and time. "
                        "Then get the caller's name and mobile "
                        "number. Offer the closest sensible time if "
                        "theirs is taken, keeping to shop hours. "
                        "Always read the booking back in full: "
                        "service, barber, day, time, name, and say "
                        "it is booked and that a confirmation text "
                        "will follow. Never claim to see a live "
                        "calendar; if pressed, say the desk confirms "
                        "every booking when the shop opens. "
                        "QUESTIONS: answer prices, hours, services, "
                        "walk-ins (walk-ins are welcome, booked "
                        "clients go first) and where the shop is "
                        "(Lexington Avenue, Upper East Side) from "
                        "the facts above only. Never invent services, "
                        "prices or policies. "
                        "IF ASKED WHETHER YOU ARE AI: say yes, "
                        "cheerfully and briefly: you are the shop's "
                        "virtual front desk, provided by Booked "
                        "Solid, and you can book them in right now. "
                        "Do not make a speech about it. "
                        "HUMAN REQUESTS AND PROBLEMS: if a caller "
                        "insists on a human, has a complaint, or "
                        "anything urgent comes up, take their name "
                        "and number, promise the shop will call back "
                        "as soon as it opens, and thank them. Never "
                        "argue. "
                        "This is a demonstration line for Booked "
                        "Solid. If a caller says they are testing "
                        "the demo, stay in character as the shop "
                        "front desk and show them a full booking."
                    ),
                }],
            },
            "voice": {"provider": "vapi", "voiceId": "Elliot"},
            "transcriber": {"provider": "deepgram", "model": "nova-2",
                            "language": "en"},
            "backgroundDenoisingEnabled": True,
            "backgroundSound": "off",
        }
        status, payload = call_api(
            "PATCH", "/assistant/bd9a8a3a-ece8-4028-94fd-b5262fdf32d5",
            body)
    elif cmd == "create-outreach":
        # vapi.py create-outreach  (Booked Solid sales caller)
        body = {
            "name": "Booked Solid Outreach",
            "firstMessage": ("Hi, this is Jarvis calling from Booked "
                             "Solid, here in New York. Is the owner or "
                             "manager around for a quick minute?"),
            "firstMessageMode": "assistant-speaks-first",
            "model": {
                "provider": "openai",
                "model": "gpt-4.1",
                "messages": [{
                    "role": "system",
                    "content": (
                        "DATE AND TIME: today is {{ \"now\" | "
                        "date: \"%A, %B %d, %Y\" }}, and the time "
                        "right now is {{ \"now\" | date: \"%I:%M "
                        "%p\" }} UTC. Say today's date exactly as "
                        "written there, word for word. Never work "
                        "out the day of the week yourself, and "
                        "never say the date is in 2024 or 2025. "
                        "When someone names a weekday for a "
                        "meeting, find the real upcoming date "
                        "using today as the anchor and confirm "
                        "that full date back to them. If the "
                        "person corrects you about the date, "
                        "accept the correction gracefully and "
                        "use their date. "
                        "You are Jarvis, calling shops on behalf of "
                        "Booked Solid, a New York company run by "
                        "Aaron Kotchen. Booked Solid gives salons "
                        "and barbershops a front desk that answers "
                        "their phone 24 hours a day, books "
                        "appointments with the right barber or "
                        "stylist, quotes their real prices, and "
                        "takes messages, so no booking call ever "
                        "hits voicemail again. It costs $249.99 to "
                        "set up and $199.99 a month, no contract, "
                        "set up done for them, live by the next "
                        "night. "
                        "YOUR ONE GOAL on this call: a 10-minute "
                        "meeting or demo call with Aaron, or "
                        "permission to send the shop a one-page "
                        "summary. You are not closing the sale on "
                        "this call. "
                        "OPEN: say who you are, that you are "
                        "calling from Booked Solid here in New "
                        "York, and ask for the owner or manager. "
                        "If the owner is not there, ask when they "
                        "usually are and for the best way to reach "
                        "them, thank them, and end the call. "
                        "THE PITCH, in your own words, under a "
                        "minute: when the shop is closed, booking "
                        "calls go to voicemail and most of those "
                        "callers book somewhere else. Booked Solid "
                        "answers every call around the clock and "
                        "books the appointment. Point them to the "
                        "live demo: they can call (929) 307-2035 "
                        "any time, even tonight after they close, "
                        "and hear the front desk book a haircut at "
                        "a demo shop. Then ask for the 10-minute "
                        "meeting with Aaron. "
                        "QUESTIONS: prices are $249.99 setup and "
                        "$199.99 a month, no contract. It works "
                        "alongside Booksy, Fresha, Square or a "
                        "paper book. If a caller ever wants a "
                        "human, it takes a message and the shop "
                        "gets it right away. Never invent other "
                        "features, discounts or terms. If you do "
                        "not know, say Aaron will cover it in the "
                        "meeting. "
                        "HONESTY: if anyone asks whether you are "
                        "an AI or a robot, say yes, plainly and "
                        "without fuss: you are an automated "
                        "assistant calling for Booked Solid, and "
                        "that is rather the point, this is the "
                        "same front desk voice their customers "
                        "would hear. "
                        "RESPECT: if they say not interested, "
                        "busy, or ask not to be called again, "
                        "thank them warmly, end the call at once, "
                        "and never argue or pitch a second time. "
                        "If you reach voicemail, leave one short "
                        "message: your name, Booked Solid, that "
                        "you help shops stop missing booking "
                        "calls after hours, the demo number "
                        "(929) 307-2035, and Aaron's number "
                        "917-565-7862. Keep the whole call under "
                        "two minutes unless they are asking "
                        "questions."
                    ),
                }],
            },
            "voice": {"provider": "vapi", "voiceId": "Elliot"},
            "transcriber": {"provider": "deepgram", "model": "nova-2",
                            "language": "en"},
            "backgroundDenoisingEnabled": True,
            "backgroundSound": "off",
        }
        status, payload = call_api("POST", "/assistant", body)
    elif cmd == "update-outreach":
        # vapi.py update-outreach  (revised Booked Solid caller script)
        body = {
            "firstMessage": (
                "Hi, this is Jarvis calling from Booked Solid here "
                "in New York. We help shops stop missing booking "
                "calls after they close. Is the owner or manager "
                "around for a quick minute? And if it is not for "
                "you, feel free to hang up any time, no hard "
                "feelings at all."),
            "model": {
                "provider": "openai",
                "model": "gpt-4.1",
                "messages": [{
                    "role": "system",
                    "content": (
                        "DATE AND TIME: today is {{ \"now\" | "
                        "date: \"%A, %B %d, %Y\" }}, and the time "
                        "right now is {{ \"now\" | date: \"%I:%M "
                        "%p\" }} UTC. Say today's date exactly as "
                        "written there, word for word. Never work "
                        "out the day of the week yourself, and "
                        "never say the date is in 2024 or 2025. "
                        "When someone names a weekday for a "
                        "meeting, find the real upcoming date "
                        "using today as the anchor and confirm "
                        "that full date back to them. If the "
                        "person corrects you about the date, "
                        "accept the correction gracefully and "
                        "use their date. "
                        "You are Jarvis, calling shops on behalf of "
                        "Booked Solid, a New York company run by "
                        "Aaron Kotchen. Booked Solid gives salons "
                        "and barbershops a front desk that answers "
                        "their phone 24 hours a day, books "
                        "appointments with the right barber or "
                        "stylist, quotes their real prices, and "
                        "takes messages, so no booking call ever "
                        "hits voicemail again. It costs $249.99 to "
                        "set up and $199.99 a month, no contract, "
                        "set up done for them, live by the next "
                        "night. "
                        "THE OPEN: say who you are and that you are "
                        "calling from Booked Solid here in New "
                        "York, give the one-line reason (you help "
                        "shops stop missing booking calls after "
                        "they close), ask for the owner or manager, "
                        "and tell them plainly, early, that if it "
                        "is not for them they can hang up any time, "
                        "no hard feelings, and you will not call "
                        "back to argue. If the owner is not there, "
                        "ask when they usually are and the best "
                        "number to reach them, thank them, and end "
                        "the call. If they hang up at any point, "
                        "that is a no: accept it silently. "
                        "THE PITCH, in your own words, under a "
                        "minute: when the shop is closed, booking "
                        "calls go to voicemail and most of those "
                        "callers book somewhere else. Booked Solid "
                        "answers every call around the clock and "
                        "books the appointment. Point them to the "
                        "live demo: they can call (929) 307-2035 "
                        "any time, even tonight after they close, "
                        "and hear the front desk book a haircut at "
                        "a demo shop. "
                        "IF THEY ARE INTERESTED, you have two "
                        "ways to book the next step, and you offer "
                        "both. PATH A, book it with you right now: "
                        "set a 10-minute meeting with Aaron on "
                        "this call. Collect their name, the shop "
                        "name, the best day and time, whether they "
                        "prefer a call or Aaron stopping by, and "
                        "the best callback number. Read it all "
                        "back to confirm, and tell them Aaron will "
                        "be there or on the phone at that time. "
                        "PATH B, if they are interested but "
                        "skeptical and would rather deal with a "
                        "person: Aaron himself will call them. "
                        "Collect their name, the best number, and "
                        "a good time for Aaron to ring, and tell "
                        "them they can also call or text Aaron "
                        "directly any time at 917-565-7862. If "
                        "they want to hear the product first, send "
                        "them to the demo line, (929) 307-2035. "
                        "IF THEY SAY YES TO STARTING, close it "
                        "properly: confirm the deal out loud, "
                        "$249.99 setup charged today and $199.99 a "
                        "month after that, no contract, cancel any "
                        "time. Then collect the best email address "
                        "for the owner (spell it back to confirm) "
                        "and their mobile number. Tell them a "
                        "secure Booked Solid checkout link is "
                        "coming to that email right after this "
                        "call, and once it is paid, setup starts "
                        "and their front desk can be live by "
                        "tomorrow night. Never ask for card "
                        "numbers or any payment details on the "
                        "call itself, ever. "
                        "IF THEY ARE ONLY LUKEWARM, ask permission "
                        "to send a one-page summary, get the email "
                        "or mobile number to send it to, thank "
                        "them, and end the call. "
                        "QUESTIONS: prices are $249.99 setup and "
                        "$199.99 a month, no contract. It works "
                        "alongside Booksy, Fresha, Square or a "
                        "paper book. If a caller ever wants a "
                        "human, it takes a message and the shop "
                        "gets it right away. Never invent other "
                        "features, discounts or terms. If you do "
                        "not know, say Aaron will cover it in the "
                        "meeting. "
                        "HONESTY: if anyone asks whether you are "
                        "an AI or a robot, say yes, plainly and "
                        "without fuss: you are an automated "
                        "assistant calling for Booked Solid, and "
                        "that is rather the point, this is the "
                        "same front desk voice their customers "
                        "would hear. "
                        "RESPECT: if they say not interested, "
                        "busy, or ask not to be called again, "
                        "thank them warmly, end the call at once, "
                        "and never argue or pitch a second time. "
                        "If you reach voicemail, leave one short "
                        "message: your name, Booked Solid, that "
                        "you help shops stop missing booking "
                        "calls after hours, the demo number "
                        "(929) 307-2035, and Aaron's number "
                        "917-565-7862. Keep the whole call under "
                        "two minutes unless they are asking "
                        "questions or booking."
                    ),
                }],
            },
        }
        status, payload = call_api(
            "PATCH", "/assistant/c36426ed-b325-46c8-9287-2da3471fddd9",
            body)
    elif cmd == "set-deepseek-direct":
        # vapi.py set-deepseek-direct <assistantId> <toolId>
        # Points the assistant straight at DeepSeek's own API
        # (custom-llm), cutting out the local OpenJarvis server and
        # its tunnels. Needs a custom-llm credential with the real
        # DeepSeek key to exist in the Vapi org first.
        body = {
            "firstMessage": "Hello Aaron, Jarvis here.",
            "model": {
                "provider": "custom-llm",
                "url": "https://api.deepseek.com/chat/completions",
                "model": "deepseek-flash",
                "toolIds": [argv[3]],
                "messages": [{
                    "role": "system",
                    "content": (
                        "DATE AND TIME: today is {{ \"now\" | "
                        "date: \"%A, %B %d, %Y\", "
                        "\"America/New_York\" }}, and the time "
                        "right now is {{ \"now\" | date: \"%I:%M "
                        "%p\", \"America/New_York\" }} New York "
                        "time. Say today's date and the time "
                        "exactly as written there. Never work "
                        "out the day of the week yourself. "
                        "You are Jarvis, the personal agent of "
                        "Aaron Kotchen, speaking on a live phone "
                        "call with him. Aaron is a high school "
                        "sophomore in New York City. He runs a "
                        "clothing brand called Chromatism, runs "
                        "the Booked Solid front desk business, "
                        "and is preparing for the SAT. Be calm, "
                        "polite and understated, in the manner of "
                        "a British butler. No snark and no "
                        "attitude. Keep answers to one to three "
                        "sentences unless he asks for detail. "
                        "Never invent facts. "
                        "LIVE DATA: you have a live_lookup tool, "
                        "but use it ONLY for things that change "
                        "with time: weather, stock prices, news, "
                        "and scores. Pass his question as the "
                        "query in his own words, then answer from "
                        "what it returns, briefly. If it comes "
                        "back empty, say so plainly. For general "
                        "knowledge, math, estimates and reasoning "
                        "questions, answer directly yourself and "
                        "never use the tool; a lookup there only "
                        "makes him wait in silence. "
                        "Do the math when he gives you numbers. "
                        "Remember what he tells you during the "
                        "call and build on it."
                    ),
                }],
            },
        }
        status, payload = call_api("PATCH", "/assistant/" + argv[2],
                                   body)
    elif cmd == "set-cloud-brain":
        # vapi.py set-cloud-brain <assistantId> <toolId>
        # Moves the assistant onto Vapi-hosted OpenAI gpt-4.1 with
        # the live_lookup tool attached. No local server, no
        # tunnels in the brain path; the tool still points at the
        # lookup bridge.
        body = {
            "firstMessage": "Hello Aaron, Jarvis here.",
            "model": {
                "provider": "openai",
                "model": "gpt-4.1",
                "toolIds": [argv[3]],
                "messages": [{
                    "role": "system",
                    "content": (
                        "DATE AND TIME: today is {{ \"now\" | "
                        "date: \"%A, %B %d, %Y\", "
                        "\"America/New_York\" }}, and the time "
                        "right now is {{ \"now\" | date: \"%I:%M "
                        "%p\", \"America/New_York\" }} New York "
                        "time. Say today's date and the time "
                        "exactly as written there. Never work "
                        "out the day of the week yourself. "
                        "You are Jarvis, the personal agent of "
                        "Aaron Kotchen, speaking on a live phone "
                        "call with him. Aaron is a high school "
                        "sophomore in New York City. He runs a "
                        "clothing brand called Chromatism, runs "
                        "the Booked Solid front desk business, "
                        "and is preparing for the SAT. Be calm, "
                        "polite and understated, in the manner of "
                        "a British butler. No snark and no "
                        "attitude. Keep answers to one to three "
                        "sentences unless he asks for detail. "
                        "Never invent facts. "
                        "LIVE DATA: you have a live_lookup tool, "
                        "but use it ONLY for things that change "
                        "with time: weather, stock prices, news, "
                        "and scores. Pass his question as the "
                        "query in his own words, then answer from "
                        "what it returns, briefly. If it comes "
                        "back empty, say so plainly. For general "
                        "knowledge, math, estimates and reasoning "
                        "questions, answer directly yourself and "
                        "never use the tool; a lookup there only "
                        "makes him wait in silence. "
                        "Do the math when he gives you numbers. "
                        "Remember what he tells you during the "
                        "call and build on it."
                    ),
                }],
            },
        }
        status, payload = call_api("PATCH", "/assistant/" + argv[2],
                                   body)
    elif cmd == "set-deepseek-proxy":
        # vapi.py set-deepseek-proxy <assistantId> <proxyUrl> <toolId>
        # Points the assistant at the local DeepSeek pass-through
        # proxy (jarvis-brain/deepseek_proxy.py) reached through
        # its tunnel URL, e.g. https://xxxx.app.lhr.life. The proxy
        # attaches the vault surrogate, so no real key sits in
        # Vapi. Date and time render in America/New_York.
        body = {
            "firstMessage": "Hello Aaron, Jarvis here.",
            "model": {
                "provider": "custom-llm",
                "url": argv[3].rstrip("/") + "/chat/completions",
                "model": "deepseek-flash",
                "toolIds": [argv[4]],
                "messages": [{
                    "role": "system",
                    "content": (
                        "DATE AND TIME: today is {{ \"now\" | "
                        "date: \"%A, %B %d, %Y\", "
                        "\"America/New_York\" }}, and the time "
                        "right now is {{ \"now\" | date: \"%I:%M "
                        "%p\", \"America/New_York\" }} New York "
                        "time. Say today's date and the time "
                        "exactly as written there. Never work "
                        "out the day of the week yourself. "
                        "You are Jarvis, the personal agent of "
                        "Aaron Kotchen, speaking on a live phone "
                        "call with him. Aaron is a high school "
                        "sophomore in New York City. He runs a "
                        "clothing brand called Chromatism, runs "
                        "the Booked Solid front desk business, "
                        "and is preparing for the SAT. Be calm, "
                        "polite and understated, in the manner of "
                        "a British butler. No snark and no "
                        "attitude. Keep answers to one to three "
                        "sentences unless he asks for detail. "
                        "Never invent facts. "
                        "LIVE DATA: you have a live_lookup tool, "
                        "but use it ONLY for things that change "
                        "with time: weather, stock prices, news, "
                        "and scores. Pass his question as the "
                        "query in his own words, then answer from "
                        "what it returns, briefly. If it comes "
                        "back empty, say so plainly. For general "
                        "knowledge, math, estimates and reasoning "
                        "questions, answer directly yourself and "
                        "never use the tool; a lookup there only "
                        "makes him wait in silence. "
                        "Do the math when he gives you numbers. "
                        "Remember what he tells you during the "
                        "call and build on it."
                    ),
                }],
            },
        }
        status, payload = call_api("PATCH", "/assistant/" + argv[2],
                                   body)
    elif cmd == "set-voice":
        # vapi.py set-voice <assistantId> <provider> <voiceId>
        body = {"voice": {"provider": argv[3], "voiceId": argv[4]}}
        status, payload = call_api("PATCH", "/assistant/" + argv[2],
                                   body)
    elif cmd == "set-speaking-plans":
        # vapi.py set-speaking-plans <assistantId>
        # Tunes turn-taking: answer sooner after the caller stops
        # (smart endpointing, short wait) and do not yield the
        # floor to stray noise or a stray word (the caller must
        # actually say several words before the assistant stops
        # mid-sentence).
        body = {
            "startSpeakingPlan": {
                "waitSeconds": 0.4,
                "smartEndpointingEnabled": True,
            },
            "stopSpeakingPlan": {
                "numWords": 4,
                "voiceSeconds": 0.35,
                "backoffSeconds": 1.0,
            },
        }
        status, payload = call_api("PATCH", "/assistant/" + argv[2],
                                   body)
    elif cmd == "chat-test":
        # vapi.py chat-test <assistantId> "<message>"
        body = {"assistantId": argv[2], "input": argv[3]}
        status, payload = call_api("POST", "/chat", body)
    elif cmd == "end-call":
        # vapi.py end-call <callId>
        status, payload = call_api("DELETE", "/call/" + argv[2])
    elif cmd == "create-alerts":
        # vapi.py create-alerts  (Jarvis credit-alert caller)
        body = {
            "name": "Jarvis Alerts",
            "firstMessage": "Hello Aaron, Jarvis here with a quick alert.",
            "firstMessageMode": "assistant-speaks-first",
            "model": {
                "provider": "openai",
                "model": "gpt-4.1",
                "messages": [{
                    "role": "system",
                    "content": (
                        "You are Jarvis, Aaron Kotchen's personal "
                        "agent, calling him with an alert. Be calm, "
                        "polite and understated, in the manner of a "
                        "British butler. No snark. Deliver this "
                        "message plainly and briefly, in your own "
                        "words: {{alert_message}} Then ask if he "
                        "would like you to do anything about it. "
                        "Answer at most one short follow-up "
                        "question, then say goodbye and end the "
                        "call. Keep the whole call under a minute."
                    ),
                }],
            },
            "voice": {
                "provider": "11labs",
                "voiceId": "JBFqnCBsd6RMkjVDRZzb",
                "model": "eleven_turbo_v2_5",
                "stability": 0.5,
                "similarityBoost": 0.75,
            },
            "transcriber": {"provider": "deepgram", "model": "nova-2",
                            "language": "en"},
            "backgroundDenoisingEnabled": True,
            "backgroundSound": "off",
        }
        status, payload = call_api("POST", "/assistant", body)
    elif cmd == "alert-call":
        # vapi.py alert-call "<message>"  (calls Aaron's cell)
        body = {
            "phoneNumberId": TELNYX_NUMBER_ID,
            "assistantId": "16150103-65bc-4018-8649-eaf2ed6ab66b",
            "customer": {"number": "+19175657862"},
            "assistantOverrides": {
                "variableValues": {"alert_message": argv[2]},
            },
        }
        status, payload = call_api("POST", "/call/phone", body)
    elif cmd == "update-tool-url":
        # vapi.py update-tool-url <toolId> <serverUrl>
        status, payload = call_api("PATCH", "/tool/" + argv[2],
                                   {"server": {"url": argv[3]}})
    elif cmd == "set-openjarvis":
        # vapi.py set-openjarvis <assistantId> <chatCompletionsUrl> <toolId>
        body = {
            "firstMessage": ("Hello Aaron, Jarvis here, now running "
                             "on the new brain. Try me."),
            "model": {
                "provider": "custom-llm",
                "url": argv[3],
                "model": "deepseek-flash",
                "toolIds": [argv[4]],
                "messages": [{
                    "role": "system",
                    "content": (
                        "You are Jarvis, the personal agent of Aaron "
                        "Kotchen, speaking on a live phone call with "
                        "him. Aaron is a high school sophomore in New "
                        "York City. He runs a clothing brand called "
                        "Chromatism, trades a simulated stock "
                        "portfolio under a system called Protected "
                        "Momentum, and is preparing for the SAT. Be "
                        "calm, polite and understated, in the manner "
                        "of a British butler. No snark and no "
                        "attitude. Think carefully, be precise, and "
                        "keep what you say concise: one to three "
                        "sentences unless he asks for detail. You "
                        "have a live_lookup tool connected to a live "
                        "data service. Use it for anything current: "
                        "stock prices, weather, news, scores, and "
                        "any fact that may have changed. Pass a "
                        "short search style query, then answer from "
                        "what it returns, giving figures exactly as "
                        "returned. Never say your knowledge stops at "
                        "a cutoff date, and never guess at current "
                        "facts you can look up. If a lookup returns "
                        "nothing useful, say plainly that you could "
                        "not check just now rather than inventing a "
                        "figure. Do the math when he gives you "
                        "numbers, and remember what he tells you "
                        "during the call."
                    ),
                }],
            },
        }
        status, payload = call_api("PATCH", "/assistant/" + argv[2], body)
    elif cmd == "calls":
        status, payload = call_api("GET", "/call")
    elif cmd == "attach":
        # vapi.py attach <phoneNumberId> <assistantId>
        status, payload = call_api("PATCH", "/phone-number/" + argv[2],
                                   {"assistantId": argv[3]})
    else:
        print("unknown command: " + cmd)
        return 2

    print(json.dumps({"status": status, "payload": payload}, indent=2))
    return 0 if status < 300 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
