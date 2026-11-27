from dataclasses import asdict, dataclass, field, fields
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
    # other fields of the entry (e.g. stxs, extensions, xsec_ref), written back unchanged
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "Sample":
        names = {f.name for f in fields(cls)} - {"extra"}
        return cls(**{k: v for k, v in data.items() if k in names}, extra={k: v for k, v in data.items() if k not in names})

    def to_dict(self) -> dict:
        data = asdict(self)
        extra = data.pop("extra")
        return {**data, **extra}


def load_sample_database(sample_database_file: Path):
    """
    Load sample database from the `datasets.json` file provided as
    `sample_database_file`.
    """
    with sample_database_file.open("r") as f:
        db = json.load(f)
    sample_lookup = {k: Sample.from_dict(v) for k, v in db.items()}
    return sample_lookup


def dump_sample_database(
    sample_lookup: dict[str, Sample],
    sample_database_file: Path,
):
    """
    Dump sample database to the `datasets.json` file provided as
    `sample_database_file`.
    """
    sample_lookup = {k: s.to_dict() for k, s in sample_lookup.items()}
    for s in sample_lookup.values():
        s.pop("filelist")
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
    filelist = Sample.from_dict(data)

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
        json.dump(filelist.to_dict(), f, indent=4, sort_keys=True)


@dataclass
class XSec:
    sample_names: list[str]
    reference: str
    order: str
    xsec: float
    calculation: str | None = None

    def ref(self) -> dict:
        """The `xsec_ref` entry of a sample with this cross section."""
        ref = {"order": self.order, "reference": self.reference}
        return {"calculation": self.calculation, **ref} if self.calculation else ref


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

