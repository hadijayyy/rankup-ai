"""
RankUp AI — Client Manager
===========================

Manages client configuration: creation, retrieval, listing, and updates.
Each client has a dedicated config file under ``data/clients/{client_id}/config.yaml``.
"""

from __future__ import annotations

import logging
import os
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Path where client data is stored
DATA_ROOT = os.environ.get(
    "RANKUP_DATA_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"),
)


def _sanitize_client_id(name: str) -> str:
    """Generate a safe filesystem-friendly client ID from a name.

    Args:
        name: The client name.

    Returns:
        A lowercase, dash-separated string safe for use in paths.
    """
    sanitized = re.sub(r"[^a-zA-Z0-9-]", "-", name.lower()).strip("-")
    return sanitized or "client"


def _clients_dir() -> str:
    """Return the path to the clients data directory."""
    return os.path.join(DATA_ROOT, "clients")


def _client_dir(client_id: str) -> str:
    """Return the directory path for a specific client."""
    return os.path.join(_clients_dir(), client_id)


def _config_path(client_id: str) -> str:
    """Return the config file path for a specific client."""
    return os.path.join(_client_dir(client_id), "config.yaml")


# ---------------------------------------------------------------------------
# In-memory fallback for YAML (uses simple dict if pyyaml unavailable)
# ---------------------------------------------------------------------------

try:
    import yaml

    def _yaml_dump(data: Any, path: str) -> None:
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def _yaml_load(path: str) -> Any:
        with open(path) as f:
            return yaml.safe_load(f) or {}

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    import json

    def _yaml_dump(data: Any, path: str) -> None:
        # Fallback: write as JSON (still usable)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def _yaml_load(path: str) -> Any:
        with open(path) as f:
            content = f.read().strip()
            if not content:
                return {}
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Minimal YAML key-value parser for simple configs
                result: Dict[str, Any] = {}
                for line in content.splitlines():
                    line = line.strip()
                    if ":" in line and not line.startswith("#"):
                        key, _, value = line.partition(":")
                        result[key.strip()] = value.strip().strip('"').strip("'")
                return result

    logger.warning("PyYAML not installed. Using JSON as fallback for client configs.")


