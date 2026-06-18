"""
RankUp AI — Orchestrator Package
=================================

Coordinates data scraping, AI analysis, dashboard updates, and
notification delivery for RankUp AI TikTok Shop optimization.

Sub-modules:
  - pipeline:     RankUpPipeline — full, daily, and weekly workflows.
  - client_manager: ClientManager — client CRUD and config management.
  - scheduler:    Scheduler — APScheduler-based automation.
"""

from .pipeline import RankUpPipeline
from .client_manager import ClientManager
from .scheduler import Scheduler

__all__ = [
    "RankUpPipeline",
    "ClientManager",
    "Scheduler",
]
