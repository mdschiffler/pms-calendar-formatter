import requests
from flask import Flask, Response, request
from icalendar import Calendar as ICal, Event as IEvent, Timezone as ITimezone, TimezoneStandard as ITimezoneStandard
from datetime import datetime, time, timedelta
from collections import defaultdict
import pytz
import re
import arrow
import logging

import json, os
CACHE_FILE = "active_reservations_cache.json"

USERNAME = "user"
PASSWORD = "password"

SOURCE_ICAL_URL = 'https://www.freetobook.com/ical/property-feed/5eac437529a87f16b68149bb183f19ef.ics'
TIMEZONE = 'America/Puerto_Rico'

# Ensure calendars are always available for these units, even when no reservations exist.
KNOWN_PROPERTIES = [
    "Room ONE",
    "Room TWO",
    "Room THREE",
    "Room FOUR",
    "Room FIVE",
    "Apartment AYA",
    "Apartment RYO",
    "Apartment UMI",
    "Apartment MAO - Five Bedroom",
]

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

slugify_cache = {}

def slugify(s: str) -> str:
    """URL-safe, case-insensitive slug for property names."""
    if s in slugify_cache:
        return slugify_cache[s]
    slug = s.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    slugify_cache[s] = slug
    return slug


# --- Cache helpers for active reservations ---
def load_cached_reservations(cache_file=CACHE_FILE):
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            try:
                data = json.load(f)
                if not isinstance(data, dict):
                    return {}
                return data
            except json.JSONDecodeError:
                return {}
    return {}

def save_cached_reservations(data, cache_file=CACHE_FILE):
    with open(cache_file, "w") as f:
        json.dump(data, f, indent=2, default=str)

