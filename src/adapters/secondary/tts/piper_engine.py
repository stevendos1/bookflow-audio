"""Motor TTS usando Piper (voces neurales locales, sin internet).

Instalación:
  1. Descarga el binario desde https://github.com/rhasspy/piper/releases
     y colócalo en ~/.local/bin/piper
  2. Descarga modelos desde https://huggingface.co/rhasspy/piper-voices/
     y colócalos en ~/.local/share/piper/
     Ejemplos:
       es_ES-carla-medium.onnx  +  es_ES-carla-medium.onnx.json
       es_MX-claude-high.onnx   +  es_MX-claude-high.onnx.json
"""

import queue
import shutil
import threading
import time
from pathlib import Path
from subprocess import DEVNULL, PIPE, Popen

from src.adapters.secondary.tts.audio_cache import LruAudioCache

MODELS_DIR = Path.home() / ".local" / "share" / "piper"

_KNOWN_VOICES: list[tuple[str, str]] = [
    # ── Español ──────────────────────────────────────────────────────
    ("es_MX-claude-high", "Claude — México ♂  ★ Alta calidad"),
    ("es_MX-ald-medium", "Ald — México ♂"),
    ("es_AR-daniela-high", "Daniela — Argentina ♀  ★ Alta calidad"),
    ("es_ES-sharvard-medium", "Sharvard — España"),
    ("es_ES-davefx-medium", "Dave — España ♂"),
    ("es_ES-carlfm-x_low", "Carl — España ♂  (ligero)"),
    # ── English US ───────────────────────────────────────────────────
    ("en_US-ryan-medium", "Ryan — US English ♂"),
    ("en_US-amy-medium", "Amy — US English ♀"),
    ("en_US-joe-medium", "Joe — US English ♂"),
    ("en_US-lessac-medium", "Lessac — US English ♀"),
    ("en_US-norman-medium", "Norman — US English ♂"),
    ("en_US-kristin-medium", "Kristin — US English ♀"),
    # ── English GB ───────────────────────────────────────────────────
    ("en_GB-alan-medium", "Alan — British English ♂"),
    ("en_GB-alba-medium", "Alba — British English ♀"),
    ("en_GB-cori-medium", "Cori — British English ♀"),
]


def _find_piper() -> Path | None:
    candidate = Path.home() / ".local" / "bin" / "piper"
    if candidate.exists():
        return candidate
    found = shutil.which("piper")
    return Path(found) if found else None


def _available_voices() -> list[tuple[str, str]]:
    return [(vid, name) for vid, name in _KNOWN_VOICES if _model_path(vid).exists()]


def _model_path(voice_id: str) -> Path:
    return MODELS_DIR / f"{voice_id}.onnx"


class PiperEngine:
    """TTS engine usando el binario piper con modelos ONNX locales."""

    ENGINE_ID = "piper"
    ENGINE_LABEL = "Piper (local neural — sin internet)"

    def __init__(self) -> None:
        self._binary = _find_piper()
        self._voice = "es_ES-carla-medium"
        self._rate = 150
        self._queue: queue.Queue = queue.Queue()
        self._prefetch_queue: queue.Queue = queue.Queue()
        self._running = False
        self._thread: threading.Thread | None = None
        self._prefetch_thread: threading.Thread | None = None
        self._current_proc: Popen | None = None
        self._generation = 0
        self._busy = False
        self._cache = LruAudioCache(max_entries=100)
        self._pending_prefetch: set[str] = set()
        self._pending_lock = threading.Lock()

    @classmethod
    def is_available(cls) -> bool:
        """True si el binario piper está instalado."""
        return _find_piper() is not None

    def has_models(self) -> bool:
        """True si hay al menos un modelo descargado."""
        return bool(_available_voices())

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
        return _available_voices()

    def install_instructions(self) -> str:
        return (
            "Para usar Piper:\n"
            "1. Descarga el binario desde GitHub:\n"
            "   https://github.com/rhasspy/piper/releases\n"
            "   y colócalo en ~/.local/bin/piper\n\n"
            "2. Descarga un modelo español desde Hugging Face:\n"
            "   https://huggingface.co/rhasspy/piper-voices/\n"
            f"   y colócalo en {MODELS_DIR}/\n"
            "   Ejemplo: es_ES-carla-medium.onnx + es_ES-carla-medium.onnx.json"
        )

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
            wav = self._synthesize(item["text"], item["voice"], item["rate"])
            if wav:
                self._cache.set(key, wav)
        finally:
            self._clear_pending_prefetch(key)

    def _do_speak(self, text: str, gen: int) -> None:
        if not self._can_start(gen):
            return
        self._play_text(text, gen)

    def _play_text(self, text: str, gen: int) -> None:
        self._busy = True
        try:
            wav = self._audio_for_playback(text)
            if not self._can_play(wav, gen):
                return
            self._play_wav(wav, gen)
        finally:
            self._busy = False

    def _audio_for_playback(self, text: str) -> bytes:
        key = _audio_key(text, self._voice, self._rate)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        wav = self._synthesize(text, self._voice, self._rate)
        if wav:
            self._cache.set(key, wav)
        return wav

    def _can_play(self, audio: bytes, gen: int) -> bool:
        return bool(audio) and self._generation == gen

    def _can_start(self, gen: int) -> bool:
        return self._generation == gen

    def _synthesize(self, text: str, voice: str, rate: int) -> bytes:
        if not self._binary:
            return b""
        model = _model_path(voice)
        if not model.exists():
            return b""
        length_scale = str(round(150 / max(rate, 50), 2))
        piper = Popen(
            [
                str(self._binary),
                "--model",
                str(model),
                "--output_file",
                "/dev/stdout",
                "--length_scale",
                length_scale,
            ],
            stdin=PIPE,
            stdout=PIPE,
            stderr=DEVNULL,
        )
        stdout, _ = piper.communicate(text.encode("utf-8"))
        return stdout or b""

    def _play_wav(self, wav: bytes, gen: int) -> None:
        paplay = Popen(["paplay", "/dev/stdin"], stdin=PIPE, stderr=DEVNULL)
        self._current_proc = paplay
        paplay.stdin.write(wav)  # type: ignore[union-attr]
        paplay.stdin.close()  # type: ignore[union-attr]
        while paplay.poll() is None:
            if self._generation != gen:
                paplay.terminate()
                break
            time.sleep(0.05)
        paplay.wait()
        self._current_proc = None

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
