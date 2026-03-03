class FakeTtsEngine:
    def __init__(self) -> None:
        self.spoken: list[str] = []
        self.prefetched: list[list[str]] = []
        self.started = False
        self.stopped = False
        self.paused = False
        self.rate = 150
        self.voice_id = "default"

    def start(self) -> None:
        self.started = True

    def speak(self, text: str) -> None:
        self.spoken.append(text)

    def prefetch(self, texts: list[str]) -> None:
        self.prefetched.append(texts)

    def stop(self) -> None:
        self.stopped = True

    def pause(self) -> None:
        self.paused = True

    def set_rate(self, rate: int) -> None:
        self.rate = rate

    def set_voice(self, voice_id: str) -> None:
        self.voice_id = voice_id

    def list_voices(self) -> list[tuple[str, str]]:
        return [("default", "Voz Falsa"), ("voice2", "Otra voz")]

    def is_speaking(self) -> bool:
        return False