def parse_and_group_events(now_override=None, cache_file=CACHE_FILE):
    logger.info("Fetching calendar feed from source...")
    response = requests.get(SOURCE_ICAL_URL)
    cal = ICal.from_ical(response.text)

    properties = defaultdict(list)
    tz = pytz.timezone(TIMEZONE)

    cache = load_cached_reservations(cache_file)
    now = now_override.astimezone(tz) if now_override else datetime.now(tz)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    seen_uids_by_prop = defaultdict(set)
    source_events_by_uid = {}

    for component in cal.walk():
        if component.name != "VEVENT":
            continue

        summary = str(component.get('SUMMARY', ''))
        uid = str(component.get('UID', ''))
        dtstart_raw = component.get('DTSTART')
        dtend_raw = component.get('DTEND')

        if not dtstart_raw or not dtend_raw:
            continue

        # Handle DATE vs DATETIME using pytz timezone-aware conversion
        puerto_rico_tz = pytz.timezone("America/Puerto_Rico")
        dtstart = dtstart_raw.dt
        dtend = dtend_raw.dt

        if isinstance(dtstart, datetime):
            if dtstart.tzinfo is None:
                dtstart = puerto_rico_tz.localize(dtstart)
        else:
            dtstart = puerto_rico_tz.localize(datetime.combine(dtstart, time(16, 0)))

        if isinstance(dtend, datetime):
            if dtend.tzinfo is None:
                dtend = puerto_rico_tz.localize(dtend)
        else:
            dtend = puerto_rico_tz.localize(datetime.combine(dtend, time(11, 0)))

        if dtend <= today_start:
            continue

        label = "Close-out"
        booking_code = "MANUAL"
        property_name = "Unknown"

        full_match = re.match(r'(Apartment|Room) ([\w\s\-]+):([\w\d]+)', summary)
        if full_match:
            _, property_name, booking_code = full_match.groups()
            label = "Reservation"
        else:
            loose_match = re.match(r'(Apartment|Room) ([\w\s\-]+)', summary)
            if loose_match and "CTB" in uid:  # likely reservation, but no explicit code
                property_name = loose_match.group(2)
                booking_code = uid.split(":")[-1] if ":" in uid else uid
                label = "Reservation"

        if label != "Reservation":
            continue
        full_property_name = summary.split(':')[0].strip()
        key = full_property_name

        dtstamp_raw = component.get('DTSTAMP')
        if dtstamp_raw:
            src_dtstamp = dtstamp_raw.dt
            if isinstance(src_dtstamp, datetime) and src_dtstamp.tzinfo is None:
                src_dtstamp = pytz.utc.localize(src_dtstamp)
        else:
            src_dtstamp = datetime.now(pytz.utc)

        # Build a normalized event dict for export
        nights = (dtend.date() - dtstart.date()).days
        summary_text = f"{full_property_name} ({booking_code})"

        # Ensure dtstart and dtend are timezone-aware in PR
        start = dtstart if dtstart.tzinfo else puerto_rico_tz.localize(dtstart)
        end = dtend if dtend.tzinfo else puerto_rico_tz.localize(dtend)

        dtstart_utc = start.astimezone(pytz.utc)
        dtend_utc = end.astimezone(pytz.utc)

        desc_lines = [
            f"Name/Unit: {full_property_name}",
            f"Reservation Code: {booking_code}",
            f"Property: {full_property_name}",
            f"UID: {uid}",
            f"Nights: {nights}",
            f"Start: {start.isoformat()} ({dtstart_utc.isoformat()} UTC)",
            f"End: {end.isoformat()} ({dtend_utc.isoformat()} UTC)",
        ]

        location_raw = component.get('LOCATION')
        if location_raw:
            desc_lines.append(f"Location: {location_raw}")

        description_raw = component.get('DESCRIPTION')
        if description_raw:
            desc_lines.append(f"Source Description: {description_raw}")

        categories_raw = component.get('CATEGORIES')
        if categories_raw:
            desc_lines.append(f"Categories: {categories_raw}")

        properties[key].append({
            'uid': uid,
            'summary': summary_text,
            'description': "\n".join(str(x) for x in desc_lines),
            'start': start,
            'end': end,
            'location': str(location_raw) if location_raw else None,
            'geo': None,
            'dtstamp': src_dtstamp.isoformat(),
            'version': 1,
            'last_seen': now.isoformat(),
        })

        seen_uids_by_prop[key].add(uid)
        source_events_by_uid[(key, uid)] = properties[key][-1]

    merged_count = 0
    restored_active_after_start = 0
    cancelled_future_missing = 0
    for prop_name, cached_events in cache.items():
        if prop_name not in properties:
            properties[prop_name] = []

        for ev in cached_events:
            try:
                cached_uid = ev.get('uid')
                cached_start = datetime.fromisoformat(ev['start']).astimezone(tz)
                cached_end = datetime.fromisoformat(ev['end']).astimezone(tz)
                cached_dtstamp = datetime.fromisoformat(ev.get('dtstamp')).astimezone(pytz.utc) if ev.get('dtstamp') else None
                cached_version = ev.get('version', 1)
                cached_last_seen = ev.get('last_seen')
            except Exception:
                continue

            in_source = (prop_name, cached_uid) in source_events_by_uid

            if in_source:
                src = source_events_by_uid[(prop_name, cached_uid)]
                try:
                    src_dt = datetime.fromisoformat(src['dtstamp']).astimezone(pytz.utc) if src.get('dtstamp') else None
                except Exception:
                    src_dt = None

                if src_dt and cached_dtstamp and src_dt > cached_dtstamp:
                    src['version'] = cached_version + 1
                    src['last_seen'] = now.isoformat()
                else:
                    src.setdefault('version', cached_version)
                    src.setdefault('last_seen', now.isoformat())
                merged_count += 1
                continue

            # At this point the event was previously cached but not present in the current source feed.
            if cached_end <= now:
                # Already ended; drop it.
                continue

            if cached_start <= now:
                # Booking has started; keep it even though the source feed dropped it.
                if cached_uid not in [e['uid'] for e in properties[prop_name]]:
                    properties[prop_name].append({
                        'uid': cached_uid,
                        'summary': ev.get('summary'),
                        'description': ev.get('description'),
                        'start': cached_start,
                        'end': cached_end,
                        'location': ev.get('location'),
                        'geo': ev.get('geo'),
                        'dtstamp': ev.get('dtstamp'),
                        'version': cached_version,
                        'last_seen': cached_last_seen or now.isoformat(),
                    })
                    merged_count += 1
                    restored_active_after_start += 1
            else:
                # Booking was removed before it began; treat as cancelled and omit from outputs/cache.
                cancelled_future_missing += 1

    logger.info(
        f"Merged {merged_count} cached active events into current feed "
        f"(restored_started={restored_active_after_start}, cancelled_future={cancelled_future_missing})"
    )

    # Ensure all known property keys are present, even if empty
    for key in KNOWN_PROPERTIES:
        if key not in properties:
            properties[key] = []

    # Save current active events to cache
    cache_to_save = {}
    for prop_name, events in properties.items():
        cache_evs = []
        for e in events:
            try:
                if e['end'] <= now:
                    continue
                cache_evs.append({
                    'uid': e['uid'],
                    'summary': e.get('summary'),
                    'start': e['start'].isoformat(),
                    'end': e['end'].isoformat(),
                    'description': e.get('description'),
                    'dtstamp': e.get('dtstamp') if e.get('dtstamp') else datetime.now(pytz.utc).isoformat(),
                    'version': e.get('version', 1),
                    'last_seen': e.get('last_seen', now.isoformat()),
                    'location': e.get('location'),
                    'geo': e.get('geo'),
                })
            except Exception:
                continue
        cache_to_save[prop_name] = cache_evs
    save_cached_reservations(cache_to_save, cache_file)

    logger.info(f"Parsed calendar: {sum(len(v) for v in properties.values())} reservation events across {len(properties)} properties")
    return properties

