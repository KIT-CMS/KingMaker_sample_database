import click
import json
import os
import re
from typing import Tuple
from das import get_dataset_info
from contextlib import nullcontext
import multiprocessing as mp
import uproot
import numpy as np
import warnings
from tqdm import tqdm
from typing import Any


class TooManyFailingFilesWarning(Warning):
    pass


# paths related to this file and this project
THIS_FILE = os.path.abspath(__file__)
THIS_DIR = os.path.dirname(THIS_FILE)
PROJECT_DIR = os.path.dirname(THIS_DIR)


# values from which the NANOAOD version has to be chosen
NANO_VERSIONS = [
    s.replace("nanoAOD_", "") for s in os.listdir(PROJECT_DIR) if s.startswith("nanoAOD_")
]


@click.group()
def main():
    pass


@main.command()
@click.argument(
    "nick",
    type=str,
    nargs=-1,
)
@click.option(
    "--database",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, readable=True),
    default=PROJECT_DIR,
    help=(
        "Path to the sample database root directory. Usually, this should be the root directory of "
        f"the 'sample_database' package that you are working with. Default: '{PROJECT_DIR}'."),
)
@click.option(
    "--nano-version",
    type=click.Choice(NANO_VERSIONS),
    default="v12",
    help=(
        "The nanoAOD version of the set of samples to show. The version should be passed as "
        f"'v<VERSION_NUMBER>'. Possible values are: {NANO_VERSIONS}. Default: 'v12'"
    )
)
def show(
    *,
    nick: Tuple[str],
    database: str,
    nano_version: str,
):
    """
    Show sample information for NICK.

    NICK is the nick of the sample to show. If not given, all samples are shown.

    To filter samples, the output can be processed with tools like `jq`.
    """
    # explicitly name 'nick' as list to avoid confusion
    nick_list = list(nick)

    # load the sample database
    database_json_path = os.path.join(database, f"nanoAOD_{nano_version}", "datasets.json")
    with open(database_json_path, "r") as f:
        data = json.load(f)

    # filter samples if nicks are given, move on with the full list otherwise
    if len(nick_list) > 0:
        data = {
            sample_nick: sample_info
            for sample_nick, sample_info in data.items()
            if sample_nick in nick_list
        }

    # print out the data in JSON format
    click.echo(json.dumps(data, sort_keys=False, indent=4))


def build_nick(nick):
    # User-produced samples, so need to something different and more general
    if nick.endswith("USER"):
        # Remove first "/", remove "USER", unify split parts with "_"
        nick = "_".join(nick.strip("/").split("/")[:2])
        return nick
    if "_ext" in nick:
        ext_v = "_ext" + nick[nick.find("_ext") + 4]
    else:
        ext_v = ""
    parts = nick.split("/")[1:]
    # nick is the first part of the DAS sting + the second part till the first "_"
    # if there is no "_" in the second part, the whole second part is used
    nick = parts[0] + "_" + parts[1].split("_")[0] + ext_v

    return nick


