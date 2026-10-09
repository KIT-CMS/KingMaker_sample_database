#!/usr/bin/env python3
"""
Build the per-nick normalisation tables (norm_table.json, lhe_scale_table.json) read by the CROWN friends.
Run on demand after changing the sample database: python -m samplemanager.scripts.build_norm_table
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
from pathlib import Path

from samplemanager import ROOT_DIR


# Set up logger
logger = logging.getLogger(__name__)

# Default values of command-line arguments
DEFAULT_OUTPUT_DIR = ROOT_DIR / "norm_tables"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the normalisation tables from the sample database.")
    parser.add_argument("--sample-database-dir", type=Path, default=ROOT_DIR, help="Sample database root.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Where the tables are written.")
    parser.add_argument(
        "--allow-missing-stxs",
        action="store_true",
        help="Build without aux_data/stxs_nick_table.json (STXS signals then get no STXS normalisation).",
    )
    return parser.parse_args()


def main(sample_database_dir: Path, output_dir: Path, allow_missing_stxs: bool) -> None:
    table = {}
    for datasets_path in sample_database_dir.glob("*/datasets.json"):
        for entry in json.loads(datasets_path.read_text()).values():
            if None in (entry.get("xsec"), entry.get("nevents"), entry.get("generator_weight")):
                continue
            table[entry["nick"]] = {key: float(entry[key]) for key in ("xsec", "nevents", "generator_weight")}
    if not table:
        raise ValueError(f"No entries found under {sample_database_dir}")

    # recommended STXS xsec*B and per-bin factors of the signal nicks, from TAUER's analyses/smhtt/stxs_tools.py
    stxs_path = sample_database_dir / "aux_data" / "stxs_nick_table.json"
    if stxs_path.exists():
        for nick, stxs in json.loads(stxs_path.read_text()).items():
            if nick in table:
                table[nick].update(xsec=stxs["xsec"], stxs={"family": stxs["family"], "bins": stxs["bins"]})
    elif allow_missing_stxs:
        logger.warning(f"{stxs_path} missing: STXS signals get no STXS normalisation")
    else:
        raise FileNotFoundError(f"{stxs_path} missing: run `python -m analyses.smhtt.stxs_tools` in TAUER and copy it over")

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "norm_table.json").write_text(json.dumps(table))
    # LHEScaleWeight nuisance -> [family, HTXS bin] pairs, from TAUER's analyses/smhtt/stxs_tools.py
    shutil.copy(sample_database_dir / "aux_data" / "stxs_lhe_scale_table.json", output_dir / "lhe_scale_table.json")
    logger.info(f"Wrote {len(table)} nicks to {output_dir}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    args = parse_arguments()
    main(args.sample_database_dir, args.output_dir, args.allow_missing_stxs)
