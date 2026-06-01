"""
Script to generate a JSON file with cross sections at 13.6 TeV for various MC samples.
"""

import argparse
import json
import os
from typing import Any

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
        "output_file",
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
    sample_names: str | list[str],
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

# Total tt cross section at 13.6 TeV, must be multiplied with BRs of the W bosons
_xsec_tt_total = 923.6

add_cross_section(
    xsec=_xsec_tt_total * _br_w_leptons**2,
    order="NNLO(QCD)+NNLL",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/TtbarNNLO; https://arxiv.org/abs/1112.5675",
    sample_names="TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8",
)

add_cross_section(
    xsec=_xsec_tt_total * 2 * _br_w_leptons * _br_w_hadrons,
    order="NNLO(QCD)+NNLL",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/TtbarNNLO; https://arxiv.org/abs/1112.5675",
    sample_names=[
        "TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8",
        "TTtoLNu2Q_TuneCP5CR1_13p6TeV_powheg-pythia8",
    ],
)

add_cross_section(
    xsec=_xsec_tt_total * _br_w_hadrons**2,
    order="NNLO(QCD)+NNLL",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/TtbarNNLO; https://arxiv.org/abs/1112.5675",
    sample_names="TTto4Q_TuneCP5_13p6TeV_powheg-pythia8",
)

# Single top quark production, t-channel processes

# Total single top (t channel) cross section for t and anti-t
# https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef
_xsec_tbq_t_total = 145.0
_xsec_tbq_antit_total = 87.2

add_cross_section(
    xsec=_xsec_tbq_t_total,
    order="NNLO(QCD)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef; https://arxiv.org/abs/2012.01574",
    sample_names="TBbarQ_t-channel_4FS_TuneCP5_13p6TeV_powheg-madspin-pythia8",
)

add_cross_section(
    xsec=_xsec_tbq_t_total * _br_w_leptons,
    order="NNLO(QCD)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef; https://arxiv.org/abs/2012.01574",
    sample_names="TBbarQtoLNu-t-channel-4FS_TuneCP5_13p6TeV_powheg-madspin-pythia8",
)

add_cross_section(
    xsec=_xsec_tbq_antit_total,
    order="NNLO(QCD)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef; https://arxiv.org/abs/2012.01574",
    sample_names="TbarBQ_t-channel_4FS_TuneCP5_13p6TeV_powheg-madspin-pythia8",
)

add_cross_section(
    xsec=_xsec_tbq_antit_total * _br_w_leptons,
    order="NNLO(QCD)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef; https://arxiv.org/abs/2012.01574",
    sample_names="TbarBQtoLNu-t-channel-4FS_TuneCP5_13p6TeV_powheg-madspin-pythia8",
)

# Single top quark production, s-channel processes

add_cross_section(
    xsec=7.244 * _br_w_leptons,
    order="NNLO(QCD)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef; no publication referenced",
    sample_names=[
        "TBbartoLplusNuBbar-s-channel-4FS_TuneCP5_13p6TeV_amcatnlo-pythia8",
        "TBbartoLNu-s-channel_TuneCP5_13p6TeV_powheg-pythia8",
    ],
)

add_cross_section(
    xsec=4.534 * _br_w_leptons,
    order="NNLO(QCD)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef; no publication referenced",
    sample_names=[
        "TbarBtoLminusNuB-s-channel-4FS_TuneCP5_13p6TeV_amcatnlo-pythia8",
        "TbarBtoLNu-s-channel_TuneCP5_13p6TeV_powheg-pythia8",
    ],
)


add_cross_section(
    xsec=7.244 * _br_w_hadrons,
    order="NNLO(QCD)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef; no publication referenced",
    sample_names=[
        "TBbarto2Q-s-channel_TuneCP5_13p6TeV_powheg-pythia8",
    ],
)

add_cross_section(
    xsec=4.534 * _br_w_hadrons,
    order="NNLO(QCD)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef; no publication referenced",
    sample_names=[
        "TbarBto2Q-s-channel_TuneCP5_13p6TeV_powheg-pythia8",
    ],
)


# Single top quark production, tW processes

# Total tW cross section (for t Wplus and tbar Wminus)
# The tW cross section is only provided for tW + tbarW, so it has to be divided by 2 in the *Wplus*
# and *Wminus* sample_names. Further, the cross section has to be multiplied with the correct BRs of the
# W bosons
_xsec_tw_total = 87.9

add_cross_section(
    xsec=_xsec_tw_total / 2 * _br_w_leptons**2,
    order="NLO(QCD)+NNLL",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef; https://arxiv.org/abs/2102.11300",
    sample_names="TWminusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8",
)

add_cross_section(
    xsec=_xsec_tw_total / 2 * _br_w_leptons**2,
    order="NLO(QCD)+NNLL",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef; https://arxiv.org/abs/2102.11300",
    sample_names="TbarWplusto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8",
)

add_cross_section(
    xsec=_xsec_tw_total / 2 * 2 * _br_w_leptons * _br_w_hadrons,
    order="NLO(QCD)+NNLL",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef; https://arxiv.org/abs/2102.11300",
    sample_names="TWminustoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8"
)

add_cross_section(
    xsec=_xsec_tw_total / 2 * 2 * _br_w_leptons * _br_w_hadrons,
    order="NLO(QCD)+NNLL",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef; https://arxiv.org/abs/2102.11300",
    sample_names="TbarWplustoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8",
)

add_cross_section(
    xsec=_xsec_tw_total / 2 * _br_w_hadrons**2,
    order="NLO(QCD)+NNLL",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef; https://arxiv.org/abs/2102.11300",
    sample_names="TWminusto4Q_TuneCP5_13p6TeV_powheg-pythia8",
)

add_cross_section(
    xsec=_xsec_tw_total / 2 * _br_w_hadrons**2,
    order="NLO(QCD)+NNLL",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/SingleTopNNLORef; https://arxiv.org/abs/2102.11300",
    sample_names="TbarWplusto4Q_TuneCP5_13p6TeV_powheg-pythia8",
)


