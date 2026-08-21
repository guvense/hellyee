"""Live islemleri. Saf fonksiyonlar: ilk arguman OSC baglantisi.

MCP sunucusu bunlarin uzerine ince bir katman. Burada Claude'a ozgu
hicbir sey yok, boylece test etmek ve baska bir arayuzden kullanmak kolay.
"""
from __future__ import annotations

import re
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


def _pick_parameter(params: list[dict], parameter: int | str) -> dict:
    """Parametre listesinden isim veya indeksle secer. Saf; OSC'ye dokunmaz."""
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


def _resolve_parameter(osc: AbletonOSC, track_index: int, device_index: int,
                       parameter: int | str) -> dict:
    return _pick_parameter(
        list_device_parameters(osc, track_index, device_index), parameter)


# --- birim farkindalikli ayarlama -----------------------------------------
_NUM_RE = re.compile(r"[-+]?\d*\.?\d+")


def _parse_display(text) -> tuple[float | None, str | None]:
    """'265 Hz' -> (265.0, 'hz') · '1.01 kHz' -> (1010.0, 'hz') · '-3 dB' -> (-3.0, 'db')"""
    text = str(text)
    m = _NUM_RE.search(text)
    if not m:
        return None, None
    value = float(m.group())
    unit = text[m.end():].strip().lower()
    if unit.startswith("khz"):
        return value * 1000.0, "hz"
    if unit.startswith("hz"):
        return value, "hz"
    return value, unit or None


def _solve_hz(read_string, write, lo: float, hi: float, target_hz: float,
              tolerance: float = 0.01, steps: int = 20) -> tuple[float, float]:
    """Device'i ekranda hedef Hz'i gosterene kadar ikili aramayla ayarlar.

    Ic deger ile gorunen Hz arasindaki egri her device'ta farklidir (EQ Eight,
    Auto Filter ve Wavetable'in ucu de baska). Sabit formul yerine device'in
    kendi value_string'ini okuyup araligi daraltmak hepsinde dogru calisir.
    """
    if lo is None or hi is None:
        raise ValueError("Bu parametrenin min/max araligi okunamadi.")
    if target_hz <= 0:
        raise ValueError("hz pozitif olmali.")

    write(lo)
    lo_hz, unit = _parse_display(read_string())
    write(hi)
    hi_hz, _ = _parse_display(read_string())
    if unit != "hz" or lo_hz is None or hi_hz is None:
        write(lo)
        raise ValueError("Bu parametre Hz göstermiyor; percent kullan.")

    ascending = hi_hz >= lo_hz
    a, b = (lo, hi)
    best = (lo, lo_hz)
    for _ in range(steps):
        mid = (a + b) / 2.0
        write(mid)
        got, _u = _parse_display(read_string())
        if got is None:
            break
        if abs(got - target_hz) < abs(best[1] - target_hz):
            best = (mid, got)
        if abs(got - target_hz) <= target_hz * tolerance:
            return (mid, got)
        if (got < target_hz) == ascending:
            a = mid
        else:
            b = mid
    write(best[0])
    return best


def _enumerate_options(read_string, write, lo: float, hi: float,
                       restore: float) -> list[dict]:
    """Ayrik bir parametrenin tum gorunen degerlerini tarar, sonra eskiye doner.

    Sync Rate, Waveform, Filter Type gibi enum parametrelerde "1/4 hangi sayi"
    diye deneme yanilma yapmayi bitirir. Tarama sirasinda deger gecici olarak
    degisir — parca calarken duyulur.
    """
    if lo is None or hi is None:
        raise ValueError("Bu parametrenin min/max araligi okunamadi.")
    span = hi - lo
    if span <= 0 or span > 128 or abs(span - round(span)) > 1e-6:
        raise ValueError("Bu parametre ayrik degil (enum); percent veya hz kullan.")

    out = []
    for i in range(int(round(span)) + 1):
        value = lo + i
        write(value)
        out.append({"value": value, "display": str(read_string())})
    write(restore)
    return out


def parameter_options(osc: AbletonOSC, track_index: int, device_index: int,
                      parameter: int | str) -> dict:
    """Ayrik bir parametrenin secenek listesini dondurur (deger + gorunen ad)."""
    t, d = int(track_index), int(device_index)
    param = _resolve_parameter(osc, t, d, parameter)
    read_string, write = _track_param_io(osc, t, d, param["index"])
    options = _enumerate_options(read_string, write, param["min"], param["max"],
                                 param["value"])
    return {"parameter": param["name"], "options": options}


def _track_param_io(osc: AbletonOSC, t: int, d: int, pindex: int):
    def write(value: float) -> None:
        osc.send("/live/device/set/parameter/value", t, d, pindex, float(value))

    def read_string() -> str:
        return _after(osc.query("/live/device/get/parameter/value_string",
                                t, d, pindex), 3)[0]

    return read_string, write


