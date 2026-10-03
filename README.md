# NitRobe

A genetically engineered soil microbe designed to destroy nitrous oxide, a powerful greenhouse gas.
3M Young Scientist Challenge 2027 · Made by Saanvi Pagadala

## → [saanvipagadala.github.io/NitRobe](https://saanvipagadala.github.io/NitRobe)

The whole project is written up there. **Start there.**

## The problem

Nitrous oxide is the 3rd worst greenhouse gas and the biggest destroyer of the
ozone layer. 70% of it comes off farm soil, released by bacteria eating the
fertilizer a crop leaves behind. Exactly 1 enzyme on Earth destroys it, built
by a set of 7 genes called *nos*.

Here is the part that makes this fixable. Legumes are not given chemical
fertilizer. They are given live bacteria, sold in a bag and coated onto the
seed, across tens of millions of hectares every spring, and a person chooses
which strain goes in each bag. **The strains they choose mostly cannot make
that enzyme.** Soybeans given 1 strain released 18 times more nitrous oxide
than soybeans given another.

## The idea

For 13 years, every published attempt has started with a strain that already
destroys N₂O and tried to make it competitive enough to survive a real
field. None has become a product, because the added strain loses the race into
the roots to the bacteria already living in the soil.

**NitRobe turns the problem around. Do not make the good strain competitive.
Make the competitive strain good.** The strain that already wins the race is
handed the set of genes it is missing.

**[The full argument →](https://saanvipagadala.github.io/NitRobe/end-to-end.html)**

## What was actually computed

| | What was done | What came of it |
|---|---|---|
| **Read** | A search over 40 whole genomes, reading the DNA itself rather than the labels on it | 13 species carry *nosZ*. 10 are not on any published list |
| **Checked** | The model against strains whose answer is already published | 3 of 3 agreed |
| **Simulated** | The modified bacterium in 8 metabolic situations | Faster in 7, never slower |
| **Designed** | The gene set itself, with accessions, from a genome anyone can download | A construct, not a sketch |

## The experiments

Nothing has been built, grown or measured. **That is the honest state of the
project**, and it is why the next step is bench work rather than more code.

2 experiments are written up as run sheets a laboratory could follow. The
first tests whether a bacterium that already exists destroys the gas. Only if
it does not does the second one build anything. Each carries blank data sheets,
a codebook defining every column, and dry runs where invented numbers,
including numbers where the experiment fails, are pushed through the analysis
to check it tells the truth before there is any truth to tell.

**[Both, in one place →](https://saanvipagadala.github.io/NitRobe/experiments/)**

## Why it could work

**The delivery system already exists.** Legume inoculant is a product farmers
already buy and already coat onto seed, across tens of millions of hectares
every spring. A better strain needs no new equipment, no new practice and
nothing asked of a farmer. It goes in the same bag.

**The hard half is already solved.** The strain being modified is the one that
already wins the race into the roots. Losing that race is what has beaten
every previous attempt for 13 years. NitRobe inherits a winner instead of
trying to build one.

**The genes pay their own way.** Destroying nitrous oxide is respiration, and
the last step of the chain releases more energy than breathing air does. The
metabolic simulation had the modified bacterium faster in 7 of 8 situations
and never slower. A gene set that earns its keep is one a bacterium has no reason to
throw away.

**The first answer is 3 weeks away.** A single vial experiment says whether
any of the shortlisted species destroys the gas. If one does, there is a
candidate to hand the genes to. If none does, the shortlist is empty, and an empty
shortlist is exactly what justifies building something new.
