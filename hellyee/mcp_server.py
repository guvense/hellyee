"""hellyee — Ableton Live MCP sunucusu.

Calistirma:  python -m hellyee.mcp_server   (stdio transport)

DIKKAT: stdio transport'ta stdout protokolun kendisidir.
Buraya asla print() koyma; log gerekiyorsa sys.stderr'e yaz.
"""
from __future__ import annotations

import json

from mcp.server import MCPServer

from . import core, music
from .osc import AbletonOSC

server = MCPServer("hellyee")

_osc: AbletonOSC | None = None


def osc() -> AbletonOSC:
    """Baglantiyi ilk kullanimda kurar ve surec boyunca acik tutar."""
    global _osc
    if _osc is None:
        _osc = AbletonOSC()
    return _osc


def _json(data) -> str:
    return json.dumps(data, ensure_ascii=False)


# ==========================================================================
# Baglanti
# ==========================================================================
@server.tool()
def check_connection() -> str:
    """Ableton'a OSC baglantisini test eder. Bir sey calismadiginda ilk buna bak."""
    if osc().ping():
        return "Baglanti tamam."
    return ("Ableton'a ulasilamiyor. Kontrol et: Live acik mi, "
            "Settings > Link, Tempo & MIDI > Control Surface listesinde "
            "AbletonOSC secili mi, 11000/11001 portlari bos mu.")


# ==========================================================================
# Sarki ve transport
# ==========================================================================
@server.tool()
def get_song_status() -> str:
    """Setin guncel durumunu dondurur: tempo, calma durumu, kanal listesi
    (index, isim, midi/audio).

    Herhangi bir degisiklikten ONCE bunu cagir. Kanal indekslerini buradan al,
    asla tahmin etme; kullanici arada Live'da elle degisiklik yapmis olabilir.
    """
    return _json(core.song_status(osc()))


@server.tool()
def set_tempo(bpm: float) -> str:
    """Setin temposunu degistirir (BPM)."""
    return core.set_tempo(osc(), bpm)


@server.tool()
def transport(action: str) -> str:
    """Oynatmayi kontrol eder.

    Args:
        action: "start", "stop" veya "continue".
    """
    return core.transport(osc(), action)


@server.tool()
def create_scene(index: int = -1) -> str:
    """Yeni bir scene (session gorunumunde satir) olusturur. -1 = sona ekle."""
    return core.create_scene(osc(), index)


@server.tool()
def fire_scene(scene_index: int) -> str:
    """Bir scene'i tetikler; o satirdaki tum klipler ayni anda calar."""
    return core.fire_scene(osc(), scene_index)


# ==========================================================================
# Kanallar
# ==========================================================================
@server.tool()
def create_track(kind: str = "midi", index: int = -1, name: str = "") -> str:
    """Yeni kanal acar ve olusan kanalin indeksini dondurur.

    Args:
        kind: "midi" (nota yazilacaksa) veya "audio" (ses kaydi/sample icin).
        index: Eklenecegi konum; -1 sona ekler.
        name: Kanal adi. Bos birakilirsa Live'in varsayilani kalir.
    """
    return _json(core.create_track(osc(), kind, index, name))


@server.tool()
def rename_track(track_index: int, name: str) -> str:
    """Bir kanalin adini degistirir."""
    return core.rename_track(osc(), track_index, name)


@server.tool()
def delete_track(track_index: int) -> str:
    """Bir kanali siler. Geri alinamaz; silmeden once kullaniciya dogrulat."""
    return core.delete_track(osc(), track_index)


@server.tool()
def duplicate_track(track_index: int) -> str:
    """Bir kanali icerigi ve device'lariyla birlikte kopyalar."""
    return core.duplicate_track(osc(), track_index)


@server.tool()
def set_mixer(track_index: int, volume: float | None = None,
              pan: float | None = None, mute: bool | None = None,
              solo: bool | None = None, arm: bool | None = None) -> str:
    """Kanalin mixer ayarlarini degistirir. Sadece verdigin alanlar degisir.

    Args:
        track_index: Kanal indeksi.
        volume: 0.0-1.0 arasi (0.85 civari 0 dB'dir).
        pan: -1.0 (sol) ile 1.0 (sag) arasi.
        mute: Sessize al.
        solo: Yalniz bu kanali dinle.
        arm: Kayit icin hazirla.
    """
    return core.set_mixer(osc(), track_index, volume, pan, mute, solo, arm)


