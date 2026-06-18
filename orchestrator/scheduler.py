"""
RankUp AI — Scheduler
======================

Provides APScheduler-based scheduling for automated RankUp AI tasks:
  - Daily review scraping and classification
  - Weekly report generation and delivery

Supports persistent storage of job schedules via the client config
system and an optional SQLAlchemy job store.
"""

from __future__ import annotations

import logging
from datetime import datetime, time
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy APScheduler import with helpful error
# ---------------------------------------------------------------------------

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.jobstores.base import JobLookupError
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False

    # Stub classes so the module can be imported without APScheduler
    class AsyncIOScheduler:  # type: ignore[no-redef]
        def __getattr__(self, name: str) -> Any:
            raise ImportError(
                "APScheduler is required for the Scheduler. "
                "Install it with: pip install apscheduler"
            )

    class CronTrigger:  # type: ignore[no-redef]
        def __init__(self, **kwargs: Any) -> None:
            raise ImportError("APScheduler is required.")

    class JobLookupError(Exception):  # type: ignore[no-redef]
        pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_WEEKDAYS = {
    "monday": "mon",
    "tuesday": "tue",
    "wednesday": "wed",
    "thursday": "thu",
    "friday": "fri",
    "saturday": "sat",
    "sunday": "sun",
}


def _parse_time(time_str: str) -> time:
    """Parse a ``"HH:MM"`` string into a :class:`datetime.time`.

    Args:
        time_str: Time in 24-hour format (e.g., ``"09:00"``, ``"14:30"``).

    Returns:
        A :class:`~datetime.time` object.

    Raises:
        ValueError: If the string cannot be parsed.
    """
    parts = time_str.strip().split(":")
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0
    return time(hour=hour, minute=minute)


def _day_to_cron(day: str) -> str:
    """Convert a day name to a cron day-of-week expression.

    Args:
        day: Full day name (e.g., ``"monday"``, ``"tuesday"``).

    Returns:
        A three-letter cron expression (e.g., ``"mon"``).
    """
    return _WEEKDAYS.get(day.lower().strip(), "mon")


# ---------------------------------------------------------------------------
# Scheduler class
# ---------------------------------------------------------------------------

