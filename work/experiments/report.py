"""
NitRobe -- turn a folder of bench sheets into a report page.

  python3 report.py --all-dry      a report for every dry run
  python3 report.py exp-1          a report from the real sheets

Every verdict on the page was decided by a rule in analyze.py that was written
down before any data existed, so a disappointing answer counts exactly as much
as a good one. A report built from invented numbers says so in its title, and
again in a quiet note at the top: loud enough that nobody mistakes it for a
result, quiet enough to read past.
"""
import datetime
import html
import sys
from pathlib import Path

import analyze
from design import EXPERIMENTS
from simulate import SCENARIOS

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "results"

CSS = """
:root { --bg:#FBFAF7; --surface:#fff; --ink:#1B1A17; --ink-2:#4A4740;
        --ink-3:#7C776C; --rule:#E2DDD1; --good:#1C6B4A; --bad:#A33A2A;
        --warn:#B5651D; }
@media (prefers-color-scheme:dark) { :root:not([data-theme="light"]) {
  --bg:#14161A; --surface:#1B1E24; --ink:#F2EFE8; --ink-2:#BFBAAF;
  --ink-3:#8B867B; --rule:#2E333C; --good:#3E9E71; --bad:#E0705C;
  --warn:#E9A23C; } }
:root[data-theme="dark"] { --bg:#14161A; --surface:#1B1E24; --ink:#F2EFE8;
  --ink-2:#BFBAAF; --ink-3:#8B867B; --rule:#2E333C; --good:#3E9E71;
  --bad:#E0705C; --warn:#E9A23C; }
* { box-sizing:border-box }
body { margin:0; background:var(--bg); color:var(--ink);
       font:16px/1.6 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif }
.wrap { max-width:56rem; margin:0 auto; padding:36px clamp(20px,4vw,48px) 88px }
header { border-bottom:2px solid var(--ink); padding-bottom:20px }
.eyebrow { font-size:12px; letter-spacing:.14em; text-transform:uppercase;
           color:var(--ink-3); font-weight:650; margin:0 0 8px;
           display:flex; align-items:center; gap:8px }
.eyebrow .mark { width:30px; height:20px }
h1 { font-size:clamp(26px,3.4vw,40px); line-height:1.15; margin:0 0 10px;
     letter-spacing:-.02em }
.sub { color:var(--ink-2); margin:0; font-size:17px }
.stamp { color:var(--ink-3); font-size:13px; margin-top:14px }
h2 { font-size:23px; margin:48px 0 6px; letter-spacing:-.01em }
h2 + .lede { color:var(--ink-2); margin:0 0 18px }
.banner { border-left:3px solid var(--warn); padding:2px 0 2px 14px;
          margin:22px 0 0; color:var(--ink-2); font-size:15px }
.banner b { color:var(--warn) }
.banner span { display:block; margin-top:3px; color:var(--ink-3) }
.cards { display:grid; gap:16px; margin:18px 0 0;
         grid-template-columns:repeat(auto-fit,minmax(290px,1fr)) }
.card { background:var(--surface); border:1px solid var(--rule);
        border-radius:12px; padding:18px 20px; border-top:4px solid var(--ink-3) }
.card.yes { border-top-color:var(--good) } .card.no { border-top-color:var(--bad) }
.card .call { font-size:15px; font-weight:680; letter-spacing:.06em;
              text-transform:uppercase; margin:0 0 6px }
.card.yes .call { color:var(--good) } .card.no .call { color:var(--bad) }
.card p { margin:0; font-size:15px; color:var(--ink-2) }
.facts { list-style:none; padding:0; margin:0 }
.facts li { border-bottom:1px solid var(--rule); padding:10px 0;
            color:var(--ink-2) }
table { border-collapse:collapse; width:100%; font-size:14.5px }
th,td { text-align:left; padding:8px 10px; border-bottom:1px solid var(--rule) }
th { font-size:12px; letter-spacing:.05em; text-transform:uppercase;
     color:var(--ink-3) }
figure { margin:18px 0 0 }
figcaption { color:var(--ink-3); font-size:13px; margin-top:10px }
.chart { width:100%; height:auto; display:block;
         --cleared:#2A6B4A; --stayed:#A8761C; --ref:#7C776C }
@media (prefers-color-scheme:dark) { :root:not([data-theme="light"]) .chart {
  --cleared:#3E9E71; --stayed:#B3842A; --ref:#8B867B } }
:root[data-theme="dark"] .chart { --cleared:#3E9E71; --stayed:#B3842A;
  --ref:#8B867B }
.chart .grid { stroke:var(--rule); stroke-width:1 }
.chart .axis { fill:var(--ink-3); font-size:12px }
.chart .lbl  { fill:var(--ink-2); font-size:12.5px }
.chart path { fill:none; stroke-width:2; stroke-linecap:round;
              stroke-linejoin:round }
.chart .s-cleared { stroke:var(--cleared) }
.chart .s-stayed  { stroke:var(--stayed) }
.chart .s-ref     { stroke:var(--ref); stroke-dasharray:5 4 }
.chart .thick { stroke-width:3.5 }
.key { display:flex; flex-wrap:wrap; gap:16px; margin:12px 0 0; padding:0;
       list-style:none; font-size:13.5px; color:var(--ink-2) }
.key li { display:flex; align-items:center; gap:7px }
.key i { width:18px; height:0; border-top-width:3px; border-top-style:solid;
         display:inline-block }
.end { color:var(--ink-3); font-size:13px; margin-top:52px;
       border-top:1px solid var(--rule); padding-top:14px }
a { color:inherit }
"""


