import os
import random
import threading
import time
from typing import Optional

import vlc

from app.core.logging_config import get_logger


class PlayerService:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.media_dir = os.getenv('MEDIA_DIR', 'media')
        self.fajr_subdir = os.getenv('FAJR_SUBDIR', os.path.join(self.media_dir, 'fajr'))
        self._play_thread: Optional[threading.Thread] = None
        self._player: Optional[vlc.MediaPlayer] = None
        self._lock = threading.Lock()
        self._is_playing = False
        self._last_prayer: Optional[str] = None
        self._last_file: Optional[str] = None
        self._desired_volume = int(os.getenv('DEFAULT_VOLUME', '80'))  # 0-100
        self._muted = False

    def _strip_unwanted(self, files):
        return [f for f in files if f and not f.startswith('.') and f.lower().endswith('.mp3')]

    def _pick_file_for_prayer(self, prayer: str) -> Optional[str]:
        if prayer.lower() == 'fajr':
            for root, _, files in os.walk(self.fajr_subdir, topdown=True):
                candidates = self._strip_unwanted(files)
                if not candidates:
                    continue
                fname = random.choice(candidates)
                return os.path.join(root, fname)
            return None
        else:
            for root, _, files in os.walk(self.media_dir, topdown=True):
                candidates = self._strip_unwanted(files)
                if not candidates:
                    continue
                fname = random.choice(candidates)
                return os.path.join(root, fname)
            return None

    def _play_file(self, file_path: str, prayer: str) -> None:
        try:
            player = vlc.MediaPlayer(file_path)
            # apply desired volume and mute status
            with self._lock:
                self._player = player
                player.audio_set_volume(self._desired_volume)
                player.audio_set_mute(self._muted)
                self._is_playing = True
                self._last_prayer = prayer
                self._last_file = file_path
            self.logger.info(f"Playing adhan file {file_path} for {prayer}")
            player.play()
            # busy wait until playback finishes
            while True:
                state = player.get_state()
                if state in (vlc.State.Ended, vlc.State.Stopped, vlc.State.Error):
                    break
                time.sleep(0.2)
        except Exception as e:
            self.logger.error(f"Player error for {file_path}: {e}")
        finally:
            with self._lock:
                self._is_playing = False
                self._player = None

    def play_prayer(self, prayer: str) -> Optional[str]:
        file_path = self._pick_file_for_prayer(prayer)
        if not file_path:
            self.logger.error(f"No media file found for prayer {prayer}")
            return None
        t = threading.Thread(target=self._play_file, args=(file_path, prayer), daemon=True)
        t.start()
        with self._lock:
            self._play_thread = t
        return file_path

    def preview(self, prayer: str) -> Optional[str]:
        return self.play_prayer(prayer)

    def set_volume(self, level: int) -> int:
        level = max(0, min(100, level))
        with self._lock:
            self._desired_volume = level
            if self._player is not None:
                self._player.audio_set_volume(level)
        self.logger.info(f"Volume set to {level}")
        return level

    def mute(self) -> bool:
        with self._lock:
            self._muted = True
            if self._player is not None:
                self._player.audio_set_mute(True)
        self.logger.info("Muted")
        return True

    def unmute(self) -> bool:
        with self._lock:
            self._muted = False
            if self._player is not None:
                self._player.audio_set_mute(False)
        self.logger.info("Unmuted")
        return False

    def status(self) -> dict:
        with self._lock:
            return {
                'is_playing': self._is_playing,
                'last_prayer': self._last_prayer,
                'last_file': self._last_file,
                'volume': self._desired_volume,
                'muted': self._muted,
            }

