"""AND word prefixes for the reviewer's PostgreSQL simple-text search.

The database normalizes German transliterations in both index and query.
Quoted terms keep typed punctuation from becoming search operators.
"""


def prefix_tsquery(text: str) -> str:
    """Return to_tsquery input that ANDs each word of *text* as a prefix.

    Each word becomes a quoted lexeme with its quotes and backslashes doubled,
    the quoting rule for tsquery input, so nothing typed is read as an operator:
    https://www.postgresql.org/docs/16/datatype-textsearch.html#DATATYPE-TSQUERY

    >>> prefix_tsquery("Potsd Haupt")
    "'Potsd':* & 'Haupt':*"
    >>> prefix_tsquery("O'Brien a|b")
    "'O''Brien':* & 'a|b':*"
    """
    terms = text.replace("\\", "\\\\").replace("'", "''").split()
    return " & ".join(f"'{term}':*" for term in terms)
