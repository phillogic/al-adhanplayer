from fastapi import APIRouter, Response
from prometheus_client import Summary, Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Metrics definitions (preserve original metric names)
GetLatestPrayerTimes_REQUEST_TIME = Summary(
    'adhan_player_GetLatestPrayerTimes_processing_seconds',
    'Time spent processing request for GetLatestPrayerTimes'
)
loop_counter = Counter('adhan_player_loop_counter', 'Description of counter')
fajr_prayer_guage = Gauge('epoch_to_fajr', 'epoch time for  fajr')
duhr_prayer_guage = Gauge('epoch_to_duhr', 'epoch time for  duhr')
asr_prayer_guage = Gauge('epoch_to_asr', 'epoch time for  asr')
maghrib_prayer_guage = Gauge('epoch_to_maghrib', 'epoch time for  maghrib')
isha_prayer_guage = Gauge('epoch_to_isha', 'epoch time for  isha')


metrics_router = APIRouter()


@metrics_router.get('/metrics', include_in_schema=False)
def metrics() -> Response:
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
