import hashlib
import re

from src.domain.models import Block


def normalize_text(text: str) -> str:
    """
    Normaliza el texto para su correcta reproducción por TTS.
    - Convierte saltos de línea Windows/Mac a Unix.
    - Separa los párrafos (identificados por 2 o más saltos de línea).
    - Colapsa espacios repetidos y saltos de línea simples dentro de un párrafo.
    - Mantiene inalterado el contenido unicode.
    """
    # 1. Normalizar retornos de carro
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2. Separar por párrafos
    paragraphs = re.split(r"\n{2,}", text)

    normalized_paragraphs = []
    for p in paragraphs:
        # 3. Limpiar espacios iniciales y finales, y colapsar espacios internos
        p = p.strip()
        if p:
            # Reemplaza cualquier secuencia de espacios o saltos simples por un solo espacio
            p = re.sub(r"[ \t\n]+", " ", p)
            normalized_paragraphs.append(p)

    return "\n\n".join(normalized_paragraphs)


class Chunker:
    def __init__(self, min_chars: int, max_chars: int, book_id: str, chapter_idx: int):
        self._min = min_chars
        self._max = max_chars
        self._book_id = book_id
        self._chapter_idx = chapter_idx
        self._blocks: list[Block] = []
        self._chunk: list[str] = []
        self._len = 0

    def process(self, text: str) -> list[Block]:
        tokens = re.findall(r"\S+|\s+", text)
        for token in tokens:
            self._process_token(token)
        self._flush()
        return self._blocks

    def _process_token(self, token: str) -> None:
        is_space = token.isspace()

        if not is_space and self._needs_max_flush(len(token)):
            self._flush()

        if not self._chunk and is_space:
            return

        self._chunk.append(token)
        self._len += len(token)

        if not is_space and self._needs_punct_flush(token):
            self._flush()

    def _needs_max_flush(self, word_len: int) -> bool:
        if not self._chunk:
            return False
        return self._len + word_len > self._max

    def _needs_punct_flush(self, word: str) -> bool:
        if self._len < self._min:
            return False
        return word[-1] in ".;:!?"

    def _flush(self) -> None:
        if not self._chunk:
            return

        while self._chunk and self._chunk[-1].isspace():
            popped = self._chunk.pop()
            self._len -= len(popped)

        if not self._chunk:
            return

        text_str = "".join(self._chunk)
        text_hash = hashlib.sha256(text_str.encode("utf-8")).hexdigest()
        block = Block(
            book_id=self._book_id,
            chapter_idx=self._chapter_idx,
            block_idx=len(self._blocks),
            text_hash=text_hash,
            text=text_str,
        )
        self._blocks.append(block)
        self._chunk.clear()
        self._len = 0


def chunk_text(
    text: str,
    min_chars: int = 500,
    max_chars: int = 1200,
    book_id: str = "",
    chapter_idx: int = 0,
) -> list[Block]:
    """Divide un texto en bloques (Blocks) respetando la puntuación y límites de caracteres."""
    chunker = Chunker(min_chars, max_chars, book_id, chapter_idx)
    return chunker.process(text)
