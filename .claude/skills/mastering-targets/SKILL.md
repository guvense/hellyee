---
name: mastering-targets
description: Platform- and purpose-specific mastering with hellyee — chain setup, gain staging, and loudness targets for Spotify, Apple Music, YouTube, SoundCloud, club/DJ play, and per-genre norms, using Live's master meter as the measurement. Use whenever the user asks to master a track, mentions a platform ("Spotify için", "master for Apple Music", "club master"), says the track sounds weak/quiet/not strong ("sesler güçlü gelmiyor", "daha yüksek olsun"), or asks about loudness, LUFS, limiting, or export readiness.
---

# Mastering Targets

## The honest measurement contract

Streaming platforms measure **LUFS** (integrated loudness) and **true peak**.
hellyee cannot read either — Live's API exposes only the master meter
(0–1 scale, 0.85 ≈ 0 dB, ~10 Hz, sustained level not true peak). So:

- Work in **meter targets** (below), calibrated from real sessions. They are
  approximations, and say so when reporting.
- If the user has a loudness meter plugin (Youlean, ADPTR) on their master,
  its readout is invisible to the API — ask the user to read the LUFS number
  aloud and adjust from that. That combination (their eyes + your control) is
  the accurate path.
- True-peak overshoot between meter samples is invisible: keep the limiter
  ceiling conservative (values below) rather than trusting the meter.

## Chain and gain staging

Order on the master: **EQ Eight → Glue Compressor → Limiter** (limiter always
last). If the user's set already has a master chain, work with it — never
stack a second limiter.

1. Trim all track faders **proportionally** until the loudest section's
   master peak reads ~0.75 pre-limiter (preserves the mix balance).
2. EQ: high-pass ≤25 Hz; fix real problems only (a −1 dB mud cut near 500 Hz,
   a gentle +1–2 dB high shelf for air). Mastering EQ moves are small.
3. Glue: ratio 2:1, slow attack (transients pass), threshold for ~1–3 dB of
   glue, auto release.
4. Limiter: raise **Gain** stepwise, measuring the loudest 8 bars each step,
   until the target below is reached.

## Targets by destination

| Destination | Industry target | hellyee meter target (drop, ~8 bars) | Limiter ceiling |
|---|---|---|---|
| **Spotify** | −14 LUFS-I, −1 dBTP | peak ≈ 0.83–0.85, mean ≈ 0.80–0.83 | **−1.0 dB** |
| **Apple Music** | −16 LUFS-I, −1 dBTP | peak ≈ 0.81–0.83, mean ≈ 0.78–0.81 | **−1.0 dB** |
| **YouTube** | −14 LUFS-I | as Spotify | −1.0 dB |
| **SoundCloud / no normalization** | loudness wins (−8…−11) | peak ≈ 0.87–0.89 | −0.3 dB |
| **Club / DJ WAV** | −6…−9 LUFS-I | peak ≈ 0.88–0.91, mean ≈ 0.86+ | −0.3 dB |
| **Ambient / dynamic material** | −16…−18 | peak ≈ 0.75–0.78 | −1.0 dB |

Platform normalization means a −8 LUFS club master gets *turned down* by
Spotify to the same perceived level as a −14 master — but arrives with its
transients crushed. Loud is only free where normalization is off (clubs,
SoundCloud, DJ pools).

**One master cannot serve both worlds.** If the user wants Spotify *and* club
versions, set the chain once and render twice with different limiter Gain
settings (~3–5 dB apart) — report both meter readings.

## Genre norms

- **Techno / trance / dnb / trap**: club-loud is idiomatic (meter 0.87+);
  streaming versions still benefit from backing off to the platform target.
- **House**: slightly gentler (0.85–0.87 club) — groove suffers first from
  over-limiting.
- **Ambient / downtempo**: do not chase loudness at all; dynamics are the
  content.

## The two guardrails (measure, always)

1. **Section contrast**: after any limiter change, measure the quietest
   section (breakdown) and the loudest (drop). If their peaks are within
   ~0.15 of each other, the arrangement has been flattened — back off. Target
   ≥ 0.20 contrast for drop-based genres.
2. **Kick survival**: the kick's own meter should still sit clearly above the
   bass after limiting. If limiting closed the gap, lower everything except
   the kick slightly rather than pushing the kick into the ceiling.

## When the user says it sounds weak

Weakness is more often mix than master. Check in this order:
1. Filter cutoffs (the muffling trap — see the hellyee skill's Hz floors).
2. Kick/bass separation and per-track EQ (body + click boosts).
3. Layer count in the weak section (a thin drop needs layers, not limiter).
4. Only then raise limiter Gain toward the destination target.

Report every change with before/after meter numbers, and state plainly that
final loudness judgment needs ears or a LUFS meter readout.