# Some tt+X processes with cross sections extracted from the sample_names (taken from the CMS cross section database)

_reference = "https://xsecdb-xsdb-official.app.cern.ch"
for _sample_name, _xsec, _order in [
    ("TTZZto4B_TuneCP5_13p6TeV_madgraph-pythia8", 0.001387, "LO(QCD)"),
    ("TTG-1Jets_PTG-100to200_TuneCP5_13p6TeV_amcatnloFXFXold-pythia8", 0.4114, "NLO(QCD)"),
    ("TTG-1Jets_PTG-10to100_TuneCP5_13p6TeV_amcatnloFXFXold-pythia8", 4.216, "NLO(QCD)"),
    ("TTG-1Jets_PTG-200_TuneCP5_13p6TeV_amcatnloFXFXold-pythia8", 0.1284, "NLO(QCD)"),
    ("TTLL_MLL-4to50_TuneCP5_13p6TeV_amcatnlo-pythia8", 0.03949, "NLO(QCD)"),
    ("TTLL_MLL-50_TuneCP5_13p6TeV_amcatnlo-pythia8", 0.08646, "NLO(QCD)"),
    ("TTLNu-1Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8", 0.2505, "NLO(QCD)"),
    ("TTLNu-EWK_TuneCP5_13p6TeV_amcatnlo-pythia8", 0.01769, "NLO(QCD)"),
    ("TTNuNu_TuneCP5_13p6TeV_amcatnlo-pythia8", 0.1638, "NLO(QCD)"),
    ("TTZ-ZtoQQ-1Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8", 0.6603, "NLO(QCD)"),
    ("TTWW_TuneCP5_13p6TeV_madgraph-madspin-pythia8", 0.008203, "LO(QCD)"),
    ("TTZZ_TuneCP5_13p6TeV_madgraph-madspin-pythia8", 0.001579, "LO(QCD)"),
    ("TTTT_TuneCP5_13p6TeV_amcatnlo-pythia8", 0.009652, "NLO(QCD)"),
]:
    add_cross_section(
        xsec=_xsec,
        order=_order,
        reference=_reference,
        sample_names=_sample_name,
    )


#
# DRELL-YAN PRODUCTION, MADGRAPH (LO)
#


# Total DY cross section at 13.6 TeV
# To also normalize the jet-binned sample_names with higher precision, we need to calculate a k factor,
# with which the NLO cross sections of the jet-binned sample_names can be scaled to the more precise NNLO
# cross section values. The cross section values correspond to DY -> l l production, so in general,
# they must not be multiplied with the BR of the Z boson into leptons.
# - MadGraph cross section: https://xsecdb-xsdb-official.app.cern.ch
# - NNLO cross section: https://twiki.cern.ch/twiki/bin/viewauth/CMS/MATRIXCrossSectionsat13p6TeV
_xsec_dy_m50_total_madgraph = 5467.0
_xsec_dy_m50_total_nnlo = 3 * 2091.7
_k_factor_dy_m50_madgraph_nnlo = _xsec_dy_m50_total_nnlo / _xsec_dy_m50_total_madgraph

# Inclusive DY -> ell ell samples (affected by MC bug for taus!)

add_cross_section(
    xsec=17380,
    order="LO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="DYto4L-2Jets_MLL-10to50_TuneCP5_13p6TeV_madgraphMLM-pythia8",
)

add_cross_section(
    xsec=_xsec_dy_m50_total_nnlo,
    order="NNLO(QCD)xNLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/viewauth/CMS/MATRIXCrossSectionsat13p6TeV; https://arxiv.org/abs/1711.06631",
    sample_names="DYto2L-4Jets_MLL-50_TuneCP5_13p6TeV_madgraphMLM-pythia8",
)

# Binned DY -> ell ell samples (affected by MC bug for taus!)

_reference="https://xsecdb-xsdb-official.app.cern.ch; https://twiki.cern.ch/twiki/bin/viewauth/CMS/MATRIXCrossSectionsat13p6TeV; https://arxiv.org/abs/1711.06631",
_order="NNLO(QCD)xNLO(EW)",
for _sample_name, _madgraph_xsec in [
    # samples binned in number of jets
    ("DYto2L-4Jets_MLL-50_1J_TuneCP5_13p6TeV_madgraphMLM-pythia8", 973.1),
    ("DYto2L-4Jets_MLL-50_2J_TuneCP5_13p6TeV_madgraphMLM-pythia8", 312.4),
    ("DYto2L-4Jets_MLL-50_3J_TuneCP5_13p6TeV_madgraphMLM-pythia8", 93.93),
    ("DYto2L-4Jets_MLL-50_4J_TuneCP5_13p6TeV_madgraphMLM-pythia8", 45.43),

    # samples binned in di-lepton pT
    ("DYto2L-4Jets_MLL-50_PTLL-40to100_TuneCP5_13p6TeV_madgraphMLM-pythia8", 403.7),
    ("DYto2L-4Jets_MLL-50_PTLL-100to200_TuneCP5_13p6TeV_madgraphMLM-pythia8", 58.46),
    ("DYto2L-4Jets_MLL-50_PTLL-200to400_TuneCP5_13p6TeV_madgraphMLM-pythia8", 6.678),
    ("DYto2L-4Jets_MLL-50_PTLL-400to600_TuneCP5_13p6TeV_madgraphMLM-pythia8", 0.3833),
    ("DYto2L-4Jets_MLL-50_PTLL-600_TuneCP5_13p6TeV_madgraphMLM-pythia8", 0.06843),

    # samples binned in (di-lepton mass, hadronic recoil)
    ("DYto2L-4Jets_MLL-4to50_HT-40to70_TuneCP5_13p6TeV_madgraphMLM-pythia8", 911.4),
    ("DYto2L-4Jets_MLL-4to50_HT-70to100_TuneCP5_13p6TeV_madgraphMLM-pythia8", 346.6),
    ("DYto2L-4Jets_MLL-4to50_HT-100to400_TuneCP5_13p6TeV_madgraphMLM-pythia8", 316.8),
    ("DYto2L-4Jets_MLL-4to50_HT-400to800_TuneCP5_13p6TeV_madgraphMLM-pythia8", 5.649),
    ("DYto2L-4Jets_MLL-4to50_HT-800to1500_TuneCP5_13p6TeV_madgraphMLM-pythia8", 0.4204),
    ("DYto2L-4Jets_MLL-4to50_HT-1500to2500_TuneCP5_13p6TeV_madgraphMLM-pythia8", 0.02079),
    ("DYto2L-4Jets_MLL-4to50_HT-2500_TuneCP5_13p6TeV_madgraphMLM-pythia8", 0.00107),
    ("DYto2L-4Jets_MLL-50to120_HT-40to70_TuneCP5_13p6TeV_madgraphMLM-pythia8", 316.7),
    ("DYto2L-4Jets_MLL-50to120_HT-70to100_TuneCP5_13p6TeV_madgraphMLM-pythia8", 140.1),
    ("DYto2L-4Jets_MLL-50to120_HT-100to400_TuneCP5_13p6TeV_madgraphMLM-pythia8", 179.6),
    ("DYto2L-4Jets_MLL-50to120_HT-400to800_TuneCP5_13p6TeV_madgraphMLM-pythia8", 6.742),
    ("DYto2L-4Jets_MLL-50to120_HT-800to1500_TuneCP5_13p6TeV_madgraphMLM-pythia8", 0.693),
    ("DYto2L-4Jets_MLL-50to120_HT-1500to2500_TuneCP5_13p6TeV_madgraphMLM-pythia8", 0.05047),
    ("DYto2L-4Jets_MLL-50to120_HT-2500_TuneCP5_13p6TeV_madgraphMLM-pythia8", 0.00346),
]:
    add_cross_section(
        xsec=_madgraph_xsec * _k_factor_dy_m50_madgraph_nnlo,
        order=_order,
        reference=_reference,
        sample_names=_sample_name,
    )


