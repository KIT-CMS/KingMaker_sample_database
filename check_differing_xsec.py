import json
from collections import defaultdict

# Load the datasets.json file
datasets_file = "/work/sgiappic/KingMaker/sample_database/nanoAOD_v12/datasets.json"

with open(datasets_file, "r") as file:
    datasets = json.load(file)

# Group entries by the portion of "dbs" between the first two slashes
grouped_entries = defaultdict(list)

for key, entry in datasets.items():
    if isinstance(entry, dict):  # Ensure the entry is a dictionary
        dbs = entry.get("dbs", "")
        if dbs:
            parts = dbs.split("/")
            if len(parts) > 2:
                group_key = f"/{parts[1]}/{parts[2]}"
                grouped_entries[group_key].append(entry)

# Check for differing "xsec" values within each group
differing_xsec_samples = {}

for group_key, entries in grouped_entries.items():
    xsec_values = {entry.get("xsec") for entry in entries if "xsec" in entry}
    if len(xsec_values) > 1:
        differing_xsec_samples[group_key] = [entry["dbs"] for entry in entries]

# Write the results to a text file
output_file = "/work/sgiappic/KingMaker/sample_database/differing_xsec_samples.txt"
# Debugging: Print xsec values for groups with differences
print("Checking xsec values for groups with differences:")
with open(output_file, "w") as file:
    if differing_xsec_samples:
        for group_key, dbs_list in differing_xsec_samples.items():
            file.write(f"Group: {group_key}\n")
            for dbs in dbs_list:
                file.write(f"  {dbs}\n")
            file.write("-------------\n\n")
    else:
        print("No groups with differing xsec values found.")
        file.write("No groups with differing xsec values found.\n")

print(f"Samples with differing xsec values have been saved to {output_file}")