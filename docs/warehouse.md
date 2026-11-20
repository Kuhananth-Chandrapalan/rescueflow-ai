# Multi-warehouse stock view & projected coverage

## Assumptions and Model Limits
- **Stock Partitioning:** Synthetic demonstration catalogs are partitioned across multiple warehouses (Central Warehouse, North Hub, South Hub) using heuristic initial distribution factors (~50%, 30%, 20%).
- **Fallback Behavior:** If single-warehouse CSV uploads are used, the system preserves single-warehouse behavior seamlessly without requiring warehouse identifiers.
- **Projected Coverage:** Days of cover are estimated by comparing warehouse-specific on-demand levels against local stock counts divided by expected daily predictions.

## User-facing Interpretation
Operators can filter inventory and replenishment queues by specific site or view aggregated totals across all warehouses to optimize transfer and replenishment decisions.
