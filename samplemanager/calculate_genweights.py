import json
import subprocess
import uproot
from rich.progress import Progress
import numpy as np
import os
import yaml


def read_filelist_from_das(dbs):
    filedict = {}
    das_query = "file dataset={}".format(dbs)
    das_query += " instance=prod/global"
    cmd = [
        "/cvmfs/cms.cern.ch/common/dasgoclient --query '{}' --json".format(das_query)
    ]
    output = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    jsonS = output.communicate()[0]
    filelist = json.loads(jsonS)
    for file in filelist:
        filedict[file["file"][0]["name"]] = file["file"][0]["nevents"]
    return [
        "{prefix}/{path}".format(prefix="root://xrootd-cms.infn.it/", path=file)
        for file in filedict.keys()
    ]


# # # main function with RDF
# def calculate_genweight(dataset):
#     ROOT.EnableImplicitMT(2)
#     start = time.time()
#     filelist = read_filelist_from_das(dataset["dbs"])
#     # add the treename to each element in the filelist
#     try:
#         d = ROOT.RDataFrame("Events", filelist)
#         cuts = {"negative": "(genWeight<0)*1", "positive": "(genWeight>=0)*1"}
#         negative_d = d.Filter(cuts["negative"]).Count()
#         positive_d = d.Filter(cuts["positive"]).Count()
#         negative = negative_d.GetValue()
#         positive = positive_d.GetValue()
#         negfrac = negative / (negative + positive)
#         genweight = 1 - 2 * negfrac
#         print(f"Final genweight: {genweight}")
#         end = time.time()
#         print(f"Time: {end - start}")
#         return genweight
#     except:
#         print("Error when reading input files")
#         return 1.0


def calculate_genweight_uproot(dataset):
    print(f"Counting negative and positive genweights for {dataset['nick']}...")
    filelist = read_filelist_from_das(dataset["dbs"])
    negative = 0
    positive = 0
    # set a threshold that if more than 10% of the files fail, the function returns None
    threshold = len(filelist) // 10
    fails = 0

    print(f"Threshold for failed files: {threshold}")
    print(f"Number of files: {len(filelist)}")
    # loop over all files and count the number of negative and positive genweights
    with Progress() as progress:
        task = progress.add_task("Files read ", total=len(filelist))
        filelist = [file + ":Events" for file in filelist]
        for i, file in enumerate(filelist):
            try:
                events = uproot.open(file, timeout=5)
                array = events["genWeight"].array(library="np")
                negative += np.count_nonzero(array < 0)
                positive += np.count_nonzero(array >= 0)
                # print(f"File {i+1}/{len(filelist)} of {dataset['nick']} read")
                progress.update(task, advance=1)
            except Exception as e:
                print("Error when reading input file")
                print(e)
                fails += 1
            if fails > threshold:
                print("Too many files failed, returning None")
                return None
        print(f"Negative: {negative} // Positive: {positive}")
        negfrac = negative / (negative + positive)
        genweight = 1 - 2 * negfrac
        print(f"Final genweight: {genweight}")
        return genweight


def calculate_genweight_from_local_file(loc_file):
    if not (os.path.isfile(loc_file) and os.path.getsize(loc_file) > 0):
        print(f"File {loc_file} does not exist or is empty, your weight is 0.0")
    else:
        with open(loc_file, "r") as f:
            local_config = yaml.safe_load(f)
            filelist = local_config["filelist"]
            negative = 0
            positive = 0
            # set a threshold that if more than 10% of the files fail, the function returns None
            threshold = len(filelist) // 10
            fails = 0
            print(f"Threshold for failed files: {threshold}")
            print(f"Number of files: {len(filelist)}")
            # loop over all files and count the number of negative and positive genweights
            with Progress() as progress:
                task = progress.add_task("Files read ", total=len(filelist))
                filelist = [file + ":Events" for file in filelist]
                for i, file in enumerate(filelist):
                    try:
                        events = uproot.open(file, timeout=5)
                        array = events["genWeight"].array(library="np")
                        negative += np.count_nonzero(array < 0)
                        positive += np.count_nonzero(array >= 0)
                        # print(f"File {i+1}/{len(filelist)} of {dataset['nick']} read")
                        progress.update(task, advance=1)
                    except Exception as e:
                        print("Error when reading input file")
                        print(e)
                        fails += 1
                    if fails > threshold:
                        print("Too many files failed, returning None")
                        return None
                print(f"Negative: {negative} // Positive: {positive}")
                negfrac = negative / (negative + positive)
                genweight = 1 - 2 * negfrac
                print(f"Final genweight: {genweight}")
                return genweight
