"""Tek komutluk kurulum: AbletonOSC indir, yamala, Claude'a bagla.

Kullanici tarafinda geriye tek elle yapilan adim kaliyor: Live'in
ayarlarindan AbletonOSC'u Control Surface olarak secmek. Live bunun icin
API sunmuyor.
"""
from __future__ import annotations

import json
import platform
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ABLETONOSC_ZIP = "https://github.com/ideoforms/AbletonOSC/archive/refs/heads/master.zip"

REMOTE_SCRIPT_DIRS = {
    "Darwin": Path.home() / "Music/Ableton/User Library/Remote Scripts",
    "Windows": Path.home() / "Documents/Ableton/User Library/Remote Scripts",
}

CLAUDE_DESKTOP_CONFIG = {
    "Darwin": Path.home() / "Library/Application Support/Claude/claude_desktop_config.json",
    "Windows": Path.home() / "AppData/Roaming/Claude/claude_desktop_config.json",
    "Linux": Path.home() / ".config/Claude/claude_desktop_config.json",
}


def _say(step: str, detail: str = "") -> None:
    print(f"  {step:<34} {detail}")


# --------------------------------------------------------------------------
def remote_scripts_dir() -> Path:
    system = platform.system()
    if system not in REMOTE_SCRIPT_DIRS:
        raise SystemExit(
            f"Ableton Live {system} uzerinde calismiyor. hellyee macOS veya "
            "Windows gerektirir."
        )
    return REMOTE_SCRIPT_DIRS[system]


def install_abletonosc(force: bool = False) -> Path:
    """AbletonOSC'u indirir ve Remote Scripts altina acar. git gerekmez."""
    dest_root = remote_scripts_dir()
    dest = dest_root / "AbletonOSC"

    if dest.exists() and not force:
        _say("AbletonOSC", "zaten kurulu")
        return dest

    dest_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "abletonosc.zip"
        _say("AbletonOSC indiriliyor", "github.com/ideoforms/AbletonOSC")
        try:
            urllib.request.urlretrieve(ABLETONOSC_ZIP, archive)
        except Exception as exc:
            raise SystemExit(f"Indirme basarisiz: {exc}\nElle kurun: {ABLETONOSC_ZIP}")

        with zipfile.ZipFile(archive) as zf:
            zf.extractall(tmp)
        extracted = next(Path(tmp).glob("AbletonOSC-*"))
        if dest.exists():
            shutil.rmtree(dest)
        shutil.move(str(extracted), str(dest))

    _say("AbletonOSC kuruldu", str(dest))
    return dest


# --------------------------------------------------------------------------
def patch_source_dir() -> Path:
    """Yama dosyalari: once kurulu pakette, sonra repo agacinda."""
    packaged = Path(__file__).resolve().parent / "_patch"
    if (packaged / "browser.py").exists():
        return packaged
    repo = Path(__file__).resolve().parent.parent / "abletonosc_patch"
    if (repo / "browser.py").exists():
        return repo
    raise SystemExit("Yama dosyalari bulunamadi (abletonosc_patch/).")


def _insert_after(path: Path, anchor: str, addition: str, marker: str) -> bool:
    text = path.read_text()
    if marker in text:
        return False
    if anchor not in text:
        raise SystemExit(
            f"{path.name} beklenen satiri icermiyor:\n  {anchor}\n"
            "AbletonOSC surumu degismis olabilir."
        )
    path.write_text(text.replace(anchor, anchor + addition, 1))
    return True


def apply_patch(root: Path) -> None:
    """browser + master handler'larini AbletonOSC'a ekler. Idempotent."""
    if not (root / "manager.py").exists():
        raise SystemExit(f"AbletonOSC bulunamadi: {root}")

    source = patch_source_dir()
    changed = 0
    for filename, handler in (("browser.py", "BrowserHandler"),
                              ("master.py", "MasterHandler")):
        shutil.copy2(source / filename, root / "abletonosc" / filename)
        stem = filename[:-3]
        changed += _insert_after(
            root / "abletonosc" / "__init__.py",
            "from .midimap import MidiMapHandler",
            f"\nfrom .{stem} import {handler}", handler)
        changed += _insert_after(
            root / "manager.py",
            "                abletonosc.MidiMapHandler(self),",
            f"\n                abletonosc.{handler}(self),",
            f"abletonosc.{handler}(self)")
        changed += _insert_after(
            root / "manager.py",
            "            importlib.reload(abletonosc.view)",
            f"\n            importlib.reload(abletonosc.{stem})",
            f"importlib.reload(abletonosc.{stem})")

    _say("Yama uygulandi", "browser + master + arrangement"
         if changed else "zaten yamali")


