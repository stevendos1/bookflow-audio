"""Interfaz gráfica Qt para el lector de libros (adaptador primario)."""

import re

from PySide6.QtCore import QPointF, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,  # usado en book_list
    QMainWindow,
    QPushButton,
    QSlider,
    QSplitter,
    QStatusBar,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from src.infrastructure.reader_app import ReaderApp, available_engines

_STYLE = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Noto Sans", "Segoe UI", "Helvetica Neue", sans-serif;
    font-size: 13px;
}
QSplitter::handle {
    background-color: #313244;
    width: 2px;
}

/* ── Botones generales ── */
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 14px;
    min-height: 32px;
}
QPushButton:hover    { background-color: #45475a; border-color: #585b70; }
QPushButton:pressed  { background-color: #585b70; }
QPushButton:disabled { background-color: #181825; color: #585b70; border-color: #313244; }

/* ── Reproducir (azul) ── */
QPushButton#btn_play {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 8px;
    font-weight: bold;
    font-size: 15px;
    min-height: 48px;
    min-width: 130px;
    padding: 8px 22px;
}
QPushButton#btn_play:hover   { background-color: #b4d0ff; }
QPushButton#btn_play:pressed { background-color: #74a8f0; }

/* ── Pausar (amarillo) ── */
QPushButton#btn_pause {
    background-color: #f9e2af;
    color: #1e1e2e;
    border: none;
    border-radius: 6px;
    font-weight: bold;
    min-height: 40px;
    padding: 6px 18px;
}
QPushButton#btn_pause:hover   { background-color: #faecc5; }
QPushButton#btn_pause:pressed { background-color: #e8cf94; }

/* ── Importar (verde) ── */
QPushButton#btn_import {
    background-color: #a6e3a1;
    color: #1e1e2e;
    border: none;
    border-radius: 6px;
    font-weight: bold;
    min-height: 38px;
}
QPushButton#btn_import:hover   { background-color: #bfecba; }
QPushButton#btn_import:pressed { background-color: #8fcc8a; }
QPushButton#btn_import:disabled { background-color: #313244; color: #585b70; }

/* ── Tarjeta Now-Playing ── */
QFrame#now_playing_card {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 10px;
}
QLabel#now_playing_title {
    color: #cdd6f4;
    font-size: 14px;
    font-weight: bold;
    background: transparent;
}
QLabel#now_playing_sub {
    color: #a6adc8;
    font-size: 11px;
    background: transparent;
}

/* ── Etiquetas de sección ── */
QLabel#section_label {
    color: #a6adc8;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 1px;
    background: transparent;
    padding: 2px 0;
}

/* ── Lista de libros (sidebar) ── */
QListWidget#book_list {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 8px;
    outline: none;
    padding: 4px;
}
QListWidget#book_list::item {
    color: #cdd6f4;
    border-radius: 5px;
    padding: 7px 10px;
    min-height: 26px;
}
QListWidget#book_list::item:hover:!selected { background-color: #2a2a3e; }
QListWidget#book_list::item:selected        { background-color: #45475a; color: #89b4fa; }

/* ── Visor de texto del capítulo ── */
QTextBrowser#text_browser {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 8px;
    color: #cdd6f4;
    font-family: "Georgia", "DejaVu Serif", serif;
    font-size: 14px;
    line-height: 1.7;
    padding: 8px;
    selection-background-color: #45475a;
}

/* ── ComboBox ── */
QComboBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 5px;
    padding: 4px 10px;
    min-height: 28px;
}
QComboBox:hover { border-color: #89b4fa; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    selection-background-color: #45475a;
    selection-color: #89b4fa;
    outline: none;
    padding: 2px;
}

