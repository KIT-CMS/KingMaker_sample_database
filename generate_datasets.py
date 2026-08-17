import os
import json

def generate_datasets_json(base_dir, output_file):
    datasets = {}

    # Load existing datasets.json if it exists
    existing_datasets = {}
    if os.path.exists(base_dir + "/datasets.json"):
        with open(base_dir + "/datasets.json", 'r') as f:
            try:
                existing_datasets = json.load(f)
            except json.JSONDecodeError:
                print(f"Invalid JSON in existing file: datasets.json")

    # Iterate through all directories in the base directory
    for era in os.listdir(base_dir):
        era_path = os.path.join(base_dir, era)

        # Skip if era_path is not a directory
        if not os.path.isdir(era_path):
            continue

        for type in os.listdir(era_path):
            type_path =  os.path.join(era_path, type)
            if not os.path.isdir(type_path):
                continue

            # Iterate through all JSON files in the type directory
            for filename in os.listdir(type_path):
                if filename.endswith('.json'):
                    file_path = os.path.join(type_path, filename)

                    # Read the JSON file
                    with open(file_path, 'r') as f:
                        try:
                            file_content = json.load(f)
                        except json.JSONDecodeError:
                            print(f"Invalid JSON in file: {file_path}")
                            continue

                    # Remove 'filelist' key if it exists
                    file_content.pop('filelist', None)

                    # Use the first line of the entry as the key for comparison
                    entry_key = file_content.get('nick', None)

                    # Skip if the entry already exists in the existing datasets
                    if entry_key in existing_datasets:
                        continue

                    # Add the entry using the first line as the key
                    datasets[entry_key] = file_content

    # Write the datasets dictionary to the output file
    with open(output_file, 'w') as f:
        json.dump(datasets, f, indent=4)

    print(f"Generated datasets.json at {output_file}")

if __name__ == "__main__":
    base_dir = "nanoAOD_v12"  # Base directory containing era subdirectories
    output_file = "datasets_temp.json"  # Output file path
    generate_datasets_json(base_dir, output_file)