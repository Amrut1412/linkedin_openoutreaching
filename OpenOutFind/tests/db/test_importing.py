# tests/db/test_importing.py
"""`outfind import` — the keyless entry into the pipeline.

The contract under test: an imported lead is indistinguishable from a harvested one to
everything downstream of discovery. Same `profile_text` shape the LLM judges, same
embedding space the GP scores, un-dealt so `fetch_qualification_candidates` picks it
up, deduped on `profile_url` so a re-import is a no-op. And no network anywhere: the
operator's file is the only source, which is the whole point of the verb.
"""
import io

import pytest
from django.core.management import call_command

from openoutfind.core.db.importing import ingest, row_for
from openoutfind.crm.models import Company, Deal, Lead

HEADERS = ["linkedin_url", "full_name", "title", "company", "website", "location"]


def _csv(tmp_path, rows, headers=HEADERS, name="leads.csv") -> str:
    path = tmp_path / name
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(row))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


@pytest.mark.django_db
class TestRowFor:
    def test_the_export_columns_map_onto_the_row_shape(self):
        row = row_for({
            "linkedin_url": "https://www.linkedin.com/in/someone/",
            "first_name": "Ada", "last_name": "Lovelace",
            "title": "Head of Support", "company": "Acme",
            "website": "https://www.acme.com/about", "reason": "ignored column",
        })

        assert row["contact_linkedin_profile_url"] == "https://www.linkedin.com/in/someone/"
        assert row["contact_full_name"] == "Ada Lovelace"
        assert row["contact_job_title"] == "Head of Support"
        assert row["company_name"] == "Acme"
        assert row["company_domain"] == "acme.com"
        assert "reason" not in row  # unknown columns change nothing

    def test_a_row_without_a_url_is_not_a_lead(self):
        assert row_for({"title": "Head of Support", "company": "Acme"}) is None

    def test_name_parts_join_when_the_file_split_them(self):
        row = row_for({"linkedin_url": "https://x", "first_name": "Ada",
                       "last_name": "Lovelace"})
        assert row["contact_full_name"] == "Ada Lovelace"


@pytest.mark.django_db
class TestIngest:
    def test_rows_become_embedded_un_dealt_leads(self, tmp_path):
        path = _csv(tmp_path, [[
            "https://www.linkedin.com/in/ada/", "Ada Lovelace", "Head of Support",
            "Acme", "acme.com", "United Kingdom",
        ]])

        report = ingest(path)

        assert (report.created, report.skipped, report.invalid) == (1, 0, 0)
        lead = Lead.objects.get(profile_url="https://www.linkedin.com/in/ada/")
        # What the LLM qualifier will read — the same flattened firmographics a
        # harvested row carries, built here from the file's columns.
        assert "head of support" in lead.profile_text
        assert "acme" in lead.profile_text
        assert lead.embedding is not None          # the GP can score it
        assert not Deal.objects.filter(lead=lead)  # and the next `find` will judge it
        assert lead.company.name == "Acme"
        assert lead.company.key == "acme.com"

    def test_a_reimport_is_a_no_op(self, tmp_path):
        rows = [["https://www.linkedin.com/in/ada/", "Ada Lovelace", "Head of Support",
                 "Acme", "acme.com", ""]]
        path = _csv(tmp_path, rows)

        first = ingest(path)
        second = ingest(path)

        assert (first.created, second.created, second.skipped) == (1, 0, 1)
        assert Lead.objects.count() == 1

    def test_rows_without_a_url_are_counted_and_dropped(self, tmp_path):
        path = _csv(tmp_path, [
            ["https://www.linkedin.com/in/ada/", "Ada", "", "", "", ""],
            ["", "", "Head of Support", "Acme", "", ""],
        ])

        report = ingest(path)

        assert (report.created, report.invalid, report.rows) == (1, 1, 2)

    def test_an_exported_file_round_trips_as_a_no_op(self, tmp_path):
        """`find 0 > leads.csv` fed back in skips everything it already holds."""
        from tests.factories import DealFactory, LeadFactory

        lead = LeadFactory(profile_url="https://www.linkedin.com/in/ada/")
        DealFactory(lead=lead)  # the export's shape implies a dealt lead
        path = _csv(
            tmp_path,
            [["", "Ada", "Lovelace", "Acme", "Head of Support", "acme.com",
              "https://www.linkedin.com/in/ada/", "a reason", "7", "today", "Ada L"]],
            headers=["email", "first_name", "last_name", "company", "title", "website",
                     "linkedin_url", "reason", "lead_id", "qualified_at", "full_name"],
        )

        report = ingest(path)

        assert (report.created, report.skipped) == (0, 1)

    def test_a_placeholder_company_makes_no_company_row(self, tmp_path):
        path = _csv(tmp_path, [[
            "https://www.linkedin.com/in/ada/", "Ada Lovelace", "Head of Support",
            "Stealth Startup", "", "",
        ]])

        ingest(path)

        assert Company.objects.count() == 0
        assert Lead.objects.get().company is None


@pytest.mark.django_db
class TestTheCommand:
    def test_the_summary_is_the_result_on_stdout(self, tmp_path):
        path = _csv(tmp_path, [[
            "https://www.linkedin.com/in/ada/", "Ada Lovelace", "Head of Support",
            "Acme", "", "",
        ]])
        out = io.StringIO()

        call_command("import", path, stdout=out)

        assert "imported 1, skipped 0, invalid 0 (1 row(s))" in out.getvalue()

    def test_json_gives_the_counts_as_one_object(self, tmp_path, capsys):
        path = _csv(tmp_path, [
            ["https://www.linkedin.com/in/ada/", "Ada", "", "", "", ""],
            ["", "", "X", "Y", "", ""],
        ])

        call_command("import", path, as_json=True)

        assert '{"rows": 2, "imported": 1, "skipped": 0, "invalid": 1}' in capsys.readouterr().out
