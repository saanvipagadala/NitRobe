"""
NitRobe -- draw the setup for each experiment, by hand.

  python3 diagrams.py      ->  results/diagrams/<experiment>.png

Every diagram is drawn for somebody who has never seen the apparatus. The
groups carry the same names the sheets use, the controls are marked as
controls, and nothing appears in a picture that is not also in the words.

The pen is in hand.py. These are the scenes.
"""
import sys
from pathlib import Path

# The pen is shared by every drawing in the submission, so it lives 1 folder up.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import math
import re

from hand import Crayon, DOODLE, MARK, render, text, wash_defs

OUT = Path(__file__).resolve().parent / "results" / "diagrams"

GREY = "#5a5a5a"
SOIL = ("#8a6a45", 0.34)
WATER = ("#6f9fb5", 0.40)
GAS = ("#d9a13c", 0.52)
NODULE = ("#c2607a", 0.52)
LEAF = ("#7ea15f", 0.44)
DEAD = ("#9b9b9b", 0.30)

# The growth medium. 1 colour, because it is 1 batch poured into every
# vial. The sterile vials get the same liquid with nothing living in it.
BROTH = ("#6f9fb5", 0.40)
STERILE = ("#9b9b9b", 0.16)
BUG = ("#2f5f73", 0.85)

# Who is living inside a nodule. Solid, not washed: in the pot stage of
# experiment 2 this colour is the entire result, so it has to survive
# being drawn on top of soil.
LOCALS, KNOWN, OURS = "#b9b1a6", "#7fb0c6", "#86c07a"

W = 1560


def shelf(items, header, footer, draw, top=240, bot=430, H=720, seed=23,
          note_gap=0, key=None):
    """A row of drawn things, each with its name and its job written under it.

    Every experiment in this project is a row of containers that differ by one
    thing, so they are all drawn the same way and a fix to one is a fix to all
    of them.
    """
    c = Crayon(seed)
    o = [wash_defs(), text(W / 2, 62, header, 40, DOODLE)]
    cw = (W - 80) / len(items)
    for i, item in enumerate(items):
        cx = 40 + cw * (i + 0.5)
        o.append(draw(c, cx, top, bot, item, cw))
        o.append(text(cx, bot + 72 + note_gap, item["name"], 32, DOODLE))
        o.append(text(cx, bot + 120 + note_gap, item["note"], 26, GREY))
        if item.get("why"):
            o.append(text(cx, bot + 168 + note_gap, item["why"], 26,
                          MARK if item.get("star") else GREY))
        if item.get("star"):
            o.append(c.out([(cx - 110, bot + 184 + note_gap),
                            (cx - 20, bot + 190 + note_gap),
                            (cx + 60, bot + 182 + note_gap),
                            (cx + 110, bot + 188 + note_gap)],
                           w=4.4, jit=1.4))
    if key:
        # Wide enough for the longest label, so 2 long entries cannot print
        # on top of each other.
        # Measured on the words a reader sees. A label carrying markup, such
        # as the subscript in N2O, is far longer as a string than it is on the
        # page, and sizing by the string pushed the first entry off-canvas.
        seen = lambda w: len(re.sub(r"<[^>]+>", "", w))
        step = max(300, 15 * max(seen(w) for _, w in key) + 60)
        kx = W / 2 - (len(key) * step) / 2 + 30
        for i, (colour, what) in enumerate(key):
            x = kx + i * step
            o.append(c.out(c.blob(x, H - 104, 14, 12, 9, 0.14), close=True,
                           w=4.0, fill=colour))
            o.append(text(x + 26, H - 96, what, 25, GREY, "start"))
    o.append(text(W / 2, H - 30, footer, 30, DOODLE))
    return W, H, "\n".join(o)


# -------------------------------------------------------------- the objects

