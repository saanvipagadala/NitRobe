"""
NitRobe -- write the codebook: every sheet, every column, what goes in it.

  python3 codebook.py     ->  codebook.md

The codebook is generated from design.py rather than typed out, so a column
cannot exist on a sheet and be missing from the codebook, or mean 2 different
things in the 2 places. Only the plain-English meaning of each column lives
here, in MEANING below.
"""
from pathlib import Path

from design import EXPERIMENTS

ROOT = Path(__file__).resolve().parent

MEANING = {
 "group": "the group number, from the table of groups above",
 "group_name": "the group's name, copied from the same table",
 "replicate": "1, 2 or 3. Which of the identical copies this one is",
 "notes": "anything unusual. A knocked pot, a cloudy strip, a late reading",
 "date": "the day it was measured, as YYYY-MM-DD",
 "date_time": "the day and clock time, because readings hours apart need both",
 "seeds_planted": "how many seeds went in, counted before covering them",
 "window_position": "where the pot sits on the sill, in the shuffled order given",
 "bench_position": "where the pot sits on the bench, in the shuffled order given",
 "rack_position": "where the vial sits in the rack, in the shuffled order given",
 "chamber_position": "where the core sits, in the shuffled order given",
 "date_planted": "the day the seeds went in",
 "date_started": "the day it was set up",
 "date_sealed": "the day the vial was closed, which is hour 0",
 "week": "0 to the last week. Week 0 is the day it was set up",
 "day": "0 upwards. Day 0 is the day it was set up",
 "hour": "hours since the vial was sealed. 0, 6, 24, 48 or 96, which is the start, then 6 hours, 1 day, 2 days and 4 days",
 "tallest_plant_cm": "the tallest plant in the pot, soil to tip, in centimetres",
 "leaves_counted": "how many leaves are open. Count, do not estimate",
 "leaf_colour_1_to_5": "1 is yellow, 5 is dark green. Judged against the same "
                       "printed card every week, in the same light",
 "plants_harvested": "how many plants were pulled and washed",
 "nodules_counted": "nodules on the washed roots. Count every one",
 "nodules_cut_open": "how many nodules were sliced with a blade",
 "nodules_pink_inside": "how many of those were bright pink inside. Pink means "
                        "nitrogen is being fixed",
 "soil_g": "grams of soil that went in", "water_ml": "millilitres of water",
 "sugar_g": "grams of sugar, which is what the bacteria eat",
 "time": "clock time of the reading. Both jars are read at the same time",
 "nitrate_ppm": "the number on the test strip, read against the bottle's chart",
 "water_colour": "what the water looks like: clear, cloudy, grey, black",
 "liquid_in_tube": "nitrate solution, or plain water",
 "soil_treatment": "live, or boiled and cooled",
 "gas_gap_mm": "the height of the gas at the closed top of the tube, against a "
               "ruler taped behind the jar",
 "photo_taken": "yes or no. Every reading gets a photo",
 "strain": "which strain is in the vial",
 "strain_applied": "which strain went on the seed, or none",
 "n2o_ppm": "nitrous oxide above the liquid, from the gas chromatograph",
 "od600": "how cloudy the liquid is, which is how much the bacteria have grown",
 "operator": "who took the reading",
 "soil_batch": "which bag of field soil this pot was filled from",
 "soil_source": "where the soil core came from",
 "nodule_id": "N01 upwards, one per nodule opened from this pot",
 "nodule_colour": "what the inside looks like: pink, white, green",
 "strain_identified": "which strain was found inside the nodule, or 'native "
                      "soil strain' if it was neither of ours",
 "method": "how it was identified. Colony PCR, or sequencing",
 "strain_id": "S1 to S4, the strain this row is about",
 "parent_strain": "the strain it was built from",
 "genes_added": "which genes were put in, or none",
 "sequence_confirmed": "yes or no. Was the DNA read back and checked",
 "date_built": "the day the strain was finished",
 "event": "what was done: inoculated and sown, fertilised, flooded",
 "amount": "how much was applied",
 "minutes_closed": "minutes since the chamber lid went on. 0, 10, 20, 30",
 "soil_temp_c": "soil temperature in degrees Celsius",
 "soil_moisture_pct": "how wet the soil is, as a percentage",
}

HEAD = """# The codebook

Every sheet in every experiment, and what belongs in every column of every one
of them.

A column that means 1 thing at the bench and another thing in the analysis
would quietly ruin an experiment, so each column is written down once, here,
and both the person and the code follow it.

**Write down only what can be read off an instrument**: a height, a weight, a
number on a test strip, a count of nodules, a reading from a machine. Every
percentage and every average is worked out afterwards by
[analyze.py](analyze.py), so each figure in the verdict leads back to something
somebody actually measured.

**A box left empty means the measurement was not taken.** It does not mean
zero. If a thing was measured and the answer was none, write 0.

The blank sheets are written by [sheets.py](sheets.py), this codebook by
[codebook.py](codebook.py), and the invented ones under `simulated/` by
[simulate.py](simulate.py).
"""


def main():
    out = [HEAD]
    for key, spec in EXPERIMENTS.items():
        out.append(f"\n---\n\n## {key}\n\n**{spec['title']}**\n")
        out.append("### The groups\n")
        out.append("| | Group | Why it is here |")
        out.append("|---|---|---|")
        for num, name, why in spec["groups"]:
            out.append(f"| **{num}** | {name} | {why} |")
        reps = spec.get("replicates", 1)
        kind, _p, n = spec["units"]
        out.append(f"\n**{n} {kind}s in all"
                   + (f", {reps} identical ones per group" if reps > 1 else "")
                   + ".** They are set out in a shuffled order rather than "
                     "grouped by recipe. Lined up by group, 1 group quietly "
                     "gets the brightest, warmest end of the shelf, and "
                     "nothing done later can undo that.\n")
        for name, sheet in sorted(spec["sheets"].items()):
            out.append(f"### `{name}`\n")
            out.append(sheet["what"] + "\n")
            out.append(f"<small>[Download {name}](data/{key}/{name}) &middot; "
                       f"blank, ready to fill in</small>\n")
            out.append("| Column | What goes in it |")
            out.append("|---|---|")
            for c in sheet["columns"]:
                out.append(f"| `{c}` | {MEANING.get(c, '')} |")
            out.append("")
    (ROOT / "codebook.md").write_text("\n".join(out) + "\n")
    print(f"  codebook.md written, {len(EXPERIMENTS)} experiments")


if __name__ == "__main__":
    main()
