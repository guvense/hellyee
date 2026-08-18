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

    if args.keep:
        print(f"\nTest kanali birakildi (index {idx}).")
    else:
        core.delete_track(osc, idx)
        print("\nTest kanali silindi.")
    return 0 if ok else 1


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
