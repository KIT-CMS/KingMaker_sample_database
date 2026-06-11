"""
Script to generate a JSON file with cross sections at 13.6 TeV for various MC samples.
"""

import argparse
import json
import os
from typing import Any, Union

SCRIPT_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)


#
# ARGUMENT PARSER
#


def parse_arguments():
    # Create the argument parser
    parser = argparse.ArgumentParser(
        description="Create JSON file with cross section database for 13.6 TeV samples.",
    )

    # Add arguments to the command-line parser
    parser.add_argument(
        "-o",
        "--output_file",
        type=str,
        help="Path to output JSON file.",
    )

    # Get the arguments
    args = parser.parse_args()

    return args


#
# CROSS SECTION DATABASE
#


# Global cross section database
__cross_sections: list[dict[str, Any]] = []


def add_cross_section(
    *,
    xsec: float,
    order: str,
    reference: str,
    sample_names: Union[str, list[str]],
):
    """
    Add a cross section to the cross section database.

    The cross section is interpreted as value in picobarn (pb).
    
    Here, a sample name corresponds to the first part of a DAS key
    `/<sample_name>/<campaign_tag>/<tier>`. For `sample_names`, either
    a single sample name or a list of sample names is passed. If
    `sample_names` is a single string, it is wrapped in a list.
    The sample names are ordered alphabetically.

    The function creates a dictionary with the following structure:

    ```python
    {
        "xsec": xsec,
        "order": order,
        "reference": reference,
        "sample_names": sample_names,
    }
    ```

    :param xsec: Process cross section (in pb).

    :param order: Perturbative order of the cross section calculation.

    :param reference: Reference information for the cross section value (e.g. publication or webpage
                      link).

    :param sample_names: Sample name or list of sample names.

    :raises ValueError: When `sample_names` is an empty list.
    """
    # Get the global cross section database
    global __cross_sections

    # If sample_names is a single string, wrap a list around it
    if isinstance(sample_names, str):
        sample_names = [sample_names]
    sample_names.sort()

    # Raise an exception when no sample name is provided
    if len(sample_names) == 0:
        raise ValueError("At least one sample name must be provided.")

    # Create the cross section database entry as a dictionary
    process_cross_section = {
        "xsec": xsec,
        "order": order,
        "reference": reference,
        "sample_names": sample_names,
    }

    # Append the cross section to the global database
    __cross_sections.append(process_cross_section)


def get_cross_section_db(sort=False) -> list[dict[str, Any]]:
    """
    Get the cross section database.

    Each entry in the database has the following structure:

    ```python
    {
        "xsec": <cross section in pb>,
        "order": "<perturbative order>",
        "reference": "<list of references>",
        "sample_names": ["<sample_name1>", "<sample_name2>", ...],
    }
    ```

    :param sort: If `True`, the database entries are sorted alphabetically by the first sample name.
                 Default: `False`.
    
    :return: List of cross section database entries.
    """
    global __cross_sections
    if sort:
        return sorted(__cross_sections, key=lambda cs: cs["sample_names"][0])
    return __cross_sections


#
# BRANCHING FRACTIONS
#


# W branching fractions
# https://pdg.lbl.gov/2022/listings/rpp2022-list-w-boson.pdf
_br_w_leptons = 3 * 0.1086  # sum of W -> e nu, mu nu, tau nu
_br_w_hadrons = 0.6741      # W -> hadrons

# Z branching fractions
# https://pdg.lbl.gov/2022/listings/rpp2022-list-z-boson.pdf
_br_z_leptons = 3 * 0.03658  # sum of Z -> e+ e-, mu+ mu-, tau+ tau-
_br_z_inv = 0.2000           # sum of Z -> nu nu (all neutrono flavours)
_br_z_hadrons = 0.6991       # Z -> hadrons
_br_z_bb = 0.1512            # Z -> bb

# Higgs branching fractions for decay modes (at 125 GeV)
# https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWGBRs
_br_h_bb = 0.5824           # H -> bb
_br_h_ww = 0.2137           # H -> WW
_br_h_tautau = 0.06272      # H -> tau tau
_br_h_zz = 0.02619          # H -> ZZ
_br_h_gammagamma = 0.00227  # H -> gamma gamma

# Higgs branching fractions for four-fermion final states (at 125 GeV)
# https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWGBRs
_br_h_llll = 2.745e-4             # H -> l+ l- l+ l-, all lepton flavours
_br_h_llll_emu_only = 1.240e-4    # H -> l+ l- l+ l-, only electron and muon lepton flavours
_br_h_eeee = 3.254e-5             # H -> e+ e- e+ e-
_br_h_eemumu = 5.897e-5           # H -> e+ e- mu+ mu-
_br_h_llnunu = 2.338e-2           # H -> l+ l- nu nu, all lepton flavours
_br_h_llnunu_emu_only = 1.055e-2  # H -> l+ l- nu nu, only electron and muon lepton flavours
_br_h_eenunu = 2.518e-3           # H -> e+ nu_e e- nu_e
_br_h_emununu = 2.519e-3          # H -> e+ nu_e mu- nu_mu


#
# TOP QUARK PROCESSES (tt, single-top, tt+X)
#

# Top quark pair production

# Total tt cross section at 13.0 TeV, must be multiplied with BRs of the W bosons
_xsec_tt_total = 833.9