def draw_pot(c, cx, top, bot, it, cw):
    """A pot, with the plant above the rim and the root below it."""
    tw, bw = 190, 140
    o = [c.out([(cx - tw / 2, top), (cx + tw / 2, top),
                (cx + bw / 2, bot), (cx - bw / 2, bot)], close=True,
               w=6.0, fill="#ffffff")]
    o.append(c.paint([(cx - tw / 2 + 8, top + 26), (cx - 20, top + 17),
                      (cx + 30, top + 33), (cx + tw / 2 - 8, top + 22),
                      (cx + bw / 2 - 5, bot - 8), (cx - bw / 2 + 5, bot - 8)],
                     *SOIL))
    o.append(c.round_blob(cx, top, tw / 2, 14, w=5.2, n=19))
    # The stem and its leaves, taller where the plant is fed.
    h = it["plant"]
    o.append(c.out([(cx, top + 10), (cx + 4, top - h / 2), (cx, top - h)],
                   w=5.2))
    for k, (dx, dy) in enumerate(((-34, 0.42), (36, 0.72))):
        pts = c.blob(cx + dx, top - h * dy, 30, 15, 11, 0.1)
        o.append(c.paint(pts, *LEAF, inner=False))
        o.append(c.out(pts, close=True, w=4.4))
    # The root, and the nodules on it.
    o.append(c.out([(cx, top + 30), (cx - 6, top + 90), (cx + 4, bot - 16)],
                   w=4.4))
    # Each nodule is drawn in the colour of whichever strain was found inside
    # it. A pot with a mix of colours is a pot the candidate only half won.
    inside = it.get("inside")
    for k in range(it["nodules"]):
        nx = cx + (-26 if k % 2 else 24)
        ny = top + 52 + k * 30
        pts = c.blob(nx, ny, 15, 13, 9, 0.14)
        fill = inside[k % len(inside)] if inside else NODULE[0]
        o.append(c.out(pts, close=True, w=4.2, fill=fill))
    return "".join(o)


def draw_jar(c, cx, top, bot, it, cw):
    """A jar of soil and water, sealed or open."""
    w = 200 if it.get("tall") else 260
    h = (bot - top) if it.get("tall") else 96
    y = top if it.get("tall") else bot - h
    o = [c.out([(cx - w / 2, y), (cx + w / 2, y),
                (cx + w / 2, y + h), (cx - w / 2, y + h)], close=True,
               w=6.0, fill="#ffffff")]
    o.append(c.paint([(cx - w / 2 + 8, y + 14), (cx, y + 6), (cx + w / 2 - 8, y + 12),
                      (cx + w / 2 - 6, y + h - 8), (cx - w / 2 + 6, y + h - 8)],
                     *WATER))
    if it.get("sealed"):
        o.append(c.out([(cx - w / 2 - 6, y - 14), (cx + w / 2 + 6, y - 14)],
                       w=9.0))
        o.append(text(cx, y - 30, "sealed", 26, DOODLE))
    else:
        for k in range(4):
            ax = cx - 78 + k * 52
            o.append(c.out([(ax, y - 78), (ax, y - 18)], w=4.4))
            o.append(c.out([(ax - 9, y - 32), (ax, y - 16), (ax + 9, y - 32)],
                           w=4.4))
        o.append(text(cx, y - 96, "air keeps getting in", 26, DOODLE))
    return "".join(o)


def draw_tube(c, cx, top, bot, it, cw):
    """A jar of slurry with an upside-down tube standing in it."""
    w, h = 250, bot - top
    o = [c.out([(cx - w / 2, top), (cx + w / 2, top), (cx + w / 2, bot),
                (cx - w / 2, bot)], close=True, w=6.0, fill="#ffffff")]
    o.append(c.out([(cx - w / 2 - 6, top - 12), (cx + w / 2 + 6, top - 12)],
                   w=9.0))
    o.append(c.paint([(cx - w / 2 + 8, top + 16), (cx, top + 8),
                      (cx + w / 2 - 8, top + 14), (cx + w / 2 - 6, bot - 8),
                      (cx - w / 2 + 6, bot - 8)], *SOIL))
    tw = 74
    o.append(c.out([(cx - tw / 2, top + 22), (cx + tw / 2, top + 22),
                    (cx + tw / 2, bot - 26), (cx - tw / 2, bot - 26)],
                   close=True, w=5.2, fill="#ffffff"))
    if it["gas"]:
        o.append(c.paint([(cx - tw / 2 + 5, top + 26), (cx + tw / 2 - 5, top + 26),
                          (cx + tw / 2 - 5, top + 92), (cx - tw / 2 + 5, top + 96)],
                         *GAS))
        o.append(text(cx, top + 72, "gas", 28, DOODLE))
    return "".join(o)


