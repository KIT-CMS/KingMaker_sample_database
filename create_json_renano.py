import json
import os

# Path to the text file with keys
keys_file = "/work/sgiappic/KingMaker/samples_2024_sig.txt"
# Directory containing the JSON files
search_dir = "/work/sgiappic/KingMaker/sample_database/nanoAOD_v15/2024/"
# Output file
output_file = "renano_v15_list.json"

# Read keys
with open(keys_file, "r") as f:
    keys = [line.strip() for line in f if line.strip()]

result = {}

# Build a set for faster lookup
keys_set = set(keys)

# Walk through all directories and files
for root, dirs, files in os.walk(search_dir):
    for file in files:
        name, ext = os.path.splitext(file)
        if ext == ".json" and name in keys_set:
            json_path = os.path.join(root, file)
            with open(json_path, "r") as jf:
                data = json.load(jf)
                if "filelist" in data:
                    result[name] = data["filelist"]

# Save result
with open(output_file, "w") as out:
    json.dump(result, out, indent=2)