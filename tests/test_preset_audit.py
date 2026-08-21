"""Preset denetimi testleri.

Bir preseti ismine bakarak secip sete koymanin maliyeti olculdu: yuklenen
lead enerjisinin %94.8'ini tek bantta tutuyordu, cunku patch'te IKI filtre
vardi ve ikincisi ~590 Hz'de duruyordu. Ilk filtreyi acmak hicbir sey
degistirmedi. Buradaki esikler ve uyari metni o olcumden geliyor.

Calistirmak icin:  .venv/bin/python -m unittest discover -s tests -t .
"""
from __future__ import annotations

import unittest

from hellyee import core

from .fake_live import FakeLive

TRACK = 7


def param(name, display, value=0.5):
    return {"name": name, "value": value, "min": 0.0, "max": 1.0,
            "display": display}


# Gercek olcumler: bant dagilimi + crest.
MEASURED = {
    "lead_bogulmus": ({"lowmid_250_800": 94.8, "mid_800_2500": 5.1,
                       "high_2500_8000": 0.0, "air_>8000": 0.0}, 2.8),
    "lead_duzeltilmis": ({"lowmid_250_800": 61.4, "mid_800_2500": 26.9,
                          "high_2500_8000": 11.5, "air_>8000": 0.2}, 3.6),
    "stab_saglikli": ({"bass_60_250": 9.8, "lowmid_250_800": 61.3,
                       "mid_800_2500": 26.8, "high_2500_8000": 2.0,
                       "air_>8000": 0.0}, 18.2),
    "pluck": ({"lowmid_250_800": 48.7, "mid_800_2500": 49.1,
               "high_2500_8000": 2.1, "air_>8000": 0.0}, 13.2),
}


def analysis(key):
    bands, crest = MEASURED[key]
    return {"band_energy_pct": bands, "crest_ratio": crest}


class Verdict(unittest.TestCase):
    """audition_verdict saf fonksiyon; gercek olcumlerle ayirt edebilmeli."""

    def test_strangled_patch_is_flagged(self):
        notes = core.audition_verdict(analysis("lead_bogulmus"))
        self.assertEqual(len(notes), 3, f"beklenen 3 bulgu, gelen: {notes}")
        joined = " ".join(notes)
        self.assertIn("tek bantta", joined)
        self.assertIn("2.5 kHz", joined)

    def test_healthy_sounds_are_not_flagged(self):
        for key in ("lead_duzeltilmis", "stab_saglikli", "pluck"):
            with self.subTest(key):
                self.assertEqual(core.audition_verdict(analysis(key)), [],
                                 f"{key} yanlis yere isaretlendi")

    def test_crest_threshold_separates_broken_from_fixed(self):
        """Bogulmus 2.8, duzeltilmis 3.6 — esik ikisinin arasinda kalmali."""
        broken = core.audition_verdict(analysis("lead_bogulmus"))
        fixed = core.audition_verdict(analysis("lead_duzeltilmis"))
        self.assertTrue(any("Crest" in n for n in broken))
        self.assertFalse(any("Crest" in n for n in fixed))

    def test_empty_analysis_says_nothing(self):
        self.assertEqual(core.audition_verdict({}), [])


class CutoffWarning(unittest.TestCase):
    def test_warning_names_the_lowest_filter_not_the_first(self):
        """Seri filtrelerde en alcak olan kazanir; uyari onu gostermeli."""
        filters = [{"name": "Filter 1 Freq", "hz": 1470.0},
                   {"name": "Filter 2 Freq", "hz": 590.0}]
        warning = core._cutoff_warning(filters)
        self.assertIn("Filter 2 Freq", warning)
        self.assertNotIn("Filter 1 Freq", warning)
        self.assertIn("EN ALCAK", warning)

    def test_open_chain_produces_no_warning(self):
        filters = [{"name": "Filter 1 Freq", "hz": 5880.0},
                   {"name": "Filter 2 Freq", "hz": 12000.0}]
        self.assertIsNone(core._cutoff_warning(filters))

    def test_role_floor_is_stricter_than_the_global_floor(self):
        """3 kHz her rol icin gecerli degil: lead tabani 4 kHz."""
        filters = [{"name": "Filter 1 Freq", "hz": 3000.0}]
        self.assertIsNone(core._cutoff_warning(filters))
        warning = core._cutoff_warning(filters, core.ROLE_CUTOFF_FLOOR_HZ["lead"])
        self.assertIsNotNone(warning)
        self.assertIn("4000 Hz", warning)


