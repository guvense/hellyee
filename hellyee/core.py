"""Live islemleri. Saf fonksiyonlar: ilk arguman OSC baglantisi.

MCP sunucusu bunlarin uzerine ince bir katman. Burada Claude'a ozgu
hicbir sey yok, boylece test etmek ve baska bir arayuzden kullanmak kolay.
"""
from __future__ import annotations

from pathlib import Path

from .music import quantize_notes
from .osc import AbletonOSC, AbletonOSCError

# --------------------------------------------------------------------------
# yardimcilar
# --------------------------------------------------------------------------
def _after(raw, n: int) -> list:
    """Cevaptaki echo edilen ilk n argumani atar."""
    return list(raw)[n:]


def _notes_to_args(notes: list[dict]) -> list:
    args: list = []
    for n in notes:
        args += [
            int(n["pitch"]),
            float(n["start"]),
            float(n["duration"]),
            int(n.get("velocity", 100)),
            int(n.get("mute", 0)),
        ]
    return args


# --------------------------------------------------------------------------
# sarki / transport
# --------------------------------------------------------------------------
def song_status(osc: AbletonOSC) -> dict:
    tempo = osc.query("/live/song/get/tempo")[0]
    playing = bool(osc.query("/live/song/get/is_playing")[0])
    names = list(osc.query("/live/song/get/track_names"))

    tracks = []
    for i, name in enumerate(names):
        try:
            is_midi = bool(_after(osc.query("/live/track/get/has_midi_input", i), 1)[0])
        except Exception:
            is_midi = None
        tracks.append({"index": i, "name": name,
                       "type": "midi" if is_midi else "audio" if is_midi is False else "?"})
    return {"tempo": tempo, "is_playing": playing, "tracks": tracks}


def set_tempo(osc: AbletonOSC, bpm: float) -> str:
    osc.send("/live/song/set/tempo", float(bpm))
    return f"Tempo {bpm} BPM."


def transport(osc: AbletonOSC, action: str) -> str:
    routes = {"start": "/live/song/start_playing",
              "stop": "/live/song/stop_playing",
              "continue": "/live/song/continue_playing"}
    if action not in routes:
        raise ValueError("action: start | stop | continue")
    osc.send(routes[action])
    return f"Transport: {action}"


def create_scene(osc: AbletonOSC, index: int = -1) -> str:
    osc.send("/live/song/create_scene", int(index))
    return "Scene olusturuldu."


def fire_scene(osc: AbletonOSC, scene_index: int) -> str:
    osc.send("/live/scene/fire", int(scene_index))
    return f"Scene {scene_index} calisiyor."


# --------------------------------------------------------------------------
# kanallar
# --------------------------------------------------------------------------
def create_track(osc: AbletonOSC, kind: str = "midi", index: int = -1,
                 name: str = "") -> dict:
    if kind not in ("midi", "audio"):
        raise ValueError("kind: midi | audio")
    before = len(osc.query("/live/song/get/track_names"))
    osc.send(f"/live/song/create_{kind}_track", int(index))
    track_index = before if index == -1 else int(index)
    if name:
        osc.send("/live/track/set/name", track_index, name)
    return {"index": track_index, "kind": kind, "name": name or "(varsayilan)"}


def rename_track(osc: AbletonOSC, track_index: int, name: str) -> str:
    osc.send("/live/track/set/name", int(track_index), name)
    return f"Kanal {track_index} -> '{name}'"


def delete_track(osc: AbletonOSC, track_index: int) -> str:
    osc.send("/live/song/delete_track", int(track_index))
    return f"Kanal {track_index} silindi."


def duplicate_track(osc: AbletonOSC, track_index: int) -> str:
    osc.send("/live/song/duplicate_track", int(track_index))
    return f"Kanal {track_index} kopyalandi."


def set_mixer(osc: AbletonOSC, track_index: int, volume: float | None = None,
              pan: float | None = None, mute: bool | None = None,
              solo: bool | None = None, arm: bool | None = None) -> str:
    t = int(track_index)
    changed = []
    if volume is not None:
        osc.send("/live/track/set/volume", t, float(volume)); changed.append(f"volume={volume}")
    if pan is not None:
        osc.send("/live/track/set/panning", t, float(pan)); changed.append(f"pan={pan}")
    if mute is not None:
        osc.send("/live/track/set/mute", t, int(bool(mute))); changed.append(f"mute={mute}")
    if solo is not None:
        osc.send("/live/track/set/solo", t, int(bool(solo))); changed.append(f"solo={solo}")
    if arm is not None:
        osc.send("/live/track/set/arm", t, int(bool(arm))); changed.append(f"arm={arm}")
    return f"Kanal {t}: {', '.join(changed) if changed else 'degisiklik yok'}"


