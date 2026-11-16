import pandas as pd
import pytest
from rescueflow.demo import inventory_catalog
from rescueflow.validation import validate_catalog


def test_validate_catalog_requires_pack_sizing_columns():
    catalog = inventory_catalog()
    catalog_dropped = catalog.drop(columns=["pack_size"])
    with pytest.raises(ValueError, match="Missing inventory columns"):
        validate_catalog(catalog_dropped)


def test_validate_catalog_rejects_invalid_pack_size():
    catalog = inventory_catalog()
    catalog.loc[0, "pack_size"] = 0
    with pytest.raises(ValueError, match="at least 1 unit"):
        validate_catalog(catalog)


def test_validate_catalog_rejects_negative_moq():
    catalog = inventory_catalog()
    catalog.loc[0, "min_order_qty"] = -5
    with pytest.raises(ValueError, match="Minimum order quantity must be non-negative"):
        validate_catalog(catalog)