def _apply_parameter(param: dict, read_string, write, value, percent, hz,
                     display) -> str:
    """value/percent/hz/display'den tam birini uygular, gorunen degeri dondurur."""
    given = [x is not None for x in (value, percent, hz, display)]
    if sum(given) != 1:
        raise ValueError("value, percent, hz veya display'den TAM BIRINI ver.")

    lo, hi = param["min"], param["max"]

    if display is not None:
        options = _enumerate_options(read_string, write, lo, hi, param["value"])
        needle = str(display).strip().lower()
        match = next((o for o in options if o["display"].strip().lower() == needle), None)
        if match is None:
            match = next((o for o in options
                          if needle in o["display"].strip().lower()), None)
        if match is None:
            names = ", ".join(o["display"] for o in options)
            raise ValueError(f"'{display}' bu parametrede yok. Mevcut: {names}")
        write(match["value"])
        return match["display"]

    if hz is not None:
        _solve_hz(read_string, write, lo, hi, float(hz))
        return str(read_string())

    if percent is not None:
        if lo is None or hi is None:
            raise ValueError(f"'{param['name']}' icin min/max okunamadi; "
                             "mutlak deger kullan.")
        value = lo + (hi - lo) * (max(0.0, min(100.0, float(percent))) / 100.0)

    write(float(value))
    try:
        return str(read_string())
    except Exception:
        return str(value)


def set_device_parameter(osc: AbletonOSC, track_index: int, device_index: int,
                         parameter: int | str, value: float | None = None,
                         percent: float | None = None, hz: float | None = None,
                         display: str | None = None) -> str:
    """Parametreyi mutlak deger, yuzde, Hz veya gorunen adla ayarlar."""
    t, d = int(track_index), int(device_index)
    param = _resolve_parameter(osc, t, d, parameter)
    read_string, write = _track_param_io(osc, t, d, param["index"])
    readable = _apply_parameter(param, read_string, write, value, percent, hz,
                                display)
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
    return _with_filter_report(osc, track_index,
                               {"track_index": raw[0], "loaded": raw[1],
                                "uri": raw[2]})


def load_item(osc: AbletonOSC, track_index: int, uri: str) -> dict:
    """URI'si bilinen bir ogeyi yukler (once browser_search ile bul)."""
    raw = osc.query("/live/browser/load_item", int(track_index), uri,
                    timeout=15.0)
    return _with_filter_report(osc, track_index,
                               {"track_index": raw[0], "loaded": raw[1],
                                "uri": raw[2]})


# --------------------------------------------------------------------------
# preset denetimi
#
# Kapali filtreli bir preset hicbir yerde hata vermez: klip yazilir, yerlesir,
# render olur. Tek iz, saatler sonra bakilan bir analizde tek banda sikismis
# enerjidir. Bu yuzden kesim frekanslari yukleme ANINDA raporlanir.
# --------------------------------------------------------------------------
_FILTER_PARAM_RE = re.compile(r"freq|cutoff", re.I)
_EQ_BAND_RE = re.compile(r"^\d+ Frequency [AB]$")   # EQ Eight bantlari: gurultu

# hellyee skill'indeki calisan tabanlar.
ROLE_CUTOFF_FLOOR_HZ = {
    "bass": 1500.0, "pad": 1500.0,
    "pluck": 3000.0, "arp": 3000.0, "keys": 3000.0,
    "lead": 4000.0,
}
LOWEST_FLOOR_HZ = min(ROLE_CUTOFF_FLOOR_HZ.values())


def device_filters(osc: AbletonOSC, track_index: int,
                   device_index: int) -> list[dict]:
    """Device'in Hz okuyan filtre parametrelerini dondurur.

    Adaylari once ISIMDEN secer, yalnizca onlarin value_string'ini sorar;
    90+ parametreli bir enstrumanda hepsini tek tek okumak yavas olurdu.
    """
    t, d = int(track_index), int(device_index)
    names = _after(osc.query("/live/device/get/parameters/name", t, d), 2)
    out = []
    for i, name in enumerate(names):
        name = str(name)
        if not _FILTER_PARAM_RE.search(name) or _EQ_BAND_RE.match(name):
            continue
        read_string, _ = _track_param_io(osc, t, d, i)
        hz, unit = _parse_display(read_string())
        if unit == "hz" and hz is not None:
            out.append({"index": i, "name": name, "hz": round(hz, 1)})
    return out


def _cutoff_warning(filters: list[dict], floor: float | None = None) -> str | None:
    """Zincirdeki EN ALCAK filtre kazanir — uyari onun uzerinden kurulur."""
    limit = floor or LOWEST_FLOOR_HZ
    low = [f for f in filters if f["hz"] < limit]
    if not low:
        return None
    worst = min(low, key=lambda f: f["hz"])
    if floor:
        return (f"'{worst['name']}' {worst['hz']:g} Hz — bu rol icin taban "
                f"{floor:g} Hz. Ses temel frekansindan ibaret kalir.")
    return (f"'{worst['name']}' {worst['hz']:g} Hz — her rol icin dusuk "
            f"(en dusuk taban {LOWEST_FLOOR_HZ:g} Hz). Bir presette birden "
            "fazla filtre olabilir ve EN ALCAK olan kazanir; ustteki bir "
            "filtreyi acmak bunu duzeltmez.")


def track_filters(osc: AbletonOSC, track_index: int,
                  role: str | None = None) -> dict:
    """Kanaldaki butun filtre kesimlerini Hz olarak listeler.

    role verilirse (bass/pad/pluck/arp/keys/lead) calisan tabanla kiyaslar.
    """
    t = int(track_index)
    floor = ROLE_CUTOFF_FLOOR_HZ.get(str(role).lower()) if role else None
    out = []
    for dev in list_devices(osc, t):
        for f in device_filters(osc, t, dev["index"]):
            f = dict(f, device_index=dev["index"], device=dev["name"])
            f["below_floor"] = floor is not None and f["hz"] < floor
            out.append(f)
    res: dict = {"track_index": t, "filters": out}
    if floor:
        res["role"] = str(role).lower()
        res["floor_hz"] = floor
    warning = _cutoff_warning(out, floor)
    if warning:
        res["warning"] = warning
    return res