# --------------------------------------------------------------------------
# klipler
# --------------------------------------------------------------------------
def create_clip(osc: AbletonOSC, track_index: int, clip_index: int,
                length_beats: float, name: str = "") -> str:
    osc.send("/live/clip_slot/create_clip", int(track_index), int(clip_index),
             float(length_beats))
    if name:
        osc.send("/live/clip/set/name", int(track_index), int(clip_index), name)
    return f"Klip: kanal {track_index}, slot {clip_index}, {length_beats} vurus."


def delete_clip(osc: AbletonOSC, track_index: int, clip_index: int) -> str:
    osc.send("/live/clip_slot/delete_clip", int(track_index), int(clip_index))
    return f"Klip silindi: {track_index}/{clip_index}"


def fire_clip(osc: AbletonOSC, track_index: int, clip_index: int) -> str:
    osc.send("/live/clip/fire", int(track_index), int(clip_index))
    return f"Klip calisiyor: {track_index}/{clip_index}"


def stop_clip(osc: AbletonOSC, track_index: int, clip_index: int) -> str:
    osc.send("/live/clip/stop", int(track_index), int(clip_index))
    return f"Klip durdu: {track_index}/{clip_index}"


def set_clip_properties(osc: AbletonOSC, track_index: int, clip_index: int,
                        name: str | None = None, loop_start: float | None = None,
                        loop_end: float | None = None,
                        color_index: int | None = None) -> str:
    t, c = int(track_index), int(clip_index)
    changed = []
    if name is not None:
        osc.send("/live/clip/set/name", t, c, name); changed.append(f"name='{name}'")
    if loop_start is not None:
        osc.send("/live/clip/set/loop_start", t, c, float(loop_start)); changed.append("loop_start")
    if loop_end is not None:
        osc.send("/live/clip/set/loop_end", t, c, float(loop_end)); changed.append("loop_end")
    if color_index is not None:
        osc.send("/live/clip/set/color_index", t, c, int(color_index)); changed.append("color")
    return f"Klip {t}/{c}: {', '.join(changed) if changed else 'degisiklik yok'}"


# --------------------------------------------------------------------------
# notalar
# --------------------------------------------------------------------------
def get_notes(osc: AbletonOSC, track_index: int, clip_index: int) -> list[dict]:
    values = _after(osc.query("/live/clip/get/notes", int(track_index), int(clip_index)), 2)
    return [
        {"pitch": int(values[i]), "start": float(values[i + 1]),
         "duration": float(values[i + 2]), "velocity": int(values[i + 3]),
         "mute": int(values[i + 4])}
        for i in range(0, len(values) - 4, 5)
    ]


def add_notes(osc: AbletonOSC, track_index: int, clip_index: int,
              notes: list[dict]) -> str:
    if not notes:
        return "Nota verilmedi."
    osc.send("/live/clip/add/notes", int(track_index), int(clip_index),
             *_notes_to_args(notes))
    return f"{len(notes)} nota eklendi ({track_index}/{clip_index})."


def clear_notes(osc: AbletonOSC, track_index: int, clip_index: int) -> str:
    osc.send("/live/clip/remove/notes", int(track_index), int(clip_index))
    return f"Klip {track_index}/{clip_index} notalari silindi."


def replace_notes(osc: AbletonOSC, track_index: int, clip_index: int,
                  notes: list[dict]) -> str:
    clear_notes(osc, track_index, clip_index)
    add_notes(osc, track_index, clip_index, notes)
    return f"{len(notes)} nota ile degistirildi ({track_index}/{clip_index})."


def quantize_clip(osc: AbletonOSC, track_index: int, clip_index: int,
                  grid: float = 0.25, strength: float = 1.0,
                  quantize_duration: bool = False) -> str:
    """Notalari okur, izgaraya oturtur, klibe geri yazar."""
    notes = get_notes(osc, track_index, clip_index)
    if not notes:
        return "Klipte nota yok."
    fixed = quantize_notes(notes, grid=grid, strength=strength,
                           quantize_duration=quantize_duration)
    replace_notes(osc, track_index, clip_index, fixed)
    return (f"{len(fixed)} nota {grid} izgarasina oturtuldu "
            f"(strength={strength}).")


