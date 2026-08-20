"""hellyee komut satiri.

  hellyee setup       AbletonOSC'u kur, yamala, Claude'a bagla
  hellyee doctor      baglantiyi ve set durumunu kontrol et
  hellyee smoke       gercek klip olusturup ucdan uca test et
"""
from __future__ import annotations

import argparse
import json
import sys

from . import core
from .osc import AbletonOSC, AbletonOSCError


def _connect() -> AbletonOSC:
    osc = AbletonOSC()
    if not osc.ping():
        print(
            "Ableton'a ulasilamadi.\n"
            "  1. Live acik mi?\n"
            "  2. Settings > Link, Tempo & MIDI > Control Surface = AbletonOSC?\n"
            "  3. 11000/11001 portlarini baska bir uygulama tutuyor olabilir.\n"
            "\nKurulum yapilmadiysa:  hellyee setup",
            file=sys.stderr)
        raise SystemExit(1)
    return osc


#: doctor'in kontrol ettigi yeni OSC route'lari — (ad, route, argumanlar).
#: Kayitli olmayan bir route hic cevap vermez; kayitli olup hata donen route
#: /live/error yollar. Ikisi de istisna atar ama mesajlari farklidir, o yuzden
#: "eksik" ile "var ama bu argumanla calismadi" ayirt edilebilir.
_CAPABILITY_PROBES = (
    ("session slot envanteri", "/live/track/get/clip_slots", (0,)),
    ("return device'lari", "/live/returns/get/devices/name", (0,)),
    ("drum pad okuma", "/live/drumrack/get/pads", (0, 0)),
)


def _probe_capabilities(osc: AbletonOSC) -> list[str]:
    """Yamanin guncel olup olmadigini kontrol eder; eksik yetenekleri dondurur."""
    missing = []
    for label, route, args in _CAPABILITY_PROBES:
        try:
            osc.query(route, *args, timeout=2.0)
        except AbletonOSCError as exc:
            #------------------------------------------------------------------
            # "cevap gelmedi" = route kayitli degil (yama bayat).
            # Baska bir hata = route var, sadece bu argumanla calismadi
            # (ornek: 0. device bir drum rack degil) — sorun yok.
            #------------------------------------------------------------------
            if "cevap gelmedi" in str(exc):
                missing.append(label)
    return missing


def cmd_doctor(args) -> int:
    osc = _connect()
    print(json.dumps(core.song_status(osc), ensure_ascii=False, indent=2))

    try:
        categories = core.browser_categories(osc)
        print(f"\nBrowser handler'i kurulu ({len(categories)} kategori)")
    except AbletonOSCError:
        print("\nBrowser handler'i YOK — device yukleme calismaz.\n"
              "  hellyee setup   (ve Live'i yeniden baslat)", file=sys.stderr)
        return 1

    try:
        devices = core.master_devices(osc)
        print(f"Master handler'i kurulu ({len(devices)} device master'da)")
    except AbletonOSCError:
        print("Master handler'i YOK — mastering ve arrangement calismaz.\n"
              "  hellyee setup   (ve Live'i yeniden baslat)", file=sys.stderr)
        return 1

    missing = _probe_capabilities(osc)
    if missing:
        print("\nHandler'lar BAYAT — su yetenekler eksik: "
              + ", ".join(missing) + "\n"
              "  hellyee setup   (Live'i yeniden baslatmaya gerek yok, "
              "yama /live/api/reload ile tazelenir)", file=sys.stderr)
        return 1
    print("Yeni yetenekler kurulu (drum pad, session slot, return device, "
          "aranjman otomasyonu)")

    try:
        import librosa  # noqa: F401
        print("Ses ozellikleri kurulu")
    except ImportError:
        print("Ses ozellikleri kurulu degil (istege bagli)\n"
              '  pip install "hellyee[audio]"')
    print("\nHer sey hazir.")
    return 0