# ==========================================================================
# Klipler
# ==========================================================================
@server.tool()
def create_clip(track_index: int, clip_index: int, length_beats: float,
                name: str = "") -> str:
    """Bir slotta bos MIDI klip olusturur. Nota yazmadan ONCE bu gerekir.

    Args:
        track_index: MIDI kanalinin indeksi.
        clip_index: Session gorunumundeki slot/satir indeksi (0'dan baslar).
        length_beats: Uzunluk vurus cinsinden. 4/4'te 1 bar = 4 vurus.
        name: Klip adi (opsiyonel).
    """
    return core.create_clip(osc(), track_index, clip_index, length_beats, name)


@server.tool()
def delete_clip(track_index: int, clip_index: int) -> str:
    """Bir slottaki klibi siler."""
    return core.delete_clip(osc(), track_index, clip_index)


@server.tool()
def fire_clip(track_index: int, clip_index: int) -> str:
    """Bir klibi calmaya baslatir."""
    return core.fire_clip(osc(), track_index, clip_index)


@server.tool()
def stop_clip(track_index: int, clip_index: int) -> str:
    """Calan bir klibi durdurur."""
    return core.stop_clip(osc(), track_index, clip_index)


@server.tool()
def set_clip_properties(track_index: int, clip_index: int,
                        name: str | None = None,
                        loop_start: float | None = None,
                        loop_end: float | None = None,
                        color_index: int | None = None) -> str:
    """Klip adini, loop sinirlarini veya rengini degistirir (vurus cinsinden)."""
    return core.set_clip_properties(osc(), track_index, clip_index, name,
                                    loop_start, loop_end, color_index)


# ==========================================================================
# Notalar
# ==========================================================================
@server.tool()
def get_clip_notes(track_index: int, clip_index: int) -> str:
    """Klipteki mevcut notalari dondurur.

    Var olan bir klibi duzenlemeden once mutlaka bunu cagir; ustune add_notes
    yapmak eski notalari silmez, uzerine ekler.
    """
    return _json(core.get_notes(osc(), track_index, clip_index))


@server.tool()
def add_notes(track_index: int, clip_index: int, notes: list[dict]) -> str:
    """Var olan bir klibe nota EKLER (mevcut notalar korunur).

    Args:
        track_index: Kanal indeksi.
        clip_index: Slot indeksi.
        notes: [{"pitch": 60, "start": 0.0, "duration": 0.5, "velocity": 100}]
            pitch: MIDI nota numarasi, 60 = C3 (Live gosterimi).
            start/duration: vurus cinsinden. 16'lik = 0.25, 8'lik = 0.5.
            velocity: 1-127, varsayilan 100.
    """
    return core.add_notes(osc(), track_index, clip_index, notes)


@server.tool()
def replace_clip_notes(track_index: int, clip_index: int,
                       notes: list[dict]) -> str:
    """Klipteki TUM notalari siler ve verdigin notalarla degistirir.

    Bir pattern'i bastan yazarken bunu kullan; add_notes ustune eklerdi.
    """
    return core.replace_notes(osc(), track_index, clip_index, notes)


@server.tool()
def clear_clip_notes(track_index: int, clip_index: int) -> str:
    """Klipteki tum notalari siler, klibi bos birakir."""
    return core.clear_notes(osc(), track_index, clip_index)


@server.tool()
def quantize_clip(track_index: int, clip_index: int, grid: float = 0.25,
                  strength: float = 1.0, quantize_duration: bool = False) -> str:
    """Klipteki notalari zaman izgarasina oturtur.

    Args:
        track_index: Kanal indeksi.
        clip_index: Slot indeksi.
        grid: Izgara adimi vurus cinsinden. 0.25 = 16'lik, 0.5 = 8'lik,
            1.0 = 4'luk, 0.125 = 32'lik.
        strength: 1.0 tam oturtur; 0.5 mesafenin yarisini kapatir ve insani
            zamanlamayi (groove) korur. Kaydedilmis calislarda 0.6-0.8 iyidir.
        quantize_duration: True ise nota surelerini de izgaraya yuvarlar.
    """
    return core.quantize_clip(osc(), track_index, clip_index, grid, strength,
                              quantize_duration)


