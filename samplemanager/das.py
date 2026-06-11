from __future__ import annotations
import os
import subprocess
from subprocess import PIPE
import json


def query_das(
    query: str,
    as_json: bool = True,
):
    """
    Query the DAS using `dasgoclient`.

    :param query: The DAS query string to execute.
    :type query: str

    :param as_json: Whether to return the output as JSON (default: ``True``).
    :type as_json: bool

    :return: The output of the DAS query, either as a string or a JSON object.
    :rtype: str | dict | list
    """

    # construct the command for dasgoclient queries
    cmd = [
        "dasgoclient",
        "-query",
        query,
    ]
    if as_json:
        cmd.append("--json")

    # execute the command
    p = subprocess.Popen(
        cmd,
        stdout=PIPE,
        stderr=PIPE,
    )
    output, error = (o.decode("utf-8") for o in p.communicate())

    # check for errors
    if p.returncode != 0:
        raise RuntimeError(
            f"Command {cmd} failed with exit code {p.returncode}.\n"
            f"Error executing dasgoclient command: {error.strip()}\n"
        )

    # if this is a JSON query, decode the response
    output = output.strip()
    if as_json:
        output = json.loads(output)

    return output


def get_dataset_info(
    keys: str | list[str],
    instance: str = "prod/global",
):
    """
    Get dataset information from DAS using the provided keys and instance.

    :param keys: A single DAS key or a list of DAS keys to query.
    :type keys: str | list[str]

    :param instance: The DAS instance to query (default: ``"prod/global"``).
    :type instance: str

    :return: A dictionary containing dataset information for each key.
    :rtype: dict[str, dict]
    """

    # transform a single key into a list
    if isinstance(keys, str):
        keys = [keys]

    # dictionary to hold dataset information for each key
    dataset_infos = {}

    for key in keys:
        # dictionary containing useful dataset information
        dataset_info = {}

        # query the dataset information
        query_dataset = f"dataset dataset={key} instance={instance}"
        query_files = f"file dataset={key} instance={instance}"
        response_dataset = query_das(query_dataset, as_json=True)
        response_files = query_das(query_files, as_json=True)

        # extract file summary information
        for subquery in response_dataset:
            if "dbs3:dataset_info" in subquery["das"]["services"]:
                dataset_info["dbs"] = subquery["dataset"][0]["name"]
                dataset_info["is_data"] = subquery["dataset"][0]["datatype"] == "data"
                dataset_info["acquisition_era"] = subquery["dataset"][0]["acquisition_era_name"]
                dataset_info["id"] = subquery["dataset"][0]["dataset_id"]
                dataset_info["sample"] = subquery["dataset"][0]["primary_dataset.name"]
                dataset_info["campaign"] = subquery["dataset"][0]["processed_ds_name"]
                dataset_info["preparation_id"] = subquery["dataset"][0]["prep_id"]
            if "dbs3:filesummaries" in subquery["das"]["services"]:
                dataset_info["n_files"] = subquery["dataset"][0]["nfiles"]
                dataset_info["n_events"] = subquery["dataset"][0]["nevents"]

        # extract sample file information
        response_files
        for item in response_files:
            if "dbs3:files_via_dataset" in item["das"]["services"]:
                dataset_info.setdefault("files", []).append(item["file"][0]["name"])

        # add dataset information for this key
        dataset_infos[key] = dataset_info

    return dataset_infos