import secrets


def get_new_id(organisation="Naturkundemuseum-Potsdam"):
    """Construct a cryptographically random 40-char hex user id."""
    _ = organisation  # Keep arg for backward compatibility with existing call sites.
    return secrets.token_hex(20)
