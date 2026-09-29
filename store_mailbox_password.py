#!/usr/bin/env python
"""Copy OUTSEND_MAILBOX_PASSWORD from .env into both installs' SiteConfig rows.

Run once after creating a Google app password. The value is read from .env
(gitignored) and written straight into the database — never echoed, never
passed on a command line, never stored in a shell history.
"""
import re
import sqlite3
import sys
from pathlib import Path

DBS = [
    Path.home() / ".openoutreach" / "data" / "db.sqlite3",
    Path.home() / ".openoutreach" / "data" / "communicate.sqlite3",
]


def main() -> int:
    env = Path(__file__).resolve().parent / ".env"
    match = re.search(
        r'^\s*OUTSEND_MAILBOX_PASSWORD\s*=\s*"?([^"\r\n]+)"?\s*$',
        env.read_text(encoding="utf-8"), re.MULTILINE)
    if not match or not match.group(1).strip():
        print("error: no OUTSEND_MAILBOX_PASSWORD=<value> line found in .env")
        return 1
    password = match.group(1).strip()

    for db in DBS:
        if not db.exists():
            print(f"skipped (no such database): {db}")
            continue
        con = sqlite3.connect(str(db))
        con.execute(
            "UPDATE openoutreach_config_siteconfig SET mailbox_password = ? WHERE id = 1",
            (password,))
        con.commit()
        con.close()
        print(f"stored: {db.name}")
    print("mailbox_password written to every row — value not shown.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
