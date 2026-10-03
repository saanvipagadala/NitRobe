"""
NitRobe -- fill the bench sheets with invented numbers, so the analysis can be
checked before there is anything real to check it on.

  python3 simulate.py --list
  python3 simulate.py exp-1
  python3 simulate.py --all

WHY THIS EXISTS, AND WHAT IT IS NOT
-----------------------------------
Experiment 1 takes 3 weeks and experiment 2 takes 3 months. The
code that reads the sheets and decides what they show should not wait that
long to be written, and it should certainly not be debugged for the first time
on the only copy of the real numbers.

So this writes plausible numbers into the same sheets a person would fill in by
hand, in several shapes, **including shapes where the experiment fails**. Then
the analysis is run against each one and checked for whether it says something
true. A rule that calls a failure a success is a mistake in the rule rather
than in the numbers, and no amount of staring at real data would ever find it.
Only a case where the right answer is already known can.

**Nothing this writes is evidence of anything.** Every folder it fills carries
a SIMULATED.md saying so, and every verdict built from one is labelled a dry
run. The real sheets live in data/<experiment>/ and these live in
data/<experiment>/simulated/<scenario>/.
"""
import csv
import random
import shutil
import sys
from pathlib import Path

from design import EXPERIMENTS

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

# What each dry run pretends happened, and what the analysis ought to say back.
SCENARIOS = {
    "exp-1": {
        "several-work": "Several shortlisted species clear the N₂O as fast as "
            "USDA 110. The project may need to build nothing at all.",
        "gene-present-not-working": "The gene is there and the N₂O stays. The "
            "gene finder found DNA rather than ability, and the analysis must "
            "say so.",
        "method-broken": "Even the positive control does nothing, so the vials "
            "are wrong and no strain can be judged.",
    },
    "exp-2": {
        "build-works": "The built strain destroys N₂O and still wins the race.",
        "nosz-alone-is-enough": "The strain given only the main gene works as "
            "well as the strain given the whole set, which would simplify "
            "the build.",
        "build-lost-the-race": "The built strain destroys N₂O and no longer "
            "wins. The invention fails on its own central claim.",
    },
    }


def rng(key, scenario):
    """The same scenario always makes the same numbers, so a dry run is
    reproducible and a change in the verdict means a change in the rules."""
    return random.Random(f"{key}/{scenario}")


def read(path):
    with open(path) as fh:
        head = []
        for ln in fh:
            if ln.lstrip().startswith("#"):
                head.append(ln)
            else:
                break
        fh.seek(0)
        rows = list(csv.DictReader(
            ln for ln in fh if not ln.lstrip().startswith("#")))
    return head, rows


def write(path, head, rows, columns):
    with open(path, "w", newline="") as fh:
        for ln in head:
            fh.write(ln.replace("blank, to be filled in by hand at the bench",
                                "SIMULATED, invented by simulate.py"))
        w = csv.DictWriter(fh, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)


def fill(key, scenario, out):
    """Copy the blanks, then put invented numbers in them."""
    spec = EXPERIMENTS[key]
    out.mkdir(parents=True, exist_ok=True)
    sheets = {}
    for name in spec["sheets"]:
        src = DATA / key / name
        head, rows = read(src)
        sheets[name] = (head, rows)
    FILLERS[key](rng(key, scenario), scenario, sheets, spec)
    for name, (head, rows) in sheets.items():
        write(out / name, head, rows, spec["sheets"][name]["columns"])
    (out / "SIMULATED.md").write_text(
        f"# SIMULATED DATA, not a result\n\n"
        f"## {scenario}\n\n{SCENARIOS[key][scenario]}\n\n"
        f"Every number in this folder was invented by simulate.py to check "
        f"whether the analysis reports it correctly. **Nothing here is "
        f"evidence of anything.**\n")


# --------------------------------------------------------------- the fillers
#
# One per experiment. Each one is short on purpose: it invents the smallest set
# of numbers that lets the analysis reach a verdict, and nothing else.

