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

        add("/live/arrangement/duplicate_clip", arrangement_duplicate_clip)
        add("/live/arrangement/get/clips", arrangement_get_clips)
        add("/live/arrangement/delete_clip", arrangement_delete_clip)
        add("/live/arrangement/clear_track", arrangement_clear_track)
        add("/live/view/show_arranger", show_arranger)