def get_sample_type(dbs_key: str):
    sample_name = dbs_key.split("/")[1]
    sample_type_regex = {
        "dyjets_powheg": re.compile(r"^DYto.*powheg.*$"),
        "dyjets_madgraph": re.compile(r"^DYto.*madgraphMLM.*$"),
        "dyjets_amcatnlo": re.compile(r"^DYto.*amcatnloFXFX.*$"),
        "wjets_madgraph": re.compile(r"^WtoLNu.*madgraphMLM.*$"),
        "wjets_amcatnlo": re.compile(r"^WtoLNu.*amcatnloFXFX.*$"),
        "ggh_htautau": re.compile(r"^GluGluH((To((TauTau)|(2Tau)))|-Hto2TauUncorrelatedDecay).*$"),
        "ggh_hbb": re.compile(r"^GluGluH((to2B)|(-Hto2B)).*$"),
        "vbf_htautau": re.compile(r"^VBFH((To((TauTau)|(2Tau)))|(-Hto2TauUncorrelatedDecay)).*$"),
        "vbf_hbb": re.compile(r"^VBFH((to2B)|(-Hto2B)).*$"),
        "rem_htautau": re.compile(r"^((WminusH)|(WplusH)|(ZH))((to)|(To)|(-Hto))((TauTau)|(2Tau)).*$"),
        "rem_hbb": re.compile(r"^((WminusH)|(WplusH)|(ZH))_Hto2B.*$"),
        "rem_hww": re.compile(r"^((GluGlu)|(VBF))Hto2W.*$"),
        "rem_hzz": re.compile(r"^((GluGlu)|(VBF)|(WminusH_)|(WplusH_))Hto((2Z)|(ZZ)).*$"),
        "rem_higgs": re.compile(r"^TTH(((to)|(_Hto))|(-Hto)).*$"),
        "hh2b2tau": re.compile(r"^((GluGluto)|(GluGlu)|(VBF))HHto2B2Tau.*$"),
        "hh4b": re.compile(r"^((GluGluto)|(VBF))HHto4B.*$"),
        "hh4v": re.compile(r"^((GluGluto)|(VBF))HHto4V.*$"),
        "nmssm_Ybb": re.compile(r"^NMSSM(_|-)XtoYHto2B2Tau.*$"),
        "nmssm_Ytautau": re.compile(r"^NMSSM(_|-)XtoYHto2Tau2B.*$"),
        "singletop": re.compile(r"^((TBbarQ.*t-channel)|(TbarBQ.*t-channel)|(TWminus)|(TbarWplus)|(TbarB.*s-channel)|(TBbar.*s-channel)).*$"),
        "rem_ttbar": re.compile(r"^TT((G)|(LL)|(LNu)|(NuNu)|(TT)|(WW)|(Z)|(ZZ)|(ZZto4B))[-_].*$"),
        "ttbar": re.compile(r"^TTto((4Q)|(LNu2Q)|(2L2Nu)).*$"),
        "diboson": re.compile(r"^((WW)|(WZ)|(ZZ)).*$"),
        "data": re.compile(r"^((EGamma)|(Muon)|(Tau)|(JetMET))$"),
    }
    for sample_type, regex in sample_type_regex.items():
        if regex.match(sample_name) is not None:
            return sample_type
    return None


def get_era(dbs_key: str):
    campaign = dbs_key.split("/")[2]
    era_regex = {
        "2022preEE": re.compile(r"^((Run2022[C-D]-22Sep2023)|(Run3Summer22Nano.*realistic)).*$"),
        "2022postEE": re.compile(r"^((Run2022[E-G]-22Sep2023)|(Run3Summer22EENano.*realistic_postEE)).*$"),
        "2023preBPix": re.compile(r"^((Run2023C.*-22Sep2023)|(Run3Summer23Nano.*realistic)).*$"),
        "2023postBPix": re.compile(r"^((Run2023D.*-22Sep2023)|(Run3Summer23BPixNano.*realistic)).*$"),
        "2024": re.compile(r"^((Run2024[C-I]-MINIv6NANOv15)|(RunIII2024Summer24Nano.*realistic)).*$"),
    }
    for era, regex in era_regex.items():
        if regex.match(campaign) is not None:
            return era
    return None


def process_file(args):
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

    warnings.warn(
        f"Failed to process {filepath} after {max_retries} attempts: {exception}",
        RuntimeWarning,
    )

    return 0, 0, True


def calculate_generator_weight_from_nano(
    filelist,
    num_workers=4,
    max_retries=5,
    timeout=30,
    fail_threshold_percent=10,
    **kwargs,
):
    threshold, fails = len(filelist) // fail_threshold_percent, 0
    negative, positive = 0, 0

    tasks = [(f"{path}:Events", max_retries, timeout) for path in filelist]

    with mp.Pool(num_workers) if num_workers > 1 else nullcontext() as context:
        iterator = (
            context.imap_unordered(process_file, tasks)
            if context
            else map(process_file, tasks)
        )

        for pos_count, neg_count, failed in tqdm(
            iterator, total=len(tasks), desc="Files", unit="file", leave=False,
        ):
            fails += int(failed)

            if fails > threshold:
                warnings.warn(
                    f"Too many files failed ({fails}/{len(filelist)}), exceeding "
                    f"threshold of {threshold}. Genweight calculation aborted, "
                    "returning None.",
                    TooManyFailingFilesWarning,
                )
                return None

            negative += neg_count
            positive += pos_count

    negfrac = negative / (negative + positive)
    genweight = 1.0 - 2.0 * negfrac

    return genweight


