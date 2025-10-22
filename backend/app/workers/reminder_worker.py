"""Scheduled worker for sending reminders"""

import time
import structlog
from datetime import datetime
from app.database import get_db_context
from app.agents.reminder import ReminderAgent

logger = structlog.get_logger()

# Run every 5 minutes
CHECK_INTERVAL_SECONDS = 300


def run_reminder_worker():
    """
    Background worker that periodically scans for pending reminders
    and sends them via appropriate channels.
    """
    logger.info("Reminder worker started", interval_seconds=CHECK_INTERVAL_SECONDS)

    while True:
        try:
            logger.info("Running reminder scan", time=datetime.utcnow().isoformat())

            with get_db_context() as db:
                reminder_agent = ReminderAgent(db)
                reminder_agent.scan_and_send_reminders()

            logger.info("Reminder scan completed successfully")

        except Exception as e:
            logger.error("Reminder worker error", error=str(e), exc_info=True)

        # Wait before next check
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_reminder_worker()
