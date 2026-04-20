"""CSV generation utilities for lead exports."""

from __future__ import annotations

import csv
import io

from app.schemas.lead import Lead


def leads_to_csv(leads: list[Lead]) -> str:
    """Convert lead records to CSV text."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "name",
            "address",
            "phone_number",
            "website",
            "email",
            "email_type",
            "email_confidence",
            "city",
            "business_type",
            "priority",
            "rating",
            "review_count",
            "summary",
            "sentiment",
            "recommended_action",
            "pitch",
        ]
    )
    for lead in leads:
        writer.writerow(
            [
                lead.name,
                lead.address or "",
                lead.phone_number or "",
                lead.website or "",
                lead.email or "",
                lead.email_type,
                lead.email_confidence,
                lead.city or "",
                lead.business_type or "",
                lead.priority_score,
                lead.rating if lead.rating is not None else "",
                lead.review_count,
                lead.business_summary,
                lead.customer_sentiment,
                lead.recommended_action,
                lead.pitch_suggestion,
            ]
        )

    return buffer.getvalue()