add_cross_section(
    xsec=_xsec_tt_total * _br_w_leptons**2,
    order="NNLO(QCD)+NNLL",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/TtbarNNLO; https://arxiv.org/abs/1112.5675",
    sample_names=[
        "TTTo2L2Nu_TuneCP5_13TeV-powheg-pythia8",
        "TTTo2L2Nu_TuneCP5up_13TeV-powheg-pythia8",
    ],
)

add_cross_section(
    xsec=_xsec_tt_total * 2 * _br_w_leptons * _br_w_hadrons,
    order="NNLO(QCD)+NNLL",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/TtbarNNLO; https://arxiv.org/abs/1112.5675",
    sample_names=[
        "TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8",
    ],
)

add_cross_section(
    xsec=_xsec_tt_total * _br_w_hadrons**2,
    order="NNLO(QCD)+NNLL",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/TtbarNNLO; https://arxiv.org/abs/1112.5675",
    sample_names=[
        "TTToHadronic_TuneCP5_13TeV-powheg-pythia8",
    ],
)

# Single top quark production, t-channel processes

# Total single top (t channel) cross section for t and anti-t
# https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef
_xsec_tbq_t_total = 134.2 
_xsec_tbq_antit_total = 80.0

add_cross_section(
    xsec=_xsec_tbq_t_total,
    order="NNLO(QCD)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef; https://arxiv.org/abs/2012.01574",
    sample_names=[
        "ST_t-channel_top_4f_InclusiveDecays_TuneCP5_13TeV-powheg-madspin-pythia8",
        "ST_t-channel_top_5f_InclusiveDecays_TuneCP5_13TeV-powheg-pythia8",
    ],
)

# add_cross_section(
#     xsec=_xsec_tbq_t_total * _br_w_leptons,
#     order="NNLO(QCD)",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef; https://arxiv.org/abs/2012.01574",
#     sample_names="TBbarQtoLNu-t-channel-4FS_TuneCP5_13p6TeV_powheg-madspin-pythia8",
# )

add_cross_section(
    xsec=_xsec_tbq_antit_total,
    order="NNLO(QCD)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef; https://arxiv.org/abs/2012.01574",
    sample_names=[
        "ST_t-channel_antitop_4f_InclusiveDecays_TuneCP5_13TeV-powheg-madspin-pythia8",
        "ST_t-channel_antitop_5f_InclusiveDecays_TuneCP5_13TeV-powheg-pythia8",
    ],
)

# add_cross_section(
#     xsec=_xsec_tbq_antit_total * _br_w_leptons,
#     order="NNLO(QCD)",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef; https://arxiv.org/abs/2012.01574",
#     sample_names="TbarBQtoLNu-t-channel-4FS_TuneCP5_13p6TeV_powheg-madspin-pythia8",
# )

# Single top quark production, s-channel processes
_xsec_tbl_t_total = 6.828
_xsec_tbl_antit_total = 4.245

add_cross_section(
    xsec=_xsec_tbl_t_total * _br_w_leptons,
    order="NNLO(QCD)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef; no publication referenced",
    sample_names=[
        "ST_s-channel_4f_leptonDecays_TuneCP5_13TeV-amcatnlo-pythia8",
    ],
)

# add_cross_section(
#     xsec=_xsec_tbl_antit_total * _br_w_leptons,
#     order="NNLO(QCD)",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef; no publication referenced",
#     sample_names=[
#         "TbarBtoLminusNuB-s-channel-4FS_TuneCP5_13p6TeV_amcatnlo-pythia8",
#         "TbarBtoLNu-s-channel_TuneCP5_13TeV_powheg-pythia8",
#     ],
# )


add_cross_section(
    xsec=_xsec_tbl_t_total * _br_w_hadrons,
    order="NNLO(QCD)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef; no publication referenced",
    sample_names=[
        "ST_s-channel_4f_hadronicDecays_TuneCP5_13TeV-amcatnlo-pythia8",
    ],
)

# add_cross_section(
#     xsec=_xsec_tbl_antit_total * _br_w_hadrons,
#     order="NNLO(QCD)",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef; no publication referenced",
#     sample_names=[
#         "TbarBto2Q-s-channel_TuneCP5_13p6TeV_powheg-pythia8",
#     ],
# )


# Single top quark production, tW processes

# Total tW cross section (for t Wplus and tbar Wminus)
# The tW cross section is only provided for tW + tbarW, so it has to be divided by 2 in the *Wplus*
# and *Wminus* sample_names. Further, the cross section has to be multiplied with the correct BRs of the
# W bosons
_xsec_tw_total = 79.3

add_cross_section(
    xsec=_xsec_tw_total / 2,
    order="NLO(QCD)+NNLL",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef; https://arxiv.org/abs/2102.11300",
    sample_names=[
        "ST_tW_top_5f_inclusiveDecays_TuneCP5_13TeV-powheg-pythia8",
        "ST_tW_antitop_5f_inclusiveDecays_TuneCP5_13TeV-powheg-pythia8",
    ],
)



# Some tt+X processes with cross sections extracted from the sample_names (taken from the CMS cross section database)

