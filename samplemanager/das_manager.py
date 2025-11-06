import questionary
import subprocess
import json
import re
from helpers import default_entry, custom_style
from datetime import datetime


class DASQuery(object):
    def __init__(
        self,
        instance,
        nick,
        type,
        database_folder,
        redirector="root://xrootd-cms.infn.it//",
    ):
        self.database_folder = database_folder
        self.client = "/cvmfs/cms.cern.ch/common/dasgoclient"
        self.instance = instance
        self.nick = nick
        self.query = ""
        self.cmd = "{client} --query '{query}' --json"
        self.querytype = type
        self.response = {}
        self.result = {}
        self.redirector = redirector

        # run the query and parse the result
        self.query_and_parse()

    def query_and_parse(self):
        if self.querytype == "search_dataset":
            self.query = "dataset={} instance={}".format(self.nick, self.instance)
            self.run_query()
            self.parse_search()
        elif self.querytype == "details":
            print("Querying details")
            self.query = "dataset={} instance={}".format(self.nick, self.instance)
            self.run_query()
            self.parse_sample_details()
        elif self.querytype == "details_with_filelist":
            print("Querying details with filelist")
            self.query = "dataset={} instance={}".format(self.nick, self.instance)
            self.run_query()
            self.parse_sample_details()
            self.query = "file dataset={} instance={}".format(self.nick, self.instance)
            self.run_query()
            self.parse_sample_details_with_filelist()
        elif self.querytype == "filelist":
            print("Querying filelist")
            self.query = "file dataset={} instance={}".format(self.nick, self.instance)
            self.run_query()
            self.parse_sample_details_with_filelist()

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
        result: dict = self.response
        services = [res["das"]["services"][0] for res in result]
        if "dbs3:filesummaries" in services:
            try:
                details = result[services.index("dbs3:filesummaries")]["dataset"][0]
            except Exception as e:
                questionary.print(f"Could not parse filesummaries: {e}")
                return
        else:
            questionary.print("No filesummaries found - Check the query")
            return
        template = default_entry()
        template["dbs"] = self.nick
        template["nick"] = self._build_nick(self.nick)
        template["era"] = self._get_era(self.nick)
        template["nevents"] = details["nevents"]
        template["instance"] = self.instance
        template["nfiles"] = details["nfiles"]
        template["sample_type"] = self._build_sampletype(self.nick)
        if template["sample_type"] != "data" and template["sample_type"] != "emb":
            template["xsec"] = self._fill_xsec(self.nick)
            template["generator_weight"] = self._fill_generator_weight(self.nick)
        self.result = template

    def parse_sample_details_with_filelist(self):
        # get the filelist from query
        self.result["filelist"] = [self.redirector + res["file"][0]["name"] for res in self.response]

    def _fill_xsec(self, nick):
        xsec = questionary.text(
            f"Set xsec for {nick} in pb. Leave blank for value of 0.0"
        ).ask()
        if xsec == "" or xsec is None:
            return 0.0
        else:
            return float(xsec)

    def _fill_generator_weight(self, nick):
        gen_weight = questionary.text(
            f"Set generator_weight for {nick}. Leave blank for value of 0.0",
            style=custom_style,
        ).ask()
        if gen_weight == "" or gen_weight is None:
            return 0.0
        else:
            return float(gen_weight)

    def _build_nick(self, nick):
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
        # Extract version (e.g., v1, v2, v2-v1, etc.) from the third part if present
        version = ""
        if len(parts) > 2:
            import re
            # Match v1, v2, v2-v1, v3-v2, etc.
            match = re.search(r"(v[0-9]-v[0-9])", parts[1])
            if match and "Run3" not in parts[1] and "RunIII" not in parts[1]: 
                #add version number to nick only for data samples since multiple versions are used at the same time
                version = "_" + match.group(1)
        # nick is the first part of the DAS string + the second part till the first "_"
        # if there is no "_" in the second part, the whole second part is used
        nick = parts[0] + "_" + parts[1].split("_")[0] + ext_v + version
        return nick

    def _get_era(self, nick):
        # regex search for run2 UL eras
        m = re.search("UL16|UL17|UL18|UL2016|UL2017|UL2018|2016UL|2017UL|2018UL", nick)
        if m:
            if "16" in m.group(0):
                if any(t in nick for t in ("preVFP", "HIPM", "APV")):
                    return "2016preVFP"
                else:
                    return "2016postVFP"
            elif "17" in m.group(0):
                return "2017"
            elif "18" in m.group(0):
                return "2018"
            
        # regex search for run3 eras
        m = re.search("2022|2023|2024|2025|2026", nick)
        if m:
            if "2022" in m.group(0):
                if any(t in nick for t in ("postEE", "2022E", "2022F", "2022G")):
                    return "2022postEE"
                else:
                    return "2022preEE"
            elif "2023" in m.group(0):
                if any(t in nick for t in ("postBPix", "2023D")):
                    return "2023postBPix"
                else:                    
                    return "2023preBPix"
            else:
                return f"{m.group(0)}"

    def _build_sampletype(self, nick):
        process = "/" + nick.split("/")[1].lower()
        sampletype = "None"
        print(f"Setting sampletype for {process}")
        if "dy".lower() in process:
            return "dyjets"
        elif "TTT".lower() in process:
            return "ttbar"
        elif any(name.lower() in process for name in ["ST_t", "/TBbar", "/TbarB", "/TWminus", "/TbarWplus",]):
            return "singletop"
        elif any(name.lower() in process for name in ["/WZ_", "/WW_", "/ZZ_", "/WWto", "/WZto", "/ZZto",]):
            return "diboson"
        elif any(
            name.lower() in process for name in ["/WWW_", "/WWZ_", "/WZZ_", "/ZZZ_"]
        ):
            return "triboson"
        elif any(name.lower() in process for name in ["EWK"]):
            return "electroweak_boson"
        elif any(
            name.lower() in process
            for name in ["/wjet", "/w1jet", "/w2jet", "/w3jet", "/w4jet", "/Wto"]
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
                "/Muon",
                "/SingleElectron",
                "/SingleMuon",
                "/SinglePhoton",
                "/Tau",
                "/Zerobias",
                "/EGamma",
                "/ParkingVBF",
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
        elif any(name.lower() in process for name in ["NMSSM_XToYHTo2B2Tau"]):
            return "nmssm_Ybb"
        elif any(name.lower() in process for name in ["NMSSM_XToYHTo2Tau2B"]):
            return "nmssm_Ytautau"
        else:
            sampletype = questionary.text(
                f"No automatic sampletype found - Set sampletype for {nick} manually: ",
                style=custom_style,
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
