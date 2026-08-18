"""Ses dosyasini iki sekilde islemek icin yardimcilar.

1) transcribe()      -> konusmayi metne cevirir (sesli komut icin)
2) audio_to_notes()  -> miril/melodi kaydindan MIDI notalari cikarir

Claude API'si ses girdisi KABUL ETMEZ (metin, gorsel ve PDF alir).
O yuzden ses her iki durumda da once yerelde islenir, sonuc metin/JSON
olarak modele verilir.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class Note:
    pitch: int          # MIDI nota numarasi (60 = C3/C4)
    start: float        # vurus (beat) cinsinden baslangic
    duration: float     # vurus cinsinden sure
    velocity: int = 100
    mute: int = 0

    def as_dict(self):
        return asdict(self)


# --------------------------------------------------------------------------
# 1) Konusma -> metin
# --------------------------------------------------------------------------
def transcribe(path: str, language: str | None = None) -> str:
    """Sesli komutu metne cevirir. Once mlx-whisper, yoksa faster-whisper."""
    try:
        import mlx_whisper  # Apple Silicon'da en hizlisi

        result = mlx_whisper.transcribe(
            path,
            path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
            language=language,
        )
        return result["text"].strip()
    except ImportError:
        pass

    from faster_whisper import WhisperModel

    model = WhisperModel("small", compute_type="int8")
    segments, _ = model.transcribe(path, language=language)
    return " ".join(s.text for s in segments).strip()


# --------------------------------------------------------------------------
# 2) Melodi -> MIDI notalari
# --------------------------------------------------------------------------
def audio_to_notes(
    path: str,
    tempo: float = 120.0,
    quantize: float | None = 0.25,
    min_duration_beats: float = 0.08,
) -> list[Note]:
    """Tek sesli (monofonik) bir kayittan nota listesi cikarir.

    librosa.pyin ile perde takibi yapar, ayni notaya denk gelen ardisik
    kareleri birlestirir ve saniyeyi vurusa cevirir.
    quantize: 0.25 -> 16'lik izgaraya oturtur, None -> ham zamanlama.
    """
    import librosa
    import numpy as np

    y, sr = librosa.load(path, sr=22050, mono=True)
    frame_length = 2048
    hop_length = frame_length // 4

    f0, voiced, _ = librosa.pyin(
        y,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C7"),
        sr=sr,
        frame_length=frame_length,
        hop_length=hop_length,
    )

    times = librosa.times_like(f0, sr=sr, hop_length=hop_length)
    midi = librosa.hz_to_midi(f0)

    beats_per_second = tempo / 60.0
    notes: list[Note] = []
    current_pitch: int | None = None
    start_time = 0.0

    def flush(end_time: float):
        nonlocal current_pitch
        if current_pitch is None:
            return
        start_beat = start_time * beats_per_second
        dur_beat = (end_time - start_time) * beats_per_second
        if quantize:
            start_beat = round(start_beat / quantize) * quantize
            dur_beat = max(quantize, round(dur_beat / quantize) * quantize)
        if dur_beat >= min_duration_beats:
            notes.append(Note(pitch=current_pitch, start=round(start_beat, 4),
                              duration=round(dur_beat, 4)))
        current_pitch = None

    for i, t in enumerate(times):
        is_voiced = bool(voiced[i]) and not np.isnan(midi[i])
        pitch = int(round(midi[i])) if is_voiced else None
        if pitch != current_pitch:
            flush(t)
            if pitch is not None:
                current_pitch = pitch
                start_time = float(t)
    flush(float(times[-1]) if len(times) else 0.0)

    return notes


def record(seconds: float = 6.0, path: str = "/tmp/hellyee_input.wav",
           samplerate: int = 44100) -> str:
    """Mikrofondan kayit alir (sesli komut veya mirildanma icin)."""
    import sounddevice as sd
    import soundfile as sf

    audio = sd.rec(int(seconds * samplerate), samplerate=samplerate,
                   channels=1, dtype="float32")
    sd.wait()
    sf.write(path, audio, samplerate)
    return path
