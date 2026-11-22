import pandas as pd
import pytest
from rescueflow.demo import inventory_catalog
from rescueflow.inventory import parse_expiry_lots


def test_parse_expiry_lots_fallback_unknown_expiry():
    cat = inventory_catalog()
    lots_result = parse_expiry_lots(None, cat, as_of="2026-11-05")
    assert len(lots_result) == len(cat)
    assert (lots_result.expiry_status == "Unknown Expiry").all()
    assert (lots_result.rescue_candidate_units == 0.0).all()
    assert lots_result.expiry_date.isna().all()


def test_parse_expiry_lots_with_valid_and_expired_lots():
    cat = inventory_catalog()
    lots_data = pd.DataFrame([
        {"sku": "BAN-01", "lot_id": "LOT-BAN-EXPIRED", "expiry_date": "2026-11-01", "lot_stock": 50.0},
        {"sku": "BAN-01", "lot_id": "LOT-BAN-FRESH", "expiry_date": "2026-11-20", "lot_stock": 100.0},
        {"sku": "TOM-02", "lot_id": "LOT-TOM-UNKNOWN", "expiry_date": None, "lot_stock": 30.0},
    ])
    res = parse_expiry_lots(lots_data, cat, as_of="2026-11-05")
    assert len(res) == 3

    expired_row = res[res.lot_id == "LOT-BAN-EXPIRED"].iloc[0]
    assert expired_row.expiry_status == "Expired"
    assert expired_row.rescue_candidate_units == 50.0

    fresh_row = res[res.lot_id == "LOT-BAN-FRESH"].iloc[0]
    assert fresh_row.expiry_status == "Fresh"
    assert fresh_row.rescue_candidate_units == 0.0

    unknown_row = res[res.lot_id == "LOT-TOM-UNKNOWN"].iloc[0]
    assert unknown_row.expiry_status == "Unknown Expiry"
    assert unknown_row.rescue_candidate_units == 0.0


def test_parse_expiry_lots_missing_columns_raises():
    cat = inventory_catalog()
    bad_lots = pd.DataFrame([{"sku": "BAN-01", "lot_stock": 10.0}])
    with pytest.raises(ValueError, match="Missing lot columns"):
        parse_expiry_lots(bad_lots, cat, as_of="2026-11-05")