#
# DRELL-YAN PRODUCTION, MADGRAPH AMC@NLO (NLO)
#


# Total DY cross section at 13.6 TeV
# To also normalize the jet-binned sample_names with higher precision, we need to calculate a k factor,
# with which the NLO cross sections of the jet-binned sample_names can be scaled to the more precise NNLO
# cross section values. The cross section values correspond to DY -> l l production, so in general,
# they must not be multiplied with the BR of the Z boson into leptons.
# - MadGraph AMC@NLO cross section: https://xsecdb-xsdb-official.app.cern.ch
# - NNLO cross section: https://twiki.cern.ch/twiki/bin/viewauth/CMS/MATRIXCrossSectionsat13p6TeV
_xsec_dy_m50_total_amcatnlo = 6688.0
_xsec_dy_m50_total_nnlo = 3 * 2091.7
_k_factor_dy_m50_amcatnlo_nnlo = _xsec_dy_m50_total_nnlo / _xsec_dy_m50_total_amcatnlo

# Inclusive DY -> ell ell samples (affected by MC bug for taus!)

add_cross_section(
    xsec=20950,
    order="NLO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="DYto2L-2Jets_MLL-10to50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8",
)

add_cross_section(
    xsec=_xsec_dy_m50_total_nnlo,
    order="NNLO(QCD)xNLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/viewauth/CMS/MATRIXCrossSectionsat13p6TeV; https://arxiv.org/abs/1711.06631",
    sample_names="DYto2L-2Jets_MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8",
)


# Inclusive DY -> ell ell samples, split by flavor, low dilepton mass (affected by MC bug for taus!)

for _sample_name in [
    "DYto2E-2Jets_Bin-MLL-10to50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8",
    "DYto2Mu-2Jets_Bin-MLL-10to50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8",
    "DYto2Tau-2Jets_Bin-MLL-10to50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8",
    ]:
    add_cross_section(
        xsec=20950 / 3,
        order="NLO(QCD)",
        reference="https://xsecdb-xsdb-official.app.cern.ch",
        sample_names=_sample_name,
    )

# Jet-binned Drell-Yan -> ell ell, tau tau samples (ell ell samples are affected by MC bug for taus!)

_order = "NNLO(QCD)xNLO(EW)"
_reference = "https://xsecdb-xsdb-official.app.cern.ch; https://twiki.cern.ch/twiki/bin/viewauth/CMS/MATRIXCrossSectionsat13p6TeV; https://arxiv.org/abs/1711.06631"
for _sample_name, _amcatnlo_xsec in [
    # DY -> ell ell
    ("DYto2L-2Jets_MLL-50_0J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8", 5378),
    ("DYto2L-2Jets_MLL-50_1J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8", 1017),
    ("DYto2L-2Jets_MLL-50_2J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8", 385.5),

    # DY -> e e
    ("DYto2E-2Jets_Bin-0J-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8", 5378 / 3),
    ("DYto2E-2Jets_Bin-1J-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8", 1017 / 3),
    ("DYto2E-2Jets_Bin-2J-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8", 385.5 / 3),

    # DY -> mu mu
    ("DYto2Mu-2Jets_Bin-0J-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8", 5378 / 3),
    ("DYto2Mu-2Jets_Bin-1J-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8", 1017 / 3),
    ("DYto2Mu-2Jets_Bin-2J-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8", 385.5 / 3),

    # DY -> tau tau
    (
        [
            "DYto2Tau-2Jets_MLL-50_0J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8",
            "DYto2Tau-2Jets_Bin-0J-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8",
        ],
        5378 / 3,
    ),
    (
        [
            "DYto2Tau-2Jets_MLL-50_1J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8",
            "DYto2Tau-2Jets_Bin-1J-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8",
        ],
        1017 / 3,
    ),
    (
        [
            "DYto2Tau-2Jets_MLL-50_2J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8",
            "DYto2Tau-2Jets_Bin-2J-MLL-50_TuneCP5_13p6TeV_amcatnloFXFX-pythia8",
        ],
        385.5 / 3,
    ),
]:
    add_cross_section(
        xsec=_amcatnlo_xsec * _k_factor_dy_m50_amcatnlo_nnlo,
        order=_order,
        reference=_reference,
        sample_names=_sample_name,
    )


