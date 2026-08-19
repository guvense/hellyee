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


# --------------------------------------------------------------------------
# 3) Dosya analizi — referans/remix icin
# --------------------------------------------------------------------------
def _load_any(path: str, sr: int = 22050):
    """m4a dahil yukler; gerekirse macOS afconvert ile wav'a cevirir."""
    import subprocess, tempfile, os
    import librosa

    ext = os.path.splitext(path)[1].lower()
    if ext in (".wav", ".aif", ".aiff", ".flac", ".mp3", ".ogg"):
        return librosa.load(path, sr=sr, mono=True)
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()
    subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16", path, tmp.name],
                   check=True, capture_output=True)
    try:
        return librosa.load(tmp.name, sr=sr, mono=True)
    finally:
        os.unlink(tmp.name)


def analyze_file(path: str) -> dict:
    """Sure, tempo, ton, seviye ve bant dagilimi — referans kiyasi icin."""
    import librosa
    import numpy as np

    y, sr = _load_any(path)
    duration = len(y) / sr

    tempo = float(np.atleast_1d(librosa.beat.beat_track(y=y, sr=sr)[0])[0])

    chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
    maj = np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88])
    minp = np.array([6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.75,3.98,2.69,3.34,3.17])
    names = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
    scored = []
    for i in range(12):
        scored.append((float(np.corrcoef(np.roll(maj, i), chroma)[0, 1]), names[i], "major"))
        scored.append((float(np.corrcoef(np.roll(minp, i), chroma)[0, 1]), names[i], "minor"))
    scored.sort(reverse=True)

    rms = float(librosa.feature.rms(y=y)[0].mean())
    peak = float(np.abs(y).max())

    # bant enerjileri: referansla spektral kiyasin temeli
    S = np.abs(librosa.stft(y, n_fft=4096)) ** 2
    freqs = librosa.fft_frequencies(sr=sr, n_fft=4096)
    bands = {"sub_<60": (0, 60), "bass_60_250": (60, 250),
             "lowmid_250_800": (250, 800), "mid_800_2500": (800, 2500),
             "high_2500_8000": (2500, 8000), "air_>8000": (8000, sr / 2)}
    total = S.sum() or 1.0
    band_pct = {k: round(float(S[(freqs >= lo) & (freqs < hi)].sum() / total * 100), 1)
                for k, (lo, hi) in bands.items()}

    return {"duration_sec": round(duration, 1), "tempo_estimate": round(tempo, 1),
            "key_guesses": [{"key": f"{r} {m}", "correlation": round(c, 3)}
                            for c, r, m in scored[:3]],
            "rms": round(rms, 4), "peak": round(peak, 3),
            "crest_ratio": round(peak / max(rms, 1e-6), 1),
            "band_energy_pct": band_pct}


def compare_files(mix_path: str, ref_path: str) -> dict:
    """Mix'i referans parcayla bant bant kiyaslar.

    Bant paylari toplam enerjinin yuzdesi oldugundan kiyas dogal olarak
    seviye-esitlenmistir: delta, "referans gibi tinlamasi icin hangi bolge
    kac dB oynamali" demektir. level_delta_db ise mutlak seviye farkidir.
    """
    import math

    a = analyze_file(mix_path)
    b = analyze_file(ref_path)
    deltas = {}
    for k in a["band_energy_pct"]:
        ma = max(a["band_energy_pct"][k], 0.01)
        mb = max(b["band_energy_pct"].get(k, 0.01), 0.01)
        deltas[k] = round(10 * math.log10(ma / mb), 1)
    level = round(20 * math.log10(max(a["rms"], 1e-6) / max(b["rms"], 1e-6)), 1)
    verdict = []
    for k, d in deltas.items():
        if d >= 2:
            verdict.append(f"{k}: mix'te {d:+.1f} dB fazla — bu bolgeyi kis")
        elif d <= -2:
            verdict.append(f"{k}: mix'te {d:+.1f} dB eksik — bu bolgeyi ac")
    if not verdict:
        verdict = ["bant dagilimi referansla uyumlu (+-2 dB icinde)"]
    if a["crest_ratio"] > b["crest_ratio"] * 1.6:
        verdict.append("mix referanstan cok daha az kompresli (crest yuksek)")
    elif b["crest_ratio"] > a["crest_ratio"] * 1.6:
        verdict.append("mix referanstan cok daha fazla kompresli (crest dusuk)")
    return {"band_delta_db": deltas, "level_delta_db": level,
            "verdict": verdict,
            "mix": {k: a[k] for k in ("rms", "peak", "crest_ratio", "band_energy_pct")},
            "ref": {k: b[k] for k in ("rms", "peak", "crest_ratio", "band_energy_pct")}}


# --------------------------------------------------------------------------
# 4) Stem ayirma — demucs (istege bagli bagimlilik)
# --------------------------------------------------------------------------
def separate_stems(path: str, two_stems: bool = False,
                   out_dir: str = "/tmp/hellyee_stems") -> dict:
    """Sarkiyi stemlere ayirir. two_stems=True: vocals + no_vocals;
    False: vocals + drums + bass + other. demucs gerektirir."""
    import importlib.util, os, subprocess, sys

    if importlib.util.find_spec("demucs") is None:
        raise RuntimeError('demucs kurulu degil: pip install "hellyee[remix]" '
                           "veya pip install demucs")
    # m4a'yi demucs'tan once wav'a cevir (guvenli yol)
    ext = os.path.splitext(path)[1].lower()
    if ext not in (".wav", ".mp3", ".flac"):
        wav = os.path.join(out_dir, "input.wav")
        os.makedirs(out_dir, exist_ok=True)
        subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16", path, wav],
                       check=True, capture_output=True)
        path = wav

    cmd = [sys.executable, "-m", "demucs", "-o", out_dir]
    if two_stems:
        cmd += ["--two-stems", "vocals"]
    cmd.append(path)
    subprocess.run(cmd, check=True, capture_output=True, timeout=1800)

    stem_name = os.path.splitext(os.path.basename(path))[0]
    stem_dir = os.path.join(out_dir, "htdemucs", stem_name)
    stems = {os.path.splitext(f)[0]: os.path.join(stem_dir, f)
             for f in sorted(os.listdir(stem_dir)) if f.endswith(".wav")}
    if not stems:
        raise RuntimeError(f"Stem bulunamadi: {stem_dir}")
    return stems
