import os
import json

def update_dataset_files(datasets_file):
    # Load datasets.json
    with open(datasets_file, 'r') as f:
        datasets = json.load(f)

    for entry_name, entry_data in datasets.items():
        era = entry_data.get("era")
        type = entry_data.get("sample_type")
        generator_weight = entry_data.get("generator_weight")
        xsec = entry_data.get("xsec")

        # Construct the path to the corresponding JSON file
        era_dir = os.path.join(os.path.dirname(datasets_file), era)
        entry_file = os.path.join(era_dir, type, f"{entry_name}.json")

        if not os.path.exists(entry_file):
            print(f"File not found: {entry_file}")
            continue

        # Load the entry JSON file
        with open(entry_file, 'r') as f:
            try:
                entry_content = json.load(f)
            except json.JSONDecodeError:
                print(f"Invalid JSON in file: {entry_file}")
                continue

        # Check and update values if necessary
        updated = False
        if entry_content.get("generator_weight") != generator_weight:
            entry_content["generator_weight"] = generator_weight
            updated = True

        if entry_content.get("xsec") != xsec:
            entry_content["xsec"] = xsec
            updated = True

        # Write back to the file if updated
        if updated:
            with open(entry_file, 'w') as f:
                json.dump(entry_content, f, indent=4)
            print(f"Updated file: {entry_file}")
        else:
            print(f"No changes needed for file: {entry_file}")

if __name__ == "__main__":
    datasets_file = "datasets.json"  # Path to datasets.json
    update_dataset_files(datasets_file)