#
# DRELL-YAN PRODUCTION, POWHEG (NLO (?))  # TODO check if this is really NLO
#


# Total DY cross section at 13.6 TeV
# To also normalize the jet-binned sample_names with higher precision, we need to calculate a k factor,
# with which the NLO cross sections of the jet-binned sample_names can be scaled to the more precise NNLO
# cross section values. The cross section values correspond to DY -> l l production, so in general,
# they must not be multiplied with the BR of the Z boson into leptons.
# - Powheg cross section: https://xsecdb-xsdb-official.app.cern.ch
# - NNLO cross section: https://twiki.cern.ch/twiki/bin/viewauth/CMS/MATRIXCrossSectionsat13p6TeV
_xsec_dy_m50_total_powheg = 3 * (2219.0 + 21.65 + 3.058 + 0.2691 + 0.01915 + 0.00111 + 0.00005949 + 0.000001558 + 3.519e-8)
_xsec_dy_m50_total_nnlo = 3 * 2091.7
_k_factor_dy_m50_powheg_nnlo = _xsec_dy_m50_total_nnlo / _xsec_dy_m50_total_powheg

# DY -> e e, mu mu, tau tau samples, binned in di-lepton mass (not affected by MC bug for taus)

_order="NLO(QCD)",
_reference="https://xsecdb-xsdb-official.app.cern.ch; https://twiki.cern.ch/twiki/bin/viewauth/CMS/MATRIXCrossSectionsat13p6TeV; https://arxiv.org/abs/1711.06631",
for _sample_name, _powheg_xsec in [
    # DY -> ee, binned in the di-lepton mass
    ("DYto2E_MLL-10to50_TuneCP5_13p6TeV_powheg-pythia8", 6744.0),
    ("DYto2E_MLL-50to120_TuneCP5_13p6TeV_powheg-pythia8", 2219),
    ("DYto2E_MLL-120to200_TuneCP5_13p6TeV_powheg-pythia8", 21.65),
    ("DYto2E_MLL-200to400_TuneCP5_13p6TeV_powheg-pythia8", 3.058),
    ("DYto2E_MLL-400to800_TuneCP5_13p6TeV_powheg-pythia8", 0.2691),
    ("DYto2E_MLL-800to1500_TuneCP5_13p6TeV_powheg-pythia8", 0.01915),
    ("DYto2E_MLL-1500to2500_TuneCP5_13p6TeV_powheg-pythia8", 0.001111),
    ("DYto2E_MLL-2500to4000_TuneCP5_13p6TeV_powheg-pythia8", 0.00005949),
    ("DYto2E_MLL-4000to6000_TuneCP5_13p6TeV_powheg-pythia8", 0.000001558),
    ("DYto2E_MLL-6000_TuneCP5_13p6TeV_powheg-pythia8", 3.519e-8),

    # DY -> mumu, binned in the di-lepton mass
    ("DYto2Mu_MLL-10to50_TuneCP5_13p6TeV_powheg-pythia8", 6744.0),
    ("DYto2Mu_MLL-50to120_TuneCP5_13p6TeV_powheg-pythia8", 2219),
    ("DYto2Mu_MLL-120to200_TuneCP5_13p6TeV_powheg-pythia8", 21.65),
    ("DYto2Mu_MLL-200to400_TuneCP5_13p6TeV_powheg-pythia8", 3.058),
    ("DYto2Mu_MLL-400to800_TuneCP5_13p6TeV_powheg-pythia8", 0.2691),
    ("DYto2Mu_MLL-800to1500_TuneCP5_13p6TeV_powheg-pythia8", 0.01915),
    ("DYto2Mu_MLL-1500to2500_TuneCP5_13p6TeV_powheg-pythia8", 0.001111),
    ("DYto2Mu_MLL-2500to4000_TuneCP5_13p6TeV_powheg-pythia8", 0.00005949),
    ("DYto2Mu_MLL-4000to6000_TuneCP5_13p6TeV_powheg-pythia8", 0.000001558),
    ("DYto2Mu_MLL-6000_TuneCP5_13p6TeV_powheg-pythia8", 3.519e-8),

    # DY -> tautau, binned in di-lepton mass
    ("DYto2Tau_MLL-10to50_TuneCP5_13p6TeV_powheg-pythia8", 6744.0),
    ("DYto2Tau_MLL-50to120_TuneCP5_13p6TeV_powheg-pythia8", 2219),
    ("DYto2Tau_MLL-120to200_TuneCP5_13p6TeV_powheg-pythia8", 21.65),
    ("DYto2Tau_MLL-200to400_TuneCP5_13p6TeV_powheg-pythia8", 3.058),
    ("DYto2Tau_MLL-400to800_TuneCP5_13p6TeV_powheg-pythia8", 0.2691),
    ("DYto2Tau_MLL-800to1500_TuneCP5_13p6TeV_powheg-pythia8", 0.01915),
    ("DYto2Tau_MLL-1500to2500_TuneCP5_13p6TeV_powheg-pythia8", 0.001111),
    ("DYto2Tau_MLL-2500to4000_TuneCP5_13p6TeV_powheg-pythia8", 0.00005949),
    ("DYto2Tau_MLL-4000to6000_TuneCP5_13p6TeV_powheg-pythia8", 0.000001558),
    ("DYto2Tau_MLL-6000_TuneCP5_13p6TeV_powheg-pythia8", 3.519e-8),
]:
    add_cross_section(
        xsec=_powheg_xsec * _k_factor_dy_m50_powheg_nnlo,
        order=_order,
        reference=_reference,
        sample_names=_sample_name,
    )


