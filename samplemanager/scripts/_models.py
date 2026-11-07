from dataclasses import asdict, dataclass, field
import json
from pathlib import Path


@dataclass
class Sample:
    nick: str
    era: str
    nevents: int
    nfiles: int
    sample_type: str
    dbs: str | None = field(default=None)
    instance: str | None = field(default=None)
    xsec: float | None = field(default=None)
    generator_weight: float | None = field(default=None)
    filelist: list[str] | None = field(default=None)


def load_sample_database(sample_database_file: Path):
    """
    Load sample database from the `datasets.json` file provided as
    `sample_database_file`.
    """
    with sample_database_file.open("r") as f:
        db = json.load(f)
    sample_lookup = {k: Sample(**v) for k, v in db.items()}
    return sample_lookup


def dump_sample_database(
    sample_lookup: dict[str, Sample],
    sample_database_file: Path,
):
    """
    Dump sample database to the `datasets.json` file provided as
    `sample_database_file`.
    """
    sample_lookup = {k: asdict(s) for k, s in sample_lookup.items()}
    with sample_database_file.open("w") as f:
        json.dump(sample_lookup, f, indent=4, sort_keys=True)


def load_sample_filelist(sample_database_dir: Path, sample: Sample) -> Sample:
    """
    Load filelist of a sample.
    """
    # Construct the filelist file path
    filelist_file = (
        sample_database_dir
        / sample.era
        / sample.sample_type
        / f"{sample.nick}.json"
    )

    # Load the filelist
    with filelist_file.open("r") as f:
        data = json.load(f)
    filelist = Sample(**data)

    return filelist


def dump_sample_filelist(sample_database_dir: Path, filelist: Sample):
    """
    Dump filelist of a sample.
    """
    # Construct the filelist file path
    filelist_file = (
        sample_database_dir
        / filelist.era
        / filelist.sample_type
        / f"{filelist.nick}.json"
    )

    # Dump the filelist
    with filelist_file.open("w") as f:
        json.dump(asdict(filelist), f, indent=4, sort_keys=True)


@dataclass
class XSec:
    sample_names: list[str]
    reference: str
    order: str
    xsec: float


def create_xsec_lookup(xsecs: list[XSec]):
    lookup = {}
    for xsec in xsecs:
        for sample_name in xsec.sample_names:
            lookup[sample_name] = xsec
    return lookup


def load_xsec_database(xsec_database_file: Path) -> dict[str, XSec]:
    """
    Load the cross section database. The function returns a lookup dictionary
    which maps a sample name to a `XSec` object. The sample name is the first
    part of a DBS string.
    """
    with xsec_database_file.open("r") as f:
        db = [XSec(**d) for d in json.load(f)]
    xsec_lookup = create_xsec_lookup(db)
    return xsec_lookup

