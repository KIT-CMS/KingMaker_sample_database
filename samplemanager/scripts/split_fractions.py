#!/usr/bin/env python3
"""
Measure the generator-weight fraction of each era's part of MC samples shared by several eras (the Summer24 MC of
2024 and 2025/2026), as split by CROWN's event::quantity::FractionSplitFlag, and store it per nick in
aux_data/split_fractions.json, which build_norm_table adds to the norm table as `split_fraction`. The event number is hashed exactly as in CROWN (splitmix64 -> [0, 1)); 2024 keeps
the events below --fraction, 2025/2026 the others.

    python -m samplemanager.scripts.split_fractions --fraction F --submit   # one condor job per file chunk
    python -m samplemanager.scripts.split_fractions --merge                  # writes aux_data/split_fractions.json
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import logging
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from samplemanager import ROOT_DIR


# Set up logger
logger = logging.getLogger(__name__)

# Default values of command-line arguments
DEFAULT_OUTPUT_DIR = Path(f"/ceph/{getpass.getuser()}/split_fractions")
DEFAULT_REDIRECTOR = "root://cms-xrd-global.cern.ch/"
DATABASE = ROOT_DIR / "nanoAOD_v15"
LOW_ERAS, HIGH_ERAS = ("2024",), ("2025", "2026")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fraction", type=float, help="Share of the events kept by the low era (CROWN's MC_SPLIT_FRACTION).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Where the per-chunk counts go.")
    parser.add_argument("--redirector", default=DEFAULT_REDIRECTOR, help="xrootd redirector replacing the filelists' one.")
    parser.add_argument("--files-per-job", type=int, default=150)
    parser.add_argument("--submit", action="store_true", help="Submit one condor job per chunk of files of every split sample.")
    parser.add_argument("--scan", nargs=2, metavar=("KEY", "CHUNK"), help="Count one chunk (what a condor job runs).")
    parser.add_argument("--merge", action="store_true", help="Sum the chunks and write aux_data/split_fractions.json.")
    return parser.parse_args()


def uniform(event):
    """splitmix64 of the event number mapped to [0, 1), as event::quantity::FractionSplitFlag."""
    import numpy as np

    z = event.astype(np.uint64) + np.uint64(0x9E3779B97F4A7C15)
    z = (z ^ (z >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
    z = (z ^ (z >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
    z ^= z >> np.uint64(31)
    return (z >> np.uint64(11)).astype(np.float64) * 2.0**-53


def split_samples() -> dict[str, dict]:
    """{filelist hash: {"nicks": {nick: era}, "files": [...]}} of the MC samples of the split eras."""
    samples = defaultdict(lambda: {"nicks": {}, "files": None})
    for era in LOW_ERAS + HIGH_ERAS:
        for path in sorted((DATABASE / era).glob("*/*.json")):
            entry = json.loads(path.read_text())
            if entry["sample_type"] in ("data", "embedding"):
                continue
            files = sorted(entry["filelist"])
            sample = samples[hashlib.sha1("\n".join(files).encode()).hexdigest()[:16]]
            sample["nicks"][entry["nick"]], sample["files"] = era, files
    return dict(samples)


def chunks(files: list[str], size: int) -> list[list[str]]:
    return [files[i : i + size] for i in range(0, len(files), size)]


def scan(key: str, chunk: int, args: argparse.Namespace) -> None:
    import numpy as np
    import uproot

    files = chunks(split_samples()[key]["files"], args.files_per_job)[chunk]
    counts, failed = dict.fromkeys(("low_pos", "low_neg", "high_pos", "high_neg"), 0), []
    for path in files:
        # the fraction is a property of the sample: unreadable files are skipped and counted
        for url in dict.fromkeys([args.redirector + path.split("//", 2)[2], path]):
            try:
                part_counts = dict.fromkeys(counts, 0)
                with uproot.open(url, handler=uproot.source.xrootd.XRootDSource, timeout=120) as f:
                    for arrays in f["Events"].iterate(["event", "genWeight"], step_size="200 MB", library="np"):
                        low, positive = uniform(arrays["event"]) < args.fraction, arrays["genWeight"] >= 0
                        for part, mask in (("low", low), ("high", ~low)):
                            part_counts[f"{part}_pos"] += int(np.count_nonzero(mask & positive))
                            part_counts[f"{part}_neg"] += int(np.count_nonzero(mask & ~positive))
                counts = {k: counts[k] + part_counts[k] for k in counts}
                break
            except Exception as e:
                logger.warning(f"{url}: {e}")
        else:
            failed.append(path)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / f"{key}_{chunk}.json").write_text(json.dumps({"fraction": args.fraction, "files": len(files), "failed": failed, **counts}))


def submit(args: argparse.Namespace) -> None:
    jobs = [(key, i) for key, sample in split_samples().items() for i in range(len(chunks(sample["files"], args.files_per_job)))]
    jobs = [(key, i) for key, i in jobs if not (args.output_dir / f"{key}_{i}.json").exists()]
    log_dir = args.output_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    wrapper = log_dir / "run.sh"
    wrapper.write_text(f"#!/bin/bash\nset -e\nexport USER={getpass.getuser()}\ncd {ROOT_DIR}\nexec {sys.executable} -m samplemanager.scripts.split_fractions "
                       f"--fraction {args.fraction!r} --output-dir {args.output_dir} --redirector {args.redirector} "
                       f"--files-per-job {args.files_per_job} --scan \"$@\"\n")
    wrapper.chmod(0o755)
    queue = "\n".join(f"    {key}, {i}" for key, i in jobs)
    (log_dir / "submit.sub").write_text(f"""universe = vanilla
