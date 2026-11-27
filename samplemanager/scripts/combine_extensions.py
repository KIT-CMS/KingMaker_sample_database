#!/usr/bin/env python3
"""
Normalise the extensions of the MC samples (same primary dataset, era and processing, `_extN` or not) together: every
nick of a group gets the summed nevents and the combined generator_weight, so CROWN's xsec / nevents * sign(genWeight)
/ generator_weight sums to the xsec over the whole group, which then has to be used complete (TAUER checks it).
The per-sample values are kept in nevents_sample / generator_weight_sample, rerun after changing them.
Example: python -m samplemanager.scripts.combine_extensions --database-folder nanoAOD_v15 (all groups, or --nicks <regex>)
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from collections import defaultdict
from pathlib import Path

from samplemanager import ROOT_DIR
from samplemanager.helpers import filelist_path, update_sample_fields


# Set up logger
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalise the extensions of MC samples together in the sample database.")
    parser.add_argument("--database-folder", type=Path, required=True, help="Database version folder, e.g. nanoAOD_v15.")
    parser.add_argument("--nicks", default=".", help="Regex selecting the groups (searched in the nicks of the group), default all.")
    parser.add_argument("--dry-run", action="store_true", help="Only print the groups and the new values.")
    return parser.parse_args()


def extension_groups(database: dict, pattern: str) -> list[list[str]]:
    """Nicks per (primary dataset, era, processing without _extN and version) with an extension, matching `pattern`."""
    groups = defaultdict(list)
    for nick, info in database.items():
        if info["sample_type"] != "data" and info["dbs"] and re.search(pattern, nick):
            primary, processed = info["dbs"].strip("/").split("/")[:2]
            groups[primary, str(info["era"]), re.sub(r"-v\d+$", "", re.sub(r"_ext\d+", "", processed))].append(nick)
    groups = [sorted(nicks) for nicks in groups.values() if len(nicks) > 1 and any("_ext" in n for n in nicks)]
    for nicks in groups:
        tags = [re.search(r"(_ext\d+)?-v\d+$", database[n]["dbs"].split("/")[2]).group(1) for n in nicks]
        if len(set(tags)) != len(tags):
            raise ValueError(f"two versions of the same sample in one group, keep one: {nicks}")
        if len({database[n]["sample_type"] for n in nicks}) > 1:
            raise ValueError(f"different sample types in one group, use the one of the base sample: {nicks}")
    return groups


def main(database_folder: Path, pattern: str, dry_run: bool) -> None:
    database_folder = database_folder if database_folder.is_absolute() else ROOT_DIR / database_folder
    database = json.loads((database_folder / "datasets.json").read_text())
    fields = {}
    for nicks in extension_groups(database, pattern):
        sample = {n: (database[n].get("nevents_sample", database[n]["nevents"]), database[n].get("generator_weight_sample", database[n]["generator_weight"])) for n in nicks}
        nevents = sum(n for n, _ in sample.values())
        generator_weight = sum(n * g for n, g in sample.values()) / nevents
        logger.info(f"{len(nicks)} nicks, nevents {nevents}, generator_weight {generator_weight:.5f}: {nicks[0]}")
        fields |= {
            n: {"nevents": nevents, "generator_weight": generator_weight, "nevents_sample": sample[n][0], "generator_weight_sample": sample[n][1], "extensions": nicks}
            for n in nicks
        }
    missing = [n for n in fields if not Path(filelist_path(str(database_folder), database[n])).exists()]
    if missing:
        raise RuntimeError(f"no per-sample json for {missing}")
    if not dry_run and fields:
        update_sample_fields(str(database_folder), fields)
        # also the index: TAUER reads the groups from datasets.json
        raw = (database_folder / "datasets.json").read_text()
        database = json.loads(raw)
        database |= {n: dict(sorted({**database[n], **values}.items())) for n, values in fields.items()}
        (database_folder / "datasets.json").write_text(json.dumps(database, indent=4) + ("\n" if raw.endswith("\n") else ""))
    logger.info(f"{'Would write' if dry_run else 'Wrote'} the combined normalisation of {len(fields)} nicks")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    args = parse_arguments()
    main(args.database_folder, args.nicks, args.dry_run)
