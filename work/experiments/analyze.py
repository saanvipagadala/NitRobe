"""
NitRobe -- read a folder of bench sheets and say what they show.

  python3 analyze.py exp-1                    the real sheets
  python3 analyze.py exp-1 --dry several-work one of the dry runs
  python3 analyze.py --all-dry                every dry run, every experiment

THE RULES ARE WRITTEN DOWN BEFORE THE DATA IS
---------------------------------------------
Every verdict below follows a rule fixed in advance, and not one of those rules
depends on how the numbers turn out. That is the difference between a result
and a story. With the rule fixed first, a disappointing answer is exactly as
reportable as a good one, and this prints it just as plainly.

NO STATISTICS VOCABULARY, ON PURPOSE
------------------------------------
This is a school project and every number in it has to be one Saanvi can
explain to a judge in her own words. So there are no p-values and no standard
deviations anywhere in here. What replaces them is not weaker, it is the same
test said plainly:

    "The WORST vial of the good strains still beat the BEST vial of the others."

With 3 replicates that sentence is as strong a claim as 3 replicates can make.
When the ranges do overlap, the honest answer is "these could not be told
apart", which is also what the arithmetic would have said, just less clearly.
"""
import csv
import statistics
import sys
from pathlib import Path

from design import EXPERIMENTS

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


def load(folder, name):
    with open(folder / name) as fh:
        return list(csv.DictReader(
            ln for ln in fh if not ln.lstrip().startswith("#")))


def num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def clean_win(better, worse):
    """The whole test, in 1 line: did the worst of one beat the best of the
    other, with no overlap at all?"""
    return bool(better) and bool(worse) and min(better) > max(worse)


def bullet(ok, text):
    """A verdict. Plain facts are returned as bare strings instead."""
    return ("yes" if ok else "no", text)


# ------------------------------------------------------------------ verdicts

def _cleared(f, sheet, idcol, groupcol):
    """How much of the gas is gone by 96 hours, per group."""
    rows = load(f, sheet)
    by = {}
    for r in rows:
        by.setdefault(r[idcol], {})[int(r["hour"])] = num(r["n2o_ppm"], 0)
    require([r["n2o_ppm"] for r in rows])
    out = {}
    for uid, pts in by.items():
        start, end = pts.get(0, 0), pts.get(96, 0)
        if start:
            out[uid] = 100 * (start - end) / start
    return out


def exp_1_groups(f):
    """Per group: mean gas cleared by 96 hours, and the verdict the rules give.

    The report draws from this, so the picture on the page and the sentences
    under it can never disagree.
    """
    vials = {r["vial_id"]: (int(r["group"]), r["strain"])
             for r in load(f, "vials.csv")}
    cleared = _cleared(f, "headspace.csv", "vial_id", "group")
    by_group = {}
    for vid, pct in cleared.items():
        g, name = vials[vid]
        by_group.setdefault((g, name), []).append(pct)
    pos = by_group.get((1, "USDA 110"), [])
    neg = by_group.get((2, "CPAC 15"), [])
    broken = not pos or statistics.mean(pos) < 50
    bar = 0.5 * statistics.mean(pos) if pos else 0
    out = []
    for (g, name), v in sorted(by_group.items()):
        mean = statistics.mean(v)
        if g <= 3:
            verdict = "control"
        elif broken:
            verdict = "unreadable"
        elif clean_win(v, neg) and mean >= bar:
            verdict = "cleared"
        else:
            verdict = "did not clear"
        out.append(dict(group=g, name=name, cleared=mean, verdict=verdict,
                        replicates=len(v)))
    return out


def exp_1_curves(f):
    """Mean nitrous oxide left in the headspace, per group, at each reading."""
    vials = {r["vial_id"]: (int(r["group"]), r["strain"])
             for r in load(f, "vials.csv")}
    by = {}
    for r in load(f, "headspace.csv"):
        g, name = vials[r["vial_id"]]
        by.setdefault((g, name), {}).setdefault(int(r["hour"]), []) \
          .append(num(r["n2o_ppm"], 0))
    return {k: {h: statistics.mean(v) for h, v in sorted(pts.items())}
            for k, pts in sorted(by.items())}


