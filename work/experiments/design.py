"""
NitRobe -- the shape of every experiment's data, in one place.

Two experiments. This file is the single description of what each one
measures. The blank-sheet writer, the dry-run
simulator and the analyser all import it, so a column cannot mean one thing on
the sheet somebody fills in by hand and another thing in the report.

WHAT IS WRITTEN DOWN vs WHAT IS WORKED OUT
------------------------------------------
Only things that can be read off an instrument get written down: a height in
centimetres, a number on a test strip, a count of nodules, a reading from a gas
chromatograph. Every percentage, every average and every difference between
groups is worked out afterwards by analyze.py.

That split is what makes a sheet checkable. A sheet holding "the gas fell 80%"
cannot be checked, because the number it came from is gone. A sheet holding
"0 hours: 100 ppm, 96 hours: 20 ppm" can be recomputed by anybody, forever.
"""

# The shortlist comes straight out of the gene finder, so the vials cannot drift
# from the species the model actually picked.
def _shortlist():
    import json
    from pathlib import Path
    screen = (Path(__file__).resolve().parents[1]
              / "dna_model" / "results" / "screen.json")
    rows = json.loads(screen.read_text())["rows"]
    hits = sorted((r for r in rows if r["found"]),
                  key=lambda r: -r["score"])
    # GCA_000011365 is USDA 110, which already goes in as the positive
    # control. The gene finder finding it is a check on the gene finder, not a 14th
    # candidate, so it does not get a second vial.
    return [r["organism"].replace("Bradyrhizobium ", "B. ")
            for r in hits if r["accession"] != "GCA_000011365"]


CANDIDATES = _shortlist()

# Each experiment names its groups once, here. Every sheet that mentions a
# group takes the name from this list rather than repeating it.
EXPERIMENTS = {

# ------------------------------------------- 1: find the N2O destroyer

"exp-1": dict(
    title="Which of the shortlisted species actually destroy nitrous "
          "oxide?",
    where="lab",
    groups=[
        (1, "USDA 110", "Positive control, known to carry and use the gene"),
        (2, "CPAC 15", "Negative control, known to lack the gene"),
        (3, "sterile medium", "No bacteria, so nothing should change"),
    ] + [(i, name, "From the gene finder")
         for i, name in enumerate(CANDIDATES, start=4)],
    units=("vial", "V", 45),        # 15 groups x 3 replicates
    replicates=3,
    sheets={
        "vials.csv": dict(
            what="The register. Which strain is in which vial, and where the "
                 "vial sits in the rack.",
            columns=["vial_id", "group", "strain", "replicate",
                     "rack_position", "date_sealed"],
            rows="register"),
        "headspace.csv": dict(
            what="Nitrous oxide in the space above the liquid, read on the gas "
                 "chromatograph.",
            columns=["vial_id", "hour", "date_time", "n2o_ppm", "od600",
                     "operator", "notes"],
            rows=("hour", 0, 6, 24, 48, 96)),
    }),

# -------------------------------------------------- 2: build NitRobe

"exp-2": dict(
    title="Does the built strain destroy N₂O, and does it still win the "
          "race into the roots?",
    where="lab",
    # Named the way the run sheet and the diagram name them. "Unmodified
    # winner" and "the parent" said nothing about which strain was meant.
    groups=[
        (1, "E109, the host", "The recipient strain, untouched. It wins the "
            "race into the roots and carries no nos genes"),
        (2, "NitRobe", "E109 given all 7 nos genes. The build"),
        (3, "E109 + nosZ alone", "Tests whether the other 6 genes were "
            "really needed"),
        (4, "USDA 110, the donor", "The strain the genes were copied from, "
            "which already destroys N₂O"),
    ],
    units=("unit", "U", 52),        # 12 vials, then 40 pots
    replicates=3,
    sheets={
        "builds.csv": dict(
            what="What was actually made, and how it was checked before "
                 "anything was grown.",
            columns=["strain_id", "parent_strain", "genes_added", "method",
                     "sequence_confirmed", "date_built", "notes"],
            rows="none"),
        "headspace.csv": dict(
            what="The vial stage. Nitrous oxide above the liquid, same method "
                 "as experiment 1.",
            columns=["vial_id", "strain_id", "hour", "date_time", "n2o_ppm",
                     "od600", "notes"],
            rows="none"),
        "nodules.csv": dict(
            what="The pot stage. One row per nodule opened.",
            columns=["pot_id", "nodule_id", "date", "strain_identified",
                     "method", "notes"],
            rows="none"),
    }),

}


def groups_of(key):
    return EXPERIMENTS[key]["groups"]