/* ── Slider ── */
QSlider::groove:horizontal {
    height: 4px;
    background-color: #45475a;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background-color: #89b4fa;
    border: none;
    width: 14px;
    height: 14px;
    border-radius: 7px;
    margin: -5px 0;
}
QSlider::sub-page:horizontal { background-color: #89b4fa; border-radius: 2px; }

/* ── StatusBar ── */
QStatusBar {
    background-color: #181825;
    color: #a6adc8;
    font-size: 11px;
    border-top: 1px solid #313244;
}

/* ── Scrollbars ── */
QScrollBar:vertical {
    background-color: #181825;
    width: 8px;
    border-radius: 4px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background-color: #45475a;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover   { background-color: #585b70; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background-color: #181825;
    height: 8px;
    border-radius: 4px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background-color: #45475a;
    border-radius: 4px;
    min-width: 20px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── Reiniciar (rojo) ── */
QPushButton#btn_restart {
    background-color: #f38ba8;
    color: #1e1e2e;
    border: none;
    border-radius: 6px;
    font-weight: bold;
    min-height: 36px;
    padding: 6px 14px;
}
QPushButton#btn_restart:hover   { background-color: #f5a3bb; }
QPushButton#btn_restart:pressed { background-color: #e07898; }
"""


class _ImportThread(QThread):
    """Ejecuta import_file en un hilo secundario para no bloquear la GUI."""

    finished = Signal(str)
    error = Signal(str)

    def __init__(self, app: ReaderApp, path: str) -> None:
        super().__init__()
        self._app = app
        self._path = path

    def run(self) -> None:
        try:
            book_id = self._app.import_file(self._path)
            self.finished.emit(book_id)
        except Exception as exc:
            self.error.emit(str(exc))


class _ChapterTextBrowser(QTextBrowser):
    """QTextBrowser que emite señal al hacer click sobre un enlace de bloque."""

    blockClicked = Signal(int, int)

    def __init__(self) -> None:
        super().__init__()
        self._press_pos = QPointF()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.position()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        super().mouseReleaseEvent(event)
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if (event.position() - self._press_pos).manhattanLength() > 4:
            return
        href = self.anchorAt(event.position().toPoint())
        block = _parse_block_href(href)
        if block:
            self.blockClicked.emit(*block)


def _parse_block_href(href: str) -> tuple[int, int] | None:
    """Parsea href tipo block://<chapter>/<block>."""
    match = re.fullmatch(r"block://(\d+)/(\d+)", href)
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2))


