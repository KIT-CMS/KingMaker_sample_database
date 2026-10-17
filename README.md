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


## Run-2 Higgs and HH cross sections in `nanoAOD_v15` (bbtautau v7)

All Run-2 (13 TeV) Higgs and HH entries in `nanoAOD_v15/` use mH = 125.00 GeV. The
Run-3 entries and the `nanoAOD_v9`/`nanoAOD_v12` databases are unchanged.

Inputs:

| Quantity | Value | Source |
|---|---|---|
| σ(ggH) N3LO | 48.58 pb | LHCHWG YR4, CERNYellowReportPageAt13TeV r29, mH = 125.00 |
| σ(VBF) | 3.782 pb | same |
| σ(W⁺H) / σ(W⁻H) | 0.8400 / 0.5328 pb | same |
| σ(ZH), incl. ggZH | 0.8839 pb | same |
| σ(ggZH) | 0.1227 pb | same |
| σ(ttH) | 0.5071 pb | same |
| σ(ggF HH) | 30.40 fb | LHCHWGHHRecommendations (2026-09-15, LHCHWG-2026-010) |
| BR(H→bb) / BR(H→ττ) / BR(H→WW) | 0.5824 / 0.06272 / 0.2137 | LHCHWG YR4, CERNYellowReportPageBR r23, mH = 125.00 |
| BR(W→ℓν), ℓ = e, μ, τ | 3 × 0.1086 = 0.3258 | PDG |
| BR(Z→ℓℓ), ℓ = e, μ, τ | 3 × 0.033658 = 0.100974 | PDG |
| BR(Z→νν) / BR(Z→qq) / BR(Z→bb) | 0.2000 / 0.6991 / 0.1512 | PDG |

Resulting values:

- **HH, κλ = 1:** 30.40 fb × 2 × 0.5824 × 0.06272 = **0.002221 pb** (`GluGluToHHTo2B2Tau` and
  `GluGluToHHTo2B2T_kl-1p00_kt-1p00_c2-0p00`).
- **HH, κλ ≠ 1 (own choice):** The new HH-WG page says that κλ scans "require their own normalisation" and publishes
  no κλ dependence. We take the legacy polynomial σ(κλ) = 68.5624 − 48.3673 κλ + 10.5635 κλ² fb (30.76 fb at κλ = 1)
  and scale it by 30.40/30.76, times 2 × 0.5824 × 0.06272: κλ = 0 → 0.00495 pb, κλ = 2.45 → 0.0009725 pb,
  κλ = 5 → 0.006557 pb. This rescaling is our choice, not an HH-WG recommendation.
- **ggH/VBF→ττ:** 48.58 × 0.06272 = 3.04694 pb, 3.782 × 0.06272 = 0.237207 pb.
- **VBF H→bb:** 3.782 × 0.5824 = 2.20264 pb. **ttH:** 0.5071 × 0.5824 = 0.295335 pb (bb),
  0.5071 × (1 − 0.5824) = 0.211765 pb (non-bb).
- **W±H, H→bb, W→ℓν:** 0.8400 × 0.5824 × 0.3258 = 0.159387 pb, 0.5328 × 0.5824 × 0.3258 = 0.101097 pb.
- **qq→ZH, H→bb:** σ(ZH) − σ(ggZH) = 0.8839 − 0.1227 = **0.7612 pb**, because the ggZH→bb samples are separate
  entries. × 0.5824 × BR(Z): ZToLL 0.0447641, ZToNuNu 0.0886646, ZToQQ 0.309927, ZToBB 0.0670304 pb.
- **ggZH, H→bb:** 0.1227 × 0.5824 × BR(Z): ZToLL 0.00721565, ZToNuNu 0.0142921, ZToQQ 0.049958, ZToBB 0.0108048 pb.
- **VH→ττ (`rem_htautau`):** W⁺H 0.8400 × 0.06272 = 0.05268 pb, W⁻H 0.5328 × 0.06272 = 0.03342 pb. `ZHToTauTau` is a
  qq→ZH sample, but no ggZH→ττ sample exists, so it gets the total σ(ZH) including ggZH as a proxy:
  0.8839 × 0.06272 = 0.05544 pb. (The earlier v9 values 0.0545 / 0.0516 / 0.0328 pb are for mH = 125.38.)
- **ggH/VBF→WW→2ℓ2ν (2017):** 48.58 × 0.2137 × 0.3258² = 1.10196 pb, 3.782 × 0.2137 × 0.3258² = 0.0857883 pb.

Shifts against the previous values (`main` f56dd8d3, used by the bbtautau v6 production) for the entries that existed
there:

| Entry (2018 unless noted) | Before (pb) | Now (pb) | Shift |
|---|---|---|---|
| GluGluToHHTo2B2Tau | 0.002246 | 0.002221 | −1.1 % |
| GluGluHToTauTau (2017, 2018) | 3.01620 | 3.04694 | +1.0 % |
| VBFHToTauTau (2017, 2018) | 0.239151 | 0.237207 | −0.8 % |
| VBFHToBB | 2.22069 | 2.20264 | −0.8 % |
| WplusH_HToBB_WToLNu / WminusH_HToBB_WToLNu | 0.161284 / 0.101135 | 0.159387 / 0.101097 | −1.2 % / −0.04 % |
| ZH_HToBB_ZToBB / ZToNuNu / ZToQQ | 0.0781963 / 0.103434 / 0.361554 | 0.0670304 / 0.0886646 / 0.309927 | −14.3 % |
| ZH_HToBB_ZToLL | 0.0567544 | 0.0447641 | −21.1 % |
| ggZH_HToBB_ZToBB / ZToQQ | 0.00934105 / 0.04319 | 0.0108048 / 0.049958 | +15.7 % |
| ggZH_HToBB_ZToLL / ZToNuNu | 0.006185 / 0.01222 | 0.00721565 / 0.0142921 | +16.7 % / +17.0 % |
| ttHTobb / ttHToNonbb | 0.309254 / 0.221746 | 0.295335 / 0.211765 | −4.5 % |
| GluGluHToWWTo2L2Nu (2017) | 1.12944 | 1.10196 | −2.4 % |
| VBFHToWWTo2L2Nu (2017) | 0.08816 | 0.0857883 | −2.7 % |

Summed over qq→ZH and ggZH, the 2018 ZH→bb rate drops by 11 % (ZToQQ, ZToBB, ZToNuNu) and 17 % (ZToLL). All other
Run-2 Higgs and HH entries are new in the v7 registration and use the values above in every era.
