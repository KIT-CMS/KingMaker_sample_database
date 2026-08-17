# KingMaker_sample_database

Sample databases for KingMaker


## Add private sample production to the sample database

Private samples can be added to the database using the script
`samplemanager/scripts/add_private_samples.py`. The script takes the following
arguments:

```
usage: add_private_samples.py [-h] --private-sample-file PRIVATE_SAMPLE_FILE
                              [--sample-database-dir SAMPLE_DATABASE_DIR] [--num-workers NUM_WORKERS]

Add private samples to the sample database.

optional arguments:
  -h, --help            show this help message and exit
  --private-sample-file PRIVATE_SAMPLE_FILE
                        Path to the YAML file containing information about private samples
  --sample-database-dir SAMPLE_DATABASE_DIR
                        Path to the sample database directory (default: root directory of this sample database repository)
  --num-workers NUM_WORKERS
                        Number of worker processes to use for file processing (default: 1)
```

The only required argument is `--private-sample-file` which is a YAML file with
information needed to add samples to the database. The file consists of a list
of specifications to add samples to the database, e.g.:

```yaml
# ...

- nanoaod_version: nanoAOD_v15
  era: "2024"
  campaign: "RunIII2024Summer24NanoAODv15-150X-kit-private"
  sample_type: "hh2b2tau"
  redirector: "root://cmsdcache-kit-disk.gridka.de:1094"
  sample_dirs:
  - "/store/user/sdaigler/mc_production/GluGluHHto2B2Tau_Par-c2-0p00-kl-1p00-kt-1p00_TuneCP5_13p6TeV_powheg-pythia8/NanoAODv15-4af6f860"
  - "/store/user/sdaigler/mc_production/GluGluHHto2B2Tau_Par-c2-0p00-kl-3p00-kt-1p00_TuneCP5_13p6TeV_powheg-pythia8/NanoAODv15-6fc60a30"
  - "/store/user/sdaigler/mc_production/GluGluHHto2B2Tau_Par-c2-0p00-kl-5p00-kt-1p00_TuneCP5_13p6TeV_powheg-pythia8/NanoAODv15-4af6f860"
  - "/store/user/sdaigler/mc_production/GluGluHHto2B2Tau_Par-c2-0p00-kl-m1p00-kt-1p00_TuneCP5_13p6TeV_powheg-pythia8/NanoAODv15-6fc60a30"

# ...
```

All entries are mandatory. A sample database entry is created for each entry in
the `sample_dirs` list. The sample nick is constructed from the second-to-last
part of the sample directory path and the campaign name, concatenated with
`"_"`.
