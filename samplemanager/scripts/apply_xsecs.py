import argparse
import logging
from math import isclose
from pathlib import Path

from ._models import (
    load_sample_database,
    dump_sample_database,
    load_sample_filelist,
    dump_sample_filelist,
    load_xsec_database,
)

# Set up logger
logger = logging.getLogger(__name__)


# Root directory of this repository
SAMPLE_DATABASE_DIR = Path(__file__).resolve().parent.parent.parent


def parse_arguments():
    # Create the parser
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sample-database-dir",
        default=SAMPLE_DATABASE_DIR,
        type=lambda x: Path(x).resolve(),
        help="Sample database directory. (default: %(default))",
    )
    parser.add_argument(
        "--nanoAOD-version",
        required=True,
        type=lambda x: Path(x).resolve(),
        helper="nanoAOD version",
    )
    parser.add_argument(
        "--xsec-database-file",
        required=True,
        type=lambda x: Path(x).resolve(),
        help="Cross section database file",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        type=str,
        help="Logging level",
    )

    # Parse arguments and convert them to a plain dictionary
    kwargs = vars(parser.parse_arguments())

    return kwargs


def main():
    # Sample database files
    sample_database_file = None
    xsec_database_file = None
    force = False

    # Get the sample database directory
    sample_database_dir = sample_database_file.parent

    # Load the sample and cross section databases
    sample_lookup = load_sample_database(sample_database_file)
    xsec_lookup = load_xsec_database(xsec_database_file)

    samples_updated = []
    for sample in sample_lookup.values():
        # - not `--force`: only replace cross sections which are set to `None`
        # - `--force`: set cross sections for all samples
        if sample.xsec is None or force:
            # Get the sample name
            sample_name = sample.dbs or None
            if sample_name is None:
                logger.warning(
                    f"Sample {sample.nick} does not have a DBS key, cannot "
                    + "set cross section"
                )
                continue
            sample_name = sample_name.split("/")[1]

            # Get the cross section object
            xsec = xsec_lookup.get(sample_name, None)
            if xsec is None:
                logger.warning(
                    "Could not find cross section matching the sample name "
                    + sample_name
                )
                continue

            # Check if the cross section is "close" to the original one, i.e.,
            # if it really needs to be changed
            if sample.xsec is not None and isclose(
                sample.xsec,
                xsec.xsec,
                rel_tol=1e-6,
            ):
                logger.debug(
                    f"Sample {sample.nick} cross section not updated, cross "
                    + "sections within relative precision of 1e-6"
                )
                continue

            # Set the sample cross section
            sample.xsec = xsec.xsec
            samples_updated.append(sample.nick)
            logger.debug(
                f"Set cross section of sample {sample.nick} to {xsec.xsec}"
            )

        # Update database
        dump_sample_database(sample_lookup, sample_database_file)
        logger.info(f"Wrote updates to main database {sample_database_file}")

        # Also update the filelist files
        for sample_nick in samples_updated:
            sample = sample_lookup[sample_nick]
            filelist = load_sample_filelist(sample_database_dir, sample)
            filelist.xsec =  sample.xsec
            dump_sample_filelist(sample_database_dir, filelist)
        logger.info(f"Updated sample filelists in {sample_database_dir}")


if __name__ == "__main__":
    # Parse arguments
    kwargs = parse_arguments()

    # Set logging level
    logging.setLevel(kwargs.pop("log_level"))

    # Execute the main function
    main(**kwargs)