def vial(c, x, top, bot, wash, gas=True, bugs=False, strain=None):
    """One sealed vial, drawn the same way everywhere it appears.

    Liquid food in the bottom with whatever is alive in it, a sealed gas space
    above that, and a rubber septum under a crimped cap on top. The septum is
    the point. It is what lets a syringe take a sample 5 times without ever
    opening the vial.

    Both experiments use this, so the glass a reader learns on experiment 1 is
    the same glass they meet again on experiment 2.
    """
    o = [c.out([(x - 33, top), (x + 33, top), (x + 33, bot), (x - 33, bot)],
               close=True, w=5.6, fill="#ffffff")]
    o.append(c.paint([(x - 27, top + 82), (x, top + 74), (x + 27, top + 80),
                      (x + 27, bot - 8), (x - 27, bot - 8)], *wash))
    if bugs:
        # The bacteria, so a reader can see what is alive in there and what is
        # not, rather than having to read it off a colour.
        for dx, dy in ((-16, 22), (6, 14), (19, 34), (-7, 46), (14, 58),
                       (-20, 66), (2, 78), (21, 88), (-12, 96)):
            o.append(c.paint(c.blob(x + dx, top + 92 + dy, 4, 4, 7, 0.22),
                             *BUG, inner=False))
    if strain:
        # Experiment 2 has 1 named strain per vial rather than a cloud of
        # them, so it gets the creature instead of the dots.
        colour, face = strain
        o.append(microbe(x, top + 116, 1.35, colour, face=face))
        o.append(microbe(x - 10, top + 164, 1.1, colour, face=False))
    if gas:
        o.append(c.paint(c.blob(x, top + 40, 22, 20, 9, 0.14), *GAS,
                         inner=False))
    # the crimp cap, sitting over the septum
    o.append(c.out([(x - 38, top - 26), (x + 38, top - 26),
                    (x + 38, top - 2), (x - 38, top - 2)],
                   close=True, w=4.6, fill="#d9d5cc"))
    return "".join(o)


def draw_vials(c, cx, top, bot, it, cw):
    """3 identical vials, because every strain is run 3 times."""
    return "".join(vial(c, cx - 92 + k * 92, top, bot, it["wash"],
                        gas=it["gas"], bugs=it.get("bugs"))
                   for k in range(3))


def draw_core(c, cx, top, bot, it, cw):
    """An intact core of field soil under a sealed chamber."""
    w = 230
    o = [c.out([(cx - w / 2 - 14, top - 96), (cx - w / 2 - 14, top - 10),
                (cx + w / 2 + 14, top - 10), (cx + w / 2 + 14, top - 96)],
               w=6.0)]
    o.append(text(cx, top - 112, "sealed lid", 26, DOODLE))
    o.append(c.out([(cx - w / 2, top), (cx + w / 2, top), (cx + w / 2, bot),
                    (cx - w / 2, bot)], close=True, w=6.0, fill="#ffffff"))
    for k, band in enumerate(((0, 40), (40, 86), (86, bot - top - 4))):
        o.append(c.paint([(cx - w / 2 + 8, top + band[0] + 6),
                          (cx + w / 2 - 8, top + band[0] + 2),
                          (cx + w / 2 - 8, top + band[1]),
                          (cx - w / 2 + 8, top + band[1])],
                         SOIL[0], 0.22 + k * 0.13))
    if it["gas"]:
        for k, (dx, dy) in enumerate(((-52, 26), (8, 46), (58, 22))):
            o.append(c.paint(c.blob(cx + dx, top - 46 + dy - 40, 20, 17, 9, .2),
                             *GAS, inner=False))
    return "".join(o)


# ------------------------------------------------------------- the 7 scenes

