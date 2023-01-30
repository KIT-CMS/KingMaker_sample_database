import questionary
import yaml
import argparse
import os
import json
import subprocess
from datetime import datetime
import re
from calculate_genweights import calculate_genweight


def default_entry():
    return {
        "nick": "",
        "dbs": "///",
        "era": -1,
        "nevents": -1,
        "nfiles": -1,
        "sample_type": "None",
        "xsec": 1.0,
        "generator_weight": 1.0,
    }


class DASQuery(object):
    def __init__(self, nick, type):
        self.client = "/cvmfs/cms.cern.ch/common/dasgoclient"
        self.nick = nick
        self.query = ""
        self.cmd = "{client} --query '{query}' --json"
        self.querytype = type
        self.response = ""
        self.result = []

        # run the query and parse the result
        self.query_and_parse()

    def query_and_parse(self):
        if self.querytype == "search_dataset":
            self.query = "dataset={}".format(self.nick)
            self.run_query()
            self.parse_search()
        elif self.querytype == "details":
            self.query = "dataset={}".format(self.nick)
            self.run_query()
            self.parse_sample_details()
        else:
            raise Exception("Query type not supported")

    def run_query(self):
        output = subprocess.Popen(
            [self.cmd.format(client=self.client, query=self.query)],
            shell=True,
            stdout=subprocess.PIPE,
        )
        jsonS = output.communicate()[0]
        try:
            self.response = json.loads(jsonS)
        except json.JSONDecodeError:
            print("Could not parse result json")
            print(str(jsonS.decode("utf-8")))
            return

    def parse_sample_details(self):
        result = self.response
        services = [res["das"]["services"][0] for res in result]
        if "dbs3:filesummaries" in services:
            details = result[services.index("dbs3:filesummaries")]["dataset"][0]
        else:
            questionary.print("No filesummaries found - Check the query")
            return
        template = default_entry()
        template["dbs"] = self.nick
        template["nick"] = self._build_nick(self.nick)
        template["era"] = self._get_era(self.nick)
        template["nevents"] = details["nevents"]
        template["nfiles"] = details["nfiles"]
        template["sample_type"] = self._build_sampletype(self.nick)
        if template["sample_type"] != "data" and template["sample_type"] != "emb":
            template["xsec"] = self._fill_xsec(self.nick)
            template["generator_weight"] = self._fill_generator_weight(self.nick)
        self.result = template

    def _fill_xsec(self, nick):
        xsec = questionary.text(
            f"Set xsec for {nick}. Leave blank for value of 1.0"
        ).ask()
        if xsec == "" or xsec is None:
            return 1.0
        else:
            return float(xsec)

    def _fill_generator_weight(self, nick):
        gen_weight = questionary.text(
            f"Set generator_weight for {nick}. Leave blank for value of 1.0"
        ).ask()
        if gen_weight == "" or gen_weight is None:
            return 1.0
        else:
            return float(gen_weight)

    def _build_nick(self, nick):
        if "_ext" in nick:
            ext_v = "_ext" + nick[nick.find("_ext") + 4]
        else:
            ext_v = ""
        parts = nick.split("/")[1:]
        # nick is the first part of the DAS sting + the second part till the first "_"
        # if there is no "_" in the second part, the whole second part is used
        nick = parts[0] + "_" + parts[1].split("_")[0] + ext_v

        return nick

    def _get_era(self, nick):
        # regex search for a year in the nick
        m = re.search("20[0-9]{2}", nick)
        if m:
            return int(m.group(0))

    def _build_sampletype(self, nick):
        process = "/" + nick.split("/")[1].lower()
        sampletype = "None"
        print(f"Setting sampletype for {process}")
        if "dy".lower() in process:
            return "dyjets"
        elif "TTT".lower() in process:
            return "ttbar"
        elif "ST_t".lower() in process:
            return "singletop"
        elif any(name.lower() in process for name in ["/WZ_", "/WW_", "/ZZ_"]):
            return "diboson"
        elif any(
            name.lower() in process for name in ["/WWW_", "/WWZ_", "/WZZ_", "/ZZZ_"]
        ):
            return "triboson"
        elif any(name.lower() in process for name in ["EWK"]):
            return "electroweak_boson"
        elif any(
            name.lower() in process
            for name in ["/wjet", "/w1jet", "/w2jet", "/w3jet", "/w4jet"]
        ):
            return "wjets"
        elif any(
            process.startswith(name.lower())
            for name in [
                "/BTagCSV",
                "/BTagMu",
                "/Charmonium",
                "/DisplacedJet",
                "/DoubleEG",
                "/DoubleMuon",
                "/DoubleMuonLowMass",
                "/HTMHT",
                "/JetHT",
                "/MET",
                "/MinimumBias",
                "/MuOnia",
                "/MuonEG",
                "/SingleElectron",
                "/SingleMuon",
                "/SinglePhoton",
                "/Tau",
                "/Zerobias",
                "/EGamma",
            ]
        ):
            return "data"
        elif "Embedding".lower() in process:
            return "embedding"
        elif any(name.lower() in process for name in ["ttZJets", "ttWJets"]):
            return "rem_ttbar"
        elif any(name.lower() in process for name in ["GluGluToContinToZZ"]):
            return "ggZZ"
        elif any(
            name.lower() in process
            for name in ["GluGluZH", "HZJ", "HWplusJ", "HWminusJ"]
        ):
            return "rem_VH"
        # tautau signals
        elif any(name.lower() in process for name in ["GluGluHToTauTau"]):
            return "ggh_htautau"
        elif any(name.lower() in process for name in ["VBFHToTauTau"]):
            return "vbf_htautau"
        elif any(
            name.lower() in process
            for name in [
                "ttHToTauTau",
                "WplusHToTauTau",
                "WminusHToTauTau",
                "ZHToTauTau",
            ]
        ):
            return "rem_htautau"
        # bb signals
        elif any(name.lower() in process for name in ["GluGluHToBB"]):
            return "ggh_hbb"
        elif any(name.lower() in process for name in ["VBFHToBB"]):
            return "vbf_hbb"

        elif any(
            name.lower() in process
            for name in [
                "ttHToBB",
                "WplusH_HToBB",
                "WminusH_HToBB",
                "ZH_HToBB",
            ]
        ):
            return "rem_hbb"
        else:
            sampletype = questionary.text(
                f"No automatic sampletype found - Set sampletype for {nick} manually: "
            ).ask()
            return sampletype
        answer = questionary.confirm(f"Is sampletype {sampletype} correct ?").ask()
        if answer:
            return sampletype
        else:
            sampletype = questionary.text(
                f"No automatic sampletype found - Set sampletype for {nick} manually: "
            ).ask()
            return sampletype

    def parse_search(self):
        datasets = []
        search_results = []
        for entry in self.response:
            if "dataset" in entry["das"]["services"][0]:
                dataset = entry["dataset"][0]["name"]
                # check if the dataset is already in the query result
                if dataset not in datasets:
                    datasets.append(dataset)
                    search_results.append(
                        {
                            "dataset": dataset,
                            "last_modification_date": datetime.utcfromtimestamp(
                                int(entry["dataset"][0]["last_modification_date"])
                            ),
                            "added": datetime.utcfromtimestamp(
                                int(entry["dataset"][0]["creation_date"])
                            ),
                        }
                    )
        # sort the results, putting the newest added sample on top
        self.result = sorted(search_results, key=lambda d: d["added"])[::-1]


