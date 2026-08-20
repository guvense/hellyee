"""automate_arrangement regresyon testleri.

Iki hata icin yazildi; ikisi de bir supurmeyi 16 bardan 24 bara uzatirken
ortaya cikti (core.py, slot ayirma ve yeniden kullanim yolu):

1. Slot ayirma `next_slot + offset` kullaniyordu. Varyantlarin bir kismi
   zaten varken yenisi gerektiginde offset sahne listesinin sonunu asiyor
   ve arkasinda sahne olmayan bir slot isteniyordu -> "Index out of range".
2. Yeniden kullanilan varyantin eski zarfi silinmiyordu. Yamadaki
   insert_step birikimli calisir, dolayisiyla eski adimlar yerinde kalirdi.

Calistirmak icin:  .venv/bin/python -m unittest discover -s tests -t .
"""
from __future__ import annotations

import unittest

from hellyee.core import automate_arrangement
from hellyee.osc import AbletonOSCError

from .fake_live import STEP, FakeLive

TRACK = 7
DEVICE = 0
CUTOFF = 1          # "Filter Cutoff" parametre indeksi
CUTOFF_MAX = 127.0

PARAMS = [
    {"name": "Device On", "value": 1.0, "min": 0.0, "max": 1.0},
    {"name": "Filter Cutoff", "value": 52.0, "min": 0.0, "max": CUTOFF_MAX},
    {"name": "Reverb", "value": 54.61, "min": 0.0, "max": CUTOFF_MAX},
]

NOTES = [{"pitch": 58, "start": 0.0, "duration": 8.0, "velocity": 90, "mute": 0}]


def pad_set() -> FakeLive:
    """Hatayi ureten setin sadelestirilmis hali.

    6 sahne, session slot 0-5 dolu, aranjmanda bar 96 ve 104'te birer
    varyant, bar 112'de varyanti olmayan bir klip. 96->120 supurmesi ucunu
    birden kapsar: ikisi yeniden kullanilir, ucuncusu yeni slot ister.
    """
    live = FakeLive(num_scenes=6)
    live.add_device(TRACK, DEVICE, PARAMS)
    live.add_session_clip(TRACK, 0, "PAD prog 8", 32.0)
    live.add_session_clip(TRACK, 1, "PAD Bbm 8", 32.0)
    live.add_session_clip(TRACK, 2, "PAD break 8", 32.0)
    live.add_session_clip(TRACK, 3, "PAD build 8", 32.0, notes=NOTES)
    live.add_session_clip(TRACK, 4, "PAD break 8 ~b96", 32.0)
    live.add_session_clip(TRACK, 5, "PAD break 8 ~b104", 32.0)

    live.place(TRACK, 1, 352.0)     # bar 88  - supurmenin disinda
    live.place(TRACK, 4, 384.0)     # bar 96  - mevcut varyant
    live.place(TRACK, 5, 416.0)     # bar 104 - mevcut varyant
    live.place(TRACK, 3, 448.0)     # bar 112 - varyanti yok
    live.place(TRACK, 0, 480.0)     # bar 120 - supurmenin disinda
    return live


SWEEP = [{"bar": 96, "percent": 14},
         {"bar": 104, "percent": 32},
         {"bar": 120, "percent": 84}]


def run_sweep(live, points=None):
    return automate_arrangement(live, TRACK, DEVICE, "Filter Cutoff",
                                points or SWEEP)


