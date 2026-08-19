"""Live Browser handler'i — AbletonOSC'a device yukleme yetenegi ekler.

Stok AbletonOSC, Live'in Browser API'sini disari acmaz; bu dosya onu ekler.
hellyee reposundaki abletonosc_patch/ altindan gelir; orada duzenleyin
(AbletonOSC guncellenince scripts/patch_abletonosc.py'yi tekrar calistirin).

DIKKAT: Live 11'in gomulu Python'u 3.7'dir. Walrus (:=), `list[str]` tipi
ve `X | Y` union sozdizimi KULLANILAMAZ.
"""
import Live
from typing import Any, List, Optional, Tuple

from .handler import AbletonOSCHandler

#: Cok derin gezinmeyi engellemek icin (User Library devasa olabilir)
DEFAULT_MAX_DEPTH = 4
DEFAULT_MAX_RESULTS = 30


class BrowserHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "browser"

    # ----------------------------------------------------------------------
    @property
    def browser(self):
        return Live.Application.get_application().browser

    def _categories(self):
        """Browser'in ust duzey bolumleri. Live surumune gore degisebilir."""
        names = ["instruments", "drums", "audio_effects", "midi_effects",
                 "plugins", "max_for_live", "sounds", "samples", "packs",
                 "user_library", "current_project", "clips"]
        result = {}
        for name in names:
            try:
                item = getattr(self.browser, name)
            except Exception:
                continue
            if item is not None:
                result[name] = item
        return result

    @staticmethod
    def _children(item) -> List[Any]:
        try:
            return list(item.children)
        except Exception:
            return []

    @staticmethod
    def _base_name(name: str) -> str:
        """Preset uzantisini atar: 'Auto Filter.adv' -> 'auto filter'."""
        lowered = name.lower()
        for ext in (".adv", ".adg", ".alp", ".ams", ".abl"):
            if lowered.endswith(ext):
                return lowered[:-len(ext)]
        return lowered

    def _score(self, name: str, needle: str) -> int:
        """Dusuk daha iyi. Tam isim eslesmesi her zaman kazanir.

        'Delay' aramasi 'Align Delay' yerine 'Delay'i bulmali.
        """
        base = self._base_name(name)
        #----------------------------------------------------------------------
        # Arama metnini de ayni sekilde normalize et: kullanici search'ten
        # aldigi ismi ("Lit Kit.adg") dogrudan verebilmeli.
        #----------------------------------------------------------------------
        needle = self._base_name(needle)
        if not needle:
            return 3
        if base == needle:
            return 0
        if base.startswith(needle):
            return 1
        if needle in base:
            return 2
        return 4

    def _walk(self, root, query: str, max_depth: int, max_results: int) -> List[Any]:
        """Yuklenebilir ogeler icinde isme gore arama, alaka sirasiyla.

        Genislik oncelikli gezinir ama ilk bulduguyla yetinmez: aday havuzunu
        toplayip skora gore siralar, boylece tam isim eslesmesi one gecer.
        """
        needle = query.lower().strip()
        pool_limit = max(max_results * 5, 40)
        scored = []
        queue = [(root, 0)]
        while queue and len(scored) < pool_limit:
            node, depth = queue.pop(0)
            for child in self._children(node):
                try:
                    name = child.name
                    loadable = child.is_loadable
                except Exception:
                    continue
                if loadable:
                    score = self._score(name, needle)
                    if score < 4:
                        scored.append((score, depth, len(name), name, child))
                        if len(scored) >= pool_limit:
                            break
                if depth + 1 < max_depth:
                    queue.append((child, depth + 1))

        #----------------------------------------------------------------------
        # skor -> derinlik -> kisa isim. Kisa isim tercih edilir cunku duz
        # device genelde preset'ten kisadir ("Delay" < "Delay Vintage Tape").
        #----------------------------------------------------------------------
        scored.sort(key=lambda row: (row[0], row[1], row[2]))
        return [row[4] for row in scored[:max_results]]

    def _find_by_uri(self, uri: str, max_depth: int = 8):
        """URI ile tam eslesen ogeyi bulur."""
        queue = [(item, 0) for item in self._categories().values()]
        while queue:
            node, depth = queue.pop(0)
            for child in self._children(node):
                try:
                    if child.uri == uri:
                        return child
                except Exception:
                    continue
                if depth + 1 < max_depth:
                    queue.append((child, depth + 1))
        return None

    def _select_track(self, track_index: int):
        #----------------------------------------------------------------------
        # Negatif indeks master kanali demektir (mastering zinciri icin).
        #----------------------------------------------------------------------
        if track_index < 0:
            track = self.song.master_track
        else:
            track = self.song.tracks[track_index]
        self.song.view.selected_track = track
        #----------------------------------------------------------------------
        # Live yeni device'i SECILI device'in ardina koyar. Zincirin sonuna
        # eklemek icin son device'i sec; hic yoksa dokunma.
        #----------------------------------------------------------------------
        try:
            if len(track.devices) > 0:
                self.song.view.select_device(track.devices[-1])
        except Exception:
            pass
        return track

    # ----------------------------------------------------------------------
    def init_api(self):
        def get_categories(params: Optional[Tuple] = ()) -> Tuple:
            return tuple(sorted(self._categories().keys()))

        def get_items(params: Optional[Tuple] = ()) -> Tuple:
            """params: category — o bolumun dogrudan cocuklarini dondurur.

            Her oge icin dortlu: name, uri, is_folder, is_loadable
            """
            category = params[0]
            categories = self._categories()
            if category not in categories:
                raise ValueError("Bilinmeyen kategori: %s" % category)
            out = []
            for child in self._children(categories[category]):
                try:
                    out += [child.name, child.uri,
                            int(child.is_folder), int(child.is_loadable)]
                except Exception:
                    continue
            return tuple(out)

        def search(params: Optional[Tuple] = ()) -> Tuple:
            """params: category, query, [max_results], [max_depth]

            Yuklenebilir ogeler arasinda isim aramasi. Ikili dondurur:
            name, uri, name, uri, ...
            """
            category = params[0]
            query = params[1] if len(params) > 1 else ""
            max_results = int(params[2]) if len(params) > 2 else DEFAULT_MAX_RESULTS
            max_depth = int(params[3]) if len(params) > 3 else DEFAULT_MAX_DEPTH

            categories = self._categories()
            if category not in categories:
                raise ValueError("Bilinmeyen kategori: %s. Secenekler: %s"
                                 % (category, ", ".join(sorted(categories))))
            matches = self._walk(categories[category], query, max_depth, max_results)
            out = []
            for item in matches:
                out += [item.name, item.uri]
            return tuple(out)

        def load_item(params: Optional[Tuple] = ()) -> Tuple:
            """params: track_index, uri — URI'si verilen ogeyi kanala yukler."""
            track_index = int(params[0])
            uri = params[1]
            item = self._find_by_uri(uri)
            if item is None:
                raise ValueError("URI bulunamadi: %s" % uri)
            if not item.is_loadable:
                raise ValueError("Bu oge yuklenebilir degil: %s" % item.name)
            self._select_track(track_index)
            self.browser.load_item(item)
            return (track_index, item.name, uri)

        def load_device(params: Optional[Tuple] = ()) -> Tuple:
            """params: track_index, category, query

            Arar ve ILK eslesmeyi yukler. Tek adimda "su kanala Auto Filter ekle".
            """
            track_index = int(params[0])
            category = params[1]
            query = params[2] if len(params) > 2 else ""

            categories = self._categories()
            if category not in categories:
                raise ValueError("Bilinmeyen kategori: %s. Secenekler: %s"
                                 % (category, ", ".join(sorted(categories))))
            matches = self._walk(categories[category], query, DEFAULT_MAX_DEPTH, 5)
            if not matches:
                raise ValueError("'%s' icin %s altinda eslesme yok"
                                 % (query, category))
            item = matches[0]
            self._select_track(track_index)
            self.browser.load_item(item)
            return (track_index, item.name, item.uri)

        self.osc_server.add_handler("/live/browser/get/categories", get_categories)
        self.osc_server.add_handler("/live/browser/get/items", get_items)
        self.osc_server.add_handler("/live/browser/search", search)
        def load_item_to_slot(params: Optional[Tuple] = ()) -> Tuple:
            """params: track_index, slot_index, uri

            Ornegin bir sample'i belirli bir session slotuna yukler.
            Live, sample yuklerken vurgulanan klip slotunu hedefler.
            """
            track_index, slot_index, uri = int(params[0]), int(params[1]), params[2]
            item = self._find_by_uri(uri)
            if item is None:
                raise ValueError("URI bulunamadi: %s" % uri)
            track = self.song.tracks[track_index]
            self.song.view.selected_track = track
            self.song.view.highlighted_clip_slot = track.clip_slots[slot_index]
            self.browser.load_item(item)
            return (track_index, slot_index, item.name)

        self.osc_server.add_handler("/live/browser/load_item_to_slot", load_item_to_slot)
        self.osc_server.add_handler("/live/browser/load_item", load_item)
        self.osc_server.add_handler("/live/browser/load_device", load_device)
