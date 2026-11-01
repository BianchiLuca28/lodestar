"""Typed domain errors. The API maps them to HTTP errors with a message key for the UI."""


class DomainError(Exception):
    """Base class; `key` is an i18n message key the UI translates."""

    key = "error.domain"


class InvalidAmount(DomainError):
    key = "error.invalidAmount"


class InvalidTransaction(DomainError):
    key = "error.invalidTransaction"
