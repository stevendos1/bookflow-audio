"""Tests de integración para PdfParser.

El fixture PDF se genera inline con base64 para no guardar binarios en el repo.
Generado con PyMuPDF 1.27.1: 2 páginas con texto y unicode.
"""

import base64
from pathlib import Path

import fitz
import pytest

from src.adapters.secondary.parsers.multi_format_parser import MultiFormatParser
from src.adapters.secondary.parsers.pdf_parser import PdfParser
from src.application.use_cases.import_book import ImportBook
from src.domain.exceptions import DomainError
from tests.fakes.repository import FakeBookRepository

# PDF de dos páginas generado con PyMuPDF 1.27.1.
# Página 1: "Hola PDF test primera pagina." + "Caracteres: a e i o u n."
# Página 2: "Segunda pagina del libro de prueba."
_TINY_PDF_B64 = (
    "JVBERi0xLjcKJcK1wrYKJSBXcml0dGVuIGJ5IE11UERGIDEuMjcuMQoKMSAwIG9iago8PC9UeXBl"
    "L0NhdGFsb2cvUGFnZXMgMiAwIFIvSW5mbzw8L1Byb2R1Y2VyKE11UERGIDEuMjcuMSk+Pj4+CmVu"
    "ZG9iagoKMiAwIG9iago8PC9UeXBlL1BhZ2VzL0NvdW50IDIvS2lkc1s0IDAgUiAxMCAwIFJdPj4K"
    "ZW5kb2JqCgozIDAgb2JqCjw8L0ZvbnQ8PC9oZWx2IDUgMCBSPj4+PgplbmRvYmoKCjQgMCBvYmoK"
    "PDwvVHlwZS9QYWdlL01lZGlhQm94WzAgMCA1OTUgODQyXS9Sb3RhdGUgMC9SZXNvdXJjZXMgMyAw"
    "IFIvUGFyZW50IDIgMCBSL0NvbnRlbnRzWzYgMCBSIDcgMCBSIDggMCBSXT4+CmVuZG9iagoKNSAw"
    "IG9iago8PC9UeXBlL0ZvbnQvU3VidHlwZS9UeXBlMS9CYXNlRm9udC9IZWx2ZXRpY2EvRW5jb2Rp"
    "bmcvV2luQW5zaUVuY29kaW5nPj4KZW5kb2JqCgo2IDAgb2JqCjw8L0xlbmd0aCAxMDIvRmlsdGVy"
    "L0ZsYXRlRGVjb2RlPj4Kc3RyZWFtCnjaFYoxDsJADAR7v8I/wDbOmpMQRSQaukjuIiq4EwUUaXh/"
    "HE2zsxraaE5SlkI5jNGM80enT//+WZVz8Hr1CwZeUJNJ3B0m4ZjiHF5LwtDwLrejCIEi6ull/fbM"
    "B92TFtoB1jcXeAplbmRzdHJlYW0KZW5kb2JqCgo3IDAgb2JqCjw8L0xlbmd0aCA5OS9GaWx0ZXIv"
    "RmxhdGVEZWNvZGU+PgpzdHJlYW0KeNrjKuRyCuEyVDAAQkMFcyMFMyAOyeXSz0jNKVMwNFQISVOI"
    "tjE1MTM1tzA3MUszMjAzNkszSzUyAPIszZLNQDLGxolAcUMzU6BImrmpmSEyzyjVLjbEi8s1hCuQ"
    "CwBOrxj1CmVuZHN0cmVhbQplbmRvYmoKCjggMCBvYmoKPDwvTGVuZ3RoIDkyL0ZpbHRlci9GbGF0"
    "ZURlY29kZT4+CnN0cmVhbQp42hXGMQqAMAxA0T2nyA1s0iZBEAfBxU3IJg4OLQ46uHh+I58HHx6Y"
    "HAhTRGiMKox+Q3fW60Ui9IbbULKSsZJmKypxYjkfnJSChD40TvZ/5TruvsDssMIH6TMVIQplbmRz"
    "dHJlYW0KZW5kb2JqCgo5IDAgb2JqCjw8L0ZvbnQ8PC9oZWx2IDUgMCBSPj4+PgplbmRvYmoKCjEw"
    "IDAgb2JqCjw8L1R5cGUvUGFnZS9NZWRpYUJveFswIDAgNTk1IDg0Ml0vUm90YXRlIDAvUmVzb3Vy"
    "Y2VzIDkgMCBSL1BhcmVudCAyIDAgUi9Db250ZW50c1sxMSAwIFIgMTIgMCBSXT4+CmVuZG9iagoK"
    "MTEgMCBvYmoKPDwvTGVuZ3RoIDEwNi9GaWx0ZXIvRmxhdGVEZWNvZGU+PgpzdHJlYW0KeNolizEK"
    "w0AMBHu9Qj/wSY5WGIILg5t0AXUh1XFHCrtI4/dbxmyx7DBLf1qChEtG2JUxKcdOw69tB4twdP48"
    "bYTB3dDwgGjxAoFjyp0rmaFm1yTqin6zy3PNl0HTa/M3XrQGvekEAj4aIgplbmRzdHJlYW0KZW5k"
    "b2JqCgoxMiAwIG9iago8PC9MZW5ndGggODMvRmlsdGVyL0ZsYXRlRGVjb2RlPj4Kc3RyZWFtCnja"
    "4yrkcgrhMlQwAEJDBXMjBTMgDsnl0s9IzSlTMDRUCElTiLYxMTOzNEs1MjAzMTM1SwbTaWbG5qZm"
    "KUB+qjmQZ5RqFxvixeUawhXIBQAX6BNsCmVuZHN0cmVhbQplbmRvYmoKCnhyZWYKMCAxMwowMDAw"
    "MDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAwNDIgMDAwMDAgbiAKMDAwMDAwMDEyMCAwMDAwMCBuIAow"
    "MDAwMDAwMTc5IDAwMDAwIG4gCjAwMDAwMDAyMjAgMDAwMDAgbiAKMDAwMDAwMDMzOSAwMDAwMCBu"
    "IAowMDAwMDAwNDI4IDAwMDAwIG4gCjAwMDAwMDA1OTkgMDAwMDAgbiAKMDAwMDAwMDc2NiAwMDAw"
    "MCBuIAowMDAwMDAwOTI2IDAwMDAwIG4gCjAwMDAwMDA5NjcgMDAwMDAgbiAKMDAwMDAwMTA4MyAw"
    "MDAwMCBuIAowMDAwMDAxMjU5IDAwMDAwIG4gCgp0cmFpbGVyCjw8L1NpemUgMTMvUm9vdCAxIDAg"
    "Ui9JRFs8MEUxN0MzOUYwQkMzQjkzMTA2NTFDM0FCNUEyQ0MyODY+PDQ0NzdCRDJGOUE5OEU2QzA4"
    "QkM0NUZCRjNCNTg1NzMxPl0+PgpzdGFydHhyZWYKMTQxMQolJUVPRgo="
)


