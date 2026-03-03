from src.domain.text import chunk_text, normalize_text


def test_normalize_text_colapsa_espacios():
    text = "Hola    mundo   con  varios    espacios."
    assert normalize_text(text) == "Hola mundo con varios espacios."


def test_normalize_text_preserva_parrafos():
    text = "Primer párrafo.\n\nSegundo párrafo.\n\n\nTercer párrafo."
    expected = "Primer párrafo.\n\nSegundo párrafo.\n\nTercer párrafo."
    assert normalize_text(text) == expected


def test_normalize_text_colapsa_saltos_simples():
    text = "Esta oración está\ncortada a la mitad."
    assert normalize_text(text) == "Esta oración está cortada a la mitad."


def test_normalize_text_respeta_unicode():
    text = "Ñandú, pingüino, áéíóú."
    assert normalize_text(text) == "Ñandú, pingüino, áéíóú."


def test_normalize_text_convierte_saltos_windows():
    text = "Hola\r\nmundo\r\n\r\notro párrafo."
    expected = "Hola mundo\n\notro párrafo."
    assert normalize_text(text) == expected


def test_normalize_text_elimina_espacios_al_inicio_y_fin():
    text = "   \n\n  Texto con espacios \t \n\n"
    assert normalize_text(text) == "Texto con espacios"


def test_chunk_text_no_corta_palabras():
    text = "Esta es una oración extremadamente larga que debe ser probada."
    blocks = chunk_text(text, min_chars=10, max_chars=15)

    expected = "Estaesunaoraciónextremadamentelargaquedebeserprobada."
    assert "".join(b.text for b in blocks).replace(" ", "") == expected
    for b in blocks:
        assert len(b.text) <= 15 or " " not in b.text


def test_chunk_text_corta_en_puntuacion():
    text = "Hola mundo. ¿Qué tal? Todo bien. Adiós."
    blocks = chunk_text(text, min_chars=10, max_chars=100)
    assert len(blocks) > 0
    assert blocks[0].text == "Hola mundo."


def test_chunk_text_salida_determinista():
    text = "El determinismo significa que la misma entrada produce la misma salida."
    blocks1 = chunk_text(text, min_chars=20, max_chars=50)
    blocks2 = chunk_text(text, min_chars=20, max_chars=50)

    assert len(blocks1) == len(blocks2)
    for b1, b2 in zip(blocks1, blocks2):
        assert b1.text_hash == b2.text_hash
        assert b1.text == b2.text
        assert b1.block_idx == b2.block_idx


def test_chunk_text_manejo_textos_cortos_o_vacios():
    assert chunk_text("") == []
    assert chunk_text("  \n  ") == []

    corto = "Hola."
    b = chunk_text(corto, min_chars=100)
    assert len(b) == 1
    assert b[0].text == "Hola."


def test_chunk_text_asigna_metadata_correctamente():
    blocks = chunk_text("A b c.", min_chars=1, book_id="book123", chapter_idx=2)
    assert len(blocks) == 1
    assert blocks[0].book_id == "book123"
    assert blocks[0].chapter_idx == 2
    assert blocks[0].block_idx == 0
