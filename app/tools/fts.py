"""Build the tsquery behind the reviewer search box.

PostgreSQL matches whole words, so "Potsd" found 0 reports and "Hauptstr"
found 10 -- against 3336 and 490 once the term is a prefix. Prefix matching
needs to_tsquery: websearch_to_tsquery has no syntax for it. The shape here is
pg_search's -- split on whitespace, strip the characters that would end a
quoted lexeme, quote each term with ':*' appended, join with '&':

    https://github.com/Casecommons/pg_search/blob/master/lib/pg_search/features/tsearch.rb
    https://github.com/discourse/discourse/blob/main/lib/search.rb

Discourse builds the same thing with prefix_match defaulting to true.

Dropping websearch_to_tsquery drops its operators too: quoted phrases, `or`
and `-word` exclusion no longer do anything. Both projects accept that.

Known misses, over 1202 prefixes of the 200 most common Ortsnamen (15, 1.2%):

* to_tsquery stems the prefix like any other word, and the german stemmer
  strips derivational endings. Langerwisch indexes as 'langerw', so "Langerw"
  finds it and "Langerwis" does not -- typing more makes the hit disappear.
  7 of the 15, unfixable while the vector is german-stemmed.
  https://www.postgresql.org/docs/16/textsearch-controls.html#TEXTSEARCH-PARSING-QUERIES
* A prefix that is itself a german stopword compiles to an empty query, so
  "Die" never finds Diedersdorf though 'diedersdorf' is in the vector. 8 of
  the 15, all at 3 to 5 characters.

Already tried: OR-ing in a second to_tsquery('simple', ...) fixes the stopword
half with no false hits, but costs 6x on the search (7 ms -> 42 ms over 29k
reports) to recover eight three-character queries. Querying 'simple' alone is
far worse -- 200 of the 1202 miss, because the vector is german-stemmed.

Matches inside a word ("otsdam" for Potsdam) are out of reach for any tsquery.
pg_trgm is the tool for that and would be its own index:
https://www.postgresql.org/docs/16/pgtrgm.html
"""

import re

# pg_search's DISALLOWED_TSQUERY_CHARACTERS, plus the curly quotes its 2.3.7
# release stripped and current master no longer does. Keeping them is
# deliberate: they do not break to_tsquery here (no unaccent in this config),
# but leaving them in makes O’Brien compile to a phrase match while O'Brien
# becomes two AND-ed terms, and one apostrophe should not change the search.
# The straight quote is the one that must go -- it would close the quoted
# lexeme and let the rest of the term be read as tsquery syntax.
_DISALLOWED_TSQUERY_CHARACTERS = re.compile(r"['?\\:‘’ʻʼ]")


def prefix_tsquery(text: str | None) -> str | None:
    """Return a prefix tsquery for *text*, or None if it holds no terms.

    None means the input carried nothing searchable -- it was empty, or only
    punctuation. The caller decides what that means; both call sites treat it
    as a search that matches nothing, which is what websearch_to_tsquery did
    with the same input.
    """
    if not text:
        return None
    terms = _DISALLOWED_TSQUERY_CHARACTERS.sub(" ", text).split()
    if not terms:
        return None
    return " & ".join(f"'{term}':*" for term in terms)
