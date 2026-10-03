"""
The pen that cannot draw straight, vendored from outreach/build/draw_by_hand.py.

The submission is meant to travel on its own, so the drawing core lives here
rather than being imported across the repository. Only the pen is copied. Every
scene in diagrams.py is this project's own.

Why hand-drawn at all: everything else in this submission is set by machine and
looks it. A diagram of an experiment is an argument about which group proves
what, and drawn by hand the eye can see which pot has the thing in it and which
one has had it taken away. It also says who made this before a word is read.

PNG and not SVG, unlike the charts: an SVG loaded through <img> cannot reach a
font, so the handwriting would have to be embedded letter by letter. Rendering
through Chrome bakes the letters into pixels and the problem disappears. The
background is left transparent, so a figure takes the colour of the page it is
set on rather than showing as a pale block.

The wobble is seeded, so the same drawing comes out of every build.
"""
import math
import random
import subprocess
import tempfile
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
INK = "#3b3230"
PENCIL = "#6b5f59"
HAND = "'Bradley Hand', 'Noteworthy', 'Chalkboard SE', cursive"


class Pen:
    """A pen that cannot draw straight, and misses the line when colouring.

    Two passes over every stroke, each wobbling differently, is what makes a
    line look drawn rather than plotted. Fills are offset a little from their
    outline for the same reason: a child colours past the edge, and a fill
    that lands exactly inside its outline reads as a computer's work.
    """

    def __init__(self, seed=11):
        self.r = random.Random(seed)

    def bow(self, x0, y0, x1, y1, amt=2.4):
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy) or 1
        nx, ny = -dy / length, dx / length
        k = self.r.uniform(-amt, amt)
        return f"Q {mx + nx * k:.1f} {my + ny * k:.1f} {x1:.1f} {y1:.1f}"

    def through(self, pts, close=False, amt=2.4, jit=1.6):
        p = [(x + self.r.uniform(-jit, jit), y + self.r.uniform(-jit, jit))
             for x, y in pts]
        d = f"M {p[0][0]:.1f} {p[0][1]:.1f}"
        for i in range(1, len(p)):
            d += " " + self.bow(*p[i - 1], *p[i], amt)
        if close:
            d += " " + self.bow(*p[-1], *p[0], amt) + " Z"
        return d

    def stroke(self, pts, close=False, colour=INK, w=2.6, passes=2, amt=2.4,
               jit=1.6, opacity=1.0):
        out = []
        for i in range(passes):
            out.append(f'<path d="{self.through(pts, close, amt, jit)}" '
                       f'fill="none" stroke="{colour}" '
                       f'stroke-width="{w - i * 0.5:.2f}" stroke-linecap="round" '
                       f'stroke-linejoin="round" '
                       f'opacity="{opacity * (1 if i == 0 else 0.5):.2f}"/>')
        return "".join(out)

    def fill(self, pts, colour, opacity=1.0, off=2.2):
        dx, dy = self.r.uniform(-off, off), self.r.uniform(-off, off)
        shifted = [(x + dx, y + dy) for x, y in pts]
        return (f'<path d="{self.through(shifted, True, 3.0, 2.0)}" '
                f'fill="{colour}" opacity="{opacity}" stroke="none"/>')

    def blob(self, cx, cy, rx, ry, n=13, wobble=0.1):
        return [(cx + rx * (1 + self.r.uniform(-wobble, wobble))
                 * math.cos(2 * math.pi * i / n),
                 cy + ry * (1 + self.r.uniform(-wobble, wobble))
                 * math.sin(2 * math.pi * i / n)) for i in range(n)]

    def scribble(self, x0, y0, x1, y1, rows, colour, w=2.0, opacity=0.5):
        """Colouring in the way a child does it: back and forth, not solid."""
        out = []
        for i in range(rows):
            y = y0 + (y1 - y0) * (i + 0.5) / rows
            pts = [(x0, y), ((x0 + x1) / 2, y + self.r.uniform(-3, 3)), (x1, y)]
            out.append(self.stroke(pts, colour=colour, w=w, passes=1, amt=2.0,
                                   jit=1.4, opacity=opacity))
        return "".join(out)


def text(x, y, s, size, colour=INK, anchor="middle", rot=0, family=HAND,
         ink=0.0, spacing=0.0):
    """Lettering, optionally with more ink in it.

    `ink` strokes the glyphs in their own colour. A script face set large is
    hard to read because its strokes stay hairline while its loops grow, and
    the usual answer -- a bolder face -- means giving up the letterforms.
    Stroking keeps the hand and only thickens it.
    """
    t = f' transform="rotate({rot} {x} {y})"' if rot else ""
    k = (f' stroke="{colour}" stroke-width="{ink}" stroke-linejoin="round"'
         if ink else "")
    sp = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'fill="{colour}" text-anchor="{anchor}"{k}{sp}{t}>{s}</text>')