@main.command()
@click.argument(
    "dbs_key",
    type=str,
    nargs=-1,
)
@click.option(
    "--database",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, readable=True),
    default=PROJECT_DIR,
    help=(
        "Path to the sample database root directory. Usually, this should be the root directory of "
        f"the 'sample_database' package that you are working with. Default: '{PROJECT_DIR}'."),
)
@click.option(
    "--nano-version",
    type=click.Choice(NANO_VERSIONS),
    default="v12",
    help=(
        "The nanoAOD version of the set of samples to show. The version should be passed as "
        f"'v<VERSION_NUMBER>'. Possible values are: {NANO_VERSIONS}. Default: 'v12'"
    )
)
def add(
    *,
    dbs_key: tuple[str],
    database: str,
    nano_version: str,
):
    """
    Add new samples to the database using the DBS_KEY of the samples.
    """
    # explicitly name 'dbs_key' as list to avoid confusion
    dbs_key_list = list(dbs_key)

    # load the sample database
    database_json_path = os.path.join(database, f"nanoAOD_{nano_version}", "datasets.json")
    with open(database_json_path, "r") as f:
        data = json.load(f)

    # get the DBS keys to check if keys passed to this program have already been added before
    dbs_keys_present = [sample_info["dbs"] for sample_info in data.values()]

    for dbs_key in dbs_key_list:
        if dbs_key in dbs_keys_present:
            click.echo(f"Skipping key '{dbs_key}' as it is already stored in the database")
            continue

        # If the sample can only be found in a non-standard instance (other than prod/global) the
        # key is passed as <DBS_KEY>:<DBS_INSTANCE>. In this case, the dbs_key must be splitted along ':'
        dbs_key, dbs_instance = dbs_key, "prod/global"
        if ":" in dbs_key:
            dbs_key, dbs_instance = dbs_key.split(":")

        # get the sample information from the DAS
        sample_info_from_das = get_dataset_info(dbs_key, instance=dbs_instance)[dbs_key]

        # get the nick and the sample type
        nick = build_nick(dbs_key)
        sample_type = get_sample_type(dbs_key)
        era = get_era(dbs_key)

        if sample_type is None:
            raise Exception(f"Sample type for '{dbs_key}' could not be found")
        if era is None:
            raise Exception(f"Era for '{dbs_key}' could not be found")


        sample_info = {
            "dbs": dbs_key,
            "era": era,
            "generator_weight": None,
            "instance": dbs_instance,
            "nevents": sample_info_from_das["n_events"],
            "nfiles": sample_info_from_das["n_files"],
            "nick": nick,
            "sample_type": sample_type,
            "xsec": None,
        }

        # save the sample in the central database file
        data[nick] = sample_info

        # add filelist file
        sample_filelist_json_path = os.path.join(
            database,
            f"nanoAOD_{nano_version}",
            era,
            sample_type,
            f"{nick}.json",
        )
        sample_info_with_filelist = sample_info.copy()
        sample_info_with_filelist["filelist"] = [
            "root://xrootd-cms.infn.it//" + s
            for s in sample_info_from_das["files"]
        ]

        if not os.path.exists(os.path.dirname(sample_filelist_json_path)):
            os.makedirs(os.path.dirname(sample_filelist_json_path))
        with open(sample_filelist_json_path, "w") as f:
            json.dump(sample_info_with_filelist, f, indent=4, sort_keys=True)

        # write to the database file after each sample to be sure that all changes are tracked back
        with open(database_json_path, "w") as f:
            json.dump(data, f, indent=4, sort_keys=True)

        click.echo(f"Sample '{dbs_key}' successfully added to the database")


