"""AbletonOSC ile konusan ince bir OSC istemcisi.

AbletonOSC 11000 portunda komut dinler, cevaplari 11001'e gonderir.
Cevap adresi istegin adresiyle ayni gelir (ornek: /live/song/get/tempo).
"""
from __future__ import annotations

import os
import queue
import threading

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient


class AbletonOSCError(RuntimeError):
    pass


class AbletonOSC:
    def __init__(self, host=None, send_port=None, recv_port=None):
        self.host = host or os.getenv("ABLETON_OSC_HOST", "127.0.0.1")
        self.send_port = int(send_port or os.getenv("ABLETON_OSC_SEND_PORT", 11000))
        self.recv_port = int(recv_port or os.getenv("ABLETON_OSC_RECV_PORT", 11001))

        self._client = SimpleUDPClient(self.host, self.send_port)
        self._waiters: dict[str, queue.Queue] = {}
        self._lock = threading.Lock()
        self._last_error: str | None = None

        dispatcher = Dispatcher()
        dispatcher.set_default_handler(self._on_message)
        self._server = ThreadingOSCUDPServer(("0.0.0.0", self.recv_port), dispatcher)
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    # --- ic isleyis -------------------------------------------------------
    def _on_message(self, address: str, *args):
        if address == "/live/error":
            self._last_error = " ".join(str(a) for a in args)
        with self._lock:
            waiter = self._waiters.get(address)
        if waiter is not None:
            waiter.put(args)

    # --- genel API --------------------------------------------------------
    def send(self, address: str, *args) -> None:
        """Cevap beklemeden komut gonderir."""
        self._last_error = None
        self._client.send_message(address, list(args))

    def query(self, address: str, *args, timeout: float = 4.0):
        """Komut gonderir ve ayni adresten donen cevabi bekler."""
        waiter: queue.Queue = queue.Queue()
        with self._lock:
            self._waiters[address] = waiter
        try:
            self.send(address, *args)
            try:
                return waiter.get(timeout=timeout)
            except queue.Empty:
                if self._last_error:
                    raise AbletonOSCError(self._last_error)
                raise AbletonOSCError(
                    f"{address} icin cevap gelmedi. Ableton acik mi ve "
                    "AbletonOSC kontrol yuzeyi secili mi?"
                )
        finally:
            with self._lock:
                self._waiters.pop(address, None)

    def ping(self) -> bool:
        try:
            self.query("/live/test", timeout=2.0)
            return True
        except AbletonOSCError:
            return False
