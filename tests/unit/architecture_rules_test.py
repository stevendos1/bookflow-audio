import ast
from pathlib import Path


class ImportVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imports: set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.add(alias.name.split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.imports.add(node.module.split(".")[0])
        self.generic_visit(node)


def get_ast_imports(filepath: Path) -> set[str]:
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=str(filepath))
        except SyntaxError:
            return set()

    visitor = ImportVisitor()
    visitor.visit(tree)
    return visitor.imports


_DOMAIN_FORBIDDEN = frozenset(
    {
        "sqlite3",
        "fitz",
        "pymupdf",
        "pyttsx3",
        "ebooklib",
        "bs4",
        "subprocess",
        "requests",
        "PySide6",
    }
)

_APPLICATION_FORBIDDEN = frozenset(
    {
        "sqlite3",
        "fitz",
        "pymupdf",
        "pyttsx3",
        "ebooklib",
        "bs4",
        "subprocess",
        "PySide6",
    }
)

_PDF_ADAPTER_ONLY = frozenset({"fitz", "pymupdf"})

_PYSIDE6_ONLY = frozenset({"PySide6"})


def test_domain_architecture_rules():
    """Domain layer must not import from any external library or other layers."""
    domain_dir = Path("src/domain")
    if not domain_dir.exists():
        return

    for py_file in domain_dir.rglob("*.py"):
        imports = get_ast_imports(py_file)
        violations = imports.intersection(_DOMAIN_FORBIDDEN)
        msg = f"Forbidden imports {violations} found in {py_file} (Domain Layer)"
        assert not violations, msg


def test_application_architecture_rules():
    """Application layer must not import from external libs (except pure ones) or infrastructure."""
    app_dir = Path("src/application")
    if not app_dir.exists():
        return

    for py_file in app_dir.rglob("*.py"):
        imports = get_ast_imports(py_file)
        violations = imports.intersection(_APPLICATION_FORBIDDEN)
        msg = f"Forbidden imports {violations} found in {py_file} (Application Layer)"
        assert not violations, msg


def test_fitz_only_in_pdf_parser_adapter():
    """fitz/pymupdf must only be imported in the PDF parser adapter, nowhere else in src/."""
    src_dir = Path("src")
    pdf_adapter = Path("src/adapters/secondary/parsers/pdf_parser.py")

    for py_file in src_dir.rglob("*.py"):
        if py_file.resolve() == pdf_adapter.resolve():
            continue
        imports = get_ast_imports(py_file)
        violations = imports.intersection(_PDF_ADAPTER_ONLY)
        msg = (
            f"fitz/pymupdf imported outside pdf_parser adapter in {py_file}. "
            "PDF parsing must stay encapsulated in the adapter."
        )
        assert not violations, msg


def test_pyside6_only_in_gui_modules():
    """PySide6 must only be imported in the GUI primary adapter and gui_main.py."""
    src_dir = Path("src")
    gui_modules = {
        Path("src/adapters/primary/gui.py").resolve(),
        Path("src/infrastructure/gui_main.py").resolve(),
    }

    for py_file in src_dir.rglob("*.py"):
        if py_file.resolve() in gui_modules:
            continue
        imports = get_ast_imports(py_file)
        violations = imports.intersection(_PYSIDE6_ONLY)
        msg = (
            f"PySide6 imported outside GUI modules in {py_file}. "
            "Qt dependencies must stay in adapters/primary/gui.py and gui_main.py."
        )
        assert not violations, msg
