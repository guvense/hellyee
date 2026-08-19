---
name: arrangement-transitions
description: How to build section transitions in an Ableton arrangement with hellyee — risers, gasps, fills, impacts, downlifters, filter blends — and which of these each genre actually uses (techno blends vs trance drama vs trap rolls vs dnb switch-ups). Use whenever the user asks about transitions, builds, drops not hitting, sections feeling disconnected, "geçişler", "patlamıyor", "akmıyor", fills, risers, or how to move between intro/build/drop/breakdown/outro — and when laying out any new arrangement's section boundaries.
---

# Arrangement & Transitions

A transition is energy management: what leaves, what enters, and what bridges
the boundary. hellyee builds these from session clips placed with
`place_in_arrangement`, empty "gap" clips that trim whatever they overlap,
and `automate_clip` envelopes that travel with the clip.

## The universal toolkit (with hellyee recipes)

| Device | Recipe | Effect |
|---|---|---|
| **Riser** | Load a riser preset (search "Riser" in sounds), hold one note 4–8 bars into the boundary | Tension rising |
| **Filter sweep** | Clip variant whose `Filter 1 Freq` automation climbs to 90–100% at the boundary | The lead/pad itself becomes the riser |
| **Roll (crescendo)** | Shaker/hat 16ths → 32nds with velocity ramping 40→127 over last 2 bars | Acceleration |
| **Kick roll** | Last 2 bars: 8ths → 16ths, velocity climbing | Heartbeat panic before a drop |
| **Gasp** | Empty gap clips over ALL tracks for the final 1–2 beats — including arps and sustained layers | The silence that makes the hit land |
| **Impact** | Crash + kick (velocity 115+) exactly on the downbeat of the new section | The exclamation mark |
| **Sub drop** | 1-bar clip, low note (A1), `Transpose` automation 0→−24 over ~3.5 beats | Floor falls away |
| **Melodic pre-cut** | Gap clips on pads/leads 1–2 bars before drums cut | Staged exit reads as intent, not error |
| **Downlifter** | Riser clip placed *after* the boundary, or reverse-shaped automation | Settling into a new section |

**The single most measurable rule: a drop only hits if the moment before it is
smaller.** Verify with the master meter: the gasp's floor should sit ≥0.15
below the build's peak, and the drop's peak above the build's peak. If build ≥
drop, the section will not land no matter what FX you stack — remove energy
from the build instead of adding to the drop.

**Watch for hole-fillers.** Any continuously-sounding layer (arps, sustained
pads with long release, 16th percussion) will fill your gasp unless it gets
its own gap clip. If a measured gasp barely dips, list every track and check
which one kept playing.

## Per-genre transition conventions

**Techno** — no drama. Sections *blend* over 8–16 bars: layers enter/exit one
at a time, filters open gradually, the kick almost never stops. Instead of a
gasp, drop the kick for exactly 1 bar then return it. A single closed-hat
entering can *be* the transition. Reserve the full riser+impact kit for one
moment in the whole track, if at all.

**House** — light touch: a filter sweep on the chord loop, an open-hat lift
in the last bar, a 1-beat drum cut before the new 8-bar phrase. A short snare
fill (4 hits, beats 3–4 of the last bar) is idiomatic; full trance risers are
not. Transitions land every 8 or 16 bars, on the loop grid.

**Trance / uplifting** — the full toolkit, staged: melodic pre-cut (2 bars) →
8-bar riser + kick roll + shaker crescendo → full gasp (1–2 beats) → impact +
sub drop → everything returns at once. Breakdown entry is the reverse: cut all
drums at once on a downbeat, leave pad+lead ringing. Second drop should add a
layer the first didn't have.

**Melodic techno** — trance's staging but stretched and subtler: 16-bar filter
climbs, no impacts, the arp never stops (it is the thread listeners follow —
give it a gap only at THE one drop).

**Drum & bass** — switch-ups: change the drum pattern every 16 bars (edit the
last 2 bars into a fill — displaced snares, doubled kicks). Bass swells into
boundaries via filter automation. Drops are announced by 1 bar of drums-only
or a vocal/FX stab, not long risers.

**Trap** — hat rolls are the transition: 16ths burst into 32nds/triplet rolls
in the last bar, often with a pitch-rising 808 or a riser. A full-bar silence
before the drop is idiomatic and hits hard. Impacts on the drop downbeat, and
the 808 gliding into its first note.

**Ambient** — no fills, no impacts. Transitions are crossfades: one pad's
volume/filter automation falls over 8–16 bars while the next rises under it.
Section boundaries should be inaudible as events.

## Section length norms

| Genre | Phrase unit | Intro | Build | Breakdown |
|---|---|---|---|---|
| Techno | 16/32 bars | 16–32 (drums only, DJ-friendly) | plateaus, not builds | 16–32 mid-track |
| House | 8/16 | 8–16 | 8 | 8–16 |
| Trance | 8/16/32 | 8–16 | 8–16 + 8 riser | 16–32, emotional core |
| DnB | 16 | 8–16 | 8 | 16 |
| Trap | 4/8 | 4–8 | 4 | 8 |

Always verify the finished arc by measurement: play each section, read the
master meter, and confirm the energy staircase you intended actually exists.