@main.command()
@click.argument(
    "nick",
    type=str,
    nargs=-1,
)
@click.option(
    "--database",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, readable=True),
    default=PROJECT_DIR,
    help=(
        "Path to the sample database root directory. Usually, this should be the root directory of "
        f"the 'sample_database' package that you are working with. Default: '{PROJECT_DIR}'."),
)
@click.option(
    "--nano-version",
    type=click.Choice(NANO_VERSIONS),
    default="v12",
    help=(
        "The nanoAOD version of the set of samples to show. The version should be passed as "
        f"'v<VERSION_NUMBER>'. Possible values are: {NANO_VERSIONS}. Default: 'v12'"
    )
)
def remove(
    *,
    nick: tuple[str],
    database: str,
    nano_version: str,
):
    """
    Set property of samples identified by NICK.
    """

    # explicitly name 'nick' as list to avoid confusion
    nick_list = list(nick)

    # load the sample database
    database_json_path = os.path.join(database, f"nanoAOD_{nano_version}", "datasets.json")
    with open(database_json_path, "r") as f:
        sample_data = json.load(f)

    for nick in nick_list:
        # Check that nick is part of the sample database
        if nick not in sample_data:
            raise ValueError(f"Nick '{nick}' not found in {database_json_path}")

        # Remove sample information from main database
        sample_info = sample_data.pop(nick)

        # If it exists, remove sample file from directory tree
        sample_filelist_json_path = os.path.join(
            database,
            f"nanoAOD_{nano_version}",
            sample_info["era"],
            sample_info["sample_type"],
            f"{nick}.json",
        )
        if os.path.exists(sample_filelist_json_path):
            os.remove(sample_filelist_json_path)

        # write to the database file after each sample to be sure that all changes are tracked back
        with open(database_json_path, "w") as f:
            json.dump(sample_data, f, indent=4, sort_keys=True)

        click.echo(f"Removed sample '{nick}'")


@main.command()
@click.argument(
    "nick",
    type=str,
    nargs=-1,
)
@click.option(
    "--database",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, readable=True),
    default=PROJECT_DIR,
    help=(
        "Path to the sample database root directory. Usually, this should be the root directory of "
        f"the 'sample_database' package that you are working with. Default: '{PROJECT_DIR}'."),
)
@click.option(
    "--nano-version",
    type=click.Choice(NANO_VERSIONS),
    default="v12",
    help=(
        "The nanoAOD version of the set of samples to show. The version should be passed as "
        f"'v<VERSION_NUMBER>'. Possible values are: {NANO_VERSIONS}. Default: 'v12'"
    )
)
@click.option(
    "--key",
    type=str,
    required=True,
    help=(
        "Name of the sample's property."
    )
)
@click.option(
    "--value",
    type=str,
    required=True,
    help=(
        "New value of the property."
    )
)
def set(
    *,
    nick: tuple[str],
    database: str,
    nano_version: str,
    key: str,
    value: Any,
):
    """
    Set property of samples identified by NICK.
    """
    # explicitly name 'nick' as list to avoid confusion
    nick_list = list(nick)

    # load the sample database
    database_json_path = os.path.join(database, f"nanoAOD_{nano_version}", "datasets.json")
    with open(database_json_path, "r") as f:
        sample_data = json.load(f)

    # try to convert the value to an integer or a float, interpret it as string otherwise
    value_conv = None
    for conv_func in [int, float]:
        try:
            value_conv = conv_func(value)
            break
        except Exception:
            pass
    if value_conv is not None:
        value = value_conv
    else:
        value = str(value)
    if value == "None":
        value = None

    # protect against setting the `filelist` attribute
    if key == "filelist":
        click.echo("Property 'filelist' cannot be set, exiting.")
        return

    for nick in nick_list:
        # load the sample information
        sample_info = sample_data[nick]

        # add the updated values to the sample information in the global database and in the
        # sample list file
        sample_filelist_json_path = os.path.join(
            database,
            f"nanoAOD_{nano_version}",
            sample_info["era"],
            sample_info["sample_type"],
            f"{nick}.json",
        )
        with open(sample_filelist_json_path, "r") as f:
            sample_info_with_filelist = json.load(f)

        # update the value
        sample_info[key] = value

        # also update the content of the seperate sample file
        sample_info_with_filelist.update(sample_info)
        with open(sample_filelist_json_path, "w") as f:
            json.dump(sample_info_with_filelist, f, indent=4, sort_keys=True)

        # write to the database file after each sample to be sure that all changes are tracked back
        with open(database_json_path, "w") as f:
            json.dump(sample_data, f, indent=4, sort_keys=True)

        click.echo(f"Property updated for '{nick}', which has now '{key}={value}'")