@app.route("/calendar/<property_name>.ics")
def export_property_calendar(property_name):
    props = parse_and_group_events()

    # Resolve slug to the original property key (support legacy hyphen-only links too)
    slug_map = {slugify(k): k for k in props.keys()}
    key = slug_map.get(property_name.lower())
    if not key:
        normalized_property_name = property_name.replace("-", " ")
        if normalized_property_name in props:
            key = normalized_property_name
    if not key:
        return Response(f"No calendar found for {property_name}", status=404)

    # Build VCALENDAR matching Hospitable-style headers
    cal_out = ICal()
    cal_out.add('prodid', 'https://pms-calendar.fly.dev/')
    cal_out.add('version', '2.0')
    cal_out.add('calscale', 'GREGORIAN')
    cal_out.add('x-published-ttl', 'PT30M')
    relcalid = f"{slugify(key)}-property@pms-calendar.fly.dev"
    cal_out.add('x-wr-relcalid', relcalid)
    cal_out.add('x-wr-caldesc', f'Reservation feed for {key} (provided by https://pms-calendar.fly.dev/)')
    cal_out.add('x-wr-calname', key)

    # Add events
    for ev in props[key]:
        e = IEvent()

        # Build a UID that is unique per PMS by combining the source UID with the unit code (e.g., MAO, AYA).
        unit_code_match = re.match(r'^(Apartment|Room)\s+([A-Z]{2,5})\b', key)
        unit_code = unit_code_match.group(2) if unit_code_match else slugify(key)

        src_uid = ev.get('uid') or f"{int(ev['start'].timestamp())}@staypr"
        src_uid_left = src_uid.split('@', 1)[0] if '@' in src_uid else src_uid
        combined_uid = f"{src_uid_left}+{unit_code}@staypr"
        e.add('uid', combined_uid)
        # Expose original identifiers for debugging/traceability
        e.add('X-ORIGINAL-UID', src_uid)
        e.add('X-UNIT-CODE', unit_code)

        ev_dtstamp = None
        try:
            ev_dtstamp = datetime.fromisoformat(ev.get('dtstamp')).astimezone(pytz.utc) if ev.get('dtstamp') else None
        except Exception:
            pass

        # Always use the newer of stored dtstamp vs now (not the older one)
        e.add('dtstamp', ev_dtstamp if ev_dtstamp else datetime.now(pytz.utc))
        e.add('summary', ev['summary'])
        e.add('description', ev['description'])

        # DTSTART/DTEND with TZID=America/Puerto_Rico
        e.add('dtstart', ev['start'])
        e['DTSTART'].params['TZID'] = 'America/Puerto_Rico'
        e.add('dtend', ev['end'])
        e['DTEND'].params['TZID'] = 'America/Puerto_Rico'

        if ev.get('location'):
            e.add('location', ev['location'])
        if ev.get('geo') and isinstance(ev['geo'], (list, tuple)) and len(ev['geo']) == 2:
            e.add('geo', ev['geo'])

        cal_out.add_component(e)

    # Append a minimal VTIMEZONE block
    tz_comp = ITimezone()
    tz_comp.add('tzid', 'America/Puerto_Rico')
    std = ITimezoneStandard()
    std.add('dtstart', datetime(2025, 9, 7, 16, 0, 0))
    std.add('tzname', 'AST')
    std.add('tzoffsetto', timedelta(hours=-4))
    std.add('tzoffsetfrom', timedelta(hours=-4))
    tz_comp.add_component(std)
    cal_out.add_component(tz_comp)

    ical_bytes = cal_out.to_ical()
    return Response(ical_bytes, mimetype='text/calendar')