# ==========================================================================
# Muzik teorisi (Live'a dokunmaz, sadece hesaplar)
# ==========================================================================
@server.tool()
def get_scale_notes(root: str, scale: str = "major", low: str = "C2",
                    high: str = "C5") -> str:
    """Bir tondaki nota numaralarini dondurur. Melodi yazarken once bunu al.

    Args:
        root: Ton merkezi, ornek "C", "F#", "Bb".
        scale: major, minor, harmonic_minor, melodic_minor, dorian, phrygian,
            lydian, mixolydian, locrian, pentatonic_major, pentatonic_minor,
            blues, chromatic.
        low: Alt sinir, ornek "C2".
        high: Ust sinir, ornek "C5".
    """
    pitches = music.scale_pitches(root, scale, low, high)
    return _json({"scale": f"{root} {scale}", "pitches": pitches,
                  "names": music.spell(pitches, root, scale)})


@server.tool()
def get_chord_notes(root: str, quality: str = "maj", inversion: int = 0) -> str:
    """Bir akorun nota numaralarini dondurur.

    Args:
        root: Kok nota, oktavla birlikte, ornek "C3", "F#2".
        quality: maj, min, dim, aug, sus2, sus4, maj7, min7, dom7, dim7,
            m7b5, add9, maj9, min9.
        inversion: 0 = kok pozisyon, 1 = birinci cevrim, ...
    """
    pitches = music.chord_pitches(root, quality, inversion)
    scale_hint = "minor" if quality.startswith("min") or quality in ("dim", "dim7", "m7b5") else "major"
    return _json({"chord": f"{root}{quality}", "pitches": pitches,
                  "names": music.spell(pitches, root.rstrip("0123456789-"), scale_hint)})


@server.tool()
def snap_notes_to_scale(pitches: list[int], root: str,
                        scale: str = "major") -> str:
    """Ton disi notalari en yakin ton ici notaya ceker.

    Sesten cikarilmis veya elle yazilmis notalari bir tona oturturken kullan.
    """
    fixed = music.snap_to_scale(pitches, root, scale)
    return _json({"pitches": fixed, "names": music.spell(fixed, root, scale)})


@server.tool()
def get_drum_map() -> str:
    """Live Drum Rack'inin standart nota eslemesini dondurur (kick=36 vb.).

    Davul pattern'i yazmadan once bunu al.
    """
    return _json(music.DRUM_MAP)


# ==========================================================================
# Device'lar — var olanlari kontrol et
# ==========================================================================
@server.tool()
def list_track_devices(track_index: int) -> str:
    """Bir kanaldaki device'lari (enstruman ve efektler) sirasiyla listeler.

    Parametre degistirmeden veya yeni device yuklemeden once bunu cagir.
    """
    return _json(core.list_devices(osc(), track_index))


@server.tool()
def list_device_parameters(track_index: int, device_index: int) -> str:
    """Bir device'in parametrelerini isim, guncel deger, min/max ve yuzdeyle
    listeler.

    Bir sesi degistirmeden once cagir: hangi parametrenin var oldugunu ve
    su an nerede durdugunu gorursun. "percent" alani degerin araliktaki
    yerini yuzde olarak verir.
    """
    return _json(core.list_device_parameters(osc(), track_index, device_index))


@server.tool()
def delete_device(track_index: int, device_index: int) -> str:
    """Bir device'i kanaldan kaldirir.

    Yanlis device yuklendiginde veya kullanici bir efekti kaldirmak
    istediginde kullan. Indeksleri list_track_devices'tan al; silme sonrasi
    sonraki device'larin indeksleri bir azalir.
    """
    return core.delete_device(osc(), track_index, device_index)