def _with_filter_report(osc: AbletonOSC, track_index: int, info: dict) -> dict:
    """Yeni yuklenen device'in kesim frekanslarini yukleme raporuna ekler."""
    if int(track_index) < 0:        # master / return: browser kanal kodlamasi
        return info
    try:
        devices = list_devices(osc, int(track_index))
        if not devices:
            return info
        filters = device_filters(osc, int(track_index), devices[-1]["index"])
    except (AbletonOSCError, IndexError, ValueError):
        return info                 # rapor bir kolaylik; yuklemeyi bozmasin
    if filters:
        info["filters"] = filters
        warning = _cutoff_warning(filters)
        if warning:
            info["warning"] = warning
    return info


# --------------------------------------------------------------------------
# master track - abletonosc_patch/master.py gerektirir
# --------------------------------------------------------------------------
MASTER = -1        # browser load_device'da master kanali
RETURN_BASE = -2   # return A = -2, B = -3, ... (browser kanal kodlamasi)


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


def _master_param_io(osc: AbletonOSC, d: int, pindex: int):
    def write(value: float) -> None:
        osc.send("/live/master/set/device/parameter/value", d, pindex, float(value))

    def read_string() -> str:
        return _after(osc.query("/live/master/get/device/parameter/value_string",
                                d, pindex), 2)[0]

    return read_string, write