def render(name, scene, folder, scale=2, width=1600, colors=48):
    """SVG through Chrome to PNG, so the handwriting arrives as pixels."""
    W, H, body = scene()
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
           f'width="{W * scale}" height="{H * scale}">{body}</svg>')
    out = Path(folder) / name
    if not Path(CHROME).exists():
        print(f"  (no Chrome; keeping the existing {name})")
        return
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "p.html"
        page.write_text(
            f'<body style="margin:0">{svg}</body>', encoding="utf-8")
        subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
             "--default-background-color=00000000",
             f"--window-size={W * scale},{H * scale}",
             "--virtual-time-budget=4000",
             f"--screenshot={Path(tmp) / 'o.png'}", f"file://{page}"],
            check=True, capture_output=True)
        from PIL import Image
        # Kept transparent rather than flattened onto white: the figure then
        # takes the colour of whatever it is set on, which is warm off-white
        # on the site and white on paper. Flattening shows as a pale block on
        # one of the two.
        img = Image.open(Path(tmp) / "o.png").convert("RGBA")
        if img.width > width:
            img = img.resize((width, round(img.height * width / img.width)),
                             Image.LANCZOS)
        # Line and flat wash is a few dozen tones, so a small palette is
        # indistinguishable and an order of magnitude smaller. FASTOCTREE
        # rather than the default, because it is the one that keeps alpha.
        #
        # Raise `colors` for a drawing with coloured lettering in it. A letter
        # is thin, so most of its pixels are part way between the ink and the
        # paper, and 48 tones is not enough to hold that gradient: the strokes
        # come out speckled.
        img.quantize(colors=colors, method=Image.FASTOCTREE).save(out,
                                                             optimize=True)
    print(f"  {name:<20} {out.stat().st_size:>8,} bytes  ({img.width}px wide)")

DOODLE = "#1c1c1c"
MARK = "#b3401f"        # the site's accent, for the group being tested


# Watercolour, faked with two SVG filters.
#
# Paint does two things a flat fill does not: its edge wanders away from the
# line it was meant to follow, and it pools darker where it dries. Fractal
# noise pushed through feDisplacementMap gives the first; laying the same
# shape down twice, translucent, gives the second where the two overlap.
#
# Several filters with different seeds, because one filter used everywhere
# gives every wash on the page an identical wobble, which reads as a texture
# rather than as paint.
WASHES = [
    # Martian dirt is rust; Earth soil is brown and much darker. Letting the
    # two read as different colours is half the point of colouring these at
    # all -- cup 5 is meant to look like the richest thing on the shelf.
    ("#c58a5e", 0.32),      # simulant, rusty
    ("#63482f", 0.52),      # potting soil, dark and dense
    ("#7ea15f", 0.42),      # leaves
    # Both of these sit on top of the tan dirt, so they have to be far
    # enough from it in hue to be seen at all -- pinker, and browner.
    ("#dd8272", 0.52),      # worms
    ("#8f6642", 0.50),      # castings
    ("#e0aa3c", 0.55),      # MarsWorm, the gold of the project's own mark
]


def wash_defs(n=6, scale=13):
    out = ['<defs>']
    for i in range(n):
        out.append(
            f'<filter id="wc{i}" x="-25%" y="-25%" width="150%" height="150%">'
            f'<feTurbulence type="fractalNoise" baseFrequency="0.019" '
            f'numOctaves="4" seed="{i * 7 + 3}" result="n"/>'
            f'<feDisplacementMap in="SourceGraphic" in2="n" '
            f'scale="{scale}" xChannelSelector="R" yChannelSelector="G"/>'
            f'</filter>')
    out.append('</defs>')
    return "".join(out)