@server.tool()
def set_device_parameter(track_index: int, device_index: int, parameter: str,
                         value: float | None = None,
                         percent: float | None = None) -> str:
    """Bir device parametresini degistirir (filtre cutoff, rezonans, drive...).

    NEREDEYSE HER ZAMAN `percent` KULLAN. Live'in ham parametre degeri ic
    olcektedir ve ekranda gorunen birim DEGILDIR: Auto Filter'in Frequency'si
    20-135 arasindadir ama "265 Hz" olarak gorunur. Hz/dB/ms cinsinden bir
    sayiyi `value` olarak verirsen yanlis yere gider.

    value ve percent'ten SADECE BIRINI ver.

    Args:
        track_index: Kanal indeksi.
        device_index: list_track_devices'tan gelen device sirasi.
        parameter: Parametre adi ("Frequency") veya indeksi ("2"). Isim tam
            eslesmezse parcali eslesme denenir ("reso" -> "Resonance").
        percent: 0-100 arasi; parametrenin min-max araligina oturtulur.
            Tercih edilen yol. "Basi kapat" -> percent=35, "yariya indir" ->
            mevcut percent'in yarisi (once list_device_parameters ile oku).
        value: Ham ic deger. Sadece list_device_parameters ile min/max'i
            gordukten ve o olcekte dusundugunden eminsen kullan.
    """
    return core.set_device_parameter(osc(), track_index, device_index,
                                     parameter, value, percent)


# ==========================================================================
# Browser — yeni device yukle (patch'li AbletonOSC gerektirir)
# ==========================================================================
@server.tool()
def browser_categories() -> str:
    """Live browser'inin yuklenebilir bolumlerini listeler.

    Tipik: instruments, drums, audio_effects, midi_effects, plugins,
    max_for_live, sounds, samples, packs, user_library.
    """
    return _json(core.browser_categories(osc()))


@server.tool()
def search_browser(category: str, query: str = "", max_results: int = 30) -> str:
    """Browser'da yuklenebilir device/preset arar; isim ve URI dondurur.

    Ne yukleyecegini tam bilmiyorsan veya kullaniciya secenek sunacaksan
    kullan. Tek adimda yuklemek icin dogrudan load_device yeterli.

    Args:
        category: browser_categories'ten bir bolum, ornek "audio_effects".
        query: Isimde aranacak metin, ornek "Auto Filter". Bos ise ilk
            yuklenebilir ogeler doner.
        max_results: Dondurelecek en fazla sonuc.
    """
    return _json(core.browser_search(osc(), category, query, max_results))


@server.tool()
def load_device(track_index: int, category: str, query: str) -> str:
    """Bir device'i arayip kanalin device zincirinin SONUNA yukler.

    "Bu kanala Auto Filter ekle" gibi istekler icin tek adim. MIDI kanalinda
    ses cikmasi icin once bir enstruman gerekir (category="instruments");
    efektler category="audio_effects" altindadir.

    Args:
        track_index: Hedef kanal indeksi.
        category: "instruments", "audio_effects", "midi_effects", "drums",
            "plugins", "max_for_live", "sounds".
        query: Device adi, ornek "Auto Filter", "Operator", "Compressor".
    """
    return _json(core.load_device(osc(), track_index, category, query))


@server.tool()
def load_device_by_uri(track_index: int, uri: str) -> str:
    """URI'si bilinen bir browser ogesini yukler (search_browser'dan gelen).

    Ayni isimde birden fazla sonuc varsa ve kullanici belirli birini sectiyse
    bunu kullan.
    """
    return _json(core.load_item(osc(), track_index, uri))


# ==========================================================================
# Master kanali ve olcum (mastering)
# ==========================================================================
@server.tool()
def measure_track_level(track_index: int, seconds: float = 7.0) -> str:
    """Bir kanalin cikis seviyesini bir loop boyunca olcer ve tepe/ortalama dondurur.

    Bu GERCEK olcumdur, tahmin degil. Miks dengesi kurarken kullan: once olc,
    fader'i ayarla, tekrar olc. Live olcegi: 0.85 = 0 dB.

    Args:
        track_index: Kanal indeksi.
        seconds: Olcum suresi. Tum loop'u kapsamali, yoksa loop'un sadece bir
            parcasini olcersin. 150 BPM'de 4 bar = 6.4 sn.
    """
    import statistics
    import time as _t
    vals = []
    end = _t.time() + max(1.0, float(seconds))
    while _t.time() < end:
        try:
            vals.append(core.track_meter(osc(), track_index))
        except Exception:
            pass
    if not vals:
        return _json({"error": "olcum alinamadi; parca caliyor mu?"})
    return _json({"peak": round(max(vals), 4),
                  "mean": round(statistics.mean(vals), 4),
                  "samples": len(vals),
                  "note": "Live olcegi, 0.85 = 0 dB. ~10 Hz ornekleme, "
                          "transient tepeleri degil surekli seviyeyi olcer."})