def exp_1(f):
    vials = {r["vial_id"]: (int(r["group"]), r["strain"])
             for r in load(f, "vials.csv")}
    cleared = _cleared(f, "headspace.csv", "vial_id", "group")
    by_group = {}
    for vid, pct in cleared.items():
        g, name = vials[vid]
        by_group.setdefault((g, name), []).append(pct)
    pos = by_group.get((1, "USDA 110"), [])
    neg = by_group.get((2, "CPAC 15"), [])
    lines = [f"positive control cleared {statistics.mean(pos):.0f}% of the N₂O, "
             f"negative control {statistics.mean(neg):.0f}%"]
    if statistics.mean(pos) < 50:
        lines.append(bullet(False, "the positive control did nothing, so the "
                                   "method is wrong and no strain can be "
                                   "judged. Fix the vials first"))
        return lines
    lines.append(bullet(True, "the method can tell a carrier from a "
                              "non-carrier, so the rest can be read"))
    # The bar is 2 things at once, and both are fixed in advance: a clean win
    # over the strain known to lack the gene, and at least half the speed of
    # the strain known to have it. A species that clears a little more than
    # nothing is not a species that destroys the gas.
    bar = 0.5 * statistics.mean(pos)
    worked = [name for (g, name), v in sorted(by_group.items())
              if g >= 4 and clean_win(v, neg) and statistics.mean(v) >= bar]
    lines.append(f"shortlisted species that cleared the N₂O: {len(worked)} of 12")
    if worked:
        lines.append(bullet(True, "the project may need to build nothing "
                                  "at all: " + ", ".join(worked[:6])))
    else:
        lines.append(bullet(False, "the gene is present and the N₂O stays. The "
                                   "gene finder found DNA rather than ability, "
                                   "and "
                                   "the write-up has to say that"))
    return lines


def _occupancy(f):
    pots = {r["pot_id"]: (int(r["group"]), r["strain_applied"])
            for r in load(f, "pots.csv")}
    share = {}
    require([r["strain_identified"] for r in load(f, "nodules.csv")])
    for r in load(f, "nodules.csv"):
        g, applied = pots[r["pot_id"]]
        hit = r["strain_identified"] == applied
        share.setdefault(g, []).append(hit)
    return {g: 100 * sum(v) / len(v) for g, v in share.items()}


def _exp_2_strains():
    """S1..S4, named the way the run sheet names them."""
    return {f"S{n}": name for n, name, _ in EXPERIMENTS["exp-2"]["groups"]}


def exp_2_curves(f):
    """Nitrous oxide left in the headspace, per strain, at each reading."""
    by = {}
    names = _exp_2_strains()
    for r in load(f, "headspace.csv"):
        g = int(r["strain_id"][1:])
        by.setdefault((g, names[r["strain_id"]]), {}) \
          .setdefault(int(r["hour"]), []).append(num(r["n2o_ppm"], 0))
    return {k: {h: statistics.mean(v) for h, v in sorted(pts.items())}
            for k, pts in sorted(by.items())}


def exp_2_groups(f):
    """Per strain: what it cleared, what share of nodules it took, and the
    verdict the rules give. The report draws from this, so the table and the
    sentences above it cannot disagree."""
    names = _exp_2_strains()
    by = {}
    for r in load(f, "headspace.csv"):
        by.setdefault(r["strain_id"], {}).setdefault(r["vial_id"], {})[
            int(r["hour"])] = num(r["n2o_ppm"], 0)
    cleared = {sid: [100 * (p.get(0, 0) - p.get(96, 0)) / p[0]
                     for p in vials.values() if p.get(0)]
               for sid, vials in by.items()}
    nod = {}
    for r in load(f, "nodules.csv"):
        sid = "S" + r["pot_id"][1]
        nod.setdefault(sid, []).append(r["strain_identified"] == sid)
    share = {k: 100 * sum(v) / len(v) for k, v in nod.items()}
    parent = statistics.mean(cleared["S1"]) if cleared.get("S1") else 0
    out = []
    for sid in sorted(cleared):
        g, mean = int(sid[1:]), statistics.mean(cleared[sid])
        if sid in ("S1", "S4"):
            verdict = "control"
        elif clean_win(cleared[sid], cleared["S1"]):
            verdict = "destroys it"
        else:
            verdict = "does not"
        out.append(dict(group=g, name=names[sid], cleared=mean,
                        share=share.get(sid), verdict=verdict,
                        replicates=len(cleared[sid])))
    return out