# --------------------------------------------------------------------------
# device'lar
# --------------------------------------------------------------------------
def list_devices(osc: AbletonOSC, track_index: int) -> list[dict]:
    names = _after(osc.query("/live/track/get/devices/name", int(track_index)), 1)
    classes = _after(osc.query("/live/track/get/devices/class_name", int(track_index)), 1)
    return [{"index": i, "name": n, "class_name": classes[i] if i < len(classes) else None}
            for i, n in enumerate(names)]


def list_device_parameters(osc: AbletonOSC, track_index: int,
                           device_index: int) -> list[dict]:
    """Parametreleri isim, guncel deger ve min/max araligiyla dondurur."""
    t, d = int(track_index), int(device_index)
    names = _after(osc.query("/live/device/get/parameters/name", t, d), 2)
    values = _after(osc.query("/live/device/get/parameters/value", t, d), 2)
    mins = _after(osc.query("/live/device/get/parameters/min", t, d), 2)
    maxs = _after(osc.query("/live/device/get/parameters/max", t, d), 2)

    out = []
    for i, name in enumerate(names):
        value = values[i] if i < len(values) else None
        lo = mins[i] if i < len(mins) else None
        hi = maxs[i] if i < len(maxs) else None
        percent = None
        if None not in (value, lo, hi) and hi != lo:
            percent = round((value - lo) / (hi - lo) * 100, 1)
        out.append({"index": i, "name": name, "value": value,
                    "min": lo, "max": hi, "percent": percent})
    return out


def delete_device(osc: AbletonOSC, track_index: int, device_index: int) -> str:
    """Kanaldan bir device'i siler."""
    osc.send("/live/track/delete_device", int(track_index), int(device_index))
    return f"Kanal {track_index} / device {device_index} silindi."


def _resolve_parameter(osc: AbletonOSC, track_index: int, device_index: int,
                       parameter: int | str) -> dict:
    params = list_device_parameters(osc, track_index, device_index)
    if isinstance(parameter, int) or str(parameter).lstrip("-").isdigit():
        idx = int(parameter)
        if not 0 <= idx < len(params):
            raise ValueError(f"Parametre indeksi araligin disinda: {idx}")
        return params[idx]

    needle = str(parameter).lower()
    match = next((p for p in params if p["name"].lower() == needle), None)
    if match is None:
        match = next((p for p in params if needle in p["name"].lower()), None)
    if match is None:
        available = ", ".join(p["name"] for p in params)
        raise ValueError(f"'{parameter}' parametresi yok. Mevcut: {available}")
    return match


def set_device_parameter(osc: AbletonOSC, track_index: int, device_index: int,
                         parameter: int | str, value: float | None = None,
                         percent: float | None = None) -> str:
    """Parametreyi mutlak degerle veya araligin yuzdesiyle ayarlar."""
    if (value is None) == (percent is None):
        raise ValueError("value VEYA percent ver, ikisini birden degil.")

    t, d = int(track_index), int(device_index)
    param = _resolve_parameter(osc, t, d, parameter)

    if percent is not None:
        lo, hi = param["min"], param["max"]
        if lo is None or hi is None:
            raise ValueError(f"'{param['name']}' icin min/max okunamadi; "
                             "mutlak deger kullan.")
        value = lo + (hi - lo) * (max(0.0, min(100.0, float(percent))) / 100.0)

    osc.send("/live/device/set/parameter/value", t, d, param["index"], float(value))

    try:
        shown = _after(osc.query("/live/device/get/parameter/value_string",
                                 t, d, param["index"]), 3)
        readable = shown[0] if shown else value
    except Exception:
        readable = value
    return f"Kanal {t} / device {d} / '{param['name']}' = {readable}"


# --------------------------------------------------------------------------
# browser (device yukleme) - abletonosc_patch/browser.py gerektirir
# --------------------------------------------------------------------------
BROWSER_HINT = ("Browser handler'i kurulu degil. "
                "Calistir: python scripts/patch_abletonosc.py, "
                "sonra Live'i yeniden baslat.")


def browser_categories(osc: AbletonOSC) -> list[str]:
    return [str(c) for c in osc.query("/live/browser/get/categories")]