class Crayon(Pen):
    """Flat black outline, white fill, rounded ends. Nothing else."""

    def out(self, pts, close=False, w=5.0, fill="none", jit=1.1, amt=1.6,
            colour=DOODLE):
        d = self.through(pts, close, amt, jit)
        return (f'<path d="{d}" fill="{fill}" stroke="{colour}" '
                f'stroke-width="{w}" stroke-linecap="round" '
                f'stroke-linejoin="round"/>')

    def paint(self, pts, colour, opacity=0.32, close=True, inner=True):
        """Lay a wash under the line work.

        Two passes: the whole shape, then a smaller one inside it. Where they
        overlap the colour doubles, which is what a pool of dried paint does
        and what stops the fill looking like a fill.
        """
        f = self.r.randrange(6)
        d = self.through(pts, close, 2.4, 1.6)
        out = [f'<g filter="url(#wc{f})">'
               f'<path d="{d}" fill="{colour}" opacity="{opacity}"/></g>']
        if inner:
            cx = sum(x for x, _ in pts) / len(pts)
            cy = sum(y for _, y in pts) / len(pts)
            small = [(cx + (x - cx) * 0.78, cy + (y - cy) * 0.72)
                     for x, y in pts]
            f2 = self.r.randrange(6)
            d2 = self.through(small, close, 2.4, 1.6)
            out.append(f'<g filter="url(#wc{f2})">'
                       f'<path d="{d2}" fill="{colour}" '
                       f'opacity="{opacity * 0.55:.2f}"/></g>')
        return "".join(out)

    def paint_along(self, d, colour, opacity=0.4, w=18):
        """A wash laid along a line, for things that are longer than wide."""
        f = self.r.randrange(6)
        return (f'<g filter="url(#wc{f})">'
                f'<path d="{d}" fill="none" stroke="{colour}" '
                f'stroke-width="{w}" stroke-linecap="round" '
                f'opacity="{opacity}"/></g>')

    def microbe(self, cx, cy, r=10, rot=0, w=3.4, colour=DOODLE):
        """MarsWorm itself: a round cell with two feelers and two eyes.

        The project's own mark is a blob with feelers, so the microbe in
        these cups is drawn as the same creature rather than as a generic
        dot. It is the only thing on the shelf that is alive and engineered,
        and it should be recognisable as the thing the project is named for.
        """
        body = self.blob(cx, cy, r, r * 0.86, 13, 0.07)
        d = self.through(body, True, 1.0, 0.6)
        g = f'<g transform="rotate({rot} {cx} {cy})">'
        out = [g, f'<path d="{d}" fill="none" stroke="{colour}" '
                  f'stroke-width="{w}" stroke-linejoin="round"/>']
        for sx in (-1, 1):
            out.append(f'<path d="M {cx + sx * r * 0.5:.1f} {cy - r * 0.8:.1f} '
                       f'q {sx * 4:.1f} -{r * 0.7:.1f} {sx * 9:.1f} '
                       f'-{r * 0.5:.1f}" fill="none" stroke="{colour}" '
                       f'stroke-width="{w * 0.8:.1f}" stroke-linecap="round"/>')
            out.append(f'<circle cx="{cx + sx * r * 0.32:.1f}" '
                       f'cy="{cy - r * 0.1:.1f}" r="{w * 0.55:.1f}" '
                       f'fill="{colour}"/>')
        return "".join(out) + "</g>"

    def dish(self, cx, cy, R=54, depth=17, wash=None, opacity=0.4, w=5.0,
             open_ratio=0.64):
        """A petri dish seen from just above, with no lid on it.

        Drawn with true ellipses and one arc rather than with the wobbling
        many-sided blobs used elsewhere. A long straight line can afford to
        wander and still look drawn; a curve built out of twenty short
        segments just looks unsteady. The character here comes from the tilt
        and the weight of the line, not from the line shaking.

        Shallow, and tipped well towards the reader: the dish is there to
        show what is living inside it, so the opening gets the room and the
        wall gets almost none.
        """
        ry = R * open_ratio
        out = []
        wall = (f"M {cx - R:.1f} {cy:.1f} L {cx - R:.1f} {cy + depth:.1f} "
                f"A {R:.1f} {ry:.1f} 0 0 0 {cx + R:.1f} {cy + depth:.1f} "
                f"L {cx + R:.1f} {cy:.1f}")
        if wash:
            f = self.r.randrange(6)
            out.append(f'<g filter="url(#wc{f})">'
                       f'<path d="{wall} A {R:.1f} {ry:.1f} 0 0 1 '
                       f'{cx - R:.1f} {cy:.1f} Z" fill="{wash}" '
                       f'opacity="{opacity * 0.75:.2f}"/></g>')
            f = self.r.randrange(6)
            out.append(f'<g filter="url(#wc{f})"><ellipse cx="{cx:.1f}" '
                       f'cy="{cy:.1f}" rx="{R - 5:.1f}" ry="{ry - 5:.1f}" '
                       f'fill="{wash}" opacity="{opacity}"/></g>')
        out.append(f'<path d="{wall}" fill="none" stroke="{DOODLE}" '
                   f'stroke-width="{w}" stroke-linecap="round"/>')
        out.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{R:.1f}" '
                   f'ry="{ry:.1f}" fill="none" stroke="{DOODLE}" '
                   f'stroke-width="{w}"/>')
        out.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{R - 7:.1f}" '
                   f'ry="{ry - 6:.1f}" fill="none" stroke="{DOODLE}" '
                   f'stroke-width="{w * 0.45:.1f}"/>')
        return "".join(out)

    def worm_outline(self, x, y, length, amp=8, waves=1.5, r=8.0,
                     taper=0.45, n=44):
        """The worm as a closed outline, rather than as a fat black line.

        Everything else in these cups is drawn as an empty shape with paint
        laid inside it -- a leaf, a casting, a grain. A worm drawn as a thick
        stroke is the odd one out, and cannot be coloured the same way. So
        the wriggle is walked with its normal, offset either side, and the
        two edges joined into one shape. It tapers from head to tail, which
        is what makes it read as an animal rather than a tube.
        """
        top, bot = [], []
        for i in range(n + 1):
            t = i / n
            px = x + length * t
            py = y + amp * math.sin(2 * math.pi * waves * t)
            dx = length
            dy = amp * 2 * math.pi * waves * math.cos(2 * math.pi * waves * t)
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            rr = r * (1 - taper * t)
            top.append((px + nx * rr, py + ny * rr))
            bot.append((px - nx * rr, py - ny * rr))

        # a rounded head, so the blunt end is the tail
        head = []
        for k in range(1, 8):
            a = math.pi * k / 8
            head.append((x - r * math.sin(a), y - r * math.cos(a)))

        pts = [bot[0]] + head + top
        d = "M %.1f %.1f " % pts[0]
        d += " ".join("L %.1f %.1f" % q for q in pts[1:])
        d += " " + " ".join("L %.1f %.1f" % q for q in reversed(bot[1:]))
        return d + " Z"

    def worm_path(self, x, y, length, hump=9, waves=2.5):
        """The wriggle itself, so the paint and the line can share it."""
        step = length / waves
        d = f"M {x:.1f} {y:.1f}"
        for i in range(int(math.ceil(waves))):
            x0 = x + step * i
            up = -hump if i % 2 == 0 else hump
            d += (f" Q {x0 + step * 0.25:.1f} {y + up:.1f} "
                  f"{x0 + step * 0.5:.1f} {y:.1f}"
                  f" Q {x0 + step * 0.75:.1f} {y - up:.1f} "
                  f"{x0 + step:.1f} {y:.1f}")
        return d

    def round_blob(self, cx, cy, rx, ry, w=5.0, fill="#ffffff", n=15):
        return self.out(self.blob(cx, cy, rx, ry, n, 0.045), close=True, w=w,
                        fill=fill, jit=0.9, amt=1.3)

    def worm(self, x, y, length, hump=9, waves=2.5, w=6.0, rot=0):
        """A worm, with a head on it.

        Three bare squiggles side by side read as water. A rounded head at
        one end, and a different angle for each, and they read as animals.
        """
        return (f'<g transform="rotate({rot} {x} {y})">'
                + self.squiggle(x, y, length, hump, waves, w)
                + f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{w * 0.85:.1f}" '
                f'fill="{DOODLE}"/></g>')

    def squiggle(self, x, y, length, hump=10, waves=3, w=5.0):
        """Drawn as curves, because a polyline reads as a zigzag."""
        return (f'<path d="{self.worm_path(x, y, length, hump, waves)}" '
                f'fill="none" stroke="{DOODLE}" stroke-width="{w}" '
                f'stroke-linecap="round"/>')

    def leaf(self, cx, cy, r=15, rot=0, w=4.0, fill="#ffffff"):
        """Two arcs meeting at a point at each end, and a midrib."""
        d = (f"M {cx - r:.1f} {cy:.1f} Q {cx:.1f} {cy - r * 0.78:.1f} "
             f"{cx + r:.1f} {cy:.1f} Q {cx:.1f} {cy + r * 0.78:.1f} "
             f"{cx - r:.1f} {cy:.1f} Z")
        rib = (f"M {cx - r * 0.72:.1f} {cy:.1f} L {cx + r * 0.72:.1f} {cy:.1f}")
        g = f'<g transform="rotate({rot} {cx} {cy})">'
        return (g + f'<path d="{d}" fill="{fill}" stroke="{DOODLE}" '
                f'stroke-width="{w}" stroke-linejoin="round"/>'
                f'<path d="{rib}" fill="none" stroke="{DOODLE}" '
                f'stroke-width="{w * 0.7:.1f}" stroke-linecap="round"/></g>')


