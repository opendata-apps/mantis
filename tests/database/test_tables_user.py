"""Tests for the Users database table functionality."""

from sqlalchemy import select
from app.database.users import TblUsers


def test_table_user_by_name(session):
    """Test retrieving a user by name pattern."""
    result = session.scalars(
        select(TblUsers).where(TblUsers.user_name.like("Losekann%"))
    ).all()

    assert any(user.user_name == "Losekann Z." for user in result)
