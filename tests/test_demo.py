from rescueflow.demo import demo_history, inventory_catalog


def test_history_is_reproducible():
    a = demo_history(days=90)
    b = demo_history(days=90)
    assert a.equals(b)
    assert a.groupby('sku').size().eq(90).all()


def test_catalog_has_unique_items():
    items = inventory_catalog()
    assert len(items) >= 8
    assert items.sku.is_unique
    assert items.unit_price.gt(items.unit_cost).all()
