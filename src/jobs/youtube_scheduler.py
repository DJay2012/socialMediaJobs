import schedule
import time
from datetime import datetime, time as dt_time
from src.log.logging import logger
from src.youtube.youtubeScraper import youtube_scraper
from src.types.enums import SocialFeedType

MINUTES_INTERVAL = 60
SocialFeedType = SocialFeedType.YOUTUBE.value
search = {"companyId": "BMW01"}

# Operating hours: 8:00 AM to 10:00 PM
START_TIME = dt_time(8, 0)  # 8:00 AM
END_TIME = dt_time(22, 0)  # 10:00 PM


def is_operating_hours():
    """Check if current time is within operating hours (8 AM - 10 PM)"""
    current_time = datetime.now().time()
    return START_TIME <= current_time <= END_TIME


def run_job():
    current_datetime = datetime.now()
    current_time_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

    # Check if we're within operating hours
    if not is_operating_hours():
        logger.info(
            f"Outside operating hours (8 AM - 10 PM): {current_time_str}. Skipping job execution."
        )
        return

    logger.note(f"Starting: {SocialFeedType} Scheduled job at {current_time_str}")
    try:
        youtube_scraper(search)
        logger.note(
            f"Completed: {SocialFeedType} Scheduled job at {current_datetime.strftime('%Y-%m-%d %H:%M:%S')}"
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

    while True:
        schedule.run_pending()
        time.sleep(1)
