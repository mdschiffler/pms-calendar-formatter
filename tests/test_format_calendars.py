import importlib.util
import json
from datetime import datetime
from pathlib import Path

from icalendar import Calendar as ICal
import pytz


MODULE_PATH = Path(__file__).resolve().parent.parent / "format-calendars.py"


def load_module():
    spec = importlib.util.spec_from_file_location("format_calendars", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DummyResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code


ICS_SAMPLE = """BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN
PRODID:-//freetobook//EN
BEGIN:VEVENT
UID:2025-12-03T10:17:43+00:00-53930@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Last update 2025-12-03 10:17:43
DTSTART:20251203T000000
DTEND:20251203T000000
END:VEVENT
BEGIN:VEVENT
UID:73132874@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Room FIVE:CTB1920E90
DTSTART;VALUE=DATE:20251201
DTEND;VALUE=DATE:20251206
END:VEVENT
BEGIN:VEVENT
UID:73313214@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Apartment RYO:CTB19308FB
DTSTART;VALUE=DATE:20251202
DTEND;VALUE=DATE:20251204
END:VEVENT
BEGIN:VEVENT
UID:73250158@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Apartment UMI:WTB192755B
DTSTART;VALUE=DATE:20251203
DTEND;VALUE=DATE:20251207
END:VEVENT
BEGIN:VEVENT
UID:73318789@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Room TWO:CTB193126D
DTSTART;VALUE=DATE:20251203
DTEND;VALUE=DATE:20251208
END:VEVENT
BEGIN:VEVENT
UID:73244251@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Apartment RYO:CTB192A5B0
DTSTART;VALUE=DATE:20251204
DTEND;VALUE=DATE:20251207
END:VEVENT
BEGIN:VEVENT
UID:73288483@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Room ONE:WTB19174DB
DTSTART;VALUE=DATE:20251204
DTEND;VALUE=DATE:20251206
END:VEVENT
BEGIN:VEVENT
UID:73231359@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Room THREE:CTB192928F
DTSTART;VALUE=DATE:20251204
DTEND;VALUE=DATE:20251206
END:VEVENT
BEGIN:VEVENT
UID:73251186@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Apartment AYA:CTB192A456
DTSTART;VALUE=DATE:20251205
DTEND;VALUE=DATE:20251208
END:VEVENT
BEGIN:VEVENT
UID:73279787@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Room ONE:CTB192D96F
DTSTART;VALUE=DATE:20251206
DTEND;VALUE=DATE:20251207
END:VEVENT
BEGIN:VEVENT
UID:73286447@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Apartment UMI:CTB192E523
DTSTART;VALUE=DATE:20251211
DTEND;VALUE=DATE:20251214
END:VEVENT
BEGIN:VEVENT
UID:73190922@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Room ONE:CTB192555E
DTSTART;VALUE=DATE:20251211
DTEND;VALUE=DATE:20251215
END:VEVENT
BEGIN:VEVENT
UID:73256713@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Room THREE:CTB192B74E
DTSTART;VALUE=DATE:20251211
DTEND;VALUE=DATE:20251215
END:VEVENT
BEGIN:VEVENT
UID:72915748@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Room FIVE:CTB190CC17
DTSTART;VALUE=DATE:20251212
DTEND;VALUE=DATE:20251215
END:VEVENT
BEGIN:VEVENT
UID:72730530@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Apartment RYO:CTB18FBBD7
DTSTART;VALUE=DATE:20251214
DTEND;VALUE=DATE:20251220
END:VEVENT
BEGIN:VEVENT
UID:73289323@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Apartment UMI:CTB192EACA
DTSTART;VALUE=DATE:20251216
DTEND;VALUE=DATE:20251220
END:VEVENT
BEGIN:VEVENT
UID:73318957@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Apartment AYA:WTB19312C6
DTSTART;VALUE=DATE:20251221
DTEND;VALUE=DATE:20251224
END:VEVENT
BEGIN:VEVENT
UID:72608579@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Apartment MAO - Five Bedroom:WTB18EFAFD
DTSTART;VALUE=DATE:20251228
DTEND;VALUE=DATE:20260103
END:VEVENT
BEGIN:VEVENT
UID:73302947@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Apartment RYO:CTB19291D3
DTSTART;VALUE=DATE:20260105
DTEND;VALUE=DATE:20260110
END:VEVENT
BEGIN:VEVENT
UID:73132431@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Apartment MAO - Five Bedroom:WTB1920DA1
DTSTART;VALUE=DATE:20260109
DTEND;VALUE=DATE:20260112
END:VEVENT
BEGIN:VEVENT
UID:68151962@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Apartment AYA:CTB1743984
DTSTART;VALUE=DATE:20260114
DTEND;VALUE=DATE:20260119
END:VEVENT
BEGIN:VEVENT
UID:68140732@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Apartment RYO:CTB17429E9
DTSTART;VALUE=DATE:20260114
DTEND;VALUE=DATE:20260119
END:VEVENT
BEGIN:VEVENT
UID:68140764@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Apartment UMI:CTB1742A00
DTSTART;VALUE=DATE:20260114
DTEND;VALUE=DATE:20260119
END:VEVENT
BEGIN:VEVENT
UID:69008635@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Apartment MAO - Five Bedroom:MTB1799717
DTSTART;VALUE=DATE:20260115
DTEND;VALUE=DATE:20260119
END:VEVENT
BEGIN:VEVENT
UID:72672750@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Apartment MAO - Five Bedroom:CTB18F609D
DTSTART;VALUE=DATE:20260206
DTEND;VALUE=DATE:20260209
END:VEVENT
BEGIN:VEVENT
UID:72641000@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Apartment MAO - Five Bedroom:WTB18E9E75
DTSTART;VALUE=DATE:20260212
DTEND;VALUE=DATE:20260216
END:VEVENT
BEGIN:VEVENT
UID:72870117@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Apartment MAO - Five Bedroom:CTB1908669
DTSTART;VALUE=DATE:20260227
DTEND;VALUE=DATE:20260302
END:VEVENT
BEGIN:VEVENT
UID:73216599@freetobook.com
DTSTAMP:20251203T101743Z
SUMMARY:Apartment MAO - Five Bedroom:CTB1927F31
DTSTART;VALUE=DATE:20260402
DTEND;VALUE=DATE:20260405
END:VEVENT
END:VCALENDAR
"""


MULTI_UNIT_BOOKING_SAMPLE = """BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN
PRODID:-//freetobook//EN
BEGIN:VEVENT
UID:74699666@freetobook.com
DTSTAMP:20260417T182517Z
SUMMARY:Apartment MAO - Five Bedroom:WTB19BCD37
DTSTART;VALUE=DATE:20260507
DTEND;VALUE=DATE:20260511
END:VEVENT
BEGIN:VEVENT
UID:74699663@freetobook.com
DTSTAMP:20260417T182517Z
SUMMARY:Apartment AYA:WTB19BCD37
DTSTART;VALUE=DATE:20260507
DTEND;VALUE=DATE:20260511
END:VEVENT
BEGIN:VEVENT
UID:74699664@freetobook.com
DTSTAMP:20260417T182517Z
SUMMARY:Apartment RYO:WTB19BCD37
DTSTART;VALUE=DATE:20260507
DTEND;VALUE=DATE:20260511
END:VEVENT
BEGIN:VEVENT
UID:74699665@freetobook.com
DTSTAMP:20260417T182517Z
SUMMARY:Apartment UMI:WTB19BCD37
DTSTART;VALUE=DATE:20260507
DTEND;VALUE=DATE:20260511
END:VEVENT
END:VCALENDAR
"""


def ical_events_from_response(response):
    cal = ICal.from_ical(response.data)
    return [component for component in cal.walk() if component.name == "VEVENT"]


def test_keeps_started_booking_missing_from_source(monkeypatch, tmp_path):
    """If the source feed drops an in-progress booking, it should be restored from cache."""
    module = load_module()
    tz = pytz.timezone(module.TIMEZONE)
    now = tz.localize(datetime(2025, 1, 10, 12, 0, 0))

    started_uid = "started-uid"
    future_uid = "future-uid"
    cache_file = tmp_path / "cache.json"

    cache_payload = {
        "Room ONE": [
            {
                "uid": started_uid,
                "summary": "Room ONE (ABC)",
                "start": tz.localize(datetime(2025, 1, 8, 16, 0, 0)).isoformat(),
                "end": tz.localize(datetime(2025, 1, 13, 11, 0, 0)).isoformat(),
                "description": "Started booking",
                "dtstamp": datetime(2025, 1, 1, 0, 0, 0, tzinfo=pytz.utc).isoformat(),
                "version": 1,
                "last_seen": now.isoformat(),
                "location": None,
                "geo": None,
            },
            {
                "uid": future_uid,
                "summary": "Room ONE (DEF)",
                "start": tz.localize(datetime(2025, 1, 12, 16, 0, 0)).isoformat(),
                "end": tz.localize(datetime(2025, 1, 15, 11, 0, 0)).isoformat(),
                "description": "Future booking",
                "dtstamp": datetime(2025, 1, 2, 0, 0, 0, tzinfo=pytz.utc).isoformat(),
                "version": 1,
                "last_seen": now.isoformat(),
                "location": None,
                "geo": None,
            },
        ]
    }
    cache_file.write_text(json.dumps(cache_payload))

    ics_text = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//test//EN\nEND:VCALENDAR"
    monkeypatch.setattr(module.requests, "get", lambda url, **kwargs: DummyResponse(ics_text))

    props = module.parse_and_group_events(now_override=now, cache_file=str(cache_file))
    room_events = props["Room ONE"]
    uids = {e["uid"] for e in room_events}

    assert started_uid in uids, "Started booking should be restored from cache when missing in source"
    assert future_uid not in uids, "Future booking removed from source before start should be treated as cancelled"


def test_parses_sample_feed_and_groups_by_property(monkeypatch, tmp_path):
    module = load_module()
    tz = pytz.timezone(module.TIMEZONE)
    now = tz.localize(datetime(2025, 12, 3, 12, 0, 0))

    cache_file = tmp_path / "cache.json"
    monkeypatch.setattr(module.requests, "get", lambda url, **kwargs: DummyResponse(ICS_SAMPLE))

    props = module.parse_and_group_events(now_override=now, cache_file=str(cache_file))

    expected_counts = {
        "Room FIVE": 2,
        "Apartment RYO": 5,
        "Apartment UMI": 4,
        "Room TWO": 1,
        "Room ONE": 3,
        "Room THREE": 2,
        "Apartment AYA": 3,
        "Apartment MAO - Five Bedroom": 7,
    }

    # Last update event is ignored and default keys still exist.
    for key in module.KNOWN_PROPERTIES:
        assert key in props, f"Default placeholder {key} key should exist even if empty"

    for prop, count in expected_counts.items():
        assert prop in props, f"{prop} should be present"
        assert len(props[prop]) == count, f"{prop} should have {count} events"

    # Check a representative event for correct timezone-aware start/end
    umi_event = next(e for e in props["Apartment UMI"] if e["uid"] == "73250158@freetobook.com")
    assert umi_event["start"].tzinfo is not None and umi_event["end"].tzinfo is not None
    assert umi_event["start"].hour == 16 and umi_event["end"].hour == 11, "DATE values should use 16:00 check-in and 11:00 checkout times"
    assert umi_event["start"].date().isoformat() == "2025-12-03"
    assert umi_event["end"].date().isoformat() == "2025-12-07"


def test_generates_empty_calendars_for_known_properties(monkeypatch, tmp_path):
    module = load_module()
    tz = pytz.timezone(module.TIMEZONE)
    now = tz.localize(datetime(2025, 1, 1, 12, 0, 0))

    cache_file = tmp_path / "cache.json"
    empty_feed = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//test//EN\nEND:VCALENDAR"
    monkeypatch.setattr(module.requests, "get", lambda url, **kwargs: DummyResponse(empty_feed))

    props = module.parse_and_group_events(now_override=now, cache_file=str(cache_file))

    for key in module.KNOWN_PROPERTIES:
        assert key in props, f"{key} should always have a generated calendar"
        assert props[key] == [], f"{key} should be empty when the source feed has no reservations"


def test_same_booking_code_across_units_is_not_deduped(monkeypatch, tmp_path):
    module = load_module()
    tz = pytz.timezone(module.TIMEZONE)
    now = tz.localize(datetime(2026, 4, 17, 12, 0, 0))

    cache_file = tmp_path / "cache.json"
    monkeypatch.setattr(module.requests, "get", lambda url, **kwargs: DummyResponse(MULTI_UNIT_BOOKING_SAMPLE))

    props = module.parse_and_group_events(now_override=now, cache_file=str(cache_file))

    expected = {
        "Apartment MAO - Five Bedroom": "74699666@freetobook.com",
        "Apartment AYA": "74699663@freetobook.com",
        "Apartment RYO": "74699664@freetobook.com",
        "Apartment UMI": "74699665@freetobook.com",
    }
    for prop, uid in expected.items():
        matching_events = [event for event in props[prop] if "WTB19BCD37" in event["summary"]]
        assert len(matching_events) == 1, f"{prop} should keep its own WTB19BCD37 reservation"
        assert matching_events[0]["uid"] == uid
        assert matching_events[0]["start"].date().isoformat() == "2026-05-07"
        assert matching_events[0]["end"].date().isoformat() == "2026-05-11"


def test_routes_export_same_booking_code_with_unit_scoped_uids(monkeypatch, tmp_path):
    module = load_module()
    tz = pytz.timezone(module.TIMEZONE)
    now = tz.localize(datetime(2026, 4, 17, 12, 0, 0))

    cache_file = tmp_path / "cache.json"
    monkeypatch.setattr(module.requests, "get", lambda url, **kwargs: DummyResponse(MULTI_UNIT_BOOKING_SAMPLE))
    props = module.parse_and_group_events(now_override=now, cache_file=str(cache_file))
    monkeypatch.setattr(module, "parse_and_group_events", lambda: props)

    expected = {
        "apartment-mao-five-bedroom": ("Apartment MAO - Five Bedroom (WTB19BCD37)", "74699666@freetobook.com", "MAO"),
        "apartment-aya": ("Apartment AYA (WTB19BCD37)", "74699663@freetobook.com", "AYA"),
        "apartment-ryo": ("Apartment RYO (WTB19BCD37)", "74699664@freetobook.com", "RYO"),
        "apartment-umi": ("Apartment UMI (WTB19BCD37)", "74699665@freetobook.com", "UMI"),
    }

    with module.app.test_client() as client:
        for slug, (summary, source_uid, unit_code) in expected.items():
            response = client.get(f"/calendar/{slug}.ics")
            assert response.status_code == 200

            events = ical_events_from_response(response)
            assert len(events) == 1
            event = events[0]
            assert str(event.get("SUMMARY")) == summary
            assert str(event.get("UID")) == f"{source_uid.split('@', 1)[0]}+{unit_code}@staypr"
            assert str(event.get("X-ORIGINAL-UID")) == source_uid
            assert str(event.get("X-UNIT-CODE")) == unit_code
            assert str(event.get("STATUS")) == "CONFIRMED"
            assert str(event.get("TRANSP")) == "OPAQUE"
            assert event.get("LAST-MODIFIED") is not None
            assert int(event.get("SEQUENCE")) == 1


def test_fetch_failure_uses_cache_without_overwriting_it(monkeypatch, tmp_path):
    module = load_module()
    tz = pytz.timezone(module.TIMEZONE)
    now = tz.localize(datetime(2026, 1, 10, 12, 0, 0))

    started_uid = "started-cache-uid"
    future_uid = "future-cache-uid"
    ended_uid = "ended-cache-uid"
    cache_file = tmp_path / "cache.json"
    cache_payload = {
        "Room ONE": [
            {
                "uid": started_uid,
                "summary": "Room ONE (STARTED)",
                "start": tz.localize(datetime(2026, 1, 8, 16, 0, 0)).isoformat(),
                "end": tz.localize(datetime(2026, 1, 13, 11, 0, 0)).isoformat(),
                "description": "Started booking",
                "dtstamp": datetime(2026, 1, 1, 0, 0, 0, tzinfo=pytz.utc).isoformat(),
                "version": 2,
                "last_seen": now.isoformat(),
                "location": None,
                "geo": None,
            },
            {
                "uid": future_uid,
                "summary": "Room ONE (FUTURE)",
                "start": tz.localize(datetime(2026, 1, 12, 16, 0, 0)).isoformat(),
                "end": tz.localize(datetime(2026, 1, 15, 11, 0, 0)).isoformat(),
                "description": "Future booking",
                "dtstamp": datetime(2026, 1, 2, 0, 0, 0, tzinfo=pytz.utc).isoformat(),
                "version": 1,
                "last_seen": now.isoformat(),
                "location": None,
                "geo": None,
            },
            {
                "uid": ended_uid,
                "summary": "Room ONE (ENDED)",
                "start": tz.localize(datetime(2026, 1, 1, 16, 0, 0)).isoformat(),
                "end": tz.localize(datetime(2026, 1, 3, 11, 0, 0)).isoformat(),
                "description": "Ended booking",
                "dtstamp": datetime(2026, 1, 1, 0, 0, 0, tzinfo=pytz.utc).isoformat(),
                "version": 1,
                "last_seen": now.isoformat(),
                "location": None,
                "geo": None,
            },
        ]
    }
    cache_file.write_text(json.dumps(cache_payload))
    original_cache_text = cache_file.read_text()

    monkeypatch.setattr(module.requests, "get", lambda url, **kwargs: DummyResponse("temporary failure", status_code=503))

    props = module.parse_and_group_events(now_override=now, cache_file=str(cache_file))
    uids = {event["uid"] for event in props["Room ONE"]}

    assert started_uid in uids
    assert future_uid in uids
    assert ended_uid not in uids
    assert cache_file.read_text() == original_cache_text