_reference = "https://xsecdb-xsdb-official.app.cern.ch"
for _sample_name, _xsec, _order in [
    ("TTZZTo4b_TuneCP5_13TeV-madgraph-pythia8", 0.001391, "LO(QCD)"),
    ("TTWH_TuneCP5_13TeV-madgraph-pythia8", 0.001143, "LO(QCD)"),
    ("TTWW_TuneCP5_13TeV-madgraph-pythia8", 0.006992, "LO(QCD)"),
    ("TTWZ_TuneCP5_13TeV-madgraph-pythia8", 0.002448, "LO(QCD)"),
    ("TTZH_TuneCP5_13TeV-madgraph-pythia8", 0.001136, "LO(QCD)"),
    ("TTZToLLNuNu_M-10_TuneCP5_13TeV-amcatnlo-pythia8", 0.2439, "NLO/unknown)"),
    ("TTZToLL_M-1to10_TuneCP5_13TeV-amcatnlo-pythia8", 0.0537, "NLO/unknown)"),
    ("TTZToNuNu_TuneCP5_13TeV_amcatnlo-pythia8", 0.1487, "NLO)"),
    ("TTZToQQ_TuneCP5_13TeV-amcatnlo-pythia8", 0.5113, "NLO/unknown)"),
    ("TTZZ_TuneCP5_13TeV-madgraph-pythia8", 0.001386, "LO(QCD)"),
    # Run3 names, find run2 if missing:
    # ("TTG-1Jets_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFXold-pythia8", 0.4114, "NLO(QCD)"),
    # ("TTG-1Jets_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFXold-pythia8", 4.216, "NLO(QCD)"),
    # ("TTG-1Jets_PTG-200_TuneCP5_13p6TeV_amcatnloFXFXold-pythia8", 0.1284, "NLO(QCD)"),
    # ("TTLL_MLL-4to50_TuneCP5_13p6TeV_amcatnlo-pythia8", 0.03949, "NLO(QCD)"),
    # ("TTLL_MLL-50_TuneCP5_13p6TeV_amcatnlo-pythia8", 0.08646, "NLO(QCD)"),
    # ("TTLNu-1Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8", 0.2505, "NLO(QCD)"),
    # ("TTLNu-EWK_TuneCP5_13p6TeV_amcatnlo-pythia8", 0.01769, "NLO(QCD)"),
    # ("TTNuNu_TuneCP5_13p6TeV_amcatnlo-pythia8", 0.1638, "NLO(QCD)"),
    # ("TTZ-ZtoQQ-1Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8", 0.6603, "NLO(QCD)"),
    # ("TTWW_TuneCP5_13p6TeV_madgraph-madspin-pythia8", 0.008203, "LO(QCD)"),
    # ("TTZZ_TuneCP5_13p6TeV_madgraph-madspin-pythia8", 0.001579, "LO(QCD)"),
    # ("TTTT_TuneCP5_13p6TeV_amcatnlo-pythia8", 0.009652, "NLO(QCD)"),
]:
    add_cross_section(
        xsec=_xsec,
        order=_order,
        reference=_reference,
        sample_names=_sample_name,
    )


#
# DRELL-YAN PRODUCTION, MADGRAPH AMC@NLO (NLO)
#


# Total DY cross section at 13 TeV
# To also normalize the jet-binned sample_names with higher precision, we need to calculate a k factor,
# with which the NLO cross sections of the jet-binned sample_names can be scaled to the more precise NNLO
# cross section values. The cross section values correspond to DY -> l l production, so in general,
# they must not be multiplied with the BR of the Z boson into leptons.
# - MadGraph cross section: https://xsecdb-xsdb-official.app.cern.ch
# - NNLO cross section: https://twiki.cern.ch/twiki/bin/viewauth/CMS/StandardModelCrossSectionsat13TeV
_xsec_dy_m50_total_madgraph = 5379.0 # DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8
_xsec_dy_m50_total_amcatnlo = 6424.0 # DYJetsToLL_M-50_TuneCP5_13TeV-amcatnloFXFX-pythia8
_xsec_dy_m50_total_nnlo = 3 * 2025.74
_k_factor_dy_m50_madgraph_nnlo = _xsec_dy_m50_total_nnlo / _xsec_dy_m50_total_madgraph
_k_factor_dy_m50_amcatnlo_nnlo = _xsec_dy_m50_total_nnlo / _xsec_dy_m50_total_amcatnlo

_reference="https://xsecdb-xsdb-official.app.cern.ch; https://twiki.cern.ch/twiki/bin/viewauth/CMS/StandardModelCrossSectionsat13TeV;",
_order="NNLO(QCD)xNLO(EW)",
for _sample_name, _madgraph_xsec in [
    # samples binned in number of jets

    # samples binned in di-lepton pT

    # samples binned in (di-lepton mass, hadronic recoil)
    
    # samples binned in Z boson pT
    ("DYJetsToLL_LHEFilterPtZ-0To50_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8", 1485.0),
    ("DYJetsToLL_LHEFilterPtZ-50To100_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8", 397.4),
    ("DYJetsToLL_LHEFilterPtZ-100To250_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8", 97.2),
    ("DYJetsToLL_LHEFilterPtZ-250To400_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8", 3.701),
    ("DYJetsToLL_LHEFilterPtZ-400To650_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8", 0.5086),
    ("DYJetsToLL_LHEFilterPtZ-650ToInf_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8", 0.04728)
    
]:
    add_cross_section(
        xsec=_madgraph_xsec * _k_factor_dy_m50_amcatnlo_nnlo,
        order=_order,
        reference=_reference,
        sample_names=_sample_name,
    )


#
# W PRODUCTION, MADGRAPH (LO)
#


