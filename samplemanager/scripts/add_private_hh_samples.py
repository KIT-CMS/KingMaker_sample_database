from XRootD.client import FileSystem
from XRootD.client.flags import DirListFlags
import logging
import ROOT
import os
import json
import pprint
import time

# Set up logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enable multithreading in ROOT
ROOT.EnableImplicitMT(8)

# Important directories, derived from location of this file
THIS_FILE = os.path.abspath(__file__)
THIS_DIR = os.path.dirname(THIS_FILE)
ROOT_DIR = os.path.dirname(os.path.dirname(THIS_DIR))

# Constants
NANOAOD_VERSION = "nanoAOD_v15"
ERA = "2024"
CAMPAIGN = "RunIII2024Summer24NanoAODv15-150X-kit-private"
SAMPLE_TYPE = "hh2b2tau"
BASE_DIRS = [
    "/store/user/sdaigler/mc_production/GluGluHHto2B2Tau_Par-c2-0p00-kl-1p00-kt-1p00_TuneCP5_13p6TeV_powheg-pythia8/NanoAODv15-4af6f860",
    "/store/user/sdaigler/mc_production/GluGluHHto2B2Tau_Par-c2-0p00-kl-3p00-kt-1p00_TuneCP5_13p6TeV_powheg-pythia8/NanoAODv15-6fc60a30",
    "/store/user/sdaigler/mc_production/GluGluHHto2B2Tau_Par-c2-0p00-kl-5p00-kt-1p00_TuneCP5_13p6TeV_powheg-pythia8/NanoAODv15-4af6f860",
    "/store/user/sdaigler/mc_production/GluGluHHto2B2Tau_Par-c2-0p00-kl-m1p00-kt-1p00_TuneCP5_13p6TeV_powheg-pythia8/NanoAODv15-6fc60a30",
]


def _retrieve_sample_files(xrootd_fs: FileSystem, base_dir: str):
    # Get all files in the base directory
    status, listing = xrootd_fs.dirlist(base_dir, DirListFlags.STAT)
    if status.code != 0:
        msg = (
            "Could not retrieve sample files from XRootD server"
            + f"{str(xrootd_fs.url)}, directory {base_dir}.\n"
            + f"Got status {status}."
        )
        logger.error(msg)
        raise RuntimeError(msg)

    # Get the file paths and concatenate server address with path
    files = [
        str(xrootd_fs.url) + os.path.join(base_dir, item.name)
        for item in listing
    ]
    logger.debug(
        f"Retrieved {len(files)} files from {str(xrootd_fs.url) + base_dir}"
    )

    return files


def _retrieve_sample_info_from_files(files: list[str]):
    # Track time
    start = time.time()

    # Create a TChain of all files of the dataset
    chain = ROOT.TChain("Events")
    for file in files:
        chain.Add(file)
        logger.debug(f"Added {file} to chain")
    events = ROOT.RDataFrame(chain)

    # Get the number of files
    n_files = len(files)

    # Get the number of events
    n_events = events.Count().GetValue()

    # Calculate the generator weight
    n_negative = (
        events.Define("is_negative", "genWeight < 0")
              .Sum("is_negative")
              .GetValue()
    )
    generator_weight = 1 - 2 * n_negative / n_events

    # Stop tracking time
    stop = time.time()

    # Compile dictionary with sample information retrieved from the files
    sample_info = {
        "nfiles": n_files,
        "nevents": n_events,
        "generator_weight": generator_weight,
    }
    logger.debug(
        "Retrieved sample information from files: "
        + f"{pprint.pformat(sample_info)}"
    )
    logger.debug(f"Sample processing took {stop - start:.1f} s.")

    return sample_info


def main():
    # Set up the XRootD file system
    fs = FileSystem("root://cmsdcache-kit-disk.gridka.de:1094")

    # Template for sample database entry
    entry_template = {
        "dbs": None,
        "era": ERA,
        "generator_weight": None,
        "instance": None,
        "nevents": None,
        "nfiles": None,
        "nick": None,
        "sample_type": SAMPLE_TYPE,
        "xsec": None,
    }

    for base_dir in BASE_DIRS:
        logger.info(f"Process directory {base_dir}")

        # Copy entry template
        entry = entry_template.copy()

        # Construct the sample nick
        sample_name = os.path.basename(os.path.dirname(base_dir))
        nick = f"{sample_name}_{CAMPAIGN}"

        # Get and sort the filelist to ensure reproducibility
        files = sorted(_retrieve_sample_files(fs, base_dir))

        # Get information from the files that is put into the database (e.g.,
        # number of events, generator weight)
        sample_info_from_files = _retrieve_sample_info_from_files(files)

        # Put together the sample database entry
        entry.update({
            "nick": nick,
            **sample_info_from_files,
        })

        # Store the entry in the global sample database
        sample_database = os.path.join(ROOT_DIR, NANOAOD_VERSION, "datasets.json")
        with open(sample_database, mode="r") as f:
            sample_db = json.load(f)
        sample_db[nick] = entry
        with open(sample_database, mode="w") as f:
            json.dump(sample_db, f, indent=4, sort_keys=True)
        logger.info(f"Added sample {nick} to the sample database.")

        # Extend the entry with the filelist
        entry["filelist"] = files

        # Store the extended entry in the sample file
        with open(
            os.path.join(
                ROOT_DIR,
                NANOAOD_VERSION,
                ERA,
                SAMPLE_TYPE,
                f"{nick}.json",
            ),
            mode="w",
        ) as f:
            json.dump(entry, f, indent=4, sort_keys=True)
        logger.info(
            f"Added sample filelist of sample {nick} to the sample database."
        )


if __name__ == "__main__":
    main()
