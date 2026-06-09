"""User role enum for Mantis Tracker.

Defines the role values stored in users.user_rolle (VARCHAR(1)).
"""

from enum import StrEnum


class UserRole(StrEnum):
    """Role enum for user access control.

    REPORTER: Regular user who submits sighting reports
    FINDER: Person who found the animal when distinct from the reporter
        (created alongside a report; has no own access)
    REVIEWER: Admin/reviewer who validates and approves reports
    """

    REPORTER = "1"
    FINDER = "2"
    REVIEWER = "9"
