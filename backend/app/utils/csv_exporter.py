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
            "city",
            "business_type",
            "priority",
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
                lead.city or "",
                lead.business_type or "",
                lead.priority_score,
            ]
        )

    return buffer.getvalue()
