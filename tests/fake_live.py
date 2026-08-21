"""Bellekte calisan sahte bir Live + AbletonOSC.

Gercek `hellyee.core` fonksiyonlarini calistirabilmek icin OSC mesaj
seviyesinde taklit eder; boylece test edilen sey core'un kendi mantigi olur,
yeniden yazilmis bir kopyasi degil.

Onemli olan uc davranis birebir modellenmistir:

1. Sahne sayisindan buyuk bir slota dokunmak "Index out of range" verir.
   Live'da `track.clip_slots[i]` boyle patlar; slot ayirma hatasi da bu
   yuzden gorunur olur.
2. `send` asla hata firlatmaz (fire-and-forget), hata bir SONRAKI `query`
   ile yuzeye cikar. hellyee/osc.py aynen boyle davranir.
3. `insert_step` birikimlidir: ayni zamana yazmak ustune yazar, baska bir
   zamandaki eski adim yerinde kalir. Kod abletonosc_patch/master.py
   icindeki automate_session'dan kopyalanmistir.
"""
from __future__ import annotations

from hellyee.osc import AbletonOSCError

STEP = 0.125


class SessionClip:
    def __init__(self, name: str, length: float, notes=None):
        self.name = name
        self.length = float(length)
        self.notes = list(notes or [])
        # (device_index, parameter_index) -> {zaman: deger}
        self.envelopes: dict[tuple[int, int], dict[float, float]] = {}

    def snapshot(self) -> dict[tuple[int, int], dict[float, float]]:
        """place_in_arrangement kopyayi O ANKI haliyle dondurur."""
        return {k: dict(v) for k, v in self.envelopes.items()}


class ArrangementClip:
    def __init__(self, name, start, length, envelopes):
        self.name = name
        self.start = float(start)
        self.length = float(length)
        self.envelopes = envelopes


