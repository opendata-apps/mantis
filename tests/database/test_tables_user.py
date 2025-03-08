"""Tests for the Users database table functionality."""
from app.database.users import TblUsers


def test_table_user_by_name(session):
    """Test retrieving a user by name pattern."""
    # Use SQLAlchemy ORM instead of raw SQL
    result = session.query(TblUsers).filter(
        TblUsers.user_name.like('Losekann%')
    ).all()
    
    # Verify the expected user is found
    assert any(user.user_name == 'Losekann Z.' for user in result)
    assert len(result) > 0


def test_table_user_by_contact(session):
    """Test retrieving users by contact email pattern."""
    # Use SQLAlchemy ORM instead of raw SQL
    result = session.query(TblUsers).filter(
        TblUsers.user_kontakt.like('%com')
    ).all()
    
    # Verify the expected number of records
    assert len(result) == 7