# --------------------------------------------------------------------------
def _server_entry() -> dict:
    """Bu kurulumu calistiracak komut."""
    return {"command": sys.executable, "args": ["-m", "hellyee.mcp_server"]}


def skill_source() -> Path | None:
    """SKILL.md: once kurulu pakette, sonra repo agacinda."""
    packaged = Path(__file__).resolve().parent / "_skill" / "SKILL.md"
    if packaged.exists():
        return packaged
    repo = (Path(__file__).resolve().parent.parent
            / ".claude" / "skills" / "hellyee" / "SKILL.md")
    return repo if repo.exists() else None


def install_skill(project_dir: Path | None = None) -> Path | None:
    """Claude'a araclarin nasil kullanilacagini ogreten skill'i kurar.

    .mcp.json ile ayni yere, projeye ozel olarak yazilir.
    """
    source = skill_source()
    if source is None:
        _say("Skill", "kaynak bulunamadi, atlandi")
        return None
    target = (project_dir or Path.cwd()) / ".claude" / "skills" / "hellyee" / "SKILL.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    _say("Skill kuruldu", str(target))
    return target


def configure_claude_code(project_dir: Path | None = None) -> Path:
    target = (project_dir or Path.cwd()) / ".mcp.json"
    config = {}
    if target.exists():
        try:
            config = json.loads(target.read_text())
        except json.JSONDecodeError:
            pass
    config.setdefault("mcpServers", {})["hellyee"] = _server_entry()
    target.write_text(json.dumps(config, indent=2) + "\n")
    _say("Claude Code yapilandirildi", str(target))
    return target


def configure_claude_desktop() -> Path:
    system = platform.system()
    target = CLAUDE_DESKTOP_CONFIG.get(system)
    if target is None:
        raise SystemExit(f"Claude Desktop yolu bilinmiyor: {system}")
    target.parent.mkdir(parents=True, exist_ok=True)
    config = {}
    if target.exists():
        try:
            config = json.loads(target.read_text())
        except json.JSONDecodeError:
            print(f"  UYARI: {target} okunamadi, ustune yazilmayacak.")
            raise SystemExit(1)
    config.setdefault("mcpServers", {})["hellyee"] = _server_entry()
    target.write_text(json.dumps(config, indent=2) + "\n")
    _say("Claude Desktop yapilandirildi", str(target))
    return target


# --------------------------------------------------------------------------
def run(client: str = "code", force: bool = False) -> int:
    print("\nhellyee kurulumu\n")
    root = install_abletonosc(force=force)
    apply_patch(root)

    if client in ("code", "both"):
        configure_claude_code()
        install_skill()
    if client in ("desktop", "both"):
        configure_claude_desktop()

    print(f"""
Otomatik kisim bitti. Geriye tek elle adim kaldi — Live bunun icin
API sunmuyor:

  1. Ableton Live'i KAPAT ve tekrar AC
     (Remote Script'ler sadece acilista taranir)

  2. Ayarlari ac
       Live 12:  Settings > Link, Tempo & MIDI
       Live 11:  Preferences > Link/Tempo/MIDI
       kisayol:  {'Cmd' if platform.system() == 'Darwin' else 'Ctrl'} + ,

  3. Control Surface tablosunda bos bir satira AbletonOSC sec
     Input ve Output None kalsin (ag uzerinden konusur, MIDI portu degil)

  4. Live'in alt seridinde sunu gormelisin:
       AbletonOSC: Listening for OSC on port 11000

Sonra dogrula:

  hellyee doctor
""")
    return 0
