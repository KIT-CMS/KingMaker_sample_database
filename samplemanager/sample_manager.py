import json
import os
from copy import deepcopy

import questionary
from das_manager import DASQuery
from database import SampleDatabase
from helpers import custom_style, database_folder_path, filelist_path, parse_args
from nanoAOD_versions import nanoAOD_versions
from rich.progress import Progress


class SampleManager(object):
    def __init__(self):
        self.args = parse_args()
        self.default_instance = "prod/global"
        self.instance_choices = ["prod/global", "prod/phys03"]
        assert self.default_instance in self.instance_choices
        self.redirector = "root://xrootd-cms.infn.it//"

        self.nanoAOD_version: int = questionary.select(
            "Select a nanoAOD version", 
            choices=nanoAOD_versions, 
            style=custom_style, 
            default=nanoAOD_versions[0]).ask()

        base_folder = os.path.abspath(self.args.database_folder)
        self.database_folder = database_folder_path(base_folder, self.nanoAOD_version)
        self.database_file = os.path.join(self.database_folder, self.args.database_file)
        questionary.print("Starting up Datasetmanager")
        self.database = SampleDatabase(self.database_folder, self.database_file)
        questionary.print("Database loaded")
        self.database.status()
        self.processing = True
        self.available_tasks = [
            "Add a new sample",             # Task 0
            "Delete a sample",              # Task 1
            "Find samples (by nick)",       # Task 2
            "Find samples (by DAS name)",   # Task 3
            "Print details of a sample",    # Task 4
            "Create a production file",     # Task 5
            "Update genweight",             # Task 6
            "Update xsec",                  # Task 7
            "Maintainance",                 # Task 8
            "Save and Exit",                # Task 9
            "Exit without Save",            # Task 10
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
                self.delete_sample()
                continue
            elif task == 2:
                self.find_samples_by_nick()
                continue
            elif task == 3:
                self.find_samples_by_das()
                continue
            elif task == 4:
                self.print_sample()
                continue
            elif task == 5:
                self.create_production_file()
            elif task == 6:
                self.update_genweight()
                continue
            elif task == 7:
                self.update_xsec()
                continue
            elif task == 8:
                self.run_maintainance()
                continue
            elif task == 9:
                self.database.save_database()
                self.database.database_maintainance()
                self.database.close_database()
                exit()
            elif task == 10:
                self.database.close_database()
                exit()

    def finding_and_adding_sample(self):
        instance = questionary.select("Select the DAS instance for the search", choices=self.instance_choices, style=custom_style, default=self.default_instance).ask()
        nick = questionary.text("Enter a DAS nick to add", style=custom_style).ask()
        if nick in self.database.dasnicks:
            questionary.print("DAS nick is already in self.")
            self.database.print_by_das(nick)
            return
        results = DASQuery(
            instance=instance,
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
                        instance=instance,
                        nick=results[task]["dataset"],
                        type="details_with_filelist",
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
            json.dump(details, f, indent=4, sort_keys=True)

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

    def update_genweight(self):
        # Ask if user wants single or multiple sample mode
        mode = questionary.select(
            "Update genweight for one sample or multiple samples?",
            choices=["Search by single nick", "Search by era (multiple selection)"],
            style=custom_style,
        ).ask()
        if mode == "Search by single nick":
            nick = questionary.autocomplete(
                "Enter a sample nick to search for",
                list(self.database.samplenicks),
                style=custom_style,
            ).ask()
            if not nick or nick not in self.database.samplenicks:
                questionary.print("No valid sample selected.")
                return
            nicks = [nick]
        else:
            possible_eras = [str(x) for x in list(self.database.eras)]
            selected_eras = questionary.checkbox(
                "Select eras to filter samples by (leave empty for all)",
                possible_eras,
                style=custom_style,
            ).ask()
            if selected_eras:
                nicks_by_era = [nick for nick in self.database.samplenicks if str(self.database.database[nick].get("era", "")) in selected_eras]
            else:
                nicks_by_era = list(self.database.samplenicks)
            nicks = questionary.checkbox(
                "Select sample nicks to update genweight for",
                choices=sorted(nicks_by_era),
                style=custom_style,
            ).ask()
            if not nicks:
                questionary.print("No samples selected.")
                return
        num_workers = questionary.text(
            "Use number of workers for parallel processing",
            default="1",
            style=custom_style,
        ).ask()
        if not num_workers.isdigit() or not int(num_workers) > 0:
            questionary.print("Number of workers must be a positive integer")
            return
        if len(nicks) == 1:
            self.database.genweight_by_nick(nicks[0], ask_for_update=True, num_workers=int(num_workers))
        else:
            for nick in nicks:
                self.database.genweight_by_nick(nick, ask_for_update=False, num_workers=int(num_workers))

    def update_xsec(self):
        nick = questionary.autocomplete(
            "Enter a sample nick to search for",
            list(self.database.samplenicks),
            style=custom_style,
        ).ask()
        if nick in self.database.samplenicks:
            self.database.xsec_by_nick(nick)
            return
        if nick in self.database.dasnicks:
            nick = self.database.get_nick_by_das(nick)
            self.database.xsec_by_nick(nick)
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
        # we check, if all samples have a dedicated filelist file
        # if not, we generate the filelist from the database information
        questionary.print("Checking if all samples have a filelist file")
        with Progress() as progress_bar:
            task = progress_bar.add_task("Samples read ", total=len(self.database.database))
            for sample in self.database.database:
                sampledata = self.database.database[sample]
                filelist_json = filelist_path(self.database_folder, sampledata)
                if not os.path.isfile(filelist_json):
                    questionary.print(f"Creating detailed filelist for {sample}")
                    # first run the query
                    sampledata["filelist"] = DASQuery(
                        instance=sampledata["instance"],
                        nick=sampledata["dbs"],
                        type="details_with_filelist",
                        database_folder=self.database_folder,
                        redirector=self.redirector,
                    ).result["filelist"]
                    self.generate_detailed_filelist(sampledata)
                else:
                    pass
                progress_bar.update(task, advance=1)
        # we further check, if the details database is up to date
        # if not, we update it
        questionary.print("Checking if details database is up to date")
        with Progress() as progress_bar:
            task = progress_bar.add_task("Samples read ", total=len(self.database.database))
            for sample in self.database.database:
                sampledata = self.database.database[sample]
                filelist_json = filelist_path(self.database_folder, sampledata)

                self.database.details_database_file = filelist_path(self.database_folder, sampledata)
                self.database.load_details_database()

                _dict = deepcopy(self.database.details_database)
                _dict.pop("filelist", None)

                if set(tuple(self.database.database[sample].items())) - set(tuple(_dict.items())):
                    self.database.details_database.update(self.database.database[sample])
                    self.database.save_details_database(verbose=False)

                progress_bar.update(task, advance=1)

            # reset state of details database
            self.database.details_database_file = None
            self.database.details_database = {}

        questionary.print("Running database maintainance")
        self.database.database_maintainance()


if __name__ == "__main__":
    manager = SampleManager()
    manager.run()
