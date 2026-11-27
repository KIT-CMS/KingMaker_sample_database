#!/usr/bin/env python3
"""
Write the per-bin STXS factors of the signal nicks (`stxs`: family and {htxs_bin: [norm, R_up, R_down]}),
from TAUER's analyses/smhtt/common/stxs_tools.py, into the sample database.
Run after updating the nick table: python -m samplemanager.scripts.stxs_normalization
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from samplemanager import ROOT_DIR
from samplemanager.helpers import update_sample_fields


# Set up logger
logger = logging.getLogger(__name__)

# Default values of command-line arguments
DEFAULT_NICK_TABLE = ROOT_DIR / "aux_data" / "stxs_nick_table.json"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write the STXS normalisation of the signal nicks into the sample database.")
    parser.add_argument("--sample-database-dir", type=Path, default=ROOT_DIR, help="Sample database root.")
    parser.add_argument("--nick-table", type=Path, default=DEFAULT_NICK_TABLE, help="STXS nick table of stxs_tools.py.")
    return parser.parse_args()


def main(sample_database_dir: Path, nick_table: Path) -> None:
    fields = {
        nick: {"stxs": {"bins": stxs["bins"], "family": stxs["family"]}}
        for nick, stxs in json.loads(nick_table.read_text()).items()
    }
    written = set()
    for database_folder in sorted(sample_database_dir.glob("nanoAOD_*")):
        written |= set(fields) - set(update_sample_fields(str(database_folder), fields))
    if set(fields) - written:
        logger.warning(f"{len(set(fields) - written)} nicks of the nick table not in any database, e.g. {sorted(set(fields) - written)[:3]}")
    logger.info(f"Wrote the STXS normalisation of {len(written)} nicks to the sample database")
    for nick in sorted(written):
        logger.info(f"{nick}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    args = parse_arguments()
    main(args.sample_database_dir, args.nick_table)
