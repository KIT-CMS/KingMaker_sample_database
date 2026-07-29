#!/usr/bin/env python3
"""
Add private samples to the sample database.
"""

from __future__ import annotations

import argparse
from XRootD.client import FileSystem
from XRootD.client.flags import DirListFlags
import logging
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import uproot
import numpy as np
import yaml

from samplemanager import ROOT_DIR


# Set up logger
logger = logging.getLogger(__name__)


# Default values of command-line arguments
DEFAULT_SAMPLE_DATABASE_DIR = ROOT_DIR
DEFAULT_NUM_WORKERS = 1


@dataclass()
class PrivateSampleInfo:
    """
    Class representing information about a private sample that is going to be
    added to the sample database.
    """

    nanoaod_version: str
    era: str
    campaign: str
    sample_type: str
    redirector: str
    sample_dirs: list[Path]

    def __post_init__(self):
        # Ensure that the sample paths are Path objects
        self.sample_dirs = [Path(s) for s in self.sample_dirs]


@dataclass()
class Sample:
    """
    Class representing a sample in the sample database.
    """

    nick: str
    era: str
    nevents: int
    nfiles: int
    sample_type: str
    filelist: list[str] | None = field(default=None)
    xsec: float | None = field(default=None)
    dbs: str | None = field(default=None)
    instance: str | None = field(default=None)
    generator_weight: float | None = field(default=None)

    def dump_database_entry(
        self,
        sample_database_dir: Path,
        nanoaod_version: str,
    ):
        # Load the database
        database_file = sample_database_dir / nanoaod_version / "datasets.json"
        with database_file.open(mode="r") as f:
            sample_db = json.load(f)

        # Convert sample to dictionary, drop filelist, and add to database
        sample = asdict(self).copy()
        sample.pop("filelist")

        # Add the sample to the database
        sample_db[self.nick] = sample

        # Dump the updated database back to the file
        with database_file.open(mode="w") as f:
            json.dump(sample_db, f, indent=4, sort_keys=True)

        logging.info(f"Added sample {self.nick} to the sample database.")

    def dump_filelist(
        self,
        sample_database_dir: Path,
        nanoaod_version: str,
    ):
        # Construct the filelist path
        filelist_file = (
            sample_database_dir
            / nanoaod_version
            / self.era
            / self.sample_type
            / f"{self.nick}.json"
        )

        # Convert sample to dictionary
        sample = asdict(self)

        # Dump the sample to the file
        with filelist_file.open(mode="w") as f:
            json.dump(sample, f, indent=4, sort_keys=True)

        logging.info(
            f"Added filelist for sample {self.nick} to the sample database."
        )


def parse_arguments() -> dict[str, Any]:
    # Create the argument parser
    parser = argparse.ArgumentParser(
        description="Add private samples to the sample database."
    )

    # Add arguments
    parser.add_argument(
        "--private-sample-file",
        type=lambda x: Path(x).resolve(),
        required=True,
        help=(
            "Path to the YAML file containing information about private "
            + "samples"
        ),
    )
    parser.add_argument(
        "--sample-database-dir",
        type=lambda x: Path(x).resolve(),
        default=DEFAULT_SAMPLE_DATABASE_DIR,
        help="Path to the sample database directory (default: %(default)s)",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=DEFAULT_NUM_WORKERS,
        help=(
            "Number of worker processes to use for file processing (default: "
            + "%(default)s)"
        ),
    )

    # Parse arguments
    args = vars(parser.parse_args())

    return args


def load_private_sample_info(
    private_sample_file: Path,
) -> list[PrivateSampleInfo]:
    """
    Load private sample information from a YAML file.

    Arguments
    ---------
    private_sample_file : Path
        Path to the YAML file containing private sample information.

    Returns
    -------
    list[PrivateSampleInfo]
        List of PrivateSampleInfo objects containing information about the
        private samples.
    """

    # Load the YAML file with private sample information
    with private_sample_file.open(mode="r") as f:
        private_sample_info_list = yaml.safe_load(f)

    sample_infos = [
        PrivateSampleInfo(**item)
        for item in private_sample_info_list
    ]

    # Log the loaded private sample information
    logger.debug(
        f"Loaded {len(sample_infos)} private sample(s) from "
        + f"{private_sample_file}."
    )

    return sample_infos


def _get_sample_filelist(
    sample_info: PrivateSampleInfo,
    sample_dir: str,
) -> list[str]:
    # Create the XRootD file system
    xrd_fs = FileSystem(sample_info.redirector)

    # Get all files in the base directory
    status, listing = xrd_fs.dirlist(str(sample_dir), DirListFlags.STAT)
    if status.code != 0:
        msg = (
            "Could not retrieve sample files from XRootD server"
            + f"{str(xrd_fs.url)}, directory {sample_dir}.\n"
            + f"Got status {status}."
        )
        logger.error(msg)
        raise RuntimeError(msg)

    # Get the file paths and concatenate server address with path
    files = [
        str(xrd_fs.url) + str(sample_dir / item.name)
        for item in listing
    ]
    logger.debug(
        f"Retrieved {len(files)} files from {str(xrd_fs.url) + str(sample_dir)}"
    )

    return files


def _get_file_based_sample_info(
    sample_info: PrivateSampleInfo,
    sample_dir: str,
    filelist: list[str],
    num_workers=1,
) -> dict[str, Any]:
    # Track time
    start = time.time()

    # Define columns which shall be read from the files
    columns = ["event"]
    if not sample_info.sample_type == "data":
        columns.append("genWeight")

    # Collect number of events and number of negative generator weights from the
    # files
    n_events = []
    n_negative = []
    for array in uproot.iterate(
        {f: "Events" for f in filelist},
        filter_name=columns,
        step_size=100_000,
        num_workers=num_workers,
        allow_missing=True,
        library="np",
    ):
        # Count number of events in the loaded chunk
        n_events.append(array["event"].shape[0])

        # For MC samples, also count the number of negative generator weights
        # to calculate the generator weight
        if "genWeight" in array:
            n_negative.append(np.sum(array["genWeight"] < 0))
        else:
            n_negative.append(0)

    # Sum up numbers of chunks
    n_files = len(filelist)
    n_events = np.sum(n_events).tolist()
    n_negative = np.sum(n_negative).tolist()

    # For samples which are not data, calculate the generator weight
    generator_weight = None
    if sample_info.sample_type != "data":
        generator_weight = 1 - 2 * n_negative / n_events

    # Compile dictionary with sample information retrieved from the files
    sample_info = {
        "nfiles": n_files,
        "nevents": n_events,
        "generator_weight": generator_weight,
    }

    # Stop tracking time
    stop = time.time()

    # Log the retrieved sample information
    delta = round(stop - start, 3)
    logger.debug(
        f"Retrieved file-based sample information for {sample_dir} in {delta} "
        + "s."
    )
    logger.debug(f"    nfiles:           {n_files}")
    logger.debug(f"    nevents:          {n_events}")
    logger.debug(f"    generator_weight: {generator_weight}")

    return sample_info


def get_sample_metadata(
    sample_info: PrivateSampleInfo,
    sample_dir: Path,
    num_workers: int = 1,
) -> Sample:
    """
    Get sample metadata for a private sample, which are going to be added to the
    sample database.

    Arguments
    ---------

    sample_info : PrivateSampleInfo
        Information about the private sample collection.

    sample_dir : Path
        Path to the directory containing the sample files.

    num_workers : int, optional
        Number of worker processes to use for file processing. Default is 1.

    Returns
    -------

    Sample
        Sample object containing the sample metadata.
    """

    # Construct the sample nick
    nick = f"{sample_dir.parent.name}_{sample_info.campaign}"

    # Retrieve the filelist for the sample
    filelist = _get_sample_filelist(sample_info, sample_dir)

    # Get information from the files (number of files, number of events,
    # generator weight) that are put into the database
    sample_info_from_files = _get_file_based_sample_info(
        sample_info,
        sample_dir,
        filelist,
        num_workers=num_workers,
    )

    # Construct the sample database entry
    sample = Sample(
        nick=nick,
        era=sample_info.era,
        sample_type=sample_info.sample_type,
        filelist=filelist,
        **sample_info_from_files,
    )

    return sample


def main(**kwargs):
    # Get the command line arguments
    sample_database_dir = kwargs.pop("sample_database_dir")
    private_sample_file = kwargs.pop("private_sample_file")
    num_workers = kwargs.pop("num_workers")

    # Log the sample database directory being used
    logger.info(f"Use sample database {sample_database_dir}")

    # Load information about private samples from the YAML file
    sample_infos = load_private_sample_info(private_sample_file)

    for sample_info in sample_infos:
        for sample_dir in sample_info.sample_dirs:
            logger.info(
                f"Process {sample_dir} (campaign {sample_info.campaign})"
            )

            # Construct the sample metadata from private sample info and
            # information extracted from the files
            sample = get_sample_metadata(
                sample_info,
                sample_dir,
                num_workers=num_workers,
            )

            # Dump the sample database entry to the global sample database
            sample.dump_database_entry(
                sample_database_dir,
                sample_info.nanoaod_version,
            )

            # Dump the sample filelist to the sample database
            sample.dump_filelist(
                sample_database_dir,
                sample_info.nanoaod_version,
            )


if __name__ == "__main__":
    # Parse command-line arguments
    kwargs = parse_arguments()

    # Configure the logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    # Execute the main program
    main(**kwargs)
