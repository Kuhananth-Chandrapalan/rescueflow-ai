import pandas as pd
import pytest
from rescueflow.demo import inventory_catalog
from rescueflow.warehouse import add_warehouse_stock, filter_warehouse_catalog


def test_add_warehouse_stock():
    cat = inventory_catalog()
    multi = add_warehouse_stock(cat, ["Hub A", "Hub B"])
    assert "warehouse" in multi.columns
    assert len(multi) == len(cat) * 2
    assert set(multi.warehouse.unique()) == {"Hub A", "Hub B"}


def test_filter_warehouse_catalog():
    cat = inventory_catalog()
    multi = add_warehouse_stock(cat, ["Hub A", "Hub B"])
    filtered_a = filter_warehouse_catalog(multi, "Hub A")
    assert len(filtered_a) == len(cat)
    assert (filtered_a.warehouse == "Hub A").all()

    all_view = filter_warehouse_catalog(multi, "All Warehouses")
    assert len(all_view) == len(cat)
    assert "warehouse" not in all_view.columns
    assert all_view.stock_units.sum() == multi.stock_units.sum()


def test_single_warehouse_fallback():
    cat = inventory_catalog()
    filtered = filter_warehouse_catalog(cat, "Hub A")
    assert len(filtered) == len(cat)
