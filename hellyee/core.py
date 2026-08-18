"""Live islemleri. Saf fonksiyonlar: ilk arguman OSC baglantisi.

MCP sunucusu bunlarin uzerine ince bir katman. Burada Claude'a ozgu
hicbir sey yok, boylece test etmek ve baska bir arayuzden kullanmak kolay.
"""
from __future__ import annotations

from .music import quantize_notes
from .osc import AbletonOSC

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