#
# W PRODUCTION, MADGRAPH (LO)
#


# Total W cross section at 13.6 TeV
# To also normalize the jet-binned sample_names with higher precision, we need to calculate a k factor,
# with which the NLO cross sections of the jet-binned sample_names can be scaled to the more precise NNLO
# cross section values. The cross section values correspond to W -> l nu production, so in general,
# they must not be multiplied with the BR of the W boson into leptons.
# - MadGraph cross section: https://xsecdb-xsdb-official.app.cern.ch
# - NNLO cross section: https://twiki.cern.ch/twiki/bin/viewauth/CMS/MATRIXCrossSectionsat13p6TeV
_xsec_w_total_madgraph = 67710.0
_xsec_w_total_nnlo = 3 * (9009.5 + 12122.5)
_k_factor_w_madgraph_nnlo = _xsec_w_total_nnlo / _xsec_w_total_madgraph

# Inclusive W -> ell nu samples

add_cross_section(
    xsec=_xsec_w_total_nnlo,
    order="NNLO(QCD)xNLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/viewauth/CMS/MATRIXCrossSectionsat13p6TeV; https://arxiv.org/abs/1711.06631",
    sample_names="WtoLNu-4Jets_TuneCP5_13p6TeV_madgraphMLM-pythia8",
)

# Exclusive W -> l nu samples

_order = "NNLO(QCD)xNLO(EW)"
_reference = "https://xsecdb-xsdb-official.app.cern.ch; https://twiki.cern.ch/twiki/bin/viewauth/CMS/MATRIXCrossSectionsat13p6TeV; https://arxiv.org/abs/1711.06631"
for _sample_name, _xsec in [
    # W -> ell nu, binned in number of jets
    ("WtoLNu-4Jets_1J_TuneCP5_13p6TeV_madgraphMLM-pythia8", 9084),
    ("WtoLNu-4Jets_2J_TuneCP5_13p6TeV_madgraphMLM-pythia8", 2925),
    ("WtoLNu-4Jets_3J_TuneCP5_13p6TeV_madgraphMLM-pythia8", 861.7),
    ("WtoLNu-4Jets_4J_TuneCP5_13p6TeV_madgraphMLM-pythia8", 416.5),

    # W -> ell nu, binned in (lepton-neutrino system mass, hadronic recoil)
    ("WtoLNu-4Jets_MLNu-0to120_HT-40to100_TuneCP5_13p6TeV_madgraphMLM-pythia8", 4254),
    ("WtoLNu-4Jets_MLNu-0to120_HT-100to400_TuneCP5_13p6TeV_madgraphMLM-pythia8", 1626),
    ("WtoLNu-4Jets_MLNu-0to120_HT-400to800_TuneCP5_13p6TeV_madgraphMLM-pythia8", 59.99),
    ("WtoLNu-4Jets_MLNu-0to120_HT-800to1500_TuneCP5_13p6TeV_madgraphMLM-pythia8", 6.23),
    ("WtoLNu-4Jets_MLNu-0to120_HT-1500to2500_TuneCP5_13p6TeV_madgraphMLM-pythia8", 0.4477),
    ("WtoLNu-4Jets_MLNu-0to120_HT-2500_TuneCP5_13p6TeV_madgraphMLM-pythia8", 0.03075),
    ("WtoLNu-4Jets_MLNu-120_HT-40to100_TuneCP5_13p6TeV_madgraphMLM-pythia8", 20.56),
    ("WtoLNu-4Jets_MLNu-120_HT-100to400_TuneCP5_13p6TeV_madgraphMLM-pythia8", 10.19),
    ("WtoLNu-4Jets_MLNu-120_HT-400to800_TuneCP5_13p6TeV_madgraphMLM-pythia8", 0.5239),
    ("WtoLNu-4Jets_MLNu-120_HT-800to1500_TuneCP5_13p6TeV_madgraphMLM-pythia8", 0.06255),
    ("WtoLNu-4Jets_MLNu-120_HT-1500to2500_TuneCP5_13p6TeV_madgraphMLM-pythia8", 0.005066),
    ("WtoLNu-4Jets_MLNu-120_HT-2500_TuneCP5_13p6TeV_madgraphMLM-pythia8", 0.0003788),
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


# Total W cross section at 13.6 TeV
# To also normalize the jet-binned sample_names with higher precision, we need to calculate a k factor,
# with which the NLO cross sections of the jet-binned sample_names can be scaled to the more precise NNLO
# cross section values. The cross section values correspond to W -> l nu production, so in general,
# they must not be multiplied with the BR of the W boson into leptons.
# - MadGraph AMC@NLO cross section: https://xsecdb-xsdb-official.app.cern.ch
# - NNLO cross section: https://twiki.cern.ch/twiki/bin/viewauth/CMS/MATRIXCrossSectionsat13p6TeV
_xsec_w_total_amcatnlo = 67710.0
_xsec_w_total_nnlo = 3 * (9009.5 + 12122.5)
_k_factor_w_nlo_nnlo = _xsec_w_total_nnlo / _xsec_w_total_amcatnlo

# Inclusive W -> ell nu samples

add_cross_section(
    xsec=_xsec_w_total_nnlo,
    order="NNLO(QCD)xNLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/viewauth/CMS/MATRIXCrossSectionsat13p6TeV; https://arxiv.org/abs/1711.06631",
    sample_names="WtoLNu-2Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8",
)

# Exclusive W -> l nu samples, binned in number of jets

_order="NNLO(QCD)xNLO(EW)"
_reference="https://xsecdb-xsdb-official.app.cern.ch; https://twiki.cern.ch/twiki/bin/viewauth/CMS/MATRIXCrossSectionsat13p6TeV; https://arxiv.org/abs/1711.06631"
for _sample_name, _xsec in [
    ("WtoLNu-2Jets_0J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8", 55760),
    ("WtoLNu-2Jets_1J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8", 9529),
    ("WtoLNu-2Jets_2J_TuneCP5_13p6TeV_amcatnloFXFX-pythia8", 3532),
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


# TODO The cross sections on https://twiki.cern.ch/twiki/bin/viewauth/CMS/MATRIXCrossSectionsat13p6TeV seem way too high. That's why we currently just use the cross sections from the sample database.

## Cross sections of WW, ZZ production at 13.6 TeV for leptonic final states
## N.B.: To obtain the "_xsec_zz_or_ww_x" values, we subtract the gg -> VV from the pp -> VV production cross section.
## Taken from https://twiki.cern.ch/twiki/bin/viewauth/CMS/MATRIXCrossSectionsat13p6TeV
## Order: nNNLO(QCD)xNLO(EW) (subtracted gg -> X at NLO)

_xsec_zz_or_ww_eemumu = 0.387 - 0.0443
_xsec_zz_or_ww_eeee = 0.1633 - 0.013
_xsec_zz_or_ww_emunuenumu = 1.5589 - 0.1497
_xsec_zz_or_ww_eenuenue = 1.6736 - 0.1602

# Cross sections of WZ production at 13.6 TeV for leptonic final states
# Taken from https://twiki.cern.ch/twiki/bin/viewauth/CMS/MATRIXCrossSectionsat13p6TeV
# Order: NNLO(QCD)xNLO(EW), gg -> X at NLO
_xsec_wz_eemuminusnumu = 0.2385
_xsec_wz_eeeminusnue = 0.2366
_xsec_wz_eemuplusnumu = 0.3474
_xsec_wz_eeeplusnue = 0.3459

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
    xsec=80.42,
    order="LO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="WW_TuneCP5_13p6TeV_pythia8",
)

add_cross_section(
    xsec=29.10,
    order="LO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="WZ_TuneCP5_13p6TeV_pythia8",
)

add_cross_section(
    xsec=12.75,
    order="LO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="ZZ_TuneCP5_13p6TeV_pythia8",
)


# WW production, split in final states (POWHEG)

add_cross_section(
    xsec=11.79,
    order="NLO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="WWto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8",
)

add_cross_section(
    xsec=48.94,
    order="NLO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="WWtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8",
)

add_cross_section(
    xsec=50.79,
    order="NLO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="WWto4Q_TuneCP5_13p6TeV_powheg-pythia8",
)

# WZ production, split in final states (POWHEG)

add_cross_section(
    xsec=4.924,
    order="NLO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="WZto3LNu_TuneCP5_13p6TeV_powheg-pythia8",
)

add_cross_section(
    xsec=15.87,
    order="NLO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="WZtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8",
)

add_cross_section(
    xsec=7.568,
    order="NLO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="WZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8",
)

# ZZ production, split in final states (POWHEG)

add_cross_section(
    xsec=1.031,
    order="NLO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="ZZto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8",
)

add_cross_section(
    xsec=6.788,
    order="NLO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="ZZto2L2Q_TuneCP5_13p6TeV_powheg-pythia8",
)

add_cross_section(
    xsec=1.39,
    order="NLO(QCD)",
    reference="https://xsecdb-xsdb-official.app.cern.ch",
    sample_names="ZZto4L_TuneCP5_13p6TeV_powheg-pythia8",
)


#
# SINGLE HIGGS PRODUCTION, gluon-gluon fusion
#


# Total ggF -> H cross section at 13.6 TeV (125 GeV)
_xsec_ggf_h_total = 52.23

# Single H -> bb, gluon-gluon fusion

add_cross_section(
    xsec=_xsec_ggf_h_total * _br_h_bb,
    order="N3LO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names=[
        "GluGluHto2B_M-125_TuneCP5_13p6TeV_powheg-minlo-pythia8",
        "GluGluH-Hto2B_Par-M-125_TuneCP5_13p6TeV_powhegMINLO-pythia8",
    ],
)

