"""
Maroon Council Core — MEPP Financial Engine (v4.0)
Control Plane §1.2: Maroon Economic Processing Protocol.

Core Financial Laws:
  - Sovereign Logistics Ceiling: Council-governed, community-protective cap on delivery fees
  - Split-Tender Orchestration: EBT/SNAP dynamically separated at the transaction microsecond
  - Revenue-Linked Subscription (RLS): Vendor fees capped at $300/month
  - Sovereign Currency Parity: 1 Maroon Buck = 1 USD
  - Zero Penny Drift: All calculations use integer cents — no floating-point rounding

The Freedmen's Bank Firewall:
  Every financial mechanism assumes external capital is at risk of confiscation.
  Sovereign custody of assets. Offline-first. Immune to regulatory freezes.
"""
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional


# ---------------------------------------------------------------------------
# Constants — Immutable Financial Laws
# ---------------------------------------------------------------------------

# Sovereign Logistics Ceiling: governed by The Council, never extractive
# This value is set by Council governance vote, not hardcoded to a specific dollar amount
SOVEREIGN_LOGISTICS_CEILING_CENTS: int = 1499  # Default Council-set ceiling (in cents)

# Revenue-Linked Subscription cap
RLS_MONTHLY_CAP_CENTS: int = 30000  # $300.00/month — protects small vendors

# Sovereign Currency parity
MAROON_BUCK_USD_PARITY: Decimal = Decimal("1.00")

# EBT-eligible category codes (USDA SNAP categories)
EBT_ELIGIBLE_CATEGORIES = {
    "produce", "dairy", "meat", "seafood", "bakery", "cereal",
    "snacks", "beverages_nonalcoholic", "canned_goods", "frozen_foods",
    "baby_food", "seeds_plants",  # Seeds/plants that produce food
}

# EBT-ineligible (always paid via fiat/Maroon Bucks)
EBT_INELIGIBLE_CATEGORIES = {
    "alcohol", "tobacco", "supplements", "hot_prepared_food",
    "household_nonfood", "delivery_fee", "platform_fee", "tip",
}


# ---------------------------------------------------------------------------
# Penny-Perfect Math — Integer Cents Only
# ---------------------------------------------------------------------------

def to_cents(dollars: float) -> int:
    """Convert dollar amount to integer cents. Zero Penny Drift enforcement."""
    return int(Decimal(str(dollars)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) * 100)


def to_dollars(cents: int) -> float:
    """Convert cents back to dollars for display."""
    return round(cents / 100, 2)


# ---------------------------------------------------------------------------
# Split-Tender Engine — Control Plane §1.2
# ---------------------------------------------------------------------------

class SplitTenderResult:
    """Result of a split-tender calculation. All values in integer cents."""

    def __init__(self):
        self.ebt_amount_cents: int = 0
        self.maroon_bucks_cents: int = 0
        self.fiat_amount_cents: int = 0
        self.delivery_fee_cents: int = 0
        self.platform_fee_cents: int = 0
        self.total_cents: int = 0
        self.items_breakdown: list = []
        self.truth_hash: str = ""

    def to_dict(self) -> dict:
        return {
            "ebt_amount": to_dollars(self.ebt_amount_cents),
            "maroon_bucks": to_dollars(self.maroon_bucks_cents),
            "fiat_amount": to_dollars(self.fiat_amount_cents),
            "delivery_fee": to_dollars(self.delivery_fee_cents),
            "platform_fee": to_dollars(self.platform_fee_cents),
            "total": to_dollars(self.total_cents),
            "items": self.items_breakdown,
            "truth_hash": self.truth_hash,
            "penny_drift_check": self._verify_zero_drift(),
        }

    def _verify_zero_drift(self) -> dict:
        """
        Verify zero penny drift — payment methods MUST equal total.
        Fiat already includes delivery_fee + platform_fee, so we only
        sum the three payment channels: EBT + Maroon Bucks + Fiat.
        """
        payment_sum = (
            self.ebt_amount_cents
            + self.maroon_bucks_cents
            + self.fiat_amount_cents
        )
        return {
            "total_cents": self.total_cents,
            "payment_sum_cents": payment_sum,
            "drift_cents": abs(self.total_cents - payment_sum),
            "is_penny_perfect": payment_sum == self.total_cents,
        }


