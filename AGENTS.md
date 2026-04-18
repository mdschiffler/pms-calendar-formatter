# PMS Calendar Splitter Agent Notes

## Purpose
This service converts one Freetobook property iCal feed into one downstream iCal feed per unit. The current source feed is `SOURCE_ICAL_URL` in `format-calendars.py`, and the public Flask routes are:

- `/` lists copyable per-unit calendar links.
- `/calendar/<property-slug>.ics` exports one unit calendar.
- `/refresh` deletes the runtime reservation cache so it rebuilds on the next request.

## Calendar Stream Creation
`parse_and_group_events()` fetches the source feed, parses each `VEVENT`, and keeps only reservation-like summaries shaped as `Apartment ...:<booking-code>` or `Room ...:<booking-code>`. The grouping key is always the full unit name before the colon, such as `Apartment AYA` or `Apartment MAO - Five Bedroom`.

Do not dedupe reservations by booker, booking code, date span, or overlapping dates. A booking that appears in several units with the same booking code and dates must produce one event in each unit's output calendar.

All-day source dates are converted to Puerto Rico local stay times: `DTSTART` at 16:00 and `DTEND` at 11:00. Datetime values without a timezone are localized to `America/Puerto_Rico`. Past events whose end is before the local start of today are ignored.

## Cache Semantics
The runtime cache file is `active_reservations_cache.json`. It is intentionally ignored by git.

The cache exists to protect active stays when the source feed drops them:

- If a cached booking is still present in the source feed, the source event wins and the cached version metadata is merged.
- If a cached booking disappears before it starts, it is treated as cancelled and omitted.
- If a cached booking disappears after it starts, it is restored from cache until it ends.
- If the source feed cannot be fetched or parsed, the app serves non-ended cached events and does not rewrite the cache.

## Export Semantics
Calendar slugs come from `slugify()`, which lowercases a unit name and replaces non-alphanumeric runs with hyphens. Known units in `KNOWN_PROPERTIES` always get calendars, even when empty.

Exported event UIDs combine the source UID left side with a unit code, for example `74699663+AYA@staypr`. This keeps same-booker, same-date multi-unit bookings distinct for downstream consumers. Each event also includes `X-ORIGINAL-UID` and `X-UNIT-CODE` for traceability.

Per-unit exports include downstream-friendly fields: `STATUS:CONFIRMED`, `TRANSP:OPAQUE`, `LAST-MODIFIED` from the source or cached `DTSTAMP`, and `SEQUENCE` from the cached version.

## Development
Install dependencies with:

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

Run the app locally with:

```bash
FLASK_APP=format-calendars.py flask run --host=0.0.0.0 --port=8080
```

Run the focused tests with:

```bash
python -m pytest tests/test_format_calendars.py
```