# Single H -> WW, gluon-gluon fusion

add_cross_section(
    xsec=_xsec_ggf_h_total * _br_h_ww * _br_w_leptons**2,
    order="N3LO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names="GluGluHto2Wto2L2Nu_M-125_TuneCP5_13p6TeV_powheg-jhugen752-pythia8",
)

add_cross_section(
    xsec=_xsec_ggf_h_total * _br_h_ww * 2 * _br_w_leptons * _br_w_leptons,
    order="N3LO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names="GluGluHto2WtoLNu2Q_M-125_TuneCP5_13p6TeV_powheg-JHUGenV752-pythia8",
)

# Single H -> tau tau, gluon-gluon fusion

add_cross_section(
    xsec=_xsec_ggf_h_total * _br_h_tautau,
    order="N3LO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names=[
        "GluGluHToTauTau_M-125_TuneCP5_13p6TeV_powheg-pythia8",
        "GluGluHTo2TauUncorrelatedDecay_M-125_CP5_13p6TeV_powheg-pythia8",
        "GluGluH-Hto2TauUncorrelatedDecay_Par-M-125_TuneCP5_13p6TeV_powheg-pythia8",
    ],
)

# Single H -> tau tau, gluon-gluon fusion, tau filter

add_cross_section(
    xsec=_xsec_ggf_h_total * _br_h_tautau * 12.66 / 32.69,  # last factor accounts for acceptance, xsec(with filter) / xsec(without filter)
    order="N3LO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955; https://xsecdb-xsdb-official.app.cern.ch",
    sample_names=[
        "GluGluH-Hto2TauUncorrelatedDecay_Fil-TauFilter_Par-M-125_TuneCP5_13p6TeV_powheg-pythia8",
    ],
)

# Single H -> ZZ, gluon-gluon fusion

add_cross_section(
    xsec=_xsec_ggf_h_total * _br_h_zz * 2 * _br_z_leptons * _br_z_hadrons,
    order="N3LO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names="GluGluHto2Zto2L2Q_M-125_TuneCP5_13p6TeV_powheg-jhugenv7520-pythia8",
)

