CREATE TABLE IF NOT EXISTS books (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    authors TEXT NOT NULL -- Guardaremos la lista como JSON o separados por comas
);

CREATE TABLE IF NOT EXISTS chapters (
    book_id TEXT NOT NULL,
    idx INTEGER NOT NULL,
    title TEXT NOT NULL,
    PRIMARY KEY (book_id, idx),
    FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS blocks (
    book_id TEXT NOT NULL,
    chapter_idx INTEGER NOT NULL,
    block_idx INTEGER NOT NULL,
    text_hash TEXT NOT NULL,
    content TEXT NOT NULL,
    PRIMARY KEY (book_id, chapter_idx, block_idx),
    FOREIGN KEY (book_id, chapter_idx) REFERENCES chapters (book_id, idx) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS progress (
    book_id TEXT PRIMARY KEY,
    chapter_idx INTEGER NOT NULL,
    block_idx INTEGER NOT NULL,
    offset INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE
);

-- Índices básicos para consultas más rápidas
CREATE INDEX IF NOT EXISTS idx_blocks_book_chapter ON blocks(book_id, chapter_idx);