# Total W cross section at 13 TeV
# To also normalize the jet-binned sample_names with higher precision, we need to calculate a k factor,
# with which the NLO cross sections of the jet-binned sample_names can be scaled to the more precise NNLO
# cross section values. The cross section values correspond to W -> l nu production, so in general,
# they must not be multiplied with the BR of the W boson into leptons.
# - MadGraph cross section: https://xsecdb-xsdb-official.app.cern.ch
# - NNLO cross section: https://twiki.cern.ch/twiki/bin/viewauth/CMS/StandardModelCrossSectionsat13TeV
_xsec_w_total_madgraph = 53940.0
_xsec_w_total_nnlo = 3 * (11811.4 + 8677.3 )
_k_factor_w_madgraph_nnlo = _xsec_w_total_nnlo / _xsec_w_total_madgraph

# Inclusive W -> ell nu samples

add_cross_section(
    xsec=_xsec_w_total_nnlo,
    order="NNLO(QCD)xNLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/viewauth/CMS/StandardModelCrossSectionsat13TeV",
    sample_names="WJetsToLNu_TuneCP5_13TeV-madgraphMLM-pythia8",
)

# Exclusive W -> l nu samples

_order = "NNLO(QCD)xNLO(EW)"
_reference = "https://xsecdb-xsdb-official.app.cern.ch; https://twiki.cern.ch/twiki/bin/viewauth/CMS/StandardModelCrossSectionsat13TeV;"
for _sample_name, _xsec in [
    # W -> ell nu, binned in number of jets
    
    # W -> ell nu, binned in sum of all jet pT (HT)
    ("WJetsToLNu_HT-70To100_TuneCP5_13TeV-madgraphMLM-pythia8",1283),
    ("WJetsToLNu_HT-100To200_TuneCP5_13TeV-madgraphMLM-pythia8", 1244.0),
    ("WJetsToLNu_HT-200To400_TuneCP5_13TeV-madgraphMLM-pythia8", 337.8),
    ("WJetsToLNu_HT-400To600_TuneCP5_13TeV-madgraphMLM-pythia8", 44.93),
    ("WJetsToLNu_HT-600To800_TuneCP5_13TeV-madgraphMLM-pythia8", 11.19),
    ("WJetsToLNu_HT-800To1200_TuneCP5_13TeV-madgraphMLM-pythia8", 4.926),
    ("WJetsToLNu_HT-1200To2500_TuneCP5_13TeV-madgraphMLM-pythia8", 1.152),

    # W -> ell nu, binned in (lepton-neutrino system mass, hadronic recoil)
]:
    add_cross_section(
        xsec=_xsec * _k_factor_w_madgraph_nnlo,
        order=_order,
        reference=_reference,
        sample_names=_sample_name,
    )


#
# W PRODUCTION, MADGRAPH AMC@NLO (NLO)
#
_xsec_w_total_amcatnlo = 66680.0
_k_factor_w_nlo_nnlo = _xsec_w_total_nnlo / _xsec_w_total_amcatnlo

# Inclusive W -> ell nu samples

add_cross_section(
    xsec=_xsec_w_total_nnlo,
    order="NNLO(QCD)xNLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/viewauth/CMS/StandardModelCrossSectionsat13TeV",
    sample_names="WJetsToLNu_TuneCP5_13TeV-amcatnloFXFX-pythia8",
)

_order="NNLO(QCD)xNLO(EW)"
_reference="https://xsecdb-xsdb-official.app.cern.ch; https://twiki.cern.ch/twiki/bin/viewauth/CMS/StandardModelCrossSectionsat13TeV"
for _sample_name, _xsec in [
    # Exclusive W -> l nu samples, binned in number of jets
    ("WJetsToLNu_0J_TuneCP5_13TeV-amcatnloFXFX-pythia8", 52780),
    ("WJetsToLNu_1J_TuneCP5_13TeV-amcatnloFXFX-pythia8", 8832),
    ("WJetsToLNu_2J_TuneCP5_13TeV-amcatnloFXFX-pythia8", 3276),
    
    # Exclusive W -> l nu samples, binned in pt
    ("WJetsToLNu_Pt-100To250_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8", 733.1),
    ("WJetsToLNu_Pt-250To400_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8", 27.92),
    ("WJetsToLNu_Pt-400To600_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8",  3.547),
    ("WJetsToLNu_Pt-600ToInf_MatchEWPDG20_TuneCP5_13TeV-amcatnloFXFX-pythia8", 0.5371),
]:
    add_cross_section(
        xsec=_xsec * _k_factor_w_nlo_nnlo,
        order=_order,
        reference=_reference,
        sample_names=_sample_name,
    )


#
# DIBOSON PRODUCTION
#


# TODO The cross sections on https://twiki.cern.ch/twiki/bin/viewauth/CMS/StandardModelCrossSectionsat13TeV seem way too high. That's why we currently just use the cross sections from the sample database.

## Cross sections of WW, ZZ production at 13.6 TeV for leptonic final states
## N.B.: To obtain the "_xsec_zz_or_ww_x" values, we subtract the gg -> VV from the pp -> VV production cross section.
## Taken from https://twiki.cern.ch/twiki/bin/viewauth/CMS/StandardModelCrossSectionsat13TeV
## Order: nNNLO(QCD)xNLO(EW) (subtracted gg -> X at NLO)
# # These are still the 13.6 TeV values !!!
# _xsec_zz_or_ww_eemumu = 0.387 - 0.0443
# _xsec_zz_or_ww_eeee = 0.1633 - 0.013
# _xsec_zz_or_ww_emunuenumu = 1.5589 - 0.1497
# _xsec_zz_or_ww_eenuenue = 1.6736 - 0.1602

