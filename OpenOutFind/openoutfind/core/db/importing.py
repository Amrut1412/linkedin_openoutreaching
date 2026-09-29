# openoutfind/core/db/importing.py
"""Bring leads in from a file the operator made, and let the pipeline judge them.

The discovery-free entry. Everything downstream of discovery — the GP, the LLM verdict,
the written reason, the export — works unchanged over imported rows, because they are
built by the same ``create_lead`` that harvests a Lead Finder page: same
``profile_text`` shape, same embedding space, same shared ``Company`` rows, same
``profile_url`` dedupe. The one thing import does not do is fetch: the operator's file
is the only source, so the pipeline's zero-ToS surface now covers a keyless install.

**The columns are the export's own**, plus a few obvious aliases, so a file moves
between tools without a mapping step — and an exported file fed back in is a clean
no-op: every row dedupes against the ``Lead`` already stored. Rows without a profile
URL are counted and dropped; URL-less rows cannot be keyed, and a lead that arrives as
an address alone is a discovery fact this path does not create.
"""
from __future__ import annotations

import csv
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# The CSV columns this reads, mapped to the Lead Finder row keys the persistence layer
# already speaks. First alias listed wins; unknown columns are ignored, which is what
# makes an export round-trip: `email`, `reason`, `lead_id` and `qualified_at` ride
# along and change nothing.
COLUMN_ALIASES = {
    "contact_linkedin_profile_url": ("linkedin_url", "profile_url", "url"),
    "contact_full_name": ("full_name",),
    "contact_first_name": ("first_name",),
    "contact_last_name": ("last_name",),
    "contact_job_title": ("title", "job_title"),
    "company_name": ("company", "company_name"),
    "company_domain": ("website", "domain", "company_domain"),
    "contact_location_country": ("location", "country"),
    "contact_headline": ("headline",),
    "contact_industry": ("industry",),
}


@dataclass
class ImportReport:
    """What one file did. The verb's whole result, in both its formats."""

    rows: int = 0            # data rows the file carried
    created: int = 0         # new Leads, embedded and awaiting qualification
    skipped: int = 0         # profile_url already stored — idempotent re-import
    invalid: int = 0         # no usable profile URL
    urls: list[str] = field(default_factory=list)  # created rows' URLs, in file order

    @property
    def changed(self) -> bool:
        return self.created > 0


def row_for(raw: dict) -> dict | None:
    """One CSV row as a Lead Finder-shaped row, or ``None`` when it names no profile."""
    lookup = {(key or "").strip().lower(): (value or "").strip()
              for key, value in raw.items()}
    row = {}
    for key, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if lookup.get(alias):
                row[key] = lookup[alias]
                break

    if not row.get("contact_linkedin_profile_url"):
        return None
    if not row.get("contact_full_name"):
        parts = " ".join(part for part in (row.get("contact_first_name"),
                                           row.get("contact_last_name")) if part)
        if parts:
            row["contact_full_name"] = parts
    domain = row.get("company_domain")
    if domain:
        row["company_domain"] = _bare_domain(domain)
    return row


def ingest(path: str | Path) -> ImportReport:
    """Read a CSV of leads into embedded, un-dealt Lead rows awaiting qualification.

    No LLM call and no network: the file becomes stored leads exactly as a harvested
    page does, and the *next* ``find`` puts them up for verdicts. Returns the counts
    the verb renders.
    """
    from openoutfind.core.db.leads import create_lead

    report = ImportReport()
    with open(path, newline="", encoding="utf-8-sig") as handle:
        for raw in csv.DictReader(handle):
            report.rows += 1
            row = row_for(raw)
            if row is None:
                logger.warning("row %d has no linkedin_url — skipped", report.rows)
                report.invalid += 1
                continue
            if create_lead(row):
                report.created += 1
                report.urls.append(row["contact_linkedin_profile_url"])
            else:
                report.skipped += 1
    return report


_SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*://", re.IGNORECASE)


def _bare_domain(value: str) -> str:
    """`https://www.acme.com/about` → `acme.com` — the shape Company keys on."""
    text = _SCHEME.sub("", value.strip()).strip("/")
    host = text.split("/", 1)[0]
    return host.removeprefix("www.")
