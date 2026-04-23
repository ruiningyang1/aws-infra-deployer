"""
utils.py — Shared helpers for the pipeline deployment toolkit.
"""

import time
import functools
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


def retry(max_attempts: int = 3, delay: float = 2.0):
    """Decorator: retry a function on exception up to max_attempts times."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    logger.warning(f"Attempt {attempt}/{max_attempts} failed: {exc}")
                    if attempt < max_attempts:
                        time.sleep(delay)
                    else:
                        raise
        return wrapper
    return decorator


def format_artifact_key(version: str, local_path: str) -> str:
    """Build the S3 object key from version tag and local file name."""
    filename = os.path.basename(local_path)
    date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
    return f"artifacts/{date_prefix}/{version}/{filename}"


def sanitize_tag(tag: str) -> str:
    """Replace characters invalid in Docker/ECR tags."""
    return tag.replace("/", "-").replace(" ", "_").lower()


def parse_image_uri(uri: str) -> dict:
    """Parse an ECR URI into its component parts."""
    registry, rest = uri.split("/", 1)
    repo, tag = rest.rsplit(":", 1) if ":" in rest else (rest, "latest")
    return {"registry": registry, "repo": repo, "tag": tag}
