import queue
import threading
from typing import Any

import pyttsx3

from src.application.ports import TtsEngine


class Pyttsx3Engine(TtsEngine):
    """
    Implementación del motor TTS usando pyttsx3.
    Opera en un hilo secundario consumiendo una cola para evitar bloquear el UI o CLI central.
    """

    def __init__(self) -> None:
        self._command_queue: queue.Queue[dict[str, Any]] = queue.Queue()
        self._worker_thread: threading.Thread | None = None
        self._running = False

        # Propiedades almacenadas localmente para responder al instante (list_voices, etc)
        self._voices: list[tuple[str, str]] = []

        # Inicializa temporalmente el motor solo para extraer info de configuración
        # y luego lo cierra ya que el objeto pyttsx3.Engine a menudo no es thread-safe
        # para compartir entre hilos.
        temp_engine = pyttsx3.init()
        self._voices = [(v.id, v.name) for v in temp_engine.getProperty("voices")]
        temp_engine.stop()

    def start(self) -> None:
        if self._running:
            return

        self._running = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

    def stop(self) -> None:
        """Detiene de forma hard el motor. Para una pausa, limpiar dicts es más limpio."""
        self._command_queue.put({"type": "stop"})
        if self._worker_thread and self._worker_thread.is_alive():
            # No hacemos join() directo para no bloquear, el daemon thread morirá si falla
            self._running = False

    def speak(self, text: str) -> None:
        """Encola el texto de manera asíncrona."""
        self._command_queue.put({"type": "speak", "text": text})

    def pause(self) -> None:
        """
        En pyttsx3, el loop de event-pump es bloqueante dentro de runAndWait().
        El método nativo stop() a veces rompe el engine irreversiblemente.
        En general, mandamos la señal de "limpiar todo".
        """
        self._command_queue.put({"type": "pause"})

    def set_rate(self, rate: int) -> None:
        self._command_queue.put({"type": "set_rate", "rate": rate})

    def set_voice(self, voice_id: str) -> None:
        self._command_queue.put({"type": "set_voice", "voice_id": voice_id})

    def list_voices(self) -> list[tuple[str, str]]:
        return self._voices

    def _worker_loop(self) -> None:
        """Bucle consumidor corriendo en el hilo separado."""
        engine = pyttsx3.init()

        while self._running:
            try:
                cmd = self._command_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            self._process_command(engine, cmd)

    def _process_command(self, engine: pyttsx3.Engine, cmd: dict[str, Any]) -> None:
        cmd_type = cmd.get("type", "")

        handlers = {
            "stop": self._handle_stop,
            "pause": self._handle_pause,
            "set_rate": self._handle_set_rate,
            "set_voice": self._handle_set_voice,
            "speak": self._handle_speak,
        }

        handler = handlers.get(cmd_type)
        if handler:
            handler(engine, cmd)

    def _handle_stop(self, engine: pyttsx3.Engine, cmd: dict[str, Any]) -> None:
        engine.stop()
        self._running = False

    def _handle_pause(self, engine: pyttsx3.Engine, cmd: dict[str, Any]) -> None:
        engine.stop()
        while not self._command_queue.empty():
            try:
                self._command_queue.get_nowait()
            except queue.Empty:
                break

    def _handle_set_rate(self, engine: pyttsx3.Engine, cmd: dict[str, Any]) -> None:
        engine.setProperty("rate", cmd["rate"])

    def _handle_set_voice(self, engine: pyttsx3.Engine, cmd: dict[str, Any]) -> None:
        engine.setProperty("voice", cmd["voice_id"])

    def _handle_speak(self, engine: pyttsx3.Engine, cmd: dict[str, Any]) -> None:
        engine.say(cmd["text"])
        engine.runAndWait()