class FilterReading(unittest.TestCase):
    def _live(self):
        live = FakeLive(num_scenes=4)
        live.add_device(TRACK, 0, [
            param("Device On", ""),
            param("Filter 1 Freq", "1.47 kHz"),
            param("Filter 2 Freq", "590 Hz"),
            param("Osc 1 Pos", "65 %"),
            param("Amp Attack", "0.26 ms"),
            param("LFO 1 Rate", "1/4"),
        ], name="Levitate Lead")
        return live

    def test_reads_hz_and_converts_khz(self):
        found = core.device_filters(self._live(), TRACK, 0)
        by_name = {f["name"]: f["hz"] for f in found}
        self.assertEqual(by_name, {"Filter 1 Freq": 1470.0,
                                   "Filter 2 Freq": 590.0})

    def test_non_hz_parameters_are_ignored(self):
        names = [f["name"] for f in core.device_filters(self._live(), TRACK, 0)]
        for skipped in ("Osc 1 Pos", "Amp Attack", "LFO 1 Rate", "Device On"):
            self.assertNotIn(skipped, names)

    def test_eq_eight_bands_are_not_reported_as_filters(self):
        """EQ Eight'in 16 bandi her kanalda gurultu yapardi."""
        live = FakeLive(num_scenes=4)
        live.add_device(TRACK, 0, [
            param("1 Frequency A", "120 Hz"),
            param("2 Frequency B", "800 Hz"),
            param("Frequency", "265 Hz"),
        ], name="EQ Eight")
        names = [f["name"] for f in core.device_filters(live, TRACK, 0)]
        self.assertEqual(names, ["Frequency"])

    def test_track_filters_flags_below_role_floor(self):
        result = core.track_filters(self._live(), TRACK, role="lead")
        flagged = {f["name"]: f["below_floor"] for f in result["filters"]}
        self.assertTrue(flagged["Filter 2 Freq"])
        self.assertTrue(flagged["Filter 1 Freq"], "1.47 kHz lead icin dusuk")
        self.assertEqual(result["floor_hz"], 4000.0)
        self.assertIn("warning", result)

    def test_track_filters_without_role_uses_the_global_floor(self):
        result = core.track_filters(self._live(), TRACK)
        self.assertNotIn("floor_hz", result)
        self.assertIn("Filter 2 Freq", result["warning"])


