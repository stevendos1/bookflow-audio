import threading
import time

import pytest

from src.adapters.secondary.tts.espeak_engine import EspeakEngine
from src.adapters.secondary.tts.piper_engine import PiperEngine


@pytest.mark.parametrize("engine_cls", [EspeakEngine, PiperEngine])
def test_tts_loop_survives_handler_exception(engine_cls):
    engine = engine_cls()
    engine.start()

    done = threading.Event()

    def broken(_item):
        raise RuntimeError("boom")

    def healthy(_item):
        done.set()

    engine._handle_command = broken  # type: ignore[method-assign]
    engine.speak("primero")
    time.sleep(0.2)

    engine._handle_command = healthy  # type: ignore[method-assign]
    engine.speak("segundo")

    assert done.wait(1.0)
    engine.stop()


def test_espeak_exposes_is_speaking_method():
    engine = EspeakEngine()
    assert isinstance(engine.is_speaking(), bool)
