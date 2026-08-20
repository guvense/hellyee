"""Master track + Arrangement handler'i.

AbletonOSC ne master kanali ne de arrangement'a klip yerlestirmeyi disari acar.
Bu dosya ikisini de ekler. (Ayni modulde olmalari kasitli: yeni bir modul
Live'in yeniden baslatilmasini gerektirir, var olan modul /live/api/reload ile
tazelenebilir.)
hellyee reposundaki abletonosc_patch/ altindan gelir.

DIKKAT: Live 11'in gomulu Python'u 3.7'dir. Walrus (:=), `list[str]` ve
`X | Y` union sozdizimi KULLANILAMAZ.
"""
from typing import Any, Optional, Tuple

from .handler import AbletonOSCHandler


class MasterHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "master"

    @property
    def master(self):
        return self.song.master_track

    def _device(self, device_index: int):
        return self.master.devices[int(device_index)]

    def init_api(self):
        # ---- mikser ------------------------------------------------------
        def get_volume(params: Optional[Tuple] = ()) -> Tuple:
            return (self.master.mixer_device.volume.value,)

        def set_volume(params: Optional[Tuple] = ()) -> None:
            self.master.mixer_device.volume.value = float(params[0])

        def get_output_meter(params: Optional[Tuple] = ()) -> Tuple:
            #------------------------------------------------------------------
            # Anlik degerdir; anlamli olmasi icin cagiran taraf tekrar tekrar
            # ornekleyip tepe/ortalama hesaplamalidir.
            #------------------------------------------------------------------
            return (self.master.output_meter_level,
                    self.master.output_meter_left,
                    self.master.output_meter_right)

        # ---- device'lar ---------------------------------------------------
        def get_devices_name(params: Optional[Tuple] = ()) -> Tuple:
            return tuple(device.name for device in self.master.devices)

        def get_devices_class_name(params: Optional[Tuple] = ()) -> Tuple:
            return tuple(device.class_name for device in self.master.devices)

        def get_parameters_name(params: Optional[Tuple] = ()) -> Tuple:
            device = self._device(params[0])
            return (params[0],) + tuple(p.name for p in device.parameters)

        def get_parameters_value(params: Optional[Tuple] = ()) -> Tuple:
            device = self._device(params[0])
            return (params[0],) + tuple(p.value for p in device.parameters)

        def get_parameters_min(params: Optional[Tuple] = ()) -> Tuple:
            device = self._device(params[0])
            return (params[0],) + tuple(p.min for p in device.parameters)

        def get_parameters_max(params: Optional[Tuple] = ()) -> Tuple:
            device = self._device(params[0])
            return (params[0],) + tuple(p.max for p in device.parameters)

        def set_parameter_value(params: Optional[Tuple] = ()) -> Tuple:
            device = self._device(params[0])
            parameter = device.parameters[int(params[1])]
            parameter.value = float(params[2])
            return (params[0], params[1], parameter.value)

        def get_parameter_value_string(params: Optional[Tuple] = ()) -> Tuple:
            device = self._device(params[0])
            parameter = device.parameters[int(params[1])]
            return (params[0], params[1], str(parameter))

        def delete_device(params: Optional[Tuple] = ()) -> Tuple:
            self.master.delete_device(int(params[0]))
            return (params[0],)

        def select(params: Optional[Tuple] = ()) -> Tuple:
            """Master'i secili yapar; browser load_item bunun uzerine yukler."""
            self.song.view.selected_track = self.master
            try:
                if len(self.master.devices) > 0:
                    self.song.view.select_device(self.master.devices[-1])
            except Exception:
                pass
            return (len(self.master.devices),)

        add = self.osc_server.add_handler
        add("/live/master/get/volume", get_volume)
        add("/live/master/set/volume", set_volume)
        add("/live/master/get/output_meter", get_output_meter)
        add("/live/master/get/devices/name", get_devices_name)
        add("/live/master/get/devices/class_name", get_devices_class_name)
        add("/live/master/get/device/parameters/name", get_parameters_name)
        add("/live/master/get/device/parameters/value", get_parameters_value)
        add("/live/master/get/device/parameters/min", get_parameters_min)
        add("/live/master/get/device/parameters/max", get_parameters_max)
        add("/live/master/set/device/parameter/value", set_parameter_value)
        add("/live/master/get/device/parameter/value_string", get_parameter_value_string)
        add("/live/master/delete_device", delete_device)
        add("/live/master/select", select)

        # ---- arrangement --------------------------------------------------
        def arrangement_duplicate_clip(params: Optional[Tuple] = ()) -> Tuple:
            """params: track_index, clip_index, time_beats

            Session'daki bir klibi arrangement'a belirtilen vurusa kopyalar.
            """
            track = self.song.tracks[int(params[0])]
            clip_slot = track.clip_slots[int(params[1])]
            if not clip_slot.has_clip:
                raise ValueError("Slotta klip yok: %s/%s" % (params[0], params[1]))
            track.duplicate_clip_to_arrangement(clip_slot.clip, float(params[2]))
            return (params[0], params[1], params[2])

        def arrangement_get_clips(params: Optional[Tuple] = ()) -> Tuple:
            """params: track_index -> name, start_time, length uclusu"""
            track = self.song.tracks[int(params[0])]
            out = []
            for clip in track.arrangement_clips:
                out += [clip.name, clip.start_time, clip.length]
            return (params[0],) + tuple(out)

        def arrangement_delete_clip(params: Optional[Tuple] = ()) -> Tuple:
            """params: track_index, arrangement_clip_index"""
            track = self.song.tracks[int(params[0])]
            clips = list(track.arrangement_clips)
            index = int(params[1])
            if not 0 <= index < len(clips):
                raise ValueError("Arrangement klip indeksi araligin disinda")
            track.delete_clip(clips[index])
            return (params[0], params[1])

        def arrangement_clear_track(params: Optional[Tuple] = ()) -> Tuple:
            """params: track_index — o kanaldaki tum arrangement kliplerini siler"""
            track = self.song.tracks[int(params[0])]
            count = 0
            for clip in list(track.arrangement_clips):
                track.delete_clip(clip)
                count += 1
            return (params[0], count)

        def show_arranger(params: Optional[Tuple] = ()) -> Tuple:
            import Live
            Live.Application.get_application().view.show_view("Arranger")
            return ("Arranger",)

        # ---- automation ---------------------------------------------------
        #------------------------------------------------------------------
        # Live envelope'lari YALNIZCA session kliplerinde olusturur; bir
        # arrangement klibinde create_automation_envelope cagirmak
        # "Not a session clip" hatasi verir. Uzun soluklu supurmeler bu yuzden
        # core tarafinda session klip varyantlarina bolunerek yazilir.
        #------------------------------------------------------------------
        def _parameter(track_index, device_index, parameter_index):
            track = self.song.tracks[int(track_index)]
            device = track.devices[int(device_index)]
            return device.parameters[int(parameter_index)]

        def automate_session(params: Optional[Tuple] = ()) -> Tuple:
            """params: track, clip_slot, device, parameter, t0,v0, t1,v1, ...

            SESSION klibine otomasyon yazar. Live envelope'lari sadece session
            kliplerinde olusturmaya izin verir; klip arrangement'a
            kopyalandiginda otomasyon da beraberinde gider.
            """
            track_index, slot_index, device_index, parameter_index = params[:4]
            points = params[4:]
            if len(points) < 4 or len(points) % 2:
                raise ValueError("En az iki (zaman, deger) cifti gerekir")

            track = self.song.tracks[int(track_index)]
            clip_slot = track.clip_slots[int(slot_index)]
            if not clip_slot.has_clip:
                raise ValueError("Slotta klip yok")
            clip = clip_slot.clip
            parameter = _parameter(track_index, device_index, parameter_index)
            envelope = clip.automation_envelope(parameter)
            if envelope is None:
                envelope = clip.create_automation_envelope(parameter)

            pairs = [(float(points[i]), float(points[i + 1]))
                     for i in range(0, len(points), 2)]
            STEP = 0.125
            written = 0
            for (t0, v0), (t1, v1) in zip(pairs, pairs[1:]):
                span = max(0.0, t1 - t0)
                steps = max(1, int(span / STEP))
                for k in range(steps):
                    frac = k / float(steps)
                    envelope.insert_step(t0 + k * STEP, STEP, v0 + (v1 - v0) * frac)
                    written += 1
            envelope.insert_step(pairs[-1][0], STEP, pairs[-1][1])
            return (track_index, slot_index, parameter.name, written + 1)

        def clear_automation(params: Optional[Tuple] = ()) -> Tuple:
            """params: track, clip_slot, device, parameter — SESSION klibi.

            automate_session'in karsiligi. Live envelope'lari yalnizca session
            kliplerinde yonetir, o yuzden temizleme de orada yapilir.
            """
            track_index, slot_index, device_index, parameter_index = params[:4]
            track = self.song.tracks[int(track_index)]
            clip_slot = track.clip_slots[int(slot_index)]
            if not clip_slot.has_clip:
                raise ValueError("Slotta klip yok")
            parameter = _parameter(track_index, device_index, parameter_index)
            clip_slot.clip.clear_envelope(parameter)
            return (track_index, slot_index, parameter.name)

        add("/live/clip/automate", automate_session)
        add("/live/clip/clear_automation", clear_automation)
        # ---- return kanallari -------------------------------------------
        def returns_get_names(params: Optional[Tuple] = ()) -> Tuple:
            return tuple(t.name for t in self.song.return_tracks)

        def returns_get_volume(params: Optional[Tuple] = ()) -> Tuple:
            index = int(params[0])
            return (index, self.song.return_tracks[index].mixer_device.volume.value)

        def returns_set_volume(params: Optional[Tuple] = ()) -> None:
            self.song.return_tracks[int(params[0])].mixer_device.volume.value = float(params[1])

        def returns_get_meter(params: Optional[Tuple] = ()) -> Tuple:
            index = int(params[0])
            return (index, self.song.return_tracks[index].output_meter_level)

        add("/live/returns/get/names", returns_get_names)
        add("/live/returns/get/volume", returns_get_volume)
        add("/live/returns/set/volume", returns_set_volume)
        add("/live/returns/get/output_meter", returns_get_meter)

        add("/live/arrangement/duplicate_clip", arrangement_duplicate_clip)
        add("/live/arrangement/get/clips", arrangement_get_clips)
        add("/live/arrangement/delete_clip", arrangement_delete_clip)
        add("/live/arrangement/clear_track", arrangement_clear_track)
        def show_session(params: Optional[Tuple] = ()) -> Tuple:
            import Live
            Live.Application.get_application().view.show_view("Session")
            return ("Session",)

        add("/live/view/show_session", show_session)
        add("/live/view/show_arranger", show_arranger)

        # ---- drum rack ----------------------------------------------------
        def drumrack_get_pads(params: Optional[Tuple] = ()) -> Tuple:
            """params: track_index, device_index -> (note, name, chain_sayisi)*

            SADECE dolu pad'leri dondurur. get_drum_map Live'in *standart*
            eslemesini verir; bu, yuklu rack'in gercekten ne caldigini. Fark
            sessiz bir pattern olarak ortaya cikar ve hata vermez, o yuzden
            pattern yazmadan once buna bak.
            """
            track = self.song.tracks[int(params[0])]
            device = track.devices[int(params[1])]
            if not getattr(device, "can_have_drum_pads", False):
                raise ValueError("Device bir drum rack degil: %s" % device.name)
            out = []
            for pad in device.drum_pads:
                count = len(pad.chains)
                if count:
                    out += [pad.note, pad.name, count]
            return (params[0], params[1]) + tuple(out)

        add("/live/drumrack/get/pads", drumrack_get_pads)

        # ---- return kanal device'lari -------------------------------------
        def _return_device(return_index, device_index):
            return self.song.return_tracks[int(return_index)].devices[int(device_index)]

        def returns_get_devices_name(params: Optional[Tuple] = ()) -> Tuple:
            devices = self.song.return_tracks[int(params[0])].devices
            return (params[0],) + tuple(d.name for d in devices)

        def returns_get_devices_class_name(params: Optional[Tuple] = ()) -> Tuple:
            devices = self.song.return_tracks[int(params[0])].devices
            return (params[0],) + tuple(d.class_name for d in devices)

        def returns_get_parameters_name(params: Optional[Tuple] = ()) -> Tuple:
            device = _return_device(params[0], params[1])
            return (params[0], params[1]) + tuple(p.name for p in device.parameters)

        def returns_get_parameters_value(params: Optional[Tuple] = ()) -> Tuple:
            device = _return_device(params[0], params[1])
            return (params[0], params[1]) + tuple(p.value for p in device.parameters)

        def returns_get_parameters_min(params: Optional[Tuple] = ()) -> Tuple:
            device = _return_device(params[0], params[1])
            return (params[0], params[1]) + tuple(p.min for p in device.parameters)

        def returns_get_parameters_max(params: Optional[Tuple] = ()) -> Tuple:
            device = _return_device(params[0], params[1])
            return (params[0], params[1]) + tuple(p.max for p in device.parameters)

        def returns_set_parameter_value(params: Optional[Tuple] = ()) -> Tuple:
            device = _return_device(params[0], params[1])
            parameter = device.parameters[int(params[2])]
            parameter.value = float(params[3])
            return (params[0], params[1], params[2], parameter.value)

        def returns_get_parameter_value_string(params: Optional[Tuple] = ()) -> Tuple:
            device = _return_device(params[0], params[1])
            parameter = device.parameters[int(params[2])]
            return (params[0], params[1], params[2], str(parameter))

        add("/live/returns/get/devices/name", returns_get_devices_name)
        add("/live/returns/get/devices/class_name", returns_get_devices_class_name)
        add("/live/returns/get/device/parameters/name", returns_get_parameters_name)
        add("/live/returns/get/device/parameters/value", returns_get_parameters_value)
        add("/live/returns/get/device/parameters/min", returns_get_parameters_min)
        add("/live/returns/get/device/parameters/max", returns_get_parameters_max)
        add("/live/returns/set/device/parameter/value", returns_set_parameter_value)
        add("/live/returns/get/device/parameter/value_string",
            returns_get_parameter_value_string)


        # ---- session slot envanteri ---------------------------------------
        def track_get_clip_slots(params: Optional[Tuple] = ()) -> Tuple:
            """params: track_index -> (slot, isim, uzunluk) ucluleri (dolu olanlar)

            Hangi slotta ne var, tek cagriyla. Slot slot has_clip sorgulamaya
            gerek kalmaz.
            """
            track = self.song.tracks[int(params[0])]
            out = []
            for i, slot in enumerate(track.clip_slots):
                if slot.has_clip:
                    out += [i, slot.clip.name, slot.clip.length]
            return (params[0],) + tuple(out)

        add("/live/track/get/clip_slots", track_get_clip_slots)
