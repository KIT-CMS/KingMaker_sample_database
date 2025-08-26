from questionary import Style
import argparse
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
        "generator_weight": 0.0,
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