class Scheduler:
    """Cron-based scheduler for automated RankUp AI pipelines.

    Uses APScheduler's ``AsyncIOScheduler`` to run jobs in the same
    event loop as the rest of the application.

    Typical usage::

        scheduler = Scheduler()
        scheduler.start()

        # Schedule a daily scrape at 08:00
        scheduler.schedule_daily_scrape("client-abc", "08:00")

        # Schedule a weekly report on Mondays at 09:00
        scheduler.schedule_weekly_report("client-abc", "monday", "09:00")
    """

    def __init__(
        self,
        job_defaults: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the scheduler.

        Args:
            job_defaults: Optional dict of default job settings passed
                to APScheduler (e.g., ``{"coalesce": True, "max_instances": 1}``).
        """
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._started = False
        self._job_defaults: Dict[str, Any] = job_defaults or {
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 300,  # 5 minutes
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the APScheduler background scheduler.

        Safe to call multiple times — subsequent calls are no-ops.
        """
        if self._started:
            logger.debug("Scheduler already started.")
            return

        try:
            self._scheduler = AsyncIOScheduler(self._job_defaults)
            self._scheduler.start()
            self._started = True
            logger.info("RankUp AI scheduler started.")
        except Exception as exc:
            logger.error("Failed to start scheduler: %s", exc)
            raise RuntimeError(f"Scheduler start failed: {exc}") from exc

    def stop(self) -> None:
        """Stop the scheduler and remove all jobs."""
        if self._scheduler and self._started:
            self._scheduler.shutdown(wait=False)
            self._started = False
            logger.info("RankUp AI scheduler stopped.")

    def _ensure_running(self) -> None:
        """Ensure the scheduler is running before scheduling a job."""
        if not self._started:
            self.start()

    # ------------------------------------------------------------------
    # Schedule helpers
    # ------------------------------------------------------------------

    def schedule_daily_scrape(
        self,
        client_id: str,
        time_str: str = "08:00",
        pipeline_func: Optional[Callable] = None,
    ) -> str:
        """Schedule a daily review scraping job for a client.

        Args:
            client_id: The client identifier.
            time_str: Time of day in ``"HH:MM"`` format (default ``"08:00"``).
            pipeline_func: Async callable for the daily pipeline. If not
                provided, imports and uses
                :meth:`RankUpPipeline.run_daily_pipeline` at runtime.

        Returns:
            The APScheduler job ID string.
        """
        self._ensure_running()
        parsed = _parse_time(time_str)
        job_id = f"daily_scrape_{client_id}"

        trigger = CronTrigger(
            hour=parsed.hour,
            minute=parsed.minute,
        )

        async def _job() -> None:
            if pipeline_func:
                await pipeline_func(client_id)
            else:
                try:
                    from .pipeline import RankUpPipeline
                    pipeline = RankUpPipeline()
                    result = await pipeline.run_daily_pipeline(client_id)
                    status = result.get("status", "unknown")
                    logger.info(
                        "Scheduled daily scrape for %s completed: %s",
                        client_id, status,
                    )
                except Exception as exc:
                    logger.error(
                        "Scheduled daily scrape for %s failed: %s",
                        client_id, exc,
                    )

        # Remove existing job with same ID to allow rescheduling
        self.remove_job(job_id)

        self._scheduler.add_job(
            _job,
            trigger=trigger,
            id=job_id,
            name=f"Daily scrape — {client_id}",
            replace_existing=True,
        )

        logger.info(
            "Scheduled daily scrape for %s at %s (job: %s)",
            client_id, time_str, job_id,
        )
        return job_id

    def schedule_weekly_report(
        self,
        client_id: str,
        day: str = "monday",
        time_str: str = "09:00",
        pipeline_func: Optional[Callable] = None,
    ) -> str:
        """Schedule a weekly report generation job for a client.

        Args:
            client_id: The client identifier.
            day: Day of the week (e.g., ``"monday"``, ``"friday"``).
            time_str: Time of day in ``"HH:MM"`` format (default ``"09:00"``).
            pipeline_func: Async callable for the weekly pipeline. If not
                provided, uses :meth:`RankUpPipeline.run_weekly_pipeline`.

        Returns:
            The APScheduler job ID string.
        """
        self._ensure_running()
        parsed = _parse_time(time_str)
        cron_day = _day_to_cron(day)
        job_id = f"weekly_report_{client_id}"

        trigger = CronTrigger(
            day_of_week=cron_day,
            hour=parsed.hour,
            minute=parsed.minute,
        )

        async def _job() -> None:
            if pipeline_func:
                await pipeline_func(client_id)
            else:
                try:
                    from .pipeline import RankUpPipeline
                    pipeline = RankUpPipeline()
                    result = await pipeline.run_weekly_pipeline(client_id)
                    status = result.get("status", "unknown")
                    logger.info(
                        "Scheduled weekly report for %s completed: %s",
                        client_id, status,
                    )
                except Exception as exc:
                    logger.error(
                        "Scheduled weekly report for %s failed: %s",
                        client_id, exc,
                    )

        self.remove_job(job_id)

        self._scheduler.add_job(
            _job,
            trigger=trigger,
            id=job_id,
            name=f"Weekly report — {client_id}",
            replace_existing=True,
        )

        logger.info(
            "Scheduled weekly report for %s on %s at %s (job: %s)",
            client_id, day, time_str, job_id,
        )
        return job_id

    def get_schedule(
        self, client_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Return all scheduled jobs, optionally filtered by client.

        Args:
            client_id: If provided, only return jobs for this client.

        Returns:
            A list of job dicts with keys:
            ``id``, ``name``, ``next_run_time``, ``trigger``.
        """
        if not self._scheduler or not self._started:
            return []

        jobs = self._scheduler.get_jobs()
        result = []

        for job in jobs:
            job_id = str(job.id)
            # Filter by client ID if requested
            if client_id is not None and client_id not in job_id:
                continue

            next_run = job.next_run_time
            result.append({
                "id": job_id,
                "name": job.name,
                "next_run_time": next_run.isoformat() if next_run else None,
                "trigger": str(job.trigger),
            })

        return result

    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job.

        Args:
            job_id: The APScheduler job ID.

        Returns:
            True if the job was removed, False if it did not exist.
        """
        if not self._scheduler or not self._started:
            return False

        try:
            self._scheduler.remove_job(job_id)
            logger.debug("Removed job: %s", job_id)
            return True
        except JobLookupError:
            logger.debug("Job not found (already removed): %s", job_id)
            return False
        except Exception as exc:
            logger.warning("Failed to remove job %s: %s", job_id, exc)
            return False

    def clear_all_jobs(self) -> int:
        """Remove all scheduled jobs.

        Returns:
            Number of jobs removed.
        """
        if not self._scheduler or not self._started:
            return 0

        jobs = self._scheduler.get_jobs()
        count = len(jobs)
        for job in jobs:
            self.remove_job(job.id)
        logger.info("Cleared %d scheduled jobs.", count)
        return count

    # ------------------------------------------------------------------
    # Persist schedule to client config
    # ------------------------------------------------------------------

    @staticmethod
    def persist_schedule(
        client_id: str,
        daily_time: Optional[str] = None,
        weekly_day: Optional[str] = None,
        weekly_time: Optional[str] = None,
    ) -> bool:
        """Save schedule preferences to the client's config file.

        This stores the desired schedule times so they can be re-applied
        after a restart (e.g., via :meth:`restore_from_config`).

        Args:
            client_id: The client identifier.
            daily_time: Time for daily scrape (e.g., ``"08:00"``).
            weekly_day: Day for weekly report (e.g., ``"monday"``).
            weekly_time: Time for weekly report (e.g., ``"09:00"``).

        Returns:
            True if persisted successfully.
        """
        try:
            from .client_manager import ClientManager
            cm = ClientManager()
            updates: Dict[str, Any] = {}
            settings: Dict[str, Any] = {}

            if daily_time is not None:
                settings["daily_scrape_time"] = daily_time
            if weekly_day is not None:
                settings["weekly_report_day"] = weekly_day
            if weekly_time is not None:
                settings["weekly_report_time"] = weekly_time

            if settings:
                updates["settings"] = settings

            if updates:
                cm.update_client(client_id, updates)
                return True
            return False
        except Exception as exc:
            logger.error("Failed to persist schedule for %s: %s", client_id, exc)
            return False

    @staticmethod
    def restore_from_config(
        client_id: str,
        scheduler: Scheduler,
    ) -> Dict[str, Optional[str]]:
        """Restore scheduled jobs from a client's config file.

        Reads ``settings.daily_scrape_time``, ``settings.weekly_report_day``,
        and ``settings.weekly_report_time`` from the client config and
        recreates the corresponding scheduled jobs.

        Args:
            client_id: The client identifier.
            scheduler: An active :class:`Scheduler` instance.

        Returns:
            A dict mapping job type (``"daily"``, ``"weekly"``) to the
            scheduled job ID, or ``None`` if not configured.
        """
        from .client_manager import ClientManager
        cm = ClientManager()
        config = cm.get_client(client_id)

        if not config:
            logger.warning("Cannot restore schedule: client %s not found.", client_id)
            return {"daily": None, "weekly": None}

        settings = config.get("settings", {})
        result: Dict[str, Optional[str]] = {"daily": None, "weekly": None}

        daily_time = settings.get("daily_scrape_time")
        if daily_time:
            job_id = scheduler.schedule_daily_scrape(client_id, daily_time)
            result["daily"] = job_id

        weekly_day = settings.get("weekly_report_day")
        weekly_time = settings.get("weekly_report_time")
        if weekly_day and weekly_time:
            job_id = scheduler.schedule_weekly_report(
                client_id, day=weekly_day, time_str=weekly_time,
            )
            result["weekly"] = job_id

        return result


__all__ = ["Scheduler"]
