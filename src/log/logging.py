import logging
from colorlog import ColoredFormatter
from typing import Any, Optional
from pathlib import Path
from datetime import datetime


home_dir = Path.home()
log_file = (
    home_dir / f'social_media_jobs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
)

# Define custom log level for SUCCESS
SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")

# Define custom log level for HIGHLIGHT
HIGHLIGHT_LEVEL = 26
logging.addLevelName(HIGHLIGHT_LEVEL, "HIGHLIGHT")

LOG_LEVEL = logging.DEBUG
LOGFORMAT = (
    "  %(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
)

# Custom color configuration
LOG_COLORS = {
    "DEBUG": "cyan",
    "INFO": "white",  # Changed from default blue to normal gray/white
    "SUCCESS": "green",  # Custom success level with green color
    "HIGHLIGHT": "yellow",  # Custom highlight level with yellow color
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "red",
}

logging.root.setLevel(LOG_LEVEL)
formatter = ColoredFormatter(LOGFORMAT, log_colors=LOG_COLORS)
stream = logging.StreamHandler()
stream.setLevel(LOG_LEVEL)
stream.setFormatter(formatter)


# Create custom logger class with convenience methods
class CustomLogger(logging.Logger):

    # Log a success message with green color
    def success(self, message: str, *args: Any, **kwargs: Any) -> None:
        if self.isEnabledFor(SUCCESS_LEVEL):
            self._log(SUCCESS_LEVEL, message, args, **kwargs)

    # Log a debug message with cyan color
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        super().debug(message, *args, **kwargs)

    # Log an info message with white color
    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        super().info(message, *args, **kwargs)

    # Log a highlighted message with yellow color
    def highlight(self, message: str, *args: Any, **kwargs: Any) -> None:
        if self.isEnabledFor(HIGHLIGHT_LEVEL):
            self._log(HIGHLIGHT_LEVEL, message, args, **kwargs)

    # Log a warning message with yellow color
    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        super().warning(message, *args, **kwargs)

    # Log an error message with red color
    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        super().error(message, *args, **kwargs)

    # Log a critical message with red color
    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        super().critical(message, *args, **kwargs)


# Set the custom logger class
logging.setLoggerClass(CustomLogger)
logger: CustomLogger = logging.getLogger("pythonConfig")  # type: ignore
logger.setLevel(LOG_LEVEL)
logger.addHandler(stream)

# Add file handler to the custom logger
file_handler = logging.FileHandler(log_file)
file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(file_formatter)
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)
