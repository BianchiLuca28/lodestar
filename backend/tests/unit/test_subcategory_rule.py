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


def test_without_altro_or_a_known_category_it_stays_empty() -> None:
    assert default_subcategory("Varie", None, CATALOG) is None
    assert default_subcategory("Sconosciuta", None, CATALOG) is None
