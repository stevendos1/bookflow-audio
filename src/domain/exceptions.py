class DomainError(Exception):
    """Excepción base para todos los errores del dominio."""

    def __init__(self, message: str, context: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.context = context or {}