def browser_search(osc: AbletonOSC, category: str, query: str = "",
                   max_results: int = 30) -> list[dict]:
    """Yuklenebilir device/preset arar. Ikili gelir: name, uri, name, uri..."""
    flat = list(osc.query("/live/browser/search", category, query,
                          int(max_results), timeout=10.0))
    return [{"name": flat[i], "uri": flat[i + 1]}
            for i in range(0, len(flat) - 1, 2)]


def load_device(osc: AbletonOSC, track_index: int, category: str,
                query: str) -> dict:
    """Arar ve ilk eslesmeyi kanalin device zincirinin sonuna yukler."""
    raw = osc.query("/live/browser/load_device", int(track_index), category,
                    query, timeout=15.0)
    return {"track_index": raw[0], "loaded": raw[1], "uri": raw[2]}


def load_item(osc: AbletonOSC, track_index: int, uri: str) -> dict:
    """URI'si bilinen bir ogeyi yukler (once browser_search ile bul)."""
    raw = osc.query("/live/browser/load_item", int(track_index), uri,
                    timeout=15.0)
    return {"track_index": raw[0], "loaded": raw[1], "uri": raw[2]}


# --------------------------------------------------------------------------
# master track - abletonosc_patch/master.py gerektirir
# --------------------------------------------------------------------------
MASTER = -1  # browser load_device'da master kanali


def master_devices(osc: AbletonOSC) -> list[dict]:
    names = list(osc.query("/live/master/get/devices/name"))
    classes = list(osc.query("/live/master/get/devices/class_name"))
    return [{"index": i, "name": n, "class_name": classes[i] if i < len(classes) else None}
            for i, n in enumerate(names)]


def master_device_parameters(osc: AbletonOSC, device_index: int) -> list[dict]:
    d = int(device_index)
    names = _after(osc.query("/live/master/get/device/parameters/name", d), 1)
    values = _after(osc.query("/live/master/get/device/parameters/value", d), 1)
    mins = _after(osc.query("/live/master/get/device/parameters/min", d), 1)
    maxs = _after(osc.query("/live/master/get/device/parameters/max", d), 1)
    out = []
    for i, name in enumerate(names):
        value = values[i] if i < len(values) else None
        lo = mins[i] if i < len(mins) else None
        hi = maxs[i] if i < len(maxs) else None
        percent = None
        if None not in (value, lo, hi) and hi != lo:
            percent = round((value - lo) / (hi - lo) * 100, 1)
        out.append({"index": i, "name": name, "value": value,
                    "min": lo, "max": hi, "percent": percent})
    return out


def set_master_parameter(osc: AbletonOSC, device_index: int,
                         parameter: int | str, value: float | None = None,
                         percent: float | None = None) -> str:
    if (value is None) == (percent is None):
        raise ValueError("value VEYA percent ver, ikisini birden degil.")
    d = int(device_index)
    params = master_device_parameters(osc, d)

    if isinstance(parameter, int) or str(parameter).lstrip("-").isdigit():
        param = params[int(parameter)]
    else:
        needle = str(parameter).lower()
        param = next((p for p in params if p["name"].lower() == needle), None)
        if param is None:
            param = next((p for p in params if needle in p["name"].lower()), None)
        if param is None:
            raise ValueError(f"'{parameter}' yok. Mevcut: "
                             + ", ".join(p["name"] for p in params))

    if percent is not None:
        lo, hi = param["min"], param["max"]
        if lo is None or hi is None:
            raise ValueError(f"'{param['name']}' icin min/max okunamadi.")
        value = lo + (hi - lo) * (max(0.0, min(100.0, float(percent))) / 100.0)

    osc.send("/live/master/set/device/parameter/value", d, param["index"], float(value))
    try:
        shown = _after(osc.query("/live/master/get/device/parameter/value_string",
                                 d, param["index"]), 2)
        readable = shown[0] if shown else value
    except Exception:
        readable = value
    return f"Master / device {d} / '{param['name']}' = {readable}"


def master_meter(osc: AbletonOSC) -> dict:
    raw = list(osc.query("/live/master/get/output_meter"))
    return {"level": raw[0], "left": raw[1], "right": raw[2]}