# Cross sections of WZ production at 13.6 TeV for leptonic final states
# Taken from https://twiki.cern.ch/twiki/bin/viewauth/CMS/StandardModelCrossSectionsat13TeV
# Order: NNLO(QCD)xNLO(EW), gg -> X at NLO
# _xsec_wz_eemuminusnumu = 0.2385
# _xsec_wz_eeeminusnue = 0.2366
# _xsec_wz_eemuplusnumu = 0.3474
# _xsec_wz_eeeplusnue = 0.3459

# total WW, ZZ, WZ cross sections at 13.6 TeV
# Some of the cross sections are way to high when comparing with Run 2 cross sections, e.g. at
# https://twiki.cern.ch/twiki/bin/viewauth/CMS/StandardModelCrossSectionsat13TeV
# - For WW, we obtain 119.48 in Run 3 and 118.7 in Run 2 -> should be fine
# - For ZZ, we obtain 120.19 in Run 3 and 13.04 in Run 2 -> multiply with magic factor 1/9 to get correct order (=> 13.35)
# - For WZ, we obtain 146.62 in Run 3 and 59.11 in Run 2 -> multiply with magic factor 2/5 to get correct order (=> 58.65)
#_xsec_ww_total = _xsec_zz_or_ww_emunuenumu / (_br_w_leptons / 3)**2
#_xsec_zz_total = ( _xsec_zz_or_ww_eeee / (_br_z_leptons / 3)**2 + _xsec_zz_or_ww_eemumu / (2 * (_br_z_leptons / 3)**2) ) / (2 * 9)
#_xsec_wz_total = (2 / 5) * (_xsec_wz_eeeplusnue + _xsec_wz_eeeminusnue) / (_br_w_leptons / 3 * _br_z_leptons / 3)
# Calculated from https://xsecdb-xsdb-official.app.cern.ch
# - for WW: WWto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8
# - for WZ: WZto3LNu_TuneCP5_13p6TeV_powheg-pythia8
# - for ZZ: ZZto4L_TuneCP5_13p6TeV_powheg-pythia8
#_xsec_ww_total = 11.79 / _br_w_leptons**2
#_xsec_wz_total = 4.924 / (_br_w_leptons * _br_z_leptons)
#_xsec_zz_total = 0.139 / _br_z_leptons**2

# Inclusive sample_names (Pythia)

add_cross_section(
    xsec=76.25,
    order="LO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="WW_TuneCP5_13TeV-pythia8",
)

add_cross_section(
    xsec=27.55,
    order="LO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="WZ_TuneCP5_13TeV-pythia8",
)

add_cross_section(
    xsec=12.23,
    order="LO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="ZZ_TuneCP5_13TeV-pythia8",
)


# WW production, split in final states

add_cross_section(
    xsec=51.65,
    order="NLO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="WWTo1L1Nu2Q_4f_TuneCP5_13TeV-amcatnloFXFX-pythia8",
)

add_cross_section(
    xsec=11.09,
    order="NLO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="WWTo2L2Nu_TuneCP5_13TeV-powheg-pythia8",
)

add_cross_section(
    xsec=51.03,
    order="NLO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="WWTo4Q_4f_TuneCP5_13TeV-amcatnloFXFX-pythia8",
)

# WZ production, split in final states

add_cross_section(
    xsec=5.257,
    order="NLO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="WZTo3LNu_TuneCP5_13TeV-amcatnloFXFX-pythia8",
)

add_cross_section(
    xsec=9.119,
    order="NLO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="WZTo1L1Nu2Q_4f_TuneCP5_13TeV-amcatnloFXFX-pythia8",
)

add_cross_section(
    xsec=3.414,
    order="NLO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="WZTo1L3Nu_4f_TuneCP5_13TeV-amcatnloFXFX-pythia8",
)

add_cross_section(
    xsec=6.565,
    order="NLO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="WZTo2Q2L_mllmin4p0_TuneCP5_13TeV-amcatnloFXFX-pythia8",
)
add_cross_section(
    xsec=10.25,
    order="NLO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="WZTo2Q2Nu_4f_TuneCP5_13TeV-amcatnloFXFX-madspin-pythia8",
)
# ZZ production, split in final states (POWHEG)

add_cross_section(
    xsec=0.9738,
    order="NLO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="ZZTo2L2Nu_TuneCP5_13TeV_powheg_pythia8",
)

add_cross_section(
    xsec=3.676,
    order="NLO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="ZZTo2Q2L_mllmin4p0_TuneCP5_13TeV-amcatnloFXFX-pythia8",
)

add_cross_section(
    xsec=1.325,
    order="NLO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="ZZTo4L_TuneCP5_13TeV_powheg_pythia8",
)

add_cross_section(
    xsec=3.262,
    order="NLO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="ZZTo4Q_5f_TuneCP5_13TeV-amcatnloFXFX-pythia8",
)

#
# SINGLE HIGGS PRODUCTION, gluon-gluon fusion
#


# Total ggF -> H cross section at 13 TeV (125 GeV) Report 5
_xsec_ggf_h_total = 48.09

# Single H -> bb, gluon-gluon fusion

# add_cross_section(
#     xsec=_xsec_ggf_h_total * _br_h_bb,
#     order="N3LO(QCD)+NLO(EW)",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR",
#     sample_names=[
#         "GluGluHto2B_M-125_TuneCP5_13p6TeV_powheg-minlo-pythia8",
#         "GluGluH-Hto2B_Par-M-125_TuneCP5_13p6TeV_powhegMINLO-pythia8",
#     ],
# )

