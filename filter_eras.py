import json

# Input and output file paths
input_file = "/work/sgiappic/KingMaker/sample_database/nanoAOD_v12/datasets.json"
output_file = "/work/sgiappic/KingMaker/sample_database/nanoAOD_v12/datasets_filtered.json"

# Eras to filter
target_eras = {"2023preBPix", "2023postBPix"}

# Read the input JSON file
with open(input_file, "r") as infile:
    data = json.load(infile)

# Filter the entries based on the era
filtered_data = {
    key: value
    for key, value in data.items()
    if value.get("era") in target_eras
}

# Write the filtered data to the output JSON file
with open(output_file, "w") as outfile:
    json.dump(filtered_data, outfile, indent=4)

print(f"Filtered data written to {output_file}")