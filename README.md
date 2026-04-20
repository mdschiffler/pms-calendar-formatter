# PMS Calendar Splitter

PMS Calendar Splitter turns one combined property iCal feed into separate `.ics` calendar feeds for each unit.

Generic use case: a booking/PMS system exports one property-level iCal feed, but another calendar consumer needs one feed per room, apartment, cabin, or unit.

This implementation was built for a **Freetobook source iCal feed** going into **Hospitable destination calendars**. It should also work for other tools that can subscribe to iCal URLs, as long as the source event summaries identify the unit and reservation code in a predictable format.

## What It Does

- Fetches one upstream iCal feed.
- Parses reservation events from summaries like `Apartment AYA:WTB19BCD37` or `Room ONE:CTB123456`.
- Groups reservations by unit name.
- Publishes one `.ics` URL per unit.
- Keeps in-progress reservations from cache if the upstream feed drops them after check-in.
- Treats future reservations that disappear from the source feed as cancelled.
- Adds downstream-friendly iCal fields for consumers such as Hospitable.
- Suffixes duplicate reservation codes in source-feed order so downstream systems do not dedupe separate unit reservations with the same code.

Example duplicate-code handling:

```text
Source events:
Apartment MAO - Five Bedroom:WTB19BCD37
Apartment AYA:WTB19BCD37
Apartment RYO:WTB19BCD37
Apartment UMI:WTB19BCD37

Exported reservation codes:
Apartment MAO - Five Bedroom -> WTB19BCD37-1
Apartment AYA                -> WTB19BCD37-2
Apartment RYO                -> WTB19BCD37-3
Apartment UMI                -> WTB19BCD37-4
```

The original reservation code is still preserved in each event as `X-ORIGINAL-RESERVATION-CODE`.

## How It Works

The app is a small Flask service in `format-calendars.py`.

Main flow:

1. `parse_and_group_events()` fetches the source iCal URL.
2. Each `VEVENT` is inspected.
3. Non-reservation events, such as `Last update ...`, are ignored.
4. All-day source dates are converted to local stay times:
   - check-in: `16:00`
   - check-out: `11:00`
5. Past-ended reservations are ignored.
6. Valid reservations are collected in source-feed order.
7. Duplicate reservation codes are suffixed only when the same code appears more than once.
8. Events are grouped by full unit name.
9. The per-unit route exports an iCal feed for that unit.

The root page lists all available unit calendar URLs:

```text
/
```

Each unit calendar is served at:

```text
/calendar/<property-slug>.ics
```

Example:

```text
/calendar/apartment-aya.ics
/calendar/room-one.ics
```

## Current Implementation

This repo currently targets:

- Source program: **Freetobook**
- Source type: one property-level iCal feed
- Destination program: **Hospitable**
- Destination type: separate iCal import URL per unit
- Deployment target: **Fly.io**
- Timezone: `America/Puerto_Rico`

Known units are configured in `KNOWN_PROPERTIES`:

```text
Room ONE
Room TWO
Room THREE
Room FOUR
Room FIVE
Apartment AYA
Apartment RYO
Apartment UMI
Apartment MAO - Five Bedroom
```

If you make this repo public or fork it for your own property, replace the hard-coded `SOURCE_ICAL_URL` in `format-calendars.py` with your own feed URL. Do not publish a private iCal URL unless you are comfortable with anyone being able to read that calendar feed.

## Requirements

- Python 3.9 or newer
- A source iCal URL from your PMS or booking system
- A destination system that can subscribe to public `.ics` URLs
- Optional for production: a Fly.io account and the Fly CLI

Runtime dependencies are listed in `requirements.txt`.

Development/test dependencies are listed in `requirements-dev.txt`.

## Step 1: Clone And Install