class SampleDatabase(object):
    def __init__(self, database_path):
        self.database_path = database_path
        self.working_database_path = (
            f"{os.path.dirname(os.path.realpath(__file__))}/database.working"
        )
        self.database = None
        self.dasnicks = set()
        self.samplenicks = set()
        self.eras = set()
        self.sample_types = set()
        # load and parse the database
        self.load_database()
        self.parse_database()

    def load_database(self):
        if not os.path.exists(self.database_path):
            # create a new one if it does not exist
            answer = questionary.confirm(
                f"Create a new database  at {self.database_path}? "
            ).ask()
            if not answer:
                raise FileNotFoundError(f"{self.database_path} does not exist ..")
            else:
                open(self.database_path, mode="a").close()
        # now copy a work verison of the database to use for edits

        if os.path.exists(self.working_database_path):
            questionary.print(" A working version of the database exists")
            answer = questionary.confirm("Load working version of database ?").ask()
            if not answer:
                raise FileNotFoundError("Aborting")
        else:
            os.system(f"cp {self.database_path} {self.working_database_path}")
        with open(self.working_database_path, "r") as stream:
            # if the file is empty load an empty dict
            self.database = yaml.safe_load(stream) or {}

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
        with open(self.database_path, "w") as stream:
            yaml.dump(self.database, stream)
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
        questionary.print(f"-" * 50, style="bold")

    def print_by_das(self, dasnick):
        for sample in self.database:
            if self.database[sample]["dbs"] == dasnick:
                self.print_by_nick(sample)

    def genweight_by_nick(self, nick):
        sample = self.database[nick]
        questionary.print(f"--- {nick} ---", style="bold")
        questionary.print(f"Current generator_weight: {sample['generator_weight']}")
        questionary.print(f"Will calcuate new generator_weight for the sameple (this will take some minutes ....)")
        # get the generator weight
        new_genweight = calculate_genweight(sample)
        questionary.print(f"New generator_weight: {new_genweight}")
        answer = questionary.confirm("Do you want to update the database?").ask()
        if answer:
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


