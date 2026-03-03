"""Motor TTS usando Microsoft Edge TTS (voces neurales) + mpg123."""

import asyncio
import queue
import threading
import time
from subprocess import DEVNULL, PIPE, Popen

import edge_tts

from src.adapters.secondary.tts.audio_cache import LruAudioCache

_VOICES: list[tuple[str, str]] = [
    ("es-MX-DaliaNeural", "Dalia — México (Neural)"),
    ("es-MX-JorgeNeural", "Jorge — México (Neural)"),
    ("es-ES-ElviraNeural", "Elvira — España (Neural)"),
    ("es-ES-AlvaroNeural", "Álvaro — España (Neural)"),
    ("es-AR-ElenaNeural", "Elena — Argentina (Neural)"),
    ("es-AR-TomasNeural", "Tomás — Argentina (Neural)"),
    ("es-CO-GonzaloNeural", "Gonzalo — Colombia (Neural)"),
    ("es-CO-SalomeNeural", "Salomé — Colombia (Neural)"),
]


class EdgeTtsEngine:
    """TTS engine con voces neurales Microsoft Edge (requiere internet)."""

    ENGINE_ID = "edge-tts"
    ENGINE_LABEL = "Edge TTS (nube — Microsoft Neural)"

    def __init__(self) -> None:
        self._voice = "es-MX-DaliaNeural"
        self._rate = 150
        self._queue: queue.Queue = queue.Queue()
        self._prefetch_queue: queue.Queue = queue.Queue()
        self._running = False
        self._thread: threading.Thread | None = None
        self._prefetch_thread: threading.Thread | None = None
        self._current_proc: Popen | None = None
        self._generation = 0
        self._busy = False  # True mientras se sintetiza o reproduce
        self._cache = LruAudioCache(max_entries=180)
        self._pending_prefetch: set[str] = set()
        self._pending_lock = threading.Lock()

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._ensure_worker()
        self._ensure_prefetch_worker()

    def speak(self, text: str) -> None:
        if not self._running:
            self.start()
        self._ensure_worker()
        self._queue.put({"cmd": "speak", "text": text, "gen": self._generation})

    def prefetch(self, texts: list[str]) -> None:
        if not texts:
            return
        voice = self._voice
        rate = self._rate
        if not self._running:
            self.start()
        self._ensure_prefetch_worker()
        for text in texts:
            self._enqueue_prefetch(text, voice, rate)

    def pause(self) -> None:
        self._generation += 1
        self._drain_queue()
        self._terminate_current_proc()

    def stop(self) -> None:
        self._running = False
        self._generation += 1
        self._drain_queue()
        self._drain_prefetch_queue()
        self._clear_all_pending_prefetch()
        self._terminate_current_proc()

    def set_rate(self, rate: int) -> None:
        self._rate = rate

    def set_voice(self, voice_id: str) -> None:
        self._voice = voice_id

    def list_voices(self) -> list[tuple[str, str]]:
        return _VOICES

    def is_speaking(self) -> bool:
        return self._busy or self._current_proc is not None or not self._queue.empty()

    # ── worker loop ──────────────────────────────────────────────────

    def _loop(self) -> None:
        while self._running:
            try:
                item = self._queue.get(timeout=0.1)
                try:
                    self._handle_command(item)
                except Exception:
                    self._busy = False
                    self._current_proc = None
            except queue.Empty:
                pass

    def _prefetch_loop(self) -> None:
        while self._running:
            try:
                item = self._prefetch_queue.get(timeout=0.1)
                self._handle_prefetch(item)
            except queue.Empty:
                pass

    def _handle_command(self, item: dict) -> None:
        if item["cmd"] == "speak":
            self._do_speak(item["text"], item["gen"])

    def _handle_prefetch(self, item: dict) -> None:
        key = item["key"]
        try:
            if self._cache.has(key):
                return
            mp3 = self._synthesize(item["text"], item["voice"], item["rate"])
            if mp3:
                self._cache.set(key, mp3)
        finally:
            self._clear_pending_prefetch(key)

    def _do_speak(self, text: str, gen: int) -> None:
        if not self._can_start(gen):
            return
        self._play_text(text, gen)

    def _play_text(self, text: str, gen: int) -> None:
        self._busy = True
        try:
            mp3 = self._audio_for_playback(text)
            if not self._can_play(mp3, gen):
                return
            self._play_mp3(mp3, gen)
        finally:
            self._busy = False

    def _audio_for_playback(self, text: str) -> bytes:
        key = _audio_key(text, self._voice, self._rate)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        mp3 = self._synthesize(text, self._voice, self._rate)
        if mp3:
            self._cache.set(key, mp3)
        return mp3

    def _can_play(self, audio: bytes, gen: int) -> bool:
        return bool(audio) and self._generation == gen

    def _can_start(self, gen: int) -> bool:
        return self._generation == gen

    def _synthesize(self, text: str, voice: str, rate: int) -> bytes:
        try:
            return asyncio.run(self._fetch_audio(text, voice, rate))
        except Exception:
            return b""

    async def _fetch_audio(self, text: str, voice: str, rate: int) -> bytes:
        communicate = edge_tts.Communicate(text, voice, rate=self._rate_str(rate))
        chunks: list[bytes] = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])
        return b"".join(chunks)

    def _play_mp3(self, mp3: bytes, gen: int) -> None:
        proc: Popen | None = None
        try:
            proc = Popen(["mpg123", "-q", "-"], stdin=PIPE, stderr=DEVNULL)
            self._current_proc = proc
            proc.stdin.write(mp3)  # type: ignore[union-attr]
            proc.stdin.close()  # type: ignore[union-attr]
            while proc.poll() is None:
                if self._generation != gen:
                    proc.terminate()
                    break
                time.sleep(0.05)
            proc.wait()
        finally:
            self._current_proc = None

    @staticmethod
    def _rate_str(rate: int) -> str:
        """Convierte palabras/min a porcentaje relativo de edge-tts."""
        pct = round((rate - 150) / 150 * 100)
        return f"+{pct}%" if pct >= 0 else f"{pct}%"

    def _enqueue_prefetch(self, text: str, voice: str, rate: int) -> None:
        key = _audio_key(text, voice, rate)
        if self._cache.has(key):
            return
        if not self._mark_pending_prefetch(key):
            return
        self._prefetch_queue.put({"text": text, "voice": voice, "rate": rate, "key": key})

    def _mark_pending_prefetch(self, key: str) -> bool:
        with self._pending_lock:
            if key in self._pending_prefetch:
                return False
            self._pending_prefetch.add(key)
            return True

    def _clear_pending_prefetch(self, key: str) -> None:
        with self._pending_lock:
            self._pending_prefetch.discard(key)

    def _clear_all_pending_prefetch(self) -> None:
        with self._pending_lock:
            self._pending_prefetch.clear()

    def _drain_queue(self) -> None:
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def _drain_prefetch_queue(self) -> None:
        while not self._prefetch_queue.empty():
            try:
                self._prefetch_queue.get_nowait()
            except queue.Empty:
                break

    def _ensure_worker(self) -> None:
        if not self._running:
            return
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _ensure_prefetch_worker(self) -> None:
        if not self._running:
            return
        if self._prefetch_thread and self._prefetch_thread.is_alive():
            return
        self._prefetch_thread = threading.Thread(target=self._prefetch_loop, daemon=True)
        self._prefetch_thread.start()

    def _terminate_current_proc(self) -> None:
        if self._current_proc:
            self._current_proc.terminate()


def _audio_key(text: str, voice: str, rate: int) -> str:
    return f"{voice}|{rate}|{text}"