class SlotAllocation(unittest.TestCase):
    """Hata 1: offsetli slot ayirma var olmayan sahneye yaziyordu."""

    def test_sweep_across_a_new_placement_does_not_raise(self):
        live = pad_set()
        # Duzeltmeden once burasi AbletonOSCError("Index out of range")
        # atiyordu: slot 6 yerine 8 isteniyordu, 8. sahne yok.
        run_sweep(live)

    def test_new_variant_lands_in_the_next_free_slot(self):
        live = pad_set()
        run_sweep(live)
        slots = live.slots[TRACK]
        self.assertIn(6, slots, "yeni varyant slot 6'ya acilmaliydi")
        self.assertEqual(slots[6].name, "PAD build 8 ~b112")
        self.assertNotIn(7, slots, "bosluk birakilmamali")
        self.assertNotIn(8, slots, "offsetli eski davranis geri gelmis")

    def test_exactly_one_scene_is_added(self):
        live = pad_set()
        self.assertEqual(live.num_scenes, 6)
        run_sweep(live)
        self.assertEqual(live.num_scenes, 7)

    def test_all_new_variants_get_consecutive_slots(self):
        """Hicbir varyant yokken ucu de yeni: 6, 7, 8 ve uc sahne."""
        live = pad_set()
        # Varyantlari sokup yerlerine kaynak klipleri koy.
        del live.slots[TRACK][4]
        del live.slots[TRACK][5]
        live.arrangement[TRACK] = []
        live.place(TRACK, 2, 384.0)
        live.place(TRACK, 2, 416.0)
        live.place(TRACK, 3, 448.0)

        run_sweep(live)

        slots = live.slots[TRACK]
        self.assertEqual(slots[4].name, "PAD break 8 ~b96")
        self.assertEqual(slots[5].name, "PAD break 8 ~b104")
        self.assertEqual(slots[6].name, "PAD build 8 ~b112")
        self.assertEqual(live.num_scenes, 7)

    def test_new_variant_copies_the_source_clip_notes(self):
        live = pad_set()
        run_sweep(live)
        self.assertEqual(live.slots[TRACK][6].notes, NOTES)


class EnvelopeReuse(unittest.TestCase):
    """Hata 2: yeniden kullanilan varyantta zarf temizlenmiyordu."""

    def _calls(self, live, address, slot):
        return [i for i, (addr, args) in enumerate(live.calls)
                if addr == address and len(args) > 1 and int(args[1]) == slot]

    def test_reused_variant_is_cleared_before_it_is_rewritten(self):
        live = pad_set()
        run_sweep(live)
        for slot in (4, 5):
            cleared = self._calls(live, "/live/clip/clear_automation", slot)
            written = self._calls(live, "/live/clip/automate", slot)
            self.assertTrue(cleared, f"slot {slot} temizlenmedi")
            self.assertTrue(written, f"slot {slot} yazilmadi")
            self.assertLess(min(cleared), min(written),
                            f"slot {slot}: temizleme yazmadan sonra gelmis")

    def test_fresh_variant_is_not_cleared(self):
        live = pad_set()
        run_sweep(live)
        self.assertFalse(self._calls(live, "/live/clip/clear_automation", 6),
                         "yeni acilan klipte temizlenecek zarf yok")

    def test_stale_steps_do_not_survive_a_rewrite(self):
        """Birikimin gozlenebildigi hal: izgaraya oturmayan eski adimlar.

        insert_step ayni zamana yazinca uzerine yazar, baska bir zamandaki
        adim yerinde kalir. Kesirli bar'la yazilan bir supurme 0.125'lik
        izgaranin disina adim koyar; ardindan hizali bir supurme bunlari
        ustune yazamaz. Temizleme olmadan zarf iki katina cikar.
        """
        live = pad_set()
        run_sweep(live, [{"bar": 96.01, "percent": 10},
                         {"bar": 104, "percent": 50}])
        run_sweep(live, [{"bar": 96, "percent": 14},
                         {"bar": 104, "percent": 32}])

        env = live.slots[TRACK][4].envelopes[(DEVICE, CUTOFF)]
        off_grid = [t for t in env if abs(t / STEP - round(t / STEP)) > 1e-9]
        self.assertEqual(off_grid, [],
                         "eski kesirli adimlar zarfta kalmis")
        self.assertEqual(len(env), 257,
                         "zarfta tam olarak 0..32 arasi 0.125'lik izgara olmali")


