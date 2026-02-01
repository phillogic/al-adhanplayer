import asyncio
import contextlib
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging_config import get_logger
from app.metrics.registry import metrics_router
from app.routers import diagnostics, prayer as prayer_router, player as player_router
from app.services.prayer_service import PrayerService
from app.services.player_service import PlayerService


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting al-adhanplayer API")
    # Initialize services
    app.state.prayer_service = PrayerService()
    app.state.player_service = PlayerService()

    stop_event = asyncio.Event()

    async def background_loop():
        # initial refresh
        if not app.state.prayer_service.timestamp:
            app.state.prayer_service.refresh_times()
        try:
            while not stop_event.is_set():
                app.state.prayer_service.maybe_daily_refresh()
                app.state.prayer_service.tick_metrics()
                # find due prayers within the window
                due = app.state.prayer_service.check_and_due_prayers()
                for prayer in due.keys():
                    app.state.player_service.play_prayer(prayer)
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            pass

    task = asyncio.create_task(background_loop())

    try:
        yield
    finally:
        logger.info("🛑 Shutting down al-adhanplayer API")
        stop_event.set()
        task.cancel()
        with contextlib.suppress(Exception):
            await task


app = FastAPI(
    title="al-adhanplayer API",
    description="Adhan player service with Prometheus metrics and control endpoints",
    version=os.getenv("BUILD_ID", "2.0.0"),
    lifespan=lifespan,
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(diagnostics.router)
app.include_router(prayer_router.router)
app.include_router(player_router.router)
app.include_router(metrics_router)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info",
    )