# Single H -> WW, gluon-gluon fusion

# add_cross_section(
#     xsec=_xsec_ggf_h_total * _br_h_ww * _br_w_leptons**2,
#     order="N3LO(QCD)+NLO(EW)",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
#     sample_names="GluGluHto2Wto2L2Nu_M-125_TuneCP5_13p6TeV_powheg-jhugen752-pythia8",
# )

# add_cross_section(
#     xsec=_xsec_ggf_h_total * _br_h_ww * 2 * _br_w_leptons * _br_w_leptons,
#     order="N3LO(QCD)+NLO(EW)",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
#     sample_names="GluGluHto2WtoLNu2Q_M-125_TuneCP5_13p6TeV_powheg-JHUGenV752-pythia8",
# )

# Single H -> tau tau, gluon-gluon fusion

add_cross_section(
    xsec=_xsec_ggf_h_total * _br_h_tautau,
    order="N3LO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names=[
        "GluGluHToTauTau_M125_TuneCP5_13TeV-powheg-pythia8",
    ],
)

# Single H -> tau tau, gluon-gluon fusion, tau filter

# add_cross_section(
#     xsec=_xsec_ggf_h_total * _br_h_tautau * 12.66 / 32.69,  # last factor accounts for acceptance, xsec(with filter) / xsec(without filter)
#     order="N3LO(QCD)+NLO(EW)",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955; https://xsecdb-xsdb-official.app.cern.ch",
#     sample_names=[
#         "GluGluH-Hto2TauUncorrelatedDecay_Fil-TauFilter_Par-M-125_TuneCP5_13p6TeV_powheg-pythia8",
#     ],
# )

# Single H -> ZZ, gluon-gluon fusion

# add_cross_section(
#     xsec=_xsec_ggf_h_total * _br_h_zz * 2 * _br_z_leptons * _br_z_hadrons,
#     order="N3LO(QCD)+NLO(EW)",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
#     sample_names="GluGluHto2Zto2L2Q_M-125_TuneCP5_13p6TeV_powheg-jhugenv7520-pythia8",
# )

# add_cross_section(
#     xsec=_xsec_ggf_h_total * _br_h_zz * _br_z_leptons**2,
#     order="N3LO(QCD)+NLO(EW)",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
#     sample_names=[
#         "GluGluHto2Zto4L_M-125_TuneCP5_13p6TeV_powheg-jhugenv7520-pythia8",
#         "GluGluHtoZZto4L_M-125_TuneCP5_13p6TeV_powheg2-JHUGenV752-pythia8",
#     ]
# )


#
# SINGLE HIGGS PRODUCTION, VECTOR BOSON FUSION
#


# Total ggF H cross section at 13 TeV (125 GeV) Report 5
_xsec_vbf_h_total = 3.813

# Single H -> bb, vector boson fusion

add_cross_section(
    xsec=_xsec_vbf_h_total * _br_h_bb,
    order="approx. NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names=[
        "VBFHToBB_M-125_dipoleRecoilOn_TuneCP5_13TeV-powheg-pythia8",
    ],
)

# Single H -> WW, vector boson fusion

# add_cross_section(
#     xsec=_xsec_vbf_h_total * _br_h_ww * _br_w_leptons**2,
#     order="approx. NNLO(QCD)+NLO(EW)",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
#     sample_names="VBFHto2Wto2L2Nu_M-125_TuneCP5_13p6TeV_powheg-jhugen752-pythia8",
# )

# add_cross_section(
#     xsec=_xsec_vbf_h_total * _br_h_ww * 2 * _br_w_leptons * _br_w_leptons,
#     order="approx. NNLO(QCD)+NLO(EW)",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
#     sample_names="VBFHto2WtoLNu2Q_M-125_TuneCP5_13p6TeV_powheg-JHUGenV752-pythia8",
# )

# Single H -> tau tau, vector boson fusion

add_cross_section(
    xsec=_xsec_vbf_h_total * _br_h_tautau,
    order="approx. NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names=[
        "VBFHToTauTau_M125_TuneCP5_13TeV-powheg-pythia8",
    ],
)

# Single H -> tau tau, vector boson fusion, tau filter

# add_cross_section(
#     xsec=_xsec_vbf_h_total * _br_h_tautau * 1.704 / 4.18,  # last factor accounts for acceptance, xsec(with filter) / xsec(without filter)
#     order="approx. NNLO(QCD)+NLO(EW)",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955; https://xsecdb-xsdb-official.app.cern.ch",
#     sample_names=[
#         "VBFH-Hto2TauUncorrelatedDecay_Fil-TauFilter_Par-M-125_TuneCP5_13p6TeV_powheg-pythia8",
#     ],
# )

# Single H -> ZZ, vector boson fusion

# TODO add VBFHto2Zto2L2Q_M-125_TuneCP5_13p6TeV_powheg-jhugenv7520-pythia8

# add_cross_section(
#     xsec=_xsec_vbf_h_total * _br_h_zz * _br_z_leptons**2,
#     order="approx. NNLO(QCD)+NLO(EW)",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
#     sample_names="VBFHto2Zto4L_M125_TuneCP5_13p6TeV_powheg-jhugenv752-pythia8",
# )


#
# SINGLE HIGGS PRODUCTION, VH PRODUCTION
#


