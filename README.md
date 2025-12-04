# PMS Calendar Splitter

Breaks a single PMS iCal feed into per-unit `.ics` files, preserving in-progress reservations even if the source feed drops them.

## Setup
- Python 3.9+ recommended.
- Install runtime deps: `pip install -r requirements.txt`
- For development/testing: `pip install -r requirements-dev.txt`

## Running locally
```bash
FLASK_APP=format-calendars.py flask run --host=0.0.0.0 --port=8080
```
Open `http://localhost:8080` to see per-property calendar links, e.g. `http://localhost:8080/calendar/room-one.ics`.

## Behavior rules
- If a booking disappears from the source feed **before it starts**, treat it as cancelled and omit it from generated `.ics`.
- If a booking disappears **after it has started**, keep it from cache so active stays remain visible to downstream consumers (e.g., cleaning schedules).
- Active reservations are cached in `active_reservations_cache.json` to support the above behavior.

## Testing
Run targeted tests:
```bash
python -m pytest tests/test_format_calendars.py
```
Tests use a temporary cache file and mocked HTTP feed to validate the cancellation/retention rules.