@main.command()
@click.argument(
    "nick",
    type=str,
    nargs=-1,
)
@click.option(
    "--database",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, readable=True),
    default=PROJECT_DIR,
    help=(
        "Path to the sample database root directory. Usually, this should be the root directory of "
        f"the 'sample_database' package that you are working with. Default: '{PROJECT_DIR}'."),
)
@click.option(
    "--nano-version",
    type=click.Choice(NANO_VERSIONS),
    default="v12",
    help=(
        "The nanoAOD version of the set of samples to show. The version should be passed as "
        f"'v<VERSION_NUMBER>'. Possible values are: {NANO_VERSIONS}. Default: 'v12'"
    )
)
@click.option(
    "--xsec-database",
    type=click.Path(exists=True, dir_okay=False, file_okay=True, readable=True),
    default=None,
    help=(
        "Path to a JSON file containing cross section information for samples."
    ),
)
def set_xsec(
    *,
    nick: tuple[str],
    database: str,
    nano_version: str,
    xsec_database: str,
):
    """
    Add new samples to the database using the DBS_KEY of the samples.
    """
    # explicitly name 'nick' as list to avoid confusion
    nick_list = list(nick)

    # load the sample database
    database_json_path = os.path.join(database, f"nanoAOD_{nano_version}", "datasets.json")
    with open(database_json_path, "r") as f:
        sample_data = json.load(f)

    # load the cross section database
    xsec_data = {}
    if xsec_database is not None:
        with open(xsec_database, "r") as f:
            xsec_data = json.load(f)


    for nick in nick_list:
        # split nick in two parts if ":" is found in the string
        nick, xsec_value = nick, None
        if ":" in nick:
            nick, xsec_value = nick.split(":")

        # load the sample information
        sample_info = sample_data[nick]

        # if the nick has not been set explicitly with "<NICK>:<XSEC_VALUE>", try to get it from the
        # xsec database
        if xsec_value is None:
            sample_name = sample_data[nick]["dbs"].split("/")[1]
            xsec_entry = next(
                (entry for entry in xsec_data if sample_name in entry["sample_names"]),
                None,
            )
            if xsec_entry is not None:
                xsec_value = xsec_entry.get("xsec", None)

        # if no cross section value has been set until here, skip this sample
        if xsec_value is None:
            click.echo(f"Skipping sample '{nick}' as no cross section value has been provided")
            continue

        # skip data samples
        if sample_info["sample_type"] == "data":
            click.echo(f"Set cross section of data sample '{nick}' to 1.0")
            xsec_value = 1.0

        # add the cross section value to the sample information in the global database and in the
        # sample list file
        sample_filelist_json_path = os.path.join(
            database,
            f"nanoAOD_{nano_version}",
            sample_info["era"],
            sample_info["sample_type"],
            f"{nick}.json",
        )
        with open(sample_filelist_json_path, "r") as f:
            sample_info_with_filelist = json.load(f)
        sample_info_with_filelist["xsec"] = xsec_value
        with open(sample_filelist_json_path, "w") as f:
            json.dump(sample_info_with_filelist, f, indent=4, sort_keys=True)

        # add the cross section value also to the sample information in the global database
        sample_data[nick]["xsec"] = xsec_value

        # write to the database file after each sample to be sure that all changes are tracked back
        with open(database_json_path, "w") as f:
            json.dump(sample_data, f, indent=4, sort_keys=True)

        click.echo(f"Cross section for sample '{nick}' added to the database")


