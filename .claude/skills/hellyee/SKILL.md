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

## The eight things that will silently break

**1. `back_to_arranger` — arrangement plays with no sound.** If a session clip
was ever fired on a track, that track ignores its arrangement clips forever
after. There is no error; it is simply silent. Call `back_to_arranger` before
arrangement playback. If tracks read 0.000 on the meter while the playhead is
clearly inside a clip, this is why.

**2. Starting playback resets the playhead.** `transport("start")` jumps to the
arrangement start and overrides any position you set beforehand. Start first,
*then* `set_playhead(bar)`. Better: pass `start_bar` to `measure_tracks` /
`record_master` and let them do the whole dance.

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

**6. Arrangement clips are frozen copies.** `place_in_arrangement` duplicates
the session clip *as it is at that moment*. Editing the session clip's notes or
automation afterwards does NOT update the copies already in the arrangement —
the user keeps hearing the old version with no error anywhere. After any
session-clip edit call **`refresh_arrangement_track`**: it re-reads the existing
layout and rebuilds it from the current session clips, so you do not have to
remember where everything was placed. (It matches by clip name — if you rename
a session clip, re-place that track by hand instead.)

**7. An empty drum pad is silent, not an error.** `get_drum_map` returns
Live's *standard* mapping (kick 36, shaker 70, …); the rack you actually loaded
does not have to fill all of it. Notes on an empty pad play nothing, report
nothing, and only surface much later as a band that reads 0.0% in an analysis.
Call **`get_drum_pads(track, device)`** after loading a rack and write only
notes it lists. Factory kits often cover just 36–51. The `sound-check` skill has
the full pre-flight — run it before you place arrangement clips, not after.

