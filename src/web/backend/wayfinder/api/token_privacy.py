"""Keep share-link bearer tokens out of HTTP access logs."""
import logging
from urllib.parse import unquote


class ShareLinkAccessFilter(logging.Filter):
    def filter(self, record):
        # Uvicorn access records: client, method, request target, HTTP version, status.
        if isinstance(record.args, tuple) and len(record.args) == 5:
            target = str(record.args[2])
            for _ in range(3):
                target = unquote(target)
            if "/join/" in target:
                record.args = (*record.args[:2], "/[share-link-request]", *record.args[3:])
        return True


def install_share_link_log_filter():
    logger = logging.getLogger("uvicorn.access")
    if not any(isinstance(item, ShareLinkAccessFilter) for item in logger.filters):
        logger.addFilter(ShareLinkAccessFilter())