def set_master_parameter(osc: AbletonOSC, device_index: int,
                         parameter: int | str, value: float | None = None,
                         percent: float | None = None, hz: float | None = None,
                         display: str | None = None) -> str:
    d = int(device_index)
    param = _pick_parameter(master_device_parameters(osc, d), parameter)
    read_string, write = _master_param_io(osc, d, param["index"])
    readable = _apply_parameter(param, read_string, write, value, percent, hz,
                                display)
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
    osc.query("/live/clip/clear_automation", int(track_index),
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


def record_master(osc: AbletonOSC, start_bar: float, bars: float = 8,
                  track_name: str = "REC") -> dict:
    """Aranjman calarken master ciktisini Resampling ile kaydeder.

    Kayit kanalinin monitoru kapatilir (feedback engeli) ve kanal mute'lanir;
    Resampling girisi mute/monitor'den etkilenmez. Kayit, global kuantizasyon
    yuzunden bir sonraki bar sinirinda baslar — start_bar'i buna gore ver.
    Donen dosya yolu analyze_file / compare_files'a verilebilir.
    """
    import time as _time

    status = song_status(osc)
    tempo = float(status["tempo"])
    rec = None
    for t in status["tracks"]:
        if t["name"] == track_name and t["type"] == "audio":
            rec = t["index"]
            break
    if rec is None:
        rec = create_track(osc, "audio", -1, track_name)["index"]

    osc.send("/live/track/set/input_routing_type", int(rec), "Resampling")
    osc.send("/live/track/set/current_monitoring_state", int(rec), 2)  # Off
    osc.send("/live/track/set/mute", int(rec), 1)
    osc.send("/live/track/set/arm", int(rec), 1)
    _time.sleep(0.3)
    if osc.query("/live/clip_slot/get/has_clip", int(rec), 0)[2]:
        delete_clip(osc, rec, 0)
        _time.sleep(0.3)

    osc.send("/live/song/set/back_to_arranger", 0)
    osc.send("/live/song/start_playing")
    _time.sleep(0.3)
    osc.send("/live/song/set/current_song_time", float(start_bar) * 4.0)
    _time.sleep(0.2)
    osc.send("/live/clip_slot/fire", int(rec), 0)   # armed bos slot -> kayit
    _time.sleep((float(bars) * 4.0 + 4.0) * 60.0 / tempo + 1.0)
    stop_clip(osc, rec, 0)
    _time.sleep(1.0)
    osc.send("/live/song/stop_playing")
    osc.send("/live/track/set/arm", int(rec), 0)

    if not osc.query("/live/clip_slot/get/has_clip", int(rec), 0)[2]:
        raise AbletonOSCError(
            "Kayit klibi olusmadi. Kanal arm edilebiliyor mu ve global "
            "kuantizasyon makul mu (1 bar) kontrol et.")
    path = osc.query("/live/clip/get/file_path", int(rec), 0)[2]
    length = float(osc.query("/live/clip/get/length", int(rec), 0)[2])
    return {"file": str(path), "track_index": int(rec),
            "length_beats": round(length, 1), "start_bar": float(start_bar)}


def audition_verdict(analysis: dict) -> list[str]:
    """analyze_file ciktisini presetin SAGLIGI acisindan okur. Saf fonksiyon.

    Esikler bu projede olculdu: bogulmus bir lead enerjisinin %94.8'ini tek
    bantta tutuyor ve crest'i 2.8; ayni sette saglikli bir stab uc banda
    yayiliyor ve crest'i 18.2.

    Bunlar "bu ses guzel mi" demez — "bu patch fiziksel olarak sakat mi" der.
    """
    notes: list[str] = []
    bands = analysis.get("band_energy_pct") or {}
    if bands:
        name, pct = max(bands.items(), key=lambda kv: kv[1])
        if float(pct) > 85.0:
            notes.append(
                f"Enerjinin %{pct:g}'i tek bantta ({name}) — patch filtreyle "
                "bogulmus. Zincirdeki HER filtrenin Hz degerini oku; en alcak "
                "olan kazanir.")
    # Crest zayif bir ayirt edici: bu sette bogulmus lead 2.8, duzeltilmis
    # hali 3.6, saglikli stab 18.2 verdi. Esik ona gore 3.0, ve surekli
    # materyalde dusuk crest'in normal oldugu soyleniyor.
    crest = analysis.get("crest_ratio")
    if crest is not None and float(crest) < 3.0:
        notes.append(
            f"Crest {crest} — neredeyse hic dinamik yok. Pad/sustained bir "
            "seste normal olabilir, ama plucky olmasi gerekiyorsa zarfa bak.")
    top = (float(bands.get("high_2500_8000", 0.0) or 0.0)
           + float(bands.get("air_>8000", 0.0) or 0.0))
    if bands and top < 1.0:
        notes.append(
            "2.5 kHz ustu bos — harmonik yok, ses temel frekansindan ibaret. "
            "Laptop hoparloru ve telefonda tamamen kaybolur.")
    return notes


def audition_instrument(osc: AbletonOSC, track_index: int, bars: float = 4,
                        bypass_master: bool = True,
                        start_bar: float | None = None) -> dict:
    """Kanali sololayip master ciktisini kaydeder — preseti KABUL ETMEDEN once.

    Elle yapinca sekiz adim: solo ac, master'i bypass et, kaydet, analiz et,
    duzelt, tekrar kaydet, master'i geri ac, solo'yu kapat. Son iki adim
    unutulursa set bozuk kalir. Burada solo ve master durumu `finally` ile
    her kosulda — hata alsa bile — geri alinir.

    bypass_master: master zinciri (EQ/glue/limiter) presetin karakterini
        gizler; auditionda varsayilan olarak devre disi birakilir.
    start_bar: verilmezse kanalin ILK arrangement klibinin bari kullanilir.
    """
    t = int(track_index)
    if start_bar is None:
        placed = arrangement_clips(osc, t)
        if not placed:
            raise ValueError(
                f"Kanal {t} aranjmanda calmiyor; start_bar ver ya da once "
                "klip yerlestir.")
        start_bar = placed[0]["start_bar"]

    saved_solo: bool | None = None
    saved_master: list[tuple[int, float]] = []
    try:
        try:
            # Stock AbletonOSC'de bu getter var ama garanti degil; yoksa
            # 1 sn'de dusup solo'yu kapali varsayar (guvenli taraf).
            saved_solo = bool(osc.query("/live/track/get/solo", t,
                                        timeout=1.0)[1])
        except (AbletonOSCError, IndexError):
            saved_solo = False
        osc.send("/live/track/set/solo", t, 1)

        if bypass_master:
            for dev in master_devices(osc):
                d = int(dev["index"])
                on = float(_after(osc.query(
                    "/live/master/get/device/parameters/value", d), 1)[0])
                saved_master.append((d, on))
                osc.send("/live/master/set/device/parameter/value", d, 0, 0.0)

        # record_master bir sonraki bar sinirinda basliyor: bir bar erken gir.
        info = record_master(osc, max(0.0, float(start_bar) - 1.0),
                             float(bars) + 1.0)
    finally:
        for d, on in saved_master:
            osc.send("/live/master/set/device/parameter/value", d, 0, on)
        if saved_solo is not None:
            osc.send("/live/track/set/solo", t, 1 if saved_solo else 0)

    info["auditioned_track"] = t
    info["master_bypassed"] = bool(bypass_master)
    try:
        info["filters"] = track_filters(osc, t)["filters"]
    except AbletonOSCError:
        pass
    return info


def apply_groove(osc: AbletonOSC, track_index: int, clip_index: int,
                 swing: float = 0.0, timing_jitter: float = 0.0,
                 velocity_jitter: int = 0, seed: int | None = None) -> dict:
    """Klipteki notalara insani his katar.

    swing 0..1: her ikinci 16'lik gec calar (1.0 = tam triplet hissi).
    timing_jitter: her notaya +-beat cinsinden rastgele mikro kayma (0.02 tipik).
    velocity_jitter: +-velocity dalgalanmasi (8 tipik).
    Ayni seed ayni sonucu verir; notalar yerinde degistirilir.
    """
    import random as _random

    rng = _random.Random(seed)
    notes = get_notes(osc, track_index, clip_index)
    if not notes:
        return {"changed": 0, "note": "klip bos"}
    for n in notes:
        pos16 = n["start"] / 0.25
        idx = round(pos16)
        if swing > 0 and abs(pos16 - idx) < 0.05 and idx % 2 == 1:
            n["start"] += (1.0 / 6.0) * float(swing)   # 16'lik swing
        if timing_jitter > 0:
            n["start"] += rng.uniform(-timing_jitter, timing_jitter)
        if velocity_jitter > 0:
            n["velocity"] = int(n["velocity"]) + rng.randint(-velocity_jitter,
                                                             velocity_jitter)
        n["start"] = max(0.0, float(n["start"]))
        n["velocity"] = max(1, min(127, int(n["velocity"])))
    replace_notes(osc, track_index, clip_index, notes)
    return {"changed": len(notes), "swing": swing,
            "timing_jitter": timing_jitter, "velocity_jitter": velocity_jitter}


# --------------------------------------------------------------------------
# playhead, loop ve olcum konumu
# --------------------------------------------------------------------------
def set_playhead(osc: AbletonOSC, bar: float) -> str:
    """Aranjman playhead'ini bir bar'a tasir (0 tabanli).

    transport("start") her zaman basa doner; once baslat, SONRA konumlandir.
    Bu fonksiyon calma durumunu degistirmez.
    """
    osc.send("/live/song/set/current_song_time", float(bar) * 4.0)
    return f"Playhead bar {bar:g}."


def set_loop(osc: AbletonOSC, start_bar: float | None = None,
             end_bar: float | None = None, enabled: bool | None = None) -> str:
    """Aranjman loop parantezini ayarlar (bar cinsinden)."""
    changed = []
    if start_bar is not None:
        osc.send("/live/song/set/loop_start", float(start_bar) * 4.0)
        changed.append(f"start={start_bar:g}")
    if start_bar is not None and end_bar is not None:
        osc.send("/live/song/set/loop_length",
                 max(1.0, (float(end_bar) - float(start_bar))) * 4.0)
        changed.append(f"end={end_bar:g}")
    if enabled is not None:
        osc.send("/live/song/set/loop", int(bool(enabled)))
        changed.append(f"loop={'on' if enabled else 'off'}")
    return "Loop: " + (", ".join(changed) if changed else "degisiklik yok")


def back_to_arranger(osc: AbletonOSC) -> str:
    """Session klibi tetiklenmis kanallari aranjmana geri dondurur.

    Bir kanalda session klibi bir kez calistiysa o kanal arrangement kliplerini
    sessizce yok sayar. Aranjmani calmadan once bunu gonder.
    """
    osc.send("/live/song/set/back_to_arranger", 0)
    return "back_to_arranger sifirlandi; kanallar aranjmani calar."


def arrangement_end_bar(osc: AbletonOSC) -> float:
    """Aranjmandaki en son klibin bittigi bar."""
    names = list(osc.query("/live/song/get/track_names"))
    end = 0.0
    for i in range(len(names)):
        try:
            for clip in arrangement_clips(osc, i):
                end = max(end, clip["start_beats"] + clip["length_beats"])
        except Exception:
            continue
    return round(end / 4.0, 3)


def measure_tracks(osc: AbletonOSC, track_indices: list[int],
                   seconds: float = 8.0, start_bar: float | None = None,
                   settle: float = 2.0) -> dict:
    """Birden cok kanali TEK calma gecisinde olcer.

    start_bar verilirse playhead oraya tasinir, calinir ve sonunda durdurulur;
    verilmezse parcanin o an caldigi yeri olcer. Playhead olculecek malzemenin
    disindaysa hersey 0.000 okur — sessiz kanalla ayirt edilemez, o yuzden
    aranjmanda daima start_bar ver.

    Live olcegi: 0.85 = 0 dB. Metre ~10 Hz gunceller; olcum penceresi tum
    loop'u kapsamali (128 BPM'de 8 bar = 15 sn).
    """
    import time as _t

    tracks = [int(t) for t in track_indices]
    if not tracks:
        raise ValueError("En az bir kanal indeksi ver.")

    drove_transport = False
    if start_bar is not None:
        osc.send("/live/song/set/back_to_arranger", 0)
        osc.send("/live/song/start_playing")
        _t.sleep(0.3)
        osc.send("/live/song/set/current_song_time", float(start_bar) * 4.0)
        # metreler onceki bolumun kuyrugunu birakana kadar bekle
        _t.sleep(max(0.5, float(settle)))
        drove_transport = True
    elif not bool(osc.query("/live/song/get/is_playing")[0]):
        raise ValueError(
            "Parca calmiyor; olcum anlamsiz olurdu. start_bar ver "
            "(ornek: start_bar=120) ya da once transport('start').")

    samples: dict[int, list[float]] = {t: [] for t in tracks}
    end = _t.time() + max(1.0, float(seconds))
    while _t.time() < end:
        for t in tracks:
            try:
                samples[t].append(track_meter(osc, t))
            except Exception:
                pass
        _t.sleep(0.02)

    if drove_transport:
        osc.send("/live/song/stop_playing")

    out = []
    for t in tracks:
        vals = samples[t]
        peak = round(max(vals), 4) if vals else 0.0
        mean = round(sum(vals) / len(vals), 4) if vals else 0.0
        out.append({"track_index": t, "peak": peak, "mean": mean,
                    "silent": peak < 0.02})
    out.sort(key=lambda r: r["peak"], reverse=True)

    silent = [r["track_index"] for r in out if r["silent"]]
    result = {"start_bar": start_bar, "seconds": seconds, "tracks": out}
    if silent:
        result["note"] = (
            f"Sessiz okunan kanallar: {silent}. Ya bu bolumde calmiyorlar, ya "
            "enstruman ses uretmiyor. Fader'i YUKSELTME — once sebebi bul.")
    return result


# --------------------------------------------------------------------------
# drum rack ve session slot envanteri
# --------------------------------------------------------------------------
def drum_pads(osc: AbletonOSC, track_index: int, device_index: int) -> dict:
    """Yuklu drum rack'te GERCEKTEN dolu olan pad'leri dondurur.

    get_drum_map Live'in standart eslemesini verir (kick 36, shaker 70...);
    yuklu rack o notalarin hepsini karsilamak zorunda degil. Bos bir pad'e
    nota yazmak hata vermez, sadece sessizdir. Davul pattern'i yazmadan once
    bunu cagir ve kullanacagin notalarin listede oldugunu dogrula.
    """
    raw = _after(osc.query("/live/drumrack/get/pads", int(track_index),
                           int(device_index)), 2)
    pads = [{"note": int(raw[i]), "name": raw[i + 1], "chains": int(raw[i + 2])}
            for i in range(0, len(raw) - 2, 3)]
    pads.sort(key=lambda p: p["note"])
    notes = [p["note"] for p in pads]
    return {"pads": pads, "notes": notes,
            "range": [min(notes), max(notes)] if notes else [],
            "note": "Bu listede olmayan her nota sessizdir."}


def session_clips(osc: AbletonOSC, track_index: int) -> list[dict]:
    """Kanalin session slotlarindaki klipleri listeler (slot, isim, uzunluk)."""
    raw = _after(osc.query("/live/track/get/clip_slots", int(track_index)), 1)
    return [{"slot": int(raw[i]), "name": raw[i + 1],
             "length_beats": round(float(raw[i + 2]), 3),
             "length_bars": round(float(raw[i + 2]) / 4, 3)}
            for i in range(0, len(raw) - 2, 3)]


# --------------------------------------------------------------------------
# return kanal device'lari
# --------------------------------------------------------------------------
def list_return_devices(osc: AbletonOSC, return_index: int) -> list[dict]:
    r = int(return_index)
    names = _after(osc.query("/live/returns/get/devices/name", r), 1)
    classes = _after(osc.query("/live/returns/get/devices/class_name", r), 1)
    return [{"index": i, "name": n, "class_name": classes[i] if i < len(classes) else None}
            for i, n in enumerate(names)]


def list_return_device_parameters(osc: AbletonOSC, return_index: int,
                                  device_index: int) -> list[dict]:
    r, d = int(return_index), int(device_index)
    names = _after(osc.query("/live/returns/get/device/parameters/name", r, d), 2)
    values = _after(osc.query("/live/returns/get/device/parameters/value", r, d), 2)
    mins = _after(osc.query("/live/returns/get/device/parameters/min", r, d), 2)
    maxs = _after(osc.query("/live/returns/get/device/parameters/max", r, d), 2)

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


def _return_param_io(osc: AbletonOSC, r: int, d: int, pindex: int):
    def write(value: float) -> None:
        osc.send("/live/returns/set/device/parameter/value", r, d, pindex,
                 float(value))

    def read_string() -> str:
        return _after(osc.query("/live/returns/get/device/parameter/value_string",
                                r, d, pindex), 3)[0]

    return read_string, write


def set_return_parameter(osc: AbletonOSC, return_index: int, device_index: int,
                         parameter: int | str, value: float | None = None,
                         percent: float | None = None, hz: float | None = None,
                         display: str | None = None) -> str:
    """Return kanalindaki bir device parametresini ayarlar (reverb decay vb.)."""
    r, d = int(return_index), int(device_index)
    param = _pick_parameter(list_return_device_parameters(osc, r, d), parameter)
    read_string, write = _return_param_io(osc, r, d, param["index"])
    readable = _apply_parameter(param, read_string, write, value, percent, hz,
                                display)
    return f"Return {r} / device {d} / '{param['name']}' = {readable}"


def load_return_device(osc: AbletonOSC, return_index: int, category: str,
                       query: str) -> dict:
    """Return kanalinin zincirine device ekler."""
    raw = load_device(osc, RETURN_BASE - int(return_index), category, query)
    return {"return_index": int(return_index), "loaded": raw["loaded"],
            "uri": raw["uri"]}


# --------------------------------------------------------------------------
# audio klip ozellikleri
# --------------------------------------------------------------------------
def set_audio_clip(osc: AbletonOSC, track_index: int, clip_index: int,
                   gain: float | None = None, pitch_coarse: int | None = None,
                   pitch_fine: float | None = None,
                   warping: bool | None = None, warp_mode: int | None = None,
                   force: bool = False) -> str:
    """Audio klibin gain / transpoze / warp ayarlarini degistirir.

    gain: 0.0-1.0 (0.5 ~ 0 dB). pitch_coarse: yari ton, +-48; 3 yari tondan
    fazlasi belirgin artifakt uretir. pitch_fine: cent, +-50.

    Warp'i ACIKTAN KAPALIYA almak klip bolgesini kirpar ve sesi kisaltir; bu
    fonksiyon o gecisi reddeder. Gercekten gerekiyorsa klibi silip yeniden
    yukle, ya da force=True ver.
    """
    t, c = int(track_index), int(clip_index)
    changed = []

    if warping is not None:
        current = bool(_after(osc.query("/live/clip/get/warping", t, c), 2)[0])
        if current and not warping and not force:
            raise ValueError(
                "Warp acikken kapatmak klip bolgesini kirpar (ses kisalir). "
                "Klibi silip warp'siz yeniden yukle, ya da force=True ver.")
        osc.send("/live/clip/set/warping", t, c, int(bool(warping)))
        changed.append(f"warping={warping}")

    if warp_mode is not None:
        osc.send("/live/clip/set/warp_mode", t, c, int(warp_mode))
        changed.append(f"warp_mode={warp_mode}")
    if gain is not None:
        osc.send("/live/clip/set/gain", t, c, float(gain))
        changed.append(f"gain={gain}")
    if pitch_coarse is not None:
        osc.send("/live/clip/set/pitch_coarse", t, c, int(pitch_coarse))
        changed.append(f"pitch_coarse={pitch_coarse}")
    if pitch_fine is not None:
        osc.send("/live/clip/set/pitch_fine", t, c, float(pitch_fine))
        changed.append(f"pitch_fine={pitch_fine}")

    if not changed:
        raise ValueError("Degistirilecek bir sey verilmedi.")
    return f"Kanal {t} klip {c}: " + ", ".join(changed)


# --------------------------------------------------------------------------
# aranjman boyunca otomasyon ve tazeleme
# --------------------------------------------------------------------------
_VARIANT_RE = re.compile(r"\s*~b\d+$")


def automate_arrangement(osc: AbletonOSC, track_index: int, device_index: int,
                         parameter: int | str, points: list[dict],
                         max_clips: int = 16) -> str:
    """Aranjman zaman cizgisi boyunca otomasyon yazar (MUTLAK bar cinsinden).

    Live envelope'lari YALNIZCA session kliplerinde olusturur — bir arrangement
    klibine yazmayi denemek "Not a session clip" hatasi verir. Uzun soluklu bir
    supurmeyi elle yapmanin yolu, kapsanan her yerlesim icin ayri bir session
    klip varyanti acip supurmenin o dilimini yazmak ve yeniden yerlestirmektir.
    Bu fonksiyon tam olarak onu yapar.

    Yan etki: kapsanan her yerlesim icin bir session klibi olusur, adi
    "<klip> ~b<bar>" olur. Ayni araligi tekrar otomatiklestirirsen ayni
    varyantlar yeniden kullanilir, yenisi birikmez.

    points: [{"bar": 96, "percent": 30}, {"bar": 128, "percent": 95}]
    Kapsanan aralikta klip yoksa hata verir; kismen kapsanan kliplerin disinda
    kalan bolumu sinir degerinde sabit tutar.
    """
    if len(points) < 2:
        raise ValueError("En az iki nokta gerekir.")
    t, d = int(track_index), int(device_index)
    param = _resolve_parameter(osc, t, d, parameter)
    lo, hi = param["min"], param["max"]

    pts = sorted(points, key=lambda p: float(p["bar"]))
    pairs: list[tuple[float, float]] = []
    for point in pts:
        if "percent" in point:
            if lo is None or hi is None:
                raise ValueError(f"'{param['name']}' icin min/max okunamadi; "
                                 "percent yerine value kullan.")
            pct = max(0.0, min(100.0, float(point["percent"])))
            value = lo + (hi - lo) * (pct / 100.0)
        else:
            value = float(point["value"])
        pairs.append((float(point["bar"]) * 4.0, value))

    span0, span1 = pairs[0][0], pairs[-1][0]
    if span1 <= span0:
        raise ValueError("Bitis bari baslangictan sonra olmali.")

    def value_at(beat: float) -> float:
        if beat <= pairs[0][0]:
            return pairs[0][1]
        if beat >= pairs[-1][0]:
            return pairs[-1][1]
        for (t0, v0), (t1, v1) in zip(pairs, pairs[1:]):
            if t0 <= beat <= t1:
                if t1 == t0:
                    return v1
                return v0 + (v1 - v0) * ((beat - t0) / (t1 - t0))
        return pairs[-1][1]

    layout = arrangement_clips(osc, t)
    affected = [(i, c) for i, c in enumerate(layout)
                if c["start_beats"] < span1
                and c["start_beats"] + c["length_beats"] > span0]
    if not affected:
        raise ValueError(f"Kanal {t}: bar {span0 / 4:g}-{span1 / 4:g} arasinda "
                         "arrangement klibi yok.")
    if len(affected) > max_clips:
        raise ValueError(
            f"Bu aralik {len(affected)} yerlesim kapsiyor; her biri icin bir "
            f"session klibi acilirdi (sinir {max_clips}). Araligi daralt ya da "
            "daha uzun klipler kullan.")

    slots = session_clips(osc, t)
    by_name = {c["name"]: c["slot"] for c in sorted(slots, key=lambda c: c["slot"])}
    next_slot = max((c["slot"] for c in slots), default=-1) + 1
    num_scenes = int(osc.query("/live/song/get/num_scenes")[0])

    created = []
    reused = 0
    for _, clip in affected:
        c0 = clip["start_beats"]
        length = clip["length_beats"]
        base = _VARIANT_RE.sub("", clip["name"])
        variant = f"{base} ~b{int(round(c0 / 4))}"

        source_slot = by_name.get(clip["name"])
        if source_slot is None:
            raise ValueError(
                f"'{clip['name']}' adli session klibi yok; kanal {t} icin "
                "otomasyon yazilamadi (hicbir sey degistirilmedi).")

        target_slot = by_name.get(variant)
        if target_slot is None:
            #--------------------------------------------------------------
            # Slotu tek tek dagit: offset kullanmak, varyantlarin bir kismi
            # yeniden kullanildiginda bosluk birakip var olmayan bir sahneye
            # yazmayi deniyordu ("Index out of range").
            #--------------------------------------------------------------
            target_slot = next_slot
            next_slot += 1
            while num_scenes <= target_slot:
                create_scene(osc, -1)
                num_scenes += 1
            create_clip(osc, t, target_slot, length, variant)
            notes = get_notes(osc, t, source_slot)
            if notes:
                add_notes(osc, t, target_slot, notes)
        else:
            #--------------------------------------------------------------
            # Yeniden kullanilan varyantta once eski zarfi sil: patch'teki
            # insert_step birikimli calisir, daha dar bir aralik yazmak eski
            # adimlari yerinde birakirdi.
            #--------------------------------------------------------------
            clear_clip_automation(osc, t, target_slot, d, param["index"])
            reused += 1

        #------------------------------------------------------------------
        # Envelope klip basina gore yazilir. Supurmenin disinda kalan bolumu
        # sinir degerinde sabit tutmak icin klip basina ve sonuna da nokta koy.
        #------------------------------------------------------------------
        a = max(span0, c0)
        b = min(span1, c0 + length)
        beats = sorted({a, b} | {bt for bt, _ in pairs if a < bt < b})
        env = [{"beat": round(bt - c0, 4), "value": value_at(bt)} for bt in beats]
        if a > c0:
            env.insert(0, {"beat": 0.0, "value": value_at(a)})
        if b < c0 + length:
            env.append({"beat": round(length, 4), "value": value_at(b)})
        automate_clip(osc, t, target_slot, d, param["index"], env)
        created.append((target_slot, c0))

    #----------------------------------------------------------------------
    # Eski yerlesimleri yuksek indeksten asagi sil (silmek indeksleri kaydirir),
    # sonra varyantlari ayni konumlara koy.
    #----------------------------------------------------------------------
    for index, _ in sorted(affected, key=lambda x: x[0], reverse=True):
        delete_arrangement_clip(osc, t, index)
    for slot, start_beats in created:
        place_in_arrangement(osc, t, slot, start_beats, repeats=1)

    msg = (f"'{param['name']}' otomasyonu bar {span0 / 4:g}-{span1 / 4:g} "
           f"arasinda {len(created)} yerlesime yazildi.")
    fresh = len(created) - reused
    if fresh:
        msg += f" {fresh} yeni session klip varyanti olusturuldu."
    if reused:
        msg += f" {reused} varyant yeniden kullanildi."
    return msg


def refresh_arrangement_track(osc: AbletonOSC, track_index: int) -> str:
    """Kanalin arrangement kliplerini session kliplerinden yeniden uretir.

    place_in_arrangement kopyayi o ANKI haliyle dondurur; session klibini
    sonradan duzeltmek aranjmandakileri degistirmez ve hata da vermez.
    Bu fonksiyon mevcut yerlesimi (isim + konum) okur, kanali temizler ve
    ayni isimli session kliplerinden ayni konumlara yeniden dizer.
    """
    t = int(track_index)
    placed = arrangement_clips(osc, t)
    if not placed:
        return f"Kanal {t}: aranjmanda klip yok."

    slots = session_clips(osc, t)
    by_name: dict[str, list[int]] = {}
    for s in slots:
        by_name.setdefault(s["name"], []).append(s["slot"])

    plan = []
    missing = []
    ambiguous = set()
    for clip in placed:
        matches = by_name.get(clip["name"], [])
        if not matches:
            missing.append(clip["name"])
            continue
        if len(matches) > 1:
            ambiguous.add(clip["name"])
        plan.append((matches[0], clip["start_beats"]))

    if missing:
        raise ValueError(
            f"Kanal {t}: su arrangement kliplerinin session karsiligi yok: "
            f"{sorted(set(missing))}. Tazeleme yapilmadi (yerlesim korundu).")

    clear_arrangement_track(osc, t)
    for slot, start_beats in plan:
        place_in_arrangement(osc, t, slot, start_beats, repeats=1)

    msg = f"Kanal {t}: {len(plan)} klip session'dan tazelendi."
    if ambiguous:
        msg += (f" Ayni isimli birden fazla session klibi var {sorted(ambiguous)}; "
                "en dusuk slot kullanildi.")
    return msg


def render_arrangement(osc: AbletonOSC, start_bar: float = 0,
                       end_bar: float | None = None,
                       track_name: str = "RENDER") -> dict:
    """Aranjmanin tamamini (veya bir araligini) master'dan wav'a kaydeder.

    Live'in Export Audio penceresi API'ye acik degil; bu, record_master'in
    Resampling yolunu tum parca boyunca kullanir. GERCEK ZAMANLI calisir:
    5 dakikalik parca 5 dakika surer. Hizli kontrol icin bolum bazli
    record_master yeterli — bunu teslim edilecek dosya icin kullan.
    """
    if end_bar is None:
        end_bar = arrangement_end_bar(osc)
    bars = float(end_bar) - float(start_bar)
    if bars <= 0:
        raise ValueError(f"Aranjman bos gorunuyor (bitis bar {end_bar}).")
    tempo = float(osc.query("/live/song/get/tempo")[0])
    result = record_master(osc, start_bar, bars, track_name=track_name)
    result["end_bar"] = float(end_bar)
    result["realtime_sec"] = round(bars * 4 * 60.0 / tempo, 1)
    return result
