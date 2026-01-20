import logging
import os  # must be independent of src.api.config

try:
    LOG_LEVEL = logging.getLevelNamesMapping().get(
        os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO
    )
except Exception:
    LOG_LEVEL = logging.INFO
logging.basicConfig(
    level=LOG_LEVEL,
    format="[%(asctime)s][%(levelname)s][%(name)s]%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)
logger.info("Logger initialized")