class Placement(unittest.TestCase):
    """Silme/yerlestirme sirasi ve kapsam disinda kalan klipler."""

    def test_placements_keep_their_original_beats(self):
        live = pad_set()
        run_sweep(live)
        clips = live.arrangement_clips(TRACK)
        self.assertEqual([c.start for c in clips],
                         [352.0, 384.0, 416.0, 448.0, 480.0])
        self.assertEqual([c.name for c in clips],
                         ["PAD Bbm 8",
                          "PAD break 8 ~b96",
                          "PAD break 8 ~b104",
                          "PAD build 8 ~b112",
                          "PAD prog 8"])

    def test_old_placements_are_deleted_high_index_first(self):
        """Silmek indeksleri kaydirir; asagidan silmek yanlis klibi goturur."""
        live = pad_set()
        run_sweep(live)
        deleted = [int(args[1]) for addr, args in live.calls
                   if addr == "/live/arrangement/delete_clip"]
        self.assertEqual(deleted, sorted(deleted, reverse=True))
        self.assertEqual(deleted, [3, 2, 1])

    def test_clips_outside_the_span_are_untouched(self):
        live = pad_set()
        before = {c.start: c.name for c in live.arrangement_clips(TRACK)}
        run_sweep(live)
        after = {c.start: c.name for c in live.arrangement_clips(TRACK)}
        for beat in (352.0, 480.0):
            self.assertEqual(after[beat], before[beat])

    def test_span_must_cover_at_least_one_clip(self):
        live = pad_set()
        with self.assertRaises(ValueError):
            run_sweep(live, [{"bar": 8, "percent": 10},
                             {"bar": 16, "percent": 90}])

    def test_max_clips_guards_runaway_variant_creation(self):
        live = pad_set()
        with self.assertRaises(ValueError):
            automate_arrangement(live, TRACK, DEVICE, "Filter Cutoff",
                                 SWEEP, max_clips=2)


class EnvelopeValues(unittest.TestCase):
    """Yazilan egri Live'da olculen degerlerle ayni mi.

    Referans olcumler Live 11'de set_playhead + list_device_parameters ile
    alindi: bar 112 -> %58.0, bar 116 -> %71.0, bar 120 -> %84.0.
    """

    def _arrangement_env(self, live, start_beat):
        clip = next(c for c in live.arrangement_clips(TRACK)
                    if c.start == start_beat)
        return clip.envelopes[(DEVICE, CUTOFF)]

    def test_build_clip_starts_where_the_ramp_left_off(self):
        live = pad_set()
        run_sweep(live)
        env = self._arrangement_env(live, 448.0)
        self.assertAlmostEqual(env[0.0] / CUTOFF_MAX * 100, 58.0, places=3)
        self.assertAlmostEqual(env[16.0] / CUTOFF_MAX * 100, 71.0, places=3)
        self.assertAlmostEqual(env[32.0] / CUTOFF_MAX * 100, 84.0, places=3)

    def test_sweep_reaches_the_top_only_on_the_last_bar(self):
        live = pad_set()
        run_sweep(live)
        top = max(max(self._arrangement_env(live, b).values())
                  for b in (384.0, 416.0, 448.0))
        self.assertAlmostEqual(top / CUTOFF_MAX * 100, 84.0, places=3)

    def test_arrangement_copies_carry_the_new_curve(self):
        """place_in_arrangement kopyayi dondurur: yerlestirme yazmadan
        sonra gelmezse aranjman eski egriyi tasir."""
        live = pad_set()
        run_sweep(live)
        for beat in (384.0, 416.0, 448.0):
            placed = self._arrangement_env(live, beat)
            slot = {384.0: 4, 416.0: 5, 448.0: 6}[beat]
            session = live.slots[TRACK][slot].envelopes[(DEVICE, CUTOFF)]
            self.assertEqual(placed, session)


if __name__ == "__main__":
    unittest.main()
