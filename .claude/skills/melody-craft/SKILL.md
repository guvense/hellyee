---
name: melody-craft
description: Writes complex, emotionally rich melodies instead of flat scale-walking patterns, and refines them iteratively through conversation. Use this skill whenever the user asks for a melody, lead line, hook, arp phrase, topline, or bassline melody — e.g. "bana melodi ver", "write a lead", "melodiyi daha duygulu yap", "bu hook çok basit", "make it more complex", "daha karmaşık olsun" — and ALWAYS when the user gives feedback on an existing melody. Works together with emotion-to-notes (which picks scale/mode/tempo); this skill decides the actual notes, rhythm, and phrasing.
---

# Melody Craft

Turns "give me a melody" into a phrase with motif logic, tension notes, breath,
and dynamics — then refines it through conversation without throwing it away.
`emotion-to-notes` decides the *palette* (key, mode, tempo, contour direction);
this skill decides the *sentences* written with that palette.

## Why generated melodies sound simple — the seven traps

A melody sounds "basit" when it has these properties. Never deliver a melody
that fails more than one of these checks:

1. **Grid marching** — every note starts on a beat or 8th. Real phrases start
   off the beat, anticipate the bar, or arrive late.
2. **Uniform durations** — all notes 0.5 or 1.0 beats. A phrase needs at least
   3 distinct duration values (e.g. 0.25 ornaments, 1.5 anchors, 3.0 arrivals).
3. **Scale-walking** — stepwise up, stepwise down, repeat. Steps are filler;
   *leaps* carry emotion. A leap of a 6th says more than six steps.
4. **No rests** — sound wall-to-wall. Rests are where the listener breathes;
   a phrase without silence is a paragraph without punctuation.
5. **Flat velocity** — everything 90–100. Velocity range across a phrase should
   span at least 25–30, shaped toward the climax, not random.
6. **Chord-tones only** — every note "safe". Emotion lives in the notes that
   *don't* belong and then resolve (see tension notes below).
7. **Copy-paste repetition** — bar 1 pasted four times. Repetition is good;
   *identical* repetition is dead. Repeat the shape, change the detail.

## Building a phrase — the craft

### Motif first, melody second
Do not write 16 bars of notes. Write a **motif**: 3–6 notes with one
distinctive feature (a leap, a rhythm, a tension-resolution). The melody is
that motif *developed*:

- **Sequence** — repeat the motif starting a step higher/lower.
- **Inversion** — mirror its direction (rise becomes fall).
- **Augmentation / diminution** — same pitches, durations doubled or halved.
- **Fragmentation** — take only the motif's tail and repeat it, tightening.
- **Octave displacement** — same note, different octave; instant drama.

A strong 8-bar phrase is typically: motif (bar 1–2), sequence of it (3–4),
fragment + build (5–6), climax + resolution (7–8).

### Question and answer (antecedent / consequent)
Structure phrases in pairs: the first half ends *away* from the tonic (on the
2nd, 5th, or 7th degree — unresolved, a question), the second half answers by
landing on the tonic or 3rd. This alone makes a melody feel intentional. For
sad/hysterical material, deny the answer once: repeat the question a third
higher, *then* resolve — delayed resolution is the single cheapest source of
emotion.

### Tension notes (the emotion carriers)
Chord tones are the skeleton; non-chord tones are the flesh. Use them
deliberately and always resolve them by step:

| Device | What it is | Feels like |
|---|---|---|
| **Appoggiatura** | leap TO a non-chord note on a strong beat, resolve down a step | grief, longing — the classic "sigh" |
| **Suspension** | hold a note while the chord changes under it, then resolve down | ache, reluctance to let go |
| **Passing tone** | fast note bridging two chord tones | flow, smoothness |
| **Neighbor tone** | step off a chord tone and back | ornament, hesitation |
| **Anticipation** | play the next chord's note *early* | urgency, leaning forward |
| **b2 oscillation** | Phrygian semitone rocking (e.g. F#–G–F#) | hysteria, menace |
| **Raised 7th** (harmonic minor) | leading tone in a minor key | drama, pull toward resolve |

Density guide: roughly 1 tension note per bar in calm material, 2–3 in
emotional peaks. Every tension note must resolve — unresolved ones read as
mistakes, not emotion (unless ending a "question" phrase on purpose).

### Leaps and recovery
After any leap of a 5th or larger, move *stepwise in the opposite direction*.
This is why big leaps sound expressive instead of random. Place the phrase's
single largest leap right before the climax note.

### Climax placement
One highest note per phrase, placed ~60–75% of the way through (bar 5–6 of 8),
reached by buildup, left by descent. Two climaxes = no climax. The climax note
gets the phrase's highest velocity and often its longest duration.

### Rhythm and placement in Live terms
- Start the phrase off the downbeat: begin at beat 0.5 or 1.5, or anticipate
  with a pickup note at beat 3.5 of the previous bar.
- Syncopate: put important notes on the "and" (x.5) and let the downbeat pass
  silently sometimes.
- Mix durations in one phrase: ornaments 0.25, motion 0.5–0.75, anchors
  1.5–2.0, arrivals 2.5–4.0. Slightly detached repeated notes (duration 0.4
  in a 0.5 slot) groove harder than full legato.
- Leave at least one rest of ≥1 beat per 4 bars. End phrases *early* (note
  ends at beat 14, next phrase at 16) — the gap is the phrase boundary.
- Velocity: shape a crescendo into the climax (e.g. 62→74→88→106) and decay
  out; accent syncopated notes +10, ghost the ornaments −20.

### Emotion → gesture map
Combine with the emotion-to-notes table (which sets mode/tempo). Gestures:

| Emotion | Signature gestures |
|---|---|
| Grief / hüzün | descending appoggiaturas, falling 3rds chain, suspensions, ends below where it started |
| Longing / özlem | rising 6th leap then stepwise fall, delayed resolution, wide rests |
| Hysteria / histeri | b2 semitone oscillation, fragmentation tightening (durations halving), climax repeated 3× |
| Hope / umut | rising sequences, anticipation notes, question phrase answered a 3rd HIGHER |
| Menace / karanlık | low register, narrow range with sudden octave-up stabs, tritone touches |
| Euphoria / coşku | upward octave displacement, syncopated repeated tonic, largest leap at drop |

## The conversation loop (refinement, not regeneration)

When the user reacts to a melody, **keep the motif and change only what the
feedback names**. Regenerating from scratch loses what they already liked —
only regenerate if they say so explicitly ("bambaşka bir şey yap").

Feedback dictionary (TR/EN → concrete edits):

| User says | Do this |
|---|---|
| "basit / too simple" | add tension notes + break grid marching (traps 1, 3, 6) |
| "duygusuz / not emotional" | appoggiaturas on strong beats, widen velocity arc, slow the harmonic rhythm under the climax |
| "karmaşık ama ruhsuz / complex but soulless" | REMOVE notes; keep contour, add rests; complexity was hiding the phrase |
| "tekdüze / monotonous" | develop the motif (sequence/inversion) instead of repeating; change bars 5–6 |
| "çok yoğun / too busy" | halve note count, keep climax and anchors, drop ornaments |
| "akılda kalmıyor / not catchy" | shorten the motif to ≤5 notes, repeat it more, simplify rhythm of the FIRST bar only |
| "yükselsin / should rise" | transpose the sequence up per repetition, climax later and higher |
| "nefes alsın / needs air" | insert rests, end phrases a beat early |
| "daha karanlık / darker" | lower register an octave, add b2/tritone touches, reduce velocity ceiling |
| "robotik / robotic" | off-grid starts, duration variety, ±8 velocity humanization, detach repeated notes |

Workflow per iteration:
1. Read the current clip with `get_clip_notes` — never edit blind.
2. Apply the *minimal* edit set from the table above.
3. `replace_clip_notes` (not add — avoid stacking).
4. Fire the clip so the user hears it, and say in one sentence what changed
   ("klimaksı bar 6'ya taşıdım, iki appoggiatura ekledim").
5. Ask nothing; wait for the next reaction.

## Delivery checklist

Before handing over any melody, verify programmatically against the trap list:

- [ ] ≥3 distinct duration values, and ≥1 note ≥1.5 beats
- [ ] ≥1 rest of ≥1 beat per 4 bars
- [ ] ≥2 notes starting off the grid-of-quarters (x.5 / x.75 / x.25)
- [ ] velocity span ≥25, single velocity peak aligned with the pitch climax
- [ ] exactly one highest pitch, at 60–75% of the phrase
- [ ] ≥1 leap ≥ a 5th, recovered by contrary stepwise motion
- [ ] ≥1 resolved tension note per 2 bars
- [ ] motif recurs at least once *varied*, never pasted identically
- [ ] phrase pair = question (non-tonic ending) then answer (tonic/3rd)

If a check fails on purpose (e.g. relentless wall-of-sound for chaos), that's
allowed — but it must be a stated choice, not an accident.
