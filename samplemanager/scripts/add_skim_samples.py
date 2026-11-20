#!/usr/bin/env python3
"""
Add the HLepRare skims (TauPOG NanoProd re-NANO of MiniAODv4, one folder per sample with nano*.root and
prodReport*.json) of the nicks of a sample list to a new database version, e.g. the 2022/2023 skim_2025_v1 as nanoAOD_v14.
The skim folder of a nick is the one whose prodReport input dataset is the MiniAOD parent of the nick's dbs.
xsec, generator_weight (sign fraction of the same MiniAOD) and sample_type are taken from the nick, nevents is
the number of processed events of the reports (the genEventCount of the Runs trees). The new nick is <folder>_<era>.

    python -m samplemanager.scripts.add_skim_samples --sample-list ../samples_2022-23.txt
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from XRootD.client import File, FileSystem

from samplemanager import ROOT_DIR
from samplemanager.scripts.add_private_samples import Sample


# Set up logger
logger = logging.getLogger(__name__)

# Default values of command-line arguments
DEFAULT_REDIRECTOR = "root://eoscms.cern.ch/"
DEFAULT_SKIM_DIR = "/eos/cms/store/group/phys_higgs/HLepRare/skim_2025_v1"
DEFAULT_SOURCE_VERSION = "nanoAOD_v12"
DEFAULT_TARGET_VERSION = "nanoAOD_v14"
DASGOCLIENT = "/cvmfs/cms.cern.ch/common/dasgoclient"
ERA_DIRS = {"Run3_2022": "2022preEE", "Run3_2022EE": "2022postEE", "Run3_2023": "2023preBPix", "Run3_2023BPix": "2023postBPix"}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Add the HLepRare skims of the nicks of a sample list to the sample database.")
    parser.add_argument("--sample-list", type=Path, required=True, help="Nicks of the source database, one per line.")
    parser.add_argument("--skim-dir", default=DEFAULT_SKIM_DIR, help="Skim directory with one Run3_<era> folder per era.")
    parser.add_argument("--redirector", default=DEFAULT_REDIRECTOR)
    parser.add_argument("--source-version", default=DEFAULT_SOURCE_VERSION, help="Database of the nicks of the sample list.")
    parser.add_argument("--target-version", default=DEFAULT_TARGET_VERSION, help="Database the skims are added to.")
    parser.add_argument("--workers", type=int, default=16)
    return parser.parse_args()


def read_reports(redirector: str, skim_dir: str, workers: int) -> dict[tuple[str, str], list[dict]]:
    """{(era dir, folder): [prodReport, ...]} of all skim folders (several reports for folders split by flavour)."""
    fs = FileSystem(redirector)

    def listdir(path):
        status, listing = fs.dirlist(path)
        if not status.ok:
            raise RuntimeError(f"{path}: {status.message}")
        return [entry.name for entry in listing]

    def read(path):
        with File() as f:
            status, _ = f.open(redirector + path)
            if not status.ok:
                raise RuntimeError(f"{path}: {status.message}")
            return json.loads(f.read()[1])

    paths = [
        (era_dir, folder, f"{skim_dir}/{era_dir}/{folder}/{name}")
        for era_dir in ERA_DIRS
        for folder in listdir(f"{skim_dir}/{era_dir}")
        for name in listdir(f"{skim_dir}/{era_dir}/{folder}")
        if name.startswith("prodReport") and name.endswith(".json")
    ]
    reports = defaultdict(list)
    with ThreadPoolExecutor(workers) as pool:
        for (era_dir, folder, path), report in zip(paths, pool.map(lambda p: read(p[2]), paths)):
            reports[(era_dir, folder)].append(report)
    return reports


def miniaod_parent(dbs: str) -> str:
    # data NANOAOD has the MiniAOD of the same name as input (DAS gives the AOD of the prompt reco for some 2023 eras)
    if dbs.endswith("/NANOAOD"):
        return dbs[: -len("NANOAOD")] + "MINIAOD"
    output = subprocess.run([DASGOCLIENT, f"-query=parent dataset={dbs}"], capture_output=True, text=True, check=True).stdout.split()
    if len(output) != 1:
        raise RuntimeError(f"{dbs}: expected one parent, DAS gives {output}")
    return output[0]


def loose_key(dataset: str) -> tuple[str, str]:
    """Primary dataset and campaign of a MiniAOD dataset, to match skims of another version of it."""
    primary, processed = dataset.strip("/").split("/")[:2]
    return primary, processed.split("-")[0] + ("_ext" if "_ext" in processed else "")


def main(args: argparse.Namespace) -> None:
    source = json.loads((ROOT_DIR / args.source_version / "datasets.json").read_text())
    nicks = []
    for name in args.sample_list.read_text().split():
        # sample list names are nicks or their unique prefix, `_ext1` selecting the ext sample
        base, ext = (name[:-5], True) if name.endswith("_ext1") else (name, False)
        candidates = [name] if name in source else [n for n in source if n.startswith(base) and ("_ext" in n[len(base):]) == ext]
        if len(candidates) != 1:
            raise RuntimeError(f"{name}: {len(candidates)} nicks of {args.source_version} match")
        nicks.append(candidates[0])
    reports = read_reports(args.redirector, args.skim_dir, args.workers)
    folders, loose_folders = defaultdict(set), defaultdict(set)
    for key, folder_reports in reports.items():
        for report in folder_reports:
            folders[report["inputDataset"]].add(key)
            loose_folders[loose_key(report["inputDataset"])].add(key)
    with ThreadPoolExecutor(args.workers) as pool:
        parents = dict(zip(nicks, pool.map(lambda nick: miniaod_parent(source[nick]["dbs"]), nicks)))

    (ROOT_DIR / args.target_version).mkdir(exist_ok=True)
    database_file = ROOT_DIR / args.target_version / "datasets.json"
    if not database_file.exists():
        database_file.write_text("{}")
    missing = []
    for nick in nicks:
        entry, parent = source[nick], parents[nick]
        matches = folders.get(parent) or loose_folders.get(loose_key(parent))
        if not matches:
            missing.append(nick)
            continue
        if parent not in folders:
            logger.warning(f"{nick}: no skim of {parent}, using the skim of {[reports[m][0]['inputDataset'] for m in matches]}")
        for era_dir, folder in sorted(matches):
            if ERA_DIRS[era_dir] != entry["era"]:
                raise RuntimeError(f"{nick}: era {entry['era']}, skim in {era_dir}/{folder}")
            folder_reports = reports[(era_dir, folder)]
            outputs = {name: output for report in folder_reports for name, output in report["outputs"].items()}
            not_processed = sum(len(report["notProcessedFiles"]) for report in folder_reports)
            if not_processed:
                logger.warning(f"{era_dir}/{folder}: {not_processed} input files not processed")
            sample = Sample(
                nick=f"{folder}_{entry['era']}",
                era=entry["era"],
                nevents=sum(o["n_selected_original"] + o["n_not_selected_original"] for o in outputs.values()),
                nfiles=len(outputs),
                sample_type=entry["sample_type"],
                filelist=[f"{args.redirector}{args.skim_dir}/{era_dir}/{folder}/{name}" for name in sorted(outputs)],
                xsec=entry["xsec"],
                dbs=folder_reports[0]["inputDataset"],
                instance=entry.get("instance"),
                generator_weight=entry["generator_weight"],
            )
            (ROOT_DIR / args.target_version / sample.era / sample.sample_type).mkdir(parents=True, exist_ok=True)
            sample.dump_filelist(ROOT_DIR, args.target_version)
            sample.dump_database_entry(ROOT_DIR, args.target_version)
    if missing:
        logger.warning(f"{len(missing)} nicks without a skim: {missing}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    main(parse_arguments())
