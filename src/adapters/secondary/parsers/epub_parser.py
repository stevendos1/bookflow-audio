"""EPUB parser usando stdlib únicamente (zipfile + xml.etree + html.parser).

Supuesto (docs/mvp.md §9): se usa stdlib en lugar de ebooklib+bs4 para no
agregar dependencias nuevas. Soporta EPUB2 y EPUB3 con estructura estándar.
"""

import xml.etree.ElementTree as ET
import zipfile
from html.parser import HTMLParser
from pathlib import Path

from src.domain.exceptions import DomainError
from src.domain.models import Chapter

_OPF_NS = "http://www.idpf.org/2007/opf"
_CONTAINER_NS = "urn:oasis:schemas:container"


class _HtmlTextExtractor(HTMLParser):
    """Extrae texto plano de HTML omitiendo script/style/head."""

    _BLOCK_TAGS = frozenset({"p", "h1", "h2", "h3", "h4", "h5", "h6", "br", "li", "div", "tr"})
    _SKIP_TAGS = frozenset({"script", "style", "head"})

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip_depth: int = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:  # noqa: ARG002
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1
        elif tag in self._BLOCK_TAGS and self._skip_depth == 0:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._parts.append(data)

    def get_text(self) -> str:
        return "".join(self._parts)


def _html_to_text(html: str) -> str:
    """Extrae texto plano de HTML omitiendo scripts, estilos y cabecera."""
    extractor = _HtmlTextExtractor()
    extractor.feed(html)
    return extractor.get_text()


def _find_el(root: ET.Element, tag: str, ns: str) -> ET.Element | None:
    """Busca elemento con namespace y sin él como fallback."""
    el = root.find(f".//{{{ns}}}{tag}")
    if el is not None:
        return el
    return root.find(f".//{tag}")


class EpubParser:
    """Parsea archivos EPUB2/EPUB3 en capítulos usando solo stdlib."""

    def parse_to_chapters(self, file_path: Path, book_id: str) -> list[tuple[Chapter, str]]:
        """Extrae capítulos de un EPUB respetando el orden del spine."""
        self._validate_path(file_path)
        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                return self._parse(zf, book_id, file_path)
        except DomainError:
            raise
        except Exception as exc:
            raise DomainError(
                f"Error al parsear EPUB: {exc}",
                {"file_path": str(file_path)},
            ) from exc

    # ------------------------------------------------------------------ #
    # Validación                                                           #
    # ------------------------------------------------------------------ #

    def _validate_path(self, file_path: Path) -> None:
        if not file_path.exists():
            raise DomainError(
                f"El archivo {file_path} no existe.",
                {"file_path": str(file_path)},
            )
        if not zipfile.is_zipfile(file_path):
            raise DomainError(
                f"No es un EPUB válido (estructura ZIP no encontrada): {file_path.name}",
                {"file_path": str(file_path)},
            )

    # ------------------------------------------------------------------ #
    # Parseo                                                               #
    # ------------------------------------------------------------------ #

    def _parse(
        self, zf: zipfile.ZipFile, book_id: str, file_path: Path
    ) -> list[tuple[Chapter, str]]:
        opf_path = self._find_opf_path(zf, file_path)
        opf_dir = Path(opf_path).parent.as_posix()
        opf_root = ET.fromstring(zf.read(opf_path).decode("utf-8"))
        href_map = self._build_href_map(opf_root)
        zip_paths = self._spine_zip_paths(opf_root, href_map, opf_dir)
        return self._chapters_from_paths(zf, zip_paths, book_id)

    def _find_opf_path(self, zf: zipfile.ZipFile, file_path: Path) -> str:
        container_xml = zf.read("META-INF/container.xml").decode("utf-8")
        root = ET.fromstring(container_xml)
        el = _find_el(root, "rootfile", _CONTAINER_NS)
        if el is None:
            raise DomainError(
                f"EPUB sin rootfile en container.xml: {file_path.name}",
                {"file_path": str(file_path)},
            )
        path = el.get("full-path", "")
        if not path:
            raise DomainError(
                f"EPUB: rootfile sin atributo full-path: {file_path.name}",
                {"file_path": str(file_path)},
            )
        return path

    def _build_href_map(self, opf_root: ET.Element) -> dict[str, str]:
        """Construye mapa id → href para ítems XHTML/HTML del manifiesto."""
        manifest = opf_root.find(f"{{{_OPF_NS}}}manifest")
        if manifest is None:
            manifest = opf_root.find("manifest")
        if manifest is None:
            return {}
        valid_types = {"application/xhtml+xml", "text/html"}
        return {
            item.get("id", ""): item.get("href", "")
            for item in manifest
            if item.get("media-type", "") in valid_types and item.get("id") and item.get("href")
        }

    def _find_spine(self, opf_root: ET.Element) -> ET.Element | None:
        spine = opf_root.find(f"{{{_OPF_NS}}}spine")
        if spine is not None:
            return spine
        return opf_root.find("spine")

    def _join_epub_path(self, opf_dir: str, href: str) -> str:
        if opf_dir and opf_dir != ".":
            return f"{opf_dir}/{href}".lstrip("/")
        return href.lstrip("/")

    def _spine_zip_paths(
        self,
        opf_root: ET.Element,
        href_map: dict[str, str],
        opf_dir: str,
    ) -> list[str]:
        """Devuelve rutas ZIP de capítulos en el orden del spine."""
        spine = self._find_spine(opf_root)
        if spine is None:
            return []
        paths = []
        for itemref in spine:
            href = href_map.get(itemref.get("idref", ""))
            if href:
                paths.append(self._join_epub_path(opf_dir, href))
        return paths

    def _chapters_from_paths(
        self,
        zf: zipfile.ZipFile,
        paths: list[str],
        book_id: str,
    ) -> list[tuple[Chapter, str]]:
        chapters = []
        for idx, path in enumerate(paths):
            try:
                html = zf.read(path).decode("utf-8", errors="replace")
            except KeyError:
                continue  # Archivo ausente en el ZIP, se omite
            text = _html_to_text(html)
            chapter = Chapter(book_id=book_id, idx=idx, title=f"Capítulo {idx + 1}")
            chapters.append((chapter, text))
        return chapters