add_cross_section(
    xsec=_xsec_ggf_h_total * _br_h_zz * _br_z_leptons**2,
    order="N3LO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names=[
        "GluGluHto2Zto4L_M-125_TuneCP5_13p6TeV_powheg-jhugenv7520-pythia8",
        "GluGluHtoZZto4L_M-125_TuneCP5_13p6TeV_powheg2-JHUGenV752-pythia8",
    ]
)


#
# SINGLE HIGGS PRODUCTION, VECTOR BOSON FUSION
#


# Total ggF H cross section at 13.6 TeV (125 GeV)
_xsec_vbf_h_total = 4.078

# Single H -> bb, vector boson fusion

add_cross_section(
    xsec=_xsec_vbf_h_total * _br_h_bb,
    order="approx. NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names=[
        "VBFHto2B_M-125_TuneCP5_13p6TeV_powheg-pythia8",
        "VBFH-Hto2B_Par-M-125_TuneCP5_13p6TeV_powheg-pythia8",
    ],
)

# Single H -> WW, vector boson fusion

add_cross_section(
    xsec=_xsec_vbf_h_total * _br_h_ww * _br_w_leptons**2,
    order="approx. NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names="VBFHto2Wto2L2Nu_M-125_TuneCP5_13p6TeV_powheg-jhugen752-pythia8",
)

add_cross_section(
    xsec=_xsec_vbf_h_total * _br_h_ww * 2 * _br_w_leptons * _br_w_leptons,
    order="approx. NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names="VBFHto2WtoLNu2Q_M-125_TuneCP5_13p6TeV_powheg-JHUGenV752-pythia8",
)

# Single H -> tau tau, vector boson fusion

add_cross_section(
    xsec=_xsec_vbf_h_total * _br_h_tautau,
    order="approx. NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names=[
        "VBFHToTauTau_M125_TuneCP5_13p6TeV_powheg-pythia8",
        "VBFHTo2TauUncorrelatedDecay_M-125_TuneCP5_13p6TeV_powheg-pythia8",
        "VBFH-Hto2TauUncorrelatedDecay_Par-M-125_TuneCP5_13p6TeV_powheg-pythia8",
    ],
)

# Single H -> tau tau, vector boson fusion, tau filter

add_cross_section(
    xsec=_xsec_vbf_h_total * _br_h_tautau * 1.704 / 4.18,  # last factor accounts for acceptance, xsec(with filter) / xsec(without filter)
    order="approx. NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955; https://xsecdb-xsdb-official.app.cern.ch",
    sample_names=[
        "VBFH-Hto2TauUncorrelatedDecay_Fil-TauFilter_Par-M-125_TuneCP5_13p6TeV_powheg-pythia8",
    ],
)

# Single H -> ZZ, vector boson fusion

# TODO add VBFHto2Zto2L2Q_M-125_TuneCP5_13p6TeV_powheg-jhugenv7520-pythia8

add_cross_section(
    xsec=_xsec_vbf_h_total * _br_h_zz * _br_z_leptons**2,
    order="approx. NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names="VBFHto2Zto4L_M125_TuneCP5_13p6TeV_powheg-jhugenv752-pythia8",
)


#
# SINGLE HIGGS PRODUCTION, VH PRODUCTION
#


# Total WH and UH cross sections at 13.6 TeV (125 GeV), splitted by W charge
_xsec_wplush_total = 0.8889
_xsec_wminush_total = 0.5677
_xsec_zh_total = 0.9439

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
    sample_names="WminusH_Hto2B_Wto2Q_M-125_TuneCP5_13p6TeV_powheg-pythia8",
)

add_cross_section(
    xsec=_xsec_wminush_total * _br_w_leptons * _br_h_bb,
    order="NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names="WminusH_Hto2B_WtoLNu_M-125_TuneCP5_13p6TeV_powheg-pythia8",
)

add_cross_section(
    xsec=_xsec_wplush_total * _br_w_hadrons * _br_h_bb,
    order="NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names="WplusH_Hto2B_Wto2Q_M-125_TuneCP5_13p6TeV_powheg-pythia8",
)

add_cross_section(
    xsec=_xsec_wplush_total * _br_w_leptons * _br_h_bb,
    order="NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names="WplusH_Hto2B_WtoLNu_M-125_TuneCP5_13p6TeV_powheg-pythia8",
)

add_cross_section(
    xsec=_xsec_zh_total * _br_z_leptons * _br_h_bb,
    order="NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names="ZH_Hto2B_Zto2L_M-125_TuneCP5_13p6TeV_powheg-pythia8",
)

add_cross_section(
    xsec=_xsec_zh_total * _br_z_hadrons * _br_h_bb,
    order="NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names="ZH_Hto2B_Zto2Q_M-125_TuneCP5_13p6TeV_powheg-pythia8",
)

# Single H -> tau tau, VH production

add_cross_section(
    xsec=_xsec_wminush_total * _br_h_tautau,
    order="NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names=[
        "WminusH-Hto2TauUncorrelatedDecay_Par-M-125_TuneCP5_13p6TeV_powhegMINNLO-pythia8",
    ],
)

add_cross_section(
    xsec=_xsec_wplush_total * _br_h_tautau,
    order="NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names=[
        "WplusH-Hto2TauUncorrelatedDecay_Par-M-125_TuneCP5_13p6TeV_powhegMINNLO-pythia8",
    ],
)

add_cross_section(
    xsec=_xsec_zh_total * _br_h_tautau,
    order="NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names=[
        "ZH-Hto2TauUncorrelatedDecay_Par-M-125_TuneCP5_13p6TeV_powhegMINNLO-pythia8",
    ],
)

# Single H -> tau tau, VH production, tau filter

add_cross_section(
    xsec=_xsec_wminush_total * _br_h_tautau * 0.2285 / 0.5788,  # last factor accounts for acceptance, xsec(with filter) / xsec(without filter)
    order="NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955; https://xsecdb-xsdb-official.app.cern.ch",
    sample_names=[
        "WminusH-Hto2TauUncorrelatedDecay_Fil-TauFilter_Par-M-125_TuneCP5_13p6TeV_powhegMINNLO-pythia8",
    ],
)

