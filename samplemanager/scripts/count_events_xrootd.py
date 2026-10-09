#!/usr/bin/env python3
"""
Count total number of events in NanoAOD ROOT files from an XRootD path.
Can read from a JSON filelist (fast) or discover files via XRootD directory listing.

Usage:
    # From JSON filelist:
    python count_events_xrootd.py --json sample_database/nanoAOD_v15/2024/dyjets_amcatnlo/DYto2Mu-2Jets_Bin-2J-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8_RunIII2024Summer24NanoAODv15-150X.json

    # From XRootD directory (recursive):
    python count_events_xrootd.py --xrd root://xrootd-cms.infn.it///store/mc/RunIII2024Summer24NanoAODv15/DYto2Mu-2Jets_Bin-2J-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/NANOAODSIM/150X_mcRun3_2024_realistic_v2-v3/
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

TREE_NAME = "Events"
MAX_WORKERS = 8

# ROOT C macro run per batch of files; prints "BATCH_TOTAL:<n>" to stdout
_ROOT_MACRO = r"""
#include <fstream>
#include <iostream>
#include <string>
void count_batch(const char* listpath) {
    std::ifstream f(listpath);
    std::string url;
    Long64_t total = 0;
    while (std::getline(f, url)) {
        if (url.empty()) continue;
        TFile *tf = TFile::Open(url.c_str(), "READ");
        if (!tf || tf->IsZombie()) {
            std::cerr << "WARNING: cannot open " << url << std::endl;
            if (tf) { tf->Close(); delete tf; }
            continue;
        }
        TTree *t = (TTree*)tf->Get("Events");
        if (t) total += t->GetEntries();
        tf->Close();
        delete tf;
    }
    std::cout << "BATCH_TOTAL:" << total << std::endl;
}
"""


def _run_root_batch(macro_path: str, batch_urls: list[str]) -> int:
    """Write a file list and run one ROOT process; return event count."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as lf:
        lf.write("\n".join(batch_urls))
        list_path = lf.name
    try:
        cmd = ["root", "-l", "-b", "-q", f'{macro_path}("{list_path}")']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        for line in result.stdout.splitlines():
            if line.startswith("BATCH_TOTAL:"):
                return int(line.split(":", 1)[1])
        # No BATCH_TOTAL found — print ROOT stderr for diagnosis
        if result.stderr:
            for line in result.stderr.splitlines()[-5:]:
                print(f"  [root stderr] {line}", file=sys.stderr)
        return 0
    finally:
        os.unlink(list_path)


def discover_files_xrd(base_url: str) -> list[str]:
    """Recursively list .root files under an XRootD URL."""
    try:
        from XRootD import client as xrd_client
        from XRootD.client.flags import DirListFlags
    except ImportError:
        print("XRootD Python bindings not available. Install with: pip install xrootd", file=sys.stderr)
        sys.exit(1)

    # Split server from path
    # e.g. root://xrootd-cms.infn.it///store/mc/... -> server=root://xrootd-cms.infn.it, path=///store/mc/...
    parts = base_url.split("//", 2)  # ['root:', '', 'xrootd-cms.infn.it//store/...']
    server_host = parts[2].split("/")[0]
    server_url = f"root://{server_host}"
    base_path = "/" + "/".join(parts[2].split("/")[1:]).lstrip("/")

    fs = xrd_client.FileSystem(server_url)
    files = []

    def recurse(path):
        status, listing = fs.dirlist(path, flags=DirListFlags.STAT)
        if not status.ok:
            print(f"  WARNING: cannot list {path}: {status.message}", file=sys.stderr)
            return
        for entry in listing:
            full_path = f"{path}/{entry.name}".replace("//", "/")
            if entry.statinfo.flags & 0x1:  # is directory
                recurse(full_path)
            elif entry.name.endswith(".root"):
                files.append(f"{server_url}/{full_path}")

    recurse(base_path)
    return files


def count_events(file_urls: list[str], workers: int = MAX_WORKERS) -> int:
    n = len(file_urls)
    print(f"Counting events across {n} files using {workers} parallel ROOT processes...")

    macro_path = os.path.join(tempfile.gettempdir(), "count_batch.C")
    with open(macro_path, "w") as mf:
        mf.write(_ROOT_MACRO)

    try:
        # Split files into `workers` batches
        batch_size = max(1, (n + workers - 1) // workers)
        batches = [file_urls[i:i + batch_size] for i in range(0, n, batch_size)]

        total = 0
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(_run_root_batch, macro_path, b): i
                       for i, b in enumerate(batches)}
            for future in as_completed(futures):
                batch_idx = futures[future]
                batch_total = future.result()
                total += batch_total
                done = sum(len(batches[futures[f]]) for f in futures if f.done())
                print(f"  batch {batch_idx + 1}/{len(batches)} done: "
                      f"{batch_total:>12,} events  ({done}/{n} files processed)")
    finally:
        os.unlink(macro_path)

    return total


def main():
    parser = argparse.ArgumentParser(description="Count total events in NanoAOD ROOT files.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--json", help="Path to JSON filelist (uses 'filelist' key)")
    group.add_argument("--xrd", help="XRootD base URL to recursively search for .root files")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS, help=f"Number of parallel threads (default: {MAX_WORKERS})")
    args = parser.parse_args()

    if args.json:
        with open(args.json) as f:
            data = json.load(f)
        file_urls = data["filelist"]
        print(f"Loaded {len(file_urls)} files from {args.json}")
    else:
        print(f"Discovering files under {args.xrd} ...")
        file_urls = discover_files_xrd(args.xrd)
        print(f"Found {len(file_urls)} .root files")

    total = count_events(file_urls, workers=args.workers)
    print(f"\nTotal events: {total:,}")


if __name__ == "__main__":
    main()
