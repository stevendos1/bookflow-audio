from dataclasses import dataclass, field


@dataclass(frozen=True)
class Book:
    id: str
    title: str
    authors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Chapter:
    book_id: str
    idx: int
    title: str


@dataclass(frozen=True)
class Block:
    book_id: str
    chapter_idx: int
    block_idx: int
    text_hash: str
    text: str


@dataclass(frozen=True)
class Progress:
    book_id: str
    chapter_idx: int
    block_idx: int
    offset: int = 0