# ----------------------------------------------------------------- the chart

# Both experiments read the same vial, so both get the same picture and the
# same table. The only difference is which rows count as controls.
CURVES = {"exp-1": ("exp_1_curves", "exp_1_groups", (1, 2, 3)),
          "exp-2": ("exp_2_curves", "exp_2_groups", (1, 4))}


def curve_chart(key, folder):
    """Gas left above the liquid, per group, at each reading.

    A line that falls is a strain destroying the gas. The controls are drawn
    dashed and named, the rest are coloured by the verdict the rules reached,
    so the picture cannot disagree with the sentences above it.
    """
    if key not in CURVES:
        return ""
    curve_fn, group_fn, controls = CURVES[key]
    try:
        curves = getattr(analyze, curve_fn)(folder)
        rows = {(r["group"], r["name"]): r["verdict"]
                for r in getattr(analyze, group_fn)(folder)}
    except (analyze.Blank, FileNotFoundError, KeyError, ZeroDivisionError,
            StopIteration):
        return ""
    if not curves:
        return ""
    hours = sorted({h for pts in curves.values() for h in pts})
    top = max((v for pts in curves.values() for v in pts.values()), default=0)
    if not hours or not top:
        return ""
    top = top * 1.1
    W, H = 760, 330
    L, R, T, B = 52, 150, 16, 44

    def x(h):
        return L + (W - L - R) * hours.index(h) / max(1, len(hours) - 1)

    def y(v):
        return T + (H - T - B) * (1 - v / top)

    parts, ends = [], []
    for (g, name), pts in curves.items():
        d = " ".join(f"{'M' if i == 0 else 'L'}{x(h):.1f},{y(pts[h]):.1f}"
                     for i, h in enumerate(hours) if h in pts)
        verdict = rows.get((g, name), "")
        # Colour only ever reports a verdict, so the 3 controls stay neutral
        # and named. A green positive control in a run where it cleared
        # nothing would be the picture telling a lie.
        if g in controls:
            cls, thick = "s-ref", g == controls[0]
        elif verdict in ("cleared", "destroys it"):
            cls, thick = "s-cleared", False
        else:
            cls, thick = "s-stayed", False
        parts.append(f'<path class="{cls}{" thick" if thick else ""}" '
                     f'd="{d}"/>')
        if g in controls:
            ends.append([y(pts[hours[-1]]), name])

    # Push the control labels apart so 2 flat lines do not print on top of
    # each other.
    ends.sort()
    for i in range(1, len(ends)):
        ends[i][0] = max(ends[i][0], ends[i - 1][0] + 17)
    labels = [f'<text class="lbl" x="{x(hours[-1]) + 8:.1f}" '
              f'y="{yy + 4:.1f}">{html.escape(nm)}</text>' for yy, nm in ends]

    grid = "".join(
        f'<line class="grid" x1="{L}" x2="{W - R}" y1="{y(v):.1f}" '
        f'y2="{y(v):.1f}"/>'
        f'<text class="axis" x="{L - 8}" y="{y(v) + 4:.1f}" '
        f'text-anchor="end">{v:.0f}</text>'
        for v in [0, top / 2, top])
    # Hours on the sheet, because that is what the clock says at the bench.
    # Days on the axis, because 96 means nothing at a glance.
    def tick(h):
        if h == 0:
            return "start"
        if h % 24:
            return f"{h}h"
        return f"{h // 24} day" + ("s" if h // 24 > 1 else "")

    ticks = "".join(
        f'<text class="axis" x="{x(h):.1f}" y="{H - B + 22}" '
        f'text-anchor="middle">{tick(h)}</text>' for h in hours)
    return f"""<h2>The N₂O, over 4 days</h2>
<figure>
<svg class="chart" viewBox="0 0 {W} {H}" role="img"
     aria-label="Nitrous oxide left in each vial over 96 hours.">
{grid}{"".join(parts)}{"".join(labels)}{ticks}
</svg>
<ul class="key">
<li><i style="border-color:var(--cleared)"></i>cleared the N₂O</li>
<li><i style="border-color:var(--stayed)"></i>N₂O stayed</li>
<li><i style="border-color:var(--ref)"></i>controls, named on the right</li>
</ul>
<figcaption>Nitrous oxide left above the liquid, in ppm, timed from the moment
the vial was sealed. Each line is the average of that group's 3 vials. A line
that falls is a strain destroying N₂O.</figcaption>
</figure>"""


def results_table(key, folder):
    """Every group, what it cleared, and what the rules called it.

    Experiment 2 also opens nodules, so its table carries that column too.
    The column appears only when there are nodules to put in it.
    """
    if key not in CURVES:
        return ""
    try:
        rows = getattr(analyze, CURVES[key][1])(folder)
    except (analyze.Blank, FileNotFoundError, KeyError, ZeroDivisionError,
            StopIteration):
        return ""
    if not rows:
        return ""
    nodules = any(r.get("share") is not None for r in rows)
    head = ("<th>No.</th><th>Strain</th><th>N₂O cleared</th>" +
            ("<th>Nodules taken</th>" if nodules else "") + "<th>The call</th>")
    body = ""
    for r in rows:
        share = ("<td>%.0f%%</td>" % r["share"] if r.get("share") is not None
                 else "<td>&mdash;</td>") if nodules else ""
        body += (f'<tr><td>{r["group"]}</td><td>{html.escape(r["name"])}</td>'
                 f'<td>{r["cleared"]:.0f}%</td>{share}'
                 f'<td>{html.escape(r["verdict"])}</td></tr>')
    said = ("What each one cleared in the vials by 96 hours, what share of the "
            "nodules it took in the pots, and what the rules called it."
            if nodules else
            "What each one cleared by 96 hours, averaged over its 3 vials, "
            "and what the rules called it.")
    return f"""<h2>Every group</h2>
<p class="lede">{said}</p>
<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"""


def page(key, folder, scenario):
    spec = EXPERIMENTS[key]
    dry = scenario is not None
    try:
        lines = analyze.VERDICTS[key](folder)
    except (analyze.Blank, FileNotFoundError, KeyError, ZeroDivisionError):
        lines = ["The sheets are still blank, so there is nothing to read yet."]
    cards = "".join(
        f'<div class="card {c}"><p class="call">{"Yes" if c == "yes" else "No"}'
        f'</p><p>{html.escape(t)}</p></div>'
        for c, t in [l for l in lines if isinstance(l, tuple)])
    facts = "".join(f"<li>{html.escape(l)}</li>"
                    for l in lines if isinstance(l, str))
    chart, groups = curve_chart(key, folder), results_table(key, folder)
    if not chart and not groups:
        chart = ""
        rows = "".join(
            f"<tr><td>{n}</td><td>{html.escape(name)}</td>"
            f"<td>{html.escape(why)}</td></tr>" for n, name, why in spec["groups"])
        groups = ("<h2>The groups</h2>\n<table><thead><tr><th>No.</th>"
                  "<th>Group</th><th>Why it is here</th></tr></thead>"
                  f"<tbody>{rows}</tbody></table>")
    title = ("Dry run: " + scenario) if dry else "Report"
    banner = (f'<div class="banner"><b>A dry run.</b> The numbers below were '
              f'invented, to check that the analysis reads them correctly.'
              f'<span>{html.escape(SCENARIOS[key][scenario])}</span></div>'
              if dry else "")
    # Published at work/experiments/results/<key>/<scenario>/report.html, so
    # the site root is 5 folders up, or 4 for a report from the real sheets.
    back = "../" * (5 if dry else 4)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} &middot; {key}</title>
