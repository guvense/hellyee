---
name: remix-and-reference
description: Reference-track and remix workflows in Ableton with hellyee — importing a commercial reference onto a muted channel and comparing against it by measurement and offline analysis, and remixing a provided song by separating its stems (vocals/drums/bass/other), importing them, and rebuilding around them. Use whenever the user mentions a reference track, A/B comparison, "referans", matching another song's sound/loudness, or asks to remix a song, extract vocals/stems, "remixle", "vokali ayır", flip/bootleg/rework an existing track.
---

# Remix & Reference

Both workflows stand on three tools: `analyze_audio_file` (offline: key, tempo,
levels, band energies), `separate_stems` (demucs), and `import_audio` (file →
User Library → session clip, with the view/indexing dance handled).

## Reference channel

Producers keep a finished commercial track on a muted channel and check their
mix against it. The hellyee version:

1. `analyze_audio_file(reference)` first — key, tempo, **band_energy_pct** and
   crest ratio are the comparison targets.
2. `import_audio(reference, track_name="REF")`, then immediately
   `set_mixer(ref_track, mute=True)`. **A reference must never play in the
   mix or reach a render.**
3. **A/B by solo**: to audition, `set_mixer(ref_track, mute=False, solo=True)`
   and fire its clip; to return, solo off + mute on. Warn the user: the
   reference passes through the master chain too, so they hear it limited —
   for honest comparison offer to temporarily disable master devices
   ("Device On" = 0) during the A/B, and restore after.
4. **Level-match before judging anything**: play the reference solo, measure
   the master meter; play the drop, measure again. Louder always sounds
   "better" — match within ~0.02 before comparing character.
5. **Spectral comparison is offline, not live.** The API cannot render or
   spectrum-analyze the project; compare the reference's `band_energy_pct`
   against what you know of the mix (which tracks occupy which bands, from
   their filters/EQ) and against per-track meters. State plainly this is
   analysis + inference, not a measured spectrum of the user's master.
6. Typical use of the numbers: reference has 25% sub+bass and your bass
   region reads thin → raise bass/kick region or tame lowmid; reference
   crest_ratio 6 vs your obviously-dynamic master → more limiting for that
   target, and vice versa.

## Remix workflow

The user provides a song and instructions ("vocals only over a new techno
beat", "halftime flip of the drop"). The pipeline:

1. **Analyze the source** — `analyze_audio_file`: its key, tempo, and where
   its energy lives. Report findings before touching anything.
2. **Separate** — `separate_stems(path)` → vocals / drums / bass / other
   (or `two_stems=True` for vocals + instrumental). Takes 30–90 s for a
   full song; say so.
3. **Import the stems the plan needs** — one `import_audio` per stem, each on
   its own named track (VOCAL STEM, DRUM STEM…). Mute the ones not in use
   rather than skipping them; the user may change their mind.
4. **Decide the tempo relationship** and say it out loud:
   - Project follows source (`set_tempo` to the source's tempo) — safest,
     stems play natural.
   - Source follows project — needs warping; auto-warp guesses wrong tempos
     on stems, so leave clips unwarped for rubato material (vocals) and
     prefer tempo-matching the project instead. Never toggle warp on→off
     (region clamp — see the hellyee skill).
5. **Key**: new musical material follows the stem's key (`get_scale_notes`),
   or transpose the stem ±(≤3) semitones with
   `set_audio_clip(pitch_coarse=…)` — more sounds artifacted. The same tool's
   `gain` sits a stem into the mix without re-exporting it. An autotune plugin locked to the target scale
   (MAutoPitch, per-note switches) covers vocal drift.
6. **Rebuild** with the genre-blueprints skill for the target style, treat
   imported stems as first-class layers: EQ them into their slot (high-pass
   a vocal stem at ~120 Hz; a drum stem fights your kick — carve or use only
   its top via steep high-pass), give vocals reverb/delay via sends.
7. **Arrange** — stems are long clips; place segments by bar using
   `place_in_arrangement`, silence sections of a stem with gap clips over
   the unwanted bars.
8. Balance and master by measurement as always. If the remix should sit
   against the original, the original *is* the reference channel — run the
   reference workflow with it.

## Honest limits

- Stem separation is good, not perfect — bleed is normal, worst on busy
  mixes. Vocals separate best; say so when quality matters.
- Export is real-time only: `render_arrangement` resamples the master in real
  time (5-minute track = 5 minutes). Verify by section with `record_master`
  first, render once at the end.
- Time-stretching quality and warp-marker placement are not controllable via
  the API — tempo-matching the project to the source avoids the whole
  problem class.