def group_of(row, spec):
    return int(row.get("group") or 0)


def exp_1(r, sc, sheets, spec):
    # Group 1 is the positive control, 2 the negative, 3 sterile, 4 to 17 the
    # shortlist. In the hoped-for run about a third of the shortlist works.
    def left(g):
        if sc == "method-broken":
            return 0.95
        if g == 1:
            return 0.05
        if g in (2, 3):
            return 0.98
        if sc == "several-work":
            return 0.08 if g in (4, 6, 9, 12, 15) else 0.9
        return 0.9                       # gene-present-not-working
    by_vial = {row["vial_id"]: int(row["group"])
               for row in sheets["vials.csv"][1]}
    for row in sheets["headspace.csv"][1]:
        g = by_vial[row["vial_id"]]
        h = int(row["hour"])
        frac = 1 - (1 - left(g)) * min(h / 96, 1)
        row["n2o_ppm"] = round(100 * frac * r.uniform(0.96, 1.04), 1)
        row["od600"] = round(0.1 + 0.5 * h / 96, 2)


def exp_2(r, sc, sheets, spec):
    gas = {"build-works": {1: 0.95, 2: 0.10, 3: 0.55, 4: 0.08},
           "nosz-alone-is-enough": {1: 0.95, 2: 0.10, 3: 0.12, 4: 0.08},
           "build-lost-the-race": {1: 0.95, 2: 0.10, 3: 0.55, 4: 0.08}}[sc]
    share = {"build-works": {1: 0.60, 2: 0.58, 3: 0.57, 4: 0.30},
             "nosz-alone-is-enough": {1: 0.60, 2: 0.58, 3: 0.59, 4: 0.30},
             "build-lost-the-race": {1: 0.60, 2: 0.14, 3: 0.20, 4: 0.30}}[sc]
    builds, head, nod = [], [], []
    for num, name, why in spec["groups"]:
        sid = f"S{num}"
        builds.append({"strain_id": sid, "parent_strain": "E109",
                       "genes_added": {1: "none", 2: "nosRZDFYLX",
                                       3: "nosZ only", 4: "none"}[num],
                       "method": "CRISPR knock-in" if num in (2, 3) else "n/a",
                       "sequence_confirmed": "yes" if num in (2, 3) else "n/a",
                       "date_built": "", "notes": why})
        for rep in range(1, 4):
            vid = f"V{num}{rep}"
            for h in (0, 6, 24, 48, 96):
                frac = 1 - (1 - gas[num]) * min(h / 96, 1)
                head.append({"vial_id": vid, "strain_id": sid, "hour": h,
                             "date_time": "",
                             "n2o_ppm": round(100 * frac * r.uniform(.96, 1.04), 1),
                             "od600": round(0.1 + 0.5 * h / 96, 2), "notes": ""})
        for pot in range(1, 11):
            pid = f"P{num}{pot:02d}"
            for i in range(1, 11):
                nod.append({"pot_id": pid, "nodule_id": f"N{i:02d}", "date": "",
                            "strain_identified": sid if r.random() < share[num]
                                                 else "native soil strain",
                            "method": "colony PCR", "notes": ""})
    for name, rows in (("builds.csv", builds), ("headspace.csv", head),
                       ("nodules.csv", nod)):
        sheets[name] = (sheets[name][0], rows)


FILLERS = {"exp-1": exp_1, "exp-2": exp_2}


def main():
    args = sys.argv[1:]
    if "--list" in args or not args:
        for key, runs in SCENARIOS.items():
            print(f"\n{key}")
            for name, why in runs.items():
                print(f"  {name:26s} {why}")
        return
    keys = list(SCENARIOS) if "--all" in args else args
    for key in keys:
        base = DATA / key / "simulated"
        if base.exists():
            shutil.rmtree(base)
        for scenario in SCENARIOS[key]:
            fill(key, scenario, base / scenario)
            print(f"  {key}/{scenario}")


if __name__ == "__main__":
    main()
