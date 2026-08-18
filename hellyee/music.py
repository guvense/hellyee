"""Muzik teorisi ve nota matematigi. OSC'den bagimsiz, saf Python.

Nota isimlendirmesi Ableton'un gosterdigi gibidir: C3 = 60.
(Standart MIDI yaziminda bu C4'tur; Live C3 gosterir.)
"""
from __future__ import annotations

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
FLAT_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
_ALIASES = {"DB": "C#", "EB": "D#", "GB": "F#", "AB": "G#", "BB": "A#"}

#: Bemolle yazilan tonlar. F minor'da nota Ab'dir, G# degil.
_FLAT_MAJOR = {"F", "Bb", "Eb", "Ab", "Db", "Gb", "Cb"}
_FLAT_MINOR = {"D", "G", "C", "F", "Bb", "Eb", "Ab"}
_MINOR_ISH = {"minor", "harmonic_minor", "melodic_minor", "dorian",
              "phrygian", "locrian", "pentatonic_minor", "blues"}

SCALES: dict[str, list[int]] = {
    "major":            [0, 2, 4, 5, 7, 9, 11],
    "minor":            [0, 2, 3, 5, 7, 8, 10],   # dogal minor
    "harmonic_minor":   [0, 2, 3, 5, 7, 8, 11],
    "melodic_minor":    [0, 2, 3, 5, 7, 9, 11],
    "dorian":           [0, 2, 3, 5, 7, 9, 10],
    "phrygian":         [0, 1, 3, 5, 7, 8, 10],
    "lydian":           [0, 2, 4, 6, 7, 9, 11],
    "mixolydian":       [0, 2, 4, 5, 7, 9, 10],
    "locrian":          [0, 1, 3, 5, 6, 8, 10],
    "pentatonic_major": [0, 2, 4, 7, 9],
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "blues":            [0, 3, 5, 6, 7, 10],
    "chromatic":        list(range(12)),
}

CHORDS: dict[str, list[int]] = {
    "maj":   [0, 4, 7],
    "min":   [0, 3, 7],
    "dim":   [0, 3, 6],
    "aug":   [0, 4, 8],
    "sus2":  [0, 2, 7],
    "sus4":  [0, 5, 7],
    "maj7":  [0, 4, 7, 11],
    "min7":  [0, 3, 7, 10],
    "dom7":  [0, 4, 7, 10],
    "dim7":  [0, 3, 6, 9],
    "m7b5":  [0, 3, 6, 10],
    "add9":  [0, 4, 7, 14],
    "maj9":  [0, 4, 7, 11, 14],
    "min9":  [0, 3, 7, 10, 14],
}

# Genel Drum Rack yerlesimi (Live varsayilani)
DRUM_MAP = {
    "kick": 36, "snare": 38, "clap": 39, "closed_hat": 42,
    "open_hat": 46, "low_tom": 41, "mid_tom": 45, "high_tom": 48,
    "crash": 49, "ride": 51, "rim": 37, "shaker": 70,
}


def note_to_midi(name: str) -> int:
    """'C3' -> 60, 'F#4' -> 78. Ableton gosterimi (C3 = 60)."""
    text = name.strip().upper().replace("♯", "#").replace("♭", "B")
    for i, ch in enumerate(text):
        if ch.isdigit() or ch == "-":
            pitch_part, octave_part = text[:i], text[i:]
            break
    else:
        raise ValueError(f"Oktav bulunamadi: {name}")
    pitch_part = _ALIASES.get(pitch_part, pitch_part)
    if pitch_part not in NOTE_NAMES:
        raise ValueError(f"Gecersiz nota adi: {name}")
    return NOTE_NAMES.index(pitch_part) + (int(octave_part) + 2) * 12


def key_uses_flats(root: str, scale: str = "major") -> bool:
    """Bu ton bemolle mi yazilir? F minor -> evet (Ab, Bb, Db, Eb)."""
    text = root.strip()
    head = text[0].upper() + text[1:].lower()
    if "b" in head[1:]:
        return True
    if "#" in head:
        return False
    return head in (_FLAT_MINOR if scale in _MINOR_ISH else _FLAT_MAJOR)


def midi_to_note(pitch: int, flats: bool = False) -> str:
    """60 -> 'C3'. flats=True ise bemolle yazar: 68 -> 'Ab3' (G#3 degil)."""
    names = FLAT_NAMES if flats else NOTE_NAMES
    return f"{names[pitch % 12]}{pitch // 12 - 2}"


def spell(pitches: list[int], root: str, scale: str = "major") -> list[str]:
    """Nota numaralarini tonun yazimina gore isimlendirir."""
    flats = key_uses_flats(root, scale)
    return [midi_to_note(p, flats) for p in pitches]


def scale_pitches(root: str, scale: str = "major",
                  low: str = "C2", high: str = "C5") -> list[int]:
    """Verilen tonda, belirtilen aralikta kalan tum MIDI nota numaralari."""
    if scale not in SCALES:
        raise ValueError(f"Bilinmeyen scale: {scale}. Secenekler: {', '.join(SCALES)}")
    root_pc = note_to_midi(root + "3") % 12
    intervals = SCALES[scale]
    lo, hi = note_to_midi(low), note_to_midi(high)
    return [p for p in range(lo, hi + 1) if (p - root_pc) % 12 in intervals]


def chord_pitches(root: str, quality: str = "maj", inversion: int = 0) -> list[int]:
    """Akor notalarini dondurur. root ornek: 'C3', 'F#2'."""
    if quality not in CHORDS:
        raise ValueError(f"Bilinmeyen akor: {quality}. Secenekler: {', '.join(CHORDS)}")
    base = note_to_midi(root)
    pitches = [base + i for i in CHORDS[quality]]
    for _ in range(inversion % max(1, len(pitches))):
        pitches = pitches[1:] + [pitches[0] + 12]
    return pitches


def snap_to_scale(pitches: list[int], root: str, scale: str = "major") -> list[int]:
    """Ton disi notalari en yakin ton ici notaya cceker."""
    root_pc = note_to_midi(root + "3") % 12
    intervals = SCALES[scale]
    out = []
    for p in pitches:
        if (p - root_pc) % 12 in intervals:
            out.append(p)
            continue
        for delta in (1, -1, 2, -2, 3, -3):
            if (p + delta - root_pc) % 12 in intervals:
                out.append(p + delta)
                break
        else:
            out.append(p)
    return out


def quantize_notes(notes: list[dict], grid: float = 0.25, strength: float = 1.0,
                   quantize_duration: bool = False) -> list[dict]:
    """Notalari izgaraya oturtur.

    grid: 0.25 = 16'lik, 0.5 = 8'lik, 1.0 = 4'luk, 0.125 = 32'lik
    strength: 1.0 tam oturtur, 0.5 mesafenin yarisini kapatir (groove korunur)
    """
    out = []
    for n in notes:
        start = float(n["start"])
        target = round(start / grid) * grid
        new_start = start + (target - start) * strength
        note = dict(n)
        note["start"] = round(max(0.0, new_start), 6)
        if quantize_duration:
            dur = round(float(n["duration"]) / grid) * grid
            note["duration"] = round(max(grid, dur), 6)
        out.append(note)
    return out
