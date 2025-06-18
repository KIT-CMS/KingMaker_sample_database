import json
import multiprocessing as mp
import os
import subprocess
from contextlib import nullcontext

import numpy as np
import uproot
from rich.progress import Progress


def read_filelist_from_das(dbs):
    filedict = {}
    das_query = "file dataset={}".format(dbs)
    das_query += " instance=prod/global"
    cmd = [
        "/cvmfs/cms.cern.ch/common/dasgoclient --query '{}' --json".format(das_query)
    ]
    output = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    jsonS = output.communicate()[0]
    filelist = json.loads(jsonS)
    for file in filelist:
        filedict[file["file"][0]["name"]] = file["file"][0]["nevents"]
    return [
        "{prefix}/{path}".format(prefix="root://xrootd-cms.infn.it/", path=file)
        for file in filedict.keys()
    ]


def _process_file(args):
    filepath, max_retries, timeout = args
    exception = None
    for _ in range(max_retries + 1):
        try:
            with uproot.open(filepath, timeout=timeout) as file:
                array = file["genWeight"].array(library="np")
            return (
                np.count_nonzero(array >= 0),  # positive_count
                np.count_nonzero(array < 0),  # negative_count
                False,  # failed_status
            )
        except Exception as e:
            exception = e

    print(f"Failed to process {filepath} after {max_retries} attempts: {exception}")
    return 0, 0, True


def _calculate_genweight_uproot(
    filelist,
    num_workers=4,
    max_retries=5,
    timeout=30,
    fail_threshold_percent=10,
    **kwargs,
):
    threshold, fails = len(filelist) // fail_threshold_percent, 0
    negative, positive = 0, 0

    print(f"Total files to process: {len(filelist)}. Failure threshold: {threshold} files.")
    tasks = [(f"{path}:Events", max_retries, timeout) for path in filelist]

    with Progress() as progress_bar:
        task = progress_bar.add_task("Files read ", total=len(filelist))

        with mp.Pool(num_workers) if num_workers > 1 else nullcontext() as context:
            for pos_count, neg_count, failed in (
                context.imap_unordered(_process_file, tasks)
                if context
                else map(_process_file, tasks)
            ):
                fails += int(failed)

                if fails > threshold:
                    print(
                        f"Too many files failed ({fails}/{len(filelist)}), exceeding "
                        f"threshold of {threshold}. Genweight calculation aborted, "
                        "returning None."
                    )
                    return None

                negative += neg_count
                positive += pos_count
                progress_bar.update(task, advance=1)

    print(f"Processed files: {len(tasks) - fails}, Failed files: {fails}")

    negfrac = negative / (negative + positive)
    genweight = 1.0 - 2.0 * negfrac

    print(f"Final genweight: {genweight}")
    return genweight


def calculate_genweight_uproot(dataset, num_workers=1, **kwargs):
    print(f"Counting negative and positive genweights for {dataset['nick']}...")

    return _calculate_genweight_uproot(
        filelist=read_filelist_from_das(dataset["dbs"]),
        num_workers=num_workers,
        **kwargs,
    )


def calculate_genweight_from_local_file(loc_file, num_workers=1, **kwargs):
    print(f"Counting negative and positive genweights from local file {loc_file}...")

    with open(loc_file, "r") as f:
        config = json.load(f)

    return _calculate_genweight_uproot(
        filelist=config["filelist"],
        num_workers=num_workers,
        **kwargs,
    )
