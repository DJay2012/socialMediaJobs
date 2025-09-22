import schedule
import time
from datetime import datetime
from log.logging import logger
from youtube.youtubeScraper import youtube_scraper
from enums.types import Platform

MINUTES_INTERVAL = 30


def run_job():
    logger.note(
        f"Starting: Youtube Scheduled job at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    try:
        # Run scraper for today's date range (automatically determined by the scraper)
        youtube_scraper(Platform.YOUTUBE_BMW)
        logger.note(
            f"Completed: Youtube Scheduled job at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    except Exception as e:
        logger.error(f"Error in scheduled job: {e}")


def RunMongoScheduler():
    logger.note(f"Job will run every {MINUTES_INTERVAL} minutes")

    run_job()
    schedule.every(MINUTES_INTERVAL).minutes.do(run_job)

    # This loop keeps the scheduler running indefinitely, checking every second
    # if any scheduled jobs are due to run, and executes them when needed.
    while True:
        schedule.run_pending()  # Run any jobs that are scheduled to run
        time.sleep(1)  # Wait for 1 second before checking again


if __name__ == "__main__":
    RunMongoScheduler()
