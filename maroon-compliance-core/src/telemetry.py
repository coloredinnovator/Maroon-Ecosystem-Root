"""
Maroon Compliance Core — Telemetry Module (v4.0)
Codex §5.1: The Palantir Mandate — all events emitted to Palantir Lake.
"""
import os
import json
import logging
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict

logger = logging.getLogger("compliance.telemetry")


class TelemetryEmitter:
    """Emits compliance telemetry to Palantir Lake (Kafka or log fallback)."""

    def __init__(self, source: str = "maroon-compliance-core"):
        self.source = source
        self._producer = None
        bootstrap = os.environ.get("KAFKA_BOOTSTRAP", "localhost:9092")
        try:
            from kafka import KafkaProducer
            self._producer = KafkaProducer(
                bootstrap_servers=[bootstrap],
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            )
            logger.info("[Compliance Telemetry] Kafka connected to %s", bootstrap)
        except Exception as exc:
            logger.warning("[Compliance Telemetry] Kafka unavailable (%s). Using log fallback.", exc)

    def emit(self, event_type: str, payload: Dict[str, Any]) -> dict:
        envelope = {
            "source": self.source,
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": payload,
            "verification_status": "VERIFIED",
            "merkle_hash": hashlib.sha512(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest(),
        }
        if self._producer:
            self._producer.send("bronze_raw_ingress", value=envelope)
            self._producer.flush()
        else:
            logger.info("[Compliance Telemetry] %s", json.dumps(envelope, default=str))
        return envelope