def exp_1():
    # This is the set-up, on day 1, before anything has happened. Every vial
    # gets the same food, the same dose of gas and the same seal, so they are
    # all drawn alike. The 1 thing that differs is what was put in the liquid,
    # which is the only thing the experiment changes. Drawing a vial here with
    # its gas already gone would be announcing the result before it is run.
    items = [
        dict(name="USDA 110", note="known to destroy " + n2o(26),
             why="the positive control", wash=BROTH, gas=True, bugs=True),
        dict(name="CPAC 15", note="known to lack the gene",
             why="the negative control", wash=BROTH, gas=True, bugs=True),
        dict(name="No bacteria", note="sterile medium",
             why="shows the " + n2o(26) + " cannot leak out", wash=STERILE, gas=True),
        dict(name="The 12", note="1 per shortlisted species",
             why="the actual question", wash=BROTH, gas=True, star=True,
             bugs=True),
    ]
    return shelf(items, "45 sealed vials. No air, the same dose of " + n2o(40) + " in each.",
                 "3 vials of every strain, so no single lucky vial decides "
                 "anything. Read at the start, 6 hours, 1, 2 and 4 days.",
                 draw_vials, top=200, bot=400, H=740,
                 key=[(GAS[0], "the dose of " + n2o(25)),
                      (BUG[0], "the bacteria, in their food and water")])


def n2o(size):
    """Nitrous oxide with a real subscript. The hand font has no sub, so the
    2 is dropped and resized, then the baseline is put back for the O."""
    return f'N<tspan dy="{size * 0.22:.0f}" font-size="{size * 0.72:.0f}">2</tspan><tspan dy="{-size * 0.22:.0f}">O</tspan>'


# The creature from the project mark, assets/nitrobe.svg, drawn at any size.
# Same geometry as the file, so the face on a diagram and the face in the
# corner of every page are the same animal.
NITROBE_GREEN = "#4fa46c"
HOST_GREY = "#a9a49b"
# Labels on the drawings sit back in a light grey, so the headings stay the
# darkest thing on the page and the black flow arrows keep the sequence.
LABEL = "#8d8a84"


def microbe(cx, cy, s, colour=NITROBE_GREEN, face=True):
    """The mark. Without a face it reads as just another bacterium."""
    eyes = ('<circle cx="-3.5" cy="-1.5" r="1.7" fill="#0e1016"/>'
            '<circle cx="3.5" cy="-1.5" r="1.7" fill="#0e1016"/>') if face else ""
    return (f'<g transform="translate({cx:.1f},{cy:.1f}) scale({s})">'
            f'<ellipse rx="12.5" ry="10" fill="{colour}"/>'
            f'<path d="M 12 3 C 18 6 20 -1 25 1" fill="none" stroke="{colour}"'
            f' stroke-width="2" stroke-linecap="round"/>'
            f'<path d="M -9 -7 L -14 -12" stroke="{colour}" stroke-width="1.8"'
            f' stroke-linecap="round"/>'
            f'<path d="M -2 -10 L -4 -16" stroke="{colour}" stroke-width="1.8"'
            f' stroke-linecap="round"/>{eyes}</g>')


def down_arrow(c, x, y0, y1):
    return (c.out([(x, y0), (x, y1)], w=5.0) +
            c.out([(x - 13, y1 - 18), (x, y1), (x + 13, y1 - 18)], w=5.0))


def right_arrow(c, x0, x1, y):
    return (c.out([(x0, y), (x1, y)], w=5.2) +
            c.out([(x1 - 20, y - 16), (x1, y), (x1 - 20, y + 16)], w=5.2))


def leader(c, x0, y0, x1, y1):
    """A label's line, with a head on it, so it points rather than just
    reaches. Set in the label grey and thinner than the flow arrows, which
    carry the sequence and stay black."""
    ang = math.atan2(y1 - y0, x1 - x0)
    h, spread = 13, 0.46
    a = (x1 - h * math.cos(ang - spread), y1 - h * math.sin(ang - spread))
    b = (x1 - h * math.cos(ang + spread), y1 - h * math.sin(ang + spread))
    return (c.out([(x0, y0), (x1, y1)], w=3.4, colour=LABEL) +
            c.out([a, (x1, y1), b], w=3.4, colour=LABEL))


