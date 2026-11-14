from lodestar.domain.ledger import FALLBACK_SUBCATEGORY, Catalog, default_subcategory

CATALOG = Catalog(
    accounts=frozenset({"A"}),
    categories={"Regali": frozenset({"Compleanno", "Altro"}), "Varie": frozenset()},
)


def test_no_subcategory_becomes_altro_when_the_category_has_one() -> None:
    assert FALLBACK_SUBCATEGORY == "Altro"
    assert default_subcategory("Regali", None, CATALOG) == "Altro"
    assert default_subcategory("Regali", "", CATALOG) == "Altro"


def test_a_given_subcategory_is_kept() -> None:
    assert default_subcategory("Regali", "Compleanno", CATALOG) == "Compleanno"


def test_a_category_that_lists_no_subcategories_also_gets_altro() -> None:
    # An empty list means any subcategory is allowed, "Altro" included (user's option b).
    assert default_subcategory("Varie", None, CATALOG) == "Altro"


def test_an_explicit_list_without_altro_or_an_unknown_category_stays_empty() -> None:
    strict = Catalog(frozenset({"A"}), {"Bollette": frozenset({"Luce", "Gas"})})
    assert default_subcategory("Bollette", None, strict) is None
    assert default_subcategory("Sconosciuta", None, CATALOG) is None
