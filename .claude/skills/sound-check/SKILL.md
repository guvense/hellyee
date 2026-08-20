---
name: sound-check
description: Pre-flight verification that every track in an Ableton set actually produces sound, before an arrangement is built on top of it — drum pad coverage, per-track metering, and the decision tree for a track that reads silent. Use right after loading instruments and writing the first clips, before placing arrangement clips; and whenever something is missing, thin, inaudible, or a band reads near zero — "hat'ler duyulmuyor", "bir şey eksik", "neden ses gelmiyor", "why is this silent", "the highs are gone".
---

# Sound check

Everything in Live fails loudly except silence. A wrong note errors, a bad
index errors, a missing file errors — but a track that makes *no sound* reports
nothing at all. It writes clean, it places clean, it renders clean, and the only
trace is a band that reads 0.0% in an analysis you might not run until the
arrangement is finished.

So check before you build. Thirty seconds here saves rebuilding an arrangement.

## When

- After loading instruments and writing the first session clips — **before**
  `place_in_arrangement`.
- After loading any drum rack, always.
- Whenever the user says something is missing, thin, or inaudible.
- Whenever a `record_master` band reads near zero where you expected content.

## The check

**1. Drum racks: read the pads, don't trust the map.**

`get_drum_map` returns Live's *standard* mapping. `get_drum_pads(track, device)`
returns what the loaded rack actually fills. They are not the same — factory
kits routinely cover only 36–51, so the shaker at 70 is silence. Write only
notes the rack lists; if you want 16th shakers and there is no shaker pad, use
the closed hat at low velocity instead.

**2. One measured pass over every track.**

Fire nothing. Place a few bars, then:

```
measure_tracks(track_indices=[0,1,2,…], start_bar=<a bar where all of them play>, seconds=15)
```

One playback pass, ranked by peak, `silent` flagged under 0.02. Pass
`start_bar` — without it you measure wherever the playhead sits, and a playhead
parked outside the section reads 0.000 on *every* track, which looks exactly
like a broken set.

**3. Read the ranking as a mix, not just a checklist.**

For four-on-the-floor: kick on top, bass under it, lead below that, then
percussion, then pads. If the ranking is upside down you have found a mix
problem before writing 176 bars over it.

## A track reads silent — the decision tree

Never raise the fader first. Work down this list:

| check | how | fix |
|---|---|---|
| Is there an instrument? | `list_track_devices` | MIDI track with only effects makes no sound |
| Is it a drum note that exists? | `get_drum_pads` | rewrite the pattern onto filled pads |
| Was a session clip ever fired? | — | `back_to_arranger` |
| Is the track muted, or another soloed? | `get_song_status` | unmute |
| Does the section actually contain the clip? | `get_arrangement_clips` | you measured the wrong bar |
| Is the filter shut? | `list_device_parameters` | see the cutoff floors in the hellyee skill |
| Genuinely quiet, not silent? | solo + `record_master` 4 bars | now a level problem — see below |

That last row is the one worth doing properly: solo the track, record four bars,
and read `peak` and the band split. A closed hat at peak 0.046 (−27 dBFS) is
audible in isolation and invisible in a mix; peak around 0.15–0.25 is where it
starts to sit. Raise the device chain (an EQ's `Output Gain`) as well as the
fader, and raise the note velocities — a rack pad quiet at velocity 70 has room
at 110.

## After any session-clip edit

Fixing a session clip does not fix the copies already in the arrangement, and
nothing warns you. Call `refresh_arrangement_track(track_index)` — it rebuilds
that track's placements from the current session clips, keeping the layout.

Then re-measure. A fix you did not measure is a fix you are guessing about.

## Say what you checked

Report the measurement, not the intention: "hats now peak 0.19 at bar 32, high
band 4.1%" beats "fixed the hats". The user cannot see your meters and you
cannot hear their speakers; the numbers are the only shared ground.