@app.route("/")
def list_properties():
    logger.info("Root URL accessed; listing all properties")
    base_url = request.url_root.rstrip("/")
    props = parse_and_group_events()
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            background-color: black;
            color: #00FF00;
            font-family: monospace;
            padding: 2em;
            font-size: 1.25em;
            line-height: 1.8;
        }}
        a {{
            color: #00FFFF;
            font-weight: bold;
        }}
        li {{
            margin-bottom: 30px;
        }}
        button {{
            background-color: #66ff66;
            color: black;
            border: none;
            padding: 5px 10px;
            cursor: pointer;
            font-weight: bold;
            transition: background-color 150ms ease, transform 120ms ease;
        }}

        button:hover {{
            background-color: #39ff14;
            transform: translateY(-2px);
        }}
        code {{
            font-size: 1em;
            display: inline-block;
        }}
        .toast {{
            visibility: hidden;
            min-width: 250px;
            background-color: #66ff66;
            color: black;
            text-align: center;
            border-radius: 4px;
            padding: 10px;
            position: fixed;
            z-index: 1;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            font-family: monospace;
        }}
        .toast.show {{
            visibility: visible;
            animation: fadein 0.5s, fadeout 0.5s 2.5s;
        }}
        @keyframes fadein {{
            from {{bottom: 0; opacity: 0;}}
            to {{bottom: 30px; opacity: 1;}}
        }}
        @keyframes fadeout {{
            from {{bottom: 30px; opacity: 1;}}
            to {{bottom: 0; opacity: 0;}}
        }}
    </style>
    <script>
        function copyToClipboard(id) {{
            const copyText = document.getElementById(id);
            navigator.clipboard.writeText(copyText.textContent).then(() => {{
                const toast = document.getElementById("toast");
                toast.className = "toast show";
                setTimeout(() => {{ toast.className = toast.className.replace("show", ""); }}, 3000);
            }});
        }}
    </script>
</head>
<body>
    <h2>MARU - Available Calendars</h2>
    <ul>
"""
    def sort_apartments_first(s):
        s_lower = s.lower()
        prefix_priority = 0 if s_lower.startswith("apartment") else (1 if s_lower.startswith("room") else 2)
        return (prefix_priority, s_lower)

    for i, prop in enumerate(sorted(props.keys(), key=sort_apartments_first)):
        url_friendly_name = slugify(prop)
        calendar_url = f"{base_url}/calendar/{url_friendly_name}.ics"
        html += f'''
    <li>
        <a href="{calendar_url}">{prop}.ics</a><br>
        <code id="url{i}">{calendar_url}</code>
        <button onclick="copyToClipboard('url{i}')">Copy</button>
    </li>
    '''

    html += f"""
    </ul>
    <div id="toast" class="toast">Copied to clipboard</div>
    <footer style="position: fixed; bottom: 10px; width: 100%; text-align: center; font-size: 0.9em;">
        Last updated: {datetime.now(pytz.timezone(TIMEZONE)).strftime('%Y-%m-%d %H:%M:%S %Z')} – © {datetime.now().year} Optihome Services LLC. All rights reserved.
    </footer>
</body>
</html>
"""
    return Response(html, mimetype='text/html')


# --- Manual cache clear route ---
@app.route("/refresh")
def refresh_cache():
    """Force clear the cached reservation data."""
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
        logger.info("Cache file deleted manually via /refresh route.")
        return Response("Cache cleared. It will rebuild automatically on next load.", status=200)
    else:
        logger.info("Cache file not found; nothing to delete.")
        return Response("No cache file found. Nothing to clear.", status=200)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
