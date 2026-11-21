from questionary import Style
import argparse
import json
import os


def parse_args():
    """
    Function used to pass the available args of the mananger. Options are 'save_mode' and 'dataset_path'
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--save-mode", help="Save mode of the database", action="store_true"
    )
    parser.add_argument(
        "--database-file",
        help="Name of the database file, default is datasets.json",
        type=str,
        default="datasets.json",
    )
    parser.add_argument(
        "--database-folder",
        help="Path to the database folder",
        type=str,
        default="sample_database",
    )
    args = parser.parse_args()
    return args

def database_folder_path(base_folder: str, nanoAOD_version: str):
    return os.path.join(base_folder, nanoAOD_version_str(nanoAOD_version))

def filelist_path(database_folder: str, sampledata: dict):
    return os.path.join(
        database_folder,
        str(sampledata["era"]),
        sampledata["sample_type"],
        sampledata["nick"] + ".json",
    )

def update_sample_fields(database_folder: str, fields: dict) -> list:
    """
    Set the fields {nick: {field: value}} in datasets.json and the per-sample jsons of `database_folder`
    (passed to CROWN by KingMaker); returns the nicks not in this database or without a per-sample json.
    """
    datasets_path = os.path.join(database_folder, "datasets.json")
    with open(datasets_path) as stream:
        database = json.load(stream)
    missing = [
        nick for nick in fields
        if nick not in database or not os.path.exists(filelist_path(database_folder, database[nick]))
    ]
    for nick, values in fields.items():
        if nick in missing:
            continue
        database[nick] = dict(sorted({**database[nick], **values}.items()))
        sample_path = filelist_path(database_folder, database[nick])
        with open(sample_path) as stream:
            details = json.load(stream)
        details.update(values)
        with open(sample_path, "w") as stream:
            json.dump(details, stream, indent=4, sort_keys=True)
    if len(missing) < len(fields):
        with open(datasets_path, "w") as stream:
            json.dump(database, stream, indent=4)
    return missing


def nanoAOD_version_str(nanoAOD_version: int) -> str:
    return f"nanoAOD_v{nanoAOD_version}"


def default_entry():
    return {
        "nick": "",
        "dbs": "///",
        "era": -1,
        "nevents": -1,
        "nfiles": -1,
        "sample_type": "None",
        "xsec": 0.0,
        "generator_weight": None,
    }


custom_style = Style(
    [
        ("qmark", "fg:#673ab7 bold"),  # token in front of the question
        ("question", "bold"),  # question text
        ("answer", "fg:#f44336 bold"),  # submitted answer text behind the question
        ("pointer", "fg:#673ab7 bold"),  # pointer used in select and checkbox prompts
        (
            "highlighted",
            "fg:#673ab7 bold",
        ),  # pointed-at choice in select and checkbox prompts
        ("selected", "fg:#cc5454"),  # style for a selected item of a checkbox
        ("separator", "fg:#cc5454"),  # separator in lists
        ("instruction", ""),  # user instructions for select, rawselect, checkbox
        ("text", ""),  # plain text
        (
            "disabled",
            "fg:#858585 italic",
        ),  # disabled choices for select and checkbox prompts
    ]
)
