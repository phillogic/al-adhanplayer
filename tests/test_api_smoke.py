from fastapi.testclient import TestClient
import app.main as main_mod


def test_health_and_metrics(monkeypatch):
    # Prevent network calls in background loop startup
    monkeypatch.setattr(main_mod.PrayerService, "refresh_times", lambda self: (None, {}, {}))
    monkeypatch.setattr(main_mod.PrayerService, "maybe_daily_refresh", lambda self: None)
    with TestClient(main_mod.app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        r2 = client.get("/metrics")
        assert r2.status_code == 200


def test_player_controls(monkeypatch):
    monkeypatch.setattr(main_mod.PrayerService, "refresh_times", lambda self: (None, {}, {}))
    monkeypatch.setattr(main_mod.PrayerService, "maybe_daily_refresh", lambda self: None)
    with TestClient(main_mod.app) as client:
        r = client.get("/api/v1/player/status")
        assert r.status_code == 200
        r = client.post("/api/v1/player/volume", params={"level": 35})
        assert r.status_code == 200 and r.json()["volume"] == 35
        r = client.post("/api/v1/player/mute")
        assert r.status_code == 200 and r.json()["muted"] is True
        r = client.post("/api/v1/player/unmute")
        assert r.status_code == 200 and r.json()["muted"] is False

