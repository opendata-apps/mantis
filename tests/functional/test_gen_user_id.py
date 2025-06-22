import re
from app.tools.gen_user_id import get_new_id


def test_generated_user_id_has_correct_length():
    """Test that generated user IDs are exactly 40 characters long."""
    userid = get_new_id()
    assert len(userid) == 40


def test_generated_user_id_format():
    """Test that generated user IDs contain only valid hexadecimal characters."""
    userid = get_new_id()
    # SHA-1 produces 40 character hex strings
    assert re.match(r'^[a-f0-9]{40}$', userid), f"Invalid user ID format: {userid}"


def test_generated_user_ids_are_unique():
    """Test that multiple generated IDs are unique."""
    ids = [get_new_id() for _ in range(100)]
    unique_ids = set(ids)
    assert len(unique_ids) == 100, "Generated IDs should be unique"
