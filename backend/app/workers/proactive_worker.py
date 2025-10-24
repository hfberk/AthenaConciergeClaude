"""Scheduled worker for sending proactive messages and recommendations"""

import time
import structlog
from datetime import datetime
from app.database import get_db_context
from app.agents.proactive import ProactiveAgent
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


def run_proactive_worker():
    """
    Background worker that periodically scans for proactive messaging opportunities.
    Runs once per day by default (configurable via PROACTIVE_CHECK_INTERVAL env var).
    """
    check_interval = settings.proactive_check_interval
    logger.info("Proactive worker started", interval_seconds=check_interval)

    while True:
        try:
            logger.info("Running proactive message scan", time=datetime.utcnow().isoformat())

            with get_db_context() as db:
                proactive_agent = ProactiveAgent(db)
                proactive_agent.scan_and_send_proactive_messages()

            logger.info("Proactive message scan completed successfully")

        except Exception as e:
            logger.error("Proactive worker error", error=str(e), exc_info=True)

        # Wait before next check
        logger.info(
            "Proactive worker sleeping",
            next_run_in_seconds=check_interval
        )
        time.sleep(check_interval)


if __name__ == "__main__":
    run_proactive_worker()
