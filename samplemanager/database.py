import json
import os

import questionary
from calculate_genweights import calculate_genweight_from_local_file
from helpers import custom_style, filelist_path


class SampleDatabase(object):
    def __init__(self, database_folder, database_file):
        self.database_folder = database_folder
        self.database_file = database_file
        self.working_database_path = f"{self.database_file}.working"
        self.details_database_file = None
        self.database = {}
        self.details_database = {}
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
                f"Create a new database at {self.database_file} ?", style=custom_style
            ).ask()
            if not answer:
                raise FileNotFoundError(f"{self.database_file} does not exist ..")
            else:
                with open(self.database_file, "w") as file:
                    file.write("{}")
        # now copy a work version of the database to use for edits

        if os.path.exists(self.working_database_path):
            questionary.print("A working version of the database exists")
            answer = questionary.confirm(
                "Load working version of database ?", style=custom_style
            ).ask()
            if not answer:
                os.system(f"cp {self.database_file} {self.working_database_path}")
        else:
            questionary.print("Preparing working version of the database")
            os.system(f"cp {self.database_file} {self.working_database_path}")
        with open(self.working_database_path) as f:
            self.database = json.load(f) or {}

    def load_details_database(self):
        if not os.path.exists(self.details_database_file):
            # create a new one if it does not exist
            questionary.print(
                f"Creating a new details database file at {self.details_database_file}"
            )
            with open(self.details_database_file, "w") as file:
                file.write("{}")
        with open(self.details_database_file) as f:
            self.details_database = json.load(f) or {}

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

    def save_database(self, verbose=True):
        if verbose:
            questionary.print("Saving database...")
        with open(self.database_file, "w") as stream:
            json.dump(self.database, stream, indent=4, sort_keys=True)
        return

    def save_working_database(self, verbose=True):
        if verbose:
            questionary.print("Saving working database...")
        with open(self.working_database_path, "w") as stream:
            json.dump(self.database, stream, indent=4, sort_keys=True)
        return

    def save_details_database(self, verbose=True):
        if verbose:
            questionary.print(f"Saving details database for {self.details_database['nick']}...")
        with open(self.details_database_file, "w") as stream:
            json.dump(self.details_database, stream, indent=4, sort_keys=True)
        return

    def database_maintainance(self):
        for sample in self.database:
            # remove the filelist entry from the dictionary
            if "filelist" in self.database[sample]:
                del self.database[sample]["filelist"]
        self.save_database()

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

    def genweight_by_nick(self, nick, ask_for_update=True, num_workers=1):
        sample = self.database[nick]
        self.details_database_file = filelist_path(
            self.database_folder, sample
        )
        self.load_details_database()
        questionary.print(f"--- {nick} ---", style="bold")
        questionary.print(f"Current generator_weight: {sample['generator_weight']}")
        questionary.print(
            "Will calcuate new generator_weight for the sample (this will take some minutes ....)"
        )
        # get the generator weight
        new_genweight = calculate_genweight_from_local_file(
            filelist_path(self.database_folder, sample),
            num_workers=num_workers,
        )
        if new_genweight is None:
            questionary.print("Error when calculating genweights, no updates done.")
        else:
            questionary.print(f"New generator_weight: {new_genweight}")
            if ask_for_update:
                answer = questionary.confirm(
                    "Do you want to update the working database ?", style=custom_style
                ).ask()
                if answer:
                    sample["generator_weight"] = new_genweight
                    self.database[nick] = sample
                    self.save_working_database()
                    if self.details_database_file and self.details_database:
                        self.details_database["generator_weight"] = new_genweight
                        self.save_details_database()
            else:
                sample["generator_weight"] = new_genweight
                self.database[nick] = sample
                self.save_working_database()
                if self.details_database_file and self.details_database:
                    self.details_database["generator_weight"] = new_genweight
                    self.save_details_database()

    def xsec_by_nick(self, nick, ask_for_update=True):
        sample = self.database[nick]
        self.details_database_file = filelist_path(
            self.database_folder, sample
        )
        self.load_details_database()
        questionary.print(f"--- {nick} ---", style="bold")
        questionary.print(f"Current cross section in pb: {sample['xsec']}")
        new_xsec = questionary.text("Enter new cross section in pb: ", default=str(sample["xsec"])).ask()
        if ask_for_update:
            answer = questionary.confirm(
                "Do you want to update the working database ?", style=custom_style
            ).ask()
            if answer:
                sample["xsec"] = float(new_xsec)
                self.database[nick] = sample
                self.save_working_database()
                if self.details_database_file and self.details_database:
                    self.details_database["xsec"] = float(new_xsec)
                    self.save_details_database()
        else:
            sample["xsec"] = float(new_xsec)
            self.database[nick] = sample
            self.save_working_database()
            if self.details_database_file and self.details_database:
                self.details_database["xsec"] = float(new_xsec)
                self.save_details_database()

    def get_nick_by_das(self, dasnick):
        for nick in self.database:
            if self.database[nick]["dbs"] == dasnick:
                return nick

    def delete_by_nick(self, nick):
        for sample in self.database:
            if sample == nick:
                dasnick = self.database[sample]["dbs"]
                del self.database[sample]
                questionary.print(f"Deleted {nick} from database")
                # also remove the sample from the sets
                self.dasnicks.remove(dasnick)
                self.samplenicks.remove(sample)
                self.save_working_database()
                return

    def delete_by_das(self, dasnick):
        for sample in self.database:
            if self.database[sample]["dbs"] == dasnick:
                del self.database[sample]
                questionary.print(f"Deleted {dasnick} from database")
                # also remove the sample from the sets
                self.dasnicks.remove(dasnick)
                self.samplenicks.remove(sample)
                self.save_working_database()
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
        self.save_working_database()
        return
