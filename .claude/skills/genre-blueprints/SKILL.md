---
name: genre-blueprints
description: Genre-specific production blueprints for building tracks in Ableton Live with hellyee — concrete tempo, drum grid, bassline, harmony, arrangement-length and sidechain conventions per genre. Use whenever the user names a genre or a genre-coded request — techno, house, deep/tech house, trance, uplifting, melodic techno, drum and bass, dnb, trap, hip-hop, ambient, downtempo — e.g. "make a techno beat", "trance tarzında olsun", "trap hi-hat'leri ekle", "bir house parçası kur", or when starting any new track where the genre is stated or clearly implied.
---

# Genre Blueprints

Concrete starting conventions per genre. These are defaults, not laws — the
user's explicit instructions always win, and an existing track's tempo/key wins
over the table. Time is in beats (1 bar = 4 beats), pitches use Live's C3=60,
drum pitches come from `get_drum_map` (kick 36, snare 38, clap 39, closed hat
42, open hat 46, ride 51, shaker 70).

Shared technique for every four-on-the-floor genre below:
- **Kick/bass frequency split**: sub region (< ~95 Hz) belongs to one element
  at a time. High-pass every non-bass melodic track at 200–320 Hz. Give the
  kick a body boost near 50–60 Hz and a click boost near 3 kHz.
- **Sidechain/duck (API recipe)**: Live's compressor sidechain *routing* is
  not exposed to the API. Use Auto Pan on the bass instead: LFO Type=Beats,
  Sync Rate=1/4, Phase=0°, Waveform=SawDown, Invert=on, Shape≈30%. Amount is
  the genre knob — see per-genre values.
- **The drop only hits if the last bar before it thins out**: cut melodic
  content 1–2 bars early, everything for the final 1–2 beats (the gasp).

## Techno (125–135 BPM)

- **Kick**: every beat, velocity 112–120, relentless. The kick *is* the song.
- **Bass**: rumble — a sub layer (root, long or rolling) plus a gritty mid
  layer high-passed at ~95 Hz with drive. Duck Amount 60–70% (heavy pump is
  idiomatic). Often a single root note per 8–16 bars; movement comes from the
  filter, not the notes.
- **Harmony/melody**: minimal. One or two-note motifs, Phrygian or natural
  minor. Tension lives in filter/automation sweeps and added/removed layers,
  not in melodic development. A stab every 2–4 bars beats a melody.
- **Hats**: closed offbeats (0.5, 1.5, …) velocity ~70–85; 16th shakers low
  velocity for drive; open hat sparingly.
- **Arrangement**: phrases of 16/32 bars; DJ-friendly 16–32 bar intro (drums
  only) and outro; energy moves in plateaus, not one big drop. Breakdowns
  16–32 bars mid-track, filter-driven.
- **Feel**: velocities tight, quantize strength 0.9–1.0. Precision is the
  aesthetic.

## House (120–126 BPM)

- **Kick** 4/4 (~112), **clap/snare on 2 and 4**, open hat on every offbeat.
- **Bass**: groovy, syncopated, staccato (duration ≈ 0.4); velocity variation
  60–110 makes the groove. Duck Amount 45–55% (pump present, not seasick).
- **Harmony**: min7/maj7/9 chords — stab chords on offbeats or a 2–4 bar
  loop; Dorian brightness suits classic house. Piano and organ stabs are
  idiomatic (search browser "E-Piano", "Organ").
- **Arrangement**: 8-bar loops layered in/out in 8/16-bar sections; less
  breakdown-drama than trance — grooves rotate rather than explode.
- **Feel**: quantize strength 0.6–0.8, keep swing. Shaker/hat velocity
  humanization matters more here than anywhere.

## Trance / Uplifting (136–142 BPM)

- **Kick** 4/4 ~115–118; clap 2&4; offbeat open hats; 16th shaker crescendo
  rolls into transitions.
- **Bass**: rolling offbeat 8ths on chord roots (start at +0.5 each beat,
  duration ~0.4), octave pickup at bar ends. Duck Amount 50–60%.
- **Harmony**: 4-chord progressions 2 bars each (i–VI–III–VII family, e.g.
  Am–F–C–G); supersaw leads with unison 40–60% and detune ±8–20 ct; pads with
  slow attack; a pluck arp in 16ths.
- **Arrangement**: long-form — 16–32 bar builds, an emotional breakdown (drums
  out, piano/pad/lead only), an 8-bar riser with opening filter, the gasp,
  then the full drop. A minor→major rotation (Am–F–C–G → C–G–Am–F) for a
  hope-payoff second drop.
- **Feel**: quantize 0.9–1.0; anthem melodies accent bar-start notes
  (velocity 110+ vs 95).

## Melodic Techno (120–126 BPM)

Techno's grid with trance's harmony: 4/4 kick, heavy duck (60%+), dark minor
arps (16ths, narrow range, hypnotic), one evolving lead motif, very long
filter automations (16–32 bars). Fewer chords than trance — often one pedal
tone under a moving arp.

## Drum & Bass (170–176 BPM)

- **Drums**: kick on beat 1, snare on beat 3 (half-time feel at high speed);
  fast 16th hat work with shuffle; ghost snares (velocity 40–55) between.
- **Bass**: long sub notes (1–4 bars) or a Reese (two detuned saws — Wavetable
  Osc 2 detune 40–60%); movement from filter automation. No 1/4 duck — duck
  briefly on kick/snare or skip sidechain.
- **Harmony**: minor, sparse pads; melody minimal or atmospheric.
- **Arrangement**: 16-bar phrases, drop at 32 or 64; switch-ups every 16 bars.

## Trap / Hip-Hop (135–150 BPM, half-time feel)

- **Drums**: kick sparse and syncopated, snare/clap on beat 3; **hats are the
  lead instrument** — 16ths with bursts of 32nds (0.125 grid) and triplet
  rolls, velocity ramps 40→100.
- **808 bass**: kick and bass are one instrument — long 808 notes following a
  dark minor root line; glide between notes (Wavetable Glide > 0). No
  sidechain; carve 300–600 Hz instead.
- **Harmony/melody**: harmonic minor or Phrygian; sparse bell/pluck motifs
  (music box, kalimba presets read as "dark toy" — idiomatic); huge space.
- **Feel**: quantize hats 1.0; melodies can sit loose (0.6).

## Ambient / Downtempo (60–90 BPM or beatless)

- **No kick, or a soft sparse one.** Percussion optional and low-velocity.
- **Pads carry everything**: attack 40%+, release 60%+, Lydian or Ionian for
  light, Aeolian for melancholy; voice chords wide (10ths, open fifths).
- **Events are rare**: one note change per bar is plenty; automation moves on
  16–32 bar spans; generous reverb (wet 40–60%) everywhere.
- Master gently: skip the limiter push, keep peaks near 0.75 — loudness is
  the enemy of this genre.

## Cross-genre workflow with hellyee

1. `get_song_status` first; match existing tempo/key if the set is occupied.
2. Build session clips per the blueprint (drums 4 bars, harmonic parts 8),
   then place with `place_in_arrangement` using the genre's section lengths.
3. Wire the duck (Auto Pan recipe above) with the genre's Amount.
4. Balance by measurement: kick on top (four-on-the-floor genres), then bass,
   then lead; verify with `measure_track_level`.
5. For emotional shaping within the genre, defer to the `emotion-to-notes`
   skill — genre sets the grid, emotion sets the notes.
