import datetime

import pytest

from app.services.prayer_service import PrayerService


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_refresh_times_filters_and_sets(monkeypatch):
    svc = PrayerService()

    now = int(datetime.datetime.now().timestamp())
    payload = {
        "data": {
            "date": {"timestamp": str(now)},
            "timings": {
                "Fajr": "05:01",
                "Sunrise": "06:00",
                "Dhuhr": "12:30",
                "Asr": "15:45",
                "Maghrib": "18:02",
                "Isha": "19:20",
            },
        }
    }

    def fake_get(url, timeout):
        return DummyResponse(payload)

    monkeypatch.setattr("app.services.prayer_service.requests.get", fake_get)
    ts, times, played = svc.refresh_times()

    assert ts is not None
    assert set(times.keys()) == {"Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"}
    assert all(v is False for v in played.values())


def test_check_and_due_prayers_window():
    svc = PrayerService()
    svc.timestamp = datetime.datetime.now()
    svc.prayer_times = {"Asr": "15:10"}
    svc.adhan_played = {"Asr": False}

    # exactly at window end
    now = datetime.datetime.combine(datetime.date.today(), datetime.time(15, 10))
    due = svc.check_and_due_prayers(now)
    assert due.get("Asr") is True

    # next call should not trigger again
    due2 = svc.check_and_due_prayers(now)
    assert due2.get("Asr") is None


def test_maybe_daily_refresh_retries_when_no_timestamp(monkeypatch):
    svc = PrayerService()
    calls = []

    def fake_refresh():
        calls.append(True)
        return None, {}, {}

    monkeypatch.setattr(svc, "refresh_times", fake_refresh)

    svc.maybe_daily_refresh()

    assert calls == [True]


def test_refresh_times_uses_https_timeout_and_status_check(monkeypatch):
    svc = PrayerService()

    now = int(datetime.datetime.now().timestamp())
    payload = {
        "data": {
            "date": {"timestamp": str(now)},
            "timings": {
                "Fajr": "05:01",
                "Dhuhr": "12:30",
                "Asr": "15:45",
                "Maghrib": "18:02",
                "Isha": "19:20",
            },
        }
    }
    seen = {}

    class ResponseWithStatus(DummyResponse):
        def raise_for_status(self):
            seen["raise_for_status"] = True

    def fake_get(url, timeout):
        seen["url"] = url
        seen["timeout"] = timeout
        return ResponseWithStatus(payload)

    monkeypatch.setattr("app.services.prayer_service.requests.get", fake_get)

    svc.refresh_times()

    assert seen["url"].startswith("https://api.aladhan.com/")
    assert seen["timeout"] == 10
    assert seen["raise_for_status"] is True
