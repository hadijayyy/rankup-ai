"""
RankUp AI — Report Formatter
=============================

Formats report data for different output channels:
  - HTML email
  - Slack markdown
  - WhatsApp plain text
  - Dashboard update dicts
"""

from __future__ import annotations

import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ReportFormatter:
    """Utility class for formatting report data across channels."""

    # ------------------------------------------------------------------
    # HTML Email report
    # ------------------------------------------------------------------

    @staticmethod
    def format_email_report(report_data: Dict[str, Any]) -> str:
        """Format a report as an HTML email string.

        Args:
            report_data: Dictionary with keys:
                - client_name (str)
                - report_type (str): "daily" | "weekly" | "monthly"
                - period_start (str): ISO date
                - period_end (str): ISO date
                - total_listings (int)
                - avg_listing_score (float)
                - listing_breakdown (list of dicts): each with product_name,
                  overall_score, status, suggestions
                - total_reviews (int)
                - positive_reviews (int)
                - negative_reviews (int)
                - neutral_reviews (int)
                - top_positive_review (dict): {text, product, date}
                - top_negative_review (dict): {text, product, date}
                - improvement_actions (list of str)
                - summary (str)

        Returns:
            An HTML string suitable for sending as an email body.
        """
        client_name = report_data.get("client_name", "Client")
        report_type = report_data.get("report_type", "weekly").capitalize()
        period_start = report_data.get("period_start", "")
        period_end = report_data.get("period_end", "")

        total_listings = report_data.get("total_listings", 0)
        avg_score = report_data.get("avg_listing_score", "N/A")
        total_reviews = report_data.get("total_reviews", 0)
        positive_reviews = report_data.get("positive_reviews", 0)
        negative_reviews = report_data.get("negative_reviews", 0)
        neutral_reviews = report_data.get("neutral_reviews", 0)
        improvement_actions = report_data.get("improvement_actions", [])
        summary = report_data.get("summary", "")

        # Listing breakdown table rows
        listing_rows_html = ""
        for listing in report_data.get("listing_breakdown", []):
            listing_rows_html += f"""
            <tr>
                <td style="padding:8px;border-bottom:1px solid #ddd;">{listing.get('product_name', 'N/A')}</td>
                <td style="padding:8px;border-bottom:1px solid #ddd;text-align:center;">{listing.get('overall_score', 'N/A')}</td>
                <td style="padding:8px;border-bottom:1px solid #ddd;text-align:center;">{listing.get('status', 'N/A')}</td>
                <td style="padding:8px;border-bottom:1px solid #ddd;">{listing.get('suggestions', '')}</td>
            </tr>"""

        # Improvement actions list
        actions_html = ""
        for action in improvement_actions:
            actions_html += f"<li style='margin-bottom:6px;'>{action}</li>"

        # Top reviews
        top_pos = report_data.get("top_positive_review", {})
        top_neg = report_data.get("top_negative_review", {})

        pos_review_html = ""
        if top_pos:
            pos_review_html = f"""
            <p><strong>"{top_pos.get('text', '')[:200]}"</strong></p>
            <p style="color:#666;">— {top_pos.get('product', '')} ({top_pos.get('date', '')})</p>"""

        neg_review_html = ""
        if top_neg:
            neg_review_html = f"""
            <p><strong>"{top_neg.get('text', '')[:200]}"</strong></p>
            <p style="color:#666;">— {top_neg.get('product', '')} ({top_neg.get('date', '')})</p>"""

        html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:Arial,Helvetica,sans-serif;color:#333;margin:0;padding:0;background-color:#f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f5f5f5;padding:20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background:linear-gradient(135deg,#667eea,#764ba2);padding:30px;text-align:center;">
                            <h1 style="color:#fff;margin:0;font-size:24px;">RankUp AI — {report_type} Report</h1>
                            <p style="color:rgba(255,255,255,0.85);margin:8px 0 0 0;">{client_name}</p>
                            <p style="color:rgba(255,255,255,0.7);margin:4px 0 0 0;font-size:13px;">
                                {period_start} — {period_end}
                            </p>
                        </td>
                    </tr>
                    <!-- Summary -->
                    <tr>
                        <td style="padding:25px 30px 15px 30px;">
                            <h2 style="font-size:18px;margin:0 0 10px 0;color:#444;">Executive Summary</h2>
                            <p style="line-height:1.6;color:#555;">{summary}</p>
                        </td>
                    </tr>
                    <!-- KPI Cards -->
                    <tr>
                        <td style="padding:0 30px 20px 30px;">
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td width="25%" style="padding:5px;">
                                        <div style="background:#e8f5e9;border-radius:6px;padding:15px;text-align:center;">
                                            <div style="font-size:28px;font-weight:bold;color:#2e7d32;">{total_listings}</div>
                                            <div style="font-size:12px;color:#555;">Listings</div>
                                        </div>
                                    </td>
                                    <td width="25%" style="padding:5px;">
                                        <div style="background:#e3f2fd;border-radius:6px;padding:15px;text-align:center;">
                                            <div style="font-size:28px;font-weight:bold;color:#1565c0;">{avg_score}</div>
                                            <div style="font-size:12px;color:#555;">Avg Score</div>
                                        </div>
                                    </td>
                                    <td width="25%" style="padding:5px;">
                                        <div style="background:#fff3e0;border-radius:6px;padding:15px;text-align:center;">
                                            <div style="font-size:28px;font-weight:bold;color:#e65100;">{total_reviews}</div>
                                            <div style="font-size:12px;color:#555;">Reviews</div>
                                        </div>
                                    </td>
                                    <td width="25%" style="padding:5px;">
                                        <div style="background:#fce4ec;border-radius:6px;padding:15px;text-align:center;">
                                            <div style="font-size:28px;font-weight:bold;color:#c62828;">{negative_reviews}</div>
                                            <div style="font-size:12px;color:#555;">Negatives</div>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- Review Sentiment -->
                    <tr>
                        <td style="padding:0 30px 20px 30px;">
                            <h3 style="font-size:15px;margin:0 0 8px 0;color:#444;">Review Sentiment</h3>
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td width="33%" style="padding:5px;">
                                        <div style="background:#c8e6c9;border-radius:4px;padding:10px;text-align:center;">
                                            <span style="font-size:20px;font-weight:bold;color:#2e7d32;">{positive_reviews}</span>
                                            <span style="font-size:12px;color:#555;"> Positive</span>
                                        </div>
                                    </td>
                                    <td width="33%" style="padding:5px;">
                                        <div style="background:#fff9c4;border-radius:4px;padding:10px;text-align:center;">
                                            <span style="font-size:20px;font-weight:bold;color:#f57f17;">{neutral_reviews}</span>
                                            <span style="font-size:12px;color:#555;"> Neutral</span>
                                        </div>
                                    </td>
                                    <td width="33%" style="padding:5px;">
                                        <div style="background:#ffcdd2;border-radius:4px;padding:10px;text-align:center;">
                                            <span style="font-size:20px;font-weight:bold;color:#c62828;">{negative_reviews}</span>
                                            <span style="font-size:12px;color:#555;"> Negative</span>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- Listing Breakdown -->
                    <tr>
                        <td style="padding:0 30px 20px 30px;">
                            <h3 style="font-size:15px;margin:0 0 8px 0;color:#444;">Listing Score Overview</h3>
                            <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
                                <thead>
                                    <tr style="background:#f0f0f0;">
                                        <th style="padding:8px;text-align:left;font-size:13px;border-bottom:2px solid #ddd;">Product</th>
                                        <th style="padding:8px;text-align:center;font-size:13px;border-bottom:2px solid #ddd;">Score</th>
                                        <th style="padding:8px;text-align:center;font-size:13px;border-bottom:2px solid #ddd;">Status</th>
                                        <th style="padding:8px;text-align:left;font-size:13px;border-bottom:2px solid #ddd;">Suggestions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {listing_rows_html if listing_rows_html else '<tr><td colspan="4" style="padding:12px;text-align:center;color:#999;">No listing data available.</td></tr>'}
                                </tbody>
                            </table>
                        </td>
                    </tr>
                    <!-- Top Reviews -->
                    <tr>
                        <td style="padding:0 30px 20px 30px;">
                            <h3 style="font-size:15px;margin:0 0 8px 0;color:#444;">Notable Reviews</h3>
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td width="50%" valign="top" style="padding:5px;">
                                        <div style="background:#f1f8e9;border-radius:6px;padding:12px;border-left:4px solid #2e7d32;">
                                            <p style="font-size:12px;color:#2e7d32;font-weight:bold;margin:0 0 5px 0;">★ Top Positive Review</p>
                                            {pos_review_html if pos_review_html else '<p style="color:#999;">No data</p>'}
                                        </div>
                                    </td>
                                    <td width="50%" valign="top" style="padding:5px;">
                                        <div style="background:#fce4ec;border-radius:6px;padding:12px;border-left:4px solid #c62828;">
                                            <p style="font-size:12px;color:#c62828;font-weight:bold;margin:0 0 5px 0;">★ Top Negative Review</p>
                                            {neg_review_html if neg_review_html else '<p style="color:#999;">No data</p>'}
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- Improvement Actions -->
                    <tr>
                        <td style="padding:0 30px 25px 30px;">
                            <h3 style="font-size:15px;margin:0 0 8px 0;color:#444;">Recommended Improvements</h3>
                            <ol style="margin:0;padding-left:20px;color:#555;line-height:1.6;">
                                {actions_html if actions_html else '<li style="color:#999;">No improvement suggestions at this time.</li>'}
                            </ol>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background:#f9f9f9;padding:20px 30px;text-align:center;border-top:1px solid #eee;">
                            <p style="font-size:12px;color:#999;margin:0;">
                                Generated by <strong>RankUp AI</strong> on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
                            </p>
                            <p style="font-size:11px;color:#bbb;margin:4px 0 0 0;">
                                This is an automated report. Replies are monitored.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
        return html

    # ------------------------------------------------------------------
    # Slack report
    # ------------------------------------------------------------------

    @staticmethod
    def format_slack_report(report_data: Dict[str, Any]) -> str:
        """Format a report as Slack markdown text.

        Args:
            report_data: Same format as :meth:`format_email_report`.

        Returns:
            A Slack-formatted message string with markdown.
        """
        client_name = report_data.get("client_name", "Client")
        report_type = report_data.get("report_type", "weekly").capitalize()
        period_start = report_data.get("period_start", "")
        period_end = report_data.get("period_end", "")
        summary = report_data.get("summary", "")

        total_listings = report_data.get("total_listings", 0)
        avg_score = report_data.get("avg_listing_score", "N/A")
        total_reviews = report_data.get("total_reviews", 0)
        positive_reviews = report_data.get("positive_reviews", 0)
        negative_reviews = report_data.get("negative_reviews", 0)
        neutral_reviews = report_data.get("neutral_reviews", 0)
        improvement_actions = report_data.get("improvement_actions", [])

        lines = [
            f"*RankUp AI — {report_type} Report*",
            f"*Client:* {client_name}",
            f"*Period:* {period_start} — {period_end}",
            "",
            f"*Summary*",
            summary,
            "",
            f"*KPIs*",
            f"• Listings: {total_listings}  |  Avg Score: {avg_score}",
            f"• Reviews: {total_reviews} (👍 {positive_reviews} / 😐 {neutral_reviews} / 👎 {negative_reviews})",
            "",
        ]

        # Listing breakdown
        listing_breakdown = report_data.get("listing_breakdown", [])
        if listing_breakdown:
            lines.append("*Listing Scores*")
            for listing in listing_breakdown:
                name = listing.get("product_name", "Unknown")
                score = listing.get("overall_score", "N/A")
                status = listing.get("status", "")
                suggestions = listing.get("suggestions", "")
                lines.append(f"  • *{name}* — Score: {score} ({status})")
                if suggestions:
                    lines.append(f"    └ {suggestions[:120]}")
            lines.append("")

        # Top reviews
        top_pos = report_data.get("top_positive_review", {})
        top_neg = report_data.get("top_negative_review", {})
        if top_pos:
            lines.append(f"*Top Positive Review*")
            lines.append(f"> {top_pos.get('text', '')[:200]}")
            lines.append(f"> — {top_pos.get('product', '')}")
            lines.append("")
        if top_neg:
            lines.append(f"*Top Negative Review*")
            lines.append(f"> {top_neg.get('text', '')[:200]}")
            lines.append(f"> — {top_neg.get('product', '')}")
            lines.append("")

        # Improvements
        if improvement_actions:
            lines.append("*Recommended Improvements*")
            for i, action in enumerate(improvement_actions, 1):
                lines.append(f"  {i}. {action}")
            lines.append("")

        lines.append(
            f"_Generated by RankUp AI — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}_"
        )

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # WhatsApp report
    # ------------------------------------------------------------------

    @staticmethod
    def format_whatsapp_report(report_data: Dict[str, Any]) -> str:
        """Format a report as plain text optimized for WhatsApp.

        Uses emojis and short lines for mobile readability.

        Args:
            report_data: Same format as :meth:`format_email_report`.

        Returns:
            A plain-text string suitable for WhatsApp.
        """
        client_name = report_data.get("client_name", "Client")
        report_type = report_data.get("report_type", "weekly").capitalize()
        period_start = report_data.get("period_start", "")
        period_end = report_data.get("period_end", "")
        summary = report_data.get("summary", "")

        total_listings = report_data.get("total_listings", 0)
        avg_score = report_data.get("avg_listing_score", "N/A")
        total_reviews = report_data.get("total_reviews", 0)
        positive_reviews = report_data.get("positive_reviews", 0)
        negative_reviews = report_data.get("negative_reviews", 0)
        neutral_reviews = report_data.get("neutral_reviews", 0)
        improvement_actions = report_data.get("improvement_actions", [])

        lines = [
            f"📊 *RankUp AI — {report_type} Report*",
            f"👤 {client_name}",
            f"📅 {period_start} to {period_end}",
            "",
            "━━━ Summary ━━━",
            summary,
            "",
            "━━━ KPIs ━━━",
            f"📦 Listings: {total_listings}  |  Avg Score: {avg_score}",
            f"⭐ Total Reviews: {total_reviews}",
            f"  👍 Positive: {positive_reviews}",
            f"  😐 Neutral: {neutral_reviews}",
            f"  👎 Negative: {negative_reviews}",
            "",
        ]

        listing_breakdown = report_data.get("listing_breakdown", [])
        if listing_breakdown:
            lines.append("━━━ Listings ━━━")
            for listing in listing_breakdown:
                name = listing.get("product_name", "Unknown")
                score = listing.get("overall_score", "N/A")
                status = listing.get("status", "")
                lines.append(f"• {name}: {score} ({status})")
            lines.append("")

        if improvement_actions:
            lines.append("━━━ Improvements ━━━")
            for action in improvement_actions:
                lines.append(f"✅ {action}")
            lines.append("")

        lines.append(
            f"🤖 Generated by RankUp AI — {datetime.utcnow().strftime('%b %d, %Y')}"
        )

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Dashboard update dict
    # ------------------------------------------------------------------

    @staticmethod
    def format_dashboard_update(
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format data as a dict suitable for updating a Sheets dashboard.

        This transforms raw analysis results into the column structure
        expected by the SheetsManager update methods.

        Args:
            update_data: Dictionary with keys:
                - listings (list of dict): raw listing analysis results
                - reviews (list of dict): raw review classification results
                - competitors (list of dict): raw competitor data
                - report (dict): report metadata

        Returns:
            A dict with keys 'listing_rows', 'review_rows',
            'competitor_rows', and optionally 'report_row', each being
            a list of lists (rows) ready for SheetsManager methods.
        """
        result: Dict[str, Any] = {}
        now_str = datetime.utcnow().isoformat()

        # Transform listings
        listings = update_data.get("listings", [])
        listing_rows = []
        for item in listings:
            suggestions = item.get("optimization_suggestions", "")
            if isinstance(suggestions, list):
                suggestions = "\n".join(suggestions)
            listing_rows.append([
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
        result["listing_rows"] = listing_rows

        # Transform reviews
        reviews = update_data.get("reviews", [])
        review_rows = []
        for item in reviews:
            review_rows.append([
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
        result["review_rows"] = review_rows

        # Transform competitors
        competitors = update_data.get("competitors", [])
        competitor_rows = []
        for item in competitors:
            competitor_rows.append([
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
        result["competitor_rows"] = competitor_rows

        # Report metadata
        report = update_data.get("report", {})
        if report:
            improvement = report.get("improvement_actions", "")
            if isinstance(improvement, list):
                improvement = "\n".join(improvement)
            result["report_row"] = [
                report.get("report_id", ""),
                report.get("report_type", ""),
                report.get("period_start", ""),
                report.get("period_end", ""),
                now_str,
                report.get("total_listings", 0),
                report.get("avg_listing_score", ""),
                report.get("total_reviews", 0),
                report.get("positive_reviews", 0),
                report.get("negative_reviews", 0),
                improvement,
                report.get("summary", ""),
            ]

        return result


__all__ = ["ReportFormatter"]
