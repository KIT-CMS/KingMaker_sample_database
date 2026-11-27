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


## Run-3 (13.6 TeV) cross sections

Every Run-3 MC entry of the H→ττ analysis carries `xsec_ref` with the `calculation` of its `xsec`, its perturbative `order` and the
`reference` it comes from. All values in pb; the same value is used in every era.

| Quantity | Value | Source |
|---|---|---|
| σ(DY→ℓℓ, m > 50) per flavour, NNLO QCD × NLO EW | 2091.7 | [MATRIX 13.6 TeV](https://twiki.cern.ch/twiki/bin/viewauth/CMS/MATRIXCrossSectionsat13p6TeV) r12 |
| σ(W⁻→ℓν) + σ(W⁺→ℓν) per flavour, NNLO QCD × NLO EW | 9009.5 + 12122.5 | same |
| σ(tt̄), NNLO+NNLL, m_t = 172.5 | 923.6 | [TtbarNNLO](https://twiki.cern.ch/twiki/bin/view/LHCPhysics/TtbarNNLO) r22 |
| σ(t-channel) t / t̄; σ(tW) t + t̄; σ(s-channel) t / t̄ | 145.0 / 87.2; 87.9; 7.244 / 4.534 | [SingleTopNNLORef](https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef) |
| Higgs production at m_H = 125.08 | ggF 52.23, VBF 4.078, W⁺H 0.8889, W⁻H 0.5677, ttH 0.5700 | [LHCHWG 13.6 TeV](https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap) |
| BR(H→ττ), BR(H→bb) | 0.062578, 0.5809 (m_H = 125.08) | [YR4 BR](https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR) |
| BR(W→ℓν) (3 flavours), BR(W→qq) | 0.3258, 0.6741 | PDG |
| Filter efficiencies ε_F | ggH 0.3869, VBF 0.4216, W⁺H 0.3582, W⁻H 0.3869, ZH 0.4030 | AN2025_055 Table 12 |
| Baselines (NLO / LO of the sample) | per sample | [XSDB](https://xsecdb-xsdb-official.app.cern.ch) |

- **DY and W jet bins:** the XSDB bin fractions renormalised to the MATRIX total, so the 0J/1J/2J bins sum to it
  (DY: 3 × 2091.7 = 6275.1, W: 3 × (9009.5 + 12122.5) = 63396); single-flavour samples ÷ 3. DY 10 < m < 50: XSDB NLO
  (MATRIX has no value below 50 GeV).
- **Diboson (powheg, qq-initiated):** XSDB × K, K = MATRIX σ_nNNLO_QCD×NLO_EW without the gg part over σ_NLO_QCD in
  the same final state (summed over the generated lepton flavours): WW 1.0729, ZZ→4ℓ 1.0535, ZZ→2ℓ2ν 1.0312 (also used
  for ZZ→2ℓ2q and ZZ→2ν2q), WZ 1.0538. gg→VV is not included (no sample). The powheg values reproduce MATRIX NLO QCD in
  the same final state to 0.3–1.4 %.
- **Top:** σ × the W branching ratios of the decay channel; tW is split equally between t and t̄.
- **Higgs signal:** σ × BR(H→ττ) × ε_F; ZH is qq→ZH only (the sample has no gg→ZH STXS bins); ttH(non-bb) × (1 − BR(bb)).
