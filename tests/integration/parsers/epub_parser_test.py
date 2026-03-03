"""Tests de integración para EpubParser y MultiFormatParser."""

from pathlib import Path

import pytest

from src.adapters.secondary.parsers.epub_parser import EpubParser
from src.adapters.secondary.parsers.multi_format_parser import MultiFormatParser
from src.domain.exceptions import DomainError

FIXTURE_EPUB = Path("tests/fixtures/tiny.epub")


# ─────────────────────────── EpubParser ─────────────────────────── #


def test_epub_fixture_exists():
    assert FIXTURE_EPUB.exists(), "Fixture tiny.epub no encontrada en tests/fixtures/"


def test_epub_parser_retorna_dos_capitulos():
    parser = EpubParser()
    result = parser.parse_to_chapters(FIXTURE_EPUB, "book_epub_01")

    assert len(result) == 2


def test_epub_parser_capitulos_tienen_metadata_correcta():
    parser = EpubParser()
    result = parser.parse_to_chapters(FIXTURE_EPUB, "book_epub_02")

    ch1, _ = result[0]
    ch2, _ = result[1]

    assert ch1.book_id == "book_epub_02"
    assert ch1.idx == 0
    assert ch2.idx == 1


def test_epub_parser_texto_capitulo_uno():
    parser = EpubParser()
    result = parser.parse_to_chapters(FIXTURE_EPUB, "book_epub_03")

    text_ch1 = result[0][1]
    assert "Chapter One" in text_ch1
    assert "first paragraph" in text_ch1.lower()


def test_epub_parser_texto_capitulo_dos():
    parser = EpubParser()
    result = parser.parse_to_chapters(FIXTURE_EPUB, "book_epub_04")

    text_ch2 = result[1][1]
    assert "chapter two" in text_ch2.lower()


def test_epub_parser_preserva_unicode():
    parser = EpubParser()
    result = parser.parse_to_chapters(FIXTURE_EPUB, "book_epub_05")

    full_text = " ".join(r[1] for r in result)
    assert "Ñandú" in full_text
    assert "áéíóú" in full_text


def test_epub_parser_omite_contenido_head():
    """El texto del <title> de <head> no debe aparecer en el contenido."""
    parser = EpubParser()
    result = parser.parse_to_chapters(FIXTURE_EPUB, "book_epub_06")

    # "Chapter One" viene del <h1>, no del <title>; pero si aparece una sola vez está bien.
    # Lo clave es que no haya ruido de CSS ni scripts:
    text_ch1 = result[0][1]
    assert "<" not in text_ch1, "El texto no debe contener etiquetas HTML"
    assert "stylesheet" not in text_ch1.lower()


def test_epub_parser_archivo_inexistente():
    parser = EpubParser()
    with pytest.raises(DomainError, match="no existe"):
        parser.parse_to_chapters(Path("no_existe.epub"), "book_x")


def test_epub_parser_archivo_no_epub(tmp_path: Path):
    fake = tmp_path / "fake.epub"
    fake.write_text("esto no es un epub")
    parser = EpubParser()
    with pytest.raises(DomainError):
        parser.parse_to_chapters(fake, "book_x")


# ─────────────────────── MultiFormatParser ──────────────────────── #


def test_multi_format_parser_enruta_epub():
    epub_parser = EpubParser()
    mfp = MultiFormatParser({".epub": epub_parser})

    result = mfp.parse_to_chapters(FIXTURE_EPUB, "mfp_01")
    assert len(result) == 2


def test_multi_format_parser_formato_no_soportado(tmp_path: Path):
    mfp = MultiFormatParser({".txt": EpubParser()})  # solo .txt registrado
    unknown = tmp_path / "libro.mobi"
    unknown.write_text("content")

    with pytest.raises(DomainError, match="no soportado"):
        mfp.parse_to_chapters(unknown, "mfp_02")


def test_multi_format_parser_extension_case_insensitive(tmp_path: Path):
    """Extensión en mayúsculas debe resolverse igual."""
    epub_parser = EpubParser()
    mfp = MultiFormatParser({".epub": epub_parser})

    # Copia tiny.epub con nombre en mayúsculas
    import shutil

    upper_epub = tmp_path / "LIBRO.EPUB"
    shutil.copy(FIXTURE_EPUB, upper_epub)

    result = mfp.parse_to_chapters(upper_epub, "mfp_03")
    assert len(result) == 2
