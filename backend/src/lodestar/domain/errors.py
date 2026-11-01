"""Typed domain errors. The API maps them to HTTP errors with a message key for the UI."""


class DomainError(Exception):
    """Base class; `key` is an i18n message key the UI translates."""

    key = "error.domain"


class InvalidAmount(DomainError):
    key = "error.invalidAmount"


class InvalidTransaction(DomainError):
    key = "error.invalidTransaction"


class FieldError(DomainError):
    """A single field of an input is invalid."""

    def __init__(self, key: str, field: str, message: str) -> None:
        super().__init__(message)
        self.key = key
        self.field = field


class NotFound(DomainError):
    key = "error.notFound"


class Conflict(DomainError):
    def __init__(self, key: str, message: str) -> None:
        super().__init__(message)
        self.key = key
