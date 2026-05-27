"""Shared constants for the paper-distiller package."""

from __future__ import annotations

from enum import StrEnum


class Category(StrEnum):
    A_CORE = "A_core"
    B_RELATED = "B_related"
    C_BACKGROUND = "C_background"


CATEGORIES = tuple(category.value for category in Category)

NOTE_DIRS = (
    "literature",
    "theorem_cards",
    "proof_cards",
    "writing_patterns",
    "verification",
)

READING_STATUS_FIELDS = (
    "file_name",
    "extracted",
    "distilled",
    "theorem_extracted",
    "proof_extracted",
    "reviewed",
    "audited",
    "audit_file",
    "human_verified",
    "revision_needed",
)

BIBLIOGRAPHY_FIELDS = (
    "title",
    "authors",
    "year",
    "venue",
    "topic",
    "priority",
    "status",
    "file_name",
    "notes_file",
)

SUPPLEMENT_SUFFIX = "_Supplement"
