# Booked Solid call kit (internal ops file, not a deliverable)

Built Mon 2026-11-16 night. Plan set by Aaron: he upgrades Telnyx to Paid on Tue 2026-11-17, then Jarvis works this list by phone during shop hours (call between 10 AM and 5 PM, Tue to Sat is best; never before a shop opens, never near closing rush if avoidable).

## The list (all Upper East Side, all verified from place records Mon night)

1. Hair Bar NYC, 843 Lexington Ave 2FL, +12122192211. Hours 10 AM to 7 PM (Sun 10 to 5). Appointment only, no walk-ins. Angle: premium keratin and color tickets, every missed evening call is real money.
2. Beyond The Beard, 170 E 61st St, +18624320121. Hours Tue to Fri 11 to 8, Mon 2 to 8, Sat 8 to 4, closed Sun. Founder-run, one master barber. Angle: when she is cutting, nobody answers, ever.
3. Debonair, 127 E 60th St, +15165571508. Hours Mon to Thu 10 to 8, Fri 10 to 7, Sat 9 to 5, Sun 10 to 3. Appointments required, premium men's grooming. Angle: appointment-only means the phone IS the front door.
4. Willy's Hair Styling, 209 E 81st St, +12126283198. Hours Mon to Sat 10 to 6. Twenty-plus years in business. Angle: closes at 6, the earliest on the list; decades of regulars calling after hours.
5. Sharp Styles Barbershop, 172 E 85th St, +19172612031. Hours Mon to Fri 8:30 to 6:30, Sat 8:30 to 5:30. Angle: early close, walk-in trade, missed calls go straight to the next shop.
6. Honeybliss Salon, 1216 Lexington Ave, +12122881676. Hours Mon to Fri 10 to 8, Sat 10 to 7, closed Sun. Angle: color and balayage tickets are $200-plus; one saved booking pays for months.

Spares: Level Two Barbershop, 1388 2nd Ave, +12127347777 (appointment only, closes 7:30). Fabio's Hair & Color Studio, 1737 2nd Ave, +12124102005 (cuts $75 to $120).

## How the calls run

- Caller: the Vapi assistant "Booked Solid Outreach", calling from the Telnyx number +1 (929) 307-0119 once the account is Paid. Requires the Paid upgrade first: trial outbound only reaches Aaron's verified cell.
- One call per shop per attempt. Log every outcome here after each call: reached owner / reached staff / voicemail / no answer / not interested / callback time / meeting booked.
- If a shop says do not call again, mark it DO NOT CALL and never dial it again.
- The win is a 10-minute meeting or demo call with Aaron, or permission to send the one-pager. The call itself is not the sale.
- Script (revised per Aaron Mon 23:17, live on the assistant via update-outreach): the open states the out early and plainly: if it is not for them, hang up any time, no hard feelings, no call back to argue. A hang-up is a no. If interested, two booking paths: PATH A, Jarvis books the 10-minute meeting with Aaron on the call (name, shop, day and time, call or in-person, callback number, read back to confirm). PATH B, for the skeptical but interested: Aaron calls them personally at a time they pick, or they can call or text Aaron directly at 917-565-7862, plus the demo line (929) 307-2035 to hear it first. Lukewarm gets the one-pager permission ask.

## Pay on the call (LIVE as of Mon 23:47)

Aaron asked Mon 23:20 whether Jarvis can take payment when a shop says yes. Design: never card numbers by voice. The yes triggers a Stripe checkout link sent to the email Jarvis captured; the shop taps and pays. Stripe connected Mon night (live account "Booked Solid", acct_1UcdwuApLOXvzPzp). Product "Booked Solid Front Desk" prod_Vdw8I97WUCGm9y; setup price price_1UceGOApLOXvzPzpqSoZ2UQn ($249.99 one-time); monthly price price_1UceGZApLOXvzPzptTFfinuT ($199.99/mo recurring). Payment link plink_1UceGeApLOXvzPzpecpoGcTz, active: https://buy.stripe.com/9B6cN492O8PQ3dm4uiejK00 (charges the setup once and starts the monthly subscription). The outreach script now has the signup path (confirm prices, capture owner email spelled back plus mobile, promise the link by email right after the call), and the Tue call run emails the link via Muse Mail to every yes. No tax is added on top of the prices in this setup; revisit before the first real charge if Aaron wants NY tax handled in Stripe.

## Outcomes log

- Mon 2026-11-16 23:50: Aaron updated Vapi billing, so all three meters are covered for the run (Telnyx Paid, Vapi updated, DeepSeek at $12). Observed Vapi costs Mon night: normal calls $0.10 to $0.40; the bot-to-bot test call ran long at $0.94.
- Mon 2026-11-16 23:12: Aaron upgraded Telnyx to Paid a night early. Pipe verified the same night: a test call from the outreach assistant to the demo line (a non-verified number the trial would have refused) connected. Aaron chose live calls over voicemail drops; the six calls are scheduled for Tue 2026-11-17 late morning via the booked-solid-telnyx-upgrade-reminder job.
