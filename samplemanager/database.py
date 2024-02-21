import os
import yaml
import json
import questionary
from helpers import custom_style, filelist_path
from calculate_genweights import calculate_genweight_from_local_file


class SampleDatabase(object):
    def __init__(self, database_folder, database_file):
        self.database_folder = database_folder
        self.database_file = database_file
        self.working_database_path = f"{self.database_file}.working"
        self.database = {}
        self.dasnicks = set()
        self.samplenicks = set()
        self.eras = set()
        self.sample_types = set()
        # load and parse the database
        self.load_database()
        self.parse_database()

    def load_database(self):
        if not os.path.exists(self.database_file):
            # create a new one if it does not exist
            answer = questionary.confirm(
                f"Create a new database  at {self.database_file}? ", style=custom_style
            ).ask()
            if not answer:
                raise FileNotFoundError(f"{self.database_file} does not exist ..")
            else:
                open(self.database_file, mode="a").close()
        # now copy a work verison of the database to use for edits

        if os.path.exists(self.working_database_path):
            questionary.print(" A working version of the database exists")
            answer = questionary.confirm(
                "Load working version of database ?", style=custom_style
            ).ask()
            if answer:
                self.working_database_path = self.database_file
        else:
            questionary.print("Preparing working version of the database")
            os.system(f"cp {self.database_file} {self.working_database_path}")
        if self.working_database_path.endswith(".yaml.working"):
            # if the file is empty load an empty dict
            with open(self.working_database_path) as f:
                self.database = yaml.safe_load(f) or {}
            # dumop the database to a json file
            questionary.print("Converting database to json...")
            with open(self.working_database_path.replace(".yaml", ".json"), "w") as f:
                json.dump(self.database, f)
            self.working_database_path = self.working_database_path.replace(
                ".yaml", ".json"
            )
        with open(self.working_database_path) as f:
            self.database = json.load(f) or {}

    def parse_database(self):
        for sample in self.database:
            if self.database[sample]["dbs"] is None:
                print(sample)
            self.dasnicks.add(self.database[sample]["dbs"])
            self.samplenicks.add(sample)
            self.eras.add(self.database[sample]["era"])
            self.sample_types.add(self.database[sample]["sample_type"])

    def status(self):
        questionary.print(
            f"The database contains {len(self.database)} samples, split over {len(self.eras)} era(s) and {len(self.sample_types)} sampletype(s)"
        )

    def save_database(self):
        questionary.print("Saving database...")
        with open(self.database_file, "w") as stream:
            json.dump(self.database, stream, indent=4)
        return

    def close_database(self):
        # remove the working database
        os.system(f"rm {self.working_database_path}")
        return

    def get_nicks(self, eras, sample_types):
        # find all nicknames that match the given era and sampletype
        nicks = []
        for sample in self.database:
            if (
                str(self.database[sample]["era"]) in eras
                and self.database[sample]["sample_type"] in sample_types
            ):
                nicks.append(sample)
        return nicks

    def print_by_nick(self, nick):
        sample = self.database[nick]
        questionary.print(f"--- {nick} ---", style="bold")
        for key in sample:
            questionary.print(f"{key}: {sample[key]}")
        questionary.print("-" * 50, style="bold")

    def print_by_das(self, dasnick):
        for sample in self.database:
            if self.database[sample]["dbs"] == dasnick:
                self.print_by_nick(sample)

    def genweight_by_nick(self, nick, ask_for_update=True):
        sample = self.database[nick]
        questionary.print(f"--- {nick} ---", style="bold")
        questionary.print(f"Current generator_weight: {sample['generator_weight']}")
        questionary.print(
            "Will calcuate new generator_weight for the sample (this will take some minutes ....)"
        )
        # get the generator weight
        new_genweight = calculate_genweight_from_local_file(
            filelist_path(self.database_folder, sample)
        )
        if new_genweight is None:
            questionary.print("Error when calculating genweights, no updates done.")
        else:
            questionary.print(f"New generator_weight: {new_genweight}")
            if ask_for_update:
                answer = questionary.confirm(
                    "Do you want to update the database?", style=custom_style
                ).ask()
                if answer:
                    sample["generator_weight"] = new_genweight
                    self.database[nick] = sample
                    self.save_database()
            else:
                sample["generator_weight"] = new_genweight
                self.database[nick] = sample
                self.save_database()

    def genweight_by_das(self, dasnick):
        for sample in self.database:
            if self.database[sample]["dbs"] == dasnick:
                self.genweight_by_nick(sample)

    def delete_by_nick(self, nick):
        for sample in self.database:
            if sample == nick:
                dasnick = self.database[sample]["dbs"]
                del self.database[sample]
                questionary.print(f"Deleted {nick} from database")
                # also remove the sample from the sets
                self.dasnicks.remove(dasnick)
                self.samplenicks.remove(sample)
                return

    def delete_by_das(self, dasnick):
        for sample in self.database:
            if self.database[sample]["dbs"] == dasnick:
                del self.database[sample]
                questionary.print(f"Deleted {dasnick} from database")
                # also remove the sample from the sets
                self.dasnicks.remove(dasnick)
                self.samplenicks.remove(sample)
                return

    def add_sample(self, details):
        if "nick" not in details:
            raise Exception("No nickname given")
        if details["dbs"] in self.dasnicks:
            questionary.print(f"Sample {details['dbs']} already exists")
            self.print_by_das(details["dbs"])
            return
        self.database[details["nick"]] = details
        self.dasnicks.add(details["dbs"])
        self.samplenicks.add(details["nick"])
        self.eras.add(details["era"])
        self.sample_types.add(details["sample_type"])
        questionary.print(
            f"✅ Successfully added {details['nick']}", style="bold italic fg:darkred"
        )
        return