# Total WH and UH cross sections at 13 TeV (125 GeV) Report 5, splitted by W charge https://gitlab.cern.ch/LHCHIGGSXS/LHCHXSWG1/crosssections
_xsec_wplush_total = 0.85
_xsec_wminush_total = 0.533
_xsec_zh_total = 0.888

# WH cross section for W -> leptons
# https://indico.cern.ch/event/1119741/contributions/4715908/attachments/2383849/4073592/YR4_13p6_VH_update.pdf
#_xsec_wminus_wtolnu_total = 6.380e-2
#_xsec_wplush_wtolnu_total = 9.896e-2

# ZH cross section for Z -> leptons/neutrinos
# https://indico.cern.ch/event/1119741/contributions/4715908/attachments/2383849/4073592/YR4_13p6_VH_update.pdf
#_xsec_zh_ztoll_total = 3.174e-2
#_xsec_zh_ztonunu_total = 1.891e-1

# Single H -> bb, VH production

add_cross_section(
    xsec=_xsec_wminush_total * _br_w_hadrons * _br_h_bb,
    order="NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names="WminusH_HToBB_WToQQ_M-125_TuneCP5_13TeV-powheg-pythia8",
)

add_cross_section(
    xsec=_xsec_wminush_total * _br_w_leptons * _br_h_bb,
    order="NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names="WminusH_HToBB_WToLNu_M-125_TuneCP5_13TeV-powheg-pythia8",
)

add_cross_section(
    xsec=_xsec_wplush_total * _br_w_hadrons * _br_h_bb,
    order="NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names="WplusH_HToBB_WToQQ_M-125_TuneCP5_13TeV-powheg-pythia8",
)

add_cross_section(
    xsec=_xsec_wplush_total * _br_w_leptons * _br_h_bb,
    order="NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names="WplusH_HToBB_WToLNu_M-125_TuneCP5_13TeV-powheg-pythia8",
)

add_cross_section(
    xsec=_xsec_zh_total * _br_z_leptons * _br_h_bb,
    order="NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names="ZH_HToBB_ZToLL_M-125_TuneCP5_13TeV-powheg-pythia8",
)

add_cross_section(
    xsec=_xsec_zh_total * _br_z_inv * _br_h_bb,
    order="NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names="ZH_HToBB_ZToNuNu_M-125_TuneCP5_13TeV-powheg-pythia8",
)

add_cross_section(
    xsec=_xsec_zh_total * _br_z_hadrons * _br_h_bb,
    order="NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names="ZH_HToBB_ZToQQ_M-125_TuneCP5_13TeV-powheg-pythia8",
)

add_cross_section(
    xsec=_xsec_zh_total * _br_z_bb * _br_h_bb,
    order="NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names="ZH_HToBB_ZToBB_M-125_TuneCP5_13TeV-powheg-pythia8",
)

# Single H -> tau tau, VH production

# add_cross_section(
#     xsec=_xsec_wminush_total * _br_h_tautau,
#     order="NNLO(QCD)+NLO(EW)",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
#     sample_names=[
#         "WminusH-Hto2TauUncorrelatedDecay_Par-M-125_TuneCP5_13p6TeV_powhegMINNLO-pythia8",
#     ],
# )

# add_cross_section(
#     xsec=_xsec_wplush_total * _br_h_tautau,
#     order="NNLO(QCD)+NLO(EW)",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
#     sample_names=[
#         "WplusH-Hto2TauUncorrelatedDecay_Par-M-125_TuneCP5_13p6TeV_powhegMINNLO-pythia8",
#     ],
# )

# add_cross_section(
#     xsec=_xsec_zh_total * _br_h_tautau,
#     order="NNLO(QCD)+NLO(EW)",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
#     sample_names=[
#         "ZH-Hto2TauUncorrelatedDecay_Par-M-125_TuneCP5_13p6TeV_powhegMINNLO-pythia8",
#     ],
# )

# Single H -> tau tau, VH production, tau filter

# add_cross_section(
#     xsec=_xsec_wminush_total * _br_h_tautau * 0.2285 / 0.5788,  # last factor accounts for acceptance, xsec(with filter) / xsec(without filter)
#     order="NNLO(QCD)+NLO(EW)",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955; https://xsecdb-xsdb-official.app.cern.ch",
#     sample_names=[
#         "WminusH-Hto2TauUncorrelatedDecay_Fil-TauFilter_Par-M-125_TuneCP5_13p6TeV_powhegMINNLO-pythia8",
#     ],
# )

# add_cross_section(
#     xsec=_xsec_wplush_total * _br_h_tautau * 0.3497 / 0.9273,  # last factor accounts for acceptance, xsec(with filter) / xsec(without filter)
#     order="NNLO(QCD)+NLO(EW)",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955; https://xsecdb-xsdb-official.app.cern.ch",
#     sample_names=[
#         "WplusH-Hto2TauUncorrelatedDecay_Fil-TauFilter_Par-M-125_TuneCP5_13p6TeV_powhegMINNLO-pythia8",
#     ],
# )

# add_cross_section(
#     xsec=_xsec_zh_total * _br_h_tautau * 0.3644 / 0.8455,  # last factor accounts for acceptance, xsec(with filter) / xsec(without filter)
#     order="NNLO(QCD)+NLO(EW)",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955; https://xsecdb-xsdb-official.app.cern.ch",
#     sample_names=[
#         "ZH-Hto2TauUncorrelatedDecay_Fil-TauFilter_Par-M-125_TuneCP5_13p6TeV_powhegMINNLO-pythia8",
#     ],
# )

# Single H -> ZZ, vector boson fusion