def draw_build(c, cx, top):
    """The 7 genes, the host they go into, and what comes out."""
    o = []
    bw, gap = 32, 6
    x0 = cx - (7 * bw + 6 * gap) / 2
    for k in range(7):
        x = x0 + k * (bw + gap)
        o.append(c.out([(x, top), (x + bw, top), (x + bw, top + 40),
                        (x, top + 40)], close=True, w=4.0,
                       fill=NITROBE_GREEN if k == 1 else "#d7ddd8"))
    o.append(text(cx, top - 16, "the 7 nos genes", 27, GREY))
    o.append(text(x0 + bw * 1.5 + gap, top + 68, "nosZ", 23, DOODLE))
    o.append(down_arrow(c, cx, top + 86, top + 134))
    o.append(microbe(cx, top + 186, 3.1, HOST_GREY, face=False))
    o.append(text(cx, top + 248, "E109, the host", 28, LABEL))
    o.append(text(cx, top + 282, "wins the race, has no genes", 24, GREY))
    o.append(down_arrow(c, cx, top + 306, top + 354))
    o.append(microbe(cx, top + 410, 3.1))
    o.append(text(cx, top + 472, "NitRobe", 30, LABEL))
    return "".join(o)


def draw_pair(c, cx, top, bot):
    """The 2 strains, in the same vial experiment 1 uses."""
    o = []
    for k, (gas, colour, face, name) in enumerate((
            (True, HOST_GREY, False, "E109, the host"),
            (False, NITROBE_GREEN, True, "NitRobe"))):
        x = cx - 84 + k * 168
        o.append(vial(c, x, top, bot, BROTH, gas=gas, strain=(colour, face)))
        o.append(text(x, bot + 36, name, 26, LABEL))
    o.append(text(cx - 84, top - 44, n2o(23) + " still there", 23, MARK))
    o.append(text(cx + 84, top - 44, n2o(23) + " gone", 23, GREY))
    return "".join(o)


def exp_2():
    """Built once, then tested twice. Drawn as the 3 things that happen."""
    c = Crayon(31)
    H = 706
    W2 = W / 2
    # No title. The 3 headings below say what happens, in order, and a line
    # over the top of them only repeated it.
    o = [wash_defs()]
    xs = (W * 0.17, W * 0.5, W * 0.79)
    heads = (("1. Build it", "weeks 1 to 6"),
             ("2. Does it destroy " + n2o(32) + "?", "week 7"),
             ("3. Does it still win the race?", "weeks 8 to 15"))
    for (name, when), x in zip(heads, xs):
        o.append(text(x, 76, name, 32, DOODLE))
        # Pinned below the lowest thing in any column, not to the
        # bottom of the canvas, so trimming the canvas cannot pull
        # the dates up into the drawing.
        o.append(text(x, 662, when, 27, MARK))
    o.append(draw_build(c, xs[0], 140))
    o.append(draw_pair(c, xs[1], 240, 500))
    o.append(draw_pot(c, xs[2], 270, 520,
                      dict(plant=130, nodules=5,
                           inside=[NITROBE_GREEN, HOST_GREY, HOST_GREY,
                                   NITROBE_GREEN, NITROBE_GREEN]), 400))
    # Name the 2 kinds of nodule, because that is the whole result. Both
    # labels sit to the right of the pot, and each line stops well short of
    # its words: a line touching the lettering reads as a strike-through.
    o.append(leader(c, xs[2] + 138, 314, xs[2] + 46, 322))
    o.append(text(xs[2] + 206, 318, "NitRobe", 25, LABEL))
    # 2 short lines. 3 looked cramped, and a single long one would have
    # pushed its own leader down to a stub to keep clear of the lettering.
    o.append(leader(c, xs[2] + 122, 394, xs[2] + 48, 386))
    o.append(text(xs[2] + 208, 394, "the soil\u2019s own", 24, LABEL))
    o.append(text(xs[2] + 208, 424, "bacteria", 24, LABEL))
    o.append(text(xs[2], 580, "every nodule opened, and the", 24, GREY))
    o.append(text(xs[2], 612, "strain inside it identified", 24, GREY))
    for x in (xs[0], xs[1]):
        o.append(right_arrow(c, x + 212, x + 286, 380))
    return W, H, "\n".join(o)


SCENES = {"exp-1": exp_1, "exp-2": exp_2}


# 48 tones is plenty for a shelf of vials. Experiment 2 has the creature in 2
# colours, soil, leaves, nodules, gold gas and blue medium in 1 picture, and at
# 48 the white inside a vial was being merged into a grey, which turned the
# gold sitting on it muddy.
COLOURS = {"exp-2": 160}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for key, scene in SCENES.items():
        render(f"{key}.png", scene, OUT, width=1400,
               colors=COLOURS.get(key, 48))


if __name__ == "__main__":
    main()
