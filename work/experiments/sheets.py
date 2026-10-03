"""
NitRobe -- write the blank sheets, ready to be filled in by hand at the bench.

  python3 sheets.py            every experiment
  python3 sheets.py exp-1      one of them

Each sheet is a plain CSV that opens in any spreadsheet. The rows that can be
known in advance are already there, so a person at the bench fills in numbers
rather than inventing row labels. Two comment lines at the top name the project
and the sheet, so a printed page can always be traced back.

It will NOT overwrite a sheet that already has anything filled in. Filling one
in is weeks of work, and no script of mine gets to delete that by accident.
"""
import csv
import random
import sys
from pathlib import Path

from design import EXPERIMENTS

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

BANNER = ("# NitRobe | 3M Young Scientist Challenge 2027 | {key} | {title}",
          "# Sheet: {name} | blank, to be filled in by hand at the bench "
          "| every column is defined in the codebook")


def units(spec, exp):
    """Name every pot, jar, tube, vial or core, and say which group it is in."""
    _kind, prefix, n = spec["units"]
    reps = spec.get("replicates", 1)
    out = []
    for i in range(1, n + 1):
        g = exp[min((i - 1) // reps, len(exp) - 1)] if reps > 1 else exp[i - 1]
        out.append((f"{prefix}{i:02d}", g, (i - 1) % reps + 1))
    return out


def rows_for(sheet, ids, groups):
    """Build the pre-filled rows, if the rows can be known before day 1."""
    cols, kind = sheet["columns"], sheet["rows"]
    if kind == "none":
        return []
    if kind == "register":
        rows = []
        # The shelf position is shuffled on purpose. Set out in group order,
        # one group quietly gets the brightest, warmest end of the shelf, and
        # nothing done later can undo that.
        order = list(range(1, len(ids) + 1))
        random.Random(1027).shuffle(order)
        for (uid, (num, name, _why), rep), pos in zip(ids, order):
            r = {cols[0]: uid}
            if "group" in cols:
                r["group"] = num
            if "replicate" in cols:
                r["replicate"] = rep
            for c in ("group_name", "strain", "strain_applied"):
                if c in cols:
                    r[c] = name
            for c in ("bench_position", "rack_position", "window_position",
                      "chamber_position"):
                if c in cols:
                    r[c] = pos
            rows.append(r)
        return rows
    # A time series: 1 row per unit per reading, with the reading left blank.
    label, *points = kind
    if len(points) == 2 and points[1] > points[0] + 1:
        points = list(range(points[0], points[1] + 1))
    return [{cols[0]: uid, label: p} for uid, _g, _r in ids for p in points]


def write(key, spec):
    exp = spec["groups"]
    ids = units(spec, exp)
    folder = DATA / key
    folder.mkdir(parents=True, exist_ok=True)
    for name, sheet in sorted(spec["sheets"].items()):
        path = folder / name
        if path.exists() and has_data(path):
            print(f"  {key}/{name:16s} left alone, it already has data in it")
            continue
        rows = rows_for(sheet, ids, exp)
        with open(path, "w", newline="") as fh:
            for line in BANNER:
                fh.write(line.format(key=key, title=spec["title"],
                                     name=name) + "\n")
            w = csv.DictWriter(fh, fieldnames=sheet["columns"])
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"  {key}/{name:16s} {len(rows):4d} rows, "
              f"{len(sheet['columns'])} columns")


def has_data(path):
    with open(path) as fh:
        body = [ln for ln in fh if not ln.lstrip().startswith("#")]
    # A header, then pre-filled row labels with every measurement blank, is
    # still a blank sheet. Anything else has been worked on.
    return any(any(c.strip() for c in ln.split(",")[2:]) for ln in body[1:])


def main():
    want = sys.argv[1:] or list(EXPERIMENTS)
    for key in want:
        if key not in EXPERIMENTS:
            sys.exit(f"no experiment called {key}")
        print(f"\n{key}: {EXPERIMENTS[key]['title']}")
        write(key, EXPERIMENTS[key])
    print(f"\n  sheets are in {DATA}")


if __name__ == "__main__":
    main()