<link rel="icon" href="{back}nitrobe.svg">
<style>{CSS}</style></head><body><div class="wrap">
<header>
  <p class="eyebrow"><img src="{back}nitrobe.svg" alt="" class="mark">
     NitRobe &middot; 3M Young Scientist Challenge 2027 &middot; {key}</p>
  <h1>{html.escape(spec['title'])}</h1>
  <p class="sub">{'A dry run on invented numbers, to check that the analysis '
                 'tells the truth.' if dry else 'Read from the sheets filled '
                 'in at the bench.'}</p>
  <p class="stamp">Written by report.py on {datetime.date.today()} &middot;
     <a href="{back}experiments/{key}.html">the run sheet</a></p>
</header>
{banner}

<h2>What the numbers show</h2>
<p class="lede">Every answer below was decided by a rule written down
<em>before</em> any data existed, so a disappointing answer counts exactly as
much as a good one.</p>
<div class="cards">{cards}</div>

{chart}

<h2>The numbers behind it</h2>
<ul class="facts">{facts}</ul>

{groups}

<div class="end">end of report</div>
</div></body></html>
"""


def write(key, folder, scenario, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page(key, folder, scenario))
    print(f"  {out.relative_to(ROOT)}")


def main():
    args = sys.argv[1:]
    if "--all-dry" in args:
        for key in EXPERIMENTS:
            for scenario in SCENARIOS[key]:
                write(key, DATA / key / "simulated" / scenario, scenario,
                      OUT / key / scenario / "report.html")
        return
    if not args:
        sys.exit(__doc__)
    key = args[0]
    write(key, DATA / key, None, OUT / key / "report.html")


if __name__ == "__main__":
    main()
