import questionary
import json
import yaml
import os
from rucio_manager import RucioManager
from das_manager import DASQuery
from database import SampleDatabase
from helpers import custom_style, parse_args, filelist_path, filelist_path_yaml


class SampleManager(object):
    def __init__(self):
        self.args = parse_args()
        self.redirector = "root://xrootd-cms.infn.it//"
        questionary.print("Starting up RucioManager")
        self.rucio_manager = RucioManager()
        self.database_folder = os.path.abspath(self.args.database_folder)
        self.database_file = os.path.join(self.database_folder, self.args.database_file)
        questionary.print("Starting up Datasetmanager")
        self.database = SampleDatabase(self.database_folder, self.database_file)
        questionary.print("Database loaded")
        self.database.status()
        self.processing = True
        self.available_tasks = [
            "Add a new sample",  # Task 0
            "Edit a sample (not implemented yet)",  # Task 1
            "Delete a sample",  # Task 2
            "Find samples (by nick)",  # Task 3
            "Find samples (by DAS name)",  # Task 4
            "Print details of a sample",  # Task 5
            "Create a production file",  # Task 6
            "Update genweight",  # Task 7
            "Maintainance",  # Task 8
            "Save and Exit",  # Task 9
            "Exit without Save",  # Task 10
        ]

    def run(self):
        while self.processing:
            answer = questionary.select(
                "What do you want to do?",
                choices=self.available_tasks,
                show_selected=True,
                use_indicator=True,
                style=custom_style,
            ).ask()
            task = self.available_tasks.index(answer)

            if task == 0:
                self.finding_and_adding_sample()
                continue
            elif task == 1:
                questionary.print("Editing not implemented yet")
                continue
            elif task == 2:
                self.delete_sample()
                continue
            elif task == 3:
                self.find_samples_by_nick()
                continue
            elif task == 4:
                self.find_samples_by_das()
                continue
            elif task == 5:
                self.print_sample()
                continue
            elif task == 6:
                self.create_production_file()
            elif task == 7:
                self.update_genweight()
                continue
            elif task == 8:
                self.run_maintainance()
                continue
            if task == 9:
                self.database.save_database()
                self.database.close_database()
                exit()
            elif task == 10:
                self.database.close_database()
                exit()

    def finding_and_adding_sample(self):
        nick = questionary.text("Enter a DAS nick to add", style=custom_style).ask()
        if nick in self.database.dasnicks:
            questionary.print("DAS nick is already in self.")
            self.database.print_by_das(nick)
            return
        results = DASQuery(
            nick=nick,
            type="search_dataset",
            database_folder=self.database_folder,
            redirector=self.redirector,
        ).result
        if len(results) == 0:
            questionary.print("No results found")
            return
        elif len(results) >= 1:
            options = []
            for result in results:
                options.append(
                    f"Nick: {result['dataset']} - last changed: {result['last_modification_date'].strftime('%d %b %Y %H:%M')} - created: {result['added'].strftime('%d %b %Y %H:%M')}"
                )
            questionary.print("Multiple results found")
            options += ["None of the above"]
            answers = questionary.checkbox(
                "Which dataset do you want to add ?",
                choices=options,
                style=custom_style,
            ).ask()
            if len(answers) == 1 and answers[0] == "None of the above":
                questionary.print("Adding nothing")
                return
            if len(answers) != 1 and "None of the above" in answers:
                questionary.print("Invalid selection, Adding nothing")
                return
            else:
                samples_added = []
                for answer in answers:
                    task = options.index(answer)
                    details = DASQuery(
                        nick=results[task]["dataset"],
                        type="details_with_filelist",
                        rucio_manager=self.rucio_manager,
                        database_folder=self.database_folder,
                        redirector=self.redirector,
                    ).result
                    self.database.add_sample(details)
                    self.generate_detailed_filelist(details)
                    samples_added.append(details["nick"])
                # now ask if the genweights should be calculated
                gen_question = questionary.confirm(
                    "Do you want to calculate the genweights for all added samples ?"
                ).ask()
                if gen_question:
                    for sample in samples_added:
                        self.database.genweight_by_nick(sample, ask_for_update=False)

    def generate_detailed_filelist(self, details):
        # first generate the folder structure for the filelist
        outputfile = filelist_path(self.database_folder, details)
        questionary.print(
            f"Generating filelist for {details['nick']}, writing to {outputfile}..."
        )
        if not os.path.exists(os.path.dirname(outputfile)):
            os.makedirs(os.path.dirname(outputfile))
        with open(outputfile, "w") as f:
            json.dump(details, f)

    def delete_sample(self):
        nick = questionary.text("Enter a nick to remove").ask()
        if nick in self.database.samplenicks:
            self.database.delete_by_nick(nick)
            return
        if nick in self.database.dasnicks:
            self.database.delete_by_das(nick)
            return
        questionary.print(f"No sample with nick {nick} found..")
        return

    def print_sample(self):
        nick = questionary.text("Enter a nick to print", style=custom_style).ask()
        if nick in self.database.samplenicks:
            self.database.print_by_nick(nick)
            return
        if nick in self.database.dasnicks:
            self.database.print_by_das(nick)
            return
        questionary.print(f"No sample with nick {nick} found..")
        return

    def find_samples_by_nick(self):
        nick = questionary.autocomplete(
            "Enter a sample nick to search for",
            list(self.database.samplenicks),
            style=custom_style,
        ).ask()
        if nick in self.database.samplenicks:
            self.database.print_by_nick(nick)
            return
        if nick in self.database.dasnicks:
            self.database.print_by_das(nick)
            return

    def update_genweight(self):
        nick = questionary.autocomplete(
            "Enter a sample nick to search for",
            list(self.database.samplenicks),
            style=custom_style,
        ).ask()
        if nick in self.database.samplenicks:
            self.database.genweight_by_nick(nick)
            return
        if nick in self.database.dasnicks:
            self.database.genweight_by_das(nick)
            return

    def find_samples_by_das(self):
        nick = questionary.autocomplete(
            "Enter a sample nick to search for",
            list(self.database.dasnicks),
            style=custom_style,
        ).ask()
        print(nick)
        if nick == "None":
            return
        if nick in self.database.dasnicks:
            self.database.print_by_das(nick)
            return

    def create_production_file(self):
        # select era and sampletypes to process
        possible_eras = [str(x) for x in list(self.database.eras)]
        possible_samples = list(self.database.sample_types)
        selected_eras = questionary.checkbox(
            "Select eras to be added ",
            possible_eras,
            style=custom_style,
        ).ask()
        selected_sample_types = questionary.checkbox(
            "Select sampletypes to be added ",
            possible_samples,
            style=custom_style,
        ).ask()
        nicks = self.database.get_nicks(
            eras=selected_eras, sample_types=selected_sample_types
        )
        outputfile = questionary.text(
            "Name of the outputfile ?", default="samples.txt", style=custom_style
        ).ask()
        with open(outputfile, "w") as f:
            for nick in nicks:
                if nick == nicks[-1]:
                    f.write(nick)
                else:
                    f.write(nick + "\n")
        questionary.print(
            f"✅ Successfully created {outputfile} and added {len(nicks)} samples"
        )
        return

    def run_maintainance(self):
        questionary.print("Running maintainance")
        # we check, if all samples have a dedicated filelist file, that is in json format
        # if not, we generate the filelist from the database information
        for sample in self.database.database:
            sampledata = self.database.database[sample]
            filelist_yaml = filelist_path_yaml(self.database_folder, sampledata)
            filelist_json = filelist_path(self.database_folder, sampledata)
            if not os.path.isfile(filelist_yaml) and not os.path.isfile(filelist_json):
                questionary.print(f"Creating detailed filelist for {sample}")
                # first run the query
                sampledata["filelist"] = [
                    self.redirector + filepath
                    for filepath in self.rucio_manager.get_rucio_blocks(
                        sampledata["dbs"]
                    )
                ]
                self.generate_detailed_filelist(sampledata)
            elif os.path.isfile(filelist_yaml) and not os.path.isfile(filelist_json):
                questionary.print(f"Converting {filelist_yaml} to json")
                with open(filelist_yaml, "r") as f:
                    data = yaml.safe_load(f)
                with open(filelist_json, "w") as f:
                    json.dump(data, f, indent=4)
                os.remove(filelist_yaml)
            else:
                pass


if __name__ == "__main__":
    manager = SampleManager()
    manager.run()
