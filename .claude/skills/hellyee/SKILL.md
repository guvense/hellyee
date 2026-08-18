---
name: hellyee
description: Making music in Ableton Live through the hellyee MCP server — creating tracks, writing MIDI, designing sounds on Live devices, automating parameters, building arrangements, and mixing by measurement. Use whenever the user asks to make, change, arrange, mix or master anything in Ableton, or when hellyee's tools are connected and something is not behaving as expected.
---

# Making music in Ableton with hellyee

You cannot hear the result. You can read the set's state, read real output
meters, and read every parameter's value in its displayed unit. Build from
those, and say plainly which judgements are measured and which are convention.

## Before you touch anything

Call `get_song_status` first, every time. It tells you the tempo, the track
indices and whether each is MIDI or audio. Never assume indices — the user
edits between your turns.

**Then check whether the set is already occupied.** Call
`get_arrangement_clips` on a few tracks. If they come back full, the user has a
project open and anything you add will play *on top of it*. Say so and ask
whether to build alongside it, mute it, or work in a new set. Silently layering
a second kick over someone's track is the most confusing failure mode there is.

If the set already has material, match its tempo and key rather than imposing
your own. Sample filenames often carry both (`..._150bpm...`, `..._Fm`).

## The five things that will silently break

**1. `back_to_arranger` — arrangement plays with no sound.** If a session clip
was ever fired on a track, that track ignores its arrangement clips forever
after. There is no error; it is simply silent. Send
`/live/song/set/back_to_arranger 0` before arrangement playback. If tracks read
0.000 on the meter while the playhead is clearly inside a clip, this is why.

**2. Starting playback resets the playhead.** `transport("start")` jumps to the
arrangement start and overrides any position you set beforehand. Start first,
*then* set the position.

**3. Automation overrides static parameter values.** Setting a filter to 80% and
then playing a clip whose automation says 30% gives you 30%. After changing a
device parameter, rewrite the automation that controls it or the change will not
survive playback.

**4. Delete from the highest index downwards.** Deleting track 13 shifts 14 to
13. Deleting `[13, 15]` in that order removes 13 and then whatever *moved into*
15 — not what you meant. Same for devices.

**5. Third-party plugins are opaque.** Serum, Vital and friends load and play,
but Live exposes a single parameter, `Device On`, until the user exposes more by
hand through Live's Configure button. Do sound design on Live's own devices —
Wavetable exposes 93 parameters, Operator and EQ Eight likewise. If the user
asks for a specific plugin, load it, tell them it is a black box to you, and
offer the Configure route.

## Sound design: percent, and the muffling trap

**Always set parameters with `percent`, never raw values.** Live's internal
scales are not the displayed unit — Auto Filter's `Frequency` runs 20–135 and
reads as "265 Hz"; Wavetable's runs 0–1. A number that looks like Hz will land
somewhere arbitrary. `set_device_parameter` reports back the displayed value;
read it to confirm what you actually did.

**The percent→Hz curve is exponential, and the bottom half is very dark.** On
Wavetable's filter, roughly: 40% ≈ 320 Hz · 50% ≈ 640 Hz · 66% ≈ 2 kHz ·
76% ≈ 4 kHz · 88% ≈ 9 kHz. Do not reason about "half open" as if it were half
the frequency.

This is the single most common way to ruin a track. Sounds need harmonics far
above their fundamental to be audible at all — a bass filtered at 400 Hz
disappears on any speaker without a subwoofer. Working minimums:

| | keep the cutoff above |
|---|---|
| Bass | ~1.5 kHz |
| Lead | ~4 kHz |
| Pad | ~1.5 kHz |
| Pluck / arp | ~3 kHz |

Darker than that is a deliberate effect (a filtered breakdown), not a default.
When the user says the track sounds muffled, read every filter's Hz value before
changing anything — the answer is usually right there.

**Make room instead of turning things up.** Everything sharing the low end makes
a mix muddy and the kick inaudible. High-pass pads, leads and plucks around
200–320 Hz; that region belongs to kick and bass. Give the kick its own EQ: a
high-pass under ~30 Hz, a small boost near 55 Hz for body, and a boost near
3 kHz for the click — the click is what makes a kick audible on laptop speakers.

**Unison above ~60% turns a lead into wash.** Wide detune plus heavy unison
reads as phasey and cheap. Around 40–50% with ±8 ct is present and solid.

## Automation

Live only creates envelopes on **session** clips and rejects them on arrangement
clips. So: write automation to the session clip with `automate_clip`, then
`place_in_arrangement` — the envelope travels with the clip.

To vary automation across a song, make several clip variants of the same notes
in different slots — dark for the breakdown, sweeping for the build, open for
the drop — and place the right slot in each section. That is how a filter sweep
across a build is actually built.

Points take `percent`, so the same reasoning as above applies. A sweep that ends
at 60% has not opened.

## Mixing by measurement

`measure_track_level` returns real meter data. Use it: measure, adjust the
fader, measure again. Do not guess at levels.

Three traps, all of which will give you confident nonsense:

- **A silent track reads 0.000.** Never treat that as "too quiet" and raise the
  fader — you will drive it to maximum. Skip any track under about 0.02.
- **Measure across a full loop.** The meter updates at roughly 10 Hz and a
  window shorter than the loop samples a random slice of it. An 8-bar loop at
  140 BPM needs about 14 seconds.
- **Wait after moving the playhead.** Meters decay slowly; measure immediately
  after a jump and you read the previous section's tail. Give it ~4 seconds.

Live's meter and fader share a scale where **0.85 = 0 dB**. It is not
dB-linear — do not convert it with `20·log10`.

A dance mix hierarchy that works: kick on top, bass just under it, lead below
that, then percussion, then pads and arps. State it as targets and converge.

## Building an arrangement

Write short session clips as building blocks — 4 bars for drums, 8 for
harmonic parts — then place them along the timeline with
`place_in_arrangement`. Do not write one 128-bar clip.

Time is in **beats**: one 4/4 bar is 4 beats, a 16th is 0.25. Pitches follow
Live's display, where **C3 = 60**.

**A drop only lands if the section before it is genuinely smaller.** Not just
quieter — thinner. Take the kick and bass out for the breakdown; their absence
is what makes the return feel enormous. Put a filter sweep across the last 8
bars, a percussion roll in the final 2, and an impact exactly on the downbeat.

Verify the result by playing each section and reading the meters. It is the only
way to catch a section that is silently empty.

## Mastering

Order on the master: EQ Eight → Glue Compressor → Limiter.

Leave headroom before the chain — trim all tracks proportionally so the master
peaks around 0.75 pre-chain, then bring it up with the limiter. Trimming
everything by the same amount preserves the balance you measured.

**Over-limiting destroys the arrangement.** If the breakdown and the drop
measure within ~0.10 of each other, the drop will not hit no matter how good the
arrangement is. Back the limiter off until they separate by 0.20 or more.

Check the master for an existing chain first. If the user already masters their
tracks, do not add a second limiter on top — say what is there and ask.

## When setup is the problem

Run `check_connection` first; it names the likely cause. Beyond that:

- Remote Scripts are scanned **only at startup** — Live must be restarted after
  installation, and AbletonOSC selected under Control Surface by hand. No API
  can do that step.
- Editing an already-loaded handler does not need a restart: send
  `/live/api/reload`. Adding a *new* handler module does.
- `hellyee doctor` reports which handlers are present and whether the optional
  audio dependencies are installed.