@main.command()
@click.argument(
    "nick",
    type=str,
    nargs=-1,
)
@click.option(
    "--database",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, readable=True),
    default=PROJECT_DIR,
    help=(
        "Path to the sample database root directory. Usually, this should be the root directory of "
        f"the 'sample_database' package that you are working with. Default: '{PROJECT_DIR}'."),
)
@click.option(
    "--nano-version",
    type=click.Choice(NANO_VERSIONS),
    default="v12",
    help=(
        "The nanoAOD version of the set of samples to show. The version should be passed as "
        f"'v<VERSION_NUMBER>'. Possible values are: {NANO_VERSIONS}. Default: 'v12'"
    )
)
@click.option(
    "--num-workers",
    type=int,
    default=4,
    help="The number of workers for parallel processing of NANOAOD files. Default: 4.",
)
@click.option(
    "--max-retries",
    type=int,
    default=5,
    help=(
        "The maximum number of retries for processing the NANOAOD files after failures. Default: "
        "5."
    ),
)
@click.option(
    "--timeout",
    type=int,
    default=30,
    help=(
        "The timeout in seconds for processing one NANOAOD file. Default: 30."
    ),
)
@click.option(
    "--fail-threshold-percent",
    type=int,
    default=10,
    help=(
        "The maximum percentage of failing files allowed before aborting the genweight "
        "calculation. Default: 10."
    ),
)
@click.option(
    "--skip-if-exists",
    is_flag=True,
    help=(
        "If set, calculation is skipped if a generator weight (i.e., a weight not equal to 'nil') "
        "already exists for the sample."
    ),
)
def calculate_generator_weight(
    *,
    nick: tuple[str],
    database: str,
    nano_version: str,
    num_workers: int,
    max_retries: int,
    timeout: int,
    fail_threshold_percent: int,
    skip_if_exists: bool,
):
    """
    Add new samples to the database using the DBS_KEY of the samples.
    """
    # explicitly name 'nick' as list to avoid confusion
    nick_list = list(nick)

    # load the sample database
    database_json_path = os.path.join(database, f"nanoAOD_{nano_version}", "datasets.json")
    with open(database_json_path, "r") as f:
        sample_data = json.load(f)

    for nick in nick_list:
        # load the sample information
        sample_info = sample_data[nick]

        # skip the sample if a generator weight already exists and the flag is set
        if skip_if_exists and sample_info["generator_weight"] is not None:
            click.echo(
                f"Skipping sample '{nick}' as it already has a generator weight "
                f"({sample_info['generator_weight']})"
            )
            continue

        # add the cross section value to the sample information in the global database and in the
        # sample list file
        sample_filelist_json_path = os.path.join(
            database,
            f"nanoAOD_{nano_version}",
            sample_info["era"],
            sample_info["sample_type"],
            f"{nick}.json",
        )
        with open(sample_filelist_json_path, "r") as f:
            sample_info_with_filelist = json.load(f)

        # skip data samples
        if sample_info["sample_type"] == "data":
            click.echo(f"Skipping sample '{nick}' as it is a data sample")
            continue

        # calculate the generator weight
        generator_weight = calculate_generator_weight_from_nano(
            [
                f  # .replace("root://xrootd-cms.infn.it", "root://cmsdcache-kit-disk.gridka.de")
                for f in sample_info_with_filelist["filelist"]
            ],
            num_workers=num_workers,
            max_retries=max_retries,
            timeout=timeout,
            fail_threshold_percent=fail_threshold_percent,
        )

        sample_info_with_filelist["generator_weight"] = generator_weight
        with open(sample_filelist_json_path, "w") as f:
            json.dump(sample_info_with_filelist, f, indent=4, sort_keys=True)

        # add the cross section value also to the sample information in the global database
        sample_data[nick]["generator_weight"] = generator_weight

        # write to the database file after each sample to be sure that all changes are tracked back
        with open(database_json_path, "w") as f:
            json.dump(sample_data, f, indent=4, sort_keys=True)

        click.echo(f"Generator weight for sample '{nick}' added to the database")


if __name__ == "__main__":
    main()