class FakeLive:
    def __init__(self, num_scenes: int = 8):
        self.num_scenes = int(num_scenes)
        self.slots: dict[int, dict[int, SessionClip]] = {}
        self.arrangement: dict[int, list[ArrangementClip]] = {}
        self.params: dict[tuple[int, int], list[dict]] = {}
        self.devices: dict[int, dict[int, str]] = {}
        self.pending_preset: list[dict] = []
        self.calls: list[tuple] = []
        self._last_error: str | None = None

    # --- kurulum ---------------------------------------------------------
    def add_session_clip(self, track, slot, name, length, notes=None):
        if slot >= self.num_scenes:
            raise AssertionError(
                f"Test kurulumu hatali: slot {slot} icin sahne yok "
                f"(num_scenes={self.num_scenes}).")
        self.slots.setdefault(track, {})[slot] = SessionClip(name, length, notes)

    def place(self, track, slot, start_beats):
        clip = self.slots[track][slot]
        self.arrangement.setdefault(track, []).append(
            ArrangementClip(clip.name, start_beats, clip.length, clip.snapshot()))
        self.arrangement[track].sort(key=lambda c: c.start)

    def add_device(self, track, device, params: list[dict], name="Device"):
        self.params[(track, device)] = params
        chain = self.devices.setdefault(track, {})
        chain[device] = name

    # --- yardimcilar -----------------------------------------------------
    def arrangement_clips(self, track) -> list[ArrangementClip]:
        return sorted(self.arrangement.get(track, []), key=lambda c: c.start)

    def _clip(self, track, slot):
        """Live'daki track.clip_slots[slot] erisiminin karsiligi."""
        if int(slot) >= self.num_scenes or int(slot) < 0:
            raise IndexError("Index out of range")
        clip = self.slots.get(track, {}).get(int(slot))
        if clip is None:
            raise IndexError("Slotta klip yok")
        return clip

    def _params(self, track, device) -> list[dict]:
        return self.params[(int(track), int(device))]

    # --- OSC yuzeyi ------------------------------------------------------
    def send(self, address: str, *args) -> None:
        self._last_error = None
        self.calls.append((address, args))
        try:
            self._dispatch(address, args)
        except IndexError as exc:
            # Gercek AbletonOSC da /live/error yollar, send sessiz kalir.
            self._last_error = str(exc)

    def query(self, address: str, *args, timeout: float = 4.0):
        self.calls.append((address, args))
        try:
            result = self._dispatch(address, args)
        except IndexError as exc:
            raise AbletonOSCError(str(exc)) from None
        if result is None:
            raise AbletonOSCError(f"{address} icin cevap gelmedi.")
        return tuple(result)

    def _dispatch(self, address: str, args):
        t = int(args[0]) if args else None

        if address == "/live/song/get/num_scenes":
            return (self.num_scenes,)

        if address == "/live/song/create_scene":
            self.num_scenes += 1
            return (self.num_scenes,)

        if address.startswith("/live/device/get/parameters/"):
            field = address.rsplit("/", 1)[1]
            key = {"name": "name", "value": "value",
                   "min": "min", "max": "max"}[field]
            params = self._params(t, args[1])
            return (args[0], args[1]) + tuple(p[key] for p in params)

        if address in ("/live/track/get/devices/name",
                       "/live/track/get/devices/class_name"):
            chain = self.devices.get(t, {})
            key = "name" if address.endswith("/name") else "class_name"
            out = [chain[i] if key == "name" else "FakeDevice"
                   for i in sorted(chain)]
            return (args[0],) + tuple(out)

        if address == "/live/device/get/parameter/value_string":
            param = self._params(t, args[1])[int(args[2])]
            return (args[0], args[1], args[2], param.get("display", ""))

        if address == "/live/browser/load_device":
            # Yeni device zincirin SONUNA gelir.
            chain = self.devices.setdefault(t, {})
            index = (max(chain) + 1) if chain else 0
            chain[index] = str(args[2])
            self.params[(t, index)] = list(self.pending_preset)
            return (args[0], str(args[2]), "uri:fake")

        if address == "/live/track/get/clip_slots":
            out = []
            for slot in sorted(self.slots.get(t, {})):
                clip = self.slots[t][slot]
                out += [slot, clip.name, clip.length]
            return (args[0],) + tuple(out)

        if address == "/live/arrangement/get/clips":
            out = []
            for clip in self.arrangement_clips(t):
                out += [clip.name, clip.start, clip.length]
            return (args[0],) + tuple(out)

        if address == "/live/clip_slot/create_clip":
            slot, length = int(args[1]), float(args[2])
            if slot >= self.num_scenes or slot < 0:
                raise IndexError("Index out of range")
            self.slots.setdefault(t, {})[slot] = SessionClip("", length)
            return (args[0], args[1])

        if address == "/live/clip/set/name":
            self._clip(t, args[1]).name = args[2]
            return (args[0], args[1])

        if address == "/live/clip/get/length":
            return (args[0], args[1], self._clip(t, args[1]).length)

        if address == "/live/clip/get/notes":
            clip = self._clip(t, args[1])
            out = []
            for n in clip.notes:
                out += [n["pitch"], n["start"], n["duration"],
                        n["velocity"], n["mute"]]
            return (args[0], args[1]) + tuple(out)

        if address == "/live/clip/add/notes":
            clip = self._clip(t, args[1])
            vals = args[2:]
            for i in range(0, len(vals) - 4, 5):
                clip.notes.append({
                    "pitch": int(vals[i]), "start": float(vals[i + 1]),
                    "duration": float(vals[i + 2]),
                    "velocity": int(vals[i + 3]), "mute": int(vals[i + 4])})
            return (args[0], args[1])

        if address == "/live/clip/automate":
            return self._automate(args)

        if address == "/live/clip/clear_automation":
            clip = self._clip(t, args[1])
            key = (int(args[2]), int(args[3]))
            clip.envelopes.pop(key, None)
            name = self._params(t, args[2])[int(args[3])]["name"]
            return (args[0], args[1], name)

        if address == "/live/arrangement/duplicate_clip":
            clip = self._clip(t, args[1])
            self.arrangement.setdefault(t, []).append(
                ArrangementClip(clip.name, float(args[2]), clip.length,
                                clip.snapshot()))
            self.arrangement[t].sort(key=lambda c: c.start)
            return (args[0], args[1], args[2])

        if address == "/live/arrangement/delete_clip":
            clips = self.arrangement_clips(t)
            index = int(args[1])
            if not 0 <= index < len(clips):
                raise IndexError("Arrangement klip indeksi araligin disinda")
            self.arrangement[t].remove(clips[index])
            return (args[0], args[1])

        raise AssertionError(f"Sahte Live bu adresi bilmiyor: {address}")

    def _automate(self, args):
        """abletonosc_patch/master.py::automate_session ile ayni mantik."""
        track_index, slot_index, device_index, parameter_index = args[:4]
        points = args[4:]
        if len(points) < 4 or len(points) % 2:
            raise ValueError("En az iki (zaman, deger) cifti gerekir")

        clip = self._clip(int(track_index), slot_index)
        key = (int(device_index), int(parameter_index))
        env = clip.envelopes.setdefault(key, {})

        pairs = [(float(points[i]), float(points[i + 1]))
                 for i in range(0, len(points), 2)]
        written = 0
        for (t0, v0), (t1, v1) in zip(pairs, pairs[1:]):
            span = max(0.0, t1 - t0)
            steps = max(1, int(span / STEP))
            for k in range(steps):
                frac = k / float(steps)
                env[round(t0 + k * STEP, 6)] = v0 + (v1 - v0) * frac
                written += 1
        env[round(pairs[-1][0], 6)] = pairs[-1][1]
        name = self._params(int(track_index), device_index)[
            int(parameter_index)]["name"]
        return (track_index, slot_index, name, written + 1)
