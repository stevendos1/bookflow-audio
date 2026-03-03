import time
from typing import Generator

import pytest

from src.adapters.secondary.tts.pyttsx3_engine import Pyttsx3Engine


@pytest.fixture
def engine() -> Generator[Pyttsx3Engine, None, None]:
    tts = Pyttsx3Engine()
    tts.start()
    yield tts
    tts.stop()


@pytest.mark.skip(reason="pyttsx3 segfault en Python 3.13. Motor reemplazado por EspeakEngine.")
def test_pyttsx3_list_voices(engine: Pyttsx3Engine):
    voices = engine.list_voices()
    assert isinstance(voices, list)
    if len(voices) > 0:
        assert isinstance(voices[0][0], str)
        assert isinstance(voices[0][1], str)


@pytest.mark.skip(reason="Smoke test que reproduce audio real. Correr manualmente para verificar.")
def test_pyttsx3_speak_smoke(engine: Pyttsx3Engine):
    engine.set_rate(200)
    engine.speak("Prueba de audio opcional con motor asíncrono. Uno, dos, tres.")

    # Damos tiempo a la cola para finalizar (smoke test manual)
    time.sleep(4)
