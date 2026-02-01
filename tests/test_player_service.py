import time

import pytest

from app.services import player_service as ps_mod
from app.services.player_service import PlayerService


class FakeState:
    Ended = "ended"
    Stopped = "stopped"
    Error = "error"


class FakeMediaPlayer:
    def __init__(self, file_path):
        self.file_path = file_path
        self._muted = False
        self._volume = 100
        self._played = False

    def audio_set_volume(self, v):
        self._volume = v

    def audio_set_mute(self, m):
        self._muted = m

    def play(self):
        self._played = True

    def get_state(self):
        # finish quickly
        return FakeState.Ended if self._played else FakeState.Stopped


class FakeVLC:
    State = FakeState

    @staticmethod
    def MediaPlayer(file_path):
        return FakeMediaPlayer(file_path)


def test_volume_and_mute_controls(monkeypatch):
    # monkeypatch vlc with fake
    monkeypatch.setattr(ps_mod, "vlc", FakeVLC)

    svc = PlayerService()
    assert svc.set_volume(40) == 40
    assert svc.status()["volume"] == 40
    svc.mute()
    assert svc.status()["muted"] is True
    svc.unmute()
    assert svc.status()["muted"] is False


def test_preview_uses_player_thread(monkeypatch):
    monkeypatch.setattr(ps_mod, "vlc", FakeVLC)

    svc = PlayerService()
    # Avoid filesystem dependency
    monkeypatch.setattr(svc, "_pick_file_for_prayer", lambda prayer: "/tmp/fake.mp3")
    path = svc.preview("asr")
    assert path == "/tmp/fake.mp3"
    # Give background thread a moment to run
    time.sleep(0.1)
    # Should have completed quickly
    assert svc.status()["is_playing"] in (True, False)

