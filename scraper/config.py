"""
RankUp AI — Global Configuration
=================================

Central configuration loaded from environment variables.
All scraper and LLM settings are defined here.
"""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)


def _env_str(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _env_int(key: str, default: int = 0) -> int:
    try:
        return int(os.environ.get(key, str(default)))
    except (ValueError, TypeError):
        return default


def _env_float(key: str, default: float = 0.0) -> float:
    try:
        return float(os.environ.get(key, str(default)))
    except (ValueError, TypeError):
        return default


@dataclass
class LLMSettings:
    """Settings for the LLM (DeepSeek V4 Flash via OpenAI-compatible API)."""
    
    # Support both OPENAI_API_KEY and OPENCODE_GO_API_KEY
    api_key: str = field(default_factory=lambda: _env_str("OPENAI_API_KEY", "") or _env_str("OPENCODE_GO_API_KEY", ""))
    base_url: str = field(default_factory=lambda: _env_str("LLM_BASE_URL", "https://opencode.ai/zen/go/v1"))
    model: str = field(default_factory=lambda: _env_str("LLM_MODEL", "deepseek-v4-flash"))
    temperature: float = field(default_factory=lambda: _env_float("LLM_TEMPERATURE", 0.3))
    max_tokens: int = field(default_factory=lambda: _env_int("LLM_MAX_TOKENS", 2500))  # Increased for DeepSeek V4 Flash reasoning (~1500) + content
    timeout: int = field(default_factory=lambda: _env_int("LLM_TIMEOUT", 120))


@dataclass
class ScraperSettings:
    """Settings for Playwright-based scraping."""

    headless: bool = field(default_factory=lambda: os.environ.get("SCRAPER_HEADLESS", "true").lower() == "true")
    navigation_timeout: int = field(default_factory=lambda: _env_int("SCRAPER_NAV_TIMEOUT", 60000))
    page_load_timeout: int = field(default_factory=lambda: _env_int("SCRAPER_PAGE_LOAD_TIMEOUT", 30000))
    min_delay: float = field(default_factory=lambda: _env_float("SCRAPER_MIN_DELAY", 1.5))
    max_delay: float = field(default_factory=lambda: _env_float("SCRAPER_MAX_DELAY", 4.0))
    retry_count: int = field(default_factory=lambda: _env_int("SCRAPER_RETRY_COUNT", 3))
    retry_delay: float = field(default_factory=lambda: _env_float("SCRAPER_RETRY_DELAY", 2.0))
    max_reviews_per_product: int = field(default_factory=lambda: _env_int("SCRAPER_MAX_REVIEWS", 100))
    viewport_width: int = field(default_factory=lambda: _env_int("SCRAPER_VIEWPORT_WIDTH", 1280))
    viewport_height: int = field(default_factory=lambda: _env_int("SCRAPER_VIEWPORT_HEIGHT", 800))


@dataclass
class ProxySettings:
    """Optional proxy configuration."""

    enabled: bool = field(default_factory=lambda: _env_str("PROXY_ENABLED", "false").lower() == "true")
    host: str = field(default_factory=lambda: _env_str("PROXY_HOST", ""))
    port: int = field(default_factory=lambda: _env_int("PROXY_PORT", 0))
    username: str = field(default_factory=lambda: _env_str("PROXY_USERNAME", ""))
    password: str = field(default_factory=lambda: _env_str("PROXY_PASSWORD", ""))

    @property
    def proxy_url(self) -> str | None:
        if not self.enabled or not self.host:
            return None
        if self.username and self.password:
            return f"http://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"http://{self.host}:{self.port}"


class Config:
    """Global configuration singleton for RankUp AI."""

    def __init__(self) -> None:
        self.llm = LLMSettings()
        self.scraper = ScraperSettings()
        self.proxy = ProxySettings()

        # Log level
        log_level_name = _env_str("LOG_LEVEL", "INFO").upper()
        self.log_level = getattr(logging, log_level_name, logging.INFO)

        # User agent rotation pool
        self.user_agents: List[str] = [
            # Chrome on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            # Chrome on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            # Edge on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
            # Firefox on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
            # Firefox on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.5; rv:125.0) Gecko/20100101 Firefox/125.0",
            # Safari on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
            # Chrome on Linux
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        ]

    def validate(self) -> None:
        """Check that required config values are set."""
        if not self.llm.api_key:
            logger.warning(
                "OPENAI_API_KEY is not set. LLM calls will fail until it is configured."
            )


# Global singleton
config = Config()

__all__ = ["config", "Config", "LLMSettings", "ScraperSettings", "ProxySettings"]