def parse_args():
    """
    Function used to pass the available args of the mananger. Options are 'save_mode' and 'dataset_path'
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--save-mode", help="Save mode of the database", action="store_true"
    )
    parser.add_argument(
        "--database-path",
        help="Path to the database",
        type=str,
        default="sample_database/datasets.yaml",
    )
    args = parser.parse_args()
    return args


def finding_and_adding_sample(database):
    nick = questionary.text("Enter a DAS nick to add").ask()
    if nick in database.dasnicks:
        questionary.print("DAS nick is already in database")
        database.print_by_das(nick)
        return
    results = DASQuery(nick=nick, type="search_dataset").result
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
        ).ask()
        if len(answers) == 1 and answers[0] == "None of the above":
            questionary.print("Adding nothing")
            return
        if len(answers) != 1 and "None of the above" in answers:
            questionary.print("Invalid selection, Adding nothing")
            return
        else:
            for answer in answers:
                task = options.index(answer)
                details = DASQuery(nick=results[task]["dataset"], type="details").result
                database.add_sample(details)


def delete_sample(database):
    nick = questionary.text("Enter a nick to remove").ask()
    if nick in database.samplenicks:
        database.delete_by_nick(nick)
        return
    if nick in database.dasnicks:
        database.delete_by_das(nick)
        return
    questionary.print(f"No sample with nick {nick} found..")
    return


def print_sample(database):
    nick = questionary.text("Enter a nick to print").ask()
    if nick in database.samplenicks:
        database.print_by_nick(nick)
        return
    if nick in database.dasnicks:
        database.print_by_das(nick)
        return
    questionary.print(f"No sample with nick {nick} found..")
    return


def find_samples_by_nick(database):
    nick = questionary.autocomplete(
        "Enter a sample nick to search for",
        database.samplenicks,
    ).ask()
    if nick in database.samplenicks:
        database.print_by_nick(nick)
        return
    if nick in database.dasnicks:
        database.print_by_das(nick)
        return

def update_genweight(database):
    nick = questionary.autocomplete(
        "Enter a sample nick to search for",
        database.samplenicks,
    ).ask()
    if nick in database.samplenicks:
        database.genweight_by_nick(nick)
        return
    if nick in database.dasnicks:
        database.genweight_by_das(nick)
        return



def find_samples_by_das(database):
    nick = questionary.autocomplete(
        "Enter a sample nick to search for",
        list(database.dasnicks),
    ).ask()
    print(nick)
    if nick == "None":
        return
    if nick in database.dasnicks:
        database.print_by_das(nick)
        return


def create_production_file(database):
    # select era and sampletypes to process
    possible_eras = [str(x) for x in list(database.eras)]
    possible_samples = list(database.sample_types)
    selected_eras = questionary.checkbox(
        "Select eras to be added ", possible_eras
    ).ask()
    selected_sample_types = questionary.checkbox(
        "Select sampletypes to be added ", possible_samples
    ).ask()
    nicks = database.get_nicks(eras=selected_eras, sample_types=selected_sample_types)
    outputfile = questionary.text(
        "Name of the outputfile ?", default="samples.txt"
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


def startup():
    args = parse_args()
    questionary.print("Starting up Datasetmanager")
    db = SampleDatabase(args.database_path)
    questionary.print("Database loaded")
    db.status()
    processing = True
    available_tasks = [
        "Add a new sample",  # Task 0
        "Edit a sample (not implemented yet)",  # Task 1
        "Delete a sample",  # Task 2
        "Find samples (by nick)",  # Task 3
        "Find samples (by DAS name)",  # Task 4
        "Print details of a sample",  # Task 5
        "Create a production file",  # Task 6
        "Update genweight", # Task 7
        "Save and Exit",  # Task 8
        "Exit without Save",  # Task 9
    ]
    while processing:
        answer = questionary.select(
            "What do you want to do?",
            choices=available_tasks,
            show_selected=True,
            use_indicator=True,
        ).ask()
        task = available_tasks.index(answer)

        if task == 0:
            finding_and_adding_sample(db)
            continue
        elif task == 1:
            questionary.print("Editing not implemented yet")
            continue
        elif task == 2:
            delete_sample(db)
            continue
        elif task == 3:
            find_samples_by_nick(db)
            continue
        elif task == 4:
            find_samples_by_das(db)
            continue
        elif task == 5:
            print_sample(db)
            continue
        elif task == 6:
            create_production_file(db)
        elif task == 7:
            update_genweight(db)
            continue
        if task == 8:
            db.save_database()
            db.close_database()
            exit()
        elif task == 9:
            db.close_database()
            exit()


if __name__ == "__main__":
    startup()