class MainWindow(QMainWindow):
    """Ventana principal del lector de libros."""
    _AUTO_ADVANCE_TIMER_MS = 120
    _STATUS_REFRESH_TICKS = 16  # ~1.9s con timer de 120ms

    def __init__(self, app: ReaderApp) -> None:
        super().__init__()
        self._app = app
        self._import_thread: _ImportThread | None = None

        self.setWindowTitle("Lector de Libros")
        self.resize(960, 700)
        self._build_ui()
        self._refresh_books()
        self._refresh_chapters()

        self._last_block_count = -1
        self._last_current_blk = -1
        self._last_chapter_idx = -1
        self._tick = 0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer)
        self._timer.start(self._AUTO_ADVANCE_TIMER_MS)
        self._rate_timer = QTimer(self)
        self._rate_timer.setSingleShot(True)
        self._rate_timer.timeout.connect(self._apply_rate_change)
        self._pending_rate = 150

    # ── construcción de la UI ────────────────────────────────────────

    def _build_ui(self) -> None:
        self.setStyleSheet(_STYLE)
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_sidebar())
        splitter.addWidget(self._build_main_panel())
        splitter.setSizes([260, 700])
        root.addWidget(splitter)

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Selecciona un libro y pulsa Reproducir.")

    def _build_sidebar(self) -> QWidget:
        """Panel izquierdo: biblioteca de libros + botón importar."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 14, 6, 12)
        layout.setSpacing(8)

        lbl = QLabel("BIBLIOTECA")
        lbl.setObjectName("section_label")
        layout.addWidget(lbl)

        self._book_list = QListWidget()
        self._book_list.setObjectName("book_list")
        self._book_list.itemDoubleClicked.connect(lambda _: self._on_play())
        layout.addWidget(self._book_list, 1)

        self._btn_import = QPushButton("+ Importar libro…")
        self._btn_import.setObjectName("btn_import")
        self._btn_import.clicked.connect(self._on_import)
        layout.addWidget(self._btn_import)
        return panel

    def _build_main_panel(self) -> QWidget:
        """Panel derecho: tarjeta, controles, ajustes y texto del capítulo."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(6, 14, 12, 12)
        layout.setSpacing(10)

        layout.addWidget(self._build_now_playing_card())
        self._build_controls_row(layout)
        self._build_chapter_nav_row(layout)
        self._build_settings_row(layout)

        lbl = QLabel("TEXTO DEL CAPÍTULO — clic en un párrafo para saltar")
        lbl.setObjectName("section_label")
        layout.addWidget(lbl)

        self._text_browser = _ChapterTextBrowser()
        self._text_browser.setObjectName("text_browser")
        self._text_browser.setOpenLinks(False)
        self._text_browser.blockClicked.connect(self._on_text_block_clicked)
        layout.addWidget(self._text_browser, 1)
        return panel

    def _build_now_playing_card(self) -> QFrame:
        """Tarjeta que muestra el libro y posición actuales."""
        card = QFrame()
        card.setObjectName("now_playing_card")
        card.setFrameShape(QFrame.Shape.StyledPanel)
        inner = QVBoxLayout(card)
        inner.setContentsMargins(14, 10, 14, 10)
        inner.setSpacing(3)

        self._now_playing_title = QLabel("Sin reproducción")
        self._now_playing_title.setObjectName("now_playing_title")
        self._now_playing_sub = QLabel("")
        self._now_playing_sub.setObjectName("now_playing_sub")

        inner.addWidget(self._now_playing_title)
        inner.addWidget(self._now_playing_sub)
        return card

    def _build_controls_row(self, root: QVBoxLayout) -> None:
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)
        self._btn_prev = QPushButton("⏮  Anterior")
        self._btn_play = QPushButton("▶   Reproducir")
        self._btn_play.setObjectName("btn_play")
        self._btn_pause = QPushButton("⏸   Pausar")
        self._btn_pause.setObjectName("btn_pause")
        self._btn_next = QPushButton("⏭  Siguiente")
        for btn in (self._btn_prev, self._btn_play, self._btn_pause, self._btn_next):
            ctrl.addWidget(btn)
        root.addLayout(ctrl)
        self._btn_prev.clicked.connect(self._on_prev)
        self._btn_play.clicked.connect(self._on_play)
        self._btn_pause.clicked.connect(self._on_pause)
        self._btn_next.clicked.connect(self._on_next)

    def _build_chapter_nav_row(self, root: QVBoxLayout) -> None:
        """Fila: botón cap. anterior + combo capítulos + cap. siguiente + reiniciar."""
        row = QHBoxLayout()
        row.setSpacing(8)

        self._btn_prev_chapter = QPushButton("❮❮  Cap. ant.")
        self._chapter_combo = QComboBox()
        self._chapter_combo.setMinimumWidth(260)
        self._btn_next_chapter = QPushButton("Cap. sig.  ❯❯")
        self._btn_restart = QPushButton("↩  Reiniciar")
        self._btn_restart.setObjectName("btn_restart")

        row.addWidget(self._btn_prev_chapter)
        row.addWidget(self._chapter_combo, 1)
        row.addWidget(self._btn_next_chapter)
        row.addWidget(self._btn_restart)
        root.addLayout(row)

        self._btn_prev_chapter.clicked.connect(self._on_prev_chapter)
        self._btn_next_chapter.clicked.connect(self._on_next_chapter)
        self._btn_restart.clicked.connect(self._on_restart)
        self._chapter_combo.currentIndexChanged.connect(self._on_chapter_changed)

    def _build_settings_row(self, root: QVBoxLayout) -> None:
        row = QHBoxLayout()
        row.setSpacing(8)

        row.addWidget(QLabel("Motor:"))
        self._engine_combo = QComboBox()
        self._engine_combo.setMinimumWidth(200)
        for eng_id, eng_label in available_engines():
            self._engine_combo.addItem(eng_label, userData=eng_id)
        self._engine_combo.currentIndexChanged.connect(self._on_engine_changed)
        row.addWidget(self._engine_combo)

        row.addWidget(QLabel("Voz:"))
        self._voice_combo = QComboBox()
        self._voice_combo.setMinimumWidth(190)
        self._populate_voices()
        self._voice_combo.currentIndexChanged.connect(self._on_voice_changed)
        row.addWidget(self._voice_combo)

        row.addWidget(QLabel("Velocidad:"))
        self._rate_slider = QSlider(Qt.Orientation.Horizontal)
        self._rate_slider.setRange(50, 400)
        self._rate_slider.setValue(150)
        self._rate_slider.setFixedWidth(130)
        self._rate_label = QLabel("150 pal/min")
        self._rate_label.setFixedWidth(80)
        self._rate_slider.valueChanged.connect(self._on_rate_changed)
        self._rate_slider.sliderReleased.connect(self._apply_rate_change)
        row.addWidget(self._rate_slider)
        row.addWidget(self._rate_label)

        row.addWidget(QLabel("Prefetch:"))
        prefetch_value = self._app.get_prefetch_window()
        self._prefetch_slider = QSlider(Qt.Orientation.Horizontal)
        self._prefetch_slider.setRange(1, 50)
        self._prefetch_slider.setValue(prefetch_value)
        self._prefetch_slider.setFixedWidth(110)
        self._prefetch_label = QLabel(f"{prefetch_value} blq")
        self._prefetch_label.setFixedWidth(46)
        self._prefetch_slider.valueChanged.connect(self._on_prefetch_changed)
        row.addWidget(self._prefetch_slider)
        row.addWidget(self._prefetch_label)

        row.addStretch()
        root.addLayout(row)

    # ── importar ─────────────────────────────────────────────────────

    def _on_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar libro", "", "Libros (*.epub *.txt *.pdf);;Todos (*)"
        )
        if not path:
            return
        self._btn_import.setEnabled(False)
        self._btn_import.setText("Importando…")
        self._import_thread = _ImportThread(self._app, path)
        self._import_thread.finished.connect(self._on_import_done)
        self._import_thread.error.connect(self._on_import_error)
        self._import_thread.start()

    def _on_import_done(self, book_id: str) -> None:
        self._btn_import.setEnabled(True)
        self._btn_import.setText("+ Importar libro…")
        self._refresh_books()
        self._select_book(book_id)
        self._refresh_chapters()
        self._status_bar.showMessage("Libro importado. Pulsa Reproducir para escuchar.")

    def _on_import_error(self, msg: str) -> None:
        self._btn_import.setEnabled(True)
        self._btn_import.setText("+ Importar libro…")
        self._status_bar.showMessage(f"Error al importar: {msg}")

    # ── reproducción ─────────────────────────────────────────────────

    def _on_play(self) -> None:
        item = self._book_list.currentItem()
        if not item:
            self._status_bar.showMessage("Selecciona un libro de la lista primero.")
            return
        book_id = item.data(Qt.ItemDataRole.UserRole)
        self._app.play(book_id)
        self._refresh_chapters()
        self._status_bar.showMessage("Reproduciendo…")
        self._refresh_text_view()

    def _on_pause(self) -> None:
        self._app.pause()
        self._status_bar.showMessage("Pausado.")

    def _on_next(self) -> None:
        self._app.next()

    def _on_prev(self) -> None:
        self._app.prev()

    def _on_block_clicked(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            ch_idx, blk_idx = data
            self._app.jump(ch_idx, blk_idx)
            self._status_bar.showMessage("Reproduciendo desde bloque seleccionado…")

    def _on_text_block_clicked(self, chapter_idx: int, block_idx: int) -> None:
        self._app.jump(chapter_idx, block_idx)
        self._refresh_text_view()
        st = self._app.status()
        if st:
            self._sync_chapter_combo(st.chapter_idx)
            self._update_now_playing(st.title, st.chapter_idx, st.block_idx)
        self._status_bar.showMessage("Reproduciendo desde párrafo seleccionado…")

    # ── motor, velocidad y voz ───────────────────────────────────────

    def _populate_voices(self) -> None:
        self._voice_combo.blockSignals(True)
        self._voice_combo.clear()
        for v_id, v_name in self._app.list_voices():
            self._voice_combo.addItem(v_name, userData=v_id)
        self._voice_combo.setCurrentIndex(0)
        self._voice_combo.blockSignals(False)
        if self._voice_combo.count() > 0:
            self._app.set_voice(self._voice_combo.itemData(0))

    def _on_engine_changed(self, index: int) -> None:
        engine_id = self._engine_combo.itemData(index)
        if not engine_id:
            return
        self._status_bar.showMessage(f"Cambiando motor a {engine_id}…")
        self._app.set_engine(engine_id)
        self._populate_voices()
        self._status_bar.showMessage(f"Motor: {self._engine_combo.currentText()}")

    def _on_rate_changed(self, value: int) -> None:
        self._pending_rate = value
        self._rate_label.setText(f"{value} pal/min")
        self._rate_timer.start(180)

    def _apply_rate_change(self) -> None:
        value = self._pending_rate
        self._app.set_rate(value)
        if not self._app.is_playing():
            return
        st = self._app.status()
        if st is None:
            return
        # Reproduce el bloque actual para que el cambio se perciba inmediatamente.
        self._app.jump(st.chapter_idx, st.block_idx)
        self._refresh_text_view()
        self._status_bar.showMessage(f"Velocidad aplicada: {value} pal/min")

    def _on_voice_changed(self, index: int) -> None:
        voice_id = self._voice_combo.itemData(index)
        if voice_id:
            self._app.set_voice(voice_id)

    def _on_prefetch_changed(self, size: int) -> None:
        self._prefetch_label.setText(f"{size} blq")
        self._app.set_prefetch_window(size)
        self._status_bar.showMessage(f"Prefetch: {size} bloques")

    # ── lista de libros ──────────────────────────────────────────────

    def _refresh_books(self) -> None:
        self._book_list.clear()
        for book_id, title in self._app.list_books():
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, book_id)
            self._book_list.addItem(item)
        if self._book_list.count() > 0 and self._book_list.currentItem() is None:
            self._book_list.setCurrentRow(0)

    def _select_book(self, book_id: str) -> None:
        for i in range(self._book_list.count()):
            item = self._book_list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == book_id:
                self._book_list.setCurrentItem(item)
                break

    def _find_voice_index(self, fragment: str) -> int:
        for i in range(self._voice_combo.count()):
            data = self._voice_combo.itemData(i) or ""
            if fragment in data:
                return i
        return 0

    # ── capítulos ────────────────────────────────────────────────────

    def _refresh_chapters(self) -> None:
        """Recarga la lista de capítulos en el combo a partir del libro actual."""
        chapters = self._app.get_chapters()
        self._chapter_combo.blockSignals(True)
        self._chapter_combo.clear()
        for idx, title in chapters:
            label = f"Cap. {idx + 1}  —  {title}" if title else f"Capítulo {idx + 1}"
            self._chapter_combo.addItem(label, userData=idx)
        self._chapter_combo.blockSignals(False)
        st = self._app.status()
        if st:
            self._sync_chapter_combo(st.chapter_idx)

    def _sync_chapter_combo(self, chapter_idx: int) -> None:
        """Mueve la selección del combo al capítulo indicado sin disparar señales."""
        self._chapter_combo.blockSignals(True)
        for i in range(self._chapter_combo.count()):
            if self._chapter_combo.itemData(i) == chapter_idx:
                self._chapter_combo.setCurrentIndex(i)
                break
        self._chapter_combo.blockSignals(False)

    def _on_prev_chapter(self) -> None:
        st = self._app.status()
        if st and st.chapter_idx > 0:
            self._app.jump_to_chapter(st.chapter_idx - 1)
            self._after_chapter_jump()

    def _on_next_chapter(self) -> None:
        chapters = self._app.get_chapters()
        st = self._app.status()
        if st and st.chapter_idx < len(chapters) - 1:
            self._app.jump_to_chapter(st.chapter_idx + 1)
            self._after_chapter_jump()

    def _on_chapter_changed(self, index: int) -> None:
        chapter_idx = self._chapter_combo.itemData(index)
        if chapter_idx is not None:
            self._app.jump_to_chapter(chapter_idx)
            self._after_chapter_jump()

    def _on_restart(self) -> None:
        self._app.restart()
        self._after_chapter_jump()
        self._status_bar.showMessage("Reiniciando desde el inicio del libro…")

    def _after_chapter_jump(self) -> None:
        """Refresca la UI inmediatamente después de un salto de capítulo."""
        self._last_block_count = -1
        self._last_current_blk = -1
        self._last_chapter_idx = -1
        self._refresh_text_view()
        st = self._app.status()
        if st:
            self._sync_chapter_combo(st.chapter_idx)
            self._update_now_playing(st.title, st.chapter_idx, st.block_idx)

    # ── panel de texto del capítulo ──────────────────────────────────

    def _refresh_text_view(self) -> None:
        blocks = self._app.get_chapter_blocks()
        st = self._app.status()
        current_blk = st.block_idx if st else -1
        current_ch = st.chapter_idx if st else -1
        unchanged = (
            len(blocks) == self._last_block_count
            and current_blk == self._last_current_blk
            and current_ch == self._last_chapter_idx
        )
        if unchanged:
            return
        self._last_block_count = len(blocks)
        self._last_current_blk = current_blk
        self._last_chapter_idx = current_ch
        self._rebuild_text_browser(blocks, current_blk)

    def _rebuild_text_browser(self, blocks: list, current_blk: int) -> None:
        parts = [
            "<html><body style='"
            "background-color:#181825; color:#cdd6f4;"
            "font-family:Georgia,serif; font-size:14px; line-height:1.75;"
            "margin:8px; padding:0;'>"
        ]
        for ch_idx, blk_idx, text in blocks:
            parts.append(self._block_html(ch_idx, blk_idx, text, blk_idx == current_blk))
        parts.append("</body></html>")
        self._text_browser.setHtml("".join(parts))
        if current_blk >= 0:
            self._text_browser.scrollToAnchor(f"b{current_blk}")

    @staticmethod
    def _block_html(ch_idx: int, blk_idx: int, text: str, active: bool) -> str:
        bg = "background-color:#1e3358;" if active else ""
        fg = "color:#89b4fa;" if active else "color:#cdd6f4;"
        num_color = "#89b4fa" if active else "#585b70"
        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        href = f"block://{ch_idx}/{blk_idx}"
        return (
            f'<p id="b{blk_idx}" style="{bg}padding:6px 10px;'
            f'border-radius:5px;margin:3px 0;">'
            f'<a href="{href}" style="{fg}text-decoration:none;">'
            f'<span style="color:{num_color};font-size:11px;">[{blk_idx + 1}]&nbsp;</span>'
            f"{safe}</a></p>"
        )

    # ── timer ────────────────────────────────────────────────────────

    def _on_timer(self) -> None:
        self._tick += 1
        self._maybe_auto_advance()
        if self._tick % self._STATUS_REFRESH_TICKS == 0:
            self._refresh_status()
            self._refresh_text_view()

    def _maybe_auto_advance(self) -> None:
        """Avanza al siguiente bloque cuando el TTS termina y estamos en modo play."""
        if self._app.is_playing() and not self._app.is_tts_speaking():
            self._app.next()

    def _refresh_status(self) -> None:
        st = self._app.status()
        if st:
            self._update_now_playing(st.title, st.chapter_idx, st.block_idx)
            self._sync_chapter_combo(st.chapter_idx)
            self._status_bar.showMessage(
                f"▶  {st.title[:40]}  —  cap {st.chapter_idx + 1}, bloque {st.block_idx + 1}"
            )

    def _update_now_playing(self, title: str, ch: int, blk: int) -> None:
        short = title[:52] + "…" if len(title) > 52 else title
        self._now_playing_title.setText(short)
        self._now_playing_sub.setText(f"Capítulo {ch + 1}  ·  Bloque {blk + 1}")

    # ── cierre ───────────────────────────────────────────────────────

    def closeEvent(self, event) -> None:  # noqa: N802
        self._timer.stop()
        if self._import_thread and self._import_thread.isRunning():
            self._import_thread.quit()
            self._import_thread.wait(2000)
        self._app.shutdown()
        event.accept()
