"""Bring leads in from a CSV the operator made — no discovery, no key, no network.

    outfind import leads.csv

The keyless entry into the pipeline. An install without a BetterContact key cannot
search the licensed index, so discovery has nothing to feed it; this verb is how leads
arrive instead. They land exactly as a harvested page does — same ``profile_text``,
same embedding space, same dedupe — and the next ``find N`` qualifies them: LLM
verdicts, written reasons, the usual CSV on stdout. **Import stores; find judges.**

The columns are the export's own (`linkedin_url`, `first_name`, `last_name`, `title`,
`company`, `website`), with a few aliases, so a file from any source imports without a
mapping step — and `find 0 > leads.csv` fed back in skips every row it already holds.

This touches nothing but the database and the file it was given. It does not call
``check_ready``: importing is exactly the act an install without keys performs, so
demanding keys here would refuse the one configuration this verb exists for.
"""
from __future__ import annotations

import io
import json
import logging
import sys

from openoutfind.core.db.importing import ingest
from openoutfind.core.errors import ErrorType, OpenOutFindError
from openoutfind.core.management.base import OpenOutFindCommand
from openoutfind.core.management.bootstrap import ensure_database

logger = logging.getLogger(__name__)


class Command(OpenOutFindCommand):
    help = "Import leads from a CSV (linkedin_url + name/title/company) for the pipeline to qualify."

    # Like `find`: the verb that may find no schema and create it. Importing into a
    # fresh install is the ordinary first move of the keyless flow.
    requires_database = False

    def add_arguments(self, parser):
        parser.add_argument("file", metavar="PATH",
                            help="CSV carrying linkedin_url per row; name, title, "
                                 "company and website are used when present. The "
                                 "export's own columns are accepted as-is.")
        parser.add_argument("--json", action="store_true", dest="as_json",
                            help="The counts as one JSON object on stdout.")

    def handle(self, *args, **options):
        path = options["file"]
        try:
            handle = open(path, newline="", encoding="utf-8-sig")
        except OSError as exc:
            raise OpenOutFindError(ErrorType.BAD_CONFIG,
                                   f"cannot read {path}: {exc}") from None
        handle.close()

        self._configure_logging(quiet=options["as_json"])
        ensure_database(io.StringIO() if options["as_json"] else self.stderr)

        report = ingest(path)

        if options["as_json"]:
            sys.stdout.write(json.dumps({
                "rows": report.rows,
                "imported": report.created,
                "skipped": report.skipped,
                "invalid": report.invalid,
            }) + "\n")
            return

        # stdout is result-only: for the import verb the result is the counts.
        self.stdout.write(
            f"imported {report.created}, skipped {report.skipped}, "
            f"invalid {report.invalid} ({report.rows} row(s))")
        if report.created:
            logger.info("%d lead(s) stored and awaiting qualification — run `find N` to judge them",
                        report.created)

    def _configure_logging(self, *, quiet: bool = False):
        from openoutfind.core.logging import configure_logging

        if quiet:
            configure_logging(level=logging.CRITICAL + 1)
            return
        configure_logging()
