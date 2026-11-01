from lodestar.config.models import AppConfig
from lodestar.domain.ledger import Catalog


def catalog_of(config: AppConfig) -> Catalog:
    """The accounts and categories a ledger line may use."""
    return Catalog(
        accounts=frozenset(a.name for a in config.accounts),
        categories={c.name: frozenset(c.subcategories) for c in config.categories},
    )
