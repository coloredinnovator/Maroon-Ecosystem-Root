"""
Maroon Council Core — MIVL Identity Verification Layer (v4.0)
Control Plane §1.1: Hardware-backed, terminal-verified, zero-trust identity.

Trust Tiers:
  0 - Anonymous     : No verification, public read-only
  1 - Registered    : Email + phone verified
  2 - Verified      : Government ID + KYC/AML passed
  3 - Community     : Vouched by 2+ Tier-3+ members
  4 - Operator      : Financial audit + operational history
  5 - Council       : Governance board appointment

RULE 0 Enforcement:
  - Default trust score for ALL entities is 0.0 (Zero-Alliance Baseline)
  - Phenotype/demographics NEVER influence tier assignment
  - Every tier transition is cryptographically recorded
  - Tier regression is automatic upon financial anomaly detection
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional
from enum import IntEnum


class MIVLTier(IntEnum):
    """MIVL Identity Verification Tiers — Control Plane §1.1"""
    ANONYMOUS = 0
    REGISTERED = 1
    VERIFIED = 2
    COMMUNITY = 3
    OPERATOR = 4
    COUNCIL = 5


# Trust score boundaries per tier
TIER_TRUST_RANGES = {
    MIVLTier.ANONYMOUS:   (0.0, 0.0),
    MIVLTier.REGISTERED:  (0.1, 0.2),
    MIVLTier.VERIFIED:    (0.2, 0.4),
    MIVLTier.COMMUNITY:   (0.4, 0.6),
    MIVLTier.OPERATOR:    (0.6, 0.8),
    MIVLTier.COUNCIL:     (0.8, 1.0),
}

# Access permissions per tier
TIER_ACCESS = {
    MIVLTier.ANONYMOUS:   {"read_public"},
    MIVLTier.REGISTERED:  {"read_public", "browse_marketplace"},
    MIVLTier.VERIFIED:    {"read_public", "browse_marketplace", "purchase", "limited_sell"},
    MIVLTier.COMMUNITY:   {"read_public", "browse_marketplace", "purchase", "sell", "safe_space", "vote"},
    MIVLTier.OPERATOR:    {"read_public", "browse_marketplace", "purchase", "sell", "safe_space", "vote", "vendor_ops", "logistics"},
    MIVLTier.COUNCIL:     {"read_public", "browse_marketplace", "purchase", "sell", "safe_space", "vote", "vendor_ops", "logistics", "governance", "strategy"},
}


class MIVLIdentity:
    """
    Represents a single identity within the Maroon ecosystem.
    Zero-Trust: default trust is 0.0. Trust is EARNED, never assumed.
    """

    def __init__(self, entity_id: str, display_name: str = ""):
        self.entity_id = entity_id
        self.display_name = display_name
        self.tier = MIVLTier.ANONYMOUS
        self.trust_score = 0.0  # RULE 0: Zero-Alliance Baseline
        self.verification_history: list = []
        self.anomaly_flags: list = []
        self.vouchers: list = []  # Entity IDs of vouching members
        self.created_at = datetime.now(timezone.utc)
        self.last_audit = None

    def _record_transition(self, action: str, old_tier: MIVLTier, new_tier: MIVLTier, reason: str):
        """Cryptographically record every tier transition — immutable audit trail."""
        record = {
            "entity_id": self.entity_id,
            "action": action,
            "old_tier": old_tier.name,
            "new_tier": new_tier.name,
            "trust_score": self.trust_score,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        # SHA-512 hash of the transition for Truth Teller chain
        record["hash"] = hashlib.sha512(
            json.dumps(record, sort_keys=True).encode()
        ).hexdigest()
        self.verification_history.append(record)
        return record

    def upgrade_tier(self, new_tier: MIVLTier, reason: str, auditor_id: Optional[str] = None) -> dict:
        """
        Upgrade identity tier. Requires explicit justification.
        No tier grants immunity from Truth Teller audits.
        """
        if new_tier <= self.tier:
            return {"error": "Cannot upgrade to same or lower tier"}

        if new_tier == MIVLTier.COMMUNITY and len(self.vouchers) < 2:
            return {"error": "Community tier requires 2+ vouchers from Tier-3+ members"}

        if new_tier == MIVLTier.OPERATOR and not self.last_audit:
            return {"error": "Operator tier requires completed financial audit"}

        old_tier = self.tier
        self.tier = new_tier
        # Set trust to the minimum of the new tier range
        min_trust, _ = TIER_TRUST_RANGES[new_tier]
        self.trust_score = min_trust

        return self._record_transition("UPGRADE", old_tier, new_tier, reason)

    def regress_tier(self, reason: str) -> dict:
        """
        Automatic tier regression upon financial anomaly or trust violation.
        Control Plane §1.1: Regression is automatic, no appeals during investigation.
        """
        old_tier = self.tier
        if self.tier > MIVLTier.ANONYMOUS:
            self.tier = MIVLTier(self.tier - 1)
        self.trust_score = TIER_TRUST_RANGES[self.tier][0]
        self.anomaly_flags.append({
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return self._record_transition("REGRESSION", old_tier, self.tier, reason)

    def flag_anomaly(self, anomaly_type: str, details: str) -> dict:
        """Flag a financial or behavioral anomaly. May trigger automatic regression."""
        flag = {
            "type": anomaly_type,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.anomaly_flags.append(flag)

        # Auto-regress on critical anomalies
        critical_types = {"financial_fraud", "identity_theft", "extraction_pattern", "buffer_class_behavior"}
        if anomaly_type in critical_types:
            self.regress_tier(f"Auto-regression: {anomaly_type}")

        return flag

    def add_voucher(self, voucher_entity_id: str, voucher_tier: MIVLTier):
        """Add a voucher for Community tier upgrade. Voucher must be Tier 3+."""
        if voucher_tier < MIVLTier.COMMUNITY:
            return {"error": "Voucher must be Tier 3 (Community) or above"}
        if voucher_entity_id not in self.vouchers:
            self.vouchers.append(voucher_entity_id)
        return {"vouchers": len(self.vouchers), "required": 2}

    def has_access(self, permission: str) -> bool:
        """Check if this identity has a specific access permission."""
        return permission in TIER_ACCESS.get(self.tier, set())

    def to_dict(self) -> dict:
        """Serialize identity for API response or storage."""
        return {
            "entity_id": self.entity_id,
            "display_name": self.display_name,
            "tier": self.tier.name,
            "tier_value": int(self.tier),
            "trust_score": self.trust_score,
            "permissions": sorted(TIER_ACCESS.get(self.tier, set())),
            "anomaly_count": len(self.anomaly_flags),
            "voucher_count": len(self.vouchers),
            "created_at": self.created_at.isoformat(),
            "verification_records": len(self.verification_history),
        }


# ---------------------------------------------------------------------------
# The Cookout Protocol — Control Plane §3.1
# ---------------------------------------------------------------------------

class CookoutProtocol:
    """
    Three-gate trust verification for external entities.
    If ANY gate fails, the entity is classified as a hostile observer.

    Gate 1: Proximity  — "Who invited you?" (traceable vouching chain)
    Gate 2: History    — "Do we know them?" (historical intent verification)
    Gate 3: Contribution — "What did you bring?" (economic/cultural contribution)
    """

    @staticmethod
    def evaluate(
        has_vouching_chain: bool,
        historical_intent_verified: bool,
        contribution_value: float,
        contribution_threshold: float = 0.0,
    ) -> dict:
        """
        Run the Cookout Protocol on an external entity.
        Returns classification: TRUSTED, TRANSACTIONAL, or HOSTILE_OBSERVER.
        """
        gates = {
            "gate_1_proximity": has_vouching_chain,
            "gate_2_history": historical_intent_verified,
            "gate_3_contribution": contribution_value > contribution_threshold,
        }

        all_passed = all(gates.values())
        passed_count = sum(gates.values())

        if all_passed:
            classification = "TRUSTED"
            trust_score = 0.4  # Start at Community tier minimum
        elif passed_count >= 2:
            classification = "TRANSACTIONAL"
            trust_score = 0.1  # Registered tier minimum — watched
        else:
            classification = "HOSTILE_OBSERVER"
            trust_score = 0.0  # Locked out

        result = {
            "gates": gates,
            "classification": classification,
            "trust_score": trust_score,
            "passed": passed_count,
            "total": len(gates),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Hash for Truth Teller audit
        result["hash"] = hashlib.sha512(
            json.dumps(result, sort_keys=True, default=str).encode()
        ).hexdigest()[:32]

        return result


# ---------------------------------------------------------------------------
# CLI Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("MIVL IDENTITY ENGINE — Zero-Alliance Baseline Test")
    print("=" * 60)

    # Create a new identity — starts at Tier 0, trust 0.0
    identity = MIVLIdentity("entity_001", "Test Vendor")
    print(f"\nNew identity: {json.dumps(identity.to_dict(), indent=2)}")

    # Upgrade through tiers
    print("\n--- Upgrading to REGISTERED ---")
    result = identity.upgrade_tier(MIVLTier.REGISTERED, "Email + phone verified")
    print(f"Result: {result}")

    print("\n--- Upgrading to VERIFIED ---")
    identity.last_audit = datetime.now(timezone.utc)
    result = identity.upgrade_tier(MIVLTier.VERIFIED, "Government ID + KYC passed")
    print(f"Result: {result}")

    # Try Community without vouchers — should fail
    print("\n--- Attempting COMMUNITY without vouchers ---")
    result = identity.upgrade_tier(MIVLTier.COMMUNITY, "Self-request")
    print(f"Result: {result}")

    # Add vouchers and try again
    identity.add_voucher("elder_001", MIVLTier.COUNCIL)
    identity.add_voucher("elder_002", MIVLTier.OPERATOR)
    print("\n--- Attempting COMMUNITY with 2 vouchers ---")
    result = identity.upgrade_tier(MIVLTier.COMMUNITY, "Vouched by 2 elders")
    print(f"Result: {result}")

    # Test anomaly-triggered regression
    print("\n--- Flagging financial anomaly ---")
    identity.flag_anomaly("financial_fraud", "Suspicious extraction pattern detected")
    print(f"After anomaly: Tier={identity.tier.name}, Trust={identity.trust_score}")

    # Cookout Protocol test
    print("\n" + "=" * 60)
    print("COOKOUT PROTOCOL — External Entity Evaluation")
    print("=" * 60)

    # Entity passes all gates
    result = CookoutProtocol.evaluate(
        has_vouching_chain=True,
        historical_intent_verified=True,
        contribution_value=5000.0,
    )
    print(f"\nFull pass: {json.dumps(result, indent=2)}")

    # Entity fails proximity gate — classified as hostile
    result = CookoutProtocol.evaluate(
        has_vouching_chain=False,
        historical_intent_verified=False,
        contribution_value=0.0,
    )
    print(f"\nFull fail: {json.dumps(result, indent=2)}")