def track_meter(osc: AbletonOSC, track_index: int) -> float:
    """Anlik cikis seviyesi (Live olcegi: 0.85 = 0 dB).

    ~10 Hz'de guncellenir; anlamli olmasi icin bir loop boyunca ornekle.
    """
    return float(_after(osc.query("/live/track/get/output_meter_level",
                                  int(track_index)), 1)[0])


def load_master_device(osc: AbletonOSC, category: str, query: str) -> dict:
    """Master kanalina device yukler (mastering zinciri icin)."""
    return load_device(osc, MASTER, category, query)


# --------------------------------------------------------------------------
# arrangement - abletonosc_patch/master.py gerektirir
# --------------------------------------------------------------------------
def arrangement_clips(osc: AbletonOSC, track_index: int) -> list[dict]:
    """Kanalin arrangement kliplerini baslangic sirasina gore dondurur."""
    raw = _after(osc.query("/live/arrangement/get/clips", int(track_index)), 1)
    clips = [{"name": raw[i], "start_beats": raw[i + 1], "length_beats": raw[i + 2]}
             for i in range(0, len(raw) - 2, 3)]
    clips.sort(key=lambda c: c["start_beats"])
    for i, clip in enumerate(clips):
        clip["index"] = i
        clip["start_bar"] = round(clip["start_beats"] / 4, 3)
        clip["length_bars"] = round(clip["length_beats"] / 4, 3)
    return clips


def place_in_arrangement(osc: AbletonOSC, track_index: int, clip_index: int,
                         start_beats: float, repeats: int = 1,
                         step_beats: float | None = None) -> str:
    """Session klibini arrangement'a kopyalar; istenirse arka arkaya tekrarlar.

    Klipteki otomasyon da beraberinde gider.
    """
    if step_beats is None:
        step_beats = float(osc.query("/live/clip/get/length",
                                     int(track_index), int(clip_index))[2])
    for k in range(max(1, int(repeats))):
        osc.query("/live/arrangement/duplicate_clip", int(track_index),
                  int(clip_index), float(start_beats) + k * float(step_beats))
    return (f"{repeats} klip yerlestirildi: kanal {track_index}, "
            f"bar {start_beats / 4:g} itibariyle")


def clear_arrangement_track(osc: AbletonOSC, track_index: int) -> str:
    raw = osc.query("/live/arrangement/clear_track", int(track_index))
    return f"Kanal {track_index}: {raw[1]} arrangement klibi silindi."


def delete_arrangement_clip(osc: AbletonOSC, track_index: int,
                            clip_index: int) -> str:
    osc.query("/live/arrangement/delete_clip", int(track_index), int(clip_index))
    return f"Kanal {track_index} arrangement klip {clip_index} silindi."


def show_arranger(osc: AbletonOSC) -> str:
    osc.query("/live/view/show_arranger")
    return "Arrangement gorunumune gecildi."


# --------------------------------------------------------------------------
# otomasyon
# --------------------------------------------------------------------------
def automate_clip(osc: AbletonOSC, track_index: int, clip_index: int,
                  device_index: int, parameter: int | str,
                  points: list[dict]) -> str:
    """Bir SESSION klibine parametre otomasyonu yazar.

    Live envelope'lari yalnizca session kliplerinde olusturur; klip
    arrangement'a kopyalandiginda otomasyon da beraberinde gider.

    points: [{"beat": 0, "percent": 30}, {"beat": 32, "percent": 95}]
    Noktalar arasi dogrusal interpolasyonla adimlanir.
    """
    if len(points) < 2:
        raise ValueError("En az iki nokta gerekir.")
    param = _resolve_parameter(osc, track_index, device_index, parameter)
    lo, hi = param["min"], param["max"]

    args: list = [int(track_index), int(clip_index), int(device_index),
                  param["index"]]
    for point in sorted(points, key=lambda p: float(p["beat"])):
        if "percent" in point:
            if lo is None or hi is None:
                raise ValueError(f"'{param['name']}' icin min/max okunamadi; "
                                 "percent yerine value kullan.")
            pct = max(0.0, min(100.0, float(point["percent"])))
            value = lo + (hi - lo) * (pct / 100.0)
        else:
            value = float(point["value"])
        args += [float(point["beat"]), float(value)]

    raw = osc.query("/live/clip/automate", *args, timeout=15.0)
    return (f"'{param['name']}' otomasyonu yazildi "
            f"({raw[3]} adim, kanal {track_index} slot {clip_index}).")