# add_cross_section(
#     xsec=_xsec_wminush_total * _br_h_zz * _br_z_leptons**2,
#     order="NNLO(QCD)+NLO(EW)",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
#     sample_names="WminusH_Hto2Zto4L_M-125_TuneCP5_13p6TeV_powheg2-minlo-HWJ-JHUGenV752-pythia8",
# )


# TODO add VH, H -> ZZ sample_names


#
# SINGLE HIGGS PRODUCTION, TTH PRODUCTION
#

# Total WH and UH cross sections at 13.6 TeV (125 GeV), splitted by W charge
_xsec_tth_total = 0.531 # https://gitlab.cern.ch/LHCHIGGSXS/LHCHXSWG1/crosssections

# Single H -> bb, ttH production

add_cross_section(
    xsec=_xsec_tth_total * _br_h_bb,
    order="unknown (not quoted in reference)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names=[
        "ttHTobb_M125_TuneCP5_13TeV-powheg-pythia8",
    ],
)

# Single H -> (not bb), ttH production

add_cross_section(
    xsec=_xsec_tth_total * (1 - _br_h_bb),
    order="unknown (not quoted in reference)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names=[
        "ttHToNonbb_M125_TuneCP5_13TeV-powheg-pythia8",
    ],
)

# Single H -> bb, ttH production

add_cross_section(
    xsec=_xsec_tth_total * _br_h_bb,
    order="unknown (not quoted in reference)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names=[
        "ttHTobb_M125_TuneCP5_13TeV-powheg-pythia8",
    ],
)

#
# HIGGS PAIR PRODUCTION, GLUON-GLUON FUSION
#


# Total gg -> HH cross section at 13 TeV (125 GeV)
# https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWGHH#Current_recommendations_for_HH_c
_xsec_gghh_total = 0.03077

# TODO signal samples are missing !!!

# gg -> HH -> bbbb

# add_cross_section(
#     xsec=_xsec_gghh_total * _br_h_bb**2,
#     order="NNLO(QCD) FTapprox",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWGHH#Current_recommendations_for_HH_c; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/1803.02463",
#     sample_names="GluGlutoHHto4B_kl-1p00_kt-1p00_c2-0p00_TuneCP5_13p6TeV_powheg-pythia8",
# )

# gg -> HH -> bbtautau

# add_cross_section(
#     xsec=_xsec_gghh_total * 2 * _br_h_bb * _br_h_tautau,
#     order="NNLO(QCD) FTapprox",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWGHH#Current_recommendations_for_HH_c; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/1803.02463",
#     sample_names=[
#         "GluGlutoHHto2B2Tau_kl-1p00_kt-1p00_c2-0p00_TuneCP5_13p6TeV_powheg-pythia8",
#         "GluGluHHto2B2Tau_Par-c2-0p00-kl-1p00-kt-1p00_TuneCP5_13p6TeV_powheg-pythia8",
#     ],
# )

# gg -> HH -> 4V

# add_cross_section(
#     xsec=_xsec_gghh_total * ( _br_h_zz**2 + _br_h_ww**2 + 2 * _br_h_zz * _br_h_ww ),
#     order="NNLO(QCD) FTapprox",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWGHH#Current_recommendations_for_HH_c; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/1803.02463",
#     sample_names="GluGlutoHHto4V_kl-1p00_kt-1p00_c2-0p00_TuneCP5_13p6TeV_powheg-pythia8",
# )


#
# HIGGS PAIR PRODUCTION, VECTOR BOSON FUSION
#


# Total gg -> HH cross section at 13 TeV (125 GeV)
# https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWGHH#Current_recommendations_for_HH_c
_xsec_vbfhh_total = 1.687e-3

# VBF -> HH -> bbbb

# add_cross_section(
#     xsec=_xsec_vbfhh_total * _br_h_bb**2,
#     order="NNLO(QCD) FTapprox",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWGHH#Current_recommendations_for_HH_c; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/1803.02463",
#     sample_names="VBFHHto4B_CV-1_C2V-1_C3-1_TuneCP5_13p6TeV_madgraph-pythia8",
# )

# VBF -> HH -> bbtautau

# add_cross_section(
#     xsec=_xsec_vbfhh_total * 2 * _br_h_bb * _br_h_tautau,
#     order="NNLO(QCD) FTapprox",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWGHH#Current_recommendations_for_HH_c; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/1803.02463",
#     sample_names="VBFHHto2B2Tau_CV-1_C2V-1_C3-1_TuneCP5_13p6TeV_madgraph-pythia8",
# )

# VBF -> HH -> 4V

# add_cross_section(
#     xsec=_xsec_vbfhh_total * ( _br_h_zz**2 + _br_h_ww**2 + 2 * _br_h_zz * _br_h_ww ),
#     order="NNLO(QCD) FTapprox",
#     reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWGHH#Current_recommendations_for_HH_c; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/1803.02463",
#     sample_names="VBFHHto4V_CV_1_C2V_1_C3_1_TuneCP5_13p6TeV_madgraph-pythia8",
# )


def main():
    # Parse command-line arguments
    args = parse_arguments()

    # Get the output file path, check if the parent exists, create if not
    output_file = os.path.abspath(args.output_file)
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    # get the cross section database and dump it to the output file
    xsec_db = get_cross_section_db(sort=True)
    with open(output_file, "w") as f:
        json.dump(xsec_db, f, indent=4, sort_keys=True)


if __name__ == "__main__":
    main()