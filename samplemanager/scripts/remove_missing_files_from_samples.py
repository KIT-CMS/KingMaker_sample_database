from XRootD.client import FileSystem
import json
from pathlib import Path
import argparse
import subprocess
import os
import logging

from samplemanager import ROOT_DIR


# Default values for parsed arguments
DEFAULT_NANOAOD_VERSION = "nanoAOD_v15"
DEFAULT_XROOTD_REDIRECTOR = "root://xrootd-cms.infn.it"

# Configure logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def parse_arguments():
    # Create the argument parser
    parser = argparse.ArgumentParser(
        description="Fix sample filelists by removing inaccessible files."
    )

    # Add arguments
    parser.add_argument(
        "--nick",
        "-n",
        type=str,
        nargs="+",
        required=True,
        help=(
            "The sample nick for which the filelist information needs to be "
            + "fixed."
        ),
    )
    parser.add_argument(
        "--nanoaod-version",
        "-v",
        type=str,
        default=DEFAULT_NANOAOD_VERSION,
        help="nanoAOD version of the database (default: %(default)s).",
    )
    parser.add_argument(
        "--xrootd-redirector",
        "-x",
        type=str,
        default=DEFAULT_XROOTD_REDIRECTOR,
        help=(
            "XRootD redirector which is used to check file accessibility "
            + "(default: %(default)s)."
        ),
    )

    return parser.parse_args()


def get_database_file(
    sample_database_dir: Path,
    nanoaod_version: str,
):
    # Construct the sample database file path
    return sample_database_dir / nanoaod_version / "datasets.json"


def load_sample_database(
    sample_database_dir: Path,
    nanoaod_version: str,
):
    # Load the sample database
    database_file = get_database_file(sample_database_dir, nanoaod_version)
    with database_file.open("r") as f:
        samples = json.load(f)

    return samples


def get_sample(
    samples: dict,
    nick: str,
):
    # Get the sample information from the database
    sample_info = samples.get(nick)
    if sample_info is None:
        raise ValueError(f"Sample '{nick}' not found in the database.")

    return sample_info


def query_dasgoclient(
    dbs: str,
):
    # Run subprocess to run dasgoclient command
    das_query = f"file dataset={dbs}"
    p = subprocess.Popen(
        [
            "/cvmfs/cms.cern.ch/common/dasgoclient",
            "--query",
            das_query,
            "-json",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy(),
    )
    stdout, stderr = p.communicate()

    # Check for errors in the dasgoclient command
    if p.returncode != 0:
        raise RuntimeError(
            f"DAS query failed with error: {stderr.decode('utf-8')}"
        )

    # Decode the response and parse as JSON output
    output = json.loads(stdout.decode("utf-8"))

    # Extract file information from the DAS output
    files = [
        {
            "name": item["file"][0]["name"],
            "nevents": item["file"][0]["nevents"],
            "status": None,
            "stat_info": None
        }
        for item in output
    ]

    return files


def access_files(
    files: list,
    xrootd_redirector: str,
):
    # Create the XRootD file system client
    fs = FileSystem(xrootd_redirector)

    for file in files:

        # Check if the ROOT file is available using XRootD
        status, stat_info = fs.stat(file["name"])
        status_code = status.code

        # Add information to file dict
        file["status_code"] = status_code
        file["stat_info"] = stat_info
        logging.debug(
            f"Checked file {file['name']}, got status code {status_code}"
        )

    # Build list of available files
    accessible_files = []
    for file in files:
        # Skip files that are not reachable
        if file["status_code"] != 0:
            continue

        # Update the file name with the XRootD redirector
        file["name"] = (
            xrootd_redirector.rstrip("/")
            + "//"
            + file["name"].lstrip("/")
        )

        # Append the accessible file to the list
        accessible_files.append(file)
    accessible_files.sort(key=lambda f: f["name"])

    # Print summary of available files and events
    nevents = sum(f["nevents"] for f in files)
    nfiles = len(files)
    accessible_nevents = sum(file["nevents"] for file in accessible_files)
    accessible_nfiles = len(accessible_files)
    logging.info(f"Total files:       {nfiles}")
    logging.info(f"Accessible files:  {accessible_nfiles}/{nfiles} ({100 * accessible_nfiles / nfiles:.2f}%)")
    logging.info(f"Accessible events: {accessible_nevents}/{nevents} ({100 * accessible_nevents / nevents:.2f}%)")

    return accessible_files


def create_filelist(
    sample_info: dict,
    accessible_files: list,
):
    # The filelist file contains the sample info and the list of accessible
    # files. Copy the sample info and update the object.
    filelist = sample_info.copy()

    # Update filelist, nevents, and nfiles according to new filelist with
    # inaccessible files removed
    filelist["filelist"] = [file["name"] for file in accessible_files]
    filelist["nevents"] = sum(file["nevents"] for file in accessible_files)
    filelist["nfiles"] = len(accessible_files)

    return filelist


def dump_filelist(
    sample_database_dir: Path,
    nanoaod_version: str,
    filelist: dict,
):
    # Create the filelist file path
    filelist_file = (
        sample_database_dir
        / nanoaod_version
        / filelist["era"]
        / filelist["sample_type"]
        / f"{filelist['nick']}.json"
    )

    # Write the new filelist to the JSON file
    with filelist_file.open("w") as f:
        json.dump(filelist, f, indent=4, sort_keys=True)

    # Log the update to the sample database
    logging.info(f"Updated filelist {filelist_file}")

    return filelist


def dump_sample_info(
    sample_database_dir: Path,
    nanoaod_version: str,
    filelist: dict,
):
    # Remove filelist entry for the sample info in the database
    sample_info = filelist.copy()
    sample_info.pop("filelist")

    # Load the sample database and update the entry
    database = load_sample_database(sample_database_dir, nanoaod_version)
    database.update({sample_info["nick"]: sample_info})

    # Write the updated database to the JSON file
    database_file = get_database_file(sample_database_dir, nanoaod_version)
    with database_file.open("w") as f:
        json.dump(database, f, indent=4, sort_keys=True)

    # Log the update to the sample database
    logging.info(
        f"Updated sample database {database_file} for nick "
        + sample_info["nick"]
    )

    return filelist


def main(
    sample_database_dir: Path,
    nanoaod_version: str,
    xrootd_redirector: str,
    nicks: list,
):
    for nick in nicks:
        logging.info(f"Processing sample: {nick}")

        # Load the sample database and get the sample info
        samples = load_sample_database(sample_database_dir, nanoaod_version)
        sample_info = get_sample(samples, nick)

        # Get sample files according to dasgoclient query
        das_files = query_dasgoclient(sample_info["dbs"])

        # Access the files and get the list of accessible files
        accessible_files = access_files(das_files, xrootd_redirector)

        # Create a new filelist with only accessible files
        filelist = create_filelist(sample_info, accessible_files)

        # Dump the new filelist to the JSON file and update the database
        dump_filelist(sample_database_dir, nanoaod_version, filelist)

        # Dump the updated sample database to the JSON file
        dump_sample_info(sample_database_dir, nanoaod_version, filelist)


if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_arguments()

    # Run the main function with parsed arguments
    main(
        sample_database_dir=ROOT_DIR,
        nanoaod_version=args.nanoaod_version,
        xrootd_redirector=args.xrootd_redirector,
        nicks=args.nick,
    )
