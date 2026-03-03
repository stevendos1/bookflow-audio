"""Motor TTS usando espeak → paplay directamente, sin dependencia de aplay ni pyttsx3."""

import queue
import subprocess
import threading
import time
from subprocess import DEVNULL, PIPE, Popen

from src.adapters.secondary.tts.audio_cache import LruAudioCache


class EspeakEngine:
    """TTS engine que sintetiza con espeak y reproduce con paplay.

    No depende de aplay (alsa-utils) ni de pyttsx3 en tiempo de ejecución.
    Obtiene la lista de voces directamente del binario espeak.
    """

    def __init__(self) -> None:
        self._queue: queue.Queue = queue.Queue()
        self._prefetch_queue: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None
        self._prefetch_thread: threading.Thread | None = None
        self._running = False
        self._current_proc: Popen | None = None
        self._generation = 0  # incrementa en cada pause para cancelar el habla actual
        self._voice = "es-la"  # español latinoamericano por defecto
        self._rate = 150
        self._voices: list[tuple[str, str]] = _discover_espeak_voices()
        self._busy = False
        self._cache = LruAudioCache(max_entries=120)
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
        # Acepta IDs con o sin prefijo de directorio (ej. "roa/es-419" → "es-419",
        # o bien el ID directo de espeak 1.x como "es-la")
        self._voice = voice_id.split("/")[-1] if "/" in voice_id else voice_id

    def list_voices(self) -> list[tuple[str, str]]:
        return self._voices

    def is_speaking(self) -> bool:
        return self._busy or self._current_proc is not None or not self._queue.empty()

    # ── hilo worker ──────────────────────────────────────────────────

    def _loop(self) -> None:
        while self._running:
            item = self._dequeue()
            if item:
                try:
                    self._handle_command(item)
                except Exception:
                    self._busy = False
                    self._current_proc = None

    def _prefetch_loop(self) -> None:
        while self._running:
            item = self._dequeue_prefetch()
            if item:
                self._handle_prefetch(item)

    def _dequeue(self) -> dict | None:
        try:
            return self._queue.get(timeout=0.1)
        except queue.Empty:
            return None

    def _dequeue_prefetch(self) -> dict | None:
        try:
            return self._prefetch_queue.get(timeout=0.1)
        except queue.Empty:
            return None

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
            self._current_proc = None
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
        try:
            result = subprocess.run(
                ["espeak", "-v", voice, "-s", str(rate), "--stdout"],
                input=text.encode("utf-8"),
                stdout=PIPE,
                stderr=DEVNULL,
                check=False,
            )
            return result.stdout
        except Exception:
            return b""

    def _play_wav(self, wav: bytes, gen: int) -> None:
        proc = Popen(["paplay", "/dev/stdin"], stdin=PIPE, stderr=DEVNULL)
        self._current_proc = proc
        proc.stdin.write(wav)  # type: ignore[union-attr]
        proc.stdin.close()  # type: ignore[union-attr]
        while proc.poll() is None:
            if self._generation != gen:
                proc.terminate()
                break
            time.sleep(0.05)
        proc.wait()

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

    def _terminate_current_proc(self) -> None:
        if self._current_proc:
            self._current_proc.terminate()


# ── descubrimiento de voces ──────────────────────────────────────────


def _discover_espeak_voices() -> list[tuple[str, str]]:
    try:
        result = subprocess.run(["espeak", "--voices"], capture_output=True, text=True, timeout=5)
        return _parse_espeak_voices(result.stdout)
    except Exception:
        return [("es-la", "Spanish (Latin America)"), ("en", "English")]


def _parse_espeak_voices(output: str) -> list[tuple[str, str]]:
    """Parsea la salida de 'espeak --voices' → list of (voice_id, display_name)."""
    voices = []
    for line in output.splitlines()[1:]:  # salta la línea de cabecera
        parts = line.split()
        if len(parts) >= 5:
            voice_id = parts[4]  # columna "File"
            lang = parts[1]  # columna "Language"
            name = parts[3].replace("-", " ").title()  # columna "VoiceName"
            voices.append((voice_id, f"{name} ({lang})"))
    return voices


def _audio_key(text: str, voice: str, rate: int) -> str:
    return f"{voice}|{rate}|{text}"