def split_tender(
    items: list,
    delivery_fee_dollars: float = 0.0,
    platform_fee_dollars: float = 0.0,
    maroon_bucks_available_dollars: float = 0.0,
    has_ebt: bool = False,
) -> SplitTenderResult:
    """
    Execute the MEPP Split-Tender Protocol.

    Separates EBT-eligible items from non-eligible at the transaction microsecond.
    Enforces the Sovereign Logistics Ceiling on delivery fees.
    All math in integer cents — zero penny drift guaranteed.

    Args:
        items: List of dicts with 'name', 'price', 'category', 'quantity'
        delivery_fee_dollars: Requested delivery fee
        platform_fee_dollars: Platform service fee
        maroon_bucks_available_dollars: Customer's Maroon Bucks balance
        has_ebt: Whether customer has an active EBT card
    """
    result = SplitTenderResult()

    # --- Enforce Sovereign Logistics Ceiling ---
    delivery_fee_cents = to_cents(delivery_fee_dollars)
    if delivery_fee_cents > SOVEREIGN_LOGISTICS_CEILING_CENTS:
        delivery_fee_cents = SOVEREIGN_LOGISTICS_CEILING_CENTS
    result.delivery_fee_cents = delivery_fee_cents

    platform_fee_cents = to_cents(platform_fee_dollars)
    result.platform_fee_cents = platform_fee_cents

    maroon_bucks_cents = to_cents(maroon_bucks_available_dollars)

    # --- Split items by EBT eligibility ---
    ebt_eligible_cents = 0
    non_ebt_cents = 0

    for item in items:
        item_total_cents = to_cents(item["price"]) * item.get("quantity", 1)
        category = item.get("category", "").lower()
        is_eligible = category in EBT_ELIGIBLE_CATEGORIES

        item_record = {
            "name": item["name"],
            "price_cents": to_cents(item["price"]),
            "quantity": item.get("quantity", 1),
            "total_cents": item_total_cents,
            "category": category,
            "ebt_eligible": is_eligible and has_ebt,
        }
        result.items_breakdown.append(item_record)

        if is_eligible and has_ebt:
            ebt_eligible_cents += item_total_cents
        else:
            non_ebt_cents += item_total_cents

    # --- Allocate EBT ---
    result.ebt_amount_cents = ebt_eligible_cents

    # --- Allocate Maroon Bucks to non-EBT items first ---
    remaining_non_ebt = non_ebt_cents
    maroon_applied = min(maroon_bucks_cents, remaining_non_ebt)
    result.maroon_bucks_cents = maroon_applied
    remaining_non_ebt -= maroon_applied

    # --- Fiat covers the rest (non-EBT items + fees) ---
    result.fiat_amount_cents = remaining_non_ebt + delivery_fee_cents + platform_fee_cents

    # --- Total ---
    result.total_cents = (
        ebt_eligible_cents + non_ebt_cents + delivery_fee_cents + platform_fee_cents
    )

    # --- Truth Teller Hash ---
    canonical = json.dumps(result.to_dict(), sort_keys=True, default=str)
    result.truth_hash = hashlib.sha512(canonical.encode()).hexdigest()[:32]

    return result


# ---------------------------------------------------------------------------
# RLS Cap Enforcement — Control Plane §1.2
# ---------------------------------------------------------------------------

def enforce_rls_cap(
    vendor_id: str,
    current_month_fees_cents: int,
    proposed_fee_cents: int,
) -> dict:
    """
    Enforce the Revenue-Linked Subscription cap ($300/month).
    Protects small vendors from predatory platform extraction.
    """
    remaining_capacity = RLS_MONTHLY_CAP_CENTS - current_month_fees_cents

    if remaining_capacity <= 0:
        return {
            "vendor_id": vendor_id,
            "fee_charged_cents": 0,
            "fee_charged": 0.0,
            "capped": True,
            "reason": "RLS monthly cap reached — vendor protected",
            "monthly_total_cents": current_month_fees_cents,
            "monthly_total": to_dollars(current_month_fees_cents),
            "cap": to_dollars(RLS_MONTHLY_CAP_CENTS),
        }

    actual_fee = min(proposed_fee_cents, remaining_capacity)
    return {
        "vendor_id": vendor_id,
        "fee_charged_cents": actual_fee,
        "fee_charged": to_dollars(actual_fee),
        "capped": actual_fee < proposed_fee_cents,
        "reason": "Fee applied" if actual_fee == proposed_fee_cents else "Partially capped by RLS",
        "monthly_total_cents": current_month_fees_cents + actual_fee,
        "monthly_total": to_dollars(current_month_fees_cents + actual_fee),
        "cap": to_dollars(RLS_MONTHLY_CAP_CENTS),
    }


# ---------------------------------------------------------------------------
# CLI Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("MEPP FINANCIAL ENGINE — Split-Tender & RLS Test")
    print("=" * 60)

    # Test split-tender with EBT
    items = [
        {"name": "Organic Apples", "price": 4.99, "category": "produce", "quantity": 2},
        {"name": "Whole Milk", "price": 3.49, "category": "dairy", "quantity": 1},
        {"name": "Hot Rotisserie Chicken", "price": 8.99, "category": "hot_prepared_food", "quantity": 1},
        {"name": "Paper Towels", "price": 5.99, "category": "household_nonfood", "quantity": 1},
    ]

    print("\n--- Split-Tender (EBT Customer) ---")
    result = split_tender(
        items=items,
        delivery_fee_dollars=25.00,  # Will be capped by Sovereign Logistics Ceiling
        platform_fee_dollars=1.99,
        maroon_bucks_available_dollars=5.00,
        has_ebt=True,
    )
    print(json.dumps(result.to_dict(), indent=2))

    print(f"\n--- Delivery fee was capped from $25.00 to ${to_dollars(SOVEREIGN_LOGISTICS_CEILING_CENTS)} ---")

    # Test RLS cap
    print("\n--- RLS Cap Enforcement ---")
    rls_result = enforce_rls_cap(
        vendor_id="vendor_small_bakery",
        current_month_fees_cents=29500,  # $295.00 already charged
        proposed_fee_cents=1000,  # $10.00 proposed
    )
    print(json.dumps(rls_result, indent=2))

    # Verify zero penny drift
    drift = result.to_dict()["penny_drift_check"]
    print(f"\n--- Penny Drift Check ---")
    print(f"Total: {drift['total_cents']} cents")
    print(f"Payment sum: {drift['payment_sum_cents']} cents")
    print(f"Drift: {drift['drift_cents']} cents")
    print(f"Penny Perfect: {drift['is_penny_perfect']}")
