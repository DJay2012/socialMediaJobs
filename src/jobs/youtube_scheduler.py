import schedule
import time
from datetime import datetime, time as dt_time
from src.log.logging import logger
from src.youtube.youtubeScraper import youtube_scraper
from src.enums.types import Platform

MINUTES_INTERVAL = 30
Platform = Platform.YOUTUBE_BMW.value

# Operating hours: 6:00 AM to 9:00 PM
START_TIME = dt_time(6, 0)  # 6:00 AM
END_TIME = dt_time(21, 0)  # 9:00 PM


def is_operating_hours():
    """Check if current time is within operating hours (6 AM - 9 PM)"""
    current_time = datetime.now().time()
    return START_TIME <= current_time <= END_TIME


def run_job():
    current_datetime = datetime.now()
    current_time_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

    # Check if we're within operating hours
    if not is_operating_hours():
        logger.info(
            f"Outside operating hours (6 AM - 9 PM): {current_time_str}. Skipping job execution."
        )
        return

    logger.note(f"Starting: {Platform} Scheduled job at {current_time_str}")
    try:
        # Run scraper for today's date range (automatically determined by the scraper)
        youtube_scraper(Platform)
        logger.note(
            f"Completed: {Platform} Scheduled job at {current_datetime.strftime('%Y-%m-%d %H:%M:%S')}"
        )
    except Exception as e:
        logger.error(f"Error in scheduled job: {e}")


def RunYoutubeScheduler():
    logger.note(f"YouTube Scheduler started")
    logger.note(f"Job will run every {MINUTES_INTERVAL} minutes")
    logger.note(
        f"Operating hours: {START_TIME.strftime('%I:%M %p')} - {END_TIME.strftime('%I:%M %p')}"
    )

    # Check current time and warn if outside operating hours
    if not is_operating_hours():
        current_time = datetime.now().time()
        logger.warning(
            f"Scheduler started outside operating hours ({current_time.strftime('%I:%M %p')}). "
            f"Jobs will only run between {START_TIME.strftime('%I:%M %p')} - {END_TIME.strftime('%I:%M %p')}"
        )

    run_job()
    schedule.every(MINUTES_INTERVAL).minutes.do(run_job)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)

    except KeyboardInterrupt:
        logger.note("Scheduler stopped by user")

    except Exception as e:
        logger.error(f"Scheduler error: {e}")
        raise
