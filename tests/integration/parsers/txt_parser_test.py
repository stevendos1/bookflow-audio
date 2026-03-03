from pathlib import Path

from src.adapters.secondary.parsers.txt_parser import TxtParser


def test_txt_parser_leer_fixture_simple():
    parser = TxtParser()
    path = Path("tests/fixtures/tiny.txt")

    result = parser.parse_to_chapters(path, book_id="book_123")

    assert len(result) == 3

    # Capítulo Inicial
    assert result[0][0].idx == 0
    assert result[0][0].book_id == "book_123"
    assert result[0][0].title == "Capítulo 1"
    assert "Prueba inicial del texto" in result[0][1]

    # Capítulo 2 (sin nombre explícito -> auto nombrado)
    assert result[1][0].idx == 1
    assert result[1][0].title == "Capítulo 2"
    assert "Cuerpo del capítulo." in result[1][1]

    # Capítulo 3 (con nombre "El Titulo")
    assert result[2][0].idx == 2
    assert result[2][0].title == "El Titulo"
    assert "Ñandú" in result[2][1]


def test_txt_parser_latin1_fallback(tmp_path: Path):
    # Crear un archivo latin-1 inválido para utf-8
    latin_file = tmp_path / "iso.txt"
    latin_file.write_bytes("Café".encode("latin-1"))

    parser = TxtParser()
    result = parser.parse_to_chapters(latin_file, "book_1")

    assert len(result) == 1
    assert result[0][1] == "Café"


def test_txt_parser_vacio(tmp_path: Path):
    vacio_file = tmp_path / "vacio.txt"
    vacio_file.write_text("")

    parser = TxtParser()
    result = parser.parse_to_chapters(vacio_file, "book_vacio")

    assert len(result) == 1
    assert result[0][1] == ""
    assert result[0][0].title == "Capítulo 1"
