"""Build the tsquery behind the reviewer search box.

Every word the reviewer types matches as a prefix ("Potsd" finds Potsdam), and
all words must occur. websearch_to_tsquery has no prefix syntax, so this builds
to_tsquery input; its phrase, `or` and `-word` operators do not apply here.
https://www.postgresql.org/docs/16/textsearch-controls.html#TEXTSEARCH-PARSING-QUERIES

to_tsquery stems a prefix like any word and drops german stopwords, so
"Langerwis" misses Langerwisch (indexed as 'langerw') and "Die" matches nothing.
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