executable = {wrapper}
arguments = $(key) $(chunk)
getenv = False
requirements = (TARGET.ProvidesEtpResources =?= true)
accounting_group = cms.higgs
x509userproxy = {Path.home() / ".globus" / "x509up"}
request_cpus = 1
request_memory = 3000
log = {log_dir}/$(key)_$(chunk).log
output = {log_dir}/$(key)_$(chunk).out
error = {log_dir}/$(key)_$(chunk).err
JobBatchName = split_fractions
queue key, chunk from (
{queue}
)
""")
    logger.info(f"{len(jobs)} chunks to scan")
    if jobs:
        subprocess.run(["condor_submit", str(log_dir / "submit.sub")], check=True)


def merge(args: argparse.Namespace) -> None:
    fractions, missing = {}, []
    for key, sample in split_samples().items():
        n_chunks = len(chunks(sample["files"], args.files_per_job))
        parts = [args.output_dir / f"{key}_{i}.json" for i in range(n_chunks)]
        if not all(p.exists() for p in parts):
            missing.append(next(iter(sample["nicks"])))
            continue
        counts = [json.loads(p.read_text()) for p in parts]
        if len({c["fraction"] for c in counts}) != 1:
            raise ValueError(f"{key}: chunks scanned with different --fraction values")
        n_failed = sum(len(c["failed"]) for c in counts)
        if n_failed > 0.2 * len(sample["files"]) or n_failed == len(sample["files"]):
            logger.warning(f"{next(iter(sample['nicks']))}: {n_failed}/{len(sample['files'])} files unreadable")
        n_eff = {part: sum(c[f"{part}_pos"] - c[f"{part}_neg"] for c in counts) for part in ("low", "high")}
        if n_eff["low"] + n_eff["high"] <= 0:
            missing.append(next(iter(sample["nicks"])))
            continue
        for nick, era in sample["nicks"].items():
            fractions[nick] = n_eff["low" if era in LOW_ERAS else "high"] / (n_eff["low"] + n_eff["high"])
    if missing:
        raise RuntimeError(f"{len(missing)} samples not fully scanned yet, e.g. {missing[:3]}: nothing written")
    (ROOT_DIR / "aux_data" / "split_fractions.json").write_text(json.dumps(fractions, indent=4, sort_keys=True) + "\n")
    logger.info(f"Wrote the split_fraction of {len(fractions)} nicks to aux_data/split_fractions.json")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    args = parse_arguments()
    if args.scan:
        scan(args.scan[0], int(args.scan[1]), args)
    elif args.submit:
        submit(args)
    elif args.merge:
        merge(args)