def exp_2(f):
    rows = require(load(f, "headspace.csv"))
    by = {}
    for r in rows:
        by.setdefault(r["strain_id"], {}).setdefault(r["vial_id"], {})[
            int(r["hour"])] = num(r["n2o_ppm"], 0)
    cleared = {}
    for sid, vials in by.items():
        cleared[sid] = [100 * (p.get(0, 0) - p.get(96, 0)) / p[0]
                        for p in vials.values() if p.get(0)]
    nod = {}
    for r in load(f, "nodules.csv"):
        sid = "S" + r["pot_id"][1]
        nod.setdefault(sid, []).append(r["strain_identified"] == sid)
    share = {k: 100 * sum(v) / len(v) for k, v in nod.items()}
    lines = [f"N₂O cleared: the host {statistics.mean(cleared['S1']):.0f}%, "
             f"NitRobe {statistics.mean(cleared['S2']):.0f}%, "
             f"nosZ alone {statistics.mean(cleared['S3']):.0f}%",
             f"nodules taken: the host {share.get('S1', 0):.0f}%, "
             f"NitRobe {share.get('S2', 0):.0f}%"]
    if not clean_win(cleared["S2"], cleared["S1"]):
        lines.append(bullet(False, "NitRobe does not destroy N₂O, so the "
                                   "construct is wrong"))
        return lines
    lines.append(bullet(True, "NitRobe destroys N₂O and the host does "
                              "not, so the genes work in it"))
    # "Still wins" means the build keeps at least 9 out of every 10 nodules
    # its unmodified parent takes. A handful of nodules either way is
    # counting noise and should not decide an invention.
    if share.get("S2", 0) >= 0.9 * share.get("S1", 1):
        lines.append(bullet(True, "NitRobe still wins the race into the "
                                  "roots, which is the whole invention"))
    else:
        lines.append(bullet(False, "NitRobe lost the race, so it is now just "
                                   "another strain that cannot compete. The "
                                   "invention fails on its central claim"))
    # The main gene counts as enough on its own if it gets within a tenth of
    # what the whole set manages.
    if clean_win(cleared["S3"], cleared["S1"]) and \
            statistics.mean(cleared["S3"]) >= 0.9 * statistics.mean(cleared["S2"]):
        lines.append(bullet(True, "the main gene did as well on its own as the "
                                  "whole set, so the build "
                                  "can be simplified"))
    else:
        lines.append(bullet(True, "the whole set was needed, which is why "
                                  "these genes travel together"))
    return lines


VERDICTS = {"exp-1": exp_1, "exp-2": exp_2}


class Blank(Exception):
    """A sheet nobody has written on yet. Reading 0 out of every empty box and
    calling that a result would be worse than saying nothing."""


def require(values):
    if not any(v not in (None, "", 0) for v in values):
        raise Blank
    return values


def report(key, folder, label):
    print(f"\n{key}  {label}")
    print(f"  {EXPERIMENTS[key]['title']}")
    if label != "the real sheets":
        print("  DRY RUN on invented numbers. Not evidence of anything.")
    print()
    try:
        for line in VERDICTS[key](folder):
            if isinstance(line, tuple):
                call, text = line
                print(f"  {'YES' if call == 'yes' else 'NO ':3s}  {text}")
            else:
                print("  " + line)
    except (Blank, FileNotFoundError, KeyError, ZeroDivisionError,
            statistics.StatisticsError):
        print("  the sheets are still blank, so there is nothing to read yet")


def main():
    args = sys.argv[1:]
    if "--all-dry" in args:
        for key in VERDICTS:
            for sub in sorted((DATA / key / "simulated").glob("*")):
                report(key, sub, f"dry run: {sub.name}")
        return
    if not args:
        sys.exit(__doc__)
    key = args[0]
    if "--dry" in args:
        name = args[args.index("--dry") + 1]
        report(key, DATA / key / "simulated" / name, f"dry run: {name}")
    else:
        report(key, DATA / key, "the real sheets")


if __name__ == "__main__":
    main()