@pytest.fixture
def tiny_pdf(tmp_path: Path) -> Path:
    """PDF de dos páginas decodificado de base64 en tiempo de ejecución."""
    pdf_path = tmp_path / "tiny.pdf"
    pdf_path.write_bytes(base64.b64decode(_TINY_PDF_B64))
    return pdf_path


# ──────────────────────────── PdfParser ─────────────────────────── #


def test_pdf_parser_retorna_dos_capitulos(tiny_pdf: Path):
    parser = PdfParser()
    result = parser.parse_to_chapters(tiny_pdf, "book_pdf_01")
    assert len(result) == 2


def test_pdf_parser_capitulos_tienen_metadata_correcta(tiny_pdf: Path):
    parser = PdfParser()
    result = parser.parse_to_chapters(tiny_pdf, "book_pdf_02")

    ch0, _ = result[0]
    ch1, _ = result[1]

    assert ch0.book_id == "book_pdf_02"
    assert ch0.idx == 0
    assert ch1.idx == 1
    assert "Página" in ch0.title


def test_pdf_parser_texto_primera_pagina(tiny_pdf: Path):
    parser = PdfParser()
    result = parser.parse_to_chapters(tiny_pdf, "book_pdf_03")

    text_p1 = result[0][1]
    assert "Hola PDF" in text_p1


def test_pdf_parser_texto_segunda_pagina(tiny_pdf: Path):
    parser = PdfParser()
    result = parser.parse_to_chapters(tiny_pdf, "book_pdf_04")

    text_p2 = result[1][1]
    assert "Segunda pagina" in text_p2


def test_pdf_parser_archivo_inexistente():
    parser = PdfParser()
    with pytest.raises(DomainError, match="no existe"):
        parser.parse_to_chapters(Path("no_existe.pdf"), "book_x")


def test_pdf_parser_archivo_no_pdf(tmp_path: Path):
    fake = tmp_path / "fake.pdf"
    fake.write_text("esto no es un pdf")
    parser = PdfParser()
    with pytest.raises(DomainError):
        parser.parse_to_chapters(fake, "book_x")


def test_pdf_parser_pdf_sin_texto(tmp_path: Path):
    """Un PDF con páginas en blanco (sin texto) debe levantar DomainError claro."""
    blank_doc = fitz.Document()
    blank_doc.new_page()  # página sin contenido
    pdf_path = tmp_path / "blank.pdf"
    pdf_path.write_bytes(blank_doc.tobytes())
    blank_doc.close()

    parser = PdfParser()
    with pytest.raises(DomainError, match="sin texto"):
        parser.parse_to_chapters(pdf_path, "book_x")


def test_pdf_parser_paginas_vacias_se_omiten(tmp_path: Path):
    """Páginas en blanco intercaladas deben omitirse; las con texto se incluyen."""
    doc = fitz.Document()
    doc.new_page()  # página 1: en blanco
    p2 = doc.new_page()  # página 2: con texto
    p2.insert_text((72, 150), "Solo esta pagina tiene texto.", fontsize=11)
    pdf_path = tmp_path / "partial.pdf"
    pdf_path.write_bytes(doc.tobytes())
    doc.close()

    parser = PdfParser()
    result = parser.parse_to_chapters(pdf_path, "book_x")
    assert len(result) == 1
    assert "Solo esta pagina" in result[0][1]


# ──────────────── MultiFormatParser — enruta a PDF ──────────────── #


def test_multi_format_parser_enruta_pdf(tiny_pdf: Path):
    mfp = MultiFormatParser({".pdf": PdfParser()})
    result = mfp.parse_to_chapters(tiny_pdf, "mfp_pdf_01")
    assert len(result) == 2


# ──────────────── ImportBook use-case con PDF ────────────────────── #


def test_import_book_con_pdf(tiny_pdf: Path):
    """ImportBook debe persistir book + bloques + progreso inicial para un PDF."""

    # Usamos el parser real para ejercitar el flujo completo
    parser = PdfParser()
    repo = FakeBookRepository()
    use_case = ImportBook(parser=parser, repository=repo)

    book_id = use_case.handle(str(tiny_pdf))

    assert book_id is not None
    book = repo.get_book(book_id)
    assert book is not None
    assert book.title == tiny_pdf.name

    progress = repo.get_progress(book_id)
    assert progress is not None
    assert progress.chapter_idx == 0
    assert progress.block_idx == 0

    # Al menos un bloque generado
    all_blocks = repo._blocks.get(book_id, [])
    assert len(all_blocks) > 0
