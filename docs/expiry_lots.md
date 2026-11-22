# Expiry-Lot Aware Food Rescue & Inventory Assumptions

## Overview
RescueFlow AI supports optional lot-level inventory tracking with explicit expiration dates. This enables granular food rescue candidate identification using First-In, First-Out (FIFO) principles.

## Core Rules & Safety Assumptions
1. **Never Claim Unknown Expiry Dates:** If inventory lots lack expiration dates (or if lot tracking is disabled, falling back to aggregate SKU catalog stock), expiration status is strictly classified as `Unknown Expiry` and rescue candidate units are reported as `0.0`. We never assume unknown stock is safe or expired.
2. **FIFO Lot Granularity:** When expiry dates are provided, lots are evaluated independently. Lots past their expiry date (`days_to_expiry < 0`) are categorized as `Expired` and flagged for immediate inspection or rescue triage. Lots expiring within 3 days are evaluated against expected demand.
3. **Human Review Mandate:** Lot-level rescue candidates are screening proxies only. Physical inspection of odor, packaging integrity, and adherence to local food safety regulations is mandatory before any donation or redistribution.
