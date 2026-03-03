import re
from pathlib import Path

from src.application.ports import BookParser
from src.domain.exceptions import DomainError
from src.domain.models import Chapter


class TxtParser(BookParser):
    def parse_to_chapters(self, file_path: Path, book_id: str) -> list[tuple[Chapter, str]]:
        if not file_path.exists():
            raise DomainError(f"El archivo {file_path} no existe.", {"file_path": str(file_path)})

        raw_text = self._read_file_safe(file_path)
        # r"(?m)^###[ \t]*(.*)$" hace match con ### al inicio de la línea.
        # Captura toda la línea como "title" en un match y el contenido que sigue
        # hasta el próximo ###
        # se convertirá en el próximo elemento de la lista "blocks"
        blocks = re.split(r"(?m)^###[ \t]*(.*)$", raw_text)

        return self._extract_chapters(blocks, book_id)

    def _extract_chapters(self, blocks: list[str], book_id: str) -> list[tuple[Chapter, str]]:
        chapters_data: list[tuple[Chapter, str]] = []

        prelude_text = blocks[0].strip()
        idx = 0
        if prelude_text:
            chapter = Chapter(book_id=book_id, idx=idx, title="Capítulo 1")
            chapters_data.append((chapter, prelude_text))
            idx += 1

        for i in range(1, len(blocks), 2):
            idx = self._process_block_pair(blocks, i, book_id, idx, chapters_data)

        if not chapters_data:
            chapter = Chapter(book_id=book_id, idx=0, title="Capítulo 1")
            chapters_data.append((chapter, ""))

        return chapters_data

    def _process_block_pair(
        self,
        blocks: list[str],
        i: int,
        book_id: str,
        idx: int,
        chapters_data: list[tuple[Chapter, str]],
    ) -> int:
        title_match = blocks[i].strip()
        title = title_match if title_match else f"Capítulo {idx + 1}"
        content = blocks[i + 1].strip()

        if content:
            chapter = Chapter(book_id=book_id, idx=idx, title=title)
            chapters_data.append((chapter, content))
            return idx + 1
        return idx

    def _read_file_safe(self, file_path: Path) -> str:
        """Intenta leer con utf-8, luego latin-1, o fuerza la lectura ignorando errores."""
        try:
            return file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                return file_path.read_text(encoding="latin-1")
            except UnicodeDecodeError:
                # Fallback extremo: reemplazar caracteres ilegibles
                return file_path.read_text(encoding="utf-8", errors="replace")