@server.tool()
def list_master_devices() -> str:
    """Master kanalindaki device'lari listeler (mastering zinciri)."""
    return _json(core.master_devices(osc()))


@server.tool()
def list_master_device_parameters(device_index: int) -> str:
    """Master'daki bir device'in parametrelerini min/max ve yuzdeyle listeler."""
    return _json(core.master_device_parameters(osc(), device_index))


@server.tool()
def set_master_parameter(device_index: int, parameter: str,
                         value: float | None = None,
                         percent: float | None = None) -> str:
    """Master'daki bir device parametresini ayarlar. `percent` tercih et.

    Ham deger ekrandaki birim degildir; percent 0-100 arasi parametrenin
    kendi araligina oturur ve sonuc okunur haliyle geri doner.
    """
    return core.set_master_parameter(osc(), device_index, parameter, value, percent)


@server.tool()
def load_master_device(category: str, query: str) -> str:
    """Master kanalina device yukler — mastering zinciri kurmak icin.

    Tipik sira: EQ Eight -> Glue Compressor -> Limiter. Limiter en sonda olmali.
    """
    return _json(core.load_master_device(osc(), category, query))


@server.tool()
def get_master_meter() -> str:
    """Master cikis seviyesini okur (level, left, right). Live olcegi: 0.85 = 0 dB."""
    return _json(core.master_meter(osc()))


# ==========================================================================
# Arrangement — sarkiyi zaman cizgisinde kurmak
# ==========================================================================
@server.tool()
def place_in_arrangement(track_index: int, clip_index: int, start_bar: float,
                         repeats: int = 1) -> str:
    """Bir session klibini arrangement zaman cizgisine kopyalar.

    Sarki yapisi kurmanin yolu budur: once session'da yapi taslari olarak
    klipler yaz, sonra bunlari bolum bolum arrangement'a yerlestir.
    Klipteki otomasyon da beraberinde gider.

    Args:
        track_index: Kanal indeksi.
        clip_index: Kaynak session slotu.
        start_bar: Yerlesecegi bar (0'dan baslar). 4/4'te bar = 4 vurus.
        repeats: Kac kez arka arkaya tekrarlansin. Klip uzunlugu kadar
            araliklarla dizilir; 8 barlik bir klip repeats=4 ile 32 bar tutar.
    """
    return core.place_in_arrangement(osc(), track_index, clip_index,
                                     start_bar * 4.0, repeats)


@server.tool()
def get_arrangement_clips(track_index: int) -> str:
    """Bir kanalin arrangement kliplerini bar konumlariyla listeler.

    Var olan bir sarkinin yapisini cikarmak icin kullan: hangi bolumde hangi
    kanal caliyor, bosluklar nerede.
    """
    return _json(core.arrangement_clips(osc(), track_index))


@server.tool()
def clear_arrangement_track(track_index: int) -> str:
    """Bir kanaldaki TUM arrangement kliplerini siler. Session klipleri kalir."""
    return core.clear_arrangement_track(osc(), track_index)


@server.tool()
def delete_arrangement_clip(track_index: int, clip_index: int) -> str:
    """Arrangement'taki tek bir klibi siler (get_arrangement_clips'teki index)."""
    return core.delete_arrangement_clip(osc(), track_index, clip_index)


@server.tool()
def show_arrangement_view() -> str:
    """Live'i Arrangement gorunumune gecirir."""
    return core.show_arranger(osc())