class FilterType(unittest.TestCase):
    """Tepeyi yalnizca lowpass/bandpass kapatir.

    Gercek olay: Wavetable'in Filter 1'i 1470 Hz'de bir HIGHPASS'ti ve tool
    onu "lead tabani 4 kHz altinda" diye isaretledi. Tepeyi kesen Filter 2
    (lowpass) idi. Tip okunmadan taban kiyasi yanlis alarm uretiyor.
    """

    def _live(self, kind, hz="590 Hz"):
        live = FakeLive(num_scenes=4)
        live.add_device(TRACK, 0, [
            param("Filter 1 Type", kind),
            param("Filter 1 Freq", hz),
        ], name="Wavetable")
        return live

    def test_highpass_below_the_floor_is_not_flagged(self):
        found = core.device_filters(self._live("Highpass"), TRACK, 0)
        self.assertEqual(found[0]["type"], "Highpass")
        self.assertFalse(found[0]["caps_top"])
        self.assertIsNone(core._cutoff_warning(found))

    def test_lowpass_below_the_floor_is_flagged(self):
        found = core.device_filters(self._live("Lowpass"), TRACK, 0)
        self.assertTrue(found[0]["caps_top"])
        self.assertIsNotNone(core._cutoff_warning(found))

    def test_bandpass_also_caps_the_top(self):
        found = core.device_filters(self._live("Bandpass"), TRACK, 0)
        self.assertTrue(found[0]["caps_top"])

    def test_notch_does_not_cap_the_top(self):
        found = core.device_filters(self._live("Notch"), TRACK, 0)
        self.assertFalse(found[0]["caps_top"])

    def test_unknown_type_is_assumed_to_cap(self):
        """Rack makrosunda tip parametresi yok; sessiz kalmaktansa isaretle."""
        live = FakeLive(num_scenes=4)
        live.add_device(TRACK, 0, [param("Filter Cutoff", "590 Hz")],
                        name="Dunkel Pad")
        found = core.device_filters(live, TRACK, 0)
        self.assertIsNone(found[0]["type"])
        self.assertTrue(found[0]["caps_top"])
        self.assertIsNotNone(core._cutoff_warning(found))

    def test_auto_filter_style_naming_finds_its_type(self):
        """Auto Filter: 'Frequency' ile 'Filter Type' isim onekini paylasmaz."""
        live = FakeLive(num_scenes=4)
        live.add_device(TRACK, 0, [
            param("Filter Type", "Highpass"),
            param("Frequency", "590 Hz"),
        ], name="Auto Filter")
        found = core.device_filters(live, TRACK, 0)
        self.assertEqual(found[0]["type"], "Highpass")
        self.assertFalse(found[0]["caps_top"])

    def test_mixed_chain_warns_only_about_the_lowpass(self):
        """Gercek LEAD: highpass 1470, lowpass 5880 — ikisi de lead tabani
        altinda degil, ama highpass hicbir kosulda sayilmamali."""
        live = FakeLive(num_scenes=4)
        live.add_device(TRACK, 0, [
            param("Filter 1 Type", "Highpass"),
            param("Filter 1 Freq", "1.47 kHz"),
            param("Filter 2 Type", "Lowpass"),
            param("Filter 2 Freq", "5.88 kHz"),
        ], name="Levitate Lead")
        result = core.track_filters(live, TRACK, role="lead")
        flagged = {f["name"]: f["below_floor"] for f in result["filters"]}
        self.assertFalse(flagged["Filter 1 Freq"], "highpass isaretlenmemeli")
        self.assertFalse(flagged["Filter 2 Freq"], "5.88 kHz taban ustunde")
        self.assertNotIn("warning", result)


class LoadReporting(unittest.TestCase):
    """Uyari YUKLEME aninda cikmali; saatler sonra kesfedilmemeli."""

    def test_loading_a_strangled_preset_warns_immediately(self):
        live = FakeLive(num_scenes=4)
        live.pending_preset = [param("Filter 1 Freq", "1.47 kHz"),
                               param("Filter 2 Freq", "590 Hz")]
        info = core.load_device(live, TRACK, "sounds", "Levitate Lead")
        self.assertEqual(info["loaded"], "Levitate Lead")
        self.assertIn("warning", info)
        self.assertIn("Filter 2 Freq", info["warning"])
        self.assertEqual(len(info["filters"]), 2)

    def test_loading_an_open_preset_is_quiet(self):
        live = FakeLive(num_scenes=4)
        live.pending_preset = [param("Filter 1 Freq", "8.2 kHz")]
        info = core.load_device(live, TRACK, "sounds", "Bright Lead")
        self.assertNotIn("warning", info)

    def test_a_preset_with_no_filters_reports_none(self):
        live = FakeLive(num_scenes=4)
        live.pending_preset = [param("Amp Attack", "0.26 ms")]
        info = core.load_device(live, TRACK, "sounds", "Simple")
        self.assertNotIn("filters", info)
        self.assertNotIn("warning", info)


if __name__ == "__main__":
    unittest.main()
