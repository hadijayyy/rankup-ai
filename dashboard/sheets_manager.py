"""
RankUp AI — Google Sheets Manager
==================================

Provides integration with Google Sheets for storing and retrieving
client listing, review, report, and competitor data.

Uses gspread library with a service account loaded from the
GOOGLE_SERVICE_ACCOUNT_JSON environment variable.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import gspread
from gspread import Worksheet, Spreadsheet
from gspread.utils import rowcol_to_a1

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column definitions for each sheet tab
# ---------------------------------------------------------------------------

_LISTING_HEADERS = [
    "Product ID",
    "Product Name",
    "URL",
    "Price",
    "Category",
    "Sales Count",
    "Rating",
    "Status",
    "Title Score",
    "Description Score",
    "Image Score",
    "Overall Score",
    "Optimization Suggestions",
    "Last Updated",
]

_REVIEW_HEADERS = [
    "Review ID",
    "Product ID",
    "Product Name",
    "Rating",
    "Review Text",
    "Reviewer",
    "Date",
    "Sentiment",
    "Category",
    "Reply Status",
    "Draft Reply",
    "Last Updated",
]

_REPORT_HEADERS = [
    "Report ID",
    "Report Type",
    "Period Start",
    "Period End",
    "Generated At",
    "Total Listings",
    "Avg Listing Score",
    "Total Reviews",
    "Positive Reviews",
    "Negative Reviews",
    "Improvement Actions",
    "Summary",
]

_COMPETITOR_HEADERS = [
    "Competitor ID",
    "Competitor Name",
    "Shop URL",
    "Product Count",
    "Top Product",
    "Avg Price",
    "Avg Rating",
    "Total Sales",
    "Last Scraped",
]


class SheetsManager:
    """Manages Google Sheets integration for RankUp AI client data."""

    def __init__(self) -> None:
        self._client: Optional[gspread.Client] = None
        self._service_account_json: Optional[str] = os.environ.get(
            "GOOGLE_SERVICE_ACCOUNT_JSON"
        )

    # ------------------------------------------------------------------
    # Auth helpers
    # ------------------------------------------------------------------

    def _get_client(self) -> gspread.Client:
        """Authenticate and return a gspread client.

        Returns:
            Authenticated gspread Client instance.

        Raises:
            RuntimeError: If GOOGLE_SERVICE_ACCOUNT_JSON is not set.
            gspread.exceptions.GSpreadException: On auth failure.
        """
        if self._client is not None:
            return self._client

        if not self._service_account_json:
            raise RuntimeError(
                "GOOGLE_SERVICE_ACCOUNT_JSON environment variable is not set. "
                "Cannot authenticate with Google Sheets."
            )

        try:
            creds_dict = json.loads(self._service_account_json)
            self._client = gspread.service_account_from_dict(creds_dict)
            logger.info("Authenticated with Google Sheets service account.")
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON."
            ) from exc
        except Exception as exc:
            raise RuntimeError(
                f"Failed to authenticate with Google Sheets: {exc}"
            ) from exc

        return self._client

    def _ensure_auth(self) -> None:
        """Ensure authentication is set up; raises if not possible."""
        self._get_client()

    # ------------------------------------------------------------------
    # Formatting helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_headers(worksheet: Worksheet, headers: List[str]) -> None:
        """Apply header formatting (bold, background color, freeze).

        Args:
            worksheet: The target worksheet.
            headers: List of header column names.
        """
        if not worksheet or not headers:
            return

        try:
            # Write headers
            worksheet.update(
                f"A1:{gspread.utils.rowcol_to_a1(1, len(headers))}",
                [headers],
            )

            # Format header row
            worksheet.format(
                f"A1:{gspread.utils.rowcol_to_a1(1, len(headers))}",
                {
                    "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2},
                    "textFormat": {
                        "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                        "bold": True,
                        "fontSize": 11,
                    },
                    "horizontalAlignment": "CENTER",
                },
            )

            # Freeze header row
            worksheet.freeze(rows=1)
        except Exception as exc:
            logger.warning("Failed to format headers: %s", exc)

    @staticmethod
    def _set_column_widths(
        worksheet: Worksheet, widths: Dict[str, int]
    ) -> None:
        """Set column widths for a worksheet.

        Args:
            worksheet: The target worksheet.
            widths: Mapping of column letter to width in pixels.
        """
        try:
            for col_letter, width in widths.items():
                worksheet.format(
                    f"{col_letter}:{col_letter}",
                    {"pixelSize": width},
                )
        except Exception as exc:
            logger.warning("Failed to set column widths: %s", exc)

    # ------------------------------------------------------------------
    # Spreadsheet creation
    # ------------------------------------------------------------------

    def create_client_sheet(self, client_name: str) -> str:
        """Create a new Google Sheets spreadsheet for a client.

        The spreadsheet includes four tabs:
          - Listings
          - Reviews
          - Reports
          - Competitors

        Args:
            client_name: The client's display name (used in the title).

        Returns:
            The spreadsheet ID (string).

        Raises:
            RuntimeError: If auth fails or sheet creation fails.
        """
        client = self._get_client()
        safe_name = client_name.replace(" ", "_").replace("/", "-")[:80]
        title = f"RankUp AI - {safe_name}"

        try:
            spreadsheet: Spreadsheet = client.create(title)
            sheet_id = str(spreadsheet.id)
            logger.info(
                "Created spreadsheet '%s' with ID: %s", title, sheet_id
            )

            # Rename default sheet and create additional tabs
            default_sheet = spreadsheet.sheet1
            default_sheet.update_title("Listings")

            spreadsheet.add_worksheet("Reviews", rows=100, cols=len(_REVIEW_HEADERS))
            spreadsheet.add_worksheet("Reports", rows=100, cols=len(_REPORT_HEADERS))
            spreadsheet.add_worksheet("Competitors", rows=100, cols=len(_COMPETITOR_HEADERS))

            # Format each tab
            for ws_name, headers, col_widths in [
                ("Listings", _LISTING_HEADERS, {
                    "A": 100, "B": 250, "C": 200, "D": 80, "E": 120,
                    "F": 90, "G": 70, "H": 80, "I": 90, "J": 100,
                    "K": 90, "L": 100, "M": 300, "N": 120,
                }),
                ("Reviews", _REVIEW_HEADERS, {
                    "A": 100, "B": 100, "C": 200, "D": 60, "E": 350,
                    "F": 120, "G": 100, "H": 80, "I": 100, "J": 90,
                    "K": 250, "L": 120,
                }),
                ("Reports", _REPORT_HEADERS, {
                    "A": 100, "B": 100, "C": 120, "D": 120, "E": 140,
                    "F": 100, "G": 110, "H": 100, "I": 110, "J": 110,
                    "K": 300, "L": 350,
                }),
                ("Competitors", _COMPETITOR_HEADERS, {
                    "A": 100, "B": 200, "C": 200, "D": 100,
                    "E": 200, "F": 80, "G": 80, "H": 100, "I": 120,
                }),
            ]:
                ws = spreadsheet.worksheet(ws_name)
                self._format_headers(ws, headers)
                self._set_column_widths(ws, col_widths)

            # Share access with the service account email (optional)
            try:
                if self._service_account_json:
                    creds_dict = json.loads(self._service_account_json)
                    if "client_email" in creds_dict:
                        spreadsheet.share(
                            creds_dict["client_email"],
                            perm_type="user",
                            role="writer",
                        )
            except Exception:
                pass  # Non-critical

            return sheet_id

        except Exception as exc:
            logger.error("Failed to create client sheet: %s", exc)
            raise RuntimeError(f"Failed to create spreadsheet: {exc}") from exc

    # ------------------------------------------------------------------
    # Data writing
    # ------------------------------------------------------------------

    def update_listing_data(
        self, sheet_id: str, listing_data: List[Dict[str, Any]]
    ) -> int:
        """Write listing analysis results to the Listings tab.

        Args:
            sheet_id: The Google Sheets spreadsheet ID.
            listing_data: A list of dictionaries, each containing listing fields
                (product_id, product_name, url, price, category, sales_count,
                rating, status, title_score, description_score, image_score,
                overall_score, optimization_suggestions).

        Returns:
            Number of rows written (excluding header).

        Raises:
            RuntimeError: If sheet access fails.
        """
        if not listing_data:
            logger.warning("No listing data to write.")
            return 0

        client = self._get_client()

        try:
            spreadsheet = client.open_by_key(sheet_id)
            ws = spreadsheet.worksheet("Listings")
        except Exception as exc:
            raise RuntimeError(
                f"Cannot access spreadsheet {sheet_id}: {exc}"
            ) from exc

        rows = []
        now_str = datetime.utcnow().isoformat()

        for item in listing_data:
            suggestions = item.get("optimization_suggestions", "")
            if isinstance(suggestions, list):
                suggestions = "\n".join(suggestions)

            rows.append([
                item.get("product_id", ""),
                item.get("product_name", ""),
                item.get("url", ""),
                item.get("price", ""),
                item.get("category", ""),
                item.get("sales_count", 0),
                item.get("rating", ""),
                item.get("status", ""),
                item.get("title_score", ""),
                item.get("description_score", ""),
                item.get("image_score", ""),
                item.get("overall_score", ""),
                suggestions,
                now_str,
            ])

        try:
            # Clear existing data (below header) and write new rows
            ws.batch_clear(["A2:N"])
            if rows:
                ws.update(
                    f"A2:{gspread.utils.rowcol_to_a1(len(rows) + 1, len(_LISTING_HEADERS))}",
                    rows,
                )
            logger.info(
                "Wrote %d listing rows to spreadsheet %s", len(rows), sheet_id
            )
            return len(rows)
        except Exception as exc:
            logger.error("Failed to write listing data: %s", exc)
            raise RuntimeError(f"Failed to write listing data: {exc}") from exc

    def update_review_data(
        self, sheet_id: str, review_data: List[Dict[str, Any]]
    ) -> int:
        """Write review data to the Reviews tab.

        Args:
            sheet_id: The Google Sheets spreadsheet ID.
            review_data: A list of dictionaries, each containing review fields
                (review_id, product_id, product_name, rating, review_text,
                reviewer, date, sentiment, category, reply_status, draft_reply).

        Returns:
            Number of rows written.

        Raises:
            RuntimeError: If sheet access fails.
        """
        if not review_data:
            logger.warning("No review data to write.")
            return 0

        client = self._get_client()

        try:
            spreadsheet = client.open_by_key(sheet_id)
            ws = spreadsheet.worksheet("Reviews")
        except Exception as exc:
            raise RuntimeError(
                f"Cannot access spreadsheet {sheet_id}: {exc}"
            ) from exc

        rows = []
        now_str = datetime.utcnow().isoformat()

        for item in review_data:
            rows.append([
                item.get("review_id", ""),
                item.get("product_id", ""),
                item.get("product_name", ""),
                item.get("rating", ""),
                item.get("review_text", ""),
                item.get("reviewer", ""),
                item.get("date", ""),
                item.get("sentiment", ""),
                item.get("category", ""),
                item.get("reply_status", "pending"),
                item.get("draft_reply", ""),
                now_str,
            ])

        try:
            ws.batch_clear(["A2:L"])
            if rows:
                ws.update(
                    f"A2:{gspread.utils.rowcol_to_a1(len(rows) + 1, len(_REVIEW_HEADERS))}",
                    rows,
                )
            logger.info(
                "Wrote %d review rows to spreadsheet %s", len(rows), sheet_id
            )
            return len(rows)
        except Exception as exc:
            logger.error("Failed to write review data: %s", exc)
            raise RuntimeError(f"Failed to write review data: {exc}") from exc

    def update_report_data(
        self, sheet_id: str, report_data: Dict[str, Any]
    ) -> bool:
        """Append a report row to the Reports tab.

        Args:
            sheet_id: The Google Sheets spreadsheet ID.
            report_data: Dictionary with keys: report_id, report_type,
                period_start, period_end, total_listings, avg_listing_score,
                total_reviews, positive_reviews, negative_reviews,
                improvement_actions, summary.

        Returns:
            True on success.

        Raises:
            RuntimeError: If sheet access fails.
        """
        client = self._get_client()

        try:
            spreadsheet = client.open_by_key(sheet_id)
            ws = spreadsheet.worksheet("Reports")
        except Exception as exc:
            raise RuntimeError(
                f"Cannot access spreadsheet {sheet_id}: {exc}"
            ) from exc

        improvement = report_data.get("improvement_actions", "")
        if isinstance(improvement, list):
            improvement = "\n".join(improvement)

        summary = report_data.get("summary", "")

        row = [
            report_data.get("report_id", ""),
            report_data.get("report_type", ""),
            report_data.get("period_start", ""),
            report_data.get("period_end", ""),
            datetime.utcnow().isoformat(),
            report_data.get("total_listings", 0),
            report_data.get("avg_listing_score", ""),
            report_data.get("total_reviews", 0),
            report_data.get("positive_reviews", 0),
            report_data.get("negative_reviews", 0),
            improvement,
            summary,
        ]

        try:
            ws.append_row(row)
            logger.info(
                "Appended report row to spreadsheet %s", sheet_id
            )
            return True
        except Exception as exc:
            logger.error("Failed to write report data: %s", exc)
            raise RuntimeError(f"Failed to write report data: {exc}") from exc

    def update_competitor_data(
        self, sheet_id: str, competitor_data: List[Dict[str, Any]]
    ) -> int:
        """Write competitor data to the Competitors tab.

        Args:
            sheet_id: The Google Sheets spreadsheet ID.
            competitor_data: A list of dictionaries with competitor fields
                (competitor_id, competitor_name, shop_url, product_count,
                top_product, avg_price, avg_rating, total_sales).

        Returns:
            Number of rows written.

        Raises:
            RuntimeError: If sheet access fails.
        """
        if not competitor_data:
            logger.warning("No competitor data to write.")
            return 0

        client = self._get_client()

        try:
            spreadsheet = client.open_by_key(sheet_id)
            ws = spreadsheet.worksheet("Competitors")
        except Exception as exc:
            raise RuntimeError(
                f"Cannot access spreadsheet {sheet_id}: {exc}"
            ) from exc

        rows = []
        now_str = datetime.utcnow().isoformat()

        for item in competitor_data:
            rows.append([
                item.get("competitor_id", ""),
                item.get("competitor_name", ""),
                item.get("shop_url", ""),
                item.get("product_count", 0),
                item.get("top_product", ""),
                item.get("avg_price", ""),
                item.get("avg_rating", ""),
                item.get("total_sales", 0),
                now_str,
            ])

        try:
            ws.batch_clear(["A2:I"])
            if rows:
                ws.update(
                    f"A2:{gspread.utils.rowcol_to_a1(len(rows) + 1, len(_COMPETITOR_HEADERS))}",
                    rows,
                )
            logger.info(
                "Wrote %d competitor rows to spreadsheet %s", len(rows), sheet_id
            )
            return len(rows)
        except Exception as exc:
            logger.error("Failed to write competitor data: %s", exc)
            raise RuntimeError(
                f"Failed to write competitor data: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Data reading
    # ------------------------------------------------------------------

    def get_client_dashboard(
        self, sheet_id: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Read all data from a client's spreadsheet.

        Args:
            sheet_id: The Google Sheets spreadsheet ID.

        Returns:
            A dictionary with keys 'listings', 'reviews', 'reports',
            'competitors', each containing a list of dicts.

        Raises:
            RuntimeError: If the sheet cannot be accessed.
        """
        client = self._get_client()

        try:
            spreadsheet = client.open_by_key(sheet_id)
        except Exception as exc:
            raise RuntimeError(
                f"Cannot access spreadsheet {sheet_id}: {exc}"
            ) from exc

        result: Dict[str, List[Dict[str, Any]]] = {
            "listings": [],
            "reviews": [],
            "reports": [],
            "competitors": [],
        }

        # Helper to convert a worksheet to a list of dicts
        def _read_worksheet(
            ws: Worksheet, headers: List[str]
        ) -> List[Dict[str, Any]]:
            try:
                records = ws.get_all_records()
                return records
            except Exception as exc:
                logger.warning(
                    "Failed to read worksheet '%s': %s", ws.title, exc
                )
                return []

        try:
            result["listings"] = _read_worksheet(
                spreadsheet.worksheet("Listings"), _LISTING_HEADERS
            )
        except Exception as exc:
            logger.warning("Could not read Listings tab: %s", exc)

        try:
            result["reviews"] = _read_worksheet(
                spreadsheet.worksheet("Reviews"), _REVIEW_HEADERS
            )
        except Exception as exc:
            logger.warning("Could not read Reviews tab: %s", exc)

        try:
            result["reports"] = _read_worksheet(
                spreadsheet.worksheet("Reports"), _REPORT_HEADERS
            )
        except Exception as exc:
            logger.warning("Could not read Reports tab: %s", exc)

        try:
            result["competitors"] = _read_worksheet(
                spreadsheet.worksheet("Competitors"), _COMPETITOR_HEADERS
            )
        except Exception as exc:
            logger.warning("Could not read Competitors tab: %s", exc)

        logger.info(
            "Read dashboard data from %s: %d listings, %d reviews, "
            "%d reports, %d competitors",
            sheet_id,
            len(result["listings"]),
            len(result["reviews"]),
            len(result["reports"]),
            len(result["competitors"]),
        )

        return result


__all__ = ["SheetsManager"]