add_cross_section(
    xsec=_xsec_wplush_total * _br_h_tautau * 0.3497 / 0.9273,  # last factor accounts for acceptance, xsec(with filter) / xsec(without filter)
    order="NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955; https://xsecdb-xsdb-official.app.cern.ch",
    sample_names=[
        "WplusH-Hto2TauUncorrelatedDecay_Fil-TauFilter_Par-M-125_TuneCP5_13p6TeV_powhegMINNLO-pythia8",
    ],
)

add_cross_section(
    xsec=_xsec_zh_total * _br_h_tautau * 0.3644 / 0.8455,  # last factor accounts for acceptance, xsec(with filter) / xsec(without filter)
    order="NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955; https://xsecdb-xsdb-official.app.cern.ch",
    sample_names=[
        "ZH-Hto2TauUncorrelatedDecay_Fil-TauFilter_Par-M-125_TuneCP5_13p6TeV_powhegMINNLO-pythia8",
    ],
)

# Single H -> ZZ, vector boson fusion

add_cross_section(
    xsec=_xsec_wminush_total * _br_h_zz * _br_z_leptons**2,
    order="NNLO(QCD)+NLO(EW)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names="WminusH_Hto2Zto4L_M-125_TuneCP5_13p6TeV_powheg2-minlo-HWJ-JHUGenV752-pythia8",
)


# TODO add VH, H -> ZZ sample_names


#
# SINGLE HIGGS PRODUCTION, TTH PRODUCTION
#

# Total WH and UH cross sections at 13.6 TeV (125 GeV), splitted by W charge
_xsec_tth_total = 0.57

# Single H -> bb, ttH production

add_cross_section(
    xsec=_xsec_tth_total * _br_h_bb,
    order="unknown (not quoted in reference)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names=[
        "TTH_Hto2B_M-125_TuneCP5_13p6TeV_powheg-pythia8",
        "TTH-Hto2B_Par-M-125_TuneCP5_13p6TeV_powheg-pythia8",
    ],
)

# Single H -> (not bb), ttH production

add_cross_section(
    xsec=_xsec_tth_total * (1 - _br_h_bb),
    order="unknown (not quoted in reference)",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWG136TeVxsec_extrap; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/2402.09955",
    sample_names=[
        "TTHtoNon2B_M-125_TuneCP5_13p6TeV_powheg-pythia8",
        "TTH-HtoNon2B_Par-M-125_TuneCP5_13p6TeV_powheg-pythia8",
    ],
)


#
# HIGGS PAIR PRODUCTION, GLUON-GLUON FUSION
#


# Total gg -> HH cross section at 13.6 TeV (125 GeV)
# https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWGHH#Current_recommendations_for_HH_c
_xsec_gghh_total = 0.03413

# gg -> HH -> bbbb

add_cross_section(
    xsec=_xsec_gghh_total * _br_h_bb**2,
    order="NNLO(QCD) FTapprox",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWGHH#Current_recommendations_for_HH_c; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/1803.02463",
    sample_names="GluGlutoHHto4B_kl-1p00_kt-1p00_c2-0p00_TuneCP5_13p6TeV_powheg-pythia8",
)

# gg -> HH -> bbtautau

add_cross_section(
    xsec=_xsec_gghh_total * 2 * _br_h_bb * _br_h_tautau,
    order="NNLO(QCD) FTapprox",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWGHH#Current_recommendations_for_HH_c; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/1803.02463",
    sample_names=[
        "GluGlutoHHto2B2Tau_kl-1p00_kt-1p00_c2-0p00_TuneCP5_13p6TeV_powheg-pythia8",
        "GluGluHHto2B2Tau_Par-c2-0p00-kl-1p00-kt-1p00_TuneCP5_13p6TeV_powheg-pythia8",
    ],
)

# gg -> HH -> 4V

add_cross_section(
    xsec=_xsec_gghh_total * ( _br_h_zz**2 + _br_h_ww**2 + 2 * _br_h_zz * _br_h_ww ),
    order="NNLO(QCD) FTapprox",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWGHH#Current_recommendations_for_HH_c; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/1803.02463",
    sample_names="GluGlutoHHto4V_kl-1p00_kt-1p00_c2-0p00_TuneCP5_13p6TeV_powheg-pythia8",
)


#
# HIGGS PAIR PRODUCTION, VECTOR BOSON FUSION
#


# Total gg -> HH cross section at 13.6 TeV (125 GeV)
# https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWGHH#Current_recommendations_for_HH_c
_xsec_vbfhh_total = 1.874e-3

# VBF -> HH -> bbbb

add_cross_section(
    xsec=_xsec_vbfhh_total * _br_h_bb**2,
    order="NNLO(QCD) FTapprox",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWGHH#Current_recommendations_for_HH_c; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/1803.02463",
    sample_names="VBFHHto4B_CV-1_C2V-1_C3-1_TuneCP5_13p6TeV_madgraph-pythia8",
)

# VBF -> HH -> bbtautau

add_cross_section(
    xsec=_xsec_vbfhh_total * 2 * _br_h_bb * _br_h_tautau,
    order="NNLO(QCD) FTapprox",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWGHH#Current_recommendations_for_HH_c; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/1803.02463",
    sample_names="VBFHHto2B2Tau_CV-1_C2V-1_C3-1_TuneCP5_13p6TeV_madgraph-pythia8",
)

# VBF -> HH -> 4V

add_cross_section(
    xsec=_xsec_vbfhh_total * ( _br_h_zz**2 + _br_h_ww**2 + 2 * _br_h_zz * _br_h_ww ),
    order="NNLO(QCD) FTapprox",
    reference="https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHWGHH#Current_recommendations_for_HH_c; https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR; https://arxiv.org/abs/1803.02463",
    sample_names="VBFHHto4V_CV_1_C2V_1_C3_1_TuneCP5_13p6TeV_madgraph-pythia8",
)


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
