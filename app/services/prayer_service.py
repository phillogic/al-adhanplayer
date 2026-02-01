import datetime
import os
import threading
from typing import Dict, Tuple, Optional

import requests

from app.core.logging_config import get_logger
from app.metrics.registry import (
    GetLatestPrayerTimes_REQUEST_TIME,
    loop_counter,
    fajr_prayer_guage,
    duhr_prayer_guage,
    asr_prayer_guage,
    maghrib_prayer_guage,
    isha_prayer_guage,
)


class PrayerService:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.city = os.getenv('PRAYER_CITY', 'Sydney')
        self.country = os.getenv('PRAYER_COUNTRY', 'AU')
        self.method = os.getenv('ALADHAN_METHOD', '1')
        self.play_window_minutes = int(os.getenv('PLAY_WINDOW_MINUTES', '2'))
        self.timestamp: Optional[datetime.datetime] = None
        self.prayer_times: Dict[str, str] = {}
        self.adhan_played: Dict[str, bool] = {}
        self._lock = threading.Lock()

    @staticmethod
    def is_five_prayer(name: str) -> bool:
        return name.lower() in ("fajr", "dhuhr", "asr", "maghrib", "isha")

    def _set_gauges_for_prayer(self, prayer: str, when: datetime.datetime) -> None:
        if prayer.lower() == 'fajr':
            fajr_prayer_guage.set(when.timestamp())
        elif prayer.lower() == 'dhuhr':
            duhr_prayer_guage.set(when.timestamp())
        elif prayer.lower() == 'asr':
            asr_prayer_guage.set(when.timestamp())
        elif prayer.lower() == 'maghrib':
            maghrib_prayer_guage.set(when.timestamp())
        elif prayer.lower() == 'isha':
            isha_prayer_guage.set(when.timestamp())

    def update_gauges(self) -> None:
        with self._lock:
            if not self.prayer_times:
                return
            for prayer, time_str in self.prayer_times.items():
                try:
                    hour = int(time_str.split(':')[0])
                    minute = int(time_str.split(':')[1])
                    when = datetime.datetime.combine(datetime.date.today(), datetime.time(hour, minute))
                    self._set_gauges_for_prayer(prayer, when)
                except Exception as e:
                    self.logger.error(f"update_gauges: failed for {prayer}={time_str}: {e}")

    @GetLatestPrayerTimes_REQUEST_TIME.time()
    def refresh_times(self) -> Tuple[Optional[datetime.datetime], Dict[str, str], Dict[str, bool]]:
        today_date = datetime.datetime.now().strftime('%d-%m-%Y')
        url = (
            f"http://api.aladhan.com/v1/timingsByCity/{today_date}?city={self.city}&country={self.country}&method={self.method}"
        )
        self.logger.debug(f"refresh_times: GET {url}")
        try:
            r = requests.get(url)
            dataset = r.json()
            api_timings = dataset["data"]["timings"]
            filtered: Dict[str, str] = {
                k: v for k, v in api_timings.items() if self.is_five_prayer(k)
            }
            ts = datetime.datetime.fromtimestamp(int(dataset["data"]["date"]["timestamp"]))
            with self._lock:
                self.timestamp = ts
                self.prayer_times = filtered
                self.adhan_played = {k: False for k in filtered.keys()}
            self.logger.info(f"refresh_times: fetched {filtered}")
            self.update_gauges()
        except Exception as err:
            self.logger.error(f"refresh_times: error: {err}")
        return self.timestamp, self.prayer_times, self.adhan_played

    def times_response(self) -> Dict:
        with self._lock:
            return {
                'timestamp': self.timestamp,
                'times': dict(self.prayer_times),
            }

    def check_and_due_prayers(self, now: Optional[datetime.datetime] = None) -> Dict[str, bool]:
        """
        Determine which prayers are due within the play window and mark them as played.
        Returns a dict of prayers that should trigger playback now {prayer: True}.
        """
        if now is None:
            now = datetime.datetime.now()
        due: Dict[str, bool] = {}
        with self._lock:
            if not self.timestamp or not self.prayer_times:
                return due
            # If the stored date is before today, refresh is needed by caller
            for prayer, time_str in self.prayer_times.items():
                try:
                    hour = int(time_str.split(':')[0])
                    minute = int(time_str.split(':')[1])
                    if hour == now.hour and not self.adhan_played.get(prayer, False):
                        delta = minute - now.minute
                        if -self.play_window_minutes <= delta <= 0:
                            self.adhan_played[prayer] = True
                            due[prayer] = True
                except Exception as e:
                    self.logger.error(f"check_and_due_prayers: error for {prayer}={time_str}: {e}")
        return due

    def maybe_daily_refresh(self) -> None:
        now = datetime.datetime.now()
        with self._lock:
            ts = self.timestamp
        if ts and ts.date() < now.date():
            self.logger.debug("maybe_daily_refresh: timestamp expired, refreshing")
            self.refresh_times()

    def tick_metrics(self) -> None:
        loop_counter.inc()
        self.update_gauges()