class ClientManager:
    """Manages client setup, configuration, and lifecycle."""

    def __init__(self) -> None:
        self._cache: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Add client
    # ------------------------------------------------------------------

    def add_client(
        self,
        name: str,
        tiktok_shop_url: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> str:
        """Register a new client and create their config.

        Creates the client directory and ``config.yaml`` file with a
        unique client ID, stores creation timestamp, and sets status
        to ``active``.

        Args:
            name: Client's display name.
            tiktok_shop_url: URL of the client's TikTok Shop.
            email: Client's contact email (optional).
            phone: Client's contact phone number (optional).

        Returns:
            The newly created client ID string.

        Raises:
            ValueError: If name or tiktok_shop_url is empty.
            RuntimeError: If the client directory cannot be created.
        """
        if not name or not name.strip():
            raise ValueError("Client name cannot be empty.")
        if not tiktok_shop_url or not tiktok_shop_url.strip():
            raise ValueError("TikTok Shop URL cannot be empty.")

        # Generate a unique client ID
        base_id = _sanitize_client_id(name)
        client_id = f"{base_id}-{uuid.uuid4().hex[:8]}"

        client_dir = _client_dir(client_id)
        try:
            os.makedirs(client_dir, exist_ok=True)
        except OSError as exc:
            raise RuntimeError(
                f"Failed to create client directory at {client_dir}: {exc}"
            ) from exc

        config: Dict[str, Any] = {
            "client_id": client_id,
            "name": name.strip(),
            "tiktok_shop_url": tiktok_shop_url.strip(),
            "email": email.strip() if email else "",
            "phone": phone.strip() if phone else "",
            "sheets_id": "",
            "created_at": datetime.utcnow().isoformat(),
            "status": "active",
            "settings": {
                "scrape_interval_hours": 24,
                "review_limit": 100,
                "report_day": "monday",
                "report_time": "09:00",
                "notify_email": True,
                "notify_whatsapp": False,
            },
        }

        try:
            _yaml_dump(config, _config_path(client_id))
        except OSError as exc:
            raise RuntimeError(
                f"Failed to write config for client {client_id}: {exc}"
            ) from exc

        self._cache[client_id] = config
        logger.info(
            "Added client '%s' (ID: %s) with shop URL: %s",
            name, client_id, tiktok_shop_url,
        )
        return client_id

    # ------------------------------------------------------------------
    # Get client
    # ------------------------------------------------------------------

    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Load a client's configuration.

        Args:
            client_id: The unique client identifier.

        Returns:
            A dictionary with the client's config, or ``None`` if not found.
        """
        # Check cache first
        if client_id in self._cache:
            return dict(self._cache[client_id])

        config_path = _config_path(client_id)
        if not os.path.isfile(config_path):
            logger.warning("Client config not found: %s", config_path)
            return None

        try:
            config = _yaml_load(config_path)
            self._cache[client_id] = config
            return dict(config)
        except Exception as exc:
            logger.error(
                "Failed to load client config %s: %s", config_path, exc
            )
            return None

    # ------------------------------------------------------------------
    # List clients
    # ------------------------------------------------------------------

    def list_clients(self) -> List[Dict[str, Any]]:
        """Return all registered clients.

        Scans the ``data/clients/`` directory for config files.

        Returns:
            A list of client config dictionaries, each containing at
            minimum ``client_id``, ``name``, and ``status``.
        """
        clients: List[Dict[str, Any]] = []
        clients_root = _clients_dir()

        if not os.path.isdir(clients_root):
            logger.info("Clients directory does not exist yet: %s", clients_root)
            return clients

        try:
            for entry in os.listdir(clients_root):
                client_dir = os.path.join(clients_root, entry)
                if not os.path.isdir(client_dir):
                    continue
                config_path = os.path.join(client_dir, "config.yaml")
                if not os.path.isfile(config_path):
                    continue
                try:
                    config = _yaml_load(config_path)
                    if config.get("client_id"):
                        self._cache[config["client_id"]] = config
                        clients.append(config)
                except Exception as exc:
                    logger.warning(
                        "Skipping invalid client config at %s: %s",
                        config_path, exc,
                    )
        except OSError as exc:
            logger.error("Failed to list clients: %s", exc)

        logger.info("Found %d registered clients.", len(clients))
        return clients

    # ------------------------------------------------------------------
    # Update client
    # ------------------------------------------------------------------

    def update_client(
        self,
        client_id: str,
        updates: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Update a client's configuration fields.

        Only the keys provided in ``updates`` are modified. The
        ``client_id`` field cannot be changed.

        Args:
            client_id: The unique client identifier.
            updates: Dictionary of fields to update (e.g., ``{"name": ...,
                "email": ..., "phone": ..., "status": ..., "sheets_id": ...,
                "settings": {...}}``).

        Returns:
            The updated config dict, or ``None`` if the client was not found.

        Raises:
            ValueError: If attempting to change ``client_id``.
        """
        if "client_id" in updates:
            raise ValueError("Cannot change the client_id of an existing client.")

        config = self.get_client(client_id)
        if config is None:
            logger.warning("Cannot update unknown client: %s", client_id)
            return None

        # Apply updates
        for key, value in updates.items():
            if key == "settings" and isinstance(value, dict):
                existing_settings = config.get("settings", {})
                existing_settings.update(value)
                config["settings"] = existing_settings
            else:
                config[key] = value

        config["updated_at"] = datetime.utcnow().isoformat()

        try:
            _yaml_dump(config, _config_path(client_id))
            self._cache[client_id] = config
            logger.info("Updated client %s: %s", client_id, set(updates.keys()))
        except OSError as exc:
            raise RuntimeError(
                f"Failed to write updated config for {client_id}: {exc}"
            ) from exc

        return dict(config)

    # ------------------------------------------------------------------
    # Delete client
    # ------------------------------------------------------------------

    def delete_client(self, client_id: str) -> bool:
        """Remove a client's configuration and data directory.

        Args:
            client_id: The unique client identifier.

        Returns:
            True if the client was deleted, False if not found.
        """
        client_dir = _client_dir(client_id)
        if not os.path.isdir(client_dir):
            logger.warning("Client directory not found: %s", client_dir)
            return False

        try:
            import shutil
            shutil.rmtree(client_dir)
            self._cache.pop(client_id, None)
            logger.info("Deleted client %s and its data directory.", client_id)
            return True
        except OSError as exc:
            logger.error("Failed to delete client %s: %s", client_id, exc)
            raise RuntimeError(
                f"Failed to delete client {client_id}: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Convenience: get/set sheets_id
    # ------------------------------------------------------------------

    def set_sheets_id(self, client_id: str, sheets_id: str) -> bool:
        """Store a Google Sheets ID for the client.

        Args:
            client_id: The unique client identifier.
            sheets_id: The Google Sheets spreadsheet ID.

        Returns:
            True on success.
        """
        result = self.update_client(client_id, {"sheets_id": sheets_id})
        return result is not None

    def get_sheets_id(self, client_id: str) -> Optional[str]:
        """Retrieve the Google Sheets ID for a client.

        Args:
            client_id: The unique client identifier.

        Returns:
            The sheets ID string, or ``None``.
        """
        config = self.get_client(client_id)
        if config:
            return config.get("sheets_id") or None
        return None


__all__ = ["ClientManager"]