# ==========================================================================
# Otomasyon — parametreleri zaman icinde hareket ettirmek
# ==========================================================================
@server.tool()
def automate_clip(track_index: int, clip_index: int, device_index: int,
                  parameter: str, points: list[dict]) -> str:
    """Bir SESSION klibine parametre otomasyonu yazar (filtre supurmesi vb.).

    Otomasyonu SESSION klibine yaz, sonra place_in_arrangement ile zaman
    cizgisine kopyala — envelope beraberinde gider. Live envelope'lari
    dogrudan arrangement kliplerinde olusturmaya izin vermez.

    Ayni melodinin farkli filtre hallerini ayri slotlara yazip bolumlere gore
    kullan: breakdown'da kisik, build'de acilan, drop'ta acik.

    Args:
        track_index: Kanal indeksi.
        clip_index: Session slotu (otomasyon buraya yazilir).
        device_index: list_track_devices'tan device sirasi.
        parameter: Parametre adi ("Filter 1 Freq") veya indeksi.
        points: [{"beat": 0, "percent": 30}, {"beat": 32, "percent": 95}]
            beat klip BASLANGICINA gore vurus; percent 0-100 arasi
            parametrenin kendi araligina oturur. Mutlak deger icin
            "percent" yerine "value" kullan. Aradaki degerler dogrusal
            interpolasyonla doldurulur.
    """
    return core.automate_clip(osc(), track_index, clip_index, device_index,
                              parameter, points)


@server.tool()
def clear_clip_automation(track_index: int, clip_index: int,
                          device_index: int, parameter: str) -> str:
    """Bir klipteki parametre otomasyonunu siler."""
    return core.clear_clip_automation(osc(), track_index, clip_index,
                                      device_index, parameter)


# ==========================================================================
# Send / Return kanallari (reverb-delay bus mixing)
# ==========================================================================
@server.tool()
def list_return_tracks() -> str:
    """Return kanallarini listeler (A-Reverb, B-Delay gibi) — isim, harf, seviye.

    Send ayarlamadan once cagir; kac return oldugunu ve neye gittigini gorursun.
    """
    return _json(core.list_return_tracks(osc()))


@server.tool()
def get_track_sends(track_index: int) -> str:
    """Bir kanalin send seviyelerini dondurur (hangi return'e ne kadar gidiyor)."""
    return _json(core.get_track_sends(osc(), track_index))


@server.tool()
def set_track_send(track_index: int, send: str, level: float) -> str:
    """Bir kanalin send seviyesini ayarlar — reverb/delay bus'ina gonderim.

    Insert reverb yerine send kullanmak, ayni reverb'u birden cok kanala
    paylastirir ve daha temiz miks verir. Olcumle calis: send'i ac,
    measure_track_level ile return'un doldugunu dogrula.

    Args:
        track_index: Kaynak kanal.
        send: Return harfi ("A", "B") veya indeksi.
        level: 0.0-1.0 arasi; 0.85 = 0 dB, tipik send 0.3-0.6.
    """
    param: int | str = send if send.strip().isalpha() else int(send)
    return core.set_track_send(osc(), track_index, param, level)


@server.tool()
def set_return_volume(return_index: int, level: float) -> str:
    """Bir return kanalinin ana seviyesini ayarlar (0.85 = 0 dB)."""
    return core.set_return_volume(osc(), return_index, level)


# ==========================================================================
# Ses analizi
# ==========================================================================
@server.tool()
def notes_from_audio(path: str, tempo: float = 120.0,
                     quantize: float = 0.25) -> str:
    """Bir ses dosyasindaki melodiyi MIDI notalarina cevirir.

    Kullanicinin mirildandigi/caldigi TEK SESLI kayitlar icindir; akor veya
    tam mix icin calismaz. Donen notalari add_notes ile klibe yazabilirsin.

    Args:
        path: Ses dosyasi yolu (wav, mp3, m4a).
        tempo: Setin temposu; saniyeyi vurusa cevirmek icin gerekli.
        quantize: Izgara adimi (0.25 = 16'lik); 0 verilirse ham zamanlama.
    """
    try:
        from .audio import audio_to_notes
        notes = audio_to_notes(path, tempo=tempo, quantize=quantize or None)
    except ImportError as exc:
        return _json({"error": f"Ses ozellikleri kurulu degil ({exc.name}). "
                               'Kur: pip install "hellyee[audio]"'})
    return _json([n.as_dict() for n in notes])


@server.tool()
def transcribe_audio(path: str) -> str:
    """Bir ses kaydindaki konusmayi metne cevirir (sesli komut icin).

    Args:
        path: Ses dosyasi yolu.
    """
    try:
        from .audio import transcribe
        return transcribe(path)
    except ImportError as exc:
        return (f"Ses ozellikleri kurulu degil ({exc.name}). "
                'Kur: pip install "hellyee[audio]"')


if __name__ == "__main__":
    server.run()          # stdio transport