```bash
git clone <your-repo-url>
cd <your-repo-directory>
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

## Step 2: Configure The Source Feed

Open `format-calendars.py` and set:

```python
SOURCE_ICAL_URL = "https://example.com/path/to/source.ics"
TIMEZONE = "America/Puerto_Rico"
```

For this implementation, `SOURCE_ICAL_URL` points to a Freetobook property feed.

If your source system is not Freetobook, make sure its event summaries follow this shape:

```text
<Unit Type> <Unit Name>:<Reservation Code>
```

Examples:

```text
Apartment AYA:WTB19BCD37
Room ONE:CTB123456
```

## Step 3: Configure Units

Edit `KNOWN_PROPERTIES` so it contains every unit that should always have a calendar URL, even when empty.

Edit `SECTION_ORDER` to control how units appear on the root listing page.

Edit `DISPLAY_NAME_OVERRIDES` if you want friendlier labels on the root page.

## Step 4: Run Locally

For local development, the Flask dev server is fine:

```bash
FLASK_APP=format-calendars.py flask run --host=0.0.0.0 --port=8080
```

For a production-like run locally, use gunicorn via the `wsgi.py` entrypoint:

```bash
gunicorn --bind 0.0.0.0:8080 wsgi:app
```

Open:

```text
http://localhost:8080
```

Then test a unit feed:

```text
http://localhost:8080/calendar/apartment-aya.ics
```

You can also use `curl`:

```bash
curl -L http://localhost:8080/calendar/apartment-aya.ics
```

## Step 5: Run Tests

```bash
python -m pytest tests/test_format_calendars.py
```

The tests use mocked iCal feeds and temporary cache files. They cover:

- grouping reservations by unit
- always generating known-property calendars
- retaining started reservations from cache
- treating removed future reservations as cancelled
- duplicate reservation-code suffixing for Hospitable
- source fetch failure behavior

## Step 6: Deploy To Fly.io

Install and log in to the Fly CLI:

```bash
fly auth login
```

Create or update `fly.toml`.

This repo currently has:

```toml
app = "pms-calendar"
primary_region = "mia"
```

If you are deploying your own copy, create a new Fly app name:

```bash
fly launch
```

If you already have a Fly app, deploy with:

```bash
fly deploy --app <your-fly-app-name>
```

For this implementation:

```bash
fly deploy --app pms-calendar
```

Check deployment status:

```bash
fly status --app <your-fly-app-name>
fly logs --app <your-fly-app-name>
```

## Step 7: Add Destination Calendars

After deployment, open the app URL in a browser:

```text
https://<your-fly-app-name>.fly.dev
```

Copy each unit-specific `.ics` URL into your destination calendar system.

For Hospitable, use the external calendar/iCal import flow for each unit/listing and paste the matching generated URL.

Examples:

```text
https://<your-fly-app-name>.fly.dev/calendar/apartment-aya.ics
https://<your-fly-app-name>.fly.dev/calendar/apartment-ryo.ics
https://<your-fly-app-name>.fly.dev/calendar/apartment-umi.ics
https://<your-fly-app-name>.fly.dev/calendar/apartment-mao-five-bedroom.ics
```

## Verify Production

Check that a known reservation appears in a specific feed:

```bash
curl -L https://<your-fly-app-name>.fly.dev/calendar/apartment-aya.ics | grep WTB19BCD37
```

Check downstream-friendly fields:

```bash
curl -L https://<your-fly-app-name>.fly.dev/calendar/apartment-aya.ics | grep -E "STATUS|TRANSP|LAST-MODIFIED|SEQUENCE|X-RESERVATION"
```

For duplicate reservation codes, verify the suffixes are present:

```bash
curl -L https://<your-fly-app-name>.fly.dev/calendar/apartment-aya.ics | grep "WTB19BCD37-"
```

## Cache Behavior

The app writes runtime state to:

```text
active_reservations_cache.json
```

This file is ignored by git.

Rules:

- If a booking disappears before it starts, it is treated as cancelled.
- If a booking disappears after it starts, it remains visible from cache until checkout.
- If the source feed cannot be fetched or parsed, the app serves non-ended cached events and does not rewrite the cache.

To clear the cache in production or locally:

```text
/refresh
```

Example:

```text
https://<your-fly-app-name>.fly.dev/refresh
```

## Important Notes For Public Repos

- Replace private source iCal URLs before publishing.
- Review `KNOWN_PROPERTIES` for private unit names.
- The app exposes generated `.ics` URLs publicly by default.
- Most calendar consumers cache iCal aggressively; changes may not appear instantly downstream.
- Hospitable may dedupe events using reservation-code-like text, so duplicate source reservation codes are intentionally suffixed.

## Troubleshooting

If a reservation is missing downstream:

1. Fetch the generated unit `.ics` URL directly with `curl`.
2. Confirm the event exists in the generated feed.
3. Confirm the event has a unique `UID`.
4. Confirm duplicate booking codes have suffixes such as `-1`, `-2`, `-3`.
5. Wait for the destination calendar system to refresh its iCal subscription.
6. If the event is missing from the generated feed, run the tests and inspect the source iCal summary format.

If Fly deploy fails:

1. Run tests locally.
2. Confirm `requirements.txt` installs cleanly.
3. Confirm `fly.toml` has the right app name.
4. Run `fly logs --app <your-fly-app-name>` for the runtime error.

## License

MIT. See [LICENSE](LICENSE).
