"""
Feedback source enum for Mantis Tracker.

Defines how users discovered the project. Values stored as VARCHAR
in user_feedback.feedback_source. Matches the ReportStatus pattern.
"""

from enum import StrEnum


class FeedbackSource(StrEnum):
    """How the user heard about the Mantis project."""

    EVENT = "EVENT"       # Auf einer Veranstaltung
    FLYER = "FLYER"       # Flyer/Folder des Projektes
    PRESS = "PRESS"       # Presse
    TV = "TV"             # Fernsehbeitrag
    INTERNET = "INTERNET" # Internetrecherche
    SOCIAL = "SOCIAL"     # Social Media
    FRIENDS = "FRIENDS"   # Freunde, Bekannte, Kollegen
    OTHER = "OTHER"       # Andere

    @classmethod
    def get_display_name(cls, value: str) -> str:
        """Return German display name for a feedback source value."""
        display_names = {
            cls.EVENT.value: "Auf einer Veranstaltung",
            cls.FLYER.value: "Flyer/Folder des Projektes",
            cls.PRESS.value: "Presse",
            cls.TV.value: "Fernsehbeitrag",
            cls.INTERNET.value: "Internetrecherche",
            cls.SOCIAL.value: "Social Media",
            cls.FRIENDS.value: "Freunde, Bekannte, Kollegen",
            cls.OTHER.value: "Andere",
        }
        return display_names.get(value, value)

    @classmethod
    def get_placeholder(cls, value: str) -> str:
        """Return placeholder text for the detail input field."""
        placeholders = {
            cls.EVENT.value: "z.B. Name der Veranstaltung, Ort",
            cls.FLYER.value: "z.B. wo haben Sie den Flyer erhalten?",
            cls.PRESS.value: "z.B. Name der Zeitung/Zeitschrift",
            cls.TV.value: "z.B. Name des Senders/der Sendung",
            cls.INTERNET.value: "z.B. Suchmaschine, Website-Name",
            cls.SOCIAL.value: "z.B. Facebook, Instagram, Twitter",
            cls.FRIENDS.value: "z.B. Freund, Kollege, Familie",
            cls.OTHER.value: "Bitte beschreiben Sie, wie Sie von uns erfahren haben",
        }
        return placeholders.get(value, "")

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        """Return WTForms-compatible choices list with blank default."""
        return [("", "-- Bitte wählen --")] + [
            (s.value, cls.get_display_name(s.value)) for s in cls
        ]

    @classmethod
    def values(cls) -> list[str]:
        """Return list of all enum values."""
        return [s.value for s in cls]
