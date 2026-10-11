import secrets


def get_new_id() -> str:
    """Construct a cryptographically random 40-char hex user id."""
    return secrets.token_hex(20)