**8. Track indices go stale the moment the user touches the set.** The user
deleting or adding one track in the GUI shifts every index below it; your
cached map then silently addresses the wrong tracks (or errors with "Index out
of range" mid-script). Re-query track names and rebuild the map at the start
of every work session, and whenever any track-level call surprises you —
never trust a map cached before user interaction.

## Sound design: presets first, then shape

**Do not build every sound from an init patch.** Live ships thousands of
professionally designed instrument racks and presets — layered, processed,
refined for years. A raw Wavetable patch you dial in blind will sound thin
next to them. The workflow that produces quality:

1. `search_browser` in the **sounds** category with the *role* as the query
   ("Pad", "Pluck", "Bass", "Lead", "Keys") plus a character word from the
   brief ("Dark Pad", "Glass Pluck") — these match Live's own preset naming.
2. Load the best candidate and **audition it before you keep it** —
   `audition_instrument(track)` solos it, bypasses the master chain (an EQ and
   limiter hide the preset's character), records, and returns the band split
   with a verdict. Picking a preset by its name is a guess; this is the step
   that turns the guess into a measurement. Skipping it is how a lead that is
   94.8% one band ends up in an arrangement.
3. Shape it with its **macros** (racks expose 8+ named macro parameters —
   they are the designer's intended handles) and with inserts (EQ, delay),
   not by rebuilding the synthesis.
4. Drop to an init Wavetable/Operator patch only when no preset is close, or
   when the user explicitly wants bespoke sound design — and say so.

Filter/cutoff floors below still apply to presets: a great preset muffled to
400 Hz is still mud.

## Mixing with your ears: the record → analyze loop

You cannot hear — but Live can record what the user hears. `record_master`
captures the master output (Resampling) while the arrangement plays and
returns a wav path plus band analysis; `compare_audio_files` diffs it against
a reference track, level-matched, in dB per band.

- Before judging or "fixing" a mix, record the loudest section and read the
  band distribution — do not EQ from imagination.
- After a chain of mix changes, record again and diff against the previous
  recording: numbers moving the wrong way beat opinions.
- When the user provides a reference track, `compare_audio_files` output is
  the mixing to-do list ("lowmid +4 dB fazla → kis").
- MIDI that measures right but feels stiff: `apply_groove` (swing for
  drums/percs, small timing/velocity jitter for melodic parts, same seed =
  reproducible). Never apply twice to the same clip — jitter accumulates.

## Sound design: say the unit you mean, and the muffling trap

**Never set a raw value.** Live's internal scales are not the displayed unit —
Auto Filter's `Frequency` runs 20–135 and reads as "265 Hz"; Wavetable's runs
0–1. `set_device_parameter` takes exactly one of four ways to say what you want:

| you mean | use | example |
|---|---|---|
| a frequency | `hz=` | `hz=250` — bisects on the device's own readout, so it is right on EQ Eight, Auto Filter and Wavetable alike |
| a named setting | `display=` | `display="1/4"`, `display="SawDown"`, `display="High Pass 12dB"` |
| a proportion | `percent=` | Amount, Shape, Drive — things with no unit |
| a raw value | `value=` | only after reading min/max |

`display=` on a wrong name lists every option in the error, and
`get_parameter_options` lists them on demand — never probe enum values by hand.
Both work on `set_master_parameter` and `set_return_parameter` too.
`set_device_parameter` reports back the displayed value; read it to confirm.

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

**A preset can have more than one filter, and the lowest LOWPASS wins.** Read
the type, not just the frequency — Wavetable ships two filters and its first one
is often a *highpass*. Raising a highpass does not open the sound, it thins it:
on a real lead, "opening" Filter 1 from 605 Hz to 1.47 kHz cut body and added no
top, because the thing capping the top was Filter 2. Note also that Wavetable's
`Filter 1 LP/HP` parameter selects the circuit model (Clean / OSR / MS2 / SMP /
PRD), *not* the response — the response is `Filter 1 Type`. Measured on that lead: moving Filter 1
shifted the energy split by 2 points; opening the Filter 2 lowpass to 5.9 kHz
shifted it by 33 and took the high band from 0.0% to 11.5%. Read
`list_track_filters(track, role=…)` — it reports every cutoff in Hz with its
response type and flags only the ones that actually cap the top. `load_device` reports them at load time too,
so a strangled preset announces itself instead of being found three hours later.

**Make room instead of turning things up.** Everything sharing the low end makes
a mix muddy and the kick inaudible. High-pass pads, leads and plucks around
200–320 Hz; that region belongs to kick and bass. Give the kick its own EQ: a
high-pass under ~30 Hz, a small boost near 55 Hz for body, and a boost near
3 kHz for the click — the click is what makes a kick audible on laptop speakers.

**Unison above ~60% turns a lead into wash.** Wide detune plus heavy unison
reads as phasey and cheap. Around 40–50% with ±8 ct is present and solid.

## Automation

Two tools, and the choice matters:

- **`automate_clip`** writes into a *session* clip. The envelope travels with
  the clip when you `place_in_arrangement`, so every copy gets the same move.
  Use it for anything that repeats — a per-bar filter wobble, a clip that should
  always sound the same.
- **`automate_arrangement`** writes across the *timeline* in absolute bars. Use
  it for anything long-form: a 32-bar filter opening through a breakdown, a
  build that rises over 16 bars, a slow swell across a whole section.

  **Live creates envelopes only on session clips** — calling
  `create_automation_envelope` on an arrangement clip fails with "Not a session
  clip". So the only way to get a sweep longer than one clip is to make a
  separate session clip per placement, each carrying its slice, and place them.
  `automate_arrangement` does exactly that bookkeeping: it opens
  `"<clip> ~b<bar>"` variants, writes the slices, and re-places them at the same
  positions. Expect new clips to appear in Session view — that is the mechanism
  working, not a bug. Re-automating the same span reuses the variants instead of
  piling up new ones, and it refuses spans covering more than `max_clips`
  placements so you do not accidentally create forty clips.

Techno and trance live on 16–32 bar moves; reach for `automate_arrangement`
before you start making clip variants.

You still may want clip variants for *character* rather than length — dark for
the breakdown, open for the drop — placed section by section. Both approaches
compose.

Points take `percent` (or `value`), so the same reasoning as above applies. A
sweep that ends at 60% has not opened.

**Land the end of a sweep on a downbeat that can hide it.** The envelope lives
inside the covered clips, so the bar after the last point the parameter snaps
back to its stored device value — instantly, mid-bar if you let it. A 16-bar
opening that ends at bar 112 slams the filter shut exactly where the build
should be at its widest. Carry the sweep through the build and put its last
point on the drop's downbeat, where the kick and the impact mask the jump.
Verify it: `set_playhead` to a bar, then read the parameter with
`list_device_parameters` — the value follows the envelope, so you can check the
curve bar by bar and confirm it reverts outside the span instead of leaking
into the rest of the track.

## Mixing by measurement

`measure_tracks` returns real meter data for several tracks in **one** playback
pass, ranked by peak. Use it: measure, adjust faders, measure again. Do not
guess at levels. `measure_track_level` is the single-track form.

**Always pass `start_bar` when working in the arrangement.** Without it you
measure wherever the playhead happens to sit — and a playhead parked outside the
section reads 0.000, which is indistinguishable from a genuinely silent track.
With it, the tool positions, plays, settles, measures and stops for you.

Three traps, all of which will give you confident nonsense:

- **A silent track reads 0.000.** Never treat that as "too quiet" and raise the
  fader — you will drive it to maximum. Anything under 0.02 comes back flagged
  `silent`: find out *why* first. Usual causes: empty drum pad (trap 7), wrong
  section, `back_to_arranger` (trap 1), mute.
- **Measure across a full loop.** The meter updates at roughly 10 Hz and a
  window shorter than the loop samples a random slice of it. An 8-bar loop at
  128 BPM needs about 15 seconds.
- **The meter is not the mix.** It reads a track's own output, before you can
  hear how it sits. Confirm balance decisions with `record_master`.

**Look at your sends before you trust them.** `list_return_devices` and
`list_return_device_parameters` show what is actually on A-Reverb and B-Delay; a
0.5 send into a 1-second room and into an 8-second hall are different mixes.
Shape them with `set_return_parameter`, and `load_return_device` if the return
is empty.

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

**Delivering the file.** Live's Export Audio dialog is not exposed to the API.
`render_arrangement` records the whole timeline through the master via
Resampling and hands back a wav — but it runs in **real time**, so a 5-minute
track takes 5 minutes. Use section-sized `record_master` for every mix decision
and `render_arrangement` only once, at the end, when the user wants the file.

## When a plugin is needed

Live's stock devices cover synthesis, EQ, compression and limiting — but some
tasks need third-party plugins. The workflow:

1. **Search what's installed first**: `search_browser("plugins", "<name>")`.
   Recommend from what the user already owns before suggesting downloads.
2. **Check exposure before promising control.** Third-party plugins load but
   most expose only `Device On` until the user clicks Configure and adds
   parameters by hand. Notable exception: MeldaProduction (M*) plugins expose
   their full parameter set — MAutoPitch exposed 28, including per-note scale
   switches. Serum exposed one. Always `list_device_parameters` after loading
   and say plainly what you can and cannot drive.
3. **If nothing suitable is installed, recommend a specific plugin** — free
   first:

| Task | First choice (free) | Notes |
|---|---|---|
| Pitch correction / autotune | **MAutoPitch** (Melda) | Full API exposure; lock the per-note switches to the song's scale |
| Loudness / LUFS metering | **Youlean Loudness Meter** | Readout is invisible to the API — the user reads it, you adjust |
| Vocal/instrument separation | **demucs** (Python, not a plugin) | Run outside Live on the file, load the stem back in |
| Synth beyond Wavetable | **Vital** | Wavetable-class; check exposure before sound-designing |
| Extra saturation/clipper | Stock Saturator first | Reach for plugins only if the user asks by name |

4. State the trade plainly: a recommended plugin the user installs mid-session
   appears in the browser without restarting Live, but its parameter exposure
   still follows rule 2.

## Sample loading and audio clips

- **Browser sample loads target the active view.** `load_item` with an audio
  file lands in the *Session* slot only when Session view is showing — switch
  first (`/live/view/show_session`), or the load silently goes nowhere.
  Files must be inside Live's browser locations (User Library) — copy them
  there first.
- **Do not toggle `warping` back and forth** — a warp on→off round trip clamps
  the clip region and truncates the audio. `set_audio_clip` refuses that
  transition for you; if auto-warp guessed the wrong tempo (chipmunk or
  slow-motion playback), delete the clip and reload fresh with warping left off.
  Unwarped is the right call for rubato material (vocals) placed over drum-free
  sections.
- **Balance samples in Live, not on disk.** `set_audio_clip` sets clip `gain`,
  `pitch_coarse` (semitones) and `pitch_fine` (cents) — no need to re-export the
  file to move a stem 2 dB or a semitone. Keep `pitch_coarse` within ±3; beyond
  that the artifacts are audible.

## When setup is the problem

Run `check_connection` first; it names the likely cause. Beyond that:

- Remote Scripts are scanned **only at startup** — Live must be restarted after
  installation, and AbletonOSC selected under Control Surface by hand. No API
  can do that step.
- Editing an already-loaded handler does not need a restart: send
  `/live/api/reload`. Adding a *new* handler module does.
- `hellyee doctor` reports which handlers are present and whether the optional
  audio dependencies are installed.