def clear_clip_automation(osc: AbletonOSC, track_index: int, clip_index: int,
                          device_index: int, parameter: int | str) -> str:
    param = _resolve_parameter(osc, track_index, device_index, parameter)
    osc.query("/live/arrangement/clear_automation", int(track_index),
              int(clip_index), int(device_index), param["index"])
    return f"'{param['name']}' otomasyonu silindi."


# --------------------------------------------------------------------------
# send / return kanallari - abletonosc_patch/master.py gerektirir
# --------------------------------------------------------------------------
def _send_index(send: int | str) -> int:
    if isinstance(send, str) and send.strip().isalpha():
        return ord(send.strip().upper()) - ord("A")
    return int(send)


def list_return_tracks(osc: AbletonOSC) -> list[dict]:
    names = list(osc.query("/live/returns/get/names"))
    out = []
    for i, name in enumerate(names):
        vol = _after(osc.query("/live/returns/get/volume", i), 1)[0]
        out.append({"index": i, "letter": chr(ord("A") + i), "name": name,
                    "volume": vol})
    return out


def get_track_sends(osc: AbletonOSC, track_index: int) -> list[dict]:
    returns = list_return_tracks(osc)
    out = []
    for r in returns:
        level = _after(osc.query("/live/track/get/send", int(track_index),
                                 r["index"]), 2)[0]
        out.append({"send": r["letter"], "return_name": r["name"],
                    "level": level})
    return out


def set_track_send(osc: AbletonOSC, track_index: int, send: int | str,
                   level: float) -> str:
    idx = _send_index(send)
    osc.send("/live/track/set/send", int(track_index), idx, float(level))
    return (f"Kanal {track_index} send {chr(ord('A') + idx)} = {level:.3f} "
            "(0.85 = 0 dB)")


def set_return_volume(osc: AbletonOSC, return_index: int, level: float) -> str:
    osc.send("/live/returns/set/volume", int(return_index), float(level))
    return f"Return {chr(ord('A') + int(return_index))} volume = {level:.3f}"


def return_meter(osc: AbletonOSC, return_index: int) -> float:
    return float(_after(osc.query("/live/returns/get/output_meter",
                                  int(return_index)), 1)[0])


# --------------------------------------------------------------------------
# ses dosyasi import - browser + session slot dansinin araclasmis hali
# --------------------------------------------------------------------------
HELLYEE_SAMPLES = Path.home() / "Music/Ableton/User Library/Samples/hellyee"


def import_audio(osc: AbletonOSC, path: str, track_name: str = "",
                 track_index: int | None = None, slot: int = 0) -> dict:
    """Bir ses dosyasini Live'a alir: User Library'ye kopyalar, session
    gorunumune gecer, klip olarak yukler. Gerekirse audio kanal olusturur.

    Browser yeni dosyayi hemen indekslemeyebilir; kisa aralikla dener.
    """
    import re
    import shutil as _shutil
    import time as _time

    src = Path(path).expanduser()
    if not src.exists():
        raise FileNotFoundError(f"Dosya yok: {src}")

    HELLYEE_SAMPLES.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", src.name)
    dest = HELLYEE_SAMPLES / safe
    if src.resolve() != dest.resolve():
        _shutil.copy2(src, dest)

    if track_index is None:
        name = track_name or src.stem
        track_index = create_track(osc, "audio", -1, name)["index"]

    osc.query("/live/view/show_session")
    uri = f"query:UserLibrary#Samples:hellyee:{safe}"
    last_error = None
    for attempt in range(8):
        try:
            osc.query("/live/browser/load_item_to_slot", int(track_index),
                      int(slot), uri, timeout=15.0)
            _time.sleep(1.0)
            if osc.query("/live/clip_slot/get/has_clip",
                         int(track_index), int(slot))[2]:
                break
        except AbletonOSCError as exc:
            last_error = exc
        _time.sleep(2.5)          # browser indekslemesi icin bekle
    else:
        raise AbletonOSCError(
            f"'{safe}' yuklenemedi. Browser indekslemesi gecikmis olabilir; "
            f"tekrar dene. Son hata: {last_error}")

    length = float(osc.query("/live/clip/get/length", int(track_index), int(slot))[2])
    if track_name:
        set_clip_properties(osc, track_index, slot, name=track_name)
    return {"track_index": int(track_index), "slot": int(slot),
            "file": str(dest), "length_beats": round(length, 1),
            "length_bars": round(length / 4, 1)}