def cmd_smoke(args) -> int:
    osc = _connect()
    track = core.create_track(osc, "midi", -1, "hellyee smoke test")
    idx = track["index"]
    print(f"kanal {idx} acildi")

    core.create_clip(osc, idx, 0, 4.0, "test")
    core.add_notes(osc, idx, 0, [
        {"pitch": 60, "start": 0.02, "duration": 0.5},
        {"pitch": 64, "start": 1.01, "duration": 0.5},
        {"pitch": 67, "start": 1.97, "duration": 0.5},
        {"pitch": 72, "start": 3.03, "duration": 0.5},
    ])
    notes = core.get_notes(osc, idx, 0)
    print(f"klipte {len(notes)} nota okundu")

    print(core.quantize_clip(osc, idx, 0, grid=0.25))
    after = core.get_notes(osc, idx, 0)
    print(f"quantize sonrasi baslangiclar: {[n['start'] for n in after]}")
    ok = len(after) == len(notes)
    if not ok:
        print("UYARI: quantize nota sayisini degistirdi", file=sys.stderr)

    try:
        core.load_device(osc, idx, "instruments", "Operator")
        print("device yuklendi:", [d["name"] for d in core.list_devices(osc, idx)])
    except AbletonOSCError as exc:
        print(f"device yukleme basarisiz: {exc}", file=sys.stderr)
        ok = False

    ok = _smoke_new_features(osc, idx) and ok

    if args.keep:
        print(f"\nTest kanali birakildi (index {idx}).")
    else:
        core.delete_track(osc, idx)
        print("\nTest kanali silindi.")
    return 0 if ok else 1


def _smoke_new_features(osc: AbletonOSC, idx: int) -> bool:
    """Yeni yeteneklerin ucdan uca testi. Sadece test kanalina dokunur."""
    ok = True

    def step(label, fn):
        nonlocal ok
        try:
            print(f"  {label}: {fn()}")
        except Exception as exc:
            print(f"  {label}: BASARISIZ — {exc}", file=sys.stderr)
            ok = False

    print("\nyeni yetenekler:")
    step("session slotlari",
         lambda: [c["name"] for c in core.session_clips(osc, idx)])
    step("playhead", lambda: core.set_playhead(osc, 0))
    step("loop", lambda: core.set_loop(osc, 0, 4, enabled=False))
    step("aranjman sonu", lambda: core.arrangement_end_bar(osc))
    step("return device'lari",
         lambda: [d["name"] for d in core.list_return_devices(osc, 0)])
    step("birim farkindalikli parametre",
         lambda: core.set_device_parameter(osc, idx, 0, "Filter Freq", hz=2000))
    step("enum secenekleri",
         lambda: len(core.parameter_options(osc, idx, 0, "Filter Type")["options"]))

    #----------------------------------------------------------------------
    # Aranjman otomasyonu ve tazeleme: klip yerlestirmeyi gerektirir.
    #----------------------------------------------------------------------
    try:
        core.place_in_arrangement(osc, idx, 0, 0.0, repeats=4)
        step("aranjman otomasyonu", lambda: core.automate_arrangement(
            osc, idx, 0, "Filter Freq",
            [{"bar": 0, "percent": 20}, {"bar": 4, "percent": 90}]))
        step("aranjman tazeleme",
             lambda: core.refresh_arrangement_track(osc, idx))
        core.clear_arrangement_track(osc, idx)
    except Exception as exc:
        print(f"  aranjman testi BASARISIZ — {exc}", file=sys.stderr)
        ok = False

    return ok


def cmd_setup(args) -> int:
    from .setup_cli import run
    return run(client=args.client, force=args.force)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="hellyee",
        description="Ableton Live'i Claude uzerinden kontrol et")
    sub = parser.add_subparsers(dest="command")

    p_setup = sub.add_parser("setup", help="AbletonOSC'u kur, yamala, Claude'a bagla")
    p_setup.add_argument("--client", choices=["code", "desktop", "both"],
                         default="code", help="hangi Claude istemcisi (varsayilan: code)")
    p_setup.add_argument("--force", action="store_true",
                         help="AbletonOSC kuruluysa bile yeniden indir")
    p_setup.set_defaults(func=cmd_setup)

    p_doctor = sub.add_parser("doctor", help="baglantiyi ve kurulumu kontrol et")
    p_doctor.set_defaults(func=cmd_doctor)

    p_smoke = sub.add_parser("smoke", help="ucdan uca test (gercek klip olusturur)")
    p_smoke.add_argument("--keep", action="store_true",
                         help="test kanalini silme")
    p_smoke.set_defaults(func=cmd_smoke)

    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        return cmd_doctor(args)          # arguman yoksa doctor
    try:
        return args.func(args)
    except AbletonOSCError as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
