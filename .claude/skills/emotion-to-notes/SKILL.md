---
name: emotion-to-notes
description: Translates an emotional description into concrete musical parameters (scale/mode, tempo range, melodic contour, velocity/dynamics, rhythmic density) and then drives hellyee's theory and note tools to realize it in Ableton Live. Use this skill whenever the user describes a feeling, mood, or emotional arc instead of (or alongside) explicit musical terms — e.g. "hüzünlü bir bassline yaz", "write something that feels anxious", "make the drop feel euphoric", "bu bölüm daha gergin olsun", or any request that names a mood, vibe, or emotional trajectory for a track or section. Also trigger when the user asks how a section's emotional arc should evolve across an arrangement (intro→build→drop→breakdown).
---

# Emotion to Notes

Converts a stated emotion into musical decisions, then calls hellyee's existing
theory and note tools (`get_scale_notes`, `get_chord_notes`, `snap_notes_to_scale`,
`get_drum_map`, `add_notes` / `replace_clip_notes`, `quantize_clip`) to write it
into the Live set. This skill is a decision layer — it does not replace any
tool, it decides *what* to call and with *what parameters*.

## Step 1 — Map the emotion to Valence/Arousal

Every emotional description reduces to two axes before anything musical happens:

- **Valence**: positive ↔ negative (pleasant vs. unpleasant)
- **Arousal**: high energy ↔ low energy (activated vs. calm)

If the user's word isn't in the table below, place it on these two axes yourself
using ordinary judgment, then find the nearest row.

| Emotion (TR / EN)              | Valence | Arousal | Mode / Scale                  | Tempo (BPM) | Contour                          | Velocity / Dynamics         | Rhythmic density        |
|---------------------------------|---------|---------|--------------------------------|-------------|-----------------------------------|------------------------------|--------------------------|
| Hüzün / Melancholy              | low     | low     | Aeolian, Dorian                | 60–85       | descending, wide leaps down       | soft, narrow range (40–70)   | sparse, long note values |
| Öfke / Anger                    | low     | high    | Phrygian, Locrian, harmonic min| 130–155     | jagged, repeated short motifs     | loud, hard-edged (100–127)   | dense, off-grid accents  |
| Huzur / Calm, Peace             | high    | low     | Ionian (major), Lydian         | 65–90       | stepwise, gentle arcs             | soft-medium, even (50–80)    | sparse, legato           |
| Coşku / Euphoria, Excitement    | high    | high    | Mixolydian, major pentatonic   | 122–145     | ascending leaps, wide range       | loud, punchy (95–120)        | dense, syncopated        |
| Gerilim / Tension, Suspense     | low     | mid     | Locrian, whole-tone, tritone-heavy | variable, often rubato-feeling | static/hovering, then sudden leap | swelling, crescendo pattern  | irregular, unstable      |
| Nostalji / Nostalgia            | mid-high| low     | Dorian, major with b7 borrowed | 70–95       | descending then resolving up      | medium, breathy (55–75)      | moderate, loose swing    |
| Umut / Hope                     | high    | mid     | Lydian, major                  | 90–115      | ascending, open intervals         | building, medium→loud        | building density         |
| Yalnızlık / Loneliness          | low     | low     | natural minor, sparse harmony  | 55–75       | isolated single-note lines        | very soft, wide dynamic gaps | very sparse               |
| Kaos / Chaos                    | low     | high    | atonal clusters, chromatic     | fast, unstable | erratic, no clear direction    | extreme range, sudden spikes | dense, polyrhythmic       |
| Zafer / Triumph                 | high    | high    | major, mixolydian, fanfare-like| 100–130     | strong upward leaps, arrival on tonic | loud, confident (100–127) | strong downbeats          |

This table is a starting point, not a cage — genre context (see the
`genre-blueprints` skill) should bend tempo and density choices toward what
actually works in the track, not override the emotional intent.

## Step 2 — Translate to tool calls

1. Pick mode/scale from Step 1 → call `get_scale_notes` (or `get_chord_notes`
   if the request is harmonic/chordal) with the user's stated or inferred key.
2. Pick tempo → if this is a new section, call `set_tempo`; if tempo is fixed
   by the existing track, keep it and lean harder on contour/density instead.
3. Generate the note sequence honoring the **contour** column — sketch pitch
   direction first (up/down/static/jagged), then fill in rhythm using the
   **density** column.
4. Set velocities using the **velocity/dynamics** range as a target, not a
   single fixed number — vary within the stated range for realism.
5. Write with `add_notes` / `replace_clip_notes`, then `snap_notes_to_scale`
   if any passing tones fall outside the target mode.
6. If the request involves drums, cross-reference `get_drum_map` for
   emotionally-appropriate hits (e.g. anger → harder-hitting closed
   percussion, calm → fewer transient elements).

## Step 3 — Emotional arcs across an arrangement

When the user describes a *trajectory* rather than a static mood (e.g.
"nostaljiden coşkuya geçsin", "make it build from tense to triumphant"):

1. Break the arc into the existing arrangement sections (intro / build / drop
   / breakdown / outro) using `get_arrangement_clips` to see what's there.
2. Assign each section a row (or an interpolated point between two rows) from
   the table — e.g. intro = Nostalji, build = Umut, drop = Zafer.
3. Vary primarily **one or two parameters at a time** between adjacent
   sections (e.g. keep the scale constant but raise density and velocity
   section over section) — abrupt changes on every axis at once read as
   randomness, not emotional development.
4. Use `automate_clip` for continuous within-section shifts (e.g. a filter
   opening as arousal rises through a build) rather than only discrete
   per-section jumps.
5. A minor→major pivot is the strongest single tool for grief→hope arcs:
   rotate the same chord family so the progression *starts* on the major
   chord (Am–F–C–G → C–G–Am–F) rather than switching keys outright.

## Step 4 — Verify by measurement, not just by ear

Consistent with hellyee's mixing philosophy, don't just assert the emotional
target was hit — check it against the notes actually written:

- **Contour check**: compute the ratio of upward vs. downward intervals in
  the written notes. Melancholy/loneliness should skew downward; hope/triumph
  should skew upward. If the written line doesn't match the intended
  direction, revise before moving on.
- **Density check**: count notes per bar against the target range implied by
  the density column. A "gerilim" (tension) passage that's actually dense and
  busy has drifted toward "kaos" — flag this and adjust.
- **Velocity spread check**: confirm the actual velocity values used fall
  within the target range from the table, and that soft/loud moods aren't
  accidentally using a flat mid-range velocity (which reads as emotionless
  regardless of pitch content).

Report back to the user in plain terms, e.g.: *"Written as Dorian, descending
contour, avg velocity 58 — matches the melancholy target you asked for."*

## Notes on ambiguity

- If an emotion word is genre-coded in the user's own style (techno/house),
  default to interpreting it through that lens first — e.g. "karanlık"
  (dark) in a techno context usually means minor/Phrygian + sparse + hard
  transients, not necessarily slow tempo.
- If the user gives both an explicit musical instruction (e.g. "F minor") and
  an emotional one that would suggest a different scale, the explicit
  instruction wins — use the emotion only to shape contour, dynamics, and
  density within that constraint.
- Never silently swap the user's stated key or tempo for an "emotionally more
  correct" one — ask or note the tension explicitly instead